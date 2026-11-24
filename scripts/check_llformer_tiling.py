"""CPU correctness gate. No photographs, checkpoints or quality metrics."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import torch
from llformer_tiling import tiled_predict


def b0_geometry(h, w):
    # Integer geometry only, transcribed from pinned test_UHD.py.
    canvas = [(d // 16 + 1) * 16 for d in (h, w)]
    padded = [((d + 15) // 16) * 16 for d in (h, w)]
    ends = [list(range(0, d-t+1, s)) for d, t, s in
            zip(padded, (720, 1280), (360, 640))]
    covered = (min(h, ends[0][-1]+720) * min(w, ends[1][-1]+1280)
               if all(ends) else 0)
    return dict(input_hw=[h, w], canvas_hw=canvas, padded_hw=padded,
                tiles=len(ends[0])*len(ends[1]), missing_after_crop=h*w-covered)


def check(out):
    out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    rng = torch.Generator().manual_seed(17)
    report = dict(torch=str(torch.__version__), python=platform.python_version(),
                  device="cpu", dtype="float32", seed=17, threads=1,
                  b0_geometry_only=[b0_geometry(*hw) for hw in
                                    [(2160,3840),(2176,3856),(400,600)]], cases=[])
    for name, hw, tile, stride in [
        ("odd", (79,113), (32,48), (16,24)),
        ("constant_axis", (1,7), (32,48), (16,24)),
        ("single", (31,47), (32,48), (32,48)),
        ("no_overlap", (64,96), (32,48), (32,48)),
        ("shifted_tail", (80,112), (32,48), (32,48)),
        ("lol_size", (400,600), (128,128), (64,64)),
    ]:
        image = torch.rand(3,*hw,generator=rng)
        for fusion in ("mean","hann"):
            pred, counts, weights, corners = tiled_predict(image, lambda x:x, tile, stride, fusion)
            const, *_ = tiled_predict(image, lambda x:torch.full_like(x,0.37), tile, stride, fusion)
            error = (pred-image).abs().max().item()
            cerror = (const-0.37).abs().max().item()
            assert pred.shape == image.shape and max(error,cerror) <= 1e-6
            assert counts.min() > 0 and weights.isfinite().all() and weights.min() > 0
            assert corners[-1] == (counts.shape[0]-tile[0],counts.shape[1]-tile[1])
            if name == "no_overlap":
                assert counts.max() == 1
            if name == "single":
                # Local operator sensitive to padding and all three RGB channels.
                op = lambda x: torch.nn.functional.avg_pool2d(x,3,1,1)
                reference = op(torch.nn.functional.pad(image[None], (0,1,0,1), "reflect"))
                actual, *_ = tiled_predict(image,op,tile,stride,fusion)
                torch.testing.assert_close(actual,reference[0,:,:hw[0],:hw[1]],rtol=0,atol=1e-6)
            np.savez_compressed(out/f"{name}_{fusion}.npz", counts=counts.numpy(),weights=weights.numpy())
            report["cases"].append(dict(name=name, hw=hw, tile=tile, stride=stride, fusion=fusion,
                corners=corners, identity_max_error=error, constant_max_error=cerror,
                count_range=[counts.min().item(),counts.max().item()],
                weight_range=[weights.min().item(),weights.max().item()]))
    # Two tiles disagree in their overlap. Use the first input pixel as the
    # per-tile prediction (0 and 1) and check the analytic blend at x=20.
    import math
    ramp = torch.arange(48).expand(3,32,48).float()/16
    op = lambda x: x[:,:,:1,:1].expand_as(x)
    values = {}
    hann = lambda i: 0.5*(1-math.cos(2*math.pi*i/31))
    a, b = [max(1e-3,hann(15)*hann(i)) for i in (20,4)]
    for fusion, expected in [("mean",0.5),("hann",b/(a+b))]:
        actual, *_ = tiled_predict(ramp,op,(32,32),(16,16),fusion)
        value = actual[0,15,20].item()
        assert abs(value-expected) <= 1e-6
        values[fusion] = dict(expected=expected, actual=value)
    report["disagreeing_tiles"] = values
    report["source_sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (Path(__file__),Path(__file__).with_name("llformer_tiling.py"))}
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(f"PASS: {len(report['cases'])} CPU cases; maximum identity error",
          max(c["identity_max_error"] for c in report["cases"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out",type=Path)
    check(parser.parse_args().out)
