# -*- coding: utf-8 -*-
"""M4 消融实验冒烟测试：验证 4 组配置都能正常前向"""
import re
import sys
import torch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # 仓库根目录
ARCH = ROOT / "basicsr" / "models" / "archs" / "RetinexFormer_arch.py"

CONFIGS = [
    ("A0", 0, 0, "Baseline（无 ORF、无 IG-MSA）"),
    ("A1", 1, 0, "仅 ORF（无 IG-MSA）"),
    ("A2", 0, 1, "仅 IG-MSA（无 ORF）"),
    ("A3", 1, 1, "完整 RetinexFormer"),
]


def set_switch(igmsa, estimator):
    text = ARCH.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^ABL_IGMSA = \d", f"ABL_IGMSA = {igmsa}", text)
    text = re.sub(r"(?m)^ABL_ESTIMATOR = \d", f"ABL_ESTIMATOR = {estimator}", text)
    # 同步修改备份文件，保证 run_ablation 的模板一致
    ARCH.write_text(text, encoding="utf-8")


def build_model():
    # 强制重新导入，避免模块缓存
    for m in list(sys.modules):
        if "RetinexFormer_arch" in m:
            del sys.modules[m]
    import importlib
    import basicsr.models.archs.RetinexFormer_arch as arch
    importlib.reload(arch)
    return arch.RetinexFormer(
        in_channels=3, out_channels=3, n_feat=40,
        stage=1, num_blocks=[1, 2, 2])


def main():
    device = torch.device("cuda")
    x = torch.rand(1, 3, 64, 64, device=device)
    ok = True
    for name, ig, est, desc in CONFIGS:
        set_switch(ig, est)
        model = build_model().to(device).eval()
        with torch.no_grad():
            y = model(x)
        finite = bool(torch.isfinite(y).all())
        print(f"{name}  IG_MSA={ig} ORF(est)={est}  out={tuple(y.shape)} "
              f"range=[{y.min():.3f},{y.max():.3f}] finite={finite}  {desc}")
        if not finite or y.shape != x.shape:
            ok = False
        del model, y
        torch.cuda.empty_cache()
    # 恢复完整配置
    set_switch(1, 1)
    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
