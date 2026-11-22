"""Check archived M1 evidence without inference or additional experiments."""
from pathlib import Path
import json,hashlib
from PIL import Image
root=Path(__file__).resolve().parents[1]
records=json.loads((root/'docs/migration_manifest.json').read_text('utf-8'))
count=0
for record in records:
    if 'project_file' not in record: continue
    path=root/record['project_file']
    payload=path.read_bytes()
    if record.get('hash_mode')=='canonical_lf_text':payload=payload.replace(b'\r\n',b'\n')
    assert hashlib.sha256(payload).hexdigest()==record['sha256'],record['project_file']
    count+=1
for model in ['retinexformer','llformer']:
    with Image.open(root/'results/m1'/model/'111.png') as image:
        image.load(); assert image.size==(600,400) and image.mode=='RGB'
print('PASS:',count,'archived records match their hashes; both original M1 outputs are 600x400 RGB.')
