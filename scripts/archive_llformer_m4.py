"""Publish only compact evidence from a verified local run to a NEW directory."""
import argparse
import csv
import json
import shutil
import statistics
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument("study",type=Path)
    p.add_argument("archive",type=Path)
    args=p.parse_args()
    src,out=args.study,args.archive
    summary=json.loads((src/"verified/summary.json").read_text())
    assert summary["verified_eval_pngs"]==60 and summary["verified_dev_pngs"]==9
    out.mkdir(parents=True,exist_ok=False)
    stages=["dev"]+[f"{mode}-{arm}" for mode in ("eval","bench") for arm in "ABCD"]
    for name in stages:
        dest=out/name
        dest.mkdir()
        for f in ("config.json","metrics.csv"):
            shutil.copyfile(src/name/f,dest/f)
        shutil.copyfile(src/(name+".log"),dest/"run.log")
    for path in ("b0-real/results.json","scale/resolution.json","verified/summary.json","edges/edge_metrics.csv"):
        dest=out/path
        dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(src/path,dest)
    edge=list(csv.DictReader((src/"edges/edge_metrics.csv").open()))
    arms=summary["arms"]
    def edge_mean(arm,key):
        return statistics.mean(float(r[key]) for r in edge if r["arm"]==arm)
    lines=["# LLFormer 实测：分块网格与融合", "",
        "固定官方 LOL 权重、CPU 四线程和全部 15 对 eval15。先在训练划分的 2.png 扫描九种网格，再按已冻结的四组设置报告正式结果。全图结果来自同机 M3；未使用测试集选参数。","",
        "|组别|块 / 步长|融合|PSNR dB ↑|SSIM ↑|边界带 MAE ↓|内部 MAE ↓|跨线梯度误差 ↓|",
        "|---|---|---|---:|---:|---:|---:|---:|"]
    configs=[("A","128 / 64","均值"),("B","256 / 128","均值"),("C","128 / 64","Hann"),("D","256 / 128","Hann")]
    base=json.loads((Path(__file__).resolve().parents[1]/"experiments/m3_evaluation/llformer/summary.json").read_text())
    for a,t,f in [("full","整图","无")]+configs:
        r=base if a=="full" else arms[a]
        lines.append(f"|{a}|{t}|{f}|{r['psnr']:.4f}|{r['ssim']:.5f}|{edge_mean(a,'edge_mae'):.3f}|{edge_mean(a,'interior_mae'):.3f}|{edge_mean(a,'boundary_gradient_mae'):.3f}|")
    lines+=["","所有组使用两个网格的内部起止线并集，边界带取每条线两侧各 2 像素。MAE 单位为 8-bit 通道灰阶；跨线梯度误差为预测与 GT 在跨线相邻像素对上的一阶差之差的绝对值。边界带 MAE 也受整体亮度影响，不能单独证明消除了可见接缝。","",
        "|配对变化（前组减后组）|平均 ΔPSNR|PSNR 改善图数|平均 ΔSSIM|SSIM 改善图数|平均 Δ边界 MAE|",
        "|---|---:|---:|---:|---:|---:|"]
    for key,r in summary["paired"].items():
        lines.append(f"|{key}|{r['psnr']['mean']:+.4f}|{r['psnr']['improved']}/15|{r['ssim']['mean']:+.5f}|{r['ssim']['improved']}/15|"+
                     (f"{r['edge_mae']['mean']:+.3f}" if 'edge_mae' in r else "见上表")+"|")
    lines+=["","固定网格时 C−A 和 D−B 隔离融合影响；固定融合时 B−A 和 D−C 隔离块大小影响。平均方向与逐图方向可能不同：",""]
    for key in ("C-A","D-B","D-A"):
        r=summary["paired"][key]["psnr"]
        lines.append(f"- {key} 的逐图 PSNR 差范围 [{r['min']:+.3f}, {r['max']:+.3f}] dB，最低差出现在 {r['worst_image']}。")
    lines+=["","## 资源","",
        "固定 111.png，Apple M5 CPU 四线程。各组独立进程、一次预热、五次测量；秒数为中位数 [最小, 最大]。纯网络时间是各块前向之和；分块管线含提块、融合及裁回；端到端另含读图和写 PNG。RSS 为进程生命周期峰值，不能作单块张量内存解释。","",
        "|组别|纯网络 s|分块管线 s|端到端 s|峰值 RSS GiB|","|---|---:|---:|---:|---:|"]
    for a,_,_ in configs:
        b=arms[a]["bench"]
        cell=lambda k:f"{b[k]['median']:.2f} [{b[k]['min']:.2f}, {b[k]['max']:.2f}]"
        lines.append(f"|{a}|{cell('net_s')}|{cell('tile_pipeline_s')}|{cell('end_to_end_s')}|{b['peak_process_gib']:.2f}|")
    lines+=["","## 边界与复核","",
        "具体图（包括退化样本）见每组 metrics.csv；固定 111.png 全图和 1:1 局部图由 inspect_llformer_edges.py 生成到本地，不向仓库复制输入或 GT。开发扫描只有一张训练图，不能从它推断全测试集的最优重叠率。","",
        "原版 B0 和仅改设备后执行的结果见 ../b0/ 及 b0-real/results.json；B0 失败不纳入均值或给作 0 分。分辨率扩展和停止原因见 scale/resolution.json。LOL 图放大仅用于测资源，不是 UHD 数据集、UHD 权重或论文 4K 结果。","",
        "作者自检：对 60 张正式输出和 9 张开发输出从保存的 PNG 独立复算 PSNR/SSIM 和边界掩膜；核实 24 次定点计时输出与对应正式图一致。无人类第二复核人，不代签；本机无 CUDA。"]
    (out/"REPORT.md").write_text("\n".join(lines)+"\n")


if __name__=="__main__":
    main()
