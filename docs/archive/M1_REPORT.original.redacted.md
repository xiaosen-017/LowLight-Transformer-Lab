# M1 基础复现报告

执行日期：2026-11-23（Asia/Shanghai）。**Retinexformer：PASS；LLFormer：PASS。** 两者均已在本机 CPU 上严格加载作者发布的 LOL 权重并完成同一张真实低光照图片的前向推理。

任务依据是用户提供的 `<USER_HOME>/Downloads/M1.md`（当前目录起初没有该文件），原文副本存于 `work/M1_source.md`。本报告同时保存在工作区根目录和 `outputs/M1_REPORT.md`，内容相同。

## 1. 本机环境与执行路径

| 项目 | 实际检查结果 |
| --- | --- |
| 工作区 | `<M1_ROOT>` |
| OS / Shell | Windows 11 家庭中文版 x64，10.0.22000；PowerShell 7.6.9 |
| CPU / RAM | Ryzen 5 5625U，6 核 12 线程；物理内存约 15.31 GiB，起始可用约 2.95 GiB |
| GPU / 驱动 | AMD Radeon 集成显卡，驱动 31.0.21912.2004；WMI 报告 AdapterRAM=512 MiB，此数不表示 CUDA 可用显存 |
| CUDA | 无 NVIDIA CUDA 设备；`nvidia-smi`、`nvcc` 不存在；最终 `torch.cuda.is_available()=False`，runtime=None |
| 原有 Python / Conda | 默认 Anaconda Python 3.7.4，Conda 4.7.12；另有 CPython 3.7.9、3.11.9 |
| 最终环境 | 两个独立 venv，均为 CPython 3.7.9 / Torch 1.13.1+cpu / torchvision 0.14.1+cpu |
| 关键依赖 | NumPy 1.21.6、Pillow 9.5.0、einops 0.6.1、PyYAML 6.0.1；LLFormer 另用 OpenCV 4.10.0.84、scikit-image 0.15.0、natsort 8.4.0 |
| Git / LFS | Git 2.20.1.windows.1 / Git LFS 2.6.1；源码不需下载 LFS 权重 |
| 磁盘 | 初始 C: 可用 58,762,240,000 bytes（54.73 GiB）；后续快照约 52.35 GiB，下载期间会变动 |
| WSL | 仅有停止的 docker-desktop WSL2；未选择该环境 |

选择 **Windows 原生 CPU**：本机没有 CUDA；原生 CPU 已实测可完成两模型，无需更改驱动、系统 CUDA 或安装 Linux。每次前向使用 4 个 Torch 线程，依次运行。

环境实际路径是 `work/venvs/retinexformer37` 和 `work/venvs/llformer37`。最初创建的 Python 3.11 venv 与 Torch 2.2.2 安装路线因 TLS 错误及大包下载过慢而放弃，**不是最终可用环境**。本机已有的可运行 CPU 发行包被实际复制到两个新环境，并补齐各自依赖与元数据；未共享 site-packages、未改原 Anaconda。两环境 `pip check` 均通过，DLL 的 `os.path.samefile` 检查证实与原环境和另一 venv 不是同一文件。详情见 `environments/*copy_manifest.json`、`*_runtime.json`、真实 freeze 和隔离日志。

网络最初直连 GitHub、pip 默认清华源及部分官方端点失败。读取已有 Windows 代理配置发现 `127.0.0.1:7897`，仅为任务进程显式配置代理，随后完成官方克隆及权重下载；未关闭证书检查或绕过登录、验证码、权限限制。失败、重试和转向均保留在 `logs/`。完整环境摘要见 `logs/environment.txt`，原始检查见 `logs/environment_raw.txt`。

## 2. Retinexformer

- **验收状态：PASS，已实际本地权重推理。**
- 官方仓库：<https://github.com/caiyuanhao1998/Retinexformer>。
- commit：`2dd9ae05f34a34e2df3b955f743215ac3cda0f82`；本地 `work/repos/Retinexformer`，受控文件无改动。
- 克隆：直连失败后使用已有代理完成 `git clone --depth 1`。前期已下载同 SHA 官方归档，成功克隆的 `.git` 与该目录合并，并恢复标准 Git 检出行尾；保留真实 clone 日志，不把单纯 ZIP 下载称为克隆。
- 环境：`work/venvs/retinexformer37`，关键版本同第 1 节。采用无界面薄 wrapper，直接导入官方原始架构及 `Options/RetinexFormer_LOL_v1.yml`。官方 demo 当前要求较新 Python；本次架构在 Python 3.7.9 上实际验证通过。BasicSR namespace 与架构导入已验证，未部署整套训练依赖或 Gradio。
- 官方权重：`work/LOL_v1.pth`，**6,475,021 bytes**，来源 <https://huggingface.co/CaiYuanhao/Retinexformer/resolve/main/LOL_v1.pth>。固定发布版本为 `7983bc70dca2cf043000f1efe793d51172d2f83b`。
- SHA-256：`9b4810dc51322fab70be8658ee0ad1df64a54aa814497b7849767baa2ff32cd1`，与官方发布记录的 LFS oid/大小完全一致；checkpoint ZIP 所有成员 CRC 检查通过。
- checkpoint 为 `params` 包装字典；**122 个参数张量，strict=True，全键匹配**。
- 输入：`outputs/samples/input/111.png`，来自本 commit 官方 `demo/examples/111.png`，官方说明其为 LOL-v1 测试集低光照图。原文件与复制输入 SHA-256 一致：`5f10ef298a617c239e0728610a565416b4503ed40384cc9710e8bbd55f22ef47`。
- 实际命令（工作区根目录）：

```powershell
$env:PYTHONNOUSERSITE='1'
& .\work\venvs\retinexformer37\Scripts\python.exe -u outputs/docs/infer_retinexformer.py --repo work/repos/Retinexformer --weights work/LOL_v1.pth --input outputs/samples/input/111.png --output outputs/retinexformer/111.png --threads 4
```

- 结果：`outputs/retinexformer/111.png`，600×400 RGB，320,793 bytes。权重加载 0.063 秒；单次前向 **5.368 秒**，未做重复平均或性能基准。
- 预处理/保存对应官方 demo：RGB float32 /255、NCHW、4 倍数 padding、整图前向、裁回原尺寸、clamp、四舍五入保存。输入未缩放或裁切；Gamma=1、brightness=1，无自集成、无 GT_mean。
- 日志：`logs/retinexformer_infer.log`；配置与许可在 `docs/source_materials/`。wrapper 与等价依据在 `docs/infer_retinexformer.py`、`patches/README.md`。
- 图像验收：可解码、非空、非全黑/全白、与输入不相同；数值范围 12～255；已打开视觉核查，场景细节可辨，无明显 RGB/BGR 交换或异常裁切。

## 3. LLFormer

- **验收状态：PASS，已实际本地权重推理。**
- 官方仓库：<https://github.com/TaoWangzj/LLFormer>。
- commit：`ed5e7bf61d2dc64ba3b4552b90eb68a38f6c5302`；本地 `work/repos/LLFormer`，受控文件无改动（运行生成的未跟踪 `__pycache__` 不属于源码补丁）。克隆成功日志：`logs/llformer_clone_proxy_retry.log`。
- 独立环境：`work/venvs/llformer37`，Python 3.7.9 / Torch 1.13.1+cpu / torchvision 0.14.1+cpu。没有照搬 README 中 Torch 1.8 + torchvision 0.3 的不匹配组合，也未装 CUDA 10.1；推理不需要训练用 warmup scheduler。
- 官方 **LOL** 权重目录：<https://drive.google.com/drive/folders/1J7NvvPsCtT0j8Rd9ombJ6sVIC6v0Xweb>；文件 <https://drive.google.com/file/d/1nTLY_gChn2_Va2BfS_R_W-bdjsqsLHJB/view>。
- 文件：`work/model_bestPSNR.pth`，**296,109,482 bytes**；SHA-256：`2ff4907e4c277194adaa3ff302a01eb04d54ac9908afe70acbcfed2029d81551`。未下载 UHD、FiveK 或第二份 SSIM 权重。
- Google Drive 常规大文件公开下载表单完成后，网络仍会中断。采用普通 HTTP 206 断点分段下载，校验段长度及 Content-Range，最终文件大小与官方目录一致，4453 个 ZIP 成员 CRC 均通过；见 `logs/llformer_weight_ranges_resumed.log`、`checkpoint_integrity.json`。哈希为本地实测值，未声称获得作者单独公布的 SHA-256。
- checkpoint 字段为 `epoch / state_dict / optimizer`；原 `state_dict` 前缀兼容逻辑保留；**1485 个参数张量，strict=True，全键匹配**。优化器字段未用于训练。
- 模型构造完全沿用官方 `test.py`：dim=16，blocks=[2,4,8,16]，refinement=2，heads=[1,2,4,8]，ffn=2.66，bias=False，WithBias，attention=True，skip=False。
- 同一原始输入 `outputs/samples/input/111.png`，未缩放。按官方普通 LOL 脚本将宽从 600 反射 padding 至 608，高保持 400；前向后裁回 600×400。
- 实际最终命令：

```powershell
$env:PYTHONNOUSERSITE='1'
$env:PYTHONPATH=(Resolve-Path work/repos/LLFormer).Path
& .\work\venvs\llformer37\Scripts\python.exe -u outputs/patches/test_llformer_cpu.py --input_dir outputs/samples/input --result_dir outputs/llformer --weights work/model_bestPSNR.pth --device cpu --threads 4
```

- 最终结果：`outputs/llformer/111.png`，600×400 RGB，374,980 bytes；最终脚本单次前向 **34.000 秒**，日志确认 `1/1`、`finish !`。无可用 CUDA 显存指标；未进行速度公平比较。
- 原脚本实际在 `model.cuda()` 报 `Torch not compiled with CUDA enabled`，完整证据在 `logs/llformer_original_cpu_failure.log`。独立副本改 `.to(device)`、CPU map_location，添加线程/严格加载/耗时日志。首次成功运行发现 Windows 的 `*.png`+`*.PNG` 重复列举同一文件，故再加保序去重；初次双次推理日志与最终单次验证均保留。
- 补丁：`patches/test_llformer_cpu.py`、`patches/llformer_cpu.patch`；未改模型架构、前处理、后处理或权重。`img_as_ubyte` 的 float32→uint8 精度提示属于原保存流程的量化提示，不是失败。
- 输出已打开检查：场景结构与颜色正常、尺寸正确；非空、非复制输入、非全黑全白，数值范围 8～255。普通 LOL 走 `test.py`，UHD 走 `test_UHD.py`；本次只运行前者的 CPU 兼容副本，未实施分块或融合改进。

## 4. 结果文件清单

所有相对路径以 `<M1_ROOT>` 为根；本机点击 `outputs/` 内文件即可查看。

| 模型 | 输入路径 | 输出路径 | 输入/输出尺寸 | 推理状态 | 证据日志 |
| --- | --- | --- | --- | --- | --- |
| Retinexformer | outputs/samples/input/111.png | outputs/retinexformer/111.png | 600×400 → 600×400 RGB | PASS | outputs/logs/retinexformer_infer.log |
| LLFormer | outputs/samples/input/111.png | outputs/llformer/111.png | 600×400 → 600×400 RGB | PASS | outputs/logs/llformer_infer.log |

还保留：

- `outputs/logs/output_validation.json`：解码、尺寸、通道、像素范围、文件哈希、非复制/非恒定检查；这些是完整性检查，不是画质评估指标。
- `outputs/environments/`：两环境完整 freeze、运行时版本/路径与独立性证据、本机包复制清单、干净重建 requirements、权重 manifest。
- `outputs/docs/`：两份详细复现说明、两个一键 PS1、输入输出核查脚本、原始 README/许可/配置和源码来源记录。
- `outputs/patches/`：LLFormer 最小 CPU/Windows 补丁和解释；Retinexformer wrapper 保存在 docs。
- `work/repos/`：两个真实官方 Git 仓库；`work/LOL_v1.pth` 与 `work/model_bestPSNR.pth` 为各模型正式使用的唯一完整 checkpoint。
- `work/llformer_download_parts/`：原始断点分块临时证据，共约 296 MB；另有放弃的 Torch 2.2.2 部分下载。自动安全检查拒绝了可选清理操作（仅返回策略拦截，未给出细则），故保留。模型始终使用完整 checkpoint，不读取这些分块。

Retinexformer 代码为 MIT，LLFormer 为 CC BY-NC-SA 4.0/学术研究使用；原始许可已保存。LOL 图像版权/使用条件见 `samples/README.md`，代码许可不重新授权数据集图片。

## 5. 遗留问题和 M2 前置条件

**M1 没有阻止两模型本地推理的遗留阻塞。** 本次仅各一张 LOL-v1 真实测试图，证明匹配官方 LOL 权重可运行；不是论文指标复现，也没有得出模型优劣结论。

进入 M2 前，需要由用户先确认本轮结果，再选定同一批 5～10 张有出处、可使用的真实低光照图片，固定文件列表、尺寸处理和权重设置。当前 CPU 已能完成该规模，但高分辨率任务的内存/耗时需届时评估；未测试 UHD CPU 或 GPU 路线。若以后进入 M3，再准备配对真值及统一 PSNR/SSIM、速度/显存协议。本轮未计算这些指标。

Python 3.7 与当前官方 UI 依赖不同，本次只验证推理闭环；其他电脑完整网络安装尚未重做，建议按固定 requirements 新建各自环境复验。本机环境复制的准确来源与限制已经明确记录。公开共享日志前应处理本机用户名/绝对路径等信息。

未创建 GitHub 仓库、未推送、未邀请协作者；未训练、未改网络、未实施 M2 正式多图比较、M3 指标评估或 M4 分块融合优化。可选临时文件清理的策略拦截不影响 M1 验收。

## 6. 一键复现指南

在此工作区打开 PowerShell，顺序执行：

```powershell
& .\outputs\docs\run_retinexformer.ps1
& .\outputs\docs\run_llformer.ps1
& .\work\venvs\retinexformer37\Scripts\python.exe outputs/docs/verify_outputs.py
```

脚本使用各自确切解释器，无需依赖默认 `python` 或手动激活。输入保持在 `outputs/samples/input/111.png`，权重分别在 `work/LOL_v1.pth`、`work/model_bestPSNR.pth`。重跑会覆盖对应输出图，并创建带时间的新日志。出现严格加载成功、实际前向日志、可打开的同尺寸 RGB 输出，以及核查脚本通过，才视为成功。

完整安装/权重下载/参数说明：[Retinexformer](<M1_ROOT>/outputs/docs/run_retinexformer.md)、[LLFormer](<M1_ROOT>/outputs/docs/run_llformer.md)。故障链：[blockers.md](<M1_ROOT>/outputs/docs/blockers.md)。根目录版报告的相对链接可改从 `outputs/M1_REPORT.md` 打开。
