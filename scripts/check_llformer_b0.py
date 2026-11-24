"""Replay the pinned upstream patch helpers on synthetic data, without its CLI."""
import argparse
import ast
import difflib
import json
import subprocess
from pathlib import Path

import torch
from torchvision.transforms.functional import crop

ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "third_party/LLFormer"


def helpers(device_compat):
    spec = json.loads((ROOT / "configs/upstreams.json").read_text())["LLFormer"]
    src = subprocess.check_output(["git","-C",str(UP),"show",spec["commit"]+":test_UHD.py"]).decode().replace("\r\n","\n")
    tree = ast.parse(src)
    parts = [ast.get_source_segment(src,node) for node in tree.body if
             isinstance(node,ast.FunctionDef) and node.name in {"image_to_patches","patches_to_image"}]
    assert len(parts)==2
    original="\n\n".join(parts)+"\n"
    adjusted=original.replace(".cuda()",".to(patches[0].device)")
    assert original.count(".cuda()")==2
    ns={"torch":torch,"crop":crop}
    exec(compile(adjusted if device_compat else original,"<pinned upstream patch helpers>","exec"),ns)
    return ns, list(difflib.unified_diff(original.splitlines(True),adjusted.splitlines(True),
                                         fromfile="B0",tofile="B0-device-only",n=0))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("output",type=Path)
    out=p.parse_args().output
    out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(4)
    records=[]
    for compat in (False,True):
        ns,diff=helpers(compat)
        for h,w in [(719,1279),(720,1280),(736,1296),(400,600),(2160,3840)]:
            H,W=(h//16+1)*16,(w//16+1)*16
            ph,pw=720,1280
            device=("cuda" if not compat and torch.cuda.is_available() else "cpu")
            row=dict(compat=compat,device=device,hw=[h,w],canvas=[H,W])
            try:
                x=torch.ones(3,h,w,device=device)
                x=torch.nn.functional.pad(x,(0,(-w)%16,0,(-h)%16),"reflect")
                patches,corners=ns["image_to_patches"](x,(ph,pw),(360,640))
                y=ns["patches_to_image"](patches,corners,(ph,pw),(3,H,W))
                crop_y=y[0,:h,:w]
                valid=crop_y.isfinite()
                row.update(tiles=len(corners),nonfinite_canvas=int((~y[0].isfinite()).sum()),
                           nonfinite_original=int((~valid).sum()),
                           constant_error_on_covered=float((crop_y[valid]-1).abs().max()))
                assert row["nonfinite_original"]==(h*w-ph*pw if (h,w)==(736,1296) else 0)
            except (RuntimeError,AssertionError) as exc:
                msg=str(exc)
                expected=("non-empty TensorList" in msg if (h,w)==(400,600) else
                    not compat and device=="cpu" and ("CUDA" in msg or "NVIDIA" in msg))
                if not expected:
                    raise
                row["expected_exception"]=type(exc).__name__+": "+msg
            records.append(row)
    (out/"b0-device.diff").write_text("".join(diff))
    (out/"outcomes.json").write_text(json.dumps(records,indent=2)+"\n")
    print(json.dumps(records))


if __name__=="__main__":
    main()
