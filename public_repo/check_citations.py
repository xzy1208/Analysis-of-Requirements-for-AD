#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_citations.py —— 论文引用完整性检查。

用途
----
每次改稿后必跑（改稿铁律）。检查两件事：
  1. 正文里引用的 [n]，参考文献表里必须都有；
  2. 参考文献表里的每一条，正文里必须都被引用过（不能有"挂着的"文献）。

用法
----
    python check_citations.py                      # 检查英文版
    python check_citations.py --zh                 # 检查中文版
    python check_citations.py --both               # 两版都查
"""
import io
import os
import re
import sys

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"
EN = os.path.join(BASE, "paper_draft_v2.md")
ZH = os.path.join(BASE, "paper_draft_v2_中文审核版.md")

# 参考文献表的行首形态
REF_LINE = re.compile(r"^\s*\[(\d{1,3})\]\s")
# 正文中的引用 [1] [1,2] [1-3]
CITE = re.compile(r"\[(\d{1,3}(?:\s*[,，]\s*\d{1,3})*)\]")


def split_doc(txt):
    """切成 (正文, 参考文献表) 两段。"""
    lines = txt.splitlines()
    ref_start = None
    for i, l in enumerate(lines):
        if re.match(r"^\s*(References|参考文献)\s*$", l, re.I):
            ref_start = i
            break
    if ref_start is None:
        # 兜底：找第一条形如 "[1] ..." 的独立行
        for i, l in enumerate(lines):
            if REF_LINE.match(l) and len(lines) - i > 20:
                ref_start = i
                break
    if ref_start is None:
        return txt, ""
    return "\n".join(lines[:ref_start]), "\n".join(lines[ref_start:])


def expand(spec):
    out = []
    for part in re.split(r"[,，]", spec):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            out.extend(range(min(a, b), max(a, b) + 1))
        else:
            out.append(int(part))
    return out


def check(path, label):
    txt = io.open(path, encoding="utf-8").read()
    body, refs = split_doc(txt)
    if not refs:
        print("!! %s: 找不到参考文献表段落" % label)
        return False

    listed = set()
    for l in refs.splitlines():
        m = REF_LINE.match(l)
        if m:
            listed.add(int(m.group(1)))

    cited = set()
    for m in CITE.finditer(body):
        for n in expand(m.group(1)):
            cited.add(n)

    missing = sorted(cited - listed)      # 引了但表里没有
    uncited = sorted(listed - cited)      # 表里有但正文没引

    print("=" * 62)
    print("%s：参考文献 %d 条，正文引用 %d 条" % (label, len(listed), len(cited)))
    if missing:
        print("  !! 正文引用了但表中没有：%s" % missing)
    if uncited:
        print("  !! 表中列出但正文未引用：%s" % uncited)
    if not missing and not uncited:
        print("  ✅ 引用完整性全绿")
    return not missing and not uncited


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--both" in args:
        ok = check(EN, "英文版")
        print()
        ok2 = check(ZH, "中文版")
        sys.exit(0 if (ok and ok2) else 1)
    if "--zh" in args:
        sys.exit(0 if check(ZH, "中文版") else 1)
    sys.exit(0 if check(EN, "英文版") else 1)
