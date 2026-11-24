# LLFormer 分块正确性检查（#9、#10）

CPU 合成检查由作者从新目录复跑，JSON 与入库记录逐字节一致。实测与合成正确性分开报告；本项目没有第二位 LLFormer 复核人。

[正式结果、逐图指标和资源记录](../../results/m4/lol_eval15_v1/REPORT.md) · [LLFormer 的方法与上下文限制](../../docs/LLFORMER_METHOD.md)。

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

## 运行单张真实图

按 configs/upstreams.json 放置固定版本的 third_party/LLFormer，并按 configs/weights.json 放置 LOL 权重（入口会校验 SHA-256）。例如在两条命令中使用同一张本地 RGB 图、同一设备，仅改变融合：

```sh
python scripts/infer_llformer_tiled.py data/input.png runs/compare/mean.png --tile 128 128 --stride 64 64 --fusion mean
python scripts/infer_llformer_tiled.py data/input.png runs/compare/hann.png --tile 128 128 --stride 64 64 --fusion hann
```

这是缩小网格的 B1/融合对照入口，不是上游默认 UHD 基线，也不是正式计时脚本。正式实验另记输入、权重、上游与实验代码 SHA、设备、线程、失败、逐图指标与资源记录，见 docs/innovation_plan.md。

## 实验复跑入口

依赖可用 `python -m pip install -r environments/llformer-m3-m4-cpu.txt` 安装。使用 M3 已登记的 LOL-v1 原包与权重。除 eval15 外只解压开发图 `our485/{low,high}/2.png`。Torchvision 与当前 Torch 配套（此次 torchvision 0.29.2）。每条命令都创建新目录。开发集先跑 3×3 的均值融合可行性扫描；正式组别在 configs/m4_lol.json 预登记，不从已知 M3 整图得分或 M4 测试得分中挑选网格。每种正式组别在新进程中跑完 15 对；固定样本效率再单测，不能把探索阶段的一次测量当作正式耗时。

```sh
python scripts/check_llformer_b0.py runs/local-b0
python scripts/check_llformer_tiling.py runs/local-gate
python scripts/run_llformer_m4.py dev A data/lol/our485 runs/local-study/dev
for arm in A B C D; do
  python scripts/run_llformer_m4.py eval "$arm" data/lol/eval15 "runs/local-study/eval-$arm"
done
for arm in A B C D; do
  python scripts/run_llformer_m4.py bench "$arm" data/lol/eval15 "runs/local-study/bench-$arm"
done
python scripts/summarize_llformer_m4.py runs/local-study data/lol runs/local-study/verified
python scripts/inspect_llformer_edges.py runs/local-study data/lol/eval15 runs/m3-eval15-local runs/local-study/edges
python scripts/probe_llformer_b0_model.py data/lol/our485/low/2.png runs/local-b0-model
python scripts/scale_llformer_lol.py data/lol/our485/low/2.png runs/local-scale
```

开发图按编号顺序取第一张，不与 eval15 重叠。小分辨率全部用 CPU，无 CUDA 显存读数；benchmark 的 RSS 为进程生命周期高水位。扩展试验单用训练划分开发图的等比缩放版，只测可行性：D 组网格，长边 512→1024→2048，若按前一级每块时间推算下一级超过 180 秒/图则停止，不把推算值当实测时间。未经修改的上游 CLI 在本机的实际失败与仅设备适配的源码差异归档在 results/m4/b0。小图原始几何检查不冒充原版 CUDA UHD 推理。本组按任务负责人要求由作者自行复算，无第二人签字。

开发图 2.png 在 384 块下名义 0% 和 25% 重叠都只产生 4 块。补齐末端锚点后，两者的实际起点相同（行 0、16，列 0、224），逐图增强输出亦相同；不能将其当作两个独立的网格效果。
