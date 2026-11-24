# 研究路线与阶段验收

| 阶段 | 状态 | 产物与验收 |
| --- | --- | --- |
| M1 基础复现 | DONE | 官方commit/权重SHA可追溯，两个独立环境，同图本地严格加载和原始输出/日志 |
| M2 五图视觉展示 | DONE | 全部5张官方demo样本清单，10张增强PNG，统一三列图和六维逐图观察 |
| M3 定量与方法分析 | LLFormer 已完成 | 统一LOL-v1配对测试集、RGB/PSNR/SSIM协议、时间/资源记录、两篇方法讨论 |
| M4 LLFormer分块与融合 | LOL 实验已完成 | 官方均值基线、覆盖/归一化正确性、平滑加权融合、四组消融及边缘/资源分析 |

LLFormer 的[整图复现](../experiments/m3_evaluation/llformer/README.md)、[与 Retinexformer 的方法对照](LLFORMER_METHOD.md)、[四组消融和资源记录](../results/m4/lol_eval15_v1/REPORT.md)均有实测证据。保留未修改 CUDA CLI 在 Mac 上的失败；未用 UHD 权重跑 4K/8K，不从 LOL 分块实验推断 UHD 质量。Retinexformer 的完整 eval15 同机测量留给该模型负责人。
