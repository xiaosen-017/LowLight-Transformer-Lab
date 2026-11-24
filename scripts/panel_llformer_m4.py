"""Make a shareable 1:1 output-only comparison of the preregistered sample."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from inspect_llformer_edges import axes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("study","whole","output"):
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    sample="111.png"
    crops=[]
    for label in ("Whole","A","B","C","D"):
        file=(args.whole/sample if label=="Whole" else next((args.study/f"eval-{label}").glob("*_"+sample)))
        with Image.open(file) as im:
            assert im.size==(600,400) and im.mode=="RGB"
            crops.append(np.array(im.crop((64,96,320,256))))
    gap=7
    sheet=Image.new("RGB",(5*(256+gap)+gap,415),"#ffffff")
    draw=ImageDraw.Draw(sheet)
    draw.text((gap,6),"LOL-v1 111.png | same 256 x 160 output crop | red ticks: shared internal tile cuts",fill="#202733")
    for j,label in enumerate(["Whole image","A: 128 / mean","B: 256 / mean","C: 128 / Hann","D: 256 / Hann"]):
        x=gap+j*(256+gap)
        draw.text((x,29),label,fill="#172a3a")
        for cut in axes(600):
            if 64<=cut<320:
                draw.line((x+cut-64,45,x+cut-64,49),fill="#cc3322")
        sheet.paste(Image.fromarray(crops[j]),(x,50))
        for cut in axes(400):
            if 96<=cut<256:
                draw.line((x-4,50+cut-96,x-1,50+cut-96),fill="#cc3322")
        diff=np.minimum(255,np.abs(crops[j].astype(int)-crops[0])*4).astype("uint8")
        sheet.paste(Image.fromarray(diff),(x,245))
    draw.text((gap,221),"4 x absolute RGB difference from Whole (same scale for all panels; not error against GT)",fill="#202733")
    with args.output.open("xb") as f:
        sheet.save(f,format="PNG")


if __name__=="__main__":
    main()
