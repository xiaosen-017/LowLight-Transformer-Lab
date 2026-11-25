# Retinexformer 模块消融归档与复跑

PR #14 提供四组各 5,000 步训练的日志和验证曲线。仓库核对了日志、`summary.csv` 和 `psnr_curves.json` 的五个计划验证点，保留原始数据与图。

| 原记录组别 | 最佳 PSNR | 迭代 | 标签检查 |
| --- | ---: | ---: | --- |
| A0 | 18.4716 | 2,000 | 两模块关闭的记录 |
| A1 | 18.5679 | 2,000 | 单模块归属待原训练证据确认 |
| A2 | 18.8396 | 2,000 | 单模块归属待原训练证据确认 |
| A3 | 20.2992 | 3,000 | 完整组记录 |

原提交的 Python 开关参数及 CSV 将 A1 写成 IG-MSA 开、ORF 关，将 A2 写成 ORF 开、IG-MSA 关。原报告的文字和图例将两组反向命名。训练日志没有保存运行时开关或架构快照，因此目前可引用四条组别曲线，以及 A3 与 A0 的 +1.8276 dB 短程差值。模块强弱或协同需要补齐两组归属并做重复实验。旧图上的 A1/A2 模块文字仍属于历史原标签。

本次新增明确分组的 `experiments/m4_retinexformer_ablation/code/prepare_run.py`。它从官方固定 Git 提交导出四份独立源码，记录开关和架构哈希。A1 为只开启光照估计/调制，A2 为只开启注意力残差分支。关闭光照估计时同时绕过值分支的光照乘法，避免零张量将注意力输出压成零。四组均已在 CPU 完成 64×64 前向检查，A3 的架构文件保持官方原始字节。这一整理后的方案用于今后训练复跑，已归档的两个单模块分数暂不映射到新组别。新方案尚无独立 5,000 步重训曲线。

```text
python experiments/m4_retinexformer_ablation/code/prepare_run.py third_party/Retinexformer runs/retinex-ablation-smoke
python experiments/m4_retinexformer_ablation/code/prepare_run.py third_party/Retinexformer runs/retinex-ablation-train --data data/lol --train
```

`--train` 需要官方训练/验证对及对应 BasicSR CUDA 训练环境，运行目录须为新目录。该入口按组记录训练退出码和每组的配置哈希。当前复核跑的是 CPU 前向检查。旧日志和旧汇总位于 `experiments/m4_retinexformer_ablation/data/`。两模型官方 LOL 权重的定量复现参见 [M3 报告](../results/m3/lolv1_eval15_windows/REPORT.md)。LLFormer 分块融合是本项目的创新主线，正式四组实验与结果见 [分块报告](../results/m4/lol_eval15_v1/REPORT.md)。
