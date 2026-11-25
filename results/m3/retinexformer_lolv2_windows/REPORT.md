# M3 · Retinexformer 的 LOL-v2 定量复现

使用作者发布的 LOLv2.zip 中 Real_captured 和 Synthetic 的完整 Test 划分，各 100 对。两个划分分别加载作者发布的匹配权重，并使用各自的官方网络配置。运行环境为 Windows、Ryzen 5 5625U CPU、四线程、Python 3.7.9、PyTorch 1.13.1+cpu、scikit-image 0.15.0。输入保留原始尺寸，反射补齐到 4 的倍数，推理后裁回。PSNR 在 [0,1] 浮点结果上计算，SSIM 按 8-bit RGB 逐通道 Gaussian 窗计算。GT 亮度校准和自集成均关闭。

| 测试划分 | 图对数 | ICCV 2023 表 1 PSNR / SSIM | 本地实测 PSNR / SSIM |
| --- | ---: | --- | --- |
| LOL-v2 Real | 100 | 22.80 / 0.840 | 22.79550 / 0.839669 |
| LOL-v2 Synthetic | 100 | 25.67 / 0.930 | 25.67270 / 0.929550 |

两组指标按论文精度均吻合。两套权重分别严格匹配 122 个参数键。逐图 SHA-256、指标及运行日志保存在结果目录。作者测试压缩包约 1.05 GB。本地以 HTTP Range 读取 ZIP 目录和测试文件所在分段，按目录记录逐个验证文件长度和 CRC32。下载的中央目录与结尾记录 SHA-256 为 `d9962f589217d9029f41e28a6bcb9ea2939530ee30ca1018a6f7dce4ea47c657`。两套权重均按作者模型仓库固定提交给出的 LFS SHA-256 核验。完整评估只有正常 RGB 输入与匹配参考参与，所有分数取逐图算术均值。

运行记录的脚本哈希取自 Windows 实际执行文件。Git 将 Python 文件换行归一为 LF，归一后 `eval_retinex_lolv2.py` 的 SHA-256 为 `35f8be12db0c124e17723cf615b8eee939360e198bcdb383e300ff1085f96858`。

## 重跑

先按项目根目录说明准备 Retinexformer 上游和 CPU 环境。下载或解包作者的 LOLv2.zip，将权重置于 `weights/retinexformer/`，使用该环境的 Python 运行。

```text
python scripts/eval_retinex_lolv2.py real data/LOLv2/Real_captured/Test third_party/Retinexformer weights/retinexformer/LOL_v2_real.pth runs/m3-ret-v2-real
python scripts/eval_retinex_lolv2.py synthetic data/LOLv2/Synthetic/Test third_party/Retinexformer weights/retinexformer/LOL_v2_synthetic.pth runs/m3-ret-v2-synthetic
```

来源 [Retinexformer 原文表 1](https://arxiv.org/html/2303.06705) · [作者测试数据](https://drive.google.com/file/d/1Ou9EljYZW8o5dbDCf9R34FS8Pd8kEp2U/view) · [作者固定权重版本](https://huggingface.co/CaiYuanhao/Retinexformer/tree/7983bc70dca2cf043000f1efe793d51172d2f83b)。
