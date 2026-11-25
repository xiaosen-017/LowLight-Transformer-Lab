"""Check streaming tile fusion against the original stack and run paired scale tests."""
import argparse
from itertools import product
import platform
from pathlib import Path
import time

import numpy as np
from PIL import Image
import torch

from eval_lolv1_pair import digest, load_model, peak_rss, quantize, read_rgb, save_rgb, scores, write_json
from llformer_tiling import reflected_axis, starts, tiled_predict


@torch.inference_mode()
def stream_predict(image, model, tile, stride, fusions, progress=False):
    h, w = image.shape[-2:]
    height, width = (max(tile, ((n+15)//16)*16) for n in (h, w))
    padded = image.index_select(1, reflected_axis(h, height, image.device))
    padded = padded.index_select(2, reflected_axis(w, width, image.device))
    anchors = list(product(starts(height, tile, stride), starts(width, tile, stride)))
    axis = torch.hann_window(tile, periodic=False, device=image.device)
    windows = {'mean': image.new_ones(tile, tile), 'hann': torch.outer(axis, axis).clamp_min(0.001)}
    sums = {name: torch.zeros_like(padded) for name in fusions}
    weights = {name: image.new_zeros(height, width) for name in fusions}
    for index, (y, x) in enumerate(anchors, 1):
        region = (slice(y, y+tile), slice(x, x+tile))
        prediction = model(padded[(slice(None),)+region].contiguous()[None])[0]
        for name in fusions:
            sums[name][(slice(None),)+region] += prediction*windows[name]
            weights[name][region] += windows[name]
        if progress and (index == len(anchors) or index % 5 == 0):
            print('Tiles', index, '/', len(anchors), flush=True)
    minimum = {name: float(weights[name].min()) for name in fusions}
    if any(value <= 0 for value in minimum.values()):
        raise ValueError('Tile coverage incomplete')
    outputs = {name: (sums[name]/weights[name])[:, :h, :w] for name in fusions}
    if not all(torch.isfinite(value).all() for value in outputs.values()):
        raise ValueError('Nonfinite fusion output')
    return outputs, dict(tiles=len(anchors), minimum_weight=minimum, shape=[h,w],
                         anchors=[list(anchor) for anchor in anchors])


def check():
    gen = torch.Generator().manual_seed(17)
    cases = []
    for h, w in [(17,29), (73,101), (96,96), (1,31)]:
        image = torch.rand(3,h,w,generator=gen)
        def predict(x):
            return torch.nn.functional.avg_pool2d(x,3,1,1)
        streamed, reconstructed = stream_predict(image,predict,32,16,['mean','hann'])
        for name in streamed:
            reference, _, _, _ = tiled_predict(image,predict,(32,32),(16,16),name)
            error = float((reference-streamed[name]).abs().max())
            if error > 1e-6:
                raise AssertionError('Streaming implementation differs from reference')
            cases.append(dict(shape=[h,w], fusion=name, max_abs_difference=error,
                              tiles=reconstructed['tiles']))
    return cases


def rgb_tensor(path, long_side=None):
    with Image.open(path) as source:
        image = source.convert('RGB')
        if long_side:
            scale = long_side/max(image.size)
            shape = tuple(round(value*scale) for value in image.size)
            image = image.resize(shape, Image.Resampling.BICUBIC)
        return torch.from_numpy(np.array(image)).permute(2,0,1).float()/255


def edge_scores(pixels, target, anchors, tile):
    residual = pixels.astype(np.float32)-target
    height, width = target.shape[:2]
    band = np.zeros((height,width),dtype=bool)
    cuts = []
    for axis, size in enumerate((height,width)):
        lines = sorted({edge for anchor in anchors for edge in (anchor[axis],anchor[axis]+tile)
                        if 0 < edge < size})
        for line in lines:
            if axis == 0:
                band[max(0,line-2):line+2,:] = True
                cuts.append(np.abs(residual[line,:,:]-residual[line-1,:,:]).ravel())
            else:
                band[:,max(0,line-2):line+2] = True
                cuts.append(np.abs(residual[:,line,:]-residual[:,line-1,:]).ravel())
    return dict(edge_pixels=int(band.sum()), edge_mae=float(np.abs(residual[band]).mean()) if band.any() else None,
                crossing_gradient_error=float(np.concatenate(cuts).mean()) if cuts else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path)
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--weights', type=Path)
    parser.add_argument('--weight-sha256')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--gt', type=Path)
    parser.add_argument('--long-side', type=int)
    parser.add_argument('--tile', type=int, default=256)
    parser.add_argument('--stride', type=int, default=128)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--check-reference', action='store_true')
    args = parser.parse_args()
    if args.tile < 16 or args.tile % 16 or not 0 < args.stride <= args.tile:
        parser.error('Tile must be a multiple of 16 and stride must be in [1, tile]')
    if args.input and not (args.repo and args.weights and args.gt):
        parser.error('Real image evaluation needs --repo, --weights and --gt')
    torch.set_num_threads(args.threads)
    args.out.mkdir(parents=True, exist_ok=False)
    report = dict(torch=str(torch.__version__), platform=platform.platform(), threads=args.threads,
                  regression_cases=check())
    write_json(args.out/'result.json',report)
    if not args.input:
        print('Eight streaming equivalence cases passed',flush=True)
        return
    model, provenance = load_model('llformer',args.repo,args.weights,args.weight_sha256)
    image = rgb_tensor(args.input,args.long_side)
    target = quantize(rgb_tensor(args.gt,args.long_side).permute(1,2,0).numpy())
    start = time.perf_counter()
    outputs, details = stream_predict(image,model,args.tile,args.stride,['mean','hann'],progress=True)
    elapsed = time.perf_counter()-start
    recorded_peak = peak_rss()
    comparisons = {}
    for name, output in outputs.items():
        file = args.out/(name+'.png')
        save_rgb(file,quantize(output.clamp(0,1).permute(1,2,0).numpy()))
        pixels = read_rgb(file)
        result = dict(scores(pixels,target), output_sha256=digest(file),
                      **edge_scores(pixels,target,details['anchors'],args.tile))
        if args.check_reference:
            baseline, _, _, _ = tiled_predict(image,model,(args.tile,)*2,(args.stride,)*2,name)
            result['stack_reference_max_abs_error'] = float((baseline-output).abs().max())
            if result['stack_reference_max_abs_error'] > 1e-5:
                raise ValueError('Checkpoint predictions differ between streaming and stack implementations')
        comparisons[name] = result
    report.update(dict(provenance, **details, input_sha256=digest(args.input), gt_sha256=digest(args.gt),
                       scale_long_side=args.long_side, tile=args.tile, stride=args.stride,
                       combined_prediction_fusion_s=elapsed, peak_process_bytes=recorded_peak,
                       metrics=comparisons))
    write_json(args.out/'result.json',report)
    print('Completed mean and Hann for',details['shape'],elapsed,'seconds',flush=True)


if __name__ == '__main__':
    main()
