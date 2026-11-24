# LLFormer / LOL-v1 整图基线

本目录只记录 LLFormer。Retinexformer 的正式重跑、跨模型速度对比及 M4 真实分块消融均不在本次结果内。原始照片、GT、增强输出和大权重留在忽略目录；不从测试图挑样。

数据：[LOL 数据作者页](https://daooshee.github.io/BMVC2018website/) 下载区的 Google Drive 原包，SHA-256 为 `47d85314b7927470cd48c97e5c1d6c896a56d6217c8e508d0736aff2d91aadcc`，只解出 eval15/{low,high}。正式输入为全部 15 对，同名 RGB 原尺寸；其中五张 low 的文件哈希与 configs/m2_samples.json 一致。官方 LOL 权重见 configs/weights.json，加载器核对 SHA 后严格加载。上游模型版本见 config.json，无训练或参数修改。

全 15 对平均：**PSNR 23.6486 dB，SSIM 0.81846**。从写出的 PNG 再以 uint8 域及逐通道 SSIM 复算，每图两项差小于 1e-9。与 M2 重合的五张增强图逐通道值最大相差 1/255，并非字节级完全相同。

## 复现

从仓库根目录运行。先配置 configs/upstreams.json 指定的 third_party/LLFormer 及 configs/weights.json 的 LOL 权重，解压上述数据。以下目录必须不存在。参考环境为 arm64 macOS、Apple M5、24 GiB 统一内存、CPU 四线程、Python 3.12。

```sh
python -m pip install torch==2.15.0 numpy==2.5.5 pillow==13.0.0 einops==0.8.2 scikit-image==0.25.2
python scripts/eval_llformer_lol.py data/lol/eval15 runs/m3-eval15-local
python scripts/verify_llformer_lol.py data/lol/eval15 runs/m3-eval15-local
python scripts/bench_llformer_cpu.py data/lol/eval15/low/111.png runs/m3-bench-local
```

整图 RGB float32、batch=1、eval/inference_mode，反射补至 16 倍数，前向后裁回、限幅并一次量化为 8-bit RGB PNG。不调 GT 均值、无自集成。对量化像素和 GT 换算至 [0,1]，用全 RGB MSE 计算每图 PSNR；SSIM 固定 11×11 Gaussian (sigma=1.5)，总体协方差，channel_axis=-1，data_range=1。两项均以每张图等权平均。上游 evaluation.py 使用 uint8 RGB 和旧版 skimage 默认 SSIM 窗口；本地 SSIM 不能直接当作论文同口径复现。0.25.2 是本地评估环境固定版本，跨模型对比需统一。

metrics.csv 每行记录一对样本的输入、GT、输出文件哈希和结果；该表的单次 forward_seconds 不是正式速度基准。benchmark.json 对固定 111.png 排除 1 次预热后记录 5 次，分别计模型前向和读图→预处理→前向→写 PNG，权重加载单列。RSS 是独立进程含权重加载的 OS 高水位，macOS 单位为字节；显存 N/A。单图资源数字不能代表 4K 或跨设备速度。

本次 111.png 五次正式前向中位数 12.30 s（11.44–12.57 s）；端到端中位数 12.34 s；独立进程峰值 RSS 2.77 GiB。六次输出文件 SHA 一致。CPU 状态和后台负载未锁定，以实测范围解释，不据此比较其他机器。

## 与论文 LOL 行对照

[原文表 2](https://arxiv.org/pdf/2212.11548) 的 LOL 行报告 PSNR 23.6491 dB、SSIM 0.8163。固定版本的上游 evaluation.py 对 uint8 RGB 使用旧版 skimage 的多通道默认 SSIM；在本地明确设置等价的 7×7 均匀窗、样本协方差，逐图等权得到 **23.64855 dB / 0.816310**（与表格差 −0.00055 dB / +0.000010）。这是相同协议的现代实现复算，不声称装了作者的历史评估环境。与小组 11×11 Gaussian 的 0.81846 分栏报告；两种 SSIM 都用完全相同的已保存增强图。未复算论文 LPIPS，不用 PSNR/SSIM 一致性推断其他指标。详见 [逐图分数](paper_window.csv)。复跑：`python scripts/score_llformer_paper.py runs/m3-eval15-local data/lol/eval15/high runs/paper-window.csv`。
