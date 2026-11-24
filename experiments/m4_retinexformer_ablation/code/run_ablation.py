# -*- coding: utf-8 -*-
"""
M4 短程消融实验自动执行脚本
===========================
自动完成：
  1. 备份原始网络代码
  2. 依次切换 ABL_IGMSA / ABL_ESTIMATOR 开关，跑 A0/A1/A2/A3 四组 5,000 步训练
  3. 每组跑完把 experiments 目录归档到 runs_ablation/<组名>/
  4. 从日志抓取 PSNR 曲线与耗时，生成汇总表 summary.csv / summary.md

用法（Anaconda Prompt，conda 环境 Retinexformer）：
  cd <仓库根目录>
  python experiments/m4_retinexformer_ablation/code/run_ablation.py
  ... --only A1 A2
  ... --skip A3       # 跳过已有 A3（复用当前 experiments 目录）

注意：本脚本会改写 basicsr/models/archs/RetinexFormer_arch.py 中的两行开关。
      原始文件已备份为 RetinexFormer_arch.py.bak，如需彻底还原可手动拷回。
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # 仓库根目录
ARCH = ROOT / "basicsr" / "models" / "archs" / "RetinexFormer_arch.py"
OPT = ROOT / "Options" / "RetinexFormer_LOL_v1.yml"
EXP = ROOT / "experiments" / "RetinexFormer_LOL_v1"
ARCHIVE = ROOT / "runs_ablation"
PY = sys.executable

CONFIGS = [
    # 组名, ABL_IGMSA, ABL_ESTIMATOR, 说明
    ("A0", 0, 0, "Baseline（移除 ORF 与 IG-MSA）"),
    ("A1", 1, 0, "仅 ORF（移除 IG-MSA）"),
    ("A2", 0, 1, "仅 IG-MSA（移除 ORF）"),
    ("A3", 1, 1, "完整 RetinexFormer"),
]


def log(msg):
    try:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
    except UnicodeEncodeError:
        print(f"[{time.strftime('%H:%M:%S')}] "
              f"{msg.encode('ascii', 'replace').decode('ascii')}", flush=True)


def set_switch(igmsa, estimator):
    """改写开关宏。"""
    text = ARCH.read_text(encoding="utf-8")
    new = re.sub(r"(?m)^ABL_IGMSA = \d", f"ABL_IGMSA = {igmsa}", text)
    new = re.sub(r"(?m)^ABL_ESTIMATOR = \d", f"ABL_ESTIMATOR = {estimator}", new)
    if new == text and f"ABL_IGMSA = {igmsa}" not in text:
        raise SystemExit("开关宏未找到，请确认 RetinexFormer_arch.py 已被打过补丁")
    ARCH.write_text(new, encoding="utf-8")


def archive(name, run_dir):
    """把 experiments 目录整体移动到归档位置。"""
    ARCHIVE.mkdir(exist_ok=True)
    dst = ARCHIVE / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.move(str(EXP), str(dst))
    log(f"  已归档 -> {dst}")
    return dst


def parse_run(name, run_dir):
    """从日志与 metric.csv 解析本条记录。"""
    rec = {"group": name, "dir": str(run_dir), "best_psnr": None,
           "best_iter": None, "last3_mean": None, "final_psnr": None,
           "minutes": None, "psnr_points": []}

    # metric.csv
    mcs = list(run_dir.glob("metric.csv"))
    pts = []
    if mcs:
        with open(mcs[0], "r", encoding="utf-8", errors="ignore") as f:
            for row in csv.reader(f):
                if len(row) >= 2:
                    try:
                        pts.append((int(row[0]), float(row[1])))
                    except ValueError:
                        continue
    rec["psnr_points"] = pts
    if pts:
        best = max(pts, key=lambda t: t[1])
        rec["best_iter"], rec["best_psnr"] = best
        rec["final_psnr"] = pts[-1][1]
        tail = pts[-3:]
        rec["last3_mean"] = sum(p for _, p in tail) / len(tail)

    # 日志里的耗时
    logs = list(run_dir.glob("train_*.log")) + list(run_dir.glob("train_*.txt"))
    if logs:
        txt = logs[-1].read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"Time consumed:\s*(\d+):(\d+):(\d+)", txt)
        if m:
            h, mi, s = map(int, m.groups())
            rec["minutes"] = round(h * 60 + mi + s / 60.0, 1)
        m = re.search(r"Updating Patch_Size to (\d+) and Batch_Size to (\d+)", txt)
        if m:
            rec["patch_size"] = int(m.group(1))
            rec["batch_size"] = int(m.group(2))
    return rec


def run_one(name, ig, est, desc, total_iter):
    log(f"===== {name}: {desc} (ABL_IGMSA={ig}, ABL_ESTIMATOR={est}) =====")
    set_switch(ig, est)

    if EXP.exists():
        # 已有残留目录（例如上次被中断），先清掉避免 BasicSR 续训
        if any(EXP.iterdir()):
            archive(f"{name}_leftover_{time.strftime('%H%M%S')}", EXP)
    EXP.mkdir(parents=True, exist_ok=True)

    cmd = [PY, "-m", "basicsr.train", "--opt", str(OPT)]
    log(f"  执行: {' '.join(cmd)}")
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=str(ROOT))
    cost = (time.time() - t0) / 60.0
    log(f"  训练结束，退出码 {proc.returncode}，用时 {cost:.1f} 分钟")

    if not EXP.exists() or not any(EXP.iterdir()):
        log(f"  [错误] {name} 没有产生任何输出，跳过")
        return None

    if proc.returncode != 0:
        log(f"  [警告] {name} 非零退出，仍归档现场")

    return archive(name, EXP)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--skip", nargs="*", default=[])
    ap.add_argument("--total-iter", type=int, default=None,
                    help="临时改写 total_iter（默认沿用 yml 里的值）")
    args = ap.parse_args()

    if not ARCH.exists():
        raise SystemExit(f"找不到 {ARCH}")

    # 若没有备份，先备份
    bak = ARCH.with_suffix(".py.bak")
    if not bak.exists():
        shutil.copy2(ARCH, bak)
        log(f"已备份原始代码 -> {bak}")

    # 可选：临时改 total_iter
    if args.total_iter:
        txt = OPT.read_text(encoding="utf-8")
        txt = re.sub(r"(?m)^(\s*total_iter:)\s*\d+", rf"\g<1> {args.total_iter}", txt)
        OPT.write_text(txt, encoding="utf-8")
        log(f"已把 total_iter 设为 {args.total_iter}")

    todo = [c for c in CONFIGS if (args.only is None or c[0] in args.only)
            and c[0] not in args.skip]

    # 如果当前 experiments 里有旧的未归档结果（用户已有的 5k 完整训练），
    # 且要跑 A3，则复用为 A3；否则先归档防止被覆盖。
    if EXP.exists() and any(EXP.iterdir()):
        pending = EXP
        if any(c[0] == "A3" for c in todo):
            ARCHIVE.mkdir(exist_ok=True)
            dst = ARCHIVE / "A3"
            if dst.exists():
                shutil.rmtree(dst)
            # 复制而非移动，保留原实验目录
            log("检测到已有实验结果，复制为 A3（完整模型）")
            shutil.copytree(str(pending), str(dst))
            todo = [c for c in todo if c[0] != "A3"]
        # 其余情况把旧目录挪开
        ARCHIVE.mkdir(exist_ok=True)
        old = ARCHIVE / f"pre_{time.strftime('%Y%m%d_%H%M%S')}"
        shutil.move(str(pending), str(old))
        log(f"旧的未归档结果已移到 {old}")

    records = []
    for name, ig, est, desc in todo:
        r = run_one(name, ig, est, desc, args.total_iter)
        if r:
            rec = parse_run(name, r)
            rec["desc"] = desc
            rec["ABL_IGMSA"] = ig
            rec["ABL_ESTIMATOR"] = est
            records.append(rec)
            log(f"  {name} 结果: best={rec['best_psnr']} @ {rec['best_iter']}, "
                f"last3={rec['last3_mean']}, 耗时={rec['minutes']} 分钟")

    # 补上已归档组的记录
    for name, ig, est, desc in CONFIGS:
        if any(r["group"] == name for r in records):
            continue
        d = ARCHIVE / name
        if d.exists():
            rec = parse_run(name, d)
            rec["desc"] = desc
            rec["ABL_IGMSA"] = ig
            rec["ABL_ESTIMATOR"] = est
            records.append(rec)

    # 恢复完整配置
    set_switch(1, 1)
    log("已把开关恢复为完整模型 (1,1)")

    records.sort(key=lambda r: r["group"])
    write_summary(records)
    return 0


def write_summary(records):
    ARCHIVE.mkdir(exist_ok=True)
    csv_path = ARCHIVE / "summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["实验", "ORF", "IG-MSA", "含义", "最佳PSNR", "最佳迭代",
                    "后3次平均PSNR", "末次PSNR", "耗时(分钟)",
                    "训练patch", "训练batch"])
        for r in records:
            w.writerow([
                r["group"],
                "✓" if r["ABL_ESTIMATOR"] else "✗",
                "✓" if r["ABL_IGMSA"] else "✗",
                r["desc"],
                f'{r["best_psnr"]:.4f}' if r["best_psnr"] else "NOT RUN",
                r["best_iter"] if r["best_iter"] else "NOT RUN",
                f'{r["last3_mean"]:.4f}' if r["last3_mean"] else "NOT RUN",
                f'{r["final_psnr"]:.4f}' if r["final_psnr"] else "NOT RUN",
                r["minutes"] if r["minutes"] else "NOT RUN",
                r.get("patch_size", "-"),
                r.get("batch_size", "-"),
            ])
    (ARCHIVE / "summary.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# M4 短程消融实验结果", "",
             "| 实验 | ORF | IG-MSA | 含义 | 最佳PSNR | 最佳迭代 | 后3次平均PSNR | 耗时 |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in records:
        lines.append(
            f'| {r["group"]} | {"✓" if r["ABL_ESTIMATOR"] else "✗"} | '
            f'{"✓" if r["ABL_IGMSA"] else "✗"} | {r["desc"]} | '
            f'{r["best_psnr"]:.4f} | {r["best_iter"]} | {r["last3_mean"]:.4f} | '
            f'{r["minutes"]} 分钟 |' if r["best_psnr"] else
            f'| {r["group"]} | - | - | {r["desc"]} | NOT RUN | - | - | - |')
    (ARCHIVE / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "=" * 70)
    try:
        print("\n".join(lines))
    except UnicodeEncodeError:
        print("\n".join(lines).encode("ascii", "replace").decode("ascii"))
    print("=" * 70)
    log(f"汇总已写入 {csv_path}")


if __name__ == "__main__":
    sys.exit(main())
