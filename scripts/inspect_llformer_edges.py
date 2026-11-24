"""Inspect fixed seam cuts and create a local contact sheet for the registered 111.png."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


def axes(n):
    # Internal prediction tile starts and ends, no outer image borders.
    out=set()
    for t in [128,256]:
        end=max(t,(n+15)//16*16)-t
        for s in {*range(0,end+1,t//2),end}:
            out.update(v for v in [s,s+t] if 0<v<n)
    return sorted(out)


def inspect(pred,gt):
    h,w=gt.shape[:2]
    dy,dx=axes(h),axes(w)
    d=pred.astype(float)-gt.astype(float)
    # Gradient(pred)-gradient(gt) on the edge-straddling pixel pair.
    crossing=np.concatenate([abs(d[dy]-d[np.asarray(dy)-1]).reshape(-1),
                             abs(d[:,dx]-d[:,np.asarray(dx)-1]).reshape(-1)])
    my=np.any(abs(np.arange(h)[:,None]+0.5-np.asarray(dy))<2,axis=1)
    mx=np.any(abs(np.arange(w)[:,None]+0.5-np.asarray(dx))<2,axis=1)
    band=my[:,None]|mx[None,:]
    return dict(boundary_gradient_mae=float(crossing.mean()),edge_mae=float(abs(d[band]).mean()),
                interior_mae=float(abs(d[~band]).mean()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ["study","eval15","whole","out"]:
        p.add_argument(n,type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for arm in ["full","A","B","C","D"]:
        base=args.whole if arm=="full" else args.study/f"eval-{arm}"
        records=list(csv.DictReader((base/"metrics.csv").open()))
        for i,r in enumerate(records):
            name=r["name"]
            with Image.open(args.eval15/"high"/name) as gt, Image.open(base/(name if arm=="full" else f"{i:02d}_{name}")) as pred:
                arr=np.asarray(pred)
                ref=np.asarray(gt)
                stats=inspect(arr,ref)
                if arm!="full":
                    assert abs(float(r["edge_mae"])-stats["edge_mae"])<1e-9
                rows.append(dict(arm=arm,name=name,**stats))
    with (args.out/"edge_metrics.csv").open("x",newline="") as f:
        cw=csv.DictWriter(f,fieldnames=rows[0],lineterminator="\n")
        cw.writeheader()
        cw.writerows(rows)
    sheet=Image.new("RGB",(3*300,2*(200+28)),"white")
    draw=ImageDraw.Draw(sheet)
    name="111.png"
    for j,(label,path) in enumerate([("Input (LOL-v1)",args.eval15/"low"/name),
        ("GT (LOL-v1)",args.eval15/"high"/name),("Whole image",args.whole/name)]+
        [(arm,next((args.study/f"eval-{arm}").glob("*_"+name))) for arm in "ABD"]):
        with Image.open(path) as im:
            sheet.paste(im.resize((300,200),Image.Resampling.LANCZOS),(j%3*300,j//3*228+25))
        draw.text((j%3*300+6,j//3*228+6),label,fill="black")
    sheet.save(args.out/"overview-local.png")
    # Full-size corresponding crop for all arms. Marks are outside image data.
    sheet=Image.new("RGB",(3*256,2*193),"white")
    draw=ImageDraw.Draw(sheet)
    paths=[("GT",args.eval15/"high"/name),("Whole",args.whole/name)]+[
        (arm,next((args.study/f"eval-{arm}").glob("*_"+name))) for arm in "ABCD"]
    for j,(label,path) in enumerate(paths):
        x,y=(j%3*256,j//3*193)
        with Image.open(path) as im:
            sheet.paste(im.crop((64,96,320,256)),(x,y+25))
        draw.text((x+5,y+5),label,fill="black")
        for sx in axes(600):
            if 64<=sx<320:
                draw.line((x+sx-64,y+21,x+sx-64,y+24),fill="red")
    sheet.save(args.out/"fixed-crop-local.png")


if __name__=="__main__":
    main()
