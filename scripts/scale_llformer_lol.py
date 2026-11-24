"""Resolution feasibility only: resize one dev photo, no UHD quality claims."""
import argparse
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from infer_llformer_tiled import ROOT, load_model
from eval_llformer_lol import digest
import platform
import subprocess
from llformer_tiling import starts,tiled_predict


def main():
    p=argparse.ArgumentParser()
    p.add_argument("dev_image",type=Path)
    p.add_argument("out",type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(4)
    model=load_model("cpu")
    # The runner is usable from an arbitrary machine; archive only portable names.
    source=args.dev_image
    config=dict(input_name=source.name,input_sha256=digest(source),
                source_script=Path(__file__).name,source_script_sha256=digest(Path(__file__)),
                code_sha=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip(),
                upstream_sha=subprocess.check_output(["git","-C",str(ROOT/"third_party/LLFormer"),"rev-parse","HEAD"],text=True).strip(),
                weights_sha256=digest(ROOT/"weights/llformer/model_bestPSNR.pth"),
                python=platform.python_version(),torch=str(torch.__version__),device="cpu",threads=4)
    (args.out/"config.json").write_text(json.dumps(config,indent=2)+"\n")
    tile,stride=256,128
    rows=[]
    seconds_per_tile=None
    with Image.open(args.dev_image) as im:
        for w in (512,1024,2048):
            h=round(im.height*w/im.width)
            count=np.prod([len(starts(max(tile,(n+15)//16*16),tile,stride)) for n in (h,w)])
            estimate=None if seconds_per_tile is None else float(count*seconds_per_tile)
            if estimate is not None and estimate>180:
                rows.append(dict(hw=[h,w],tiles=int(count),status="NOT RUN",reason="projected >180s/image",estimate_s=estimate))
                break
            source=im.convert("RGB").resize((w,h),Image.Resampling.BICUBIC)
            x=torch.from_numpy(np.array(source)).permute(2,0,1).float()/255
            before=time.perf_counter()
            y,c,_,corners=tiled_predict(x,model,(tile,tile),(stride,stride),"hann")
            elapsed=time.perf_counter()-before
            rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=="darwin" else 1024)
            assert len(corners)==count and tuple(y.shape)==(3,h,w) and int(c.min())>0
            rows.append(dict(hw=[h,w],tiles=int(count),status="RUN",elapsed_s=elapsed,
                       peak_process_bytes=rss,estimate_s=estimate))
            seconds_per_tile=elapsed/count
            if elapsed>180 or rss>8*2**30:
                rows[-1]["stop"]="measured resource limit"
                break
    (args.out/"resolution.json").write_text(json.dumps(rows,indent=2)+"\n")
    print(rows)


if __name__=="__main__":
    main()
