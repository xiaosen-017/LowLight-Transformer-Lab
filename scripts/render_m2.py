"""Compose measured M2 outputs into fixed-layout visual panels (no enhancement)."""
from pathlib import Path
import argparse,json,os
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser()
p.add_argument('--run',required=True,type=Path)
p.add_argument('--output',required=True,type=Path)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
run=(a.run if a.run.is_absolute() else root/a.run).resolve()
target=(a.output if a.output.is_absolute() else root/a.output).resolve()
record=json.loads((run/'run_record.json').read_text('utf-8'))
assert record['status']=='PASS','Complete actual inference before rendering.'
manifest=json.loads((root/'configs/m2_samples.json').read_text('utf-8'))
target.mkdir(parents=True,exist_ok=True)
font_candidates=[Path(os.environ.get('WINDIR',''))/'Fonts/arial.ttf',Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
font=next((ImageFont.truetype(str(f),24) for f in font_candidates if f.is_file()),ImageFont.load_default())
small=next((ImageFont.truetype(str(f),21) for f in font_candidates if f.is_file()),ImageFont.load_default())
columns=[('input','Input'),('retinexformer','Retinexformer'),('llformer','LLFormer')]
panels=[]
for sample in manifest['samples']:
    name=sample['name']; width,height=sample['width'],sample['height']
    canvas=Image.new('RGB',(3*width,height+88),(255,255,255)); draw=ImageDraw.Draw(canvas)
    draw.text((16,8),'LOL-v1  |  '+name,font=font,fill=(25,25,25))
    for col,(folder,label) in enumerate(columns):
        with Image.open(run/folder/name) as image:
            image.load(); assert image.mode=='RGB' and image.size==(width,height)
            canvas.paste(image,(col*width,76))
        draw.text((col*width+16,43),label,font=small,fill=(30,30,30))
    canvas.save(target/(Path(name).stem+'_comparison.png'))
    panels.append(canvas)
overview=Image.new('RGB',(panels[0].width,sum(x.height for x in panels)),(255,255,255))
y=0
for panel in panels:overview.paste(panel,(0,y));y+=panel.height
overview=overview.resize((900,round(overview.height/2)),Image.Resampling.LANCZOS)
overview.save(target/'overview.png')
print('Rendered five native-size three-column panels and 900-pixel web overview.')
