#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_annotator_workbook.py —— 生成可直接发给第二标注者的工作手册。

它解决的问题
------------
原工具包要让标注者在六个模型的原始产物里通读，判断"某条阈值需求有没有被覆盖"。
这既慢（每个模型几千行）又容易漏（漏看就错判为"未覆盖"）。

本脚本的做法：
  1. 对每个「阈值原子 × 模型」组合，按关键字自动摘出候选条款（pre/post/追溯说明）；
  2. 把候选条款整理成一张张"判定卡"，标注者只需看每张卡上的几行候选，
     判断"覆盖 / 部分覆盖 / 未覆盖"，并填一句证据；
  3. 判定卡里【不出现】主标注的答案，标注者看不到 primary_label。

用法
----
    python build_annotator_workbook.py
    # 产出：
    #   annotator_workbook.md         给标注者看的手册（Markdown，可直接读）
    #   annotator_form.json           给标注者填的表格（JSON）
    #   candidate_clauses.json        机器可读的候选条款（复核用）
"""
import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))

# 六模型 × 层级。标注取材范围与主标注一致：**L0 与 L1 合并**，
# 因为有些阈值（如 N-5 的 RSS 安全距离、TH-3/4 的场景包络）落在 L0 的
# Motion_Planning / Safety_Shield 上，而不在 L1 的 AEB 分支里。
MES_FILES = {
    "M1":   ["models/M1_manual_human/MES_M1_L0.json",
             "models/M1_manual_human/MES_M1_L1.json"],
    "M1.1": ["models/M1_1_manual_plus_thresholds/MES_M1.1_L0.json",
             "models/M1_1_manual_plus_thresholds/MES_M1.1_L1.json"],
    "M2":   ["models/M2_AI_SOFL_single/MES_M2_L0.json",
             "models/M2_AI_SOFL_single/MES_M2_L1.json"],
    "M3":   ["models/M3_AI_DFD/MES_M3_L0.json",
             "models/M3_AI_DFD/MES_M3_L1.json"],
    "M4":   ["models/M4_AI_UML/MES_M4_L0.json",
             "models/M4_AI_UML/MES_M4_L1.json"],
    "M5":   ["models/M5_AI_StateMachine/MES_M5_L1.json"],
}

# 对照集原子（8 条，在所有模型里都恒为覆盖）——同样必须给出候选条款。
# 否则标注者面对"候选条款：无"只能凭空判断，会系统性打低分，
# 使对照集一致率失去意义（它本来是用来检查"是否对某类模型一律给已覆盖"的）。
# 注意：这些条目只用于对照集取材，不参与判别力集卡片的生成。
CONTROL_SPEC = {
    "TH-2":  {"title": "前向碰撞预警须在 TTC=2.0 s 前发出",
              "source": "N-2",
              "keywords": [r"ttc", r"\b2\.0\b", r"fcw", r"warn", r"collision_?warning"]},
    "AEB-1": {"title": "F3.1 对每个预测目标计算 TTC，报告最小 TTC 与考虑的目标数量",
              "source": "F3.1",
              "keywords": [r"ttc", r"min_?ttc", r"obj_?count", r"target_?count",
                           r"ttc_?set", r"compute_?ttc", r"time_?to_?collision"]},
    "AEB-3": {"title": "F3.2 按最小 TTC 分三级：TTC>3.0s 无风险、1.5–3.0s 注意、≤1.5s 临界",
              "source": "F3.2 / A-5",
              "keywords": [r"risk_?level", r"classif", r"ttc", r"\b3\.0\b", r"\b1\.5\b",
                           r"\b2\b", r"critical", r"moderate", r"severe"]},
    "EXT-3": {"title": "E3 driver_intent：驾驶员指令与 ODD 状态、注意力状态输入",
              "source": "E3",
              "keywords": [r"driver_?intent", r"\bintent\b", r"attention", r"odd",
                           r"driver_?state", r"driver_?accel", r"handover"]},
    "EXT-5": {"title": "E5 map_data：当前位置高精地图路段（道路/车道/限速/曲率）输入",
              "source": "E5",
              "keywords": [r"map_?data", r"map", r"lane", r"curvature", r"posted_?speed",
                           r"road", r"geofence", r"hd_?map"]},
    "EXT-6": {"title": "E6 traffic_rules：当前适用交通规则（限速与信号灯状态）输入",
              "source": "E6",
              "keywords": [r"traffic_?rules?", r"speed_?limit", r"posted_?speed", r"signal",
                           r"traffic_?light", r"odr"]},
    "SCOPE-1": {"title": "系统为 SAE L2 级整车级 ADAS 车载系统，驾驶员持续监督",
                "source": "R-SCOPE-1",
                "keywords": [r"sae", r"\bl2\b", r"level_?2", r"supervis", r"driver",
                             r"odd", r"system_?scope", r"whole_?vehicle", r"vehicle_?level"]},
    "SCOPE-3": {"title": "规格约束功能分配与数据依赖，不约束功能内部算法",
                "source": "R-SCOPE-3",
                "keywords": [r"scope", r"allocat", r"data_?depend", r"dependency",
                             r"process_?alloc", r"decompos", r"partition"]},
}

# 各模型里"以文档而非契约"承载语义的文件 —— 标注者必须一并看，
# 因为主标注把文档性表述也算作覆盖（这正是 TH-3/TH-4 在 M3/M4 拿到满分的原因）。
DOC_SOURCES = {
    "M1":   [],
    "M1.1": [],
    "M2":   [],
    "M3":   ["models/M3_AI_DFD/M3_process_dictionary.md",
             "models/M3_AI_DFD/README.md"],
    "M4":   ["models/M4_AI_UML/M4_constraints.md"],
    "M5":   [],
}

# 模型的展示名与它的原始产物路径（标注者想看原件时用）
MODEL_INFO = {
    "M1":   ("M1 人工 SOFL（原始版）",      "models/M1_manual_human/BehaviorPlanning.fModule"),
    "M1.1": ("M1.1 人工 SOFL（补入阈值表）", "models/M1_1_manual_plus_thresholds/BehaviorPlanning.fModule"),
    "M2":   ("M2 LLM 生成 SOFL",            "models/M2_AI_SOFL_single/AEB_Branch.fModule"),
    "M3":   ("M3 LLM 生成 DFD",             "models/M3_AI_DFD/M3_process_dictionary.md"),
    "M4":   ("M4 LLM 生成 UML 类图/顺序图",  "models/M4_AI_UML/M4_L1.puml + M4_constraints.md"),
    "M5":   ("M5 LLM 生成 UML 状态机",       "models/M5_AI_StateMachine/M5_AEB_statechart.puml"),
}

# 五条有判别力的阈值原子 → 候选条款的关键字
# 关键字设计原则：覆盖"数值本身""单位换算""同义字段名""追溯说明"四种写法。
#
# 附：ELEMENTS —— 每条判别力原子的**要素分解**。
# 用途：把 1（覆盖）与 0.5（部分覆盖）的界线变成可机械执行的动作，
# 而不是让标注者凭语感判断"表达得够不够明确"。
# 要素划分**只来自规格原文**（N-1/N-3/N-4/N-5/N-6 与 A-2 参数集），
# 与任何标注结果无关，因此不含答案 —— 手册给出的是"考题的结构"，不是"标准答案"。
# 元素数经核对与主标注一致：TH-1/TH-3 单要素（二值判断），
# TH-4 三要素、TH-5 两要素、TH-6 两要素（可判 0.5 —— 主标注的 3 个 0.5 全落在这三条上）。
ELEMENTS = {
    "TH-1": ["AEB 能力的适用车速上限 **≥ 130 km/h**"
             "（即：模型写 `speed<=130.0` 即满足；写 `speed<=100.0` 则不满足）"],
    "TH-3": ["碰撞速度降低量 > 30 km/h"],
    "TH-4": ["CCRm 试验场景的 VUT 车速窗口 60–130 km/h",
             "CCRm 试验场景的目标初速 20 km/h",
             "CCRb 试验场景的目标减速度 −4 m/s²"],
    "TH-5": ["保持 RSS 纵向安全距离 d_min（作为可判定的约束写出，而非仅定性提及）",
             "采用集成方定义的 RSS 参数集（ρ = 0.1 s、a_max,accel = 2.0、"
             "a_max,brake = 4.0、a_min,brake = 4.0）"],
    "TH-6": ["危险持续期间的制动减速度下限 ≥ a_min,brake（= 4.0 m/s²）",
             "响应时间内的加速度上限 ≤ a_max,accel（= 2.0 m/s²）"],
}

# 各需求的"适用条件 / 排除条件"——**不计入要素**。
# 理由：这些是对要求适用范围的限定（限定得越窄，要求越弱），不是模型需要另行编码的断言。
# 模型把这些限定也编码进去反而是过度约束。
# 明确列出是为了防止标注者据此误判 0.5（例如 M1.1 的 TH-1 写的是 ego_state.speed<=130.0，
# 没有另写"静止目标除外"，但那不影响覆盖 —— 主标注也是判 1）。
NOT_ELEMENTS = {
    "TH-1": "「静止目标除外」是适用范围排除（规格原文：operational up to ... "
            "130 km/h, stationary targets excluded），不计入要素。模型未另行编码该排除，"
            "**不影响覆盖**，仍按 1 个要素判定。\n"
            "> ⚠️ **不等号方向**：本需求写的是「上限**至少** 130 km/h」，"
            "约束的是**上限本身**（要求上限 V ≥ 130）；而模型写 `ego_state.speed<=130.0`，"
            "是把上限**取成 130**。130 ≥ 130 成立，**因此模型写法正确，不要判 0.5**。\n"
            "> 只有两种情况算没写出来：模型写出的上限**小于** 130（如 `<=100.0`）——"
            "那会在 100–130 km/h 之间留下 AEB 不生效的空档；"
            "或模型写的是**严格**不等式 `<130.0`——那样恰好在 130 km/h 时能力不可用，"
            "不满足「至少 130」。",
    "TH-3": "「部分介入（type 3）」是适用情形，**不计入要素**。"
            "模型若用风险等级或机动类型来表达「部分介入」即可，不要求出现字面 type 3。",
}

ATOM_SPEC = {
    "TH-1": {
        "title": "AEB 工作车速上限至少 130 km/h（静止目标除外）",
        "source": "N-1",
        "keywords": [r"\b130\b", r"\b130\.0\b", r"km/h", r"kmh", r"speed_limit_upper",
                     r"max_?speed", r"v_max", r"upper_speed"],
    },
    "TH-3": {
        "title": "部分介入需将碰撞速度降低超过 30 km/h",
        "source": "N-3",
        "keywords": [r"\b30\b", r"\b30\.0\b", r"30\s*km", r"km/h", r"impact",
                     r"collision_speed", r"delta_?v", r"\bdv\b", r"speed_?reduction"],
    },
    "TH-4": {
        "title": "CCRm 测试包络 VUT 60–130 km/h、目标 20 km/h；CCRb 目标减速度 −4 m/s²",
        "source": "N-4",
        "keywords": [r"ccr", r"\benvelope\b", r"test_?scenario", r"\b60\b", r"\b110\b",
                     r"\b20\b", r"vut", r"target_?speed", r"scenario"],
    },
    "TH-5": {
        "title": "保持 RSS 纵向安全距离 d_min，采用集成方定义参数集",
        "source": "N-5 / A-2",
        "keywords": [r"d_?min", r"rss", r"safe_?distance", r"safe_?gap", r"min_?gap",
                     r"lead_?gap", r"longitudinal", r"following", r"\bgap\b"],
    },
    "TH-6": {
        "title": "危险持续期间至少以 a_min,brake 制动，响应时间内不超过 a_max,accel",
        "source": "N-6",
        "keywords": [r"a_?min", r"a_?max", r"brak", r"decel", r"accel",
                     r"\b4\.0\b", r"\b2\.0\b", r"braking_?profile", r"safe_?decel"],
    },
}

# 各模型里与阈值无关的噪声条款（用于排除纯泛用条款）
GENERIC = re.compile(
    r"^\s*(true|if true then)?\s*$"
    r"|count\s*>=\s*0"
    r"|min_ttc\s*>=\s*0"
    r"|speed\s*>=\s*0"
    r"|speed_limit\s*>=\s*0"
    r"|path_length\s*>=\s*0"
    r"|horizon\s*>=\s*0",
    re.I,
)

LEVEL_NOTE = {
    "M1":   "Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）",
    "M1.1": "Level-0 + Level-1，AEB 分支已补入阈值表",
    "M2":   "Level-0（ADAS_System）+ Level-1（AEB_Branch）",
    "M3":   "Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里",
    "M4":   "Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md",
    "M5":   "Level-1（AEB 状态机），约束写在状态迁移标签上",
}


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def clauses_of(mes):
    """把一个模型的 MES 摊平成 [(元素id, 位置, 文本)]。"""
    out = []
    for e in mes.get("elements", []):
        eid = e.get("id")
        for c in e.get("preconditions", []) or []:
            out.append((eid, "precondition", c))
        for pc in e.get("postconditions", []) or []:
            # 两种格式：字典 {guard, effect}（M3/M4/M5）或纯字符串（M1/M1.1/M2）
            if isinstance(pc, dict):
                g = pc.get("guard", "") or ""
                ef = pc.get("effect", "") or ""
            else:
                g, ef = "", str(pc)
            txt = ef if (not g or g.strip() == "true") else "%s -> %s" % (g, ef)
            out.append((eid, "postcondition", txt))
        for inv in e.get("invariants", []) or []:
            out.append((eid, "invariant", inv))
    # 注意：追溯表行不在这里产出 —— 由 trace_rows() 单独负责，
    # 否则同一条追溯行会被采集两次（一次作为普通条款、一次作为高优先级声明）。
    return out


def trace_rows(mes):
    """抽出追溯表行，并保留其 requirement 标签。

    追溯表是模型**自己**声明"我在哪一条实现了哪条规格条款"的地方，
    因此它是候选条款抽取里最可靠、且不含任何答案的信号：
    标注者看到 [N-4] 这一行，就等于看到了模型对该需求的自我声明。
    """
    out = []
    for tr in mes.get("traceability", []) or []:
        req = (tr.get("requirement") or "").strip()
        note = tr.get("note", "") or ""
        rb = tr.get("realised_by", "") or ""
        els = tr.get("elements", []) or []
        txt = "[%s] %s | 载体: %s | 元素: %s" % (req, note, rb, ", ".join(els))
        out.append((req, "traceability", txt))
    return out


def score_clause(text, spec):
    """返回命中强度：2=强（数值/字段直接对上），1=弱（语义相关），0=无。"""
    t = text.lower()
    hits = []
    for kw in spec["keywords"]:
        for m in re.finditer(kw, t, re.I):
            hits.append((kw, m.group(0)))
            break
    if not hits:
        return 0, []
    strong = [h for h in hits if h[0] not in (r"\bgap\b", r"\b60\b", r"\b20\b", r"\b30\b",
                                             r"brak", r"accel", r"decel", r"rss")]
    return (2 if strong else 1), hits


def doc_lines(mid, spec, parts=None):
    """从该模型的文档型产物里摘取候选行（带文件与行号）。

    命中来源条款编号（如 "| N-4 | F3.3 | CCRm envelope |"）的行优先级最高 ——
    这类行就是模型在文档表格里对该需求的显式声明。
    """
    parts = parts or []
    out = []
    for rel in DOC_SOURCES.get(mid, []):
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        try:
            txt = io.open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for i, line in enumerate(txt.splitlines(), 1):
            s = line.strip()
            if not s or len(s) > 400:
                continue
            hit_tag = None
            for p in parts:
                if re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(p), s):
                    hit_tag = p
                    break
            sc, hits = score_clause(s, spec)
            if hit_tag:
                prio = 3
            elif sc >= 1:
                prio = 2 if sc == 2 else 1
            else:
                continue
            out.append({"element": os.path.basename(rel),
                        "where": "文档 L%d" % i,
                        "text": s,
                        "priority": prio,
                        "src": "DOC:%s" % os.path.basename(rel),
                        "matched": [h[0] for h in hits]})
    return out


def collect_candidates(aid, mid, spec, atom):
    """收集「某原子 × 某模型」的候选条款。

    优先级：
      3 = 模型自己声明实现了该来源条款（追溯表标签 / 文档表格行）—— 最可靠
      2 = 关键字强命中（数值或字段名直接对上）
      1 = 关键字弱命中（语义相关但无具体数值）
    """
    parts = [p.strip() for p in re.split(r"[/,]", (atom or {}).get("source_clause", ""))
             if p.strip()]
    cands, seen = [], set()
    for rel in MES_FILES.get(mid, []):
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        mes = load(path)
        lvl = "L0" if rel.endswith("_L0.json") else "L1"
        # --- 契约条款（pre / post / invariant）---
        for eid, where, txt in clauses_of(mes):
            if not txt or GENERIC.search(txt):
                continue
            s, hits = score_clause(txt, spec)
            if s < 1:
                continue
            key = (eid, where, txt)
            if key in seen:
                continue
            seen.add(key)
            cands.append({"element": "%s@%s" % (eid, lvl), "where": where, "text": txt,
                          "priority": 2 if s == 2 else 1,
                          "src": "%s@%s" % (eid, lvl),
                          "matched": [h[0] for h in hits]})
        # --- 追溯表行 ---
        for req, where, txt in trace_rows(mes):
            key = ("tr", lvl, req, txt)
            if key in seen:
                continue
            if req in parts:
                prio = 3
            else:
                s, hits = score_clause(txt, spec)
                if s < 1:
                    continue
                prio = 2 if s == 2 else 1
            seen.add(key)
            cands.append({"element": "traceability@%s" % lvl, "where": where, "text": txt,
                          "priority": prio, "src": "TR:%s@%s" % (req, lvl), "matched": []})
    # --- 文档型产物 ---
    for c in doc_lines(mid, spec, parts):
        key = (c["element"], c["where"], c["text"])
        if key in seen:
            continue
        seen.add(key)
        cands.append(c)
    return cands


def decomposition_rows(mid, limit=8):
    """列出模型的元素分解（元素 id + 其首个前置条件）。

    用途：像 SCOPE-3「规格约束功能分配与数据依赖」这类需求，
    在模型里不体现为某条文字条款，而是体现为"分解成哪些元素、元素之间怎么传数据"。
    没有这一兜底，对照集里会出现"候选条款：无"的空卡，迫使标注者凭空打 0 分，
    反而污染对照集的一致率。
    """
    out = []
    for rel in MES_FILES.get(mid, []):
        if not rel.endswith("_L0.json"):
            continue
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        mes = load(path)
        for e in mes.get("elements", []):
            pres = e.get("preconditions", []) or []
            pres = [p for p in pres if isinstance(p, str) and p.strip()]
            if pres:
                out.append({"element": "%s@L0" % e.get("id"), "where": "decomposition",
                            "text": pres[0], "priority": 1,
                            "src": "DECOMP:%s" % e.get("id"), "matched": []})
            if len(out) >= limit:
                return out
    return out


def allocate(cands, max_total=16, per_src=2):
    """挑选最终展示的候选条款。

    关键：不能简单取"命中最强的前 N 条"—— 否则某个高频元素（如 F5/F6 的
    舒适性上限）会把名额占满，而真正承载该需求的**文档表格行**被挤掉。
    做法：按优先级排序，每个来源（元素 id / 追溯标签 / 文档文件）最多取 per_src 条，
    先满足高优先级，再回填剩余名额。
    """
    cands = sorted(cands, key=lambda c: (-c["priority"], c["where"], c["text"]))
    chosen, cnt, used = [], {}, set()
    for c in cands:
        if len(chosen) >= max_total:
            break
        if cnt.get(c["src"], 0) >= per_src:
            continue
        cnt[c["src"]] = cnt.get(c["src"], 0) + 1
        used.add(id(c))
        chosen.append(c)
    for c in cands:
        if len(chosen) >= max_total:
            break
        if id(c) in used:
            continue
        used.add(id(c))
        chosen.append(c)
    return chosen


def build():
    atoms = load(os.path.join(ROOT, "atomic_requirements_human.json"))
    atom_by_id = {a["id"]: a for a in atoms}
    manual = load(os.path.join(ROOT, "coverage_manual.json"))

    # 候选条款 + 判定卡数据
    candidates = {}
    cards = []

    def primary_label(mid, aid):
        for lv in ("L1", "L0"):
            for r in manual.get(mid, {}).get(lv, {}).get("rows", []):
                if r["id"] == aid:
                    return r["score"]
        return None

    def make_card(aid, mid, spec, setname):
        keep = allocate(collect_candidates(aid, mid, spec, atom_by_id.get(aid, {})))
        # 兜底：对照集里若仍无候选（需求靠元素分解而非文字条款体现），
        # 给出元素分解清单，让标注者有依据判断，而不是凭空打 0。
        if not keep and setname == "control":
            keep = decomposition_rows(mid)
        candidates["%s|%s" % (aid, mid)] = keep
        # 主标注仅用于本脚本自检，不写进给标注者的产物
        return {"atom_id": aid, "model": mid, "candidates": keep,
                "primary_label": primary_label(mid, aid), "set": setname}

    # ---- 判别力集：5 条阈值原子 × 6 模型 = 30 张卡（必做）----
    for aid, spec in ATOM_SPEC.items():
        for mid in MES_FILES:
            cards.append(make_card(aid, mid, spec, "discriminating"))

    # ---- 对照集：8 条恒为覆盖的原子 × 3 模型 = 24 张卡（可选）----
    # 抽样沿用 make_discriminating_sample.py 的种子结果，保证与 κ 脚本口径一致。
    tpl_path = os.path.join(BASE, "labelling_template_discriminating.json")
    if os.path.exists(tpl_path):
        tpl = load(tpl_path)
        for r in tpl["rows"]:
            if r.get("set") != "control":
                continue
            aid, mid = r["atom_id"], r["model"]
            spec = CONTROL_SPEC.get(aid, {"keywords": []})
            cards.append(make_card(aid, mid, spec, "control"))

    # ---------- 给标注者的 Markdown 手册 ----------
    L = []
    A = L.append
    A("# 需求覆盖度第二标注工作手册\n")
    A("> 这份手册要你做的事只有一件：**判断若干条需求，在某个模型里有没有被写到**。")
    A("> 全程约 30–45 分钟。判断依据全部写在下面的候选条款里，你不需要通读模型全文。\n")

    A("## 一、你要做什么\n")
    A("每个任务是一对「需求 + 模型」。你打开模型里与该需求相关的条款（手册已经替你摘出来了），")
    A("然后判断它算不算覆盖了这条需求，给出三个分数之一：\n")
    A("| 分数 | 含义 | 判断标准 |")
    A("|---|---|---|")
    A("| **1** | 覆盖 | 这条需求的**每一个要素**都被模型条款明确写出 |")
    A("| **0.5** | 部分覆盖 | 模型触及了这条需求，但**至少有一个要素没写出来** |")
    A("| **0** | 未覆盖 | 模型里找不到对应语义 |")
    A("")
    A("**关键判断规则（重要）**：一条需求如果是由另一条需求推导出来的，")
    A("那么当模型只写出了那个推导结果、没写推导依据时，")
    A("**算「1」（覆盖）**，只要这个推导关系在该模型里有说明（追溯表、注释、文档里写过\"由 X 推导\"即可）。")
    A("如果没有说明，就按「0.5」或「0」处理。")
    A("")
    A("> 这条规则是本次标注的核心分歧点，也是我们最想知道你判断的地方。")
    A("> 遇到拿不准的，按你第一反应的读法填，并在 evidence 里写明你的理由。\n")
    A("**第二条规则（同样重要）**：每条需求都给了它在规格里的**来源条款编号**"
      "（如 `N-4`、`F3.1`、`R-SCOPE-1`）。")
    A("候选条款里凡是带这个编号的行 —— 追溯表里的 `[N-4] …`、"
      "文档表格里的 `| N-4 | … |` —— 都是**模型自己声明\"我实现了这条需求\"**。")
    A("看到这类行时，请把它当作强证据；但也要核对它下面的载体条款是否真的写出了该需求的语义。\n")
    A("**第三条规则：1 与 0.5 的界线 —— 要素分解测试**\n")
    A("「明确写出」与「部分写出」的分界不是语气强弱，而是**这条需求的要素有没有被写全**。")
    A("每条需求下面都列出了它的要素（要素划分来自规格原文，与任何标注结果无关）。")
    A("把要素逐个对到模型条款上：\n")
    A("| 情形 | 分数 |")
    A("|---|---|")
    A("| 每个要素都在条款里被写出 | **1** |")
    A("| 模型触及了这条需求，但至少有一个要素没写出来 | **0.5** |")
    A("| 一个要素都没写出来 | **0** |")
    A("")
    A("「被写出」包含两种情形，**都算写出**：")
    A("1. 数值/条件直接出现在契约里；")
    A("2. 数值/条件出现在追溯表或文档里，且追溯说明写清了它与本需求的对应关系。\n")
    A("「没写出来」有三种典型形态，**都要判 0.5、不判 1**：")
    A("- **只有信号名、没有约束** —— 提到了这个量，但没把它写成契约"
      "（例如只写\"保持最小间距\"却无 d_min 表达式）；")
    A("- **只覆盖一半职责** —— 复合需求里只写了一部分"
      "（例如写了制动下限、没写响应时间上限）；")
    A("- **要素落在别处** —— 本分支的条款里没有，由父模块或相邻元素实现。\n")
    A("> **规则一优先于规则三**：若某个要素可由推导覆盖、且推导关系有说明，")
    A("> 该要素即视为\"已写出\"；规则三只用来判断**要素是否齐全**。\n")
    A("**适用条件与排除条件不计入要素。** 需求里\"在……情形下\"\"（……除外）\"这类措辞，")
    A("是对要求**适用范围的限定**，不是模型需要另行编码的断言 —— 限定越窄，要求越弱。")
    A("模型把这些限定也编码进去反而是过度约束。个别需求的具体说明列在该需求下方。\n")

    A("## 二、评分怎么写\n")
    A("- `label`：填 `1`、`0.5` 或 `0`")
    A("- `evidence`：一句话，指出你依据哪个元素、哪条条款，以及是怎么对应的。")
    A("  例如：`C-F3-4 postcondition 写了 decel_req>=6.0，与 N-3 的 30 km/h 经 A-1 推导对应`")
    A("- 拿不准的照实填，不必迎合任何\"标准答案\"——我们要的是你的独立判断。\n")

    A("## 三、纪律要求\n")
    A("- **不要**去查论文正文、结论表或任何标注结果文件。")
    A("- 提问请在开始前一次性问完（规格里的缩写、术语含义等），标注过程中不要再逐条问。")
    A("- 材料里如果出现你觉得矛盾或说不通的地方，照实记下来，这本身也是有用的信息。\n")

    A("## 四、模型材料对照表\n")
    A("每张判定卡下面都附了候选条款。如果候选明显不相关、而你怀疑模型里其实有相关内容，")
    A("可以翻看原始产物：\n")
    A("| 模型 | 是什么 | 原始产物 |")
    A("|---|---|---|")
    for mid in MES_FILES:
        name, rel = MODEL_INFO[mid]
        A("| `%s` | %s | `%s` |" % (mid, name, rel))
    A("")

    # 判定卡
    n_disc = sum(1 for c in cards if c["set"] == "discriminating")
    n_ctrl = len(cards) - n_disc
    A("## 五、判定卡\n")
    A("共 %d 张卡：**必做 %d 张**（第一部分，承载全部有争议的判断）；"
      "**可选 %d 张**（第二部分，对照集，用于检查你是不是对某类模型一律给\"已覆盖\"）。\n"
      "时间紧就只做必做部分。\n" % (len(cards), n_disc, n_ctrl))

    cur_atom = None
    for c in cards:
        aid, mid = c["atom_id"], c["model"]
        if aid != cur_atom:
            cur_atom = aid
            spec = ATOM_SPEC.get(aid) or CONTROL_SPEC.get(aid)
            if spec:
                A("### 需求 %s —— %s\n" % (aid, spec["title"]))
                A("来源条款：%s\n" % spec["source"])
            else:
                A("### 需求 %s（对照集条目，用于检查判断偏差）\n" % aid)
                atom_txt = atom_by_id.get(aid, {}).get("text", "")
                A("需求原文：%s\n" % atom_txt)
            src_clause = atom_by_id.get(aid, {}).get("source_clause", "")
            if src_clause:
                A("规格来源条款编号：`%s`（模型若在追溯表或文档表格里标注了这个编号，"
                  "说明它自称实现了该条款 —— 请一并考虑）\n" % src_clause)
            els = ELEMENTS.get(aid)
            if els:
                A("**本需求的要素分解**（%d 个要素，来自规格原文；"
                  "请把每个要素逐个对到模型条款上）：\n" % len(els))
                for i, e in enumerate(els):
                    A("- 要素 %s：%s" % (chr(ord("a") + i), e))
                A("")
                ne = NOT_ELEMENTS.get(aid)
                if ne:
                    A("> %s\n" % ne)
                A("→ %d 个要素全部写出 = `1`；写出一部分 = `0.5`；一个都没写出 = `0`\n" % len(els))
            else:
                A("（对照集条目）该需求按**整体**判定：模型里有条款表达其语义 → `1`；"
                  "完全没有 → `0`。\n")
        name, rel = MODEL_INFO[mid]
        tag = "（可选）" if c["set"] == "control" else ""
        A("#### 卡 %s × %s — %s%s\n" % (aid, mid, name, tag))
        A("*%s*\n" % LEVEL_NOTE[mid])
        cands = c["candidates"]
        if not cands:
            A("> **候选条款：无。** 该模型中未检索到与本需求相关的条款。")
            A("> 若你认为漏检，请翻看原始产物 `%s`。\n" % rel)
        else:
            A("候选条款（按相关度排序，请逐条看）：\n")
            for cc in cands:
                A("- `%s` [%s] %s" % (cc["element"], cc["where"], cc["text"]))
            A("")
        A("→ **label** = `___`    **evidence** = ________________________\n")
    wb = "\n".join(L)

    # ---------- 给标注者的 JSON 表单（不含答案） ----------
    # 判别力集 30 个判断（必做）+ 对照集 24 个判断（可选，用于查系统性偏差）
    form = {
        "_readme": (
            "填 label（1 / 0.5 / 0）与 evidence（一句话）。本文件不含任何参考答案。\n"
            "set=discriminating 的行是必做的（30 个）；set=control 的行是可选的（24 个），"
            "用于检查是否存在系统性偏差，若时间紧可整组留空。"),
        "rows": [{"atom_id": c["atom_id"], "model": c["model"], "level": "L1",
                  "set": c["set"], "label": "", "evidence": ""} for c in cards],
    }

    io.open(os.path.join(BASE, "annotator_workbook.md"), "w", encoding="utf-8").write(wb)
    io.open(os.path.join(BASE, "annotator_form.json"), "w", encoding="utf-8").write(
        json.dumps(form, indent=2, ensure_ascii=False))
    io.open(os.path.join(BASE, "candidate_clauses.json"), "w", encoding="utf-8").write(
        json.dumps(candidates, indent=2, ensure_ascii=False))

    # ---------- 自检：候选摘录是否足以让标注者独立判断 ----------
    print("已生成 annotator_workbook.md / annotator_form.json / candidate_clauses.json")
    print("判定卡 %d 张" % len(cards))
    print()

    n1 = sum(1 for c in cards if c["primary_label"] == 1)
    miss = [c for c in cards if c["primary_label"] == 1 and not c["candidates"]]
    print("自检 1：主标注=1 的卡片是否给出了候选")
    for c in miss:
        print("  !! %s x %s 主标注=1 但候选为空" % (c["atom_id"], c["model"]))
    print("  候选为空的「主标注=1」卡片：%d / %d" % (len(miss), n1))

    # 自检 2：主标注=1 的卡片里，是否至少有一条候选直接命中来源条款编号
    # （模型自称实现了该条款）。这条是"只看判定卡就能判断"的关键保证。
    weak = []
    for c in cards:
        if c["primary_label"] != 1:
            continue
        if not any(cc.get("priority") == 3 for cc in c["candidates"]):
            weak.append(c)
    print()
    print("自检 2：主标注=1 的卡片里是否存在「模型显式声明实现该条款」的候选")
    for c in weak:
        print("  ~  %s x %s 无 priority-3 候选（仅靠关键字推断）" % (c["atom_id"], c["model"]))
    print("  缺少 priority-3 候选的卡片：%d / %d" % (len(weak), n1))

    # 自检 3：文档型载体是否被截断挤掉（TH-3/TH-4 在 M3/M4 靠文档拿满分）
    print()
    print("自检 3：候选中是否仍含文档型载体")
    lost = []
    for c in cards:
        if c["primary_label"] != 1:
            continue
        has_doc = any(cc["where"].startswith("文档") for cc in c["candidates"])
        src = atom_by_id.get(c["atom_id"], {}).get("source_clause", "")
        parts = [p.strip() for p in re.split(r"[/,]", src) if p.strip()]
        need_doc = any(cc["where"].startswith("文档") and
                       any(p in cc["text"] for p in parts) for cc in c["candidates"])
        if not has_doc and need_doc:
            lost.append(c)
    print("  文档型实现被挤掉的「主标注=1」卡片：%d" % len(lost))
    for c in lost:
        print("    !! %s x %s" % (c["atom_id"], c["model"]))

    print()
    print("候选条数分布：")
    for aid in list(ATOM_SPEC) + list(CONTROL_SPEC):
        row = []
        for mid in MES_FILES:
            k = "%s|%s" % (aid, mid)
            if k in candidates:
                row.append("%s:%d" % (mid, len(candidates[k])))
        print("  %-8s %s" % (aid, "  ".join(row)))


if __name__ == "__main__":
    build()
