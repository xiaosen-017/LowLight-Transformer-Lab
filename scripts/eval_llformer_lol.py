"""Reproduce full-frame LLFormer on the official paired LOL-v1 eval15 split."""
import argparse
import csv
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import skimage
import torch
from PIL import Image
from skimage.metrics import structural_similarity
from infer_llformer_tiled import ROOT, load_model


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("eval15", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--threads", type=int, default=4)
    args = p.parse_args()
    low, high = [args.eval15 / name for name in ("low", "high")]
    names = sorted(f.name for f in low.glob("*.png"))
    if len(names) != 15 or names != sorted(f.name for f in high.glob("*.png")):
        p.error("expected 15 identical low/high PNG names in official eval15")
    torch.set_num_threads(args.threads)
    model = load_model("cpu")
    args.out.mkdir(parents=True, exist_ok=False)
    config = dict(method="LLFormer whole-frame", device="cpu", threads=args.threads,
                  torch=str(torch.__version__), python=platform.python_version(),
                  numpy=np.__version__, skimage=skimage.__version__,
                  upstream=subprocess.check_output(["git","-C",str(ROOT/"third_party/LLFormer"),
                      "rev-parse","HEAD"],text=True).strip(),
                  weights_sha256=digest(ROOT/"weights/llformer/model_bestPSNR.pth"),
                  script_sha256=digest(Path(__file__)), loader_sha256=digest(
                      ROOT/"scripts/infer_llformer_tiled.py"), repeats=1,
                  timing="exploratory single CPU forward, no warm-up; not a benchmark")
    (args.out/"config.json").write_text(json.dumps(config,indent=2)+"\n")
    rows = []
    for name in names:
        with Image.open(low/name) as src, Image.open(high/name) as gt:
            if src.mode != "RGB" or gt.mode != "RGB" or src.size != gt.size:
                raise ValueError(f"invalid pair: {name}")
            x = torch.from_numpy(np.array(src)).permute(2,0,1)[None].float()/255
            ref = np.asarray(gt,dtype=np.float64)/255
        h,w = x.shape[2:]
        x = torch.nn.functional.pad(x,(0,(-w)%16,0,(-h)%16),"reflect")
        with torch.inference_mode():
            start = time.perf_counter()
            y = model(x)
            seconds = time.perf_counter()-start
            if not y.isfinite().all():
                raise ValueError(f"nonfinite output: {name}")
            rgb = (y[0,:,:h,:w].clamp(0,1)*255).round().byte().permute(1,2,0).numpy()
        Image.fromarray(rgb).save(args.out/name)
        pred = rgb.astype(np.float64)/255
        mse = np.mean((ref-pred)**2)
        row = dict(name=name, width=w,height=h, low_sha256=digest(low/name),
                   gt_sha256=digest(high/name),png_sha256=digest(args.out/name),
                   psnr=float(-10*np.log10(mse)) if mse else float("inf"),
                   ssim=structural_similarity(ref,pred,channel_axis=-1,data_range=1,
                       win_size=11,gaussian_weights=True,sigma=1.5,use_sample_covariance=False),
                   forward_seconds=seconds)
        rows.append(row)
        print(name, f"{row['psnr']:.4f} dB, SSIM {row['ssim']:.5f}, {seconds:.2f}s",flush=True)
    with (args.out/"metrics.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary={k:float(np.mean([r[k] for r in rows])) for k in ("psnr","ssim")}
    (args.out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(summary)


if __name__ == "__main__":
    main()
