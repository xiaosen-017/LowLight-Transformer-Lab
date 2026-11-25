"""Create auditable ablation configurations in disposable upstream copies."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import torch
import yaml

ROOT = Path(__file__).resolve().parents[3]
ARCH = Path('basicsr/models/archs/RetinexFormer_arch.py')
OPTIONS = Path('Options/RetinexFormer_LOL_v1.yml')
GROUPS = {'A0': (False, False), 'A1': (True, False),
          'A2': (False, True), 'A3': (True, True)}


def patched_arch(source, orf, ig_msa):
    if orf and ig_msa:
        return source
    source = source.replace('\r\n', '\n')
    def replace_once(old, new):
        nonlocal source
        if source.count(old) != 1:
            raise ValueError('Pinned upstream code does not match ablation anchor')
        source = source.replace(old, new)

    if not ig_msa:
        replace_once('            x = attn(x, illu_fea_trans=illu_fea.permute(0, 2, 3, 1)) + x\n', '')
    if not orf:
        replace_once('        v = v * illu_attn\n', '')
        replace_once('        illu_fea, illu_map = self.estimator(img)\n'
                     '        input_img = img * illu_map + img\n',
                     '        channels = self.estimator.conv1.out_channels\n'
                     '        illu_fea = img.new_ones(img.shape[0], channels, *img.shape[-2:])\n'
                     '        input_img = img\n')
    return source


def import_arch(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dataset_options(config, data):
    for name, source, count in [('train', 'our485', 485), ('val', 'eval15', 15)]:
        inputs, targets = data/source/'low', data/source/'high'
        pairs = {file.name for file in inputs.glob('*.png')}
        if len(pairs) != count or pairs != {file.name for file in targets.glob('*.png')}:
            raise ValueError('Expected %s matched PNG pairs in %s' % (count, source))
        config['datasets'][name].update(dataroot_gt=str(targets), dataroot_lq=str(inputs))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upstream', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--train', action='store_true', help='Run the four CUDA training jobs after smoke testing')
    args = parser.parse_args()
    if args.train and (args.data is None or not torch.cuda.is_available()):
        parser.error('--train requires the complete LOL-v1 training and validation splits and CUDA')
    upstream = args.upstream.resolve()
    pin = json.loads((ROOT/'configs/upstreams.json').read_text())['Retinexformer']['commit']
    actual = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != pin:
        raise ValueError('Expected the pinned Retinexformer commit ' + pin)
    bundle = subprocess.check_output(['git', '-C', str(upstream), 'archive', '--format=zip', pin])
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        original = archive.read(ARCH.as_posix()).decode('utf-8')
        config = yaml.safe_load(archive.read(OPTIONS.as_posix()))
    if args.train:
        dataset_options(config, args.data.resolve())
    network = dict(config['network_g'])
    network.pop('type')
    args.out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    image = torch.rand(1, 3, 64, 64, generator=torch.Generator().manual_seed(17))
    report = []
    for group, (orf, ig_msa) in GROUPS.items():
        target = args.out.resolve()/group
        with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
            archive.extractall(target)
        path = target/ARCH
        revision = patched_arch(original, orf, ig_msa)
        path.write_bytes(revision.encode('utf-8'))
        torch.manual_seed(100)
        model = import_arch(path, 'retinex_'+group).RetinexFormer(**network).eval()
        with torch.inference_mode():
            output = model(image)
        if output.shape != image.shape or not torch.isfinite(output).all():
            raise ValueError('Ablation forward failed: ' + group)
        if group == 'A3' and revision != original:
            raise AssertionError('Complete configuration must preserve the upstream architecture')
        record = dict(group=group, ORF=orf, IG_MSA=ig_msa, upstream=pin,
                      arch_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      smoke_shape=list(output.shape), smoke='PASS',
                      gate_without_orf='multiplicative gate bypassed at every level', training='not_run')
        if args.train:
            config['name'] = 'RetinexFormer_LOLv1_'+group+'_5000'
            config['num_gpu'] = 1
            config['manual_seed'] = 100
            config['train']['total_iter'] = 5000
            config['val']['val_freq'] = 1000
            config['path'].update(pretrain_network_g=None, resume_state=None)
            config_path = target/'Options/ablation_lolv1.yml'
            config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
            record['config_sha256'] = hashlib.sha256(config_path.read_bytes()).hexdigest()
            with (target/'ablation_train.log').open('w', encoding='utf-8') as log:
                result = subprocess.run([sys.executable, '-m', 'basicsr.train', '--opt', str(config_path)],
                                        cwd=target, env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                                        stdout=log, stderr=subprocess.STDOUT)
            record['training'] = 'completed' if result.returncode == 0 else 'failed'
            record['exit_code'] = result.returncode
        report.append(record)
        (args.out/'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print(group, 'ORF', orf, 'IG-MSA', ig_msa, record['smoke'], record['training'], flush=True)
        if args.train:
            result.check_returncode()


if __name__ == '__main__':
    main()
