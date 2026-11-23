# GitHub项目状态

仓库：https://github.com/xiaosen-017/LowLight-Transformer-Lab；Public；main。

## 里程碑

| 阶段 | 当前状态 |
| --- | --- |
| M1 基础复现与归档 | 已完成 |
| M2 统一视觉展示 | 已完成 |
| M3 定量评估与方法分析 | 待开展 |
| M4 LLFormer分块推理与融合优化 | 待开展 |

## 任务清单

| Issue | 标题 | 阶段 | 状态 |
| --- | --- | --- | --- |
| [#1](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/1) | [M1] 整理 Retinexformer 复现说明、环境与推理结果 | M1 | closed |
| [#2](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/2) | [M1] 整理 LLFormer 复现说明、环境与推理结果 | M1 | closed |
| [#3](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/3) | [M1] 整合可重跑脚本、真实日志与权重获取说明 | M1 | closed |
| [#4](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/4) | [M2] 确定统一的 5–10 张测试图与图片来源 | M2 | closed |
| [#5](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/5) | [M2] 生成统一视觉对比图及定性观察记录 | M2 | closed |
| [#6](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/6) | [M3] 统一测试集与 PSNR/SSIM 评估协议 | M3 | open |
| [#7](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/7) | [M3] 测量并分析两个模型的增强质量与推理效率 | M3 | open |
| [#8](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/8) | [M3] 撰写两篇论文的方法对比与讨论 | M3 | open |
| [#9](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/9) | [M4] 建立 LLFormer 原始分块推理基线 | M4 | open |
| [#10](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/10) | [M4] 实现加权重叠融合并进行正确性检查 | M4 | open |
| [#11](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/11) | [M4] 完成分块大小/重叠率/融合策略消融实验 | M4 | open |

现有11个研究/开发Issues、4个里程碑。阶段/类型标签为m1、m2、m3、m4、documentation、experiment、enhancement、bug。

## 协作设置

Issues开启，wiki关闭；允许Squash/Rebase，合并后自动删除功能分支。PR模板记录目的、修改、复现命令、实际结果与关联Issue，成员按Issue认领并交叉复核。

main已配置1次批准、代码所有者审核、撤销过期批准、解决讨论、禁止force-push与删除。管理员保留管理例外。代码所有者为xiaosen-017，规则见.github/CODEOWNERS。Projects仍使用已有Issues和Milestones进行任务管理。

CLI凭据保存在系统keyring，仓库内无Token。原M1目录/环境/权重未移动或修改；M2结果与运行记录见README和docs/M2_REPORT.md。
