# M1 输入出处及后续数据管理

原输入：600×400 RGB 的 `111.png`；SHA-256 `5f10ef298a617c239e0728610a565416b4503ed40384cc9710e8bbd55f22ef47`。来自固定 Retinexformer 官方 commit 的 `demo/examples/111.png`，其 README 明确说明为 LOL-v1 测试集 `test/low/` 的未修改图。

原数据集：[Deep Retinex Decomposition for Low-Light Enhancement (BMVC 2018)](https://daooshee.github.io/BMVC2018website/)。[作者附带示例归属说明](../docs/source_materials/LOL_example_attribution.md) 已归档。

为避免给未明确再分发授权的原始图片新增拷贝，本仓库不提交输入图片或完整数据集；运行 `scripts/setup_upstreams.ps1` 后脚本默认读取官方克隆自带的该样例。增强输出和对照图用于非商业学术研究展示，保留数据来源；代码许可不重新授权原始图像。

M2 先登记 5–10 张图片的来源、使用范围、哈希和尺寸，再批量运行。M3 记录官方测试划分、匹配 GT 和统一协议；输入、GT 和生成结果使用不同目录，不能把增强输出误作输入。所有新增数据放在被忽略的 data/ 下，在实验清单记录可再获取路径，禁止上传私有照片或完整数据集。

## M2五图展示

已使用官方demo的全部五张LOL-v1测试图，来源/文件SHA见configs/m2_samples.json。原始输入PNG继续从官方上游获取；三列对照面板包含原图和两模型输出，用于本项目的非商业学术研究展示。M2原始增强PNG、对照面板与总览保存在results/m2/。
