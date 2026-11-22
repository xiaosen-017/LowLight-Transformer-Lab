"""One-image CPU inference using the original Retinexformer architecture.
Preprocessing/loading/padding/save follow official app.py (gamma=1, no ensemble).
"""
import argparse
import importlib.util
import json
import hashlib
import time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
import yaml
from PIL import Image, ImageOps

p=argparse.ArgumentParser()
p.add_argument('--repo',type=Path,required=True)
p.add_argument('--weights',type=Path,required=True)
p.add_argument('--input',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--threads',type=int,default=4)
a=p.parse_args()
torch.set_num_threads(a.threads)
print('Python executable:',__import__('sys').executable,flush=True)
print('torch:',torch.__version__,'CUDA available:',torch.cuda.is_available(),'device: cpu','threads:',torch.get_num_threads(),flush=True)
spec=importlib.util.spec_from_file_location('official_retinexformer_arch',a.repo/'basicsr/models/archs/RetinexFormer_arch.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
network=dict(yaml.safe_load((a.repo/'Options/RetinexFormer_LOL_v1.yml').read_text(encoding='utf-8'))['network_g'])
assert network.pop('type')=='RetinexFormer'
start=time.perf_counter()
checkpoint=torch.load(a.weights,map_location='cpu',weights_only=True)
state=checkpoint.get('params_ema',checkpoint.get('params',checkpoint))
state={(k[7:] if k.startswith('module.') else k):v for k,v in state.items()}
model=mod.RetinexFormer(**network)
status=model.load_state_dict(state,strict=True)
model.eval()
print('checkpoint fields:',list(checkpoint)[:10], 'state tensors:',len(state),'strict load:',status,flush=True)
load_seconds=time.perf_counter()-start
image=ImageOps.exif_transpose(Image.open(a.input)).convert('RGB')
arr=np.array(image,dtype=np.float32)/255.0
x=torch.from_numpy(arr).permute(2,0,1).unsqueeze(0)
h,w=x.shape[-2:]; ph,pw=(-h)%4,(-w)%4
x=F.pad(x,(0,pw,0,ph),mode='reflect' if h>ph and w>pw else 'replicate')
print('input:',image.size,'RGB; padded tensor:',tuple(x.shape),'gamma=1; brightness=1; ensemble=False; resize=False',flush=True)
start=time.perf_counter()
with torch.inference_mode():
    y=model(x)[...,:h,:w].clamp(0,1)
seconds=time.perf_counter()-start
assert torch.isfinite(y).all()
out=np.rint(y[0].permute(1,2,0).numpy()*255).astype(np.uint8)
a.output.parent.mkdir(parents=True,exist_ok=True)
Image.fromarray(out).save(a.output)
stats={'model':'Retinexformer','device':'cpu','threads':a.threads,'weights_sha256':hashlib.sha256(a.weights.read_bytes()).hexdigest(),'state_tensors':len(state),'strict_load':str(status),'input':str(a.input.resolve()),'output':str(a.output.resolve()),'input_size':list(image.size),'output_size':list(Image.open(a.output).size),'mode':'RGB','load_seconds':load_seconds,'forward_seconds':seconds,'input_mean_rgb':arr.mean(axis=(0,1)).tolist(),'output_mean_rgb':(out/255).mean(axis=(0,1)).tolist(),'output_min':int(out.min()),'output_max':int(out.max()),'mean_absolute_change_0_255':float(np.abs(out.astype(float)-np.array(image).astype(float)).mean())}
a.output.with_suffix('.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False,indent=2),flush=True)
print('SUCCESS: real official-weight local forward and PNG saved',flush=True)
