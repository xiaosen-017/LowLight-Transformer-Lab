"""One image, registered LOL checkpoint, corrected grid, mean or Hann fusion."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import torch

from llformer_tiling import tiled_predict

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("image", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--tile", nargs=2, type=int, default=(128,128), metavar=("H","W"))
    p.add_argument("--stride", nargs=2, type=int, default=(64,64), metavar=("H","W"))
    p.add_argument("--fusion", choices=("mean","hann"), default="mean")
    p.add_argument("--device", choices=("cpu","cuda","mps"), default="cpu")
    args = p.parse_args()
    spec = next(x for x in json.loads((ROOT/"configs/weights.json").read_text())
                if x["model"] == "LLFormer")
    weight = ROOT/spec["path"]
    with weight.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest() != spec["sha256"]:
            p.error("checkpoint SHA-256 does not match the registered LOL weights")
    sys.path.insert(0,str(ROOT/"third_party/LLFormer"))
    from model.LLFormer import LLFormer
    model = LLFormer(inp_channels=3,out_channels=3,dim=16,num_blocks=[2,4,8,16],
                     num_refinement_blocks=2,heads=[1,2,4,8],ffn_expansion_factor=2.66,
                     bias=False,LayerNorm_type="WithBias",attention=True,skip=False)
    state = torch.load(weight,map_location="cpu",weights_only=True)["state_dict"]
    model.load_state_dict({k.removeprefix("module."):v for k,v in state.items()})
    model.to(args.device).eval()
    with Image.open(args.image) as src:
        rgb = torch.from_numpy(np.array(src.convert("RGB"))).permute(2,0,1)
    pred, *_ = tiled_predict(rgb.to(args.device,torch.float32)/255,model,
                             tuple(args.tile),tuple(args.stride),args.fusion)
    pixels = (pred.clamp(0,1)*255).round().byte().permute(1,2,0).cpu().numpy()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("xb") as f:
        Image.fromarray(pixels).save(f,format="PNG")


if __name__ == "__main__":
    main()
