# -*- coding: utf-8 -*-
"""M4 消融实验图表：PSNR 曲线对比 + 最佳 PSNR 柱状图"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[3]  # 仓库根目录
ARCHIVE = ROOT / "runs_ablation"
OUT_FIG = ROOT / "m4_figures"
OUT_FIG.mkdir(exist_ok=True)

# 中文字体
for name in ("Microsoft YaHei", "SimHei", "SimSun"):
    if any(name == f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [name]
        break
plt.rcParams["axes.unicode_minus"] = False

curves = json.loads((ARCHIVE / "psnr_curves.json").read_text(encoding="utf-8"))
rows = list(__import__("csv").DictReader(
    open(ARCHIVE / "summary.csv", encoding="utf-8-sig")))

LABEL = {
    "A0": "A0 Baseline (无 ORF / 无 IG-MSA)",
    "A1": "A1 仅 ORF",
    "A2": "A2 仅 IG-MSA",
    "A3": "A3 完整 RetinexFormer",
}
COLOR = {"A0": "#8C8C8C", "A1": "#5B8FF9", "A2": "#F6BD16", "A3": "#E8684A"}
STYLE = {"A0": "--", "A1": "-.", "A2": ":", "A3": "-"}

# ---------- 图 1：四组 PSNR 曲线 ----------
fig, ax = plt.subplots(figsize=(8, 4.4), dpi=220)
for g in ("A0", "A1", "A2", "A3"):
    pts = curves.get(g) or []
    if not pts:
        continue
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, marker="o", markersize=5, linewidth=2,
            color=COLOR[g], linestyle=STYLE[g], label=LABEL[g])
    bx, by = max(pts, key=lambda p: p[1])
    ax.annotate(f"{by:.2f}", (bx, by), textcoords="offset points",
                xytext=(0, 9), fontsize=8, color=COLOR[g], ha="center")

ax.set_xlabel("Iteration")
ax.set_ylabel("Validation PSNR (dB)")
ax.set_title("M4 短程消融实验：四组验证 PSNR 对比（5,000 步）")
ax.grid(alpha=0.3)
ax.legend(fontsize=8, loc="lower right")
ax.set_xticks([1000, 2000, 3000, 4000, 5000])
plt.tight_layout()
f1 = OUT_FIG / "m4_ablation_psnr_curves.png"
plt.savefig(f1, dpi=220, bbox_inches="tight")
print("saved", f1)

# ---------- 图 2：最佳 PSNR 柱状图 ----------
fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=220)
groups = [r["实验"] for r in rows]
best = [float(r["最佳PSNR"]) for r in rows]
bars = ax.bar(groups, best, color=[COLOR[g] for g in groups], width=0.6)
base = min(best)
for b, v in zip(bars, best):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"{v:.2f}",
            ha="center", fontsize=9)
ax.set_ylim(base - 0.8, max(best) + 0.6)
ax.set_ylabel("Best PSNR (dB)")
ax.set_title("M4 消融实验：各组最佳 PSNR（5,000 步短程训练）")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
f2 = OUT_FIG / "m4_ablation_best_psnr.png"
plt.savefig(f2, dpi=220, bbox_inches="tight")
print("saved", f2)

# ---------- 打印关键差值 ----------
d = {r["实验"]: float(r["最佳PSNR"]) for r in rows}
print("\n相对 A0 的提升：")
for g in ("A1", "A2", "A3"):
    print(f"  {g} - A0 = +{d[g] - d['A0']:.4f} dB")
print(f"  完整( A3 ) - 无IGMSA( A1 ) = +{d['A3'] - d['A1']:.4f} dB")
print(f"  完整( A3 ) - 无ORF( A2 ) = +{d['A3'] - d['A2']:.4f} dB")
