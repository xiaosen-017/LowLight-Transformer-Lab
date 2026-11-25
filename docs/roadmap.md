# 研究路线与阶段验收

| 阶段 | 状态 | 产物与验收 |
| --- | --- | --- |
| M1 基础复现 | DONE | 官方commit/权重SHA可追溯，两个独立环境，同图本地严格加载和原始输出/日志 |
| M2 五图视觉展示 | DONE | 全部5张官方demo样本清单，10张增强PNG，统一三列图和六维逐图观察 |
| M3 定量与方法分析 | LOL-v1 两模型已完成 | LOL-v1 两模型及 LOL-v2 Retinexformer 官方权重评估、逐图指标、同机开销与方法讨论 |
| M4 LLFormer分块与融合 | LOL 实验已完成 | 官方均值基线、覆盖/归一化正确性、平滑加权融合、四组消融及边缘/资源分析 |

LLFormer 的[整图复现](../experiments/m3_evaluation/llformer/README.md)、[与 Retinexformer 的方法对照](LLFORMER_METHOD.md)、[四组消融和资源记录](../results/m4/lol_eval15_v1/REPORT.md)均有实测证据。保留未修改 CUDA CLI 在 Mac 上的失败；未用 UHD 权重跑 4K/8K，不从 LOL 分块实验推断 UHD 质量。两模型的 15 对图同机评估已完成，Retinexformer 额外完成 LOL-v2 Real 与 Synthetic 各 100 对。见 [LOL-v1 报告](../results/m3/lolv1_eval15_windows/REPORT.md) 和 [LOL-v2 报告](../results/m3/retinexformer_lolv2_windows/REPORT.md)。流式融合扩展使用 LOL-v1 权重，长边 2048 的记录见 [流式融合报告](../results/m4/streaming_windows/REPORT.md)。
