#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
formal_criterion_checker.py —— 统一形式化判据检查器（论文 Table IV / VII-b / VII-c / VII-d 共用一份实现）

问题背景
--------
论文正文两处使用"空洞/恒真"口径：
  (1) Table IV 的 I4（形式化精确度）由 score_models_v2.py 计算，其"有效前置条件"
      判据只排除两种写法：`x <> null` 与 `x <> ''`（VACUOUS_RE，两型）。
  (2) Table VII-b / VII-c 的空洞统计由 analyze_rerun.py / precondition_tiers.py 计算，
      覆盖五类恒真式族：`x <> null`、`x = x`、`nat >= 0`、`x <> ''`、`if true then`（五型）。
两处口径不同 -> 同一个"空洞率"在两张表里含义不一致。本脚本把两者合并为**一份实现**：
分类函数直接复用 `precondition_tiers.tier()`（即 Table VII-c 的实现），并对
M1–M5 的 MES 契约字段与 12 份源文本产物跑同一套判据。

三个 I4 口径
------------
  legacy2   = I4 现行实现：仅排除 null_guard 与 empty_guard（复核用，论文中已标注为旧口径）
  unified5  = I4 统一口径：排除五类恒真式族  → **本文采用**
  strictT4  = 严格判据：前置条件中至少含一条"实质"子句（T4），作为下界披露

分层判据（与 Table VII-c 完全一致）
------------------------------------
  T1 tautology  五类恒真式之一（由类型即可判定）
  T2a spec-flag 规格 E1/E2 声明的每传感器有效性旗标（camera_valid 等）
  T2b self-flag 生成器自行在 composed type 中声明的 `valid` 旗标
  T3 axiom     域公理：按约定成立的界（speed ≥ 0、经纬度范围、path_length > 0）
  T4 content   实质：与阈值比较或字段间关系

类型信息来源（可追溯）
----------------------
  M1  models/M1_manual_human/{System,BehaviorPlanning}.fModule 的 typeDeclaration
  M2  models/M2_AI_SOFL_single/{ADAS_System,AEB_Branch}.fModule 的 typeDeclaration
  M4  models/M4_AI_UML/M4_L*.puml 的属性类型声明（`+ attr : nat`）
  M3  models/M3_AI_DFD/M3_process_dictionary.md 的过程字典（编码字段按 nat 处理）
  M5  models/M5_AI_StateMachine/M5_AEB_statechart.puml 的守卫变量类型（下方显式表）

输出：formal_criterion_results.json + 控制台对照表
"""
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "experiment_kit", "prompt_rerun"))

from analyze_rerun import collect_types, parse_contracts, from_md, from_fmodule, PROJ  # noqa: E402
from precondition_tiers import tier  # noqa: E402  ← 唯一分类实现（与 Table VII-c 同源）

# M3 / M5 无显式类型声明，字段类型按下表（来自各自源文件的显式说明）
EXPLICIT_TYPES = {
    "M3": {"risk_level": "nat", "warning": "nat", "active": "nat", "type": "nat",
           "manoeuvre": "nat", "obj_count": "nat", "count": "nat", "lead_id": "nat",
           "road_id": "nat", "lane_id": "nat"},
    "M5": {"obj_count": "nat", "risk_level": "nat", "sensor_validity": "nat",
           "odd_active": "nat", "driver_accel_request": "nat", "warning": "nat",
           "ego_speed": "real", "min_ttc": "real", "deceleration": "real"},
}

AMBIGUOUS = ["及时", "安全", "合适", "适当", "合理", "尽快", "有效", "良好",
             "timely", "adequate", "appropriate", "reasonable", "sufficient",
             "efficient", "safe", "proper"]

WEIGHTS = [
    (0.4, 0.3, 0.3),      # 论文当前
    (0.2, 0.4, 0.4), (0.6, 0.2, 0.2), (0.5, 0.25, 0.25), (0.33, 0.33, 0.34),
    (0.25, 0.5, 0.25), (0.5, 0.5, 0.0), (0.34, 0.33, 0.33),
]


# ---------------------------------------------------------------- 类型映射
def _flat(types):
    out = {}
    for _t, fields in types.items():
        for fname, ftype in fields.items():
            if ftype in ("real", "nat", "String"):
                out.setdefault(fname, ftype)
    return out


def load_types(model_id):
    """返回嵌套类型表 {"_": {field: primitive}}，供 analyze_rerun.field_prim 使用。"""
    flat = {}
    if model_id in ("M1", "M1.1", "M2"):
        folder = {"M1": "M1_manual_human",
                  "M1.1": "M1_1_manual_plus_thresholds",
                  "M2": "M2_AI_SOFL_single"}[model_id]
        files = ({"M1": ["System.fModule", "BehaviorPlanning.fModule"],
                  "M1.1": ["System.fModule", "BehaviorPlanning.fModule"],
                  "M2": ["ADAS_System.fModule", "AEB_Branch.fModule"]}[model_id])
        types = {}
        for f in files:
            p = Path(BASE) / "models" / folder / f
            if not p.exists():
                continue
            code, _ = from_fmodule(p)
            for t, fields in collect_types(code).items():
                types.setdefault(t, {}).update(fields)
        flat = _flat(types)
    elif model_id == "M4":
        for f in ("M4_L0.puml", "M4_L1.puml"):
            p = Path(BASE) / "models" / "M4_AI_UML" / f
            if not p.exists():
                continue
            txt = p.read_text(encoding="utf-8-sig")
            for m in re.finditer(r"^\s*[+\-]?\s*([A-Za-z_]\w*)\s*:\s*(real|nat|String)\s*$",
                                 txt, re.M):
                flat.setdefault(m.group(1), m.group(2))
    else:
        flat = dict(EXPLICIT_TYPES.get(model_id, {}))
    return {"_": flat}


# ---------------------------------------------------------------- MES 侧
def _split_clauses(cond_list):
    from analyze_rerun import split_and
    out = []
    for s in cond_list or []:
        for part in split_and(str(s)):
            if part:
                out.append(part)
    return out


def mes_contract_texts(doc):
    pres, posts = [], []
    for e in doc.get("elements", []):
        pres += _split_clauses(e.get("preconditions"))
        for p in e.get("postconditions") or []:
            if isinstance(p, dict):
                posts += _split_clauses([p.get("guard", "")])
                posts += _split_clauses([p.get("effect", "")])
            else:
                posts += _split_clauses([p])
        for inv in (e.get("invariants") or []):
            posts += _split_clauses([inv])
    return pres, posts


MODEL_DIR = {"M1": "M1_manual_human", "M1.1": "M1_1_manual_plus_thresholds", "M2": "M2_AI_SOFL_single", "M3": "M3_AI_DFD",
             "M4": "M4_AI_UML", "M5": "M5_AI_StateMachine"}


def analyse_mes(model_id, level, types):
    p = Path(BASE) / "models" / MODEL_DIR[model_id] / ("MES_%s_%s.json" % (model_id, level))
    if not p.exists():
        return None
    doc = json.load(io.open(p, encoding="utf-8-sig"))
    els = doc.get("elements", [])
    pres, posts = mes_contract_texts(doc)

    pre_tiers, post_tiers, pre_fam = Counter(), Counter(), Counter()
    per_elem = []
    for e in els:
        cs = _split_clauses(e.get("preconditions"))
        ts = [tier(c, types) for c in cs]
        per_elem.append((e.get("name"), cs, ts))
        for t, f in ts:
            pre_tiers[t] += 1
            pre_fam[f] += 1
    for c in posts:
        post_tiers[tier(c, types)[0]] += 1

    n_el = len(els)
    eff5 = sum(1 for _n, _cs, ts in per_elem if any(t != "T1" for t, _f in ts))
    eff2 = sum(1 for _n, _cs, ts in per_elem
               if any(not (t == "T1" and f in ("null_guard", "empty_guard")) for t, f in ts))
    sub4 = sum(1 for _n, _cs, ts in per_elem if any(t == "T4" for t, _f in ts))

    all_text = " ".join(pres + posts)
    nonvac = " ".join([c for c in pres + posts if tier(c, types)[0] != "T1"])
    amb_l = sum(all_text.lower().count(w) for w in AMBIGUOUS)
    amb_u = sum(nonvac.lower().count(w) for w in AMBIGUOUS)
    quant = sum(1 for e in els if e.get("quantified")) / max(n_el, 1)

    return OrderedDict(
        model=model_id, level=level, elements=n_el,
        pre_clauses=len(pres), post_clauses=len(posts),
        pre_tiers=dict(pre_tiers), post_tiers=dict(post_tiers), pre_families=dict(pre_fam),
        effective_pre_legacy2=eff2, effective_pre_unified5=eff5, substantive_pre_t4=sub4,
        quantified_ratio=round(quant, 4),
        amb_ratio_legacy=round(min(amb_l / max(n_el, 1), 1.0), 4),
        amb_ratio_unified=round(min(amb_u / max(n_el, 1), 1.0), 4),
        source=str(p),
    )


def i4(pre_eff_ratio, quant, amb_ratio, w=(0.4, 0.3, 0.3)):
    return w[0] * pre_eff_ratio + w[1] * quant + w[2] * (1 - amb_ratio)


# ---------------------------------------------------------------- 源文本侧
def analyse_source(label, path, loader):
    code, _raw = loader(path)
    types = collect_types(code)
    pre_tiers, post_tiers, fam = Counter(), Counter(), Counter()
    eff = sub = pre_n = post_n = 0
    for _name, _mod, pres, posts in parse_contracts(code):
        pre_n += len(pres)
        post_n += len(posts)
        ts = [tier(c, types) for c in pres]
        if any(t != "T1" for t, _f in ts):
            eff += 1
        if any(t == "T4" for t, _f in ts):
            sub += 1
        for t, f in ts:
            pre_tiers[t] += 1
            fam[f] += 1
        for c in posts:
            post_tiers[tier(c, types)[0]] += 1
    n_proc = len(parse_contracts(code))
    return OrderedDict(
        label=label, processes=n_proc, pre=pre_n, post=post_n,
        pre_tiers=dict(pre_tiers), post_tiers=dict(post_tiers), families=dict(fam),
        effective_pre=eff, substantive_pre=sub,
        vacuous_rate_pre=round(pre_tiers["T1"] / pre_n, 4) if pre_n else 0.0,
        vacuous_rate_all=round((pre_tiers["T1"] + post_tiers["T1"]) / (pre_n + post_n), 4)
        if (pre_n + post_n) else 0.0,
    )


# ---------------------------------------------------------------- 权重敏感性
def weight_sensitivity(rows, criterion):
    key = {"legacy2": "effective_pre_legacy2", "unified5": "effective_pre_unified5",
           "strictT4": "substantive_pre_t4"}[criterion]
    amb = "amb_ratio_legacy" if criterion == "legacy2" else "amb_ratio_unified"
    out = []
    for w in WEIGHTS:
        vals = {}
        for r in rows:
            pre_eff = r[key] / max(r["elements"], 1)
            vals["%s_%s" % (r["model"], r["level"])] = round(
                i4(pre_eff, r["quantified_ratio"], r[amb], w), 4)
        out.append({"weights": list(w), "values": vals})
    stable = {}
    for w_row in out:
        v = w_row["values"]
        stable.setdefault("M2_L1_gt_M4_L1", []).append(v["M2_L1"] > v["M4_L1"])
        stable.setdefault("M1_L0_gt_M3_L0", []).append(v["M1_L0"] > v["M3_L0"])
        stable.setdefault("M1_L1_gt_M4_L1", []).append(v["M1_L1"] > v["M4_L1"])
    stable = {k: (all(v) if all(v) else not any(v)) for k, v in stable.items()}
    return out, stable


# ---------------------------------------------------------------- main
def main():
    rows = []
    for mid, levels in (("M1", ["L0", "L1"]), ("M1.1", ["L0", "L1"]),
                        ("M2", ["L0", "L1"]), ("M3", ["L0", "L1"]),
                        ("M4", ["L0", "L1"]), ("M5", ["L1"])):
        types = load_types(mid)
        for lv in levels:
            r = analyse_mes(mid, lv, types)
            if r:
                rows.append(r)

    print("=" * 116)
    print("I4 三口径对照（M1–M5 × L0/L1）；分类实现 = precondition_tiers.tier()（与 Table VII-c 同源）")
    print("=" * 116)
    print(f"{'模型':<5}{'层':<4}{'elem':>6}{'pre':>5}{'eff2':>6}{'eff5':>6}{'subT4':>7}"
          f"{'quant':>7}{'ambL':>7}{'ambU':>7}{'I4_leg2':>10}{'I4_unif5':>10}{'I4_T4':>8}")
    print("-" * 116)
    for r in rows:
        n = max(r["elements"], 1)
        r["I4_legacy2"] = round(i4(r["effective_pre_legacy2"] / n, r["quantified_ratio"],
                                   r["amb_ratio_legacy"]), 3)
        r["I4_unified5"] = round(i4(r["effective_pre_unified5"] / n, r["quantified_ratio"],
                                    r["amb_ratio_unified"]), 3)
        r["I4_strictT4"] = round(i4(r["substantive_pre_t4"] / n, r["quantified_ratio"],
                                    r["amb_ratio_unified"]), 3)
        print(f"{r['model']:<5}{r['level']:<4}{r['elements']:>6}{r['pre_clauses']:>5}"
              f"{r['effective_pre_legacy2']:>6}{r['effective_pre_unified5']:>6}"
              f"{r['substantive_pre_t4']:>7}{r['quantified_ratio']:>7.3f}"
              f"{r['amb_ratio_legacy']:>7.3f}{r['amb_ratio_unified']:>7.3f}"
              f"{r['I4_legacy2']:>10.3f}{r['I4_unified5']:>10.3f}{r['I4_strictT4']:>8.3f}")

    same = all(r["I4_legacy2"] == r["I4_unified5"] for r in rows)
    print(f"\n>> legacy2 与 unified5 是否逐项相等： {same}")

    sens, stable = {}, {}
    for crit in ("legacy2", "unified5", "strictT4"):
        sens[crit], stable[crit] = weight_sensitivity(rows, crit)
    keys = ["M1_L0", "M1_L1", "M2_L0", "M2_L1", "M3_L0", "M3_L1", "M4_L0", "M4_L1", "M5_L1"]
    for crit in ("unified5", "strictT4"):
        print()
        print("=" * 116)
        print(f"权重敏感性（口径 {crit}）：I4 = w1·有效pre + w2·量化 + w3·(1−歧义)")
        print("=" * 116)
        hdr = f"{'权重 (pre,quant,amb)':<24}" + "".join(f"{k:>9}" for k in keys)
        print(hdr)
        print("-" * len(hdr))
        for w_row in sens[crit]:
            w = w_row["weights"]
            print(f"({w[0]:.2f},{w[1]:.2f},{w[2]:.2f})".ljust(24)
                  + "".join(f"{w_row['values'].get(k, float('nan')):>9.3f}" for k in keys))
        print("  排序稳定性:", stable[crit])

    src_cases = [
        ("M1 人工基准", Path(BASE) / "models/M1_manual_human/System.fModule", None),
        ("M1' (L1)", Path(BASE) / "models/M1_manual_human/BehaviorPlanning.fModule", None),
        ("M2 MiniMax 无禁令", Path(BASE) / "models/M2_AI_SOFL_single/ADAS_System.fModule", None),
        ("M2' (L1)", Path(BASE) / "models/M2_AI_SOFL_single/AEB_Branch.fModule", None),
        ("A1 MiniMax+单点禁令", Path(BASE) / "experiment_kit/prompt_rerun/outputs/A1_minimax_prohibited.md", from_md),
        ("A2 MiniMax+单点禁令", Path(BASE) / "experiment_kit/prompt_rerun/outputs/A2_minimax_prohibited.md", from_md),
        ("B1 Hunyuan 无禁令", Path(BASE) / "experiment_kit/prompt_rerun/outputs/B1_hunyuan_unprohibited.md", from_md),
        ("B2 Hunyuan 无禁令", Path(BASE) / "experiment_kit/prompt_rerun/outputs/B2_hunyuan_unprohibited.md", from_md),
        ("C1 Hunyuan+单点禁令", Path(BASE) / "experiment_kit/prompt_rerun/outputs/C1_hunyuan_prohibited.md", from_md),
        ("D1 MiniMax+泛禁令", Path(BASE) / "experiment_kit/prompt_rerun/outputs/D1_minimax_family_ban.md", from_md),
        ("D2 Hunyuan+泛禁令", Path(BASE) / "experiment_kit/prompt_rerun/outputs/D2_hunyuan_family_ban.md", from_md),
        ("B3 MiniMax无禁令(当前)", Path(BASE) / "experiment_kit/prompt_rerun/outputs/B3_minimax_no_ban_current.md", from_md),
        ("B4 MiniMax无禁令(当前)", Path(BASE) / "experiment_kit/prompt_rerun/outputs/B4_minimax_no_ban_current.md", from_md),
    ]

    src_rows = []
    for label, path, loader in src_cases:
        if not path.exists():
            continue
        ld = loader if loader else (from_fmodule if path.suffix == ".fModule" else from_md)
        src_rows.append(analyse_source(label, path, ld))

    # M1 / M2 为双 module 模型：与 Table VII-c 一致，按"合并两 module"口径再给一行
    def merged_rows(tag):
        parts = [r for r in src_rows if r["label"].startswith(tag)]
        if len(parts) != 2:
            return None
        m = OrderedDict(label=tag + " 人工基准" if tag == "M1" else "M2 MiniMax 无禁令",
                        processes=sum(p["processes"] for p in parts),
                        pre=sum(p["pre"] for p in parts), post=sum(p["post"] for p in parts),
                        pre_tiers={}, post_tiers={}, families={}, effective_pre=0,
                        substantive_pre=0)
        for p in parts:
            for k in ("T1", "T2a", "T2b", "T3", "T4"):
                m["pre_tiers"][k] = m["pre_tiers"].get(k, 0) + p["pre_tiers"].get(k, 0)
            for k in ("T1", "T2a", "T2b", "T3", "T4"):
                m["post_tiers"][k] = m["post_tiers"].get(k, 0) + p["post_tiers"].get(k, 0)
            for k, v in p["families"].items():
                m["families"][k] = m["families"].get(k, 0) + v
            m["effective_pre"] += p["effective_pre"]
            m["substantive_pre"] += p["substantive_pre"]
        m["vacuous_rate_pre"] = round(m["pre_tiers"].get("T1", 0) / m["pre"], 4) if m["pre"] else 0.0
        tot = m["pre"] + m["post"]
        m["vacuous_rate_all"] = round(
            (m["pre_tiers"].get("T1", 0) + m["post_tiers"].get("T1", 0)) / tot, 4) if tot else 0.0
        return m

    merged_out = []
    for tag in ("M1", "M2"):
        m = merged_rows(tag)
        if m:
            merged_out.append(m)
    src_rows = merged_out + [r for r in src_rows if not r["label"].startswith(("M1", "M2"))]

    print()
    print("=" * 116)
    print("源文本侧统一判据（与 Table VII-c 同一 tier() 实现）")
    print("=" * 116)
    print(f"{'条件':<24}{'proc':>5}{'pre':>5}{'post':>6}{'T1':>5}{'T2a':>5}{'T2b':>5}"
          f"{'T3':>5}{'T4':>5}{'effPre':>9}{'subPre':>9}{'pre空洞率':>10}{'全率':>8}")
    print("-" * 116)
    for r in src_rows:
        t = r["pre_tiers"]
        print(f"{r['label']:<24}{r['processes']:>5}{r['pre']:>5}{r['post']:>6}"
              f"{t.get('T1', 0):>5}{t.get('T2a', 0):>5}{t.get('T2b', 0):>5}"
              f"{t.get('T3', 0):>5}{t.get('T4', 0):>5}"
              f"{r['effective_pre']:>4}/{r['processes']:<4}{r['substantive_pre']:>4}/{r['processes']:<4}"
              f"{r['vacuous_rate_pre']:>10.1%}{r['vacuous_rate_all']:>8.1%}")

    # ---- 与既有 Table VII-c 数据对拍 ----
    ref = Path(BASE) / "experiment_kit/prompt_rerun/precondition_tiers.json"
    check = None
    if ref.exists():
        old = json.load(io.open(ref, encoding="utf-8"))
        oldmap = {}
        for o in old:
            key = o["label"].replace(" ", "")
            oldmap[key] = o
        diffs = []
        for r in src_rows:
            key = r["label"].replace(" ", "")
            o = oldmap.get(key)
            if not o:
                continue
            ot = o["tiers"]
            nt = r["pre_tiers"]
            for k in ("T1", "T2a", "T2b", "T3", "T4"):
                if ot.get(k, 0) != nt.get(k, 0):
                    diffs.append(f"{r['label']}.{k}: 旧 {ot.get(k, 0)} vs 新 {nt.get(k, 0)}")
        check = {"compared": len(src_rows), "diffs": diffs, "identical": not diffs}
        print()
        print("对拍 Table VII-c（precondition_tiers.json）：",
              "完全一致" if not diffs else f"存在 {len(diffs)} 处差异")
        for d in diffs:
            print("   ", d)

    out = {
        "generated_by": "formal_criterion_checker.py",
        "classifier": "experiment_kit/prompt_rerun/precondition_tiers.py :: tier()（与 Table VII-c 同源）",
        "note": ("I4 三口径：legacy2=两型排除（旧实现，仅复核）；unified5=五族恒真式族（本文采用）；"
                 "strictT4=要求至少一条实质子句（下界披露）"),
        "models": rows,
        "weight_sensitivity": sens,
        "ordering_stability": stable,
        "source_conditions": src_rows,
        "crosscheck_vs_table_vii_c": check,
    }
    p = Path(BASE) / "formal_criterion_results.json"
    io.open(p, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n写入:", p)


if __name__ == "__main__":
    main()
