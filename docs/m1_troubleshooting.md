# M1 故障与修复记录

最终两个模型均完成本地官方权重前向推理，无未解决的 M1 推理阻塞。

| 障碍 | 实际错误/证据 | 原因判断 | 修复及结果 |
| --- | --- | --- | --- |
| GitHub 直连克隆 | clone.log / clone_retry.log：SSL_ERROR_SYSCALL、10054、443 超时 | Git 未使用 Windows 已配置代理；网络亦会中断 | 读取已有代理 127.0.0.1:7897，仅对命令显式配置；官方浅克隆成功，SHA 已核验 |
| pip 原默认镜像与官方 PyPI TLS | retinexformer_install*.log：SSL UNEXPECTED_EOF_WHILE_READING | 镜像/直连 TLS 不稳定 | 尝试官方源、CPU 源、TLS 验证保持开启的 curl 本地传输桥；这些尝试都不是最终成功安装路径，桥已停止 |
| Torch 2.2.2 大包传输慢 | install_proxy.log、install_strategy_change.txt，部分 wheel 仍留在 work | 传输低速且反复失败 | 主动取消 Python 3.11 路线。用本地既有且已可导入的 1.13.1+cpu 包做物理独立复制，两套 Python 3.7.9 venv，未启用 system-site-packages |
| 复制依赖元数据不全 | 初次 pip_check.log：matplotlib/idna 缺失 | 旧包 .egg-info 与用户级活跃包位置不同 | 按原环境活跃发行包定位，补齐独立 matplotlib 依赖与元数据；两个 pip_check_final.log 均无缺失；来源/哈希/独立性可查 |
| 权重网络断线 | weight_download*.log：TLS handshake、timeout、curl 56 | 官方源跨网传输中断 | Retinexformer 使用已有代理下载并对照官方 LFS SHA-256；LLFormer 使用公开表单与标准 HTTP 206 分段续传，每段校验后合并，最终 ZIP CRC/大小与严格加载通过 |
| LLFormer 写死 CUDA | llformer_original_cpu_failure.log：Torch not compiled with CUDA enabled，test.py 的 model.cuda() | 本机只有 AMD 集显，Torch CPU 构建无 CUDA | 独立副本添加 --device cpu、.to(device)、map_location=cpu；原网络不改，实际权重加载/前向成功 |
| Windows glob 重复 PNG | llformer_infer_initial_duplicate_glob.log：同一 111.png 出现 1/2、2/2 | Windows 文件 glob 大小写不敏感，原脚本合并 *.png 与 *.PNG | 保序去重文件列表；最终再次实际运行，一张图只处理 1/1 |
| float32→uint8 提示 | LLFormer 原保存函数 img_as_ubyte 的 Possible precision loss | 归一化浮点输出按原算法量化保存到 PNG | 保留官方保存方式；输出数值及视觉核查通过，不将提示判为失败 |
| 可选临时分块清理 | 自动安全检查返回 blocked by policy，未提供细则 | 删除动作被自动策略拦截，未执行 | 保留 work/llformer_download_parts 和部分 wheel；推理只读两个完整 checkpoint，交付不受影响 |

所有兼容处理仅服务 M1。未通过其他网络改写算法、未变更系统驱动或原 Anaconda、未绕过登录/验证码/权限。干净电脑的固定依赖完整网络重建尚未实测，区别于本机当前已通过的两个环境。
