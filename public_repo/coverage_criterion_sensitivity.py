#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
coverage_criterion_sensitivity.py —— 覆盖率标注口径的敏感性分析。

问题
----
论文的 I1（需求覆盖度）依赖人工语义判定。有一类判定存在口径空间：
「某阈值在规格中只是另一个阈值的推导依据（如 N-3 的 >30 km/h 冲击速度降低
与 N-4 的 CCRm 包络，在 §7 中都是 A-1 = 6.0 m/s² 的来源）」——
模型若写出了 A-1 的数值，是否就算「覆盖」了 N-3/N-4？

本脚本把三种口径下的 Level-1 I1 全部算出来，检验论文的核心排序是否依赖
这一选择：

  口径 A（论文采用）  N-3/N-4 可经 A-1 体现 → 记 1
  口径 B（宽松）      只有模型自身产物里直接出现 N-3/N-4 的数值或包络才记 1
  口径 C（严格）      N-3/N-4 必须写出独立契约才记 1，否则记 0

若三种口径下核心排序一致，则 I1 的结论不依赖该判定，第二标注者的作用
限于核对个别原子，而非支撑结论。

输出：coverage_criterion_sensitivity.json + 控制台对照表。
"""
import io
import json
import os
import re

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"
L1_MODELS = ["M1", "M1.1", "M2", "M3", "M4", "M5"]
CORE_ATOMS = ["TH-1", "TH-3", "TH-4", "TH-5", "TH-6"]

# 每个模型产物里是否出现 N-3/N-4 的数值或包络（口径 B 的依据）
MODEL_FILES = {
    "M1": ["models/M1_manual_human/System.fModule", "models/M1_manual_human/BehaviorPlanning.fModule",
           "models/M1_manual_human/MES_M1_L0.json", "models/M1_manual_human/MES_M1_L1.json"],
    "M1.1": ["models/M1_1_manual_plus_thresholds/System.fModule",
             "models/M1_1_manual_plus_thresholds/BehaviorPlanning.fModule",
             "models/M1_1_manual_plus_thresholds/MES_M1.1_L0.json",
             "models/M1_1_manual_plus_thresholds/MES_M1.1_L1.json"],
    "M2": ["models/M2_AI_SOFL_single/ADAS_System.fModule", "models/M2_AI_SOFL_single/AEB_Branch.fModule",
           "models/M2_AI_SOFL_single/README.md", "models/M2_AI_SOFL_single/MES_M2_L1.json"],
    "M3": ["models/M3_AI_DFD/M3_process_dictionary.md", "models/M3_AI_DFD/README.md",
           "models/M3_AI_DFD/MES_M3_L1.json"],
    "M4": ["models/M4_AI_UML/M4_L1.puml", "models/M4_AI_UML/M4_constraints.md",
           "models/M4_AI_UML/README.md", "models/M4_AI_UML/MES_M4_L1.json"],
    "M5": ["models/M5_AI_StateMachine/M5_AEB_statechart.puml", "models/M5_AI_StateMachine/MES_M5_L1.json"],
}
# 口径 B：产物里直接出现下列任一模式即视为覆盖 N-3/N-4
DIRECT_N3N4 = re.compile(r"N-3|N-4|CCRm|CCRb|30\s*km/h|30\.0|60.{0,3}130")
# 口径 C：模型自身必须写出独立契约（排除仅靠 A-1 数值）
HAS_INDEPENDENT_N3N4 = {"M1": False, "M1.1": False, "M2": False,
                         "M3": False, "M4": False, "M5": False}


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def main():
    cov_path = os.path.join(BASE, "coverage_manual.json")
    manual = load(cov_path)
    base = {}
    for m in L1_MODELS:
        base[m] = {r["id"]: r["score"] for r in manual[m]["L1"]["rows"]}

    # 口径 B：按产物扫描重判 TH-3 / TH-4
    direct = {}
    for m, files in MODEL_FILES.items():
        txt = ""
        for f in files:
            p = os.path.join(BASE, f.replace("/", os.sep))
            if os.path.exists(p):
                txt += io.open(p, encoding="utf-8", errors="replace").read()
        direct[m] = bool(DIRECT_N3N4.search(txt))

    def build(crit):
        sc = {}
        for m in L1_MODELS:
            sc[m] = dict(base[m])
            if crit == "B":
                for a in ("TH-3", "TH-4"):
                    if not direct[m]:
                        sc[m][a] = 0.0
            elif crit == "C":
                for a in ("TH-3", "TH-4"):
                    if not HAS_INDEPENDENT_N3N4[m]:
                        sc[m][a] = 0.0
        return {m: round(sum(v.values()) / len(v), 4) for m, v in sc.items()}

    res = {"primary": {m: round(sum(base[m].values()) / len(base[m]), 4) for m in L1_MODELS},
           "direct_n3n4_present": direct,
           "criteria": {}}

    print("=" * 92)
    print("覆盖率标注口径的敏感性分析（Level-1 I1）")
    print("=" * 92)
    print("口径 A（论文采用）：N-3/N-4 可经 A-1 体现")
    print("口径 B（宽松）    ：仅当模型产物中直接出现 N-3/N-4 数值或包络才记 1")
    print("口径 C（严格）    ：N-3/N-4 必须有独立契约，否则记 0")
    print()
    print(f"{'model':7s} {'A 主标注':>9s} {'B 宽松':>9s} {'C 严格':>9s}")
    for crit, name in (("A", "primary"), ("B", "B"), ("C", "C")):
        res["criteria"][name] = build(crit)
    for m in L1_MODELS:
        print("%-7s %9.3f %9.3f %9.3f" % (m, res["criteria"]["primary"][m],
                                            res["criteria"]["B"][m], res["criteria"]["C"][m]))

    print("\n核心排序是否依赖口径：")
    checks = []
    for name in ("primary", "B", "C"):
        c = res["criteria"][name]
        checks.append({
            "criterion": name,
            "M1_below_M1.1": c["M1"] < c["M1.1"],
            "M1.1_equals_M3_M4": c["M1.1"] == c["M3"] == c["M4"],
            "M1.1_above_M2": c["M1.1"] > c["M2"],
            "M1_and_M5_equal": c["M1"] == c["M5"],
        })
    for ch in checks:
        print("  [%s] M1<M1.1:%s  M1.1=M3=M4:%s  M1.1>M2:%s  M1=M5:%s"
              % (ch["criterion"], ch["M1_below_M1.1"], ch["M1.1_equals_M3_M4"],
                 ch["M1.1_above_M2"], ch["M1_and_M5_equal"]))
    stable = all(all(v for k, v in ch.items() if k != "criterion") for ch in checks)
    res["core_ordering_stable_across_criteria"] = stable
    print("\n=> 核心排序在三种口径下%s" % ("完全一致（结论不依赖该判定）✓" if stable
                                          else "存在变化（须在论文中披露）"))

    out = os.path.join(BASE, "coverage_criterion_sensitivity.json")
    io.open(out, "w", encoding="utf-8").write(json.dumps(res, indent=2, ensure_ascii=False))
    print("已写出 coverage_criterion_sensitivity.json")


if __name__ == "__main__":
    main()
