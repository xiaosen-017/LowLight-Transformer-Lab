# LLFormer M1 复现说明

## 当前电脑直接重跑

在本任务目录打开 PowerShell：

```powershell
& .\outputs\docs\run_llformer.ps1
```

使用独立 `work/venvs/llformer37` 环境；输入 `outputs/samples/input/111.png`；权重 `work/model_bestPSNR.pth`；输出 `outputs/llformer/111.png`。每次另存带时间的 rerun 日志。

核心命令：

```powershell
$env:PYTHONNOUSERSITE='1'
$env:PYTHONPATH=(Resolve-Path work/repos/LLFormer).Path
& .\work\venvs\llformer37\Scripts\python.exe -u outputs/patches/test_llformer_cpu.py --input_dir outputs/samples/input --result_dir outputs/llformer --weights work/model_bestPSNR.pth --device cpu --threads 4
```

验收看 `strict checkpoint load: <All keys matched successfully>`，然后确有前向耗时和 `1/1`、`finish !`，并打开实际保存 PNG。不能把原脚本报错前的模型初始化视为成功。

## 官方来源和配置

- 官方仓库：[TaoWangzj/LLFormer](https://github.com/TaoWangzj/LLFormer)。
- commit：`ed5e7bf61d2dc64ba3b4552b90eb68a38f6c5302`；`work/repos/LLFormer`。
- 实际克隆使用本机现有代理，并加 `-c http.version=HTTP/1.1`；成功克隆的 `.git` 与同 SHA 官方源码归档合并后恢复标准 Git 检出，原受控文件无修改。克隆日志见 `../logs/llformer_clone_proxy_retry.log`。
- 官方 README 的 **LOL** 权重目录：<https://drive.google.com/drive/folders/1J7NvvPsCtT0j8Rd9ombJ6sVIC6v0Xweb>。
- 下层 `models`：<https://drive.google.com/drive/folders/1AZchyGAR5vtQpIEZTdDYH9t605nk_YBR>。
- 只取 `model_bestPSNR.pth`：[官方文件](https://drive.google.com/file/d/1nTLY_gChn2_Va2BfS_R_W-bdjsqsLHJB/view)。不取第二份 SSIM 权重或 UHD 权重。
- 下载入口：<https://drive.google.com/uc?export=download&id=1nTLY_gChn2_Va2BfS_R_W-bdjsqsLHJB>。Google Drive 展示常规“大文件无法扫描病毒”的 Download anyway 表单；采用该公开下载表单，无登录、验证码或权限绕过。文件大小由官方目录记录为 296,109,482 bytes。
- 本次源连接不稳定，普通下载后改用服务器支持的 HTTP 206 byte ranges，保留现有前缀，逐段检查字节数和 Content-Range，再组合为单份 checkpoint。过程见 `../logs/llformer_weight_ranges_resumed.log`。哈希和最终完整性检查见主报告。
- LOL 网络与官方 `test.py` 一致：dim=16，num_blocks=[2,4,8,16]，num_refinement_blocks=2，heads=[1,2,4,8]，ffn_expansion_factor=2.66，bias=False，LayerNorm_type=WithBias，attention=True，skip=False。
- 读取 `state_dict`，保留官方 `module.` 去前缀兼容，严格加载；不替换成其他网络。

## 环境和最小兼容处理

实际 Python 3.7.9 / Torch 1.13.1+cpu / torchvision 0.14.1+cpu，与 Retinexformer **独立**。环境复制方式、两份真实 freeze 和网络失败记录见主报告和 `run_retinexformer.md`。

官方 README 的 Python 3.7 / Torch 1.8 / torchvision 0.3 / CUDA 10.1 组合不匹配本机，也不是正确的 Torch/torchvision 配对；本次使用本地已验证可用的 1.13.1/0.14.1 CPU 组合。未装 CUDA、未改驱动。推理不引用训练用 warmup scheduler，未安装训练组件或启动训练。

原 `test.py` 实际在 `model.cuda()` 报 `Torch not compiled with CUDA enabled`，见 `../logs/llformer_original_cpu_failure.log`。适配脚本是原 `test.py` 的副本，加入 CPU 选择、CPU checkpoint 映射、4 线程和日志。首次真实推理还发现 Windows glob 把同一 PNG 列举两次，现保序去重；最终重新验证只处理 `1/1`，单次前向约 34.00 秒。原仓库不改动，逐行 diff 在 `../patches/llformer_cpu.patch`。

输入保持 600×400；官方 16 倍数反射 padding 将宽度补到 608，前向后裁回 600×400。未缩放、未切块；RGB→BGR 只在 OpenCV 保存前执行一次。

其他组员干净环境重建（尚未在本任务做完整网络重装）：

```powershell
py -3.7 -m venv work/venvs/llformer37
& .\work\venvs\llformer37\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r outputs/environments/requirements_rebuild.txt
& .\outputs\docs\run_llformer.ps1
```

若权重下载返回 HTML，不要改名当权重使用；重新核对官方文件来源和完整文件大小。若换成 CUDA 环境，可用脚本 `--device cuda`，但本轮只验收 CPU。

`test_UHD.py` 面向 UHD 权重/大图，含原版分块和均值融合逻辑，已阅读，未运行或改进；该内容留给后续阶段。
