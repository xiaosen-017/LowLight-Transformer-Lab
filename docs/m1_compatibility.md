# 兼容处理范围

两个官方仓库的受版本控制文件均未改动。

## Retinexformer

`../scripts/infer_retinexformer.py` 是单张图、无界面的薄 wrapper。直接动态导入原仓库 `basicsr/models/archs/RetinexFormer_arch.py`，读取原始 `Options/RetinexFormer_LOL_v1.yml`，使用官方 checkpoint 的 `params` 并 `strict=True` 加载。

与当前官方 `app.py` 对应：RGB float32 /255、NCHW、4 的倍数反射 padding、单次前向、裁回原尺寸、clamp[0,1]、四舍五入保存 RGB PNG。输入 Gamma=1、输出亮度=1、关闭自集成；本图未缩放。不安装 Gradio UI 和整套训练依赖。Python 3.7 用前缀判断/切片代替 `str.removeprefix`，含义相同。BasicSR namespace 与原始架构导入已验证；未宣称整套 BasicSR 训练栈可运行。

## LLFormer

`test_llformer_cpu.py` 从官方 `test.py` 生成，`llformer_cpu.patch` 是与原始脚本的逐行差异。新增 `--device` 和 `--threads`，把写死的 `.cuda()` 改为 `.to(device)`，checkpoint 通过 `map_location='cpu'` 反序列化，保留原有 `state_dict`/`module.` 前缀兼容逻辑，明确 `strict=True`，增加成功加载、有限数值检查和耗时日志。通过 `PYTHONPATH` 导入官方 `model/LLFormer.py`。

Windows 的 glob 大小写不敏感，原 `*.png` + `*.PNG` 列表会把同一图列出两次；首次真实推理日志显示 `1/2`、`2/2` 均为 `111.png`。兼容脚本保序去重文件列表，最终再次验证只运行 `1/1`。

模型构造参数、RGB 预处理、16 倍数反射 padding、整图前向、clamp、原尺寸裁回、`img_as_ubyte` 和 OpenCV RGB→BGR 保存逻辑均与原脚本一致。未使用 `test_UHD.py`，未实施任何分块、融合或训练改动。
