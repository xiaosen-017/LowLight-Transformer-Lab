"""M2: run both existing official-weight M1 entries on a frozen five-image list.
Uses independent existing interpreters and does not install packages or train.
"""
import argparse,json,hashlib,subprocess,os,sys,time,shutil,datetime
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--ret-python',required=True,type=Path)
p.add_argument('--ll-python',required=True,type=Path)
p.add_argument('--ret-repo',type=Path,default=Path('third_party/Retinexformer'))
p.add_argument('--ll-repo',type=Path,default=Path('third_party/LLFormer'))
p.add_argument('--ret-weights',type=Path,default=Path('weights/retinexformer/LOL_v1.pth'))
p.add_argument('--ll-weights',type=Path,default=Path('weights/llformer/model_bestPSNR.pth'))
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
def absolute(value):return (value if value.is_absolute() else root/value).resolve()
for key in ['ret_python','ll_python','ret_repo','ll_repo','ret_weights','ll_weights','output']:setattr(a,key,absolute(getattr(a,key)))
if a.output.exists() and any(a.output.iterdir()):raise SystemExit('Choose a new run directory; existing experiment is preserved.')
def digest(file):return hashlib.sha256(file.read_bytes()).hexdigest()
manifest=json.loads((root/'configs/m2_samples.json').read_text('utf-8'))
upstreams=json.loads((root/'configs/upstreams.json').read_text('utf-8'))
weights=json.loads((root/'configs/weights.json').read_text('utf-8'))
for model,repo,weight,python in [('Retinexformer',a.ret_repo,a.ret_weights,a.ret_python),('LLFormer',a.ll_repo,a.ll_weights,a.ll_python)]:
    assert python.is_file(),'Interpreter missing: use a prepared independent environment.'
    spec=next(x for x in weights if x['model']==model)
    assert weight.is_file(),'Official weight missing: see weights/README.md'
    assert weight.stat().st_size==spec['size'] and digest(weight)==spec['sha256'],'Wrong or incomplete checkpoint.'
    assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip()==upstreams[model]['commit']
    assert not subprocess.check_output(['git','-C',str(repo),'diff','--name-only']).strip(),'Use clean official upstream.'
for sample in manifest['samples']:
    original=a.ret_repo/sample['upstream_path']
    assert original.is_file() and digest(original)==sample['sha256'],sample['name']
a.output.mkdir(parents=True)
inputs=a.output/'input'; inputs.mkdir()
for sample in manifest['samples']:shutil.copy2(a.ret_repo/sample['upstream_path'],inputs/sample['name'])
record={'experiment':'M2','started_at':datetime.datetime.now().astimezone().isoformat(),'git_commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD']).decode().strip(),'manifest_sha256':digest(root/'configs/m2_samples.json'),'upstreams':upstreams,'weights':weights,'settings':manifest['preprocessing'],'commands':[],'status':'RUNNING','samples':[x['name'] for x in manifest['samples']]}
record['script_sha256']={x:digest(root/x) for x in ['scripts/run_m2.py','scripts/infer_retinexformer.py','patches/test_llformer_cpu.py']}
def save(): (a.output/'run_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
save()
env=dict(os.environ,PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
def run(model,command,log):
    print('RUN',model,' '.join(str(x) for x in command),flush=True)
    task={'model':model,'argv':[str(x) for x in command],'log':str(log),'started_at':datetime.datetime.now().astimezone().isoformat()}
    record['commands'].append(task); save()
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run([str(x) for x in command],env=env,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
    task['exit_code']=result.returncode
    if result.returncode:
        record['status']='FAILED';save();print(log.read_text('utf-8'),flush=True);raise SystemExit(result.returncode)
    print('PASS',model,log.name,flush=True);save()
retout=a.output/'retinexformer';retout.mkdir();logs=a.output/'logs';logs.mkdir()
for sample in manifest['samples']:
    env['PYTHONPATH']=str(a.ret_repo)
    run('Retinexformer',[a.ret_python,'-u',root/'scripts/infer_retinexformer.py','--repo',a.ret_repo,'--weights',a.ret_weights,'--input',inputs/sample['name'],'--output',retout/sample['name'],'--threads','4'],logs/('retinexformer_'+sample['name']+'.log'))
env['PYTHONPATH']=str(a.ll_repo)
run('LLFormer',[a.ll_python,'-u',root/'patches/test_llformer_cpu.py','--input_dir',inputs,'--result_dir',a.output/'llformer','--weights',a.ll_weights,'--device','cpu','--threads','4'],logs/'llformer.log')
record['status']='PASS';record['completed_at']=datetime.datetime.now().astimezone().isoformat();save()
print('M2 PASS: 5 matched inputs, 5 Retinexformer outputs and 5 LLFormer outputs.',flush=True)
