# M3 · LOL-v1 两篇论文的定量复现与同机对照

2026-11-25 在同一台 Ryzen 5 5625U Windows CPU 上重复运行两套官方网络。两套环境均为 Python 3.7.9、PyTorch 1.13.1+cpu、NumPy 1.21.6、Pillow 9.5.0、scikit-image 0.15.0。均使用四个 Torch 线程、RGB float32、batch 1、原尺寸、反射补边和裁回。独立进程记录权重文件 SHA、源码提交及严格加载键数。模型输出采用 8-bit RGB PNG。

数据为完整 LOL-v1 eval15，15 张低照度图与 15 张 GT。下载固定版本的 `test.zip`，SHA-256 为 `d425ccb38436d2fd4b26783b0ff97b6fc14a34524c1924a7dc62e9c0d9c9f080`。**全部 30 个 PNG 的哈希与 PR #13 从官方原包提取的记录一致**。官方数据是 Wei 等人在 BMVC 2018 提供的 LOL。下载地址见 [LOL 官方主页](https://daooshee.github.io/BMVC2018website/) 和 [字节核验通过的固定镜像](https://huggingface.co/datasets/okita-souji/LOLv1/blob/443818c380a4159db7f344cd9319b75e85ee5cbf/test.zip)。

## 论文同口径

| 论文、数据 | 论文 PSNR / SSIM | 复现实测 PSNR / SSIM | 其余 LOL 论文指标 |
| --- | --- | --- | --- |
| Retinexformer，ICCV 2023 表 1 | 25.16 / 0.845 | **25.15527 / 0.845458** | 表 1 的 LOL-v1 恢复质量以 PSNR / SSIM 表示 |
| LLFormer，AAAI 2023 表 2 | 23.6491 / 0.8163 | **23.64912 / 0.816309** | AlexNet LPIPS **0.169239**（论文 0.1692），MAE **0.063452**（论文 0.0635） |

Retinexformer 使用官方测试代码的浮点 PSNR 和 11×11 Gaussian RGB SSIM，sigma=1.5、总体协方差，SSIM 计算于 8-bit 量化图。两项均在论文精度下吻合。GT-mean 是另一个使用参考亮度的诊断设置，保存在 `retinexformer/metrics.csv`，不参与主表。LLFormer 使用保存的 RGB PNG 计算 PSNR、7×7 均匀窗样本协方差 SSIM、RGB MAE（[0,1]）及上游 `evaluation.py` 的 AlexNet LPIPS（输入 [-1,1]）。LPIPS 采用 0.1.4 及 torchvision 官方 AlexNet 卷积层。下载只取所需张量并逐项验证 ZIP CRC，资产 SHA 另存。

来源 [Retinexformer 原文表 1](https://arxiv.org/html/2303.06705) · [LLFormer 原文表 2](https://arxiv.org/html/2212.11548) · [LLFormer 评估源码](https://github.com/TaoWangzj/LLFormer/blob/ed5e7bf61d2dc64ba3b4552b90eb68a38f6c5302/evaluation.py)。

## 小组统一对照

| 模型 | 全 15 图 RGB PNG PSNR ↑ | Gaussian SSIM ↑ | 111.png 前向 / 端到端中位数 | 进程峰值工作集 |
| --- | ---: | ---: | ---: | ---: |
| Retinexformer | 25.1531 dB | 0.84546 | 3.92 / 4.16 s | 0.93 GiB |
| LLFormer | 23.6491 dB | 0.81846 | 42.60 / 42.92 s | 1.78 GiB |

Retinexformer 在统一口径下平均高 1.5040 dB、SSIM 高 0.02700。15 张中分别有 10 张 PSNR 和 13 张 SSIM 更高。计时为每模型一个独立进程，固定 111.png，一次预热后五次，权重加载单独记录。端到端含读图、模型推理、裁回量化和 PNG 保存。工作集是单个进程从启动到基准结束的高水位，含整组评估和权重加载。时间和内存结论限定于本机、当前线程和 600×400 样本。

Retinexformer 先估计光照、调制输入，再用光照特征调制注意力的值分支并恢复细节。LLFormer 用行列轴向建模和跨层特征融合，设计目标包括高分辨率运行。当前 LOL-v1 分数和速度反映整套模型与已发布权重在该协议下的表现，模块因果归因需要独立消融。LLFormer 裁小图块会缩短同行同列可见的上下文，重叠融合针对跨块预测不一致。见 [方法与边界分析](../../../docs/LLFORMER_METHOD.md) 和 [分块四组结果](../../m4/lol_eval15_v1/REPORT.md)。

## 重跑

先按根目录说明准备固定上游和 `configs/weights.json` 中的权重，将测试包解压至 `data/lol/eval15`。对两模型分别用对应环境的 Python 执行。

```text
python scripts/eval_lolv1_pair.py retinexformer data/lol/eval15 third_party/Retinexformer weights/retinexformer/LOL_v1.pth runs/m3-ret
python scripts/eval_lolv1_pair.py llformer data/lol/eval15 third_party/LLFormer weights/llformer/model_bestPSNR.pth runs/m3-ll
python -m pip install lpips==0.1.4
python scripts/fetch_alexnet_features.py runs/alexnet_features.npz
python scripts/score_lolv1_perceptual.py runs/m3-ll data/lol/eval15/high runs/alexnet_features.npz runs/m3-ll-extra
```

本轮保存 30 张输出在本地忽略目录，Git 归档包含逐图指标、输入/GT/输出 SHA、环境和重复计时。项目完成范围为两篇论文共享的 LOL-v1 表格结果。论文的其他数据集、训练完整流程与 UHD-LOL4K/8K 表格另有各自数据和权重。
