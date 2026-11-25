"""Evaluate either official LOL-v1 model using the same paired images and CPU protocol."""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

try:
    from skimage.metrics import structural_similarity
except ImportError:
    from skimage.measure import compare_ssim as structural_similarity

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hash_stream(stream)


def hash_stream(stream):
    hashed = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        hashed.update(block)
    return hashed.hexdigest()


def module_from(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_model(name, repo, weights, expected_sha=None):
    registration = next(x for x in json.loads((ROOT/'configs/weights.json').read_text())
                        if x['model'].lower() == name)
    upstream = json.loads((ROOT/'configs/upstreams.json').read_text())[registration['model']]
    sha = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if sha != upstream['commit'] or subprocess.check_output(['git', '-C', str(repo), 'diff', 'HEAD', '--']):
        raise ValueError('Expected clean pinned upstream: ' + upstream['commit'])
    weight_hash = digest(weights)
    if weight_hash != (expected_sha or registration['sha256']):
        raise ValueError('Checkpoint SHA-256 does not match the experiment registration')
    if name == 'llformer' and torch.__version__.split('+')[0] == '1.13.1':
        # The registered author checkpoint includes optimizer scalars that the
        # older restricted unpickler cannot read. Only the registered LOL file
        # may use its historical upstream loader on this version of Torch.
        if weight_hash != registration['sha256']:
            raise ValueError('Use a modern Torch weights-only loader for other checkpoints')
        checkpoint = torch.load(str(weights), map_location='cpu')
    else:
        checkpoint = torch.load(str(weights), map_location='cpu', weights_only=True)
    if name == 'retinexformer':
        import yaml
        module = module_from('official_retinex_arch', repo/'basicsr/models/archs/RetinexFormer_arch.py')
        config = yaml.safe_load((repo/'Options/RetinexFormer_LOL_v1.yml').read_text())['network_g']
        config.pop('type')
        model = module.RetinexFormer(**config)
        state = checkpoint.get('params_ema', checkpoint.get('params', checkpoint))
    else:
        module = module_from('official_llformer_arch', repo/'model/LLFormer.py')
        model = module.LLFormer(inp_channels=3, out_channels=3, dim=16,
                                num_blocks=[2, 4, 8, 16], num_refinement_blocks=2,
                                heads=[1, 2, 4, 8], ffn_expansion_factor=2.66, bias=False,
                                LayerNorm_type='WithBias', attention=True, skip=False)
        state = checkpoint['state_dict']
    cleaned = {k[7:] if k.startswith('module.') else k: v for k, v in state.items()}
    model.load_state_dict(cleaned, strict=True)
    return model.eval(), dict(upstream=sha, weights_sha256=weight_hash, strict_state_keys=len(cleaned))


def read_rgb(path):
    with Image.open(path) as image:
        if image.mode != 'RGB':
            raise ValueError('Expected RGB: ' + path.name)
        return np.array(image)


def save_rgb(path, array):
    Image.fromarray(array, 'RGB').save(str(path))


def predict(model, array, multiple):
    h, w = array.shape[:2]
    tensor = torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0).float()/255
    tensor = F.pad(tensor, (0, (-w) % multiple, 0, (-h) % multiple), 'reflect')
    with torch.inference_mode():
        started = time.perf_counter()
        restored = model(tensor)
        seconds = time.perf_counter()-started
    cropped = restored[0, :, :h, :w].clamp(0, 1).permute(1, 2, 0).numpy()
    if not np.isfinite(cropped).all():
        raise ValueError('Nonfinite prediction')
    return cropped, seconds


def quantize(rgb):
    return np.rint(rgb*255).astype(np.uint8)


def scores(pred, gt):
    if pred.shape != gt.shape:
        raise ValueError('Prediction and reference shapes differ')
    delta = pred.astype(np.float64)-gt
    mse = np.mean(delta**2)
    result = {'psnr': float(10*math.log10(255**2/mse)) if mse else float('inf')}
    for key, size, gaussian, covariance in [('ssim', 11, True, False), ('ssim_uniform7', 7, False, True)]:
        result[key] = float(np.mean([structural_similarity(pred[:, :, c], gt[:, :, c],
            data_range=255, win_size=size, gaussian_weights=gaussian, sigma=1.5,
            use_sample_covariance=covariance) for c in range(3)]))
    return result


def peak_rss():
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        class MemoryCounters(ctypes.Structure):
            _fields_ = [('size', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
                (field, ctypes.c_size_t) for field in ('peak_working_set', 'working_set', 'peak_paged',
                    'paged', 'peak_nonpaged', 'nonpaged', 'pagefile', 'peak_pagefile')]
        handle = ctypes.windll.kernel32.GetCurrentProcess
        handle.restype = wintypes.HANDLE
        counter = MemoryCounters()
        counter.size = ctypes.sizeof(counter)
        method = ctypes.windll.psapi.GetProcessMemoryInfo
        method.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD]
        if not method(handle(), ctypes.byref(counter), counter.size):
            raise OSError('Could not read peak working set')
        return counter.peak_working_set
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', choices=['retinexformer', 'llformer'])
    parser.add_argument('dataset', type=Path)
    parser.add_argument('repo', type=Path)
    parser.add_argument('weights', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--bench-repeats', type=int, default=5)
    parser.add_argument('--benchmark-only', action='store_true')
    args = parser.parse_args()
    low, high = args.dataset/'low', args.dataset/'high'
    names = sorted(x.name for x in low.glob('*.png'))
    if len(names) != 15 or names != sorted(x.name for x in high.glob('*.png')):
        parser.error('Expected 15 matching LOL-v1 low/high PNG names')
    reference = ROOT/'experiments/m3_evaluation/llformer/metrics.csv'
    with reference.open(encoding='utf-8') as stream:
        manifest = {row['name']:row for row in csv.DictReader(stream)}
    if set(names) != set(manifest) or any(
            digest(low/name) != manifest[name]['low_sha256'] or
            digest(high/name) != manifest[name]['gt_sha256'] for name in names):
        parser.error('Input or GT SHA-256 differs from the registered official LOL-v1 eval15')
    torch.set_num_threads(args.threads)
    cv2.setNumThreads(1)
    setup = time.perf_counter()
    model, provenance = load_model(args.model, args.repo.resolve(), args.weights)
    setup = time.perf_counter()-setup
    multiple = 4 if args.model == 'retinexformer' else 16
    args.out.mkdir(parents=True, exist_ok=False)
    images = args.out/'images'
    images.mkdir()
    write_json(args.out/'config.json', dict(provenance, model=args.model, platform=platform.platform(),
        python=platform.python_version(), torch=str(torch.__version__), numpy=np.__version__,
        threads=args.threads, script_sha256=digest(Path(__file__)), setup_s=setup, device='cpu'))
    if not args.benchmark_only:
        rows = []
        for name in names:
            source, target = read_rgb(low/name), read_rgb(high/name)
            restored, seconds = predict(model, source, multiple)
            file = images/name
            save_rgb(file, quantize(restored))
            metrics = scores(read_rgb(file), target)
            row = dict(name=name, low_sha256=digest(low/name), gt_sha256=digest(high/name),
                       output_sha256=digest(file), forward_seconds=seconds, **metrics)
            if args.model == 'retinexformer':
                target_f = target.astype(np.float32)/255
                row['paper_psnr_float'] = float(10*math.log10(1/np.mean((target_f-restored)**2)))
                a = cv2.cvtColor(restored, cv2.COLOR_BGR2GRAY).mean()
                b = cv2.cvtColor(target_f, cv2.COLOR_BGR2GRAY).mean()
                calibrated = np.clip(restored*(b/a), 0, 1)
                row['gt_mean_psnr_float'] = float(10*math.log10(1/np.mean((target_f-calibrated)**2)))
                row['gt_mean_ssim'] = scores(quantize(calibrated), target)['ssim']
            rows.append(row)
            print(name, round(metrics['psnr'], 4), round(metrics['ssim'], 5), flush=True)
        write_csv(args.out/'metrics.csv', rows)
        summary_keys = ('psnr', 'ssim', 'ssim_uniform7', 'paper_psnr_float', 'gt_mean_psnr_float', 'gt_mean_ssim')
        write_json(args.out/'summary.json', {k: statistics.mean(r[k] for r in rows)
                   for k in summary_keys if k in rows[0]})
    if args.bench_repeats:
        sample = low/'111.png'
        bench = []
        for i in range(args.bench_repeats+1):
            started = time.perf_counter()
            restored, seconds = predict(model, read_rgb(sample), multiple)
            file = images/('benchmark_%d.png' % i)
            save_rgb(file, quantize(restored))
            end_to_end = time.perf_counter()-started
            bench.append(dict(index=i, warmup=(i == 0), forward_s=seconds, end_to_end_s=end_to_end,
                              output_sha256=digest(file)))
        write_json(args.out/'benchmark.json', dict(sample=sample.name, input_sha256=digest(sample),
            peak_process_bytes=peak_rss(), rows=bench,
            medians={k: statistics.median(x[k] for x in bench[1:]) for k in ('forward_s', 'end_to_end_s')}))


if __name__ == '__main__':
    main()
