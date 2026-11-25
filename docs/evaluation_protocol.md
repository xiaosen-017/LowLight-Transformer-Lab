# 实验协议：M2 与 LLFormer 的 M3/M4


M2已按configs/m2_samples.json冻结并完成全部5张官方demo图：22、111、146、493、778，原尺寸600×400，两个模型使用匹配LOL权重和相同输入。三列图、逐图观察与完整性检查已归档；本文件以下的配对指标和资源重复测量方案用于M3/M4。

LLFormer 的实际整图环境、两种窗口口径及完整数据见 [M3 复现](../experiments/m3_evaluation/llformer/README.md)。M4 冻结的网格、时间边界和可重跑命令见 [分块实验](../experiments/m4_tiling/README.md)。下面保留组内统一协议及其历史背景。

## 数据与模型

M2：同一批5–10张真实低光图，逐图记录来源/许可范围、文件SHA256、原始分辨率、是否GT配对。M3：优先LOL-v1官方测试划分，使用两模型各自LOL匹配官方权重；不能挑不同测试图或用训练图冒充测试集。原尺寸优先；资源原因缩放需单独实验配置，两个模型采用同一缩放、同一插值并记录新哈希。原输入、GT和输出目录分离。

M4第一轮用当前固定LOL checkpoint做受控较小图的策略正确性与敏感性研究；这不代表UHD论文设置。若转UHD-LOL4K，另冻结官方UHD权重、合法小样本、SHA和硬件，形成独立实验组，不混报LOL/UHD结果。

## 预处理、质量指标

RGB、float32 [0,1]、eval/no_grad，记录两模型各自必要的反射padding和原尺寸裁回；不使用GT_mean、自集成、额外Gamma/亮度调参。默认保存无损RGB PNG，禁止为美观后处理后再计分。

建议冻结实现：scikit-image 0.19.3 或经讨论确认的固定版本，在单独评估环境计算，明确与M1推理环境scikit-image0.15不同，不能改原成功环境。拟定PSNR按RGB所有像素平均MSE后 `10*log10(1/MSE)`（MSE=0为+∞），data_range=1；SSIM按RGB各通道，win_size=11、gaussian_weights=True、sigma=1.5、use_sample_covariance=False、data_range=1，边界处理与版本固定。运行前对照官方评估方法核查差异：如果官方采用Y通道、不同边界/窗口，报告本协议及差异，不声称同口径。小于窗口的测试图单独规定或排除，不悄改窗口。

逐图指标与全测试集算术均值同时保存；不得只选择表现好的图片。论文原始指标另列引用，不直接与本机不同协议数字排位。M1尚未实际计算任何PSNR/SSIM。

## 计时和资源

同一硬件、设备、线程数、精度、输入分辨率与batch=1；拟用一次不计时预热、随后至少5次正式单图重复，汇报中位数及范围，另记冷启动。CPU用perf_counter；CUDA计时前后同步，分开记录模型前向与端到端（加载/解码/传输/保存）的范围。模型/权重加载不混入纯前向计时。固定运行次序或交错顺序并记录后台负载。

CPU分别记录进程峰值RSS及测量工具/采样间隔；CUDA若可用，用固定工具记录峰值allocated/reserved，不能把缓存占用与实际张量占用混淆。当前机器没有CUDA，因此显存字段写N/A。M1的5.37秒与34.00秒仅历史单次前向记录，不纳入正式性能结论。

## 展示与记录

定性观察逐图记录暗部纹理、噪声、色偏、过曝、边缘/拼接伪影；保持同一显示缩放和颜色设置，不独立调亮对比图。M4固定实际块边界，可在预定边界带上记录像素梯度跳变和对GT的残差；此为补充边缘诊断，不替代PSNR/SSIM，也不按最优结果重新选边界。

每次实验至少保存：Git SHA、上游SHA、权重SHA、配置/数据清单、Python/Torch/评估库版本、设备、padding/裁回/分块策略、逐图结果、日志、指标CSV及失败/OOM。没有真实运行的格子写NOT RUN，不填预测数值。结果主张由第二人独立复核。


两模型 LOL-v1 定量复现细节与两个 SSIM 口径见 `results/m3/lolv1_eval15_windows/REPORT.md`。当前 Windows 实测沿用 scikit-image 0.15.0，逐通道显式设置 SSIM 窗口与协方差。

## 论文复现覆盖范围

以论文作者的方法为验收对象。每个数据集分别登记测试划分、官方模型权重、预处理和指标，不把不同数据集的结果合并成同一复现结论。

| 论文 | 数据或实验 | 验收项 |
| --- | --- | --- |
| Retinexformer | LOL-v1 eval15 | 表 1，PSNR 25.16 / SSIM 0.845，已复现 |
| Retinexformer | LOL-v2 Real / Synthetic | 表 1，22.80 / 0.840 与 25.67 / 0.930，各 100 对，使用各自的官方权重，已完成 |
| Retinexformer | SID / SMID / SDSD-indoor / SDSD-outdoor | 表 1，分别用上游测试 YAML、测试名单与预处理获得各自 PSNR / SSIM，尚待评估 |
| Retinexformer | MIT-Adobe FiveK 与论文模块消融 | 匹配作者处理后的 sRGB 划分。论文消融按原训练预算与配置重跑，尚待评估 |
| LLFormer | LOL-v1 eval15 | 表 2，PSNR 23.6491、SSIM 0.8163、LPIPS 0.1692、MAE 0.0635，已复现 |
| LLFormer | MIT-Adobe FiveK | 表 2，PSNR 25.7528、SSIM 0.9231、LPIPS 0.0447、MAE 0.0505。已定位作者 test 中的 high/low 数据目录与权重目录，尚待下载和评估 |
| LLFormer | UHD-LOL4K / UHD-LOL8K | 表 1，分别使用官方 2,100 / 937 对测试图、对应权重与原论文分块协议，计算全图 PSNR、SSIM、LPIPS、MAE，尚待评估 |
| LLFormer | 原论文训练与消融 | 独立核对作者训练配置、检查点和原论文消融设置，尚待评估 |
| 课题 M4 | LLFormer 分块、Hann 和流式拼接 | LOL-v1 全 15 对图和 2048 长边扩展均已实测。原生 UHD 另用同图、同权重、同网格对照均值、Hann 及堆叠/流式资源开销 |

原生 UHD 先用一对官方 4K 样本完成覆盖率、逐像素一致性和资源冒烟，再分批跑完整测试划分。准备可访问的官方配对文件、对应 checkpoint，以及 CUDA GPU 和足够磁盘。4K 测试下载约 69.7 GB，解包和输出还需额外空间。本机仅有 AMD 集显，C 盘检查剩余约 50 GiB。两篇论文的原始训练配置保存在各自官方项目。分支中的 Retinexformer 补充消融默认记录修正开关并运行前向，完整训练使用 CUDA 入口。

来源 [Retinexformer 论文](https://arxiv.org/html/2303.06705) · [Retinexformer 官方数据与测试入口](https://github.com/caiyuanhao1998/Retinexformer#testing) · [LLFormer 论文](https://arxiv.org/html/2212.11548) · [LLFormer 官方数据与权重](https://github.com/TaoWangzj/LLFormer#downloads)。
