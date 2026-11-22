# 官方权重：自行下载，不提交

脚本根据 [configs/weights.json](../configs/weights.json) 校验字节数与 SHA-256。缺少或不匹配即停止。

| 模型 | 本地相对位置 | 官方来源 | bytes / SHA-256 |
| --- | --- | --- | --- |
| Retinexformer LOL-v1 | weights/retinexformer/LOL_v1.pth | [固定官方 HF 发布](https://huggingface.co/CaiYuanhao/Retinexformer/resolve/7983bc70dca2cf043000f1efe793d51172d2f83b/LOL_v1.pth) | 6475021 / `9b4810dc51322fab70be8658ee0ad1df64a54aa814497b7849767baa2ff32cd1` |
| LLFormer LOL | weights/llformer/model_bestPSNR.pth | [官方 README 链接的文件](https://drive.google.com/file/d/1nTLY_gChn2_Va2BfS_R_W-bdjsqsLHJB/view) | 296109482 / `2ff4907e4c277194adaa3ff302a01eb04d54ac9908afe70acbcfed2029d81551` |

```powershell
New-Item -ItemType Directory -Force weights/retinexformer,weights/llformer | Out-Null
curl.exe -fL 'https://huggingface.co/CaiYuanhao/Retinexformer/resolve/7983bc70dca2cf043000f1efe793d51172d2f83b/LOL_v1.pth' -o weights/retinexformer/LOL_v1.pth
# LLFormer 通过上表官方网页常规下载后放到规定位置。
Get-FileHash weights/retinexformer/LOL_v1.pth -Algorithm SHA256
Get-FileHash weights/llformer/model_bestPSNR.pth -Algorithm SHA256
```

官方 Google Drive 出现登录、验证码或配额限制时通过正常交互处理，不使用未知网盘替代。若已在本机 M1 保存权重，用运行脚本的 -Weights 指向原文件即可，无需复制大权重。M4 若转 UHD-LOL4K，应另立权重/数据来源记录，不能混用当前 LOL 权重。
