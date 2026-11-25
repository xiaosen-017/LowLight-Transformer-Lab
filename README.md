# LowLight-Transformer-Lab

**基于 Transformer 的低光照图像增强：复现、对比与推理优化**。主题：Transformer Models in CV。

项目围绕 Retinexformer 与 LLFormer 展开，依次完成官方模型复现、统一样本展示、配对数据评估，以及 LLFormer 分块推理和重叠融合优化。

## 当前进展

| 阶段 | 状态 | 产物 |
| --- | --- | --- |
| M1 基础复现 | 已完成 | 两个独立环境，官方LOL权重严格加载，同图本地推理及完整记录 |
| M2 视觉展示 | 已完成 | 5张LOL-v1测试图、10张增强结果、三列对照图和逐图观察 |
| M3 定量评估与方法分析 | LOL-v1 已完成 | 两模型各 15 对 LOL-v1、Retinexformer 另评估 200 对 LOL-v2，提供论文指标对照和同机基准 |
| M4 分块推理与融合优化 | LOL-v1 已完成 | 四组正式消融、边界与资源对照、流式融合与分辨率扩展 |

## 两个模型的研究重点

| 模型 | 论文与实现 | 核心设计 | 本项目关注点 |
| --- | --- | --- | --- |
| Retinexformer | [ICCV 2023论文](https://arxiv.org/abs/2303.06705) · [官方代码](https://github.com/caiyuanhao1998/Retinexformer) | 将Retinex思路与光照引导Transformer结合，在增强过程中利用光照信息 | 暗区细节、亮度分配与颜色恢复 |
| LLFormer | [AAAI 2023论文](https://arxiv.org/abs/2212.11548) · [官方代码](https://github.com/TaoWangzj/LLFormer) | 轴向多头自注意力与跨层特征融合，面向高分辨率低光照增强 | 增强质量、分块边界连续性与推理资源开销 |

固定上游版本：Retinexformer `2dd9ae0`，LLFormer `ed5e7bf`；完整SHA与许可保存在 `configs/upstreams.json` 和 `THIRD_PARTY_NOTICES.md`。

## M2：五张真实低光照图片的统一展示

使用官方demo收录的全部5张LOL-v1测试图：22、111、146、493、778。原输入及两模型输出均为 **600×400 RGB**。左列为原图，中列为Retinexformer，右列为LLFormer。

![M2五图总览：原图、Retinexformer、LLFormer](results/m2/figures/overview.png)

| 样本 | 场景 | 逐图观察 |
| --- | --- | --- |
| 22.png | 收纳柜与灰色玩偶 | 柜内布料、纸箱和玩偶轮廓恢复；浅墙和柜门仍有颗粒。 |
| 111.png | 窗边金属筒与管道 | 两者均恢复金属孔洞与工具；Retinexformer台面略亮，LLFormer筒身阴影更深。 |
| 146.png | 衣物、衣架与浅色墙 | 衣架细线和衣物条纹显现；背景墙仍有细颗粒。 |
| 493.png | 彩色静物、玩偶与色卡 | LLFormer的红黄色更鲜艳、浅色区域更亮；Retinexformer整体较暗，绒毛与阴影仍有颗粒。 |
| 778.png | 体育馆看台与通道 | 座椅、栏杆和场地边线恢复；大面积暗墙与看台表面仍有明显颗粒。 |

这批结果显示，两模型都提高了暗区的可辨性，差别主要体现在亮度分配、色彩浓度和颗粒表现。493.png适合观察彩色静物与浅色绒毛，778.png适合观察密集座椅、栏杆和大面积暗背景。完整 15 对图评估与统一性能记录见 M3。

**本轮设置**：官方LOL-v1匹配权重、CPU、float32、4线程；原尺寸输入、Gamma=1、输出亮度=1、自集成关闭。Retinexformer按4倍数padding，LLFormer按16倍数padding后裁回原尺寸。10张增强结果均保存为无损PNG。

五张输入来自LOL-v1测试集，来源为固定Retinexformer官方commit的 `demo/examples/`。总览按统一比例缩小用于网页展示；`results/m2/figures/` 保存600像素宽单列的逐图对照，`results/m2/retinexformer/` 与 `results/m2/llformer/` 保存原始增强结果。图片版权归原数据集作者，本项目用于低光照增强方法的学术研究与效果展示。

## 研究路线与阶段验收

### M1：建立可重跑的官方模型基线

记录官方代码commit、权重大小与SHA-256；分别保存环境依赖、输入输出和成功/失败日志。Retinexformer与LLFormer的独立CPU环境已运行通过，M1档案保存在 `docs/M1_REPORT.md`。

### M2：统一样本和视觉观察

固定5张输入的来源、尺寸与哈希；两模型读取同一原始输入，使用匹配的LOL权重；生成原图/Retinexformer/LLFormer三列图。逐图记录亮度、暗部纹理、噪声、色彩、高亮区域与边缘表现。本轮已完成5图推理和图像核验，记录保存在 `experiments/m2_visual/`。

### M3：定量评估与方法讨论

两套官方预训练权重均在 **LOL-v1 eval15** 完成定量复现，逐图指标在 `results/m3/lolv1_eval15_windows/`。

| 模型 | 论文口径 PSNR / SSIM | 项目统一口径 PSNR / SSIM |
| --- | --- | --- |
| Retinexformer | **25.15527 dB / 0.845458** | 25.1531 dB / 0.84546 |
| LLFormer | **23.64912 dB / 0.816309** | 23.6491 dB / 0.81846 |

LLFormer 原论文另外两项也已复算，LPIPS **0.169239**，MAE **0.063452**。同机计时采用 Windows CPU 四线程及一次预热五次测量。

Retinexformer 另完成 **LOL-v2 Real 与 Synthetic 各 100 对**。Real 得到 **22.79550 / 0.839669**，Synthetic 得到 **25.67270 / 0.929550**。两组指标按论文精度均吻合。逐图结果和运行命令见 `results/m3/retinexformer_lolv2_windows/`。

论文其余数据集和原始训练的验收范围列在 `docs/evaluation_protocol.md`。LLFormer 的待评估数据包括 MIT-Adobe FiveK 及原生 UHD-LOL4K/8K。

论文分析围绕三个问题展开：光照引导与轴向注意力分别解决什么问题；网络设计如何影响细节、颜色与资源开销；哪些场景暴露两种方法的局限。方法与局限分析见 `docs/LLFORMER_METHOD.md`，完整协议见 `docs/evaluation_protocol.md`。

### M4：LLFormer分块推理与重叠融合优化

**目标**：在固定LLFormer网络和官方预训练权重下，研究图块大小、重叠率与融合方式对接缝、图像质量和资源开销的影响。

**实现与验证**

1. 保存上游 `test_UHD.py` 的分块与均值融合基线。原参考配置为720×1280图块、360×640步长。
2. 单独处理设备适配、末端图块覆盖和重建尺寸；网格补足最后一个锚点，重建后裁回原图。
3. 在相同网格下实现二维平滑窗加权融合。先累积浮点预测与权重和，再统一归一化；同时处理Hann窗零端点和图像外边界。
4. 先以小图完成正确性检查，再增加图像分辨率。小图实验块大小为128/256/384，重叠率为0/25%/50%。

融合形式为 `output = Σ(weight × prediction) / Σ(weight)`。正确性验收包括：像素覆盖率100%、权重和严格为正、无NaN/Inf；恒等与常数重建、单块、奇数尺寸及小于图块的输入测试通过。

| 消融组 | 图块网格 | 融合策略 | 观察因素 |
| --- | --- | --- | --- |
| A 基线 | 固定参考网格 | 均值融合 | 基准效果和开销 |
| B 仅改网格 | 调整块大小/重叠率 | 均值融合 | 网格参数影响 |
| C 仅改融合 | 与A相同 | 平滑加权融合 | 融合策略影响 |
| D 组合 | 与B相同 | 与C相同 | 网格与融合共同作用 |

小图消融沿用当前LOL权重；UHD实验单独登记UHD-LOL4K官方权重和对应样本。四组实验使用同一批输入、权重、设备与评估口径，记录PSNR、SSIM、固定边界带的视觉伪影、运行时间和峰值内存。参数在开发子集上选择，冻结配置后运行正式测试。四组正式消融与边界指标见 `results/m4/lol_eval15_v1/REPORT.md`。256 像素块均值融合的平均 PSNR 为 **23.3641 dB**，256 像素块 Hann 融合的平均 SSIM 为 **0.81775**。固定网格时，Hann 提高了平均 SSIM，但平均 PSNR 略低。流式推理每次仅保留当前图块预测，在原尺寸与原堆叠实现完全一致，并实测长边 2048。2048 样本上 Hann 的跨线梯度误差为 2.23，均值融合为 9.31。完整记录见 `results/m4/streaming_windows/`。

Retinexformer 的四组短程模块消融是补充实验，历史 A1/A2 标签与记录存在冲突，当前按组编号展示。修复后的隔离入口、开关记录和四组前向检查见 `docs/RETINEXFORMER_ABLATION.md`。

## 复现环境与运行方式

原始 M1/M2 运行环境：Windows 11、Ryzen 5 5625U、Python 3.7.9、PyTorch 1.13.1+cpu、torchvision 0.14.1+cpu。两个模型使用独立环境；精确依赖保存在 `environments/`。

```powershell
git clone https://github.com/xiaosen-017/LowLight-Transformer-Lab.git
cd LowLight-Transformer-Lab
./scripts/setup_upstreams.ps1
py -3.7 -m venv .venvs/retinexformer
py -3.7 -m venv .venvs/llformer
& ./.venvs/retinexformer/Scripts/python.exe -m pip install --index-url https://pypi.org/simple -r environments/requirements_cpu_py37.txt
& ./.venvs/llformer/Scripts/python.exe -m pip install --index-url https://pypi.org/simple -r environments/requirements_cpu_py37.txt
```

将官方权重放入下列位置，文件大小与SHA-256由运行脚本自动核对：

| 模型 | 权重位置 |
| --- | --- |
| Retinexformer | `weights/retinexformer/LOL_v1.pth` |
| LLFormer | `weights/llformer/model_bestPSNR.pth` |

```powershell
# M1单图
./scripts/run_retinexformer.ps1
./scripts/run_llformer.ps1
# M2五图
./scripts/run_m2.ps1 -OutputDir runs/m2/reproduce
& ./.venvs/retinexformer/Scripts/python.exe scripts/validate_m2.py --run runs/m2/reproduce --output runs/m2/reproduce/validation.json
& ./.venvs/retinexformer/Scripts/python.exe scripts/render_m2.py --run runs/m2/reproduce --output runs/m2/reproduce/figures
```

已有环境和权重可通过参数直接引用。M2脚本提供 `-RetPython`、`-LLPython`、`-RetUpstream`、`-LLUpstream`、`-RetWeights`、`-LLWeights`；单图入口提供 `-PythonExe`、`-Upstream`、`-Weights`、`-InputPath`。新运行输出保存在 `runs/`，归档结果保存在 `results/`。

## 协作流程

1. 组员将GitHub用户名发给仓库所有者，接受Collaborator邀请。
2. 从最新main创建自己的功能/实验分支，完成修改并推送该分支。
3. 创建目标为main的Pull Request，写明改动、运行命令、实际结果和对应Issue。
4. 仓库所有者xiaosen-017审核，确认后使用Squash and merge合并，并删除已合并分支。

main使用PR审核规则，代码所有者为xiaosen-017。权重、完整数据集、环境与运行缓存按现有.gitignore保存在本地。

## 项目目录

```text
configs/        上游版本、官方权重、M2五图清单
scripts/        推理、指标评估、视觉对照和分块融合
patches/        LLFormer CPU与Windows兼容适配
environments/   两套依赖与环境记录
results/m1/     单图复现档案
results/m2/     十张增强图、五张对照图、总览和运行记录
results/m3/     LOL-v1、Retinexformer LOL-v2 与同机对照
results/m4/     LLFormer 分块消融、资源记录和流式扩展
logs/           原M1与M2推理日志
experiments/    视觉观察、定量评估和消融实验记录
docs/           详细报告、运行说明和实验设计
.github/        Issue与PR模板
```
