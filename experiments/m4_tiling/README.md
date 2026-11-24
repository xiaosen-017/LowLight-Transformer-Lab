# LLFormer 分块正确性检查（#9、#10）

已完成 CPU 合成检查，等待另一位组员复核。官方权重的 B0/B1、配对质量指标和 #11 四组消融：NOT RUN。合成输入没有任何增强质量含义。

## 从仓库根目录复跑

使用 Python 3.12 和 PyTorch；本次测试环境及实现 SHA-256 见 [实测报告](../../results/m4/cpu_gate.json)。

```sh
python -m pip install torch==2.15.0 numpy pillow einops
python scripts/check_llformer_tiling.py runs/m4-my-check
python scripts/verify_m1_archive.py
```

输出目录必须是新目录。每例保存未裁剪的覆盖计数、权重和（npz）及 JSON 记录（尺寸、角点、误差）。固定 seed=17，不需要照片、模型或 GPU。6 种输入 × 2 种融合均通过，恒等重建最大绝对误差 3.58e-7。另验常数预测、与整图相同反射补边的单块局部算子，以及两个预测不同的块在指定交叠点的解析权重。

## 原版和修正版

B0 依据 configs/upstreams.json 固定的 LLFormer ed5e7bf 中 test_UHD.py：默认块 720×1280、步长 360×640。报告中 b0_geometry_only 只复算整数网格，不是运行原模型的失败日志。2160×3840 有 25 块，画布多出的边缘会被裁掉，原图没有漏覆盖；2176×3856 仍只有 25 块，裁回后漏 96,256 像素；400×600 没有合法分块。

B1 取实际补边尺寸，向右/下反射补到 16 的倍数且不小于块（长度为 1 的轴复制），补末端锚点并去重。均值与 Hann 共用完全相同的提块、逐块前向和浮点累积流程，均保留上游一次 stack 所有块的方式。Hann 为两个非周期一维窗的外积，再对二维权重设 0.001 下限。先验证覆盖再归一化，最后裁剪；只有写 PNG 时才限幅和量化。注意：stride=tile 若需要补末端锚点，尾部仍有重叠；零重叠对照必须检查实际计数。

## 第二人复核后运行真实模型

按 configs/upstreams.json 放置固定版本的 third_party/LLFormer，并按 configs/weights.json 放置 LOL 权重（入口会校验 SHA-256）。例如在两条命令中使用同一张本地 RGB 图、同一设备，仅改变融合：

```sh
python scripts/infer_llformer_tiled.py data/input.png runs/compare/mean.png --tile 128 128 --stride 64 64 --fusion mean
python scripts/infer_llformer_tiled.py data/input.png runs/compare/hann.png --tile 128 128 --stride 64 64 --fusion hann
```

这是缩小网格的 B1/融合对照入口，不是上游默认 UHD 基线，也不是正式计时脚本。正式实验另记输入、权重、上游与实验代码 SHA、设备、线程、失败、逐图指标与资源记录，见 docs/innovation_plan.md。
