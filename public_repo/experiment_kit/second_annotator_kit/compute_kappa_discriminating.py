#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
compute_kappa_discriminating.py —— 第二标注者与主标注的 Cohen's κ（判别力导向版）。

与原 `compute_kappa.py` 的差别：
  1. 分开报告**判别力集**与**对照集**的 κ。对照集是随机抽取的恒为 1 条目，
     其一致率检验的是"是否存在系统性偏差"（例如对某类模型一律给 1），
     与主 κ 是两件事，混在一起会稀释判别力集的信号。
  2. 支持 `--selftest`：用主标注自身作为第二标注，验证流程连通。
  3. 报告每个原子上的分歧，便于定向校对。

用法：
    python compute_kappa_discriminating.py labelling_template_filled.json
    python compute_kappa_discriminating.py labelling_template_filled.json --selftest
"""
import io
import json
import os
import sys
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
CATS = [0.0, 0.5, 1.0]


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def kappa(pairs):
    """pairs: [(second, primary)] → (agree, kappa_unweighted, kappa_linear)"""
    n = len(pairs)
    if n == 0:
        return 0.0, 0.0, 0.0
    agree = sum(1 for s, p in pairs if s == p) / n
    m1 = {c: sum(1 for s, p in pairs if s == c) / n for c in CATS}
    m2 = {c: sum(1 for s, p in pairs if p == c) / n for c in CATS}
    pe = sum(m1[c] * m2[c] for c in CATS)
    k = (agree - pe) / (1 - pe) if pe < 1 else 1.0
    w = {(a, b): 1 - abs(a - b) for a in CATS for b in CATS}
    po_w = sum(w[(s, p)] for s, p in pairs) / n
    pe_w = sum(m1[a] * m2[b] * w[(a, b)] for a in CATS for b in CATS)
    kw = (po_w - pe_w) / (1 - pe_w) if pe_w < 1 else 1.0
    return agree, k, kw


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    path = sys.argv[1]
    selftest = "--selftest" in sys.argv
    rows = load(os.path.join(BASE, path))
    if isinstance(rows, dict):
        rows = rows["rows"]
    manual = load(os.path.join(ROOT, "coverage_manual.json"))

    sets = defaultdict(list)
    missing = []
    for r in rows:
        key = (r["atom_id"], r["model"], r["level"])
        blk = manual.get(r["model"], {}).get(r["level"], {}).get("rows", [])
        hit = [x for x in blk if x["id"] == r["atom_id"]]
        if not hit:
            missing.append(key)
            continue
        prim = float(hit[0]["score"])
        sec = prim if selftest else r.get("label", "")
        if sec in ("", None):
            missing.append(key)
            continue
        sets[r.get("set", "all")].append((r["atom_id"], r["model"], r["level"],
                                          float(sec), prim))

    if missing:
        print("警告：%d 行未填或主标注中找不到对应原子：" % len(missing))
        for k in missing[:10]:
            print("   ", k)

    for name in ("discriminating", "control"):
        pairs = [(s, p) for _a, _m, _l, s, p in sets.get(name, [])]
        if not pairs:
            continue
        agree, k, kw = kappa(pairs)
        label = "判别力集（有模型间差异的条目）" if name == "discriminating" \
            else "对照集（随机抽取的恒为 1 条目）"
        print("\n=== %s ===" % label)
        print("n = %d  原始一致率 = %.3f" % (len(pairs), agree))
        print("未加权 Cohen's kappa = %.3f" % k)
        print("线性加权 kappa     = %.3f" % kw)

        by_atom = defaultdict(list)
        for a, m, lv, s, p in sets[name]:
            by_atom[a].append((m, s, p))
        # 分歧 = 该原子上第二标注者与主标注不一致
        dis = [(a, v) for a, v in by_atom.items()
               if any(s != p for _m, s, p in v)]
        if dis:
            print("分歧原子（%d 条）：" % len(dis))
            for a, v in sorted(dis):
                for m, s, p in v:
                    if s != p:
                        print("   %-8s %-6s 第二标注=%.1f  主标注=%.1f" % (a, m, s, p))
        else:
            print("该集内无分歧。")

    allp = [(s, p) for v in sets.values() for _a, _m, _l, s, p in v]
    if allp:
        agree, k, kw = kappa(allp)
        print("\n=== 合并（判别力集 + 对照集）===")
        print("n = %d  一致率 = %.3f  未加权 κ = %.3f  线性加权 κ = %.3f"
              % (len(allp), agree, k, kw))
        print("（论文正文应报告判别力集的 κ；对照集一致率单独说明其偏差含义）")


if __name__ == "__main__":
    main()
