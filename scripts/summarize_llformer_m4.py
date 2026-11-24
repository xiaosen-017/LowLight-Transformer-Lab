"""Independently verify saved M4 PNGs, then tabulate paired metrics and timings."""
import argparse
import csv
import json
import statistics
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

from eval_llformer_lol import digest
from infer_llformer_tiled import ROOT


def metrics(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def verify(path,split):
    rows=metrics(path/"metrics.csv")
    for i,row in enumerate(rows):
        name=row["name"]
        png=path/f"{i:02d}_{name}"
        for key,fn in dict(png=png,gt=split/"high"/name,low=split/"low"/name).items():
            assert digest(fn)==row[key+"_sha256"]
        with Image.open(png) as im, Image.open(split/"high"/name) as ref:
            a,b=np.array(im),np.array(ref)
        ps=peak_signal_noise_ratio(b,a,data_range=255)
        ss=np.mean([structural_similarity(a[:,:,c],b[:,:,c],win_size=11,data_range=255,
                    gaussian_weights=True,sigma=1.5,use_sample_covariance=False) for c in range(3)])
        assert abs(ps-float(row["psnr"]))<1e-9 and abs(ss-float(row["ssim"]))<1e-9
        # Independent mask: measure distance of each pixel center to each internal cut.
        h,w=b.shape[:2]
        cuts=[]
        for n in (h,w):
            coords=set()
            for t in (128,256):
                last=max(t,((n+15)//16)*16)-t
                anchors=set(range(0,last+1,t//2))|{last}
                coords.update(v for a0 in anchors for v in (a0,a0+t) if 0<v<n)
            cuts.append(np.array([any(abs(j+0.5-k)<2 for k in coords) for j in range(n)]))
        mask=cuts[0][:,None]|cuts[1][None,:]
        residual=abs(a.astype(float)-b)
        assert int(mask.sum())==int(row["edge_pixels"])
        assert abs(residual[mask].mean()-float(row["edge_mae"]))<1e-10
        assert int(row["covered_min"])>0 and float(row["weight_min"])>0
    return rows


def main():
    p=argparse.ArgumentParser()
    for arg in ("study","lol","out"):
        p.add_argument(arg,type=Path)
    args=p.parse_args()
    plan=json.loads((ROOT/"configs/m4_lol.json").read_text())
    official=metrics(ROOT/"experiments/m3_evaluation/llformer/metrics.csv")
    runs={}
    summary={}
    for arm,(t,s,fusion) in plan["formal"].items():
        rows=verify(args.study/f"eval-{arm}",args.lol/"eval15")
        assert [x["name"] for x in rows]==[x["name"] for x in official]
        assert all((int(r["tile"]),int(r["stride"]),r["fusion"])==(t,s,fusion) for r in rows)
        runs[arm]=rows
        stats={k:statistics.mean(float(r[k]) for r in rows)
               for k in ("psnr","ssim","edge_mae","whole_mae")}
        bench=metrics(args.study/f"bench-{arm}/metrics.csv")
        assert [r["repeat"] for r in bench]==list("012345")
        target=next(r for r in rows if r["name"]=="111.png")
        assert all(r["png_sha256"]==target["png_sha256"] and
                   (r["tile"],r["stride"],r["fusion"])==(target["tile"],target["stride"],target["fusion"])
                   for r in bench)
        stats["bench"]={k:dict(median=statistics.median(v),min=min(v),max=max(v)) for k in
                ("net_s","tile_pipeline_s","end_to_end_s") for v in [[float(r[k]) for r in bench[1:]]]}
        stats["bench"]["peak_process_gib"]=max(int(r["peak_process_bytes"]) for r in bench)/2**30
        summary[arm]=stats
    dev=verify(args.study/"dev",args.lol/"our485")
    assert len(dev)==9 and {(int(r["tile"]),int(r["stride"])) for r in dev}=={
        (t,t*(100-p)//100) for t in plan["dev_tiles"] for p in plan["dev_overlap_percent"]}
    runs["full"]=official
    deltas={}
    for x,y in [("C","A"),("D","B"),("B","A"),("D","C"),("D","A"),("D","full")]:
        diffs={}
        for k in ("psnr","ssim","edge_mae") if y!="full" else ("psnr","ssim"):
            vals=[float(a[k])-float(b[k]) for a,b in zip(runs[x],runs[y],strict=True)]
            diffs[k]=dict(mean=statistics.mean(vals),min=min(vals),max=max(vals),
                          improved=sum((v<0 if k=="edge_mae" else v>0) for v in vals),
                          worst_image=runs[y][(vals.index(max(vals)) if k=="edge_mae" else vals.index(min(vals)))]["name"])
        deltas[x+"-"+y]=diffs
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/"summary.json").write_text(json.dumps(dict(arms=summary,paired=deltas,
           verified_eval_pngs=60,verified_dev_pngs=9,bench_repeated_pngs=24),indent=2)+"\n")
    print(json.dumps(summary))


if __name__=="__main__":
    main()
