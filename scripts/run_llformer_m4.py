"""Frozen CPU LLFormer grid study. One fresh process per arm."""
import argparse
import csv
import json
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity
import torch

from eval_llformer_lol import digest
from infer_llformer_tiled import ROOT, load_model
from llformer_tiling import starts, tiled_predict

PLAN = ROOT/"configs/m4_lol.json"


def edge_mask(h,w,plan):
    mask = np.zeros((h,w),bool)
    for tile,stride,_ in plan["formal"].values():
        for dim,n in enumerate((h,w)):
            padded=max(tile,((n+15)//16)*16)
            axes=starts(padded,tile,stride)
            for v in {a+b for a in axes for b in (0,tile) if 0<a+b<n}:
                band=slice(max(0,v-2),min(n,v+2))
                if dim==0:
                    mask[band,:]=True
                else:
                    mask[:,band]=True
    return mask


def run(args):
    cfg=json.loads(PLAN.read_text())
    torch.set_num_threads(4)
    device="cpu"
    model=load_model(device)
    out=args.output
    out.mkdir(parents=True,exist_ok=False)
    meta=dict(arm=args.arm,device=device,threads=torch.get_num_threads(),python=platform.python_version(),
              torch=str(torch.__version__),code_sha=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
              source_sha256=digest(Path(__file__)),plan_sha256=digest(PLAN),upstream=json.loads(
              (ROOT/"configs/upstreams.json").read_text())["LLFormer"]["commit"],
              weight_sha256=digest(ROOT/"weights/llformer/model_bestPSNR.pth"),mode=args.mode)
    (out/"config.json").write_text(json.dumps(meta,indent=2)+"\n")
    pairs=args.data
    if args.mode=="dev":
        jobs=[("2.png",t,t*(100-o)//100,"mean",0) for t in cfg["dev_tiles"] for o in cfg["dev_overlap_percent"]]
    else:
        t,s,f=cfg["formal"][args.arm]
        if args.mode=="bench":
            jobs=[("111.png",t,s,f,i) for i in range(6)]
        else:
            ref=list(csv.DictReader((ROOT/"experiments/m3_evaluation/llformer/metrics.csv").open()))
            assert len(ref)==15
            for row in ref:
                assert all(digest(pairs/sub/row["name"])==row[key] for sub,key in
                           [("low","low_sha256"),("high","gt_sha256")])
            jobs=[(r["name"],t,s,f,0) for r in ref]
    with (out/"metrics.csv").open("x",newline="") as fp:
        for num,(name,t,s,f,i) in enumerate(jobs):
            start=time.perf_counter()
            with Image.open(pairs/"low"/name) as im:
                rgb=torch.from_numpy(np.array(im.convert("RGB"))).permute(2,0,1).float()/255
            h,w=rgb.shape[-2:]
            net_s=0
            def predict(batch):
                nonlocal net_s
                before=time.perf_counter()
                pred=model(batch)
                net_s+=time.perf_counter()-before
                return pred
            before=time.perf_counter()
            y,counts,weights,corners=tiled_predict(rgb,predict,(t,t),(s,s),f)
            pipeline=time.perf_counter()-before
            arr=(y.clamp(0,1)*255).round().byte().permute(1,2,0).numpy()
            png=out/f"{num:02d}_{name}"
            Image.fromarray(arr).save(png)
            elapsed=time.perf_counter()-start
            rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=="darwin" else 1024)
            with Image.open(pairs/"high"/name) as im:
                gt=np.asarray(im.convert("RGB"),dtype=np.float64)
            delta=arr.astype(float)-gt
            mask=edge_mask(h,w,cfg)
            row=dict(name=name,arm=args.arm,tile=t,stride=s,fusion=f,repeat=i,tiles=len(corners),
                     covered_min=int(counts.min()),weight_min=float(weights.min()),
                     net_s=net_s,tile_pipeline_s=pipeline,end_to_end_s=elapsed,peak_process_bytes=rss,
                     psnr=float(10*np.log10(255**2/np.mean(delta**2))),
                     ssim=structural_similarity(gt,arr.astype(float),channel_axis=-1,data_range=255,
                           win_size=11,gaussian_weights=True,sigma=1.5,use_sample_covariance=False),
                     edge_pixels=int(mask.sum()),edge_mae=float(abs(delta[mask]).mean()),
                     whole_mae=float(abs(delta).mean()),low_sha256=digest(pairs/"low"/name),
                     gt_sha256=digest(pairs/"high"/name),png_sha256=digest(png))
            if num==0:
                writer=csv.DictWriter(fp,fieldnames=row,lineterminator="\n")
                writer.writeheader()
            writer.writerow(row)
            fp.flush()
            print(name,t,s,f,i,round(row["psnr"],3),round(elapsed,2),flush=True)
            if elapsed>180 or rss>8*2**30:
                raise RuntimeError("predeclared resource stop; retained completed output")
            del y,counts,weights,rgb


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("dev","eval","bench"))
    p.add_argument("arm",choices=list("ABCD"))
    p.add_argument("data",type=Path)
    p.add_argument("output",type=Path)
    run(p.parse_args())
