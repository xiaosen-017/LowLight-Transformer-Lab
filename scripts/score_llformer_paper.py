"""Compute the upstream-style uint8 uniform-window SSIM, separately from M3."""
import argparse
import csv
import statistics
from pathlib import Path
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio,structural_similarity


def main():
    p=argparse.ArgumentParser()
    for arg in ("run","gt","csv"):
        p.add_argument(arg,type=Path)
    args=p.parse_args()
    rows=[]
    for r in list(csv.DictReader((args.run/"metrics.csv").open())):
        name=r["name"]
        with Image.open(args.run/name) as im, Image.open(args.gt/name) as ref:
            a,b=np.array(im),np.array(ref)
        assert a.dtype==b.dtype==np.uint8
        psnr=peak_signal_noise_ratio(b,a,data_range=255)
        assert abs(psnr-float(r["psnr"]))<1e-9
        rows.append(dict(name=name,psnr=psnr,ssim_uniform_7=structural_similarity(
                   b,a,data_range=255,win_size=7,gaussian_weights=False,
                   use_sample_covariance=True,channel_axis=-1)))
    assert len(rows)==len(set(x["name"] for x in rows))==15
    with args.csv.open("x",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0],lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print({k:statistics.mean(r[k] for r in rows) for k in ("psnr","ssim_uniform_7")})


if __name__=="__main__":
    main()
