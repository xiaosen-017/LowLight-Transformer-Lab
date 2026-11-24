"""Score the five existing paired M2 outputs; do not infer or mix runs with M3."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity
from eval_llformer_lol import digest
from infer_llformer_tiled import ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("eval15",type=Path)
    p.add_argument("out",type=Path)
    args=p.parse_args()
    inputs=json.loads((ROOT/"configs/m2_samples.json").read_text())["samples"]
    rows=[]
    for rec in inputs:
        name=rec["name"]
        assert digest(args.eval15/"low"/name)==rec["sha256"]
        with Image.open(args.eval15/"high"/name) as im:
            gt=np.asarray(im)
        for model in ("llformer","retinexformer"):
            path=ROOT/"results/m2"/model/name
            with Image.open(path) as im:
                arr=np.asarray(im)
            assert arr.shape==gt.shape==(400,600,3) and arr.dtype==gt.dtype==np.uint8
            rows.append(dict(name=name,model=model,gt_sha256=digest(args.eval15/"high"/name),
                        output_sha256=digest(path),psnr=peak_signal_noise_ratio(gt,arr,data_range=255),
                        ssim=structural_similarity(gt,arr,channel_axis=-1,data_range=255,
                        gaussian_weights=True,sigma=1.5,win_size=11,use_sample_covariance=False)))
    with args.out.open("x",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=rows[0],lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for model in ("llformer","retinexformer"):
        print(model,{k:float(np.mean([r[k] for r in rows if r["model"]==model])) for k in ("psnr","ssim")})


if __name__=="__main__":
    main()
