# M1 归档报告

状态：**M1 PASS (single-image inference on CPU)**。这是原 M1 的归档整理；原报告逐段保留于 [脱敏原报告](archive/M1_REPORT.original.redacted.md)，未将后续规划或迁移检查写成原始实验。

## 原始运行事实

Windows 11 x64；AMD Ryzen 5 5625U；AMD Radeon 集显，无 NVIDIA CUDA；Python 3.7.9、PyTorch 1.13.1+cpu、torchvision 0.14.1+cpu，两个独立 venv。原始报告记录两环境 pip check 通过、用户 site 禁用且 DLL 是不同物理文件。完整版本见 [environments](../environments/README.md)。

| 模型 | 严格加载 | 官方权重 | 单次 CPU 前向记录 | 图像 |
| --- | --- | --- | --- | --- |
| Retinexformer | params，122 tensors，全键匹配 | LOL_v1.pth | 5.3681221 s（约5.37秒） | [600×400 RGB PNG](../results/m1/retinexformer/111.png) |
| LLFormer | state_dict，1485 tensors，全键匹配 | LOL model_bestPSNR.pth | 33.9998851 s（约34.00秒） | [600×400 RGB PNG](../results/m1/llformer/111.png) |

这些数字仅为 M1 已有记录，不是统一预热、重复计时或全量测试的正式速度结论；本阶段没有计算 PSNR/SSIM。两张图是原始输出的逐字节副本，文件哈希见 [迁移清单](migration_manifest.json)。

上游 commit：Retinexformer `2dd9ae05f34a34e2df3b955f743215ac3cda0f82`；LLFormer `ed5e7bf61d2dc64ba3b4552b90eb68a38f6c5302`。官方 URL/许可证见 [upstreams](../configs/upstreams.json)。

权重 SHA-256 / 大小：

- Retinexformer：`9b4810dc51322fab70be8658ee0ad1df64a54aa814497b7849767baa2ff32cd1`；6,475,021 bytes，与官方 HF LFS oid 一致。
- LLFormer：`2ff4907e4c277194adaa3ff302a01eb04d54ac9908afe70acbcfed2029d81551`；296,109,482 bytes。本地实测哈希，官方来源与 ZIP CRC 检查记录保留；不声称作者另行公布哈希。

原输入是官方 Retinexformer demo 提供的 LOL-v1 测试图 `111.png`，600×400 RGB；输入 SHA-256 为 `5f10ef298a617c239e0728610a565416b4503ed40384cc9710e8bbd55f22ef47`。原始图像不随本仓库重新分发，使用 setup_upstreams 后从官方 commit 读取。出处见 [数据说明](../data/README.md)。

## 入口、适配与故障

Retinexformer 直接导入原始架构和 LOL-v1 YAML。RGB float32 /255、4 倍数反射 padding、整图前向、裁回原尺寸、clamp 和四舍五入保存；Gamma=1、亮度=1、自集成关闭，无 GT_mean。LLFormer 保留原 LOL test.py 网络参数、16 倍数反射 padding（400×600→400×608）、整图推理、原后处理，输出裁回原尺寸。

最小兼容修复：LLFormer 的写死 CUDA 改设备选择和 CPU map_location；Windows glob 大小写造成重复输入，保序去重后最终真实运行 1/1。完整 [patch](../patches/llformer_cpu.patch)、[适配脚本](../patches/test_llformer_cpu.py) 保留版权署名与许可。未改网络、未训练、未实施 M4 分块融合。

网络 TLS/克隆失败、3.11/Torch2.2.2 安装路线放弃、本机已有 CPU 包的物理复制、补齐元数据、权重断点续传、原 CUDA 错误以及重复 glob 的首次成功日志均保留在 [logs/m1](../logs/m1)。原成功环境与原 M1 目录未移动或修改。原绝对路径被替换为 `<M1_ROOT>`、`<USER_HOME>` 等，具体脱敏范围见 [日志说明](../logs/README.md)。

## 当前团队项目的重跑方式

原始命令全文保留在脱敏原报告中；新入口只改变路径/配置组织：

```powershell
./scripts/setup_upstreams.ps1
./scripts/run_retinexformer.ps1 -PythonExe ./.venvs/retinexformer/Scripts/python.exe
./scripts/run_llformer.ps1 -PythonExe ./.venvs/llformer/Scripts/python.exe
```

权重自行放入 [规定位置](../weights/README.md)，不会提交到 Git。其他设备安装与本机已验证环境的差别见两份运行说明；完整网络重装并未在本次冒称验证完成。

## 限制与下一阶段

M1 仅证明一张真实图的官方权重本地推理。M2/M3/M4/M5 均 TODO，M4 唯一主线是 LLFormer 原网络/固定权重下的分块推理与融合优化。本次只归档和规划，不执行后续实验。现有权重是 LOL，不能不加区别地当成 UHD-LOL4K 权重使用。
