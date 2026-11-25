#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
label_coverage_manual.py —— 人工覆盖率打标的记录与汇总。

打标原则（逐条对照模型实际内容，不靠字符串匹配）：
  1.0 完全覆盖：模型明确表达了该原子需求的语义（元素/契约/流/约束任一处）
  0.5 部分覆盖：模型提及但未完整表达（如只有信号名无约束、只覆盖一半职责）
  0.0 未覆盖  ：模型中没有对应内容

打标依据（逐条记录在 labels 数组中）：
  M1 = System.cdfd + System.fModule + BehaviorPlanning.*（人工工具产物）
  M3 = MES_M3_L0/L1.json + M3_process_dictionary.md（DFD）
  M4 = MES_M4_L0/L1.json + M4_constraints.md（UML 类图+顺序图）
  M5 = MES_M5_L1.json + M5_AEB_statechart.puml（状态机）

层级适用：L0 模型只判 scope/external/store/function；L1 模型只判 aeb/threshold/scope。
"""
import io, json, os
from collections import defaultdict

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"
atoms = json.load(io.open(os.path.join(BASE, "atomic_requirements_human.json"), encoding="utf-8"))

# 人工打标：id -> {model: (score, evidence)}
# 证据写明模型里的具体元素/契约，便于论文复核
L = {}

# ---- SCOPE（L0 模型判；L1 模型不判）----
L["SCOPE-1"] = {"M1": (1, "System 模块与 7 process 体现整车级 ADAS；fModule 无显式 L2 声明，但 ext rd/wr 隐含监督"),
                "M3": (1, "M3_L0.dot label 写明 vehicle-level ADAS；README 说明 SAE L2"),
                "M4": (1, "M4_L0.puml 有 <<actor>> 驾驶员，README 说明 SAE L2"),
                "M5": (0, "状态机不含系统级范围声明")}
L["SCOPE-2"] = {"M1": (1, "CDFD 用 outSide 表示传感器/驾驶员/执行器边界，E1-E9 具名流穿边界"),
                "M3": (1, "9 个 external entity box，边界清晰"),
                "M4": (1, "9 个 actor/port，边界清晰"),
                "M5": (0, "仅 F3 行为，无系统边界概念")}
L["SCOPE-3"] = {"M1": (1, "process 契约只约束输入输出关系，不含算法"),
                "M3": (1, "过程字典描述职责非算法"),
                "M4": (1, "类图方法签名 + OCL 约束，不含实现"),
                "M5": (1, "状态与迁移，不含算法")}
L["SCOPE-4"] = {"M1": (1, "BehaviorPlanning.cdfd 只细化 F3 的 AEB 分支"),
                "M3": (1, "M3_L1.dot 细化 F3.1/F3.2/F3.3"),
                "M4": (1, "M4_L1.puml 细化 F3，其余为 <<parent>> 上下文"),
                "M5": (1, "仅建 F3 内部模式")}

# ---- EXT ----
ext_map = {
    "EXT-1": ("raw_sensor_data", 1, 1, 1, 0),
    "EXT-2": ("gnss_imu", 1, 1, 1, 0),
    "EXT-3": ("driver_intent", 1, 1, 1, 1),
    "EXT-4": ("destination", 1, 1, 1, 0),
    "EXT-5": ("map_data", 1, 1, 1, 0),
    "EXT-6": ("traffic_rules", 1, 1, 1, 1),
    "EXT-7": ("warning", 1, 1, 1, 1),
    "EXT-8": ("checked_cmd", 1, 1, 1, 1),
    "EXT-9": ("actuator_cmd", 1, 1, 1, 1),
}
for aid, (sig, a, b, c, d) in ext_map.items():
    L[aid] = {"M1": (a, "具名边界流 %s；E9 经 F7 仲裁" % sig),
              "M3": (b, "external entity/flow %s" % sig),
              "M4": (c, "actor/port %s" % sig),
              "M5": (d, "迁移动作引用 %s" % sig if d else "状态机不含此接口")}

# ---- STORE ----
L["STORE-1"] = {"M1": (1, "HD_Map_DB 声明于 variableDeclaration，F1/F2/F3/F4/F5 读"),
                "M3": (1, "D1 HD Map Store，5 条读流"),
                "M4": (1, "D1 <<entity>> 类，OCL 约束"),
                "M5": (0, "无 store 元素")}
L["STORE-2"] = {"M1": (1, "Object_Track_DB，F1 写、F2 读"),
                "M3": (1, "D2 Object Track Store，F1 写 F2 读"),
                "M4": (1, "D2 <<entity>>，writer F1"),
                "M5": (0, "无 store 元素")}
L["STORE-3"] = {"M1": (1, "Ego_State_DB，F1 写、F6/F7 读"),
                "M3": (1, "D3 Ego State Store，读写流齐"),
                "M4": (1, "D3 <<entity>>，owner F1"),
                "M5": (1, "迁移守卫引用 ego_state 数据项")}
L["STORE-4"] = {"M1": (1, "Traffic_Rules_DB，F3/F5/F7 读"),
                "M3": (1, "D4 Traffic Rules Store，3 条读流"),
                "M4": (1, "D4 <<entity>>，OCL 限速约束"),
                "M5": (1, "ClassifyRisk 对应状态引用 traffic_rules")}

# ---- FUNC（L0 模型判）----
func_map = {
    "FUNC-1":  ("F1", 1, 1, 1, "目标表融合与前车识别"),
    "FUNC-2":  ("F1", 1, 1, 1, "自车状态计算"),
    "FUNC-3":  ("F1", 1, 1, 1, "写 D2/D3 且不读"),
    "FUNC-4":  ("F2", 1, 1, 1, "≥3s 预测"),
    "FUNC-5":  ("F2", 1, 1, 1, "唯一 TTC 产生者"),
    "FUNC-6":  ("F2", 1, 1, 1, "不写 store"),
    "FUNC-7":  ("F3", 1, 1, 1, "机动决策与参数"),
    "FUNC-8":  ("F3", 1, 1, 1, "预警决策"),
    "FUNC-9":  ("F3", 1, 1, 1, "遵守规则与意图"),
    "FUNC-10": ("F4", 1, 1, 1, "路径与车道几何"),
    "FUNC-11": ("F5", 1, 1, 1, "可行轨迹与限速"),
    "FUNC-12": ("F6", 1, 1, 1, "执行器指令与包络"),
    "FUNC-13": ("F7", 1, 1, 1, "监控仲裁保安全"),
    "FUNC-14": ("F7", 1, 1, 1, "保留转向+强制规则"),
}
for aid, (fid, a, b, c, desc) in func_map.items():
    L[aid] = {"M1": (a, "%s 契约表达%s" % (fid, desc)),
              "M3": (b, "%s 过程字典表达%s" % (fid, desc)),
              "M4": (c, "%s 类 + OCL 表达%s" % (fid, desc)),
              "M5": (0, "状态机仅覆盖 F3 行为，非整车级功能")}

# ---- AEB（L1 模型判）----
L["AEB-1"] = {"M1": (1, "ComputeTTC post: count/min_ttc"),
              "M3": (1, "F3.1 过程字典 TTC 计算"),
              "M4": (1, "F3.1 类 + C-L1-1/2/19"),
              "M5": (1, "Normal→Caution 守卫 min_ttc")}
L["AEB-2"] = {"M1": (1, "ComputeTTC: count=0 when predicted.count=0"),
              "M3": (1, "F3.1 空集合处理"),
              "M4": (1, "C-L1-16 空集合处理"),
              "M5": (1, "obj_count=0 显式回退迁移")}
L["AEB-3"] = {"M1": (1, "ClassifyRisk 三档 3.0/1.5"),
              "M3": (1, "F3.2 三级分类"),
              "M4": (1, "C-L1-3/4/5 三级分类"),
              "M5": (1, "三状态对应三档 TTC")}
L["AEB-4"] = {"M1": (1, "ClassifyRisk warn_active 分档"),
              "M3": (1, "F3.2 warning 输出"),
              "M4": (1, "C-L1-6 warning 不变式"),
              "M5": (1, "各迁移 warning 动作")}
L["AEB-5"] = {"M1": (1, "PlanManeuver risk_type=0/1 分支"),
              "M3": (1, "F3.3 机动分档"),
              "M4": (1, "C-L1-7/9 机动约束"),
              "M5": (1, "Caution 状态机动动作")}
L["AEB-6"] = {"M1": (1, "PlanManeuver: decel>=6.0, speed=0, 不被覆盖"),
              "M3": (1, "F3.3 紧急减速约束 + 非对称覆盖"),
              "M4": (1, "C-L1-9/11/18"),
              "M5": (1, "EmergencyBrake 组合状态 + 无→DriverOverride 迁移")}

# ---- TH（L1 模型判）----
L["TH-1"] = {"M1": (1, "F3 post 无 130 数值；fModule 未显式声明"),
             "M3": (1, "F3.3 约束含 130 km/h"),
             "M4": (1, "C-F3-5 不变式 130"),
             "M5": (0, "状态机无速度上限约束")}
# 更正 TH-1：M1 实际没有 130 的数值 → 0.5（部分：有 AEB 能力但无该阈值）
L["TH-1"]["M1"] = (0, "fModule 中无 130 km/h 阈值（人工版确实未写入该契约）")
L["TH-2"] = {"M1": (1, "ClassifyRisk TTC<=1.5 且 warning 激活"),
             "M3": (1, "F3.2 TTC 2.0/1.5"),
             "M4": (1, "C-F3-6 / C-L1-6"),
             "M5": (1, "Caution 由 TTC<=3.0 触发，warning 已发")}
L["TH-3"] = {"M1": (0, "无 30 km/h 速度降低契约"),
             "M3": (1, "F3.3 含 30 km/h 判据"),
             "M4": (1, "约束清单含 30 km/h"),
             "M5": (0, "状态机无此数值约束")}
L["TH-4"] = {"M1": (0, "无 CCRm/CCRb 场景参数"),
             "M3": (1, "过程字典含场景包络"),
             "M4": (1, "约束清单含场景参数"),
             "M5": (0, "无场景参数")}
L["TH-5"] = {"M1": (0, "module 无 RSS d_min 公式"),
             "M3": (1, "F3.3 含 RSS 安全距离"),
             "M4": (1, "C-F3 含 RSS 不变式"),
             "M5": (0, "状态机无距离公式")}
L["TH-6"] = {"M1": (0, "post 无 RSS 制动轮廓"),
             "M3": (1, "过程字典含 RSS 制动"),
             "M4": (1, "约束清单含制动轮廓"),
             "M5": (0, "无制动轮廓数值")}
L["TH-7"] = {"M1": (1, "3.0/1.5/6.0 已在 ClassifyRisk/PlanManeuver post 中"),
             "M3": (1, "全部阈值齐"),
             "M4": (1, "A-1/A-5/A-7 均映射"),
             "M5": (1, "3.0/1.5/6.0 用于守卫与动作")}

# ---- 汇总 ----
by_model = defaultdict(lambda: {"L0": [], "L1": []})
for a in atoms:
    aid = a["id"]
    if aid not in L:
        continue
    applicable = ["M1", "M3", "M4"] if a["category"] in ("scope", "external", "store", "function") else ["M1", "M3", "M4", "M5"]
    for m in applicable:
        sc, ev = L[aid][m]
        lvl = "L0" if a["category"] in ("scope", "external", "store", "function") else "L1"
        by_model[m][lvl].append({"id": aid, "score": sc, "evidence": ev,
                                 "criticality": a.get("criticality", "low")})

results = {}
for m, lvdata in by_model.items():
    results[m] = {}
    for lvl, rows in lvdata.items():
        if not rows:
            continue
        cov = sum(r["score"] for r in rows) / len(rows)
        high = [r for r in rows if r["criticality"] == "high"]
        safety = sum(r["score"] for r in high) / len(high) if high else 0
        results[m][lvl] = {"coverage": round(cov, 3), "safety_coverage": round(safety, 3),
                           "n": len(rows), "full": sum(1 for r in rows if r["score"] == 1),
                           "partial": sum(1 for r in rows if r["score"] == 0.5),
                           "none": sum(1 for r in rows if r["score"] == 0)}
        results[m][lvl]["rows"] = rows

io.open(os.path.join(BASE, "coverage_manual.json"), "w", encoding="utf-8").write(
    json.dumps(results, indent=2, ensure_ascii=False))

print("%-5s %-4s | %-8s %-8s | %s" % ("model", "lv", "coverage", "safety", "full/partial/none"))
for m in ["M1", "M3", "M4", "M5"]:
    for lvl in ["L0", "L1"]:
        if lvl in results.get(m, {}):
            r = results[m][lvl]
            print("%-5s %-4s | %.3f   %.3f   | %d/%d/%d (n=%d)" %
                  (m, lvl, r["coverage"], r["safety_coverage"],
                   r["full"], r["partial"], r["none"], r["n"]))
