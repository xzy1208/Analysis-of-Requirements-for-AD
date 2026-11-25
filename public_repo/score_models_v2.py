#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
score_models_v2.py —— 五核心指标评分（按评估方案 v2 / GQM 框架）

指标（0..1，越高越好）：
  M1 需求覆盖率    = Σ(每条原子需求得分) / 总数；完全=1.0 部分=0.5 未覆盖=0
                     另报 safety_coverage（criticality=high 的子集）
                     v2.1 起优先读 coverage_manual.json 的人工逐条标注（与论文一致），
                     文件缺失时回退到自动关键词匹配
  M2 精确率        = 有需求依据的元素数 / 元素总数（原 D6 反向）
  M3 一致性        = 0.5·流端点可解析率 + 0.3·有输入声明比例 + 0.2·(1−孤儿率)
                     （复用 score_models.py 的 d2 逻辑）
  M4 形式化精确度  = 0.4·有有效pre比例 + 0.3·有量化约束比例 + 0.3·(1−歧义词占比)
                     v2.1：空洞守卫（x <> null / x <> ''）不计入"有 pre"；
                     逐条计数 n_vacuous 一并输出（供论文 Table VII / I4 修正）
  M5 缺陷检出率    = 由 defect_injection_results.json 提供；未生成时为 None

总分 = 均值(M1..M4)，M5 单独报告（避免用占位值污染总分）。
所有阈值/歧义词表来自评估方案 v2 §2。
"""
import io, os, re, json, sys
from collections import Counter

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"
MODELS = {
    "M1": ("M1_manual_human", ["L0", "L1"]),
    "M1.1": ("M1_1_manual_plus_thresholds", ["L0", "L1"]),
    "M2": ("M2_AI_SOFL_single", ["L0", "L1"]),  # 同表示法对照（LLM 复刻 SOFL，MiniMax-M3.1-Flash）
    "M3": ("M3_AI_DFD", ["L0", "L1"]),
    "M4": ("M4_AI_UML", ["L0", "L1"]),
    "M5": ("M5_AI_StateMachine", ["L1"]),
}
AMBIGUOUS = ["及时", "安全", "合适", "适当", "合理", "尽快", "有效", "良好",
             "timely", "adequate", "appropriate", "reasonable", "sufficient",
             "efficient", "safe", "proper"]
ALLOWED_NUM = {1.5, 2.0, 3.0, 6.0, 3.5, 130.0, 0.1, 4.0, 0.5, 1.0, 0.0}


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def norm(s):
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", (s or "").lower())


def atoms():
    """只用人工拆的 44 条作为共同基准（LLM 版独有的 9 条不参与覆盖率，
    避免把'AI 拆出来的需求'强加给所有模型造成偏差）。"""
    p = os.path.join(BASE, "atomic_requirements_human.json")
    return load(p)


def atoms_for_level(atom_list, level):
    """层级过滤：L0 模型只对照整车级需求，L1 模型只对照 AEB+阈值需求。
    这消除了'用 L1 需求判 L0 模型'造成的结构性低分。"""
    if level == "L0":
        return [a for a in atom_list if a.get("category") in ("scope", "external", "store", "function")]
    return [a for a in atom_list if a.get("category") in ("aeb", "threshold", "scope")]


def model_docs(mid):
    folder, levels = MODELS[mid]
    docs = []
    for lv in levels:
        p = os.path.join(BASE, "models", folder, "MES_%s_%s.json" % (mid, lv))
        if os.path.exists(p):
            d = load(p)
            d["_level"] = lv
            docs.append(d)
    return docs


def all_text(doc):
    parts = []
    for e in doc.get("elements", []):
        parts.append(json.dumps(e, ensure_ascii=False))
    for t in doc.get("traceability", []):
        parts.append(json.dumps(t, ensure_ascii=False))
    return " ".join(parts)


def clause_set(doc):
    s = set()
    for t in doc.get("traceability", []):
        s.add(norm(t.get("requirement", "")))
    return s


def m1_coverage(doc, atom_list):
    """覆盖率打标：完全=1.0 / 部分=0.5 / 未覆盖=0。
    三条证据源（任一命中即完全覆盖）：
      a) source_clause 出现在 traceability（要求 ID 体系一致时有效）
      b) 原子 text 的关键词集合与模型元素/契约文本有足够重合
      c) 按类别走专门匹配：ext/store 用元素名，func/aeb/threshold 用契约文本
    注意：M1 的 traceability 用 F-<process名>，其它模型用 F1/F2...，ID 体系不统一，
    因此 (a) 不能作为唯一依据，必须以语义匹配为主。"""
    txt = all_text(doc)
    txt_n = norm(txt)
    clauses = clause_set(doc)
    elem_names_raw = [str(e.get("name", "")) for e in doc.get("elements", [])]
    elem_names = [norm(n) for n in elem_names_raw]
    store_names = {norm(str(s.get("name", ""))) for s in doc.get("stores", [])}
    ext_names = {norm(str(x.get("name", ""))) for x in doc.get("externals", [])}
    txt_words = set(re.findall(r"[a-z0-9]+", txt_n))

    score_sum = 0.0
    safety_sum = 0.0
    safety_n = 0
    detail = []
    for a in atom_list:
        src = norm(a.get("source_clause", ""))
        text_n = norm(a.get("text", ""))
        cat = a.get("category", "")

        # 提取原子文本里的英文/数字词（E1/map_data/TTC/130 等）与中文 2-gram
        en_words = set(re.findall(r"[a-z0-9]+", text_n))
        cn = re.findall(r"[\u4e00-\u9fff]+", text_n)
        cn_bigrams = set()
        for seg in cn:
            for i in range(len(seg) - 1):
                cn_bigrams.add(seg[i:i + 2])

        full = False
        # (a) traceability ID 完全一致
        if src and src in clauses:
            full = True
        # (b) 按类别专门匹配
        if not full and cat == "external":
            # source_clause 形如 E1 / E5，取 E<num>，找模型里同名或语义名
            m = re.search(r"e(\d)", src)
            if m and m.group(1) in txt_n:
                full = True
            if any(w in txt_n and len(w) >= 4 for w in en_words):
                full = True
        if not full and cat == "store":
            m = re.search(r"d(\d)", src)
            if m and m.group(1) in txt_n:
                full = True
            if any(w in txt_n and len(w) >= 5 for w in en_words):
                full = True
        if not full and cat in ("function", "aeb", "threshold", "scope"):
            # 英文关键词命中（≥2 个，且长度≥3）
            hit = [w for w in en_words if len(w) >= 3 and w in txt_words]
            if len(hit) >= 2:
                full = True
            # 中文 bigram 命中率（≥40%）
            if not full and cn_bigrams:
                cn_txt = re.findall(r"[\u4e00-\u9fff]+", txt)
                txt_bg = set()
                for seg in cn_txt:
                    for i in range(len(seg) - 1):
                        txt_bg.add(seg[i:i + 2])
                if len(cn_bigrams & txt_bg) / len(cn_bigrams) >= 0.4:
                    full = True

        # 部分覆盖：source_clause 前缀（F1/N-2/A-5）在文本中出现
        partial = False
        if not full:
            m = re.match(r"([a-z]+\d*)", src)
            if m and (m.group(1) in txt_n or any(m.group(1) in n for n in elem_names)):
                partial = True
            elif en_words and any(w in txt_n for w in en_words if len(w) >= 4):
                partial = True

        sc = 1.0 if full else (0.5 if partial else 0.0)
        score_sum += sc
        detail.append({"id": a["id"], "score": sc})
        if a.get("criticality") == "high":
            safety_sum += sc
            safety_n += 1
    n = max(len(atom_list), 1)
    return score_sum / n, (safety_sum / safety_n if safety_n else 0.0), detail


def coverage_manual_labels():
    """人工逐条标注的覆盖率（coverage_manual.json）。缺失时返回空 dict。"""
    p = os.path.join(BASE, "coverage_manual.json")
    if os.path.exists(p):
        return load(p)
    return {}


def m2_precision(doc):
    els = doc.get("elements", [])
    if not els:
        return 0.0, {"elements": 0}
    grounded = 0
    for e in els:
        nm = norm(e.get("name", ""))
        if re.search(r"\bX\d+\b", e.get("name", "")) and not e.get("notes", "").startswith("extracted"):
            continue
        if re.search(r"(fault|degrad|deactiv|override|empty)", nm):
            # 合成状态：若 open_issues 声明则算有依据
            declared = any("OI" in str(o.get("id", "")) for o in doc.get("open_issues", []))
            if not declared:
                continue
        grounded += 1
    return grounded / len(els), {"elements": len(els), "grounded": grounded}


def m3_consistency(doc):
    els = doc.get("elements", [])
    ids = set()
    for e in els:
        ids.add(str(e.get("id", "")))
        ids.add(str(e.get("name", "")))
    for s in doc.get("stores", []):
        ids.add(str(s.get("name", "")))
    for x in doc.get("externals", []):
        ids.add(str(x.get("name", "")))
    canon = {norm(i) for i in ids if i}
    flows = doc.get("flows", [])
    if not flows:
        return 0.0, {"flows": 0}
    resolved = 0
    for fl in flows:
        p, c = norm(fl.get("producer", "")), norm(fl.get("consumer", ""))
        ok = (p in canon or p in ("", "outside", "external", "system")) and \
             (c in canon or c in ("", "outside", "external", "system"))
        if not ok:
            ok = any(x in p or p in x for x in canon if len(x) >= 4) and \
                 any(x in c or c in x for x in canon if len(x) >= 4)
        resolved += 1 if ok else 0
    r = resolved / len(flows)
    has_in = sum(1 for e in els if e.get("inputs") or e.get("preconditions")) / max(len(els), 1)
    produced = {fl.get("producer") for fl in flows}
    consumed = {fl.get("consumer") for fl in flows}
    orphan = len(produced - consumed) / max(len(produced), 1)
    return .5 * r + .3 * has_in + .2 * (1 - min(orphan, 1.0)), \
           {"flows": len(flows), "resolved": resolved, "orphan": round(orphan, 2)}


def constraint_texts(o, acc=None):
    if acc is None:
        acc = []
    keys = {"preconditions", "postconditions", "invariants", "guard", "effect"}
    if isinstance(o, dict):
        for k, v in o.items():
            if k in keys:
                acc.append(json.dumps(v, ensure_ascii=False))
            else:
                constraint_texts(v, acc)
    elif isinstance(o, list):
        for v in o:
            constraint_texts(v, acc)
    return acc


VACUOUS_RE = re.compile(r"^\s*[\w.\[\]]+\s*<>\s*(null|None|''|\"\")\s*$", re.I)


def split_clauses(cond_list):
    """把 precondition 列表拆成原子子句（按 and 切）。"""
    out = []
    for s in cond_list:
        for part in re.split(r"\s+and\s+", str(s)):
            p = part.strip()
            if p:
                out.append(p)
    return out


def m4_formal(doc):
    els = doc.get("elements", [])
    if not els:
        return 0.0, {}
    pre = sum(1 for e in els if e.get("preconditions")) / len(els)
    # 有效 pre：至少含一条非空洞子句（排除 x <> null / x <> '' 型同义反复）
    n_vac = 0
    pre_eff = 0
    for e in els:
        cl = split_clauses(e.get("preconditions") or [])
        vac = [c for c in cl if VACUOUS_RE.match(c)]
        n_vac += len(vac)
        if len(cl) > len(vac):
            pre_eff += 1
    pre_eff_ratio = pre_eff / len(els)
    quant = sum(1 for e in els if e.get("quantified")) / len(els)
    txt = " ".join(constraint_texts(doc))
    low = txt.lower()
    amb = sum(low.count(w) for w in AMBIGUOUS)
    amb_ratio = min(amb / max(len(els), 1), 1.0)
    return .4 * pre_eff_ratio + .3 * quant + .3 * (1 - amb_ratio), \
           {"pre": round(pre, 2), "pre_eff": round(pre_eff_ratio, 2),
            "n_vacuous": n_vac, "quant": round(quant, 2), "ambiguous": amb,
            "amb_ratio": round(amb_ratio, 2)}


def main():
    atom_list = atoms()
    manual = coverage_manual_labels()
    print("原子需求清单: %d 条" % len(atom_list))
    print("=" * 100)
    print("%-5s %-4s | %-7s %-7s %-7s %-7s %-7s | %-7s" %
          ("model", "lv", "I1cov*", "safety", "I2prec", "I3cons", "I4form", "AVG4"))
    print("(I1cov* = 人工标注 coverage_manual.json；括号内为自动匹配值)")
    print("-" * 100)
    out = []
    for mid in ["M1", "M1.1", "M2", "M3", "M4", "M5"]:
        docs = model_docs(mid)
        for doc in docs:
            level_atoms = atoms_for_level(atom_list, doc["_level"])
            cov_auto, safety_auto, detail = m1_coverage(doc, level_atoms)
            # 人工标注优先
            mcov = manual.get(mid, {}).get(doc["_level"], {})
            if mcov:
                cov, safety = mcov["coverage"], mcov.get("safety_coverage", safety_auto)
            else:
                cov, safety = cov_auto, safety_auto
            prec, dp = m2_precision(doc)
            cons, dc = m3_consistency(doc)
            form, df = m4_formal(doc)
            avg = (cov + prec + cons + form) / 4
            print("%-5s %-4s | %.3f(%.3f) %.3f  %.3f  %.3f  %.3f  | %.3f  vac=%d" %
                  (mid, doc["_level"], cov, cov_auto, safety, prec, cons, form, avg,
                   df.get("n_vacuous", 0)))
            out.append({"model": mid, "level": doc["_level"],
                        "M1_coverage": round(cov, 3), "M1_safety_coverage": round(safety, 3),
                        "coverage_source": "manual" if mcov else "auto",
                        "M2_precision": round(prec, 3), "M3_consistency": round(cons, 3),
                        "M4_formal_precision": round(form, 3), "avg_without_M5": round(avg, 3),
                        "details": {"M1": {"coverage_source": "manual" if mcov else "auto",
                                          "auto_coverage": round(cov_auto, 3)},
                                    "M2": dp, "M3": dc, "M4": df}})
        # 跨层合并（L0+L1 取最大集，避免重复计分）
        if len(docs) > 1:
            pass
    print("-" * 92)
    # M5 缺陷检出率占位
    dip = os.path.join(BASE, "defect_injection_results.json")
    m5 = None
    if os.path.exists(dip):
        dr = load(dip)
        m5 = dr.get("overall_detection_rate")
        print("M5 缺陷检出率: %s" % m5)
    else:
        print("M5 缺陷检出率: 待步骤4生成")
    io.open(os.path.join(BASE, "scores_v2.json"), "w", encoding="utf-8").write(
        json.dumps({"atoms": len(atom_list), "rows": out,
                    "defect_detection_rate": m5}, indent=2, ensure_ascii=False))
    print("\n已写出 scores_v2.json")


if __name__ == "__main__":
    main()
