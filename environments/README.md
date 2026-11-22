# 环境与重建范围

M1 使用两个独立 Python 3.7.9 venv，Torch 1.13.1+cpu / torchvision 0.14.1+cpu。freeze 为真实发行包元数据，旧版记录可能不带 +cpu；实际导入版本以脱敏 runtime.json 为准。requirements_cpu_py37.txt 显式选择官方 CPU wheel。

M1 因网络失败，实际使用本机已有发行包的物理独立复制，补齐依赖/元数据，并通过两份 pip check 与真实推理；复制清单保留版本/哈希，源绝对路径脱敏。没有把整套环境提交到仓库，也不要求组员照抄作者的本机包目录。

干净电脑可参考：

```powershell
py -3.7 -m venv .venvs/retinexformer
py -3.7 -m venv .venvs/llformer
& ./.venvs/retinexformer/Scripts/python.exe -m pip install --index-url https://pypi.org/simple -r environments/requirements_cpu_py37.txt
& ./.venvs/llformer/Scripts/python.exe -m pip install --index-url https://pypi.org/simple -r environments/requirements_cpu_py37.txt
```

以上完整网络重建路径尚未在本阶段重新安装验证；当前机器会通过 -PythonExe 引用原成功环境完成最小迁移 smoke test。Python 3.7 已老旧，此配置用于保留 M1；新硬件/新 Python/CUDA 路线应单独环境和记录，验证后通过 PR 更新，不破坏 M1 环境。不要无差别 pip install -U。
