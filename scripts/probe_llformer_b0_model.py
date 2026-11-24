"""Compare original B0 geometry (device-only adapter) to B1, on one dev pair."""
import argparse
import json
import resource
import sys
import time
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from check_llformer_b0 import helpers
from infer_llformer_tiled import ROOT, load_model
from eval_llformer_lol import digest
import platform
import subprocess
from llformer_tiling import tiled_predict


@torch.inference_mode()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("image",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--default-tile",action="store_true")
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(4)
    model=load_model("cpu")
    # The runner is usable from an arbitrary machine; archive only portable names.
    source=args.image
    config=dict(input_name=source.name,input_sha256=digest(source),
                source_script=Path(__file__).name,source_script_sha256=digest(Path(__file__)),
                code_sha=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip(),
                upstream_sha=subprocess.check_output(["git","-C",str(ROOT/"third_party/LLFormer"),"rev-parse","HEAD"],text=True).strip(),
                weights_sha256=digest(ROOT/"weights/llformer/model_bestPSNR.pth"),
                python=platform.python_version(),torch=str(torch.__version__),device="cpu",threads=4)
    (args.out/"config.json").write_text(json.dumps(config,indent=2)+"\n")
    ns,_=helpers(True)
    rows=[]
    with Image.open(args.image) as source:
        # Controlled development geometry only: no UHD quality claim.
        cases=([(720,1280,720,1280)] if args.default_tile else
               [(256,320,128,128),(272,336,128,128),(80,96,128,128)])
        for h,w,ph,pw in cases:
            im=(source.resize((w,h),Image.Resampling.BICUBIC) if args.default_tile
                else source.crop((0,0,w,h)))
            rgb=torch.from_numpy(np.array(im.convert("RGB"))).permute(2,0,1).float()/255
            row=dict(hw=[h,w],tile=[ph,pw],stride=[ph//2,pw//2],default_tile=args.default_tile)
            before=time.perf_counter()
            try:
                parts,corners=ns["image_to_patches"](rgb,(ph,pw),(ph//2,pw//2))
                outputs=[model(tile)[0] for tile in parts.split(1)]
                b0=ns["patches_to_image"](outputs,corners,(ph,pw),(3,h+16,w+16))[:,:h,:w]
                valid=b0.isfinite().all(dim=0)
                row.update(b0_tiles=len(corners),b0_invalid_pixels=int((~valid).sum()))
                del parts,outputs
            except RuntimeError as exc:
                if "non-empty TensorList" not in str(exc):
                    raise
                row["b0_error"]=str(exc)
                b0=None
            row["b0_seconds"]=time.perf_counter()-before
            b1,counts,_,corners=tiled_predict(rgb,model,(ph,pw),(ph//2,pw//2))
            row.update(b1_tiles=len(corners),b1_min_count=int(counts.min()),b1_invalid_pixels=int(
                (~b1.isfinite().all(dim=0)).sum()))
            if b0 is not None and bool(valid.all()):
                row["max_abs_b0_b1"]=float((b0-b1).abs().max())
                assert row["max_abs_b0_b1"]<=1e-6
            if (h,w)==(272,336):
                assert row["b0_invalid_pixels"]==h*w-256*320
            row["peak_process_bytes"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(
                1 if sys.platform=="darwin" else 1024)
            rows.append(row)
            print(row,flush=True)
    (args.out/"results.json").write_text(json.dumps(rows,indent=2)+"\n")


if __name__=="__main__":
    main()
