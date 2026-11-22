# 真实日志与脱敏口径

m1/包含原M1已有成功与失败日志的脱敏副本：CPU/CUDA错误、TLS和克隆错误、失败安装路线、权重断点、初次重复PNG和最终1/1、依赖缺失及修复、环境与图像核查。不删除失败证据，不把新入口重跑写成原始M1。

个人根路径/用户目录/原解释器目录替换为 `<M1_ROOT>`、`<USER_HOME>`、`<PYTHON_HOME>`、`<LEGACY_BASE>`、`<WINDOWS>`；PowerShell transcript主机/身份字段替换为说明行。原始未脱敏文件仍留在原M1本机目录，未修改。脱敏前原文件SHA和迁移结果SHA见 docs/migration_manifest.json，便于本机审核；路径映射表只放本机私有档案，不上传。

新迁移smoke test另存migration/，运行产物留在忽略的runs/；结果归档results/m1是逐字节复制的历史输出。日志中5.37/34.00秒不是公平性能基准。仓库未保存访问Token或官方大文件下载表单临时身份字段。
