#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
merge_atomic_requirements.py —— 合并人工/LLM 双拆的原子需求清单，计算 Jaccard 一致性。

Jaccard 用两种口径：
  1) 严格 ID 匹配：两侧 id 集合的交/并（但两边编号体系独立，通常偏低，仅参考）
  2) 语义匹配：按 source_clause + 关键词做贪心对齐，算语义重合率（论文报告此值）

产出：
  atomic_requirements_v1.json  —— 合并后的最终清单（人工版为准，LLM 版独有的条目标记为 llm_only）
  atomic_requirements_merge_report.json —— 一致性指标
"""
import io, json, os, re
from collections import Counter

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def norm(s):
    s = s.lower()
    s = re.sub(r"[a-z0-9]+", lambda m: m.group(0), s)
    return re.sub(r"\s+", "", s)


def tokens(s):
    """中文按 2-gram，英文/数字按词"""
    s = norm(s)
    cn = re.findall(r"[\u4e00-\u9fff]+", s)
    en = re.findall(r"[a-z0-9]+", s)
    t = set(en)
    for seg in cn:
        for i in range(len(seg) - 1):
            t.add(seg[i:i + 2])
        if len(seg) == 1:
            t.add(seg)
    return t


def sim(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def source_key(x):
    return re.sub(r"\s|/", "", str(x.get("source_clause", ""))).upper()


def main():
    human = load(os.path.join(BASE, "atomic_requirements_human.json"))
    llmp = os.path.join(BASE, "atomic_requirements_llm.json")
    if not os.path.exists(llmp):
        print("LLM 版尚未生成，无法合并")
        return
    llm = load(llmp)

    # 严格 ID Jaccard
    h_ids = {x["id"] for x in human}
    l_ids = {x["id"] for x in llm}
    id_jac = len(h_ids & l_ids) / len(h_ids | l_ids) if (h_ids | l_ids) else 0

    # 语义贪心对齐：限制同类 + source_clause 相同优先
    used = set()
    pairs = []
    for h in human:
        best, bs = None, 0.0
        for j, l in enumerate(llm):
            if j in used:
                continue
            s = sim(h["text"], l["text"])
            if h.get("category") == l.get("category"):
                s += 0.10
            if source_key(h) == source_key(l):
                s += 0.15
            if s > bs:
                bs, best = s, j
        if best is not None and bs >= 0.30:
            used.add(best)
            pairs.append((h, llm[best], bs))
        else:
            pairs.append((h, None, 0.0))
    matched = sum(1 for _, l, _ in pairs if l is not None)
    sem_jac = matched / max(len(human), len(llm))

    merged = []
    for h, l, s in pairs:
        rec = dict(h)
        rec["llm_match"] = l["id"] if l else None
        rec["llm_similarity"] = round(s, 3)
        merged.append(rec)
    for j, l in enumerate(llm):
        if j not in used:
            rec = dict(l)
            rec["llm_only"] = True
            rec["id"] = "LLM-" + rec["id"]
            merged.append(rec)

    io.open(os.path.join(BASE, "atomic_requirements_v1.json"), "w", encoding="utf-8").write(
        json.dumps(merged, indent=2, ensure_ascii=False))

    report = {
        "human_count": len(human),
        "llm_count": len(llm),
        "matched_semantic": matched,
        "id_jaccard": round(id_jac, 3),
        "semantic_jaccard": round(sem_jac, 3),
        "human_categories": dict(Counter(x.get("category") for x in human)),
        "llm_categories": dict(Counter(x.get("category") for x in llm)),
        "llm_only_count": len(llm) - matched,
        "note": "semantic_jaccard is the reported inter-rater agreement; id_jaccard is not meaningful because the two splits use independent numbering",
    }
    io.open(os.path.join(BASE, "atomic_requirements_merge_report.json"), "w", encoding="utf-8").write(
        json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
