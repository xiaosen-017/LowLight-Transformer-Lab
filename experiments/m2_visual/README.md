# M2 统一视觉展示

状态：DONE / PASS。五张LOL-v1输入（22、111、146、493、778）已分别完成两个官方预训练模型的本地CPU推理，共10张600×400 RGB增强PNG。

样本清单：configs/m2_samples.json；运行记录：results/m2/run_record.json；图像核查：results/m2/validation.json；三列图和总览：results/m2/figures/；六维观察：本目录observations.csv与observations.json；详细报告：docs/M2_REPORT.md。

统一原输入、原尺寸、LOL匹配权重、4线程/float32，Gamma=1、亮度=1，自集成关闭。总览和逐图面板仅做版式拼接。后续质量指标和统一计时在M3开展。
