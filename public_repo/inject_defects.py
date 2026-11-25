#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
inject_defects.py —— 缺陷注入（每个模型 6 个缺陷，共 24 个）

五类缺陷（按评估方案 v2 §3.1）：
  D-OMISSION      需求遗漏：删除一个承载需求的元素/流
  D-CONTRADICTION 前后矛盾：把阈值改成与规格冲突的值
  D-CONDITION     条件错误：改比较算子（>= 改成 >）
  D-FLOW          数据流缺失：删除一条关键流
  D-AMBIGUOUS     歧义描述：把精确约束改成模糊词

输出：
  models/<folder>/MES_<mid>_<lv>_defective.json  —— 脏模型
  defect_manifest.json —— 缺陷清单（评审时知道植入了什么，但不给评审者看）
"""
import io, os, json, copy

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"
TARGETS = [
    ("M1", "M1_manual_human", "L0"),
    ("M3", "M3_AI_DFD", "L0"),
    ("M4", "M4_AI_UML", "L0"),
    ("M5", "M5_AI_StateMachine", "L1"),
]


def find_elem(doc, key):
    for e in doc["elements"]:
        if key.lower() in (str(e.get("id", "")) + " " + str(e.get("name", ""))).lower():
            return e
    return None


def inject(doc, mid):
    defects = []
    d = copy.deepcopy(doc)

    # 1. OMISSION：删掉一个元素（选中间位置的，避免太显眼）
    victim = d["elements"][min(3, len(d["elements"]) - 1)]
    vid = victim["id"]
    d["elements"] = [e for e in d["elements"] if e["id"] != vid]
    d["flows"] = [f for f in d["flows"]
                  if f.get("producer") != vid and f.get("consumer") != vid]
    defects.append({"id": "DEF-1", "type": "omission",
                    "description": "删除功能/状态 %s 及其相关流" % vid,
                    "expected": "评审者应报告该需求未被覆盖"})

    # 2. CONTRADICTION：把阈值改成与规格冲突的值（6.0 -> 2.0）
    txt = json.dumps(d, ensure_ascii=False)
    if "6.0" in txt:
        def repl(o):
            if isinstance(o, dict):
                return {k: repl(v) for k, v in o.items()}
            if isinstance(o, list):
                return [repl(v) for v in o]
            if isinstance(o, str):
                return o.replace("6.0", "2.0").replace("3.0 s", "0.5 s")
            return o
        d = repl(d)
        defects.append({"id": "DEF-2", "type": "contradiction",
                        "description": "紧急减速度 6.0 改为 2.0（违反 A-1）；风险阈值 3.0s 改为 0.5s",
                        "expected": "评审者应报告与需求规格冲突"})

    # 3. CONDITION：算子反转 >= -> >
    n_changed = 0
    def flip(o):
        nonlocal n_changed
        if isinstance(o, dict):
            return {k: flip(v) for k, v in o.items()}
        if isinstance(o, list):
            return [flip(v) for v in o]
        if isinstance(o, str):
            new = o.replace(">=", "==")
            if new != o:
                n_changed += 1
            return new
        return o
    d = flip(d)
    defects.append({"id": "DEF-3", "type": "condition",
                    "description": "把 %d 处 >= 条件改成 ==（边界语义错误）" % n_changed,
                    "expected": "评审者应报告条件错误"})

    # 4. FLOW：删一条关键流
    if d["flows"]:
        flow = d["flows"][len(d["flows"]) // 2]
        fname = flow.get("name", "?")
        d["flows"] = [f for f in d["flows"] if f is not flow]
        defects.append({"id": "DEF-4", "type": "flow",
                        "description": "删除数据流 %s（producer=%s consumer=%s）" %
                                       (fname, flow.get("producer"), flow.get("consumer")),
                        "expected": "评审者应报告接口/数据流缺失"})

    # 5. AMBIGUOUS：把 preconditions 改成模糊描述
    done = False
    for e in d["elements"]:
        if e.get("preconditions"):
            e["preconditions"] = ["输入应在适当时刻有效"]
            e["responsibility"] = "及时处理相关数据以提供合适输出"
            done = True
            break
    defects.append({"id": "DEF-5", "type": "ambiguous",
                    "description": "把一处精确前置条件改成模糊词（适当/及时/合适）" if done else "未找到可改的前置条件",
                    "expected": "评审者应报告歧义描述"})

    # 6. TRACEABILITY：删掉一半追溯条目
    tr = d.get("traceability", [])
    if tr:
        d["traceability"] = tr[:len(tr) // 2]
    defects.append({"id": "DEF-6", "type": "omission",
                    "description": "删除 %d 条追溯记录" % (len(tr) - len(tr) // 2) if tr else "无追溯可删",
                    "expected": "评审者应报告可追溯性缺失"})
    return d, defects


def main():
    manifest = []
    for mid, folder, lv in TARGETS:
        src = os.path.join(BASE, "models", folder, "MES_%s_%s.json" % (mid, lv))
        doc = json.load(io.open(src, encoding="utf-8-sig"))
        dirty, defects = inject(doc, mid)
        out = os.path.join(BASE, "models", folder, "MES_%s_%s_defective.json" % (mid, lv))
        io.open(out, "w", encoding="utf-8").write(json.dumps(dirty, indent=2, ensure_ascii=False))
        print("%s-%s: %d 缺陷 -> %s" % (mid, lv, len(defects), os.path.basename(out)))
        for x in defects:
            manifest.append({"model": mid, "level": lv, **x,
                             "file": out})
    io.open(os.path.join(BASE, "defect_manifest.json"), "w", encoding="utf-8").write(
        json.dumps(manifest, indent=2, ensure_ascii=False))
    print("总缺陷数:", len(manifest))


if __name__ == "__main__":
    main()
