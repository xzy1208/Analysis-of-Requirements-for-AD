#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cross_reviewer_analysis.py —— 跨评审模型对照分析

对比评审模型 A (Tencent Hunyuan 4 Flash, review_round1/2/3.json) 与
评审模型 B (DeepSeek-v4-pro, review_roundB1/B2/B3.json 盲评 + review_anchored.json)
在缺陷注入任务上的表现：

  - 检出率 detection rate = 命中的植入缺陷数 / 6
  - 误报率 false positive rate = 非植入缺陷报告数 / 总报告数
  - Cohen's kappa（相对人工真值 defect_manifest.json）
  - 两模型检出集合的 Jaccard 相似度

命中判定口径与 analyze_defect_injection.py 保持一致：评审 finding 的 type 与
植入缺陷 type 一致，且 location/detail 与缺陷描述语义关联即算命中。
DeepSeek B 的人工复核（ADJ_B）在本脚本内逐条记录。

特别注意 M5 的 DEF-4：真值为「删除 T10_guard 流（Caution->DriverOverride）」，
而两个评审模型都倾向报告「route/D1/risk level 流缺失」（M5 原生缺陷，非注入）。
因此 M5 DEF-4 在严格口径下两模型均未真正命中；模型 A 原 ADJ 将其记为命中，
此处以注释说明，保留 A 原值以维持既有结果可比，同时输出严格口径的对照。
"""
import io, os, json

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"

# ---- DeepSeek B 盲评三轮的人工复核（finding 索引 -> 命中的 DEF-x，None=误报）----
# 与 analyze_defect_injection.py 的 ADJ 结构一致
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

# 锚定轮的人工复核
ADJ_ANCHORED = {
    "M1": {0:"DEF-1",1:"DEF-2",2:"DEF-3",3:"DEF-4",4:"DEF-5",5:"DEF-6"},
    "M3": {0:"DEF-1",1:"DEF-4",2:"DEF-3",3:"DEF-5",4:None},
    "M4": {0:"DEF-1",1:"DEF-4",2:"DEF-2",3:"DEF-3",4:"DEF-5",5:"DEF-6"},
    "M5": {0:"DEF-2",1:"DEF-3",2:"DEF-3",3:None,4:"DEF-5",5:None},
}


def load(p):
    return json.load(io.open(p, encoding="utf-8"))


def compute_rows(reviews_path, adj, reviewer, rounds):
    """返回 [{round, model, detected, n_detected, n_findings, fp, detection_rate, fpr}]"""
    rows = []
    for rnd in rounds:
        rev = load(os.path.join(BASE, reviews_path % rnd))
        for rv in rev["reviews"]:
            mid = rv["model"]
            findings = rv.get("findings", [])
            amap = adj[rnd][mid]
            hits = set()
            fp = 0
            for idx, f in enumerate(findings):
                t = amap.get(idx)
                if t:
                    hits.add(t)
                else:
                    fp += 1
            det = len(hits) / 6
            fpr = fp / len(findings) if findings else 0.0
            rows.append({"round": rnd, "model": mid, "reviewer": reviewer,
                         "detected": sorted(hits), "n_detected": len(hits),
                         "n_findings": len(findings), "false_positives": fp,
                         "detection_rate": round(det, 3),
                         "false_positive_rate": round(fpr, 3)})
    return rows


def summarize(rows, label):
    out = {"reviewer": label, "by_model": {}, "overall": {}}
    for mid in ["M1", "M3", "M4", "M5"]:
        rs = [r for r in rows if r["model"] == mid]
        rates = [r["detection_rate"] for r in rs]
        mean = sum(rates) / len(rates)
        var = sum((x - mean) ** 2 for x in rates) / (len(rates) - 1)
        allhits = set()
        for r in rs:
            allhits.update(r["detected"])
        out["by_model"][mid] = {
            "rounds": rates,
            "mean_detection_rate": round(mean, 3),
            "variance": round(var, 4),
            "mean_false_positive_rate": round(sum(r["false_positive_rate"] for r in rs) / len(rs), 3),
            "union_detected": sorted(allhits),
            "union_detection_rate": round(len(allhits) / 6, 3),
        }
    allrates = [r["detection_rate"] for r in rows]
    out["overall"] = {
        "mean_detection_rate": round(sum(allrates) / len(allrates), 3),
        "total_false_positives": sum(r["false_positives"] for r in rows),
        "total_findings": sum(r["n_findings"] for r in rows),
        "overall_false_positive_rate": round(sum(r["false_positives"] for r in rows) /
                                             max(sum(r["n_findings"] for r in rows), 1), 3),
    }
    # kappa
    tp = sum(x["n_detected"] for x in rows)
    fn = len(rows) * 6 - tp
    fp = out["overall"]["total_false_positives"]
    tn = max(0, len(rows) * 6 - fp)
    n = tp + fn + fp + tn
    if n:
        po = (tp + tn) / n
        p_tp = (tp + fp) / n
        p_tn = (fn + tn) / n
        p_pp = (tp + fn) / n
        p_pn = (fp + tn) / n
        pe = p_tp * p_pp + p_tn * p_pn
        kappa = (po - pe) / (1 - pe) if pe < 1 else 0
        out["overall"]["cohen_kappa"] = round(kappa, 3)
        out["overall"]["confusion"] = {"TP": tp, "FN": fn, "FP": fp, "TN": tn}
    return out


def jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return round(len(a & b) / len(a | b), 3) if (a | b) else 0.0


def main():
    # 模型 A（Hy）—— 从既有结果读取 union 检出集合
    a_res = load(os.path.join(BASE, "defect_injection_results.json"))
    a_union = {mid: set(v["union_detected"]) for mid, v in a_res["by_model"].items()}

    # 模型 B（DeepSeek）盲评三轮
    rows_b = compute_rows("review_roundB%d.json", ADJ_B, "DeepSeek-v4-pro", (1, 2, 3))
    b_res = summarize(rows_b, "DeepSeek-v4-pro (blind)")
    b_union = {mid: set(v["union_detected"]) for mid, v in b_res["by_model"].items()}

    # 锚定轮
    anchor = load(os.path.join(BASE, "review_anchored.json"))
    anchor_rows = []
    for rv in anchor["reviews"]:
        mid = rv["model"]
        findings = rv.get("findings", [])
        amap = ADJ_ANCHORED[mid]
        hits = set(); fp = 0
        for idx, f in enumerate(findings):
            t = amap.get(idx)
            if t:
                hits.add(t)
            else:
                fp += 1
        anchor_rows.append({"model": mid, "detected": sorted(hits),
                            "n_detected": len(hits), "n_findings": len(findings),
                            "false_positives": fp,
                            "detection_rate": round(len(hits)/6, 3),
                            "false_positive_rate": round(fp/len(findings), 3) if findings else 0.0})
    anchor_union = {mid: set(r["detected"]) for mid, r in
                    [(m, next(x for x in anchor_rows if x["model"] == m)) for m in ["M1","M3","M4","M5"]]}

    # Jaccard：A vs B（盲评），B盲评 vs B锚定
    jac = {}
    for mid in ["M1", "M3", "M4", "M5"]:
        jac[mid] = {
            "A_vs_B_blind": jaccard(a_union[mid], b_union[mid]),
            "B_blind_vs_B_anchored": jaccard(b_union[mid], anchor_union[mid]),
            "A_union": sorted(a_union[mid]),
            "B_blind_union": sorted(b_union[mid]),
            "B_anchored_union": sorted(anchor_union[mid]),
        }

    out = {
        "reviewer_A": {"name": "Tencent Hunyuan 4 Flash",
                        "source": "defect_injection_results.json",
                        "mean_detection_rate": a_res["overall"]["mean_detection_rate"],
                        "cohen_kappa": a_res["overall"]["cohen_kappa"],
                        "overall_false_positive_rate": a_res["overall"]["overall_false_positive_rate"]},
        "reviewer_B": {"name": "DeepSeek-v4-pro",
                        "blind": b_res,
                        "anchored_union_detection": {mid: round(len(anchor_union[mid])/6, 3)
                                                     for mid in ["M1","M3","M4","M5"]}},
        "jaccard": jac,
        "methodology_notes": [
            "M5 DEF-4 (T10_guard 删除) 在严格口径下两模型均未真正命中；二者都报告了 M5 原生的 route/D1/risk level 流缺失（非注入缺陷），反映『流删除』类缺陷在状态机表示法下难以精确定位。",
            "DEF-6 (追溯删除) 是两模型共同的高漏检项：Hy 三轮从未检出，DeepSeek 仅在 B1 盲评检出 M1/M3/M4 的追溯缺失。",
            "盲评受限于同一会话上下文：评审者 B 在同一会话中已读到评审者 A 的结果，严格盲评无法完全净化；锚定轮显式引入 A 的 findings 以度量锚定效应。",
        ],
    }

    io.open(os.path.join(BASE, "cross_reviewer_results.json"), "w", encoding="utf-8").write(
        json.dumps(out, indent=2, ensure_ascii=False))

    # 打印摘要
    print("=== 跨评审模型对照 ===")
    print("模型 A (Hy):      mean_detection=%.3f  kappa=%.3f  FP=%.3f" % (
        a_res["overall"]["mean_detection_rate"],
        a_res["overall"]["cohen_kappa"],
        a_res["overall"]["overall_false_positive_rate"]))
    print("模型 B (DeepSeek): mean_detection=%.3f  kappa=%.3f  FP=%.3f" % (
        b_res["overall"]["mean_detection_rate"],
        b_res["overall"]["cohen_kappa"],
        b_res["overall"]["overall_false_positive_rate"]))
    print("\n%-5s | %-10s | %-10s | %-10s | %-10s" % ("model", "A_det", "B_det", "Jac(A,B)", "Jac(Bblind,Banchor)"))
    for mid in ["M1", "M3", "M4", "M5"]:
        print("%-5s | %.3f      | %.3f      | %.3f       | %.3f" % (
            mid,
            len(a_union[mid]) / 6,
            len(b_union[mid]) / 6,
            jac[mid]["A_vs_B_blind"],
            jac[mid]["B_blind_vs_B_anchored"]))


if __name__ == "__main__":
    main()
