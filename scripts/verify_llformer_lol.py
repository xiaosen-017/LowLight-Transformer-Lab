from pathlib import Path
import csv, json, hashlib
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity
import argparse
p=argparse.ArgumentParser(description="Verify logged quality from saved eval15 PNGs")
p.add_argument("eval15",type=Path)
p.add_argument("run",type=Path)
args=p.parse_args()
r=args.run
rows=list(csv.DictReader(open(r/'metrics.csv')))
assert len(rows)==len(set(x['name'] for x in rows))==15
stats=[]
for row in rows:
    name=row['name']
    img=np.asarray(Image.open(r/name))
    gt=np.asarray(Image.open((args.eval15/'high')/name))
    assert hashlib.sha256((r/name).read_bytes()).hexdigest()==row['png_sha256']
    a=peak_signal_noise_ratio(gt,img,data_range=255)
    b=np.mean([structural_similarity(gt[:,:,i],img[:,:,i],data_range=255,
          gaussian_weights=True,win_size=11,sigma=1.5,use_sample_covariance=False) for i in range(3)])
    assert abs(a-float(row['psnr']))<1e-9 and abs(b-float(row['ssim']))<1e-9
    old=Path('results/m2/llformer')/name
    if old.exists():
        diff=np.abs(img.astype(int)-np.asarray(Image.open(old)).astype(int))
        stats.append(dict(name=name,max_uint8_difference=int(diff.max()),differing_values=int((diff!=0).sum())))
report={'paired_pngs_verified':len(rows),'metric_tolerance':1e-9,'m2_comparison':stats}
(r/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
