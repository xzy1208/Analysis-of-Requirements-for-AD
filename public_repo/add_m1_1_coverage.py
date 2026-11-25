#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
add_m1_1_coverage.py —— 为 M1.1（人工 SOFL 模型 + 阈值表补入）补写人工覆盖标注。

M1.1 = models/M1_1_manual_plus_thresholds/ 下的 SOFL 工具产物，由 M1 的
System.cdfd/System.fModule/BehaviorPlanning.cdfd/BehaviorPlanning.fModule
派生：Level-0 架构与端口不变，Level-1 与 Level-0 的 pre/post 契约补入
§7 规范阈值（N-1…N-7）与 §8 假设（A-1…A-7）所要求的约束。

打标口径与既有 M1/M3/M4 完全一致（label_coverage_manual.py 的原则）：
  1.0 完全覆盖 —— 模型明确表达该原子需求的语义（元素/契约/流/约束任一处）
  0.5 部分覆盖 —— 模型提及但未完整表达
  0.0 未覆盖  —— 模型中没有对应内容

其中 N-3（>30 km/h 冲击速度降低）与 N-4（CCRm 测试包络）按与 M3/M4 相同的
口径判定为"经 A-1 体现"：二者在规格 §7 中是 A-1 = 6.0 m/s² 的推导依据，
M3 与 M4 同样未把 §7 的推导中间量写成约束值，只在阈值追溯表中记录。

本脚本只写入 coverage_manual.json 的 "M1.1" 条目，不改动 M1–M5 的既有条目。
"""
import io
import json
import os

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"
COV = os.path.join(BASE, "coverage_manual.json")

# ---- M1.1 的 Level-1 逐条标注（13 条：6 条 AEB + 7 条阈值） ----------------
L1_ROWS = [
    ("AEB-1", 1, "ComputeTTC post: ttc_values.min_ttc>=0，且 count 与 min_ttc 逐对象计算",
     "high"),
    ("AEB-2", 1, "ComputeTTC post: predicted_trajectories.count=0 => ttc_values.count=0",
     "medium"),
    ("AEB-3", 1, "ClassifyRisk post 三档：min_ttc>3.0 / <=3.0 and >1.5 / <=1.5 → risk_type=0/1/2",
     "high"),
    ("AEB-4", 1, "ClassifyRisk post: warn_active=0（no risk）、warn_active=1（caution 与 critical）",
     "high"),
    ("AEB-5", 1, "PlanManeuver post: risk_type=0 → maneuver_type=1（cruise）、risk_type=1 → maneuver_type=2（减速）",
     "high"),
    ("AEB-6", 1, "PlanManeuver post: risk_type=2 → decel_req>=6.0 且 target_speed=0；"
                 "driver_intent.intent_type=2 且 risk_type<2 时才转 cruise，紧急减速不可被驾驶员加速请求覆盖",
     "high"),
    ("TH-1", 1, "PlanManeuver pre 新增 ego_state.speed<=130.0（N-1：AEB 能力可用至 130 km/h）",
     "high"),
    ("TH-2", 1, "ClassifyRisk post: min_ttc<=1.5 → warning.warn_active=1；caution 档（1.5<min_ttc<=3.0）亦置位，"
                "故 TTC=2.0 s 时预警已发出（N-2）",
     "high"),
    ("TH-3", 1, "经 A-1 体现：PlanManeuver post decel_req>=6.0；M1.1 追溯表 N-3 行记录 >30 km/h 冲击速度降低，"
                "§7 推导中间量不写入约束值（与 M3、M4 同口径）",
     "high"),
    ("TH-4", 1, "经 A-1 体现：PlanManeuver post decel_req>=6.0；M1.1 追溯表 N-4 行记录 CCRm 包络为 A-1 的推导前提，"
                "不作为约束值（与 M3、M4 同口径）",
     "high"),
    ("TH-5", 1, "Motion_Planning post: trajectory.min_gap<=predicted_trajectories.lead_gap；"
                "Prediction post 产出 predicted_trajectories.lead_gap>=0（N-5：RSS 纵向安全距离 d_min，A-2 参数）",
     "high"),
    ("TH-6", 1, "Motion_Planning post: trajectory.decel_limit>=4.0；Control post: brake_cmd>=decel_limit 且 "
                "accel_cmd<=2.0；Safety_Shield post: brake_cmd>=4.0、accel_cmd<=2.0"
                "（N-6：RSS 制动轮廓 a_min,brake=4.0、a_max,accel=2.0）",
     "high"),
    ("TH-7", 1, "A-1: PlanManeuver post decel_req>=6.0；A-5: ClassifyRisk post 阈值 3.0/1.5；"
                "A-7: Prediction/Motion_Planning 的 3.0 s 预测视界",
     "high"),
]


def main():
    cov = json.load(io.open(COV, encoding="utf-8"))
    m1 = cov["M1"]

    # ---- Level-0：M1.1 的架构与端口与 M1 完全同构，仅契约内容增加 ----
    l0_rows = []
    for r in m1["L0"]["rows"]:
        nr = dict(r)
        if r["id"] in ("STORE-2", "STORE-3", "STORE-4", "FUNC-1", "FUNC-5", "FUNC-6", "FUNC-7"):
            nr["evidence"] = r["evidence"] + "（M1.1 在同一架构上补入阈值契约，结构与端口不变）"
        l0_rows.append(nr)

    # ---- Level-1：逐条新标注 ----
    l1_rows = [{"id": i, "score": s, "evidence": e, "criticality": c}
               for i, s, e, c in L1_ROWS]

    def agg(rows):
        n = len(rows)
        full = sum(1 for r in rows if r["score"] == 1)
        part = sum(1 for r in rows if r["score"] == 0.5)
        none = sum(1 for r in rows if r["score"] == 0)
        covv = sum(r["score"] for r in rows) / n
        hi = [r for r in rows if r.get("criticality") == "high"]
        safety = sum(r["score"] for r in hi) / len(hi) if hi else 0.0
        return {"coverage": round(covv, 4), "safety_coverage": round(safety, 4),
                "n": n, "full": full, "partial": part, "none": none, "rows": rows}

    cov["M1.1"] = {"L0": agg(l0_rows), "L1": agg(l1_rows)}
    io.open(COV, "w", encoding="utf-8").write(
        json.dumps(cov, indent=2, ensure_ascii=False))

    print("M1.1 覆盖标注已写入 coverage_manual.json")
    for lvl in ("L0", "L1"):
        b = cov["M1.1"][lvl]
        print("  %s: coverage=%.3f safety=%.3f n=%d full=%d partial=%d none=%d"
              % (lvl, b["coverage"], b["safety_coverage"], b["n"],
                 b["full"], b["partial"], b["none"]))


if __name__ == "__main__":
    main()
