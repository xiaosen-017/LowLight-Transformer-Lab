# M4 · LLFormer 流式重叠融合与分辨率扩展

正式创新实验以已经合并的 15 对 LOL-v1 四组对照为基础。固定预训练模型和权重，先修正末端锚点与输出裁回，再比较块大小和融合权重。现有 [A/B/C/D 正式报告](../lol_eval15_v1/REPORT.md) 包含 60 张输出指标、接缝误差、重复计时与峰值内存。这里记录后续验证。

`scripts/run_m4_stream.py` 每次前向单个图块，立即将预测与权重累加到图像画布。均值和 Hann 共用相同网络预测、锚点和裁回规则。Hann 使用非周期窗外积和 0.001 正下限。锚点覆盖、有限值与正权重均参与运行检查。内存结构由保存全部图块与预测改为当前图块与每种融合的累加画布。

## 验证和实测

- Windows CPU、四线程、PyTorch 1.13.1+cpu，固定 LLFormer LOL-v1 官方权重，严格匹配 1485 个参数键。
- 先重跑原分块检查，12 个合成用例通过，恒等重建最大误差 `3.5763e-7`。流式算子与原堆叠实现在另外 8 个合成对照中完全一致。111.png 原尺寸两种融合的官方模型浮点输出也完全一致，`max_abs_error=0`。
- 真实图选用 M3 已登记的 111.png。2048 长边试验将同一低照度图及其 GT 一起用双三次插值放大，分别以原尺寸和放大尺寸计算指标。原尺寸采用 A/B/C/D 中 256/128 网格。2048 扩展使用 256/224 网格，以减少 CPU 计算。

| 输入 | 块大小/步长 | 融合 | 块数 | PSNR dB | Gaussian SSIM | 跨线梯度误差 ↓ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 600×400 原尺寸 | 256/128 | mean | 12 | 18.9821 | 0.87360 | — |
| 600×400 原尺寸 | 256/128 | hann | 12 | 18.8989 | 0.87460 | — |
| 2048×1365 双三次放大 | 256/224 | mean | 54 | 16.3274 | 0.82121 | 9.308 |
| 2048×1365 双三次放大 | 256/224 | hann | 54 | 16.2530 | 0.82659 | 2.234 |

在相同的 54 块预测上，Hann 比均值降低跨线梯度误差 **7.075** 个 8-bit 灰阶，提高 SSIM **0.00538**，同时 PSNR 下降 **0.0744 dB**，边界带 MAE 略升。接缝梯度改善与全图像素精度是不同的评价维度。峰值进程工作集 **0.712 GiB**，54 块一次前向并累计两种结果 **411.72 s**。开销属于单次资源实测，正式重复计时参见 A/B/C/D 报告。

## 重跑

命令从仓库根执行，输入和参考取 M3 的匹配测试对，权重与源码按仓库清单准备。

```text
python scripts/run_m4_stream.py runs/m4-check --threads 1
python scripts/run_m4_stream.py runs/m4-native --repo third_party/LLFormer --weights weights/llformer/model_bestPSNR.pth --input data/lol/eval15/low/111.png --gt data/lol/eval15/high/111.png --tile 256 --stride 128 --check-reference
python scripts/run_m4_stream.py runs/m4-scale --repo third_party/LLFormer --weights weights/llformer/model_bestPSNR.pth --input data/lol/eval15/low/111.png --gt data/lol/eval15/high/111.png --long-side 2048 --tile 256 --stride 224
```

当前课题的 LOL-v1 验收包括完整 15 对图消融、分块实现正确性和长边 2048 资源扩展。3840×2160/7680×4320 的原生 UHD 数据及对应权重实验仍属另一验证范围。官方 4K 测试集发布量约 69.7 GB，本机 C 盘检查可用约 50 GiB。尝试作者链接时 OneDrive 返回 HTTP 429，百度网盘要求提取交互。本次没有取得原生 UHD 数据的配对文件和完整验收结果。见 [UHD-LOL 官方数据页](https://taowangzj.github.io/projects/LLFormer/)。
