# Retinexformer 短程模块消融

`data/` 和 `figures/` 保存 PR #14 的原始训练日志与图表。A1/A2 的历史开关归属待核对，两组判读暂以编号为准。当前复跑协议、四组结果、局限及正确命令请见 [消融归档和复跑说明](../../docs/RETINEXFORMER_ABLATION.md)。

当前入口是 `code/prepare_run.py`。默认在新目录执行四组 CPU 前向检查，`--train` 在匹配的 CUDA 环境执行四组短程训练。执行记录见 [本次前向检查](../../results/m4/retinexformer_ablation_smoke.json)。
