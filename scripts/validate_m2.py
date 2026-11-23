"""Validate the frozen M2 visual sample outputs without GT quality metrics."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
run=(a.run if a.run.is_absolute() else root/a.run).resolve()
target=(a.output if a.output.is_absolute() else root/a.output).resolve()
manifest=json.loads((root/'configs/m2_samples.json').read_text('utf-8'))
record=json.loads((run/'run_record.json').read_text('utf-8'));assert record['status']=='PASS'
scenes=[]
for sample in manifest['samples']:
    name=sample['name'];source=run/'input'/name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==sample['sha256']
    with Image.open(source) as image:original=np.array(image.convert('RGB'))
    outputs=[]
    for model in ['retinexformer','llformer']:
        file=run/model/name
        with Image.open(file) as image:
            image.load();assert image.mode=='RGB' and image.size==(sample['width'],sample['height'])
            arr=np.array(image)
        assert arr.dtype==np.uint8 and arr.std()>1 and arr.min()<arr.max() and not np.array_equal(arr,original)
        item={'model':model,'file':'results/m2/'+model+'/'+name,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'width':image.width,'height':image.height,'mode':'RGB','pixel_min':int(arr.min()),'pixel_max':int(arr.max()),'pixel_std':float(arr.std()),'decode_and_shape':'PASS','different_from_input':True}
        if name=='111.png':
            m1=root/'results/m1'/model/name
            item['same_bytes_as_m1']=hashlib.sha256(m1.read_bytes()).hexdigest()==item['sha256'];assert item['same_bytes_as_m1']
        outputs.append(item)
    scenes.append({'input':name,'input_sha256':sample['sha256'],'outputs':outputs})
result={'status':'PASS','input_count':5,'model_output_count':10,'settings':manifest['preprocessing'],'scenes':scenes,'scope':'Image decoding, dimensions, dtype and integrity checks; no GT-based quality metrics computed.'}
target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: five matched inputs and ten nonempty, decodable, original-size RGB outputs; M1 scene unchanged.')
