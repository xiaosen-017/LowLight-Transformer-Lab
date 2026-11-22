# 上游归属与许可

- Retinexformer：Yuanhao Cai 等，ICCV 2023；原代码MIT。官方代码通过固定commit脚本获取，不作为本仓库原创源码。许可全文保存在 docs/source_materials/Retinexformer_LICENSE.txt。
- LLFormer：Tao Wang、Kaihao Zhang、Tianrun Shen、Wenhan Luo、Bjorn Stenger、Tong Lu，AAAI 2023；CC BY-NC-SA 4.0，学术研究用途。patches/test_llformer_cpu.py为官方test.py的M1兼容派生，保留作者署名；改动是CPU映射、线程/日志、严格加载及Windows文件列表去重，按同许可使用。原许可见 docs/source_materials/LLFormer_LICENSE.txt 和 https://creativecommons.org/licenses/by-nc-sa/4.0/ 。
- 原论文/代码引用和固定commit见README、configs/upstreams.json；不将上游工作当作团队原创模型。
- LOL-v1照片及其派生增强图不因代码MIT许可而获得新的图像许可证。输入不再分发，通过官方来源获取；已归档输出仅作私有组内非商业课程研究证据，来源完整保留，转公开前须核实权利。
- 团队新增文档/编排脚本暂未授予额外公开再分发许可；后续如选许可证，需在不违反以上上游/数据条款前提下由团队明确决定。
