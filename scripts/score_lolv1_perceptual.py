"""Score the same saved LOL-v1 PNGs with the LLFormer AlexNet LPIPS protocol."""
import argparse
import csv
from pathlib import Path
import statistics

import lpips
import numpy as np
import torch

from eval_lolv1_pair import digest, read_rgb, write_csv, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('gt', type=Path)
    parser.add_argument('alexnet', type=Path, help='Official torchvision checkpoint or extracted convolution NPZ')
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    torch.set_num_threads(4)
    with (args.run/'metrics.csv').open(encoding='utf-8') as stream:
        baseline = list(csv.DictReader(stream))
    if len(baseline) != 15 or len({r['name'] for r in baseline}) != 15:
        raise ValueError('Expected 15 evaluated pairs')
    weight_sha = digest(args.alexnet)
    extracted = args.alexnet.suffix == '.npz'
    if not extracted and not weight_sha.startswith('7be5be79'):
        raise ValueError('Expected torchvision alexnet-owt-7be5be79.pth')
    # LPIPS 0.1.4 constructs AlexNet slices in this module. Load only the
    # feature tensors from the verified torchvision checkpoint into the slices.
    evaluator = lpips.LPIPS(net='alex', pnet_rand=True, verbose=False).eval()
    if extracted:
        with np.load(args.alexnet, allow_pickle=False) as arrays:
            checkpoint = {key:torch.from_numpy(arrays[key]) for key in arrays.files}
    else:
        checkpoint = torch.load(str(args.alexnet), map_location='cpu', weights_only=True)
    feature_state = {}
    for key, tensor in checkpoint.items():
        if not key.startswith('features.'):
            continue
        index = int(key.split('.')[1])
        group = 1 if index < 2 else 2 if index < 5 else 3 if index < 8 else 4 if index < 10 else 5
        feature_state['slice%d.' % group + key[len('features.'):]] = tensor
    evaluator.net.load_state_dict(feature_state, strict=True)
    del checkpoint
    results = []
    with torch.inference_mode():
        for row in baseline:
            name = row['name']
            prediction, target = args.run/'images'/name, args.gt/name
            if digest(prediction) != row['output_sha256'] or digest(target) != row['gt_sha256']:
                raise ValueError('Pixel file digest mismatch: ' + name)
            rgb, gt = read_rgb(prediction), read_rgb(target)
            a, b = (torch.from_numpy(im).permute(2,0,1)[None].float()/127.5-1 for im in (rgb, gt))
            results.append(dict(name=name, prediction_sha256=digest(prediction), gt_sha256=digest(target),
                lpips_alex=float(evaluator(a,b).item()), mae=float(np.abs(rgb.astype(np.float64)-gt).mean()/255)))
            print(name, results[-1]['lpips_alex'], results[-1]['mae'], flush=True)
    args.out.mkdir(parents=True, exist_ok=False)
    write_csv(args.out/'metrics.csv',results)
    write_json(args.out/'summary.json',dict(alexnet_sha256=weight_sha, lpips_version='0.1.4',
        alexnet_asset='convolution tensors extracted from official archive, ZIP CRC checked' if extracted else 'full torchvision checkpoint',
        **{metric:statistics.mean(row[metric] for row in results) for metric in ('lpips_alex','mae')}))


if __name__ == '__main__':
    main()
