# -*- coding: utf-8 -*-
"""由 precondition_tiers.json 生成 Table VII-c 的 Markdown 行。

用法：python experiment_kit/prompt_rerun/table_vii_c.py

与 table_vii_d.py 一样，目的���让论文中的表与判据实现保持同源。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiment_kit" / "prompt_rerun" / "precondition_tiers.json"

# 论文表中的行（按顺序）；成对的用 (key1, key2) 表示
GROUPS = [
    ("M1 人工基准", "M1 manual (human reference)"),
    ("M2 MiniMax 无禁令", "M2 MiniMax, no ban"),
    (("B3 MiniMax无禁令(当前)", "B4 MiniMax无禁令(当前)"), "B3 / B4 MiniMax, no ban (current)"),
    (("A1 MiniMax+单点禁令", "A2 MiniMax+单点禁令"), "A MiniMax, single ban (r1 / r2)"),
    ("D1 MiniMax+泛禁令", "D1 MiniMax, family ban"),
    (("B1 Hunyuan 无禁令", "B2 Hunyuan 无禁令"), "B Hunyuan, no ban (r1 / r2)"),
    ("C1 Hunyuan+单点禁令", "C Hunyuan, single ban"),
    ("D2 Hunyuan+泛禁令", "D2 Hunyuan, family ban"),
]


def fmt_pair(v1, v2, pct=False):
    if pct:
        return f"{v1*100:.1f}% / {v2*100:.1f}%"
    return f"{v1} / {v2}"


def main():
    rows = json.loads(RES.read_text(encoding="utf-8"))
    by = {r["label"]: r for r in rows}

    print("| Condition | pre | T1 | flag (self) | axiom | substantive | content rate |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for key, name in GROUPS:
        if isinstance(key, tuple):
            r1, r2 = by[key[0]], by[key[1]]
            pre = fmt_pair(r1["pre"], r2["pre"])
            t1 = fmt_pair(r1["tiers"]["T1"], r2["tiers"]["T1"])
            t2 = fmt_pair(r1["tiers"]["T2b"], r2["tiers"]["T2b"])
            t3 = fmt_pair(r1["tiers"]["T3"], r2["tiers"]["T3"])
            t4 = fmt_pair(r1["tiers"]["T4"], r2["tiers"]["T4"])
            cr = fmt_pair(r1["content_rate"], r2["content_rate"], pct=True)
        else:
            r = by[key]
            pre = r["pre"]
            t1 = r["tiers"]["T1"]
            t2 = r["tiers"]["T2b"]
            t3 = r["tiers"]["T3"]
            t4 = r["tiers"]["T4"]
            cr = f"{r['content_rate']*100:.0f}%"
        print(f"| {name} | {pre} | {t1} | {t2} | {t3} | {t4} | {cr} |")


if __name__ == "__main__":
    main()
