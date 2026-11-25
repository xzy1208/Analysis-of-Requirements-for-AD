# -*- coding: utf-8 -*-
"""由 contract_content_results.json 生成 Table VII-d 的 Markdown 行。

用法：python experiment_kit/prompt_rerun/table_vii_d.py

这样表格与判据实现保持同源：改判据只需重跑 contract_content_analysis.py
再执行本脚本，论文中的表不会与数据脱节。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiment_kit" / "prompt_rerun" / "contract_content_results.json"

# 输出顺序与论文 Table VII-d 一致
ORDER = [
    ("M1 manual", "M1 manual (human reference)"),
    ("M2 MiniMax no ban", "M2 MiniMax, no ban"),
    ("B3 MiniMax no ban (current)", "B3 MiniMax, no ban (current)"),
    ("B4 MiniMax no ban (current)", None),          # 与 B3 合并成一行
    ("A2 MiniMax single ban", "A2 MiniMax, single ban"),
    ("D1 MiniMax family ban", "D1 MiniMax, family ban"),
    ("B1 Hunyuan no ban", "B1 Hunyuan, no ban"),
    ("B2 Hunyuan no ban", "B2 Hunyuan, no ban"),
    ("C1 Hunyuan single ban", "C1 Hunyuan, single ban"),
    ("D2 Hunyuan family ban", "D2 Hunyuan, family ban"),
]


def pct(x):
    return f"{x*100:.1f}%"


def main():
    data = json.loads(RES.read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("rows", [])
    by = {r["label"]: r for r in rows}

    out = []
    for key, name in ORDER:
        if name is None:
            continue
        r = by.get(key)
        if not r:
            print(f"  缺少 {key}，跳过")
            continue
        if key.startswith("B3 MiniMax"):
            r2 = by.get("B4 MiniMax no ban (current)")
            pre = f"{pct(r['pre_rate'])} / {pct(r2['pre_rate'])}"
            ps = f"{pct(r['post_strict_rate'])} / {pct(r2['post_strict_rate'])}"
            pa = f"{pct(r['post_all_rate'])} / {pct(r2['post_all_rate'])}"
            pn = f"{r['pre_n']} / {r2['pre_n']}"
            postn = f"{r['post_strict_n']} / {r2['post_strict_n']}"
            out.append(f"| {name} | {pre} | {ps} | {pa} | {pn} | {postn} |")
        else:
            out.append(f"| {name} | {pct(r['pre_rate'])} | {pct(r['post_strict_rate'])} | "
                       f"{pct(r['post_all_rate'])} | {r['pre_n']} | {r['post_strict_n']} |")

    print("| Condition | pre substantive | post substantive (strict) | post substantive (all) | pre n | post n |")
    print("|---|---:|---:|---:|---:|---:|")
    for line in out:
        print(line)


if __name__ == "__main__":
    main()
