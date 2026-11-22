# retinexformer：团队项目运行入口

原始 M1 已 PASS；这是迁移后的入口说明，历史记录见 [原始说明脱敏副本](archive/run_retinexformer_M1_original.redacted.md)。

1. 从仓库根运行 `./scripts/setup_upstreams.ps1`，获取两个指定作者仓库并固定 [commit](../configs/upstreams.json)。已有代理可通过 `-Proxy <你的代理URL>` 显式传入；不写入团队默认设置。
2. 按 [环境说明](../environments/README.md) 创建独立环境，或使用已存在、已验证的解释器；按 [权重说明](../weights/README.md) 下载官方 LOL 权重。权重不入 Git。
3. 执行：

```powershell
./scripts/run_retinexformer.ps1 -PythonExe ./.venvs/retinexformer/Scripts/python.exe
```

若重用本机 M1，不修改或复制其环境，显式设置 `-PythonExe <原环境解释器>`、`-Upstream <原官方代码目录>`、`-Weights <原权重>`、`-InputPath <原输入图>`；这些个人路径只在本地终端使用，不提交文件。脚本会核对 commit、受控修改、权重哈希和大小。

默认输入来自 `third_party/Retinexformer/demo/examples/111.png`；默认输出到被忽略的 `runs/retinexformer/时间/images/`，日志在同次运行目录。用 `-OutputDir` 可选其他运行目录，保持历史 `results/m1` 不变；`-Threads 4` 为本次 CPU 默认。

成功必须看到全键严格匹配、真实前向记录、正常结束及可解码 PNG。Retinexformer 为 122 个张量；LLFormer 为 1485 个张量、最终同图只处理 1/1。两模型原始输入/输出均 600×400 RGB；LLFormer 内部宽 padding 到608再裁回。原代码与最小适配依据见 [兼容说明](m1_compatibility.md) 和 [故障记录](m1_troubleshooting.md)。

该入口只提供 M1 单图 CPU 复现；没有实现 M2 批量展示、M3 指标、M4 分块/融合或任何训练功能。完整网络安装、CUDA和超高清资源表现仍需未来独立验证。
