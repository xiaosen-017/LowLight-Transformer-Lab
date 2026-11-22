## Ultra-High-Definition Low-Light Image Enhancement: A Benchmark and Transformer-Based Method
## Tao Wang, Kaihao Zhang, Tianrun Shen, Wenhan Luo, Bjorn Stenger, Tong Lu
## https://arxiv.org/pdf/2212.11548.pdf

import torch
import torchvision.transforms.functional as TF
import torch.nn.functional as F
from PIL import Image
import os
from skimage import img_as_ubyte
from collections import OrderedDict
from natsort import natsorted
from glob import glob

import cv2
import argparse
from time import perf_counter
from model.LLFormer import LLFormer
parser = argparse.ArgumentParser(description='Demo Low-light Image Enhancement')
parser.add_argument('--input_dir', default='./datasets/LOL/test/low/', type=str, help='Input images')
parser.add_argument('--result_dir', default='./results/LOL/', type=str, help='Directory for results')
parser.add_argument('--weights',
                    default='./checkpoints/LOL/models/model_bestPSNR.pth', type=str,
                    help='Path to weights')

parser.add_argument('--device', default='cpu', choices=['cpu','cuda'])
parser.add_argument('--threads', type=int, default=4)
args = parser.parse_args()
device = torch.device(args.device)
torch.set_num_threads(args.threads)
print('torch:', torch.__version__, 'device:', device, 'threads:', torch.get_num_threads(), flush=True)


def save_img(filepath, img):
    cv2.imwrite(filepath, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))


def load_checkpoint(model, weights):
    checkpoint = torch.load(weights, map_location='cpu')
    print('checkpoint fields:', list(checkpoint), flush=True)
    try:
        status = model.load_state_dict(checkpoint["state_dict"], strict=True)
    except:
        state_dict = checkpoint["state_dict"]
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = k[7:]  # remove `module.`
            new_state_dict[name] = v
        status = model.load_state_dict(new_state_dict, strict=True)

    print('strict checkpoint load:', status, 'state tensors:', len(checkpoint['state_dict']), flush=True)

inp_dir = args.input_dir
out_dir = args.result_dir

os.makedirs(out_dir, exist_ok=True)

files = natsorted(#glob(os.path.join(inp_dir, '*.jpg')) +
                  glob(os.path.join(inp_dir, '*.JPG'))
                  + glob(os.path.join(inp_dir, '*.png'))
                  + glob(os.path.join(inp_dir, '*.PNG')))

# Windows glob is case-insensitive: *.png + *.PNG otherwise duplicates inputs.
files = list(dict.fromkeys(files))
if len(files) == 0:
    raise Exception(f"No files found at {inp_dir}")

# Load corresponding models architecture and weights

model = LLFormer(inp_channels=3,out_channels=3,dim = 16,num_blocks = [2,4,8,16],num_refinement_blocks = 2,heads = [1,2,4,8],ffn_expansion_factor = 2.66,bias = False,LayerNorm_type = 'WithBias',attention=True,skip = False)
model.to(device)

load_started = perf_counter()
load_checkpoint(model, args.weights)
print('weight_load_seconds:', perf_counter()-load_started, flush=True)
model.eval()

print('restoring images......')

mul = 16
index = 0
psnr_val_rgb = []
for file_ in files:
    img = Image.open(file_).convert('RGB')
    input_ = TF.to_tensor(img).unsqueeze(0).to(device)

    # Pad the input if not_multiple_of 16
    h, w = input_.shape[2], input_.shape[3]
    H, W = ((h + mul) // mul) * mul, ((w + mul) // mul) * mul
    padh = H - h if h % mul != 0 else 0
    padw = W - w if w % mul != 0 else 0
    input_ = F.pad(input_, (0, padw, 0, padh), 'reflect')
    forward_started = perf_counter()
    with torch.no_grad():
        restored = model(input_)

    elapsed = perf_counter()-forward_started
    if device.type == 'cuda':
        torch.cuda.synchronize()
        elapsed = perf_counter()-forward_started
    assert torch.isfinite(restored).all()
    print('input:', file_, 'original_size:', (w,h), 'padded_shape:', tuple(input_.shape), 'forward_seconds:', elapsed, flush=True)
    restored = torch.clamp(restored, 0, 1)
    restored = restored[:, :, :h, :w]
    restored = restored.permute(0, 2, 3, 1).cpu().detach().numpy()
    restored = img_as_ubyte(restored[0])

    f = os.path.splitext(os.path.split(file_)[-1])[0]
    save_img((os.path.join(out_dir, f + '.png')), restored)
    index += 1
    print('%d/%d' % (index, len(files)))

print(f"Files saved at {out_dir}")
print('finish !')
