"""Audit only Git-indexed files before a team commit/push. No credentials printed."""
from pathlib import Path
import subprocess,re,hashlib,json
root=Path(__file__).resolve().parents[1]
files=subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split('\0')
bad=[]; count=0
for name in filter(None,files):
    path=root/name; count+=1
    if any(x in Path(name).parts for x in ['.git','third_party','external','.venvs','__pycache__','runs','local']):bad.append((name,'excluded directory'))
    if path.suffix.lower() in ['.pth','.pt','.ckpt','.safetensors','.zip','.pem','.key','.pyc']:bad.append((name,'excluded artifact'))
    if path.stat().st_size>5*1024*1024:bad.append((name,'unexpected large file'))
    if path.suffix.lower()=='.png':continue
    text=path.read_text('utf-8',errors='replace')
    patterns=[r'[A-Za-z]:[\\/]+(?:Users|bigdata|windows|Program Files)',r'\bgh[pousr]_[A-Za-z0-9_]{20,}',r'\bgithub_pat_[A-Za-z0-9_]{20,}',r'BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY']
    for pattern in patterns:
        if re.search(pattern,text,re.I):bad.append((name,'private path or credential-like value'))
    if path.suffix=='.json':
        try:json.loads(text)
        except ValueError:bad.append((name,'invalid JSON'))
if bad:
    for item in bad: print(item)
    raise SystemExit('Audit failed; do not push.')
print('PASS: audited',count,'indexed files; no excluded artifacts, personal absolute paths, credential patterns or malformed JSON.')
