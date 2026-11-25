"""Evaluate Retinexformer with the author checkpoints on the 100-pair LOL-v2 test split."""
import argparse
import math
import platform
import statistics
import time
from pathlib import Path

import cv2
import numpy as np
import torch

from eval_lolv1_pair import digest, load_model, peak_rss, predict, quantize, read_rgb, scores, write_csv, write_json

WEIGHT_SHA256 = {
    'real': '539bd16c4da6179e45616329f249c4672951b1045193428e1d042c50d4b65a0b',
    'synthetic': '2f793853c6b1ba0b4a3ff12b7b10f0f2c851eaefda1006437eb3f35229838c4a',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant', choices=WEIGHT_SHA256)
    parser.add_argument('dataset', type=Path, help='Original Real_captured or Synthetic Test directory')
    parser.add_argument('repo', type=Path)
    parser.add_argument('weights', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    low, high = args.dataset/'Low', args.dataset/'Normal'
    names = sorted(p.name for p in low.glob('*.png'))
    if len(names) != 100 or names != sorted(p.name for p in high.glob('*.png')):
        parser.error('Expected 100 identically named pairs in Low and Normal')
    torch.set_num_threads(args.threads)
    cv2.setNumThreads(1)
    model, provenance = load_model('retinexformer', args.repo, args.weights,
        expected_sha=WEIGHT_SHA256[args.variant], retinex_variant='LOL_v2_'+args.variant)
    args.out.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in names:
        src, ref = low/name, high/name
        source, target = read_rgb(src), read_rgb(ref)
        restored, seconds = predict(model, source, 4)
        target_f = target.astype(np.float32)/255
        output = quantize(restored)
        row = dict(name=name, width=source.shape[1], height=source.shape[0],
                   input_sha256=digest(src), gt_sha256=digest(ref),
                   paper_psnr_float=float(10*math.log10(1/np.mean((target_f-restored)**2))),
                   paper_ssim=scores(output,target)['ssim'], forward_seconds=seconds)
        rows.append(row)
        print(name, round(row['paper_psnr_float'], 5), round(row['paper_ssim'], 6), flush=True)
    write_csv(args.out/'metrics.csv', rows)
    write_json(args.out/'summary.json', dict(provenance, test_pairs=len(rows),
        variant=args.variant, threads=args.threads, device='cpu', platform=platform.platform(),
        python=platform.python_version(), torch=str(torch.__version__), numpy=np.__version__,
        script_sha256=digest(Path(__file__)), evaluator_sha256=digest(Path(__file__).with_name('eval_lolv1_pair.py')),
        psnr=statistics.mean(row['paper_psnr_float'] for row in rows),
        ssim=statistics.mean(row['paper_ssim'] for row in rows),
        sum_forward_s=sum(row['forward_seconds'] for row in rows), peak_process_bytes=peak_rss()))


if __name__ == '__main__':
    main()
