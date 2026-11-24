"""CPU whole-frame latency and process peak RSS on one registered LOL sample."""
import argparse
import json
import platform
import resource
import statistics
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
import torch

from eval_llformer_lol import digest
from infer_llformer_tiled import ROOT, load_model


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("image",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--threads",type=int,default=4)
    args=p.parse_args()
    if sys.platform not in ("darwin","linux"):
        p.error("ru_maxrss units implemented for macOS and Linux only")
    args.out.mkdir(parents=True,exist_ok=False)
    sha=digest(args.image)
    expected=next(x for x in json.loads((ROOT/"configs/m2_samples.json").read_text())["samples"]
                  if x["name"]=="111.png")["sha256"]
    if sha!=expected:
        p.error("expected the registered official 111.png")
    torch.set_num_threads(args.threads)
    t=time.perf_counter()
    model=load_model("cpu")
    setup=time.perf_counter()-t
    rows=[]
    with torch.inference_mode():
        for i in range(6):
            start=time.perf_counter()
            with Image.open(args.image) as im:
                x=torch.from_numpy(np.array(im.convert("RGB"))).permute(2,0,1)[None].float()/255
            h,w=x.shape[2:]
            x=torch.nn.functional.pad(x,(0,(-w)%16,0,(-h)%16),"reflect")
            before=time.perf_counter()
            y=model(x)
            after=time.perf_counter()
            rgb=(y[0,:,:h,:w].clamp(0,1)*255).round().byte().permute(1,2,0).numpy()
            png=args.out/f"{i}.png"
            Image.fromarray(rgb).save(png)
            elapsed=time.perf_counter()-start
            rows.append(dict(index=i,phase="warmup" if i==0 else "measured",
                             forward_s=after-before,end_to_end_s=elapsed,output_sha256=digest(png)))
            del x,y,rgb
    assert len({r["output_sha256"] for r in rows})==1
    report=dict(device="cpu",machine=platform.machine(),system=platform.system(),
                os_release=platform.release(),threads=args.threads,input_sha256=sha,
                setup_s=setup,setup_scope="checkpoint hash, model import/build/load/eval",
                process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*
                    (1 if sys.platform=="darwin" else 1024),
                rss_scope="OS process lifetime high-water mark including load; not model-only",
                torch=str(torch.__version__),python=platform.python_version(), rows=rows)
    for key in ("forward_s","end_to_end_s"):
        vals=[r[key] for r in rows[1:]]
        report[key]=dict(median=statistics.median(vals),min=min(vals),max=max(vals))
    (args.out/"benchmark.json").write_text(json.dumps(report,indent=2)+"\n")
    print({k:report[k] for k in ("forward_s","end_to_end_s","process_peak_rss_bytes")})


if __name__=="__main__":
    main()
