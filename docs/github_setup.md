# GitHub 建仓验收记录

日期：2026-11-23（Asia/Shanghai）。本次仅完成 M1 归档、团队仓库与后续任务规划。

## 实际仓库与提交

- 仓库：<https://github.com/xiaosen-017/LowLight-Transformer-Lab>；当前账户 `xiaosen-017`；**Private**；默认分支 **main**。
- 首个本地提交：`425333015bcf7875143ddc0d81f161a488485a09`。
- 首轮成功推送的分支头：`3d8970fc87508f98949a52524b9e13fd3f9a8c24`。此记录随后作为文档提交，最新提交请看 [commits/main](https://github.com/xiaosen-017/LowLight-Transformer-Lab/commits/main)。
- 原M1目录、两套成功环境和权重未移动、删除或修改；只用原环境运行两次各一张图的迁移smoke，结果与历史输出逐字节相同。证据见 [migration_smoke.json](migration_smoke.json)。
- 已提交报告、真实结果图、精确依赖、脱敏成功/失败日志、CPU/Windows补丁、参数化重跑入口、上游/权重清单、阶段计划与Issue/PR模板。
- 未提交上游完整仓库、嵌套.git、原始输入图、环境、权重、完整数据集、下载缓存或个人绝对路径。输入从作者官方固定commit获取，许可及私有组内使用范围见数据说明。

## 已创建里程碑

- [M1](https://github.com/xiaosen-017/LowLight-Transformer-Lab/milestone/1)：已关闭，M1归档完成。
- [M2](https://github.com/xiaosen-017/LowLight-Transformer-Lab/milestone/2)：OPEN / TODO，未执行实验。
- [M3](https://github.com/xiaosen-017/LowLight-Transformer-Lab/milestone/3)：OPEN / TODO，未执行实验。
- [M4](https://github.com/xiaosen-017/LowLight-Transformer-Lab/milestone/4)：OPEN / TODO，未执行实验。
- [M5](https://github.com/xiaosen-017/LowLight-Transformer-Lab/milestone/5)：OPEN / TODO，未执行实验。

## 已创建 Issues

| Issue | 标题 | Milestone | 实际状态 |
| --- | --- | --- | --- |
| [#1](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/1) | [M1] 整理 Retinexformer 复现说明、环境与推理结果 | M1 | closed |
| [#2](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/2) | [M1] 整理 LLFormer 复现说明、环境与推理结果 | M1 | closed |
| [#3](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/3) | [M1] 整合可重跑脚本、真实日志与权重获取说明 | M1 | closed |
| [#4](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/4) | [M2] 确定统一的 5–10 张测试图与图片来源 | M2 | open |
| [#5](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/5) | [M2] 生成统一视觉对比图及定性观察记录 | M2 | open |
| [#6](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/6) | [M3] 统一测试集与 PSNR/SSIM 评估协议 | M3 | open |
| [#7](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/7) | [M3] 测量并分析两个模型的增强质量与推理效率 | M3 | open |
| [#8](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/8) | [M3] 撰写两篇论文的方法对比与讨论 | M3 | open |
| [#9](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/9) | [M4] 建立 LLFormer 原始分块推理基线 | M4 | open |
| [#10](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/10) | [M4] 实现加权重叠融合并进行正确性检查 | M4 | open |
| [#11](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/11) | [M4] 完成分块大小/重叠率/融合策略消融实验 | M4 | open |
| [#12](https://github.com/xiaosen-017/LowLight-Transformer-Lab/issues/12) | [M5] 汇总课程报告、展示图表与团队分工 | M5 | open |

已建9个建议标签：m1/m2/m3/m4/m5/documentation/experiment/enhancement/bug。没有把未提供GitHub账号的组员虚构为assignee；A/B/C仅为建议角色。

## 协作设置与真实限制

已开启Issues、关闭wiki、合并后自动删功能分支；允许Squash/Rebase，关闭Merge commit。PR模板包含目的、修改、复现命令、结果与Issue；[CONTRIBUTING](../CONTRIBUTING.md) 规定 main 稳定、功能/实验/文档分支、至少另一人复核。

- 分支保护：未启用。实际API返回 `HTTP 403: Upgrade to GitHub Pro or make this repository public to enable this feature.` 为保持用户要求的Private，未改公开或升级账户。当前“需review后合并”是团队流程，**不是平台强制生效**。
- Projects看板：未创建。实际CLI返回当前授权缺少 `read:project`。没有为可选看板要求追加账户授权，已按任务书使用 **Issues + Milestones** 完成任务管理。
- 已完成的CLI授权保存在系统keyring；没有把Token放入Git、聊天、命令参数或日志。

## 组员加入与下一步

仓库所有者需提供另外两位组员的真实GitHub用户名，才能据此邀请与分配任务；不要发送密码或Token。用户名可从各自头像 → Your profile → 页面URL最后一段确认。未发送任何尚未授权/未知账号的邀请。

入组后：先读README → docs/M1_REPORT.md → 对应运行说明；接受邀请后克隆私有仓库，在相关Issue认领任务。M2先确认5–10图来源清单；M3先冻结评估口径；M4先做基线/覆盖正确性，再做融合和消融。**M2/M3/M4/M5尚未执行，无训练或提前创新实验。**

## M2后续进展

建仓之后已完成M2：5张统一输入、10张增强结果、三列对照图和逐图观察，详见README及docs/M2_REPORT.md。上文保留建仓时点的验收快照。M3/M4/M5待开展。
