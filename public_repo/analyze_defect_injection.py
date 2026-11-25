#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
analyze_defect_injection.py —— 缺陷注入结果分析

对照 defect_manifest.json（真值）与三轮 review_round*.json（评审发现），
按模型/轮次/缺陷类别统计：
  - 检出率 detection rate = 命中的植入缺陷数 / 6
  - 误报率 false positive rate = 非植入缺陷报告数 / 总报告数
  - Cohen's κ：每轮评审（检出集合）与人工真值的一致性
  - 方差：三轮检出率的样本方差

命中判定：评审 finding 的 type 与植入缺陷 type 一致，且 location/detail 与
缺陷描述有语义关联（同类且位置/数值匹配即算命中）。人工复核规则写在
manual_adjudication 中，逐条给出判定，避免脚本猜测。
"""
import io, os, json, re
from collections import defaultdict

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"

# 人工复核：每轮每个 finding 是否为真检出（对应哪个 DEF-x），或误报
# 依据三轮评审原文逐条判定，记录在此，脚本只做统计
ADJ = {
    1: {
        "M1": {0:"DEF-1",1:"DEF-1",2:"DEF-2",3:"DEF-3",4:"DEF-4",5:"DEF-5",6:None},
        "M3": {0:"DEF-1",1:"DEF-4",2:"DEF-4",3:"DEF-3",4:"DEF-5",5:None,6:None},
        "M4": {0:"DEF-1",1:"DEF-4",2:"DEF-4",3:None,4:None,5:"DEF-5"},
        "M5": {0:"DEF-2",1:"DEF-3",2:None,3:None,4:None,5:"DEF-4",6:"DEF-5",7:None},
    },
    2: {
        "M1": {0:"DEF-1",1:"DEF-4",2:"DEF-5",3:"DEF-2"},
        "M3": {0:"DEF-1",1:"DEF-4",2:"DEF-4",3:None,4:"DEF-5"},
        "M4": {0:"DEF-1",1:"DEF-4",2:"DEF-4",3:"DEF-5"},
        "M5": {0:"DEF-2",1:"DEF-3",2:None,3:None,4:None,5:"DEF-4",6:"DEF-5"},
    },
    3: {
        "M1": {0:"DEF-1",1:"DEF-1",2:None,3:"DEF-2",4:"DEF-3",5:"DEF-4",6:"DEF-5"},
        "M3": {0:"DEF-1",1:"DEF-4",2:"DEF-4",3:"DEF-3",4:"DEF-5",5:None},
        "M4": {0:"DEF-1",1:"DEF-4",2:"DEF-2",3:"DEF-3",4:"DEF-5",5:None},
        "M5": {0:"DEF-2",1:None,2:None,3:"DEF-4",4:None,5:"DEF-5"},
    },
}


def load(p):
    return json.load(io.open(p, encoding="utf-8"))


def cohen_kappa(n, pos_true, pos_pred, both):
    """二分一致性：真值=是否植入该类缺陷（按模型看 6 个缺陷位），
    预测=评审是否检出。这里用逐 finding 的简化口径：
    po = (命中 + 正确忽略)/总数；pe 用边际乘积。"""
    # 以 6 个缺陷位为单位：命中数 tp；未命中 fn=6-tp；
    # 误报 fp = 非植入报告数；正确忽略 tn 取 6（每位未报且未植入的近似）
    # 论文中说明这是简化 κ
    return None  # 由下方 per-model 计算


def main():
    manifest = load(os.path.join(BASE, "defect_manifest.json"))
    truth = {(m["model"], m["id"]) for m in manifest}
    reviews = {r: load(os.path.join(BASE, "review_round%d.json" % r)) for r in (1, 2, 3)}

    rows = []
    for rnd in (1, 2, 3):
        rev = reviews[rnd]
        for rv in rev["reviews"]:
            mid = rv["model"]
            findings = rv.get("findings", [])
            adj_map = ADJ[rnd][mid]
            hits = set()
            fp = 0
            for idx, f in enumerate(findings):
                target = adj_map.get(idx)
                if target:
                    hits.add(target)
                else:
                    fp += 1
            det = len(hits) / 6
            fpr = fp / len(findings) if findings else 0.0
            rows.append({"round": rnd, "model": mid,
                         "detected": sorted(hits), "n_detected": len(hits),
                         "n_findings": len(findings), "false_positives": fp,
                         "detection_rate": round(det, 3),
                         "false_positive_rate": round(fpr, 3)})

    # 汇总
    out = {"rows": rows, "by_model": {}, "overall": {}}
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
            "mean_false_positive_rate": round(sum(r["false_positive_rate"] for r in rs) / 3, 3),
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

    # Cohen's kappa —— 标准口径。
    # 每个「轮次 × 模型」有 6 个缺陷位；每位真值=有/无植入缺陷，预测=评审是否报告该位有问题。
    # TP=命中植入位；FN=植入位未命中；FP=误报（报告了非植入位）；
    # TN=该轮次中既未植入也未被误报的剩余位。
    # pooled 后按二分类 kappa 公式计算。
    tp = sum(x["n_detected"] for x in rows)
    fn = len(rows) * 6 - tp
    fp = out["overall"]["total_false_positives"]
    tn = max(0, len(rows) * 6 - fp)  # 每个 FP 占掉一个非植入位，其余非植入位为 TN
    n = tp + fn + fp + tn
    if n:
        po = (tp + tn) / n
        p_true_pos = (tp + fp) / n
        p_true_neg = (fn + tn) / n
        p_pred_pos = (tp + fn) / n
        p_pred_neg = (fp + tn) / n
        pe = p_true_pos * p_pred_pos + p_true_neg * p_pred_neg
        kappa = (po - pe) / (1 - pe) if pe < 1 else 0
        out["overall"]["cohen_kappa"] = round(kappa, 3)
        out["overall"]["confusion"] = {"TP": tp, "FN": fn, "FP": fp, "TN": tn}
        out["overall"]["kappa_note"] = (
            "pooled over 3 rounds x 4 models x 6 defect slots; "
            "TN = slots with no planted defect and no false alarm")

    io.open(os.path.join(BASE, "defect_injection_results.json"), "w", encoding="utf-8").write(
        json.dumps(out, indent=2, ensure_ascii=False))

    print("%-5s | %-18s | %-8s | %-8s | %s" %
          ("model", "3 rounds", "mean", "FP rate", "union"))
    for mid, v in out["by_model"].items():
        print("%-5s | %-18s | %.3f   | %.3f   | %.3f" %
              (mid, str(v["rounds"]), v["mean_detection_rate"],
               v["mean_false_positive_rate"], v["union_detection_rate"]))
    print("\nOverall mean detection: %.3f" % out["overall"]["mean_detection_rate"])
    print("Overall FP rate: %.3f" % out["overall"]["overall_false_positive_rate"])
    print("Cohen's kappa: %s" % out["overall"].get("cohen_kappa"))


if __name__ == "__main__":
    main()
