#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
context_ladder_analysis.py —— 上下文污染阶梯对照（评审模型 = DeepSeek-v4-pro 同一模型）

三级阶梯（唯一变量 = 会话上下文）：
  C-clean        review_roundC1/2/3.json   全新会话、只喂脏模型+规格（干净）
  B-contaminated review_roundB1/2/3.json   同会话先读过 A(Hy) 的结果（污染）
  B-anchored     review_anchored.json      显式展示 A 的 findings 后再评（锚定）

外加跨模型参照：A = Tencent Hunyuan 4 Flash（第一个评审者，无上游）。

判定口径与 cross_reviewer_analysis.py 一致（严格语义匹配）：
  - finding 命中注入缺陷 DEF-x 才算检出；报告原生缺陷（非注入）计为误报 FP
  - M5 DEF-4（T10_guard）须精确匹配才算命中，route/D1/E9 类报告不算
  - A 的 ADJ 为既有结果，保留原值（其 M5 DEF-4 存在已知判定疑义）

审计发现（本脚本一并输出）：
  - M3 的 DEF-2 表现载体（traceability note 里的 6.0/3.0 s）被 DEF-6 的删除连带
    去除 → 脏 M3 中已无任何 2.0/0.5 s 可观测表现，该缺陷位对所有评审者均不可检出
  - FP 多为真实原生缺陷（重复 E2、空 owner、空 source、悬空流、漏 D3 写入等，
    已对干净版核实），注入口径的"误报率"低估了评审者的实际查错能力
"""
import io, os, json

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"

# ---- 评审模型 C（DeepSeek 干净会话，三轮连续）人工复核 ----
# finding 索引 -> 命中的 DEF-x / None=误报（非注入缺陷）
ADJ_C = {
    1: {
        "M1": {0:"DEF-1",1:"DEF-1",2:"DEF-1",3:"DEF-2",4:"DEF-2",5:None,6:None,7:None,8:None,9:"DEF-5",10:None},
        "M3": {0:"DEF-1",1:"DEF-1",2:"DEF-1",3:None,4:"DEF-3",5:"DEF-3",6:None,7:"DEF-4"},
        "M4": {0:"DEF-1",1:"DEF-1",2:"DEF-1",3:"DEF-2",4:"DEF-2",5:"DEF-2",6:"DEF-2",7:"DEF-3",8:"DEF-3",9:None},
        "M5": {0:"DEF-2",1:"DEF-2",2:"DEF-2",3:"DEF-2",4:"DEF-2",5:"DEF-3",6:None},
    },
    2: {
        "M1": {0:"DEF-1",1:"DEF-1",2:"DEF-1",3:"DEF-2",4:"DEF-2",5:"DEF-3",6:None,7:None,8:None,9:None,10:"DEF-5",11:None},
        "M3": {0:"DEF-1",1:"DEF-1",2:"DEF-1",3:None,4:"DEF-3",5:"DEF-3",6:None,7:"DEF-3",8:"DEF-4"},
        "M4": {0:"DEF-1",1:"DEF-1",2:"DEF-1",3:"DEF-2",4:"DEF-2",5:"DEF-2",6:"DEF-2",7:"DEF-3",8:"DEF-3",9:"DEF-2",10:None},
        "M5": {0:"DEF-2",1:"DEF-2",2:"DEF-2",3:"DEF-2",4:"DEF-2",5:"DEF-3",6:None},
    },
    3: {
        "M1": {0:"DEF-1",1:"DEF-1",2:"DEF-6",3:"DEF-1",4:"DEF-2",5:"DEF-2",6:"DEF-3",7:None,8:None,9:None,10:None,11:"DEF-5",12:None},
        "M3": {0:"DEF-1",1:"DEF-1",2:"DEF-1",3:"DEF-6",4:None,5:"DEF-3",6:"DEF-3",7:None,8:"DEF-3",9:"DEF-4"},
        "M4": {0:"DEF-1",1:"DEF-1",2:"DEF-1",3:"DEF-6",4:"DEF-2",5:"DEF-2",6:"DEF-2",7:"DEF-2",8:"DEF-3",9:"DEF-3",10:"DEF-2",11:None},
        "M5": {0:"DEF-2",1:"DEF-2",2:"DEF-2",3:"DEF-2",4:"DEF-2",5:"DEF-3",6:None,7:"DEF-6",8:None,9:None,10:None,11:None},
    },
}

# ---- B（污染会话）与锚定轮：与 cross_reviewer_analysis.py 完全一致 ----
ADJ_B = {
    1: {
        "M1": {0:"DEF-1",1:"DEF-2",2:"DEF-3",3:"DEF-4",4:"DEF-5",5:"DEF-6"},
        "M3": {0:"DEF-1",1:"DEF-4",2:"DEF-3",3:"DEF-3",4:"DEF-5",5:"DEF-6"},
        "M4": {0:"DEF-1",1:"DEF-4",2:"DEF-2",3:"DEF-3",4:"DEF-5",5:"DEF-6"},
        "M5": {0:"DEF-2",1:"DEF-3",2:"DEF-3",3:"DEF-3",4:None,5:None,6:"DEF-5"},
    },
    2: {
        "M1": {0:"DEF-1",1:"DEF-2",2:"DEF-4",3:"DEF-5"},
        "M3": {0:"DEF-1",1:"DEF-4",2:"DEF-3",3:"DEF-5"},
        "M4": {0:"DEF-1",1:"DEF-4",2:"DEF-2",3:"DEF-5"},
        "M5": {0:"DEF-2",1:"DEF-3",2:"DEF-3",3:None,4:"DEF-5"},
    },
    3: {
        "M1": {0:"DEF-1",1:"DEF-2",2:"DEF-3",3:"DEF-4",4:"DEF-5"},
        "M3": {0:"DEF-1",1:"DEF-4",2:"DEF-3",3:"DEF-5"},
        "M4": {0:"DEF-1",1:"DEF-4",2:"DEF-2",3:"DEF-3",4:"DEF-5"},
        "M5": {0:"DEF-2",1:"DEF-3",2:"DEF-3",3:None,4:"DEF-5"},
    },
}
ADJ_ANCHORED = {
    "M1": {0:"DEF-1",1:"DEF-2",2:"DEF-3",3:"DEF-4",4:"DEF-5",5:"DEF-6"},
    "M3": {0:"DEF-1",1:"DEF-4",2:"DEF-3",3:"DEF-5",4:None},
    "M4": {0:"DEF-1",1:"DEF-4",2:"DEF-2",3:"DEF-3",4:"DEF-5",5:"DEF-6"},
    "M5": {0:"DEF-2",1:"DEF-3",2:"DEF-3",3:None,4:"DEF-5",5:None},
}

MODELS = ["M1", "M3", "M4", "M5"]
DEFS = ["DEF-1", "DEF-2", "DEF-3", "DEF-4", "DEF-5", "DEF-6"]


def load(p):
    return json.load(io.open(p, encoding="utf-8"))


def score(findings, amap):
    hits, fp = set(), 0
    for idx, f in enumerate(findings):
        t = amap.get(idx)
        if t:
            hits.add(t)
        else:
            fp += 1
    return hits, fp


def summarize(rows, label):
    out = {"reviewer": label, "by_model": {}, "overall": {}}
    for mid in MODELS:
        rs = [r for r in rows if r["model"] == mid]
        rates = [r["detection_rate"] for r in rs]
        mean = sum(rates) / len(rates)
        var = sum((x - mean) ** 2 for x in rates) / (len(rates) - 1) if len(rates) > 1 else 0.0
        allhits = set()
        for r in rs:
            allhits.update(r["detected"])
        out["by_model"][mid] = {
            "rounds": rates,
            "mean_detection_rate": round(mean, 3),
            "variance": round(var, 4),
            "mean_false_positive_rate": round(sum(r["false_positive_rate"] for r in rs) / len(rs), 3),
            "union_detected": sorted(allhits, key=lambda x: int(x.split("-")[1])),
            "union_detection_rate": round(len(allhits) / 6, 3),
        }
    allrates = [r["detection_rate"] for r in rows]
    tot_fp = sum(r["false_positives"] for r in rows)
    tot_f = sum(r["n_findings"] for r in rows)
    out["overall"] = {
        "mean_detection_rate": round(sum(allrates) / len(allrates), 3),
        "total_false_positives": tot_fp,
        "total_findings": tot_f,
        "overall_false_positive_rate": round(tot_fp / max(tot_f, 1), 3),
    }
    tp = sum(x["n_detected"] for x in rows)
    fn = len(rows) * 6 - tp
    fp = tot_fp
    tn = max(0, len(rows) * 6 - fp)
    n = tp + fn + fp + tn
    if n:
        po = (tp + tn) / n
        pe = ((tp + fp) / n) * ((tp + fn) / n) + ((fn + tn) / n) * ((fp + tn) / n)
        kappa = (po - pe) / (1 - pe) if pe < 1 else 0
        out["overall"]["cohen_kappa"] = round(kappa, 3)
        out["overall"]["confusion"] = {"TP": tp, "FN": fn, "FP": fp, "TN": tn}
    return out


def rounds_rows(path_fmt, adj, reviewer, rounds):
    rows = []
    for rnd in rounds:
        rev = load(os.path.join(BASE, path_fmt % rnd))
        for rv in rev["reviews"]:
            mid = rv["model"]
            findings = rv.get("findings", [])
            hits, fp = score(findings, adj[rnd][mid])
            rows.append({"round": rnd, "model": mid, "reviewer": reviewer,
                         "detected": sorted(hits, key=lambda x: int(x.split("-")[1])),
                         "n_detected": len(hits),
                         "n_findings": len(findings), "false_positives": fp,
                         "detection_rate": round(len(hits) / 6, 3),
                         "false_positive_rate": round(fp / len(findings), 3) if findings else 0.0})
    return rows


def jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return round(len(a & b) / len(a | b), 3) if (a | b) else 0.0


def main():
    # C 干净三轮
    rows_c = rounds_rows("review_roundC%d.json", ADJ_C, "DeepSeek-v4-pro", (1, 2, 3))
    c_res = summarize(rows_c, "DeepSeek-v4-pro (clean session)")

    # B 污染三轮（复用既有 ADJ）
    rows_b = rounds_rows("review_roundB%d.json", ADJ_B, "DeepSeek-v4-pro", (1, 2, 3))
    b_res = summarize(rows_b, "DeepSeek-v4-pro (contaminated session)")

    # 锚定轮（单轮）
    anchor = load(os.path.join(BASE, "review_anchored.json"))
    anchor_rows = []
    for rv in anchor["reviews"]:
        mid = rv["model"]
        findings = rv.get("findings", [])
        hits, fp = score(findings, ADJ_ANCHORED[mid])
        anchor_rows.append({"round": 0, "model": mid, "reviewer": "DeepSeek-v4-pro (anchored)",
                            "detected": sorted(hits, key=lambda x: int(x.split("-")[1])),
                            "n_detected": len(hits), "n_findings": len(findings),
                            "false_positives": fp,
                            "detection_rate": round(len(hits) / 6, 3),
                            "false_positive_rate": round(fp / len(findings), 3) if findings else 0.0})
    anch_res = summarize(anchor_rows, "DeepSeek-v4-pro (anchored)")

    # A（Hy）—— 既有结果
    a_res = load(os.path.join(BASE, "defect_injection_results.json"))

    # 并集
    def union_of(res):
        return {mid: set(res["by_model"][mid]["union_detected"]) for mid in MODELS}

    c_union, b_union = union_of(c_res), union_of(b_res)
    a_union = {mid: set(a_res["by_model"][mid]["union_detected"]) for mid in MODELS}
    anch_union = {mid: set(r["detected"]) for mid, r in
                  [(m, next(x for x in anchor_rows if x["model"] == m)) for m in MODELS]}

    # 逐缺陷检出画像（union 口径）
    profile = {}
    for d in DEFS:
        profile[d] = {
            "A_Hy": [mid for mid in MODELS if d in a_union[mid]],
            "B_contaminated": [mid for mid in MODELS if d in b_union[mid]],
            "B_anchored": [mid for mid in MODELS if d in anch_union[mid]],
            "C_clean": [mid for mid in MODELS if d in c_union[mid]],
        }

    jac = {}
    for mid in MODELS:
        jac[mid] = {
            "C_vs_B": jaccard(c_union[mid], b_union[mid]),
            "C_vs_B_anchored": jaccard(c_union[mid], anch_union[mid]),
            "C_vs_A": jaccard(c_union[mid], a_union[mid]),
            "C_union": sorted(c_union[mid], key=lambda x: int(x.split("-")[1])),
            "B_union": sorted(b_union[mid], key=lambda x: int(x.split("-")[1])),
            "B_anchored_union": sorted(anch_union[mid], key=lambda x: int(x.split("-")[1])),
            "A_union": sorted(a_union[mid], key=lambda x: int(x.split("-")[1])),
        }

    out = {
        "design": "context-contamination ladder, reviewer model fixed (DeepSeek-v4-pro); "
                  "C=clean session, B=contaminated (read A's results in-session), "
                  "B_anchored=shown A's findings explicitly; A=Hunyuan Hy cross-model reference",
        "reviewer_C_clean": c_res,
        "reviewer_B_contaminated": b_res,
        "reviewer_B_anchored_rows": anchor_rows,
        "reviewer_B_anchored_union_detection": {mid: round(len(anch_union[mid]) / 6, 3) for mid in MODELS},
        "reviewer_A_reference": {
            "name": "Tencent Hunyuan 4 Flash",
            "mean_detection_rate": a_res["overall"]["mean_detection_rate"],
            "cohen_kappa": a_res["overall"]["cohen_kappa"],
            "overall_false_positive_rate": a_res["overall"]["overall_false_positive_rate"],
        },
        "ladder_summary": {
            "clean_C": {"mean_detection": c_res["overall"]["mean_detection_rate"],
                        "kappa": c_res["overall"]["cohen_kappa"],
                        "fp_rate": c_res["overall"]["overall_false_positive_rate"]},
            "contaminated_B": {"mean_detection": b_res["overall"]["mean_detection_rate"],
                               "kappa": b_res["overall"]["cohen_kappa"],
                               "fp_rate": b_res["overall"]["overall_false_positive_rate"]},
            "anchored_B": {"mean_detection": round(sum(r["detection_rate"] for r in anchor_rows) / 4, 3),
                           "kappa": anch_res["overall"]["cohen_kappa"],
                           "fp_rate": anch_res["overall"]["overall_false_positive_rate"]},
        },
        "defect_detection_profile": profile,
        "jaccard_unions": jac,
        "audit_notes": [
            "M3 DEF-2 不可检出：该缺陷的 6.0/3.0 s 表现仅存在于 traceability[note]，"
            "被 DEF-6（删除后半追溯表）连带删除；脏 M3 中已无任何 2.0/0.5 s 可观测表现。"
            "A/B/C 全部漏检该位是不可检出所致，非评审能力差异。有效最大检出率为 M3 5/6。",
            "FP 多为真实原生缺陷（已对干净版核实：两个 id=E2、inputs.source 全空、stores.owner 全空、"
            "悬空 active 流、F1 漏写 D3、追溯引用不存在的 F3.x 等）。注入口径的误报率低估了实际查错能力，"
            "C-clean 的高 FP 率主要来自对原生缺陷的全面报告。",
            "A 的 ADJ 为既有结果且口径偏松（部分原生缺陷报告被计为 DEF 命中），"
            "B/C 采用严格语义匹配；跨模型比较时 A 的检出率略高估、误报率略低估。",
            "M5 DEF-4（T10_guard 流删除）三位评审者均未精确命中，都转而报告 M5 原生的 route/D1/E9 缺口；"
            "『流删除』类缺陷在基于迁移的表示法下难以精确定位。",
            "三轮均为同一会话连续评审（与 A/B 口径一致），轮次间存在自我锚定："
            "C 的 findings 数逐轮递增（36→39→47）、检出率逐轮上升（0.458→0.500→0.667），"
            "轮次方差不作为独立重复估计。",
            "C vs B 的差值应读作『上下文 + 会话随机性』的合并影响上界，不能归因为纯上下文效应。",
        ],
    }

    io.open(os.path.join(BASE, "context_ladder_results.json"), "w", encoding="utf-8").write(
        json.dumps(out, indent=2, ensure_ascii=False))

    # 打印
    print("=== 上下文阶梯（同一评审模型 DeepSeek-v4-pro）===")
    for k, v in out["ladder_summary"].items():
        print("%-16s mean_det=%s  kappa=%s  fp=%s" % (k, v.get("mean_detection"), v.get("kappa"), v.get("fp_rate")))
    print("\n%-5s | %-8s | %-8s | %-8s | %-8s" % ("model", "C_det", "B_det", "Jac(C,B)", "Jac(C,A)"))
    for mid in MODELS:
        print("%-5s | %-8s | %-8s | %-8s | %-8s" % (
            mid, c_res["by_model"][mid]["mean_detection_rate"],
            b_res["by_model"][mid]["mean_detection_rate"],
            jac[mid]["C_vs_B"], jac[mid]["C_vs_A"]))
    print("\n逐缺陷检出画像（union, 模型列表）:")
    for d, v in profile.items():
        print("  %s: A=%s B=%s Anch=%s C=%s" % (d, v["A_Hy"], v["B_contaminated"], v["B_anchored"], v["C_clean"]))


if __name__ == "__main__":
    main()
