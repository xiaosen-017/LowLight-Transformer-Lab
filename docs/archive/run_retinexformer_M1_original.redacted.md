# Retinexformer M1 复现说明

## 当前电脑直接重跑

在本任务目录打开 PowerShell，执行：

```powershell
& .\outputs\docs\run_retinexformer.ps1
```

脚本从自身位置推导任务根目录，使用 `work/venvs/retinexformer37/Scripts/python.exe`，不依赖当前终端激活状态。输出覆盖 `outputs/retinexformer/111.png`，每次创建独立 `outputs/logs/retinexformer_rerun_时间.log`。

本次已实际成功执行的核心命令是：

```powershell
$env:PYTHONNOUSERSITE='1'
$env:PYTHONPATH=(Resolve-Path work/repos/Retinexformer).Path
& .\work\venvs\retinexformer37\Scripts\python.exe -u outputs/docs/infer_retinexformer.py --repo work/repos/Retinexformer --weights work/LOL_v1.pth --input outputs/samples/input/111.png --output outputs/retinexformer/111.png --threads 4
```

日志：`../logs/retinexformer_infer.log`。成功条件：`strict load: <All keys matched successfully>`、122 个 state tensor、真实前向后出现 `SUCCESS`，PNG 可打开且为 600×400 RGB。

## 仓库和权重

- 官方仓库：[caiyuanhao1998/Retinexformer](https://github.com/caiyuanhao1998/Retinexformer)。
- commit：`2dd9ae05f34a34e2df3b955f743215ac3cda0f82`；本地 `work/repos/Retinexformer`。
- 已实际克隆：通过现有本机代理执行 `git -c http.proxy=http://127.0.0.1:7897 clone --depth 1 https://github.com/caiyuanhao1998/Retinexformer.git work/retinexformer_git`。先前已取得同 SHA 官方 ZIP；随后将成功克隆的 `.git` 放入相同源码目录并用 `git checkout -- .` 恢复 Git 标准检出行尾。受控文件无修改。
- 只获取 `LOL_v1.pth`，保存在 `work/LOL_v1.pth`，6,475,021 bytes。
- 实际下载地址：<https://huggingface.co/CaiYuanhao/Retinexformer/resolve/main/LOL_v1.pth>。
- 对应固定发布版本：`7983bc70dca2cf043000f1efe793d51172d2f83b`，固定链接：<https://huggingface.co/CaiYuanhao/Retinexformer/resolve/7983bc70dca2cf043000f1efe793d51172d2f83b/LOL_v1.pth>。
- SHA-256：`9b4810dc51322fab70be8658ee0ad1df64a54aa814497b7849767baa2ff32cd1`，已与官方 LFS oid/大小核对，发布记录在 `retinexformer_official_weight_tree.json`。
- 配置：官方 `Options/RetinexFormer_LOL_v1.yml`，网络参数原样使用。

重新下载可执行（代理变量只在已有同地址代理的本机使用）：

```powershell
$env:HTTPS_PROXY='http://127.0.0.1:7897'
curl.exe -fL --retry 3 --retry-all-errors 'https://huggingface.co/CaiYuanhao/Retinexformer/resolve/7983bc70dca2cf043000f1efe793d51172d2f83b/LOL_v1.pth' -o work/LOL_v1.pth
Get-FileHash work/LOL_v1.pth -Algorithm SHA256
```

## 环境安装及差异

实际：Python 3.7.9、Torch 1.13.1+cpu、torchvision 0.14.1+cpu、NumPy 1.21.6、Pillow 9.5.0、einops 0.6.1、PyYAML 6.0.1。`pip check` 最终无缺失依赖。

最初已尝试独立 Python 3.11 + Torch 2.2.2，但 PyPI/原镜像发生 TLS EOF，大 wheel 传输极慢，故主动取消该路线。没有把失败尝试写成成功安装。

本机最终环境由 `py -3.7 -m venv work/venvs/retinexformer37` 创建。针对网络限制，将本机原来可运行的 CPU 包按活跃发行包 RECORD 实际复制到该 venv，未链接系统 site-packages；后补实际发行包元数据，并独立安装 einops/natsort。复制清单、源路径和文件清单哈希见 `../environments/*copy_manifest.json`。同一方法独立生成另一套 LLFormer 环境，二者不共享包文件。开发头文件和静态链接库不属于推理所需，未要求完整编译环境。

其他组员在干净电脑可按下面路径重建；这些是可执行重建说明，**并非本次已执行的完整网络安装记录**：

```powershell
py -3.7 -m venv work/venvs/retinexformer37
& .\work\venvs\retinexformer37\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r outputs/environments/requirements_rebuild.txt
& .\outputs\docs\run_retinexformer.ps1
```

`requirements_rebuild.txt` 明确使用官方 CPU wheel；`pip freeze` 的原包元数据版本可能不带 `+cpu`，运行时的真实版本以环境检查日志为准。

没有启动 Gradio；薄 wrapper 直接导入官方架构，采用官方 demo 相同预处理和保存方式。当前官方 demo UI 要求较新 Python，但该架构在本次 Python 3.7 上实际通过。BasicSR namespace 可导入，架构可加载；未配置或声称训练入口全部可用。兼容依据见 `../patches/README.md`。

## 常见问题

- 直接 `python` 指向原 Anaconda 3.7.4，不能据此判断本任务环境；始终使用脚本中的确切解释器。
- 本机无 CUDA，不要添加 `.cuda()`。
- 网络默认镜像为清华源，曾发生 TLS EOF；可用官方 PyPI，并让当前进程使用电脑已有代理。未修改系统代理、驱动、全局 Python 或 CUDA。
- 不加 `--GT_mean`，不加自集成，不额外调 Gamma/亮度；本轮不计算论文指标。
