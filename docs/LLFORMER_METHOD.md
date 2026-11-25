# LLFormer 为什么适合研究分块，分块又改变了什么

LLFormer 论文研究超高清低光增强，给出 4K/8K 基准。它用轴向注意力和跨层融合降低高分辨率建模的压力。项目固定的 LOL 权重用于 600×400 图像；下文模型机制与 UHD 论文有关，项目实测不等于复现论文的 4K/8K 指标。

在固定版本的 `model/LLFormer.py` 中，`NextAttentionZ` 先做行注意力，再转置高宽做列注意力，最后转回。在 H×W 的特征图上，忽略通道、头数等常数，两个注意力矩阵的元素数合计随 HW(H+W) 增长；展平所有像素做全注意力则随 (HW)² 增长。这是注意力部分的复杂度，不是整网运行时间。网络还使用卷积、前馈层和多尺度上下采样；`LAM_Module_v2` 在层间计算注意力，融合多个阶段的特征。把跨层融合与本项目在图像空间里加权拼块区分开：前者是预训练网络的一部分，后者只发生在模型输出之后。

Retinexformer 的出发点不同：先估计光照以提亮输入，再用光照表征引导 Transformer 恢复，处理提亮时显露的噪声与失真。因此不能从“都是 Transformer”推定两者有相同的分块误差，也不能拿不同机器的一次计时给它们排速度名次。本文仅负责 LLFormer 的结果。

块越小，单次注意力看到的同行、同列范围越短。相邻块在同一重叠像素上可能给出不同预测。均值让边缘和中心的预测等权；归一化 Hann 则在有其他块覆盖时减弱边缘预测。它无法补回块外上下文，也未保证提高 PSNR。A/C 和 B/D 固定网格比较权重，A/B 和 C/D 固定融合比较块尺寸；不同块尺寸要在同一张边界掩膜上评价，避免换一批像素后误判收益。

来源：[LLFormer 论文](https://arxiv.org/abs/2212.11548)、[上游实现（固定版本）](https://github.com/TaoWangzj/LLFormer/blob/ed5e7bf61d2dc64ba3b4552b90eb68a38f6c5302/model/LLFormer.py)、[Retinexformer 论文](https://arxiv.org/abs/2303.06705)。本项目的整图结果与指标口径见 [M3 实验](../experiments/m3_evaluation/llformer/README.md)。

同一口径的局部对照：把仓库之前冻结的全部 5 张 M2 增强 PNG 与官方配对 GT 匹配，不重跑模型、不挑图。LLFormer 平均 22.1470 dB / 0.78745，Retinexformer 平均 24.1107 dB / 0.82624。这里只能说两个方法在这批展示图上的差异；不能归因于某个模块，不能替代两个模型各自跑完 15 张的全测试集对比。两者不比较历史单次运行速度。[逐图原始数据](../experiments/m3_evaluation/llformer/m2_five_pairs.csv)；复算命令：`python scripts/compare_m2_pairs.py data/lol/eval15 runs/m2-paired-check.csv`。


## 完整测试集的两模型结果

Retinexformer 的 `Illumination_Estimator` 使用 RGB 和通道均值生成照度图与光照特征。单阶段网络将输入调制为 `img * illu_map + img`，恢复网络以光照特征乘到值分支。IG-MSA 把每个 head 的查询和键排成通道 × 空间布局，注意力矩阵作用在每头的通道维。固定通道宽度时，该乘法对像素数量近似线性。LLFormer 在每一行和列上分别生成空间注意力矩阵，固定通道宽度时矩阵规模随 `HW(H+W)` 增长。两种复杂度只描述各自注意力部分，不能替代实测推理时间。

统一 eval15 上，Retinexformer 与 LLFormer 的平均 PSNR 分别为 25.1531 和 23.6491 dB，Gaussian SSIM 为 0.84546 和 0.81846。Retinexformer 在 15 张中有 10 张 PSNR 更高、13 张 SSIM 更高，同机单图四线程也更快。较大照度变化与暗区颗粒可能驱动场景间差异，逐图 CSV 可定位反例。模型、训练方案、权重来源共同影响结果，不能由两模型差值推断单一模块效果。LLFormer 的分块实验进一步表明，固定网格改变融合可以降低跨线误差并提高 SSIM，同时牺牲一些像素级 PSNR。见 [统一实测](../results/m3/lolv1_eval15_windows/REPORT.md) 和 [LLFormer 分块对照](../results/m4/lol_eval15_v1/REPORT.md)。
