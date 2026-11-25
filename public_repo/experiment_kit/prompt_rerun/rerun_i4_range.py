# -*- coding: utf-8 -*-
"""对所有 SOFL 重跑计算 I4（L0/L1），得到同条件下的运行间区间。

用途（审稿意见第二部分第 1 条）：
    B3 与 B4 是同一模型、同一提示词的两次运行，空洞率 25.2% vs 2.5%、
    有效前置条件 1/10 vs 10/10。M2（50.3%）只是该分布中的一次抽样。
    本脚本给出 MiniMax 无禁令条件下的 I4 区间，判断 M2-vs-M4 的差距
    是否落在运行间波动之内。

口径与 Table IV 完全一致：
    - 前置条件组有效 = 至少一条子句的 tier 不属于 {T1,T2a,T2b,T3}
    - 实质子句 = tier == "T4"
    - I4 = 0.4 * 有有效前置条件 + 0.3 * 有量化约束 + 0.3 * (1 - 歧义词比率)
      量化与歧义两项对同一生成器不同次运行是常量，故本脚本只报出
      0.4 * 有效前置条件比例 这一项（记作 I4_pre），
      完整 I4 由 score_models_v2.py 在主模型上给出。

用法：python experiment_kit/prompt_rerun/rerun_i4_range.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_kit" / "prompt_rerun"))

from analyze_rerun import from_fmodule, parse_contracts, collect_types  # noqa: E402
from precondition_tiers import tier  # noqa: E402

# 无实质内容的 tier
NON_SUBSTANTIVE = {"T1", "T2a", "T2b", "T3"}

RERUNS = [
    ("B3", "MiniMax", "no ban (current prompt)", "outputs/B3_minimax_no_ban_current.md"),
    ("B4", "MiniMax", "no ban (current prompt)", "outputs/B4_minimax_no_ban_current.md"),
    ("A1", "MiniMax", "single-idiom ban", "outputs/A1_minimax_prohibited.md"),
    ("A2", "MiniMax", "single-idiom ban", "outputs/A2_minimax_prohibited.md"),
    ("D1", "MiniMax", "family-wide ban", "outputs/D1_minimax_family_ban.md"),
    ("B1", "Hunyuan", "no ban", "outputs/B1_hunyuan_unprohibited.md"),
    ("B2", "Hunyuan", "no ban", "outputs/B2_hunyuan_unprohibited.md"),
    ("C1", "Hunyuan", "single-idiom ban", "outputs/C1_hunyuan_prohibited.md"),
    ("D2", "Hunyuan", "family-wide ban", "outputs/D2_hunyuan_family_ban.md"),
]

M2_MODULES = [
    ("L0", ROOT / "models" / "M2_AI_SOFL_single" / "ADAS_System.fModule"),
    ("L1", ROOT / "models" / "M2_AI_SOFL_single" / "AEB_Branch.fModule"),
]


def split_clauses(text):
    return [c.strip() for c in re.split(r"\s+and\s+", text) if c.strip()]


def measure(code, types):
    """返回 (前置条件组数, 有效组数, 子句总数, 实质子句数)。"""
    groups = 0
    eff_groups = 0
    clauses_total = 0
    subst_clauses = 0
    for _name, _mod, pres, _posts in parse_contracts(code):
        for p in pres:
            groups += 1
            cl = split_clauses(p)
            clauses_total += len(cl)
            subst_here = 0
            for c in cl:
                t = tier(c, types)
                if t and t[0] == "T4":
                    subst_here += 1
            subst_clauses += subst_here
            if subst_here > 0:
                eff_groups += 1
    return groups, eff_groups, clauses_total, subst_clauses


def _extract_process_blocks(txt):
    """从整篇文本抽出 (level_hint, module_text) 列表。

    重跑输出的代码块结构与 process 结束标记不统一：
      - B3/B4 等：process 块以 `end_process` 结束；
      - 部分输出：没有 end_process，块在下一个 `process` 开头处结束。
    因此按"process 起点"切分，块的终点取 end_process 或下一个 process 起点，
    取二者中较早者。

    另外代码块结构也不统一（整模块一块 / module head、类型、store、process
    分成多块），故不能按代码块切分。
    """
    starts = [m.start() for m in re.finditer(r"^\s*process\s+[\w.]+\s*\(", txt, re.M)]
    segs = []
    for i, s in enumerate(starts):
        # 块的终点：下一个 process 起点；若中间有 end_process，用 end_process
        # 作为该 process 的真正结束，但 end_process 之后到下一个 process
        # 之间的内容（如尾部注释）不属于任何 process。
        e_next = starts[i + 1] if i + 1 < len(starts) else len(txt)
        e_end = txt.find("end_process", s)
        if e_end > 0:
            e_end += len("end_process")
            segs.append(txt[s:e_end])
        else:
            segs.append(txt[s:e_next])
    return segs


def _level_of(txt, pos, pname):
    """判断该 process 属于 L0 还是 L1。

    判据优先级：
      1. process 名带点号/下划线数字后缀（F3.1 / F3_1）→ Level 1 的细化；
      2. 最近的 module 声明（AEB_Branch → L1；ADAS_System → L0）；
      3. 最近的 "Level 0/1" 文字；
      4. 兜底：F1..F7 这类顶层名 → L0。
    """
    # 1. 点号/下划线后缀的细化名
    if re.match(r"F\d[._]\d", pname):
        return "L1"
    # 2. module 声明（只认行首的模块头，注释里提到的模块名不算）
    ctx = txt[max(0, pos - 3000): pos]
    mods = re.findall(r"^\s*module\s+(\w+)", ctx, re.M)
    if mods:
        last = mods[-1]
        if "AEB" in last:
            return "L1"
        if "ADAS" in last or "System" in last:
            return "L0"
    # 3. 文字
    tail = ctx[-1500:]
    if re.search(r"Level\s*1|AEB_Branch", tail):
        return "L1"
    if re.search(r"Level\s*0|ADAS_System", tail):
        return "L0"
    # 4. 兜底：顶层功能名属 L0
    return "L0"


def _quant_and_amb(pres, posts, types):
    """估算 quant（量化约束比例）与 amb（歧义词比率）两项。

    与 score_models_v2.py 同一量纲，但重跑文件不含 MES，无法完整复刻
    该脚本的全部规则，故此处采用**可复现的近似**：
      - quant：含数值比较符（> >= < <=）或数值常量的 pre/post 子句占全部
        pre/post 子句的比例；
      - amb：歧义词（about/approximately/usually 等）出现的子句比例。
    两项对同一生成器的不同次运行近似为常量，故区间的主要宽度来自
    有效前置条件这一项。
    """
    AMBIG = re.compile(r"\b(about|approximately|roughly|usually|often|normally|"
                       r"etc|and so on|some|several|many|few|appropriate|"
                       r"suitable|reasonable|if possible|as needed)\b", re.I)
    NUMCMP = re.compile(r"[<>]=?|\d+\.?\d*")
    all_clauses = []
    for p in pres:
        all_clauses += split_clauses(p)
    for p in posts:
        all_clauses += split_clauses(p)
    if not all_clauses:
        return 0.0, 0.0
    quant = sum(1 for c in all_clauses if NUMCMP.search(c)) / len(all_clauses)
    amb = sum(1 for c in all_clauses if AMBIG.search(c)) / len(all_clauses)
    return round(quant, 4), round(amb, 4)


def analyse_rerun(md_path):
    """从 .md 重跑输出里抽出 L0 / L1 两段并测量。

    做法：按 `process 名(` 的行首位置切分全文，每个 process 段取其中的
    `pre` / `post` 行。层级由 process 名判定（F3.1 / F3_1 这类带细化后缀的属 L1，
    F1..F7 顶层属 L0），因为不同输出的模块头写法不一致，靠上下文推断层级
    不可靠（注释里出现的模块名会被误捕）。
    """
    txt = Path(md_path).read_text(encoding="utf-8", errors="replace")
    starts = [(m.start(), m.group(1))
              for m in re.finditer(r"^\s*process\s+([\w.]+)\s*\(", txt, re.M)]
    if not starts:
        return {}
    # 类型声明：取全文里所有 composed of 块
    types_src = "\n".join(re.findall(r"(\w+)\s*=\s*composed of.*?\bend", txt, re.S))
    types = collect_types(types_src + "\n" + txt)

    buckets = {"L0": {"pre": [], "post": []}, "L1": {"pre": [], "post": []}}
    for i, (s, name) in enumerate(starts):
        e = starts[i + 1][0] if i + 1 < len(starts) else len(txt)
        seg = txt[s:e]
        lvl = "L1" if re.match(r"F\d[._]\d", name) else "L0"
        for line in seg.splitlines():
            t = line.strip()
            if t.startswith("pre"):
                clause = t[3:].strip()
                if clause:
                    buckets[lvl]["pre"].append(clause)
            elif t.startswith("post"):
                clause = t[4:].strip()
                if clause:
                    buckets[lvl]["post"].append(clause)

    out = {}
    for level, b in buckets.items():
        pres = b["pre"]
        if not pres:
            continue
        groups = len(pres)
        eff = 0
        clauses_total = 0
        subst = 0
        for p in pres:
            cl = split_clauses(p)
            clauses_total += len(cl)
            s_here = sum(1 for c in cl if (tier(c, types) or ("T4", None))[0] == "T4")
            subst += s_here
            if s_here > 0:
                eff += 1
        quant, amb = _quant_and_amb(pres, b["post"], types)
        pre_eff = round(eff / groups, 4)
        i4 = round(0.4 * pre_eff + 0.3 * quant + 0.3 * (1 - amb), 4)
        out[level] = dict(groups=groups, eff_groups=eff,
                          clauses=clauses_total, subst_clauses=subst,
                          pre_eff=pre_eff, quant=quant, amb_ratio=amb,
                          i4_pre=round(0.4 * pre_eff, 4), i4=i4)
    return out


def analyse_m2():
    """M2 的真实产物（models/M2_AI_SOFL_single）。"""
    out = {}
    for level, path in M2_MODULES:
        code, _ = from_fmodule(path)
        types = collect_types(code)
        pres, posts = [], []
        for _name, _mod, ps, qs in parse_contracts(code):
            pres += ps
            posts += qs
        g, e, c, s = measure(code, types)
        quant, amb = _quant_and_amb(pres, posts, types)
        pre_eff = round(e / g, 4) if g else 0.0
        out[level] = dict(groups=g, eff_groups=e, clauses=c, subst_clauses=s,
                          pre_eff=pre_eff, quant=quant, amb_ratio=amb,
                          i4_pre=round(0.4 * pre_eff, 4),
                          i4=round(0.4 * pre_eff + 0.3 * quant + 0.3 * (1 - amb), 4))
    return out


def main():
    results = {"M2": analyse_m2()}
    for tag, gen, cond, rel in RERUNS:
        p = ROOT / "experiment_kit" / "prompt_rerun" / rel
        if not p.exists():
            print(f"  缺少 {rel}，跳过")
            continue
        results[tag] = analyse_rerun(p)
        results[tag]["_meta"] = dict(generator=gen, condition=cond)

    # 分组汇总
    print("=" * 100)
    print("SOFL 重跑的 I4 区间")
    print("  I4 = 0.4*pre_eff + 0.3*quant + 0.3*(1-amb_ratio)")
    print("  注：quant/amb 两项对同一生成器不同次运行为准常量，区间宽度主要来自 pre_eff")
    print("=" * 100)
    by_cond = {}
    for tag, d in results.items():
        meta = d.get("_meta", {})
        key = (meta.get("generator", "MiniMax"), meta.get("condition", "no ban (current prompt)"))
        for level in ("L0", "L1"):
            if level in d:
                by_cond.setdefault(key, {}).setdefault(level, []).append(
                    (tag, d[level]["i4"], d[level].get("pre_eff", 0.0),
                     d[level]["eff_groups"], d[level]["groups"]))

    for key, levels in sorted(by_cond.items()):
        gen, cond = key
        print(f"\n[{gen} | {cond}]")
        for level, vals in sorted(levels.items()):
            vs = sorted(vals, key=lambda x: x[1])
            lo, hi = vs[0][1], vs[-1][1]
            names = ", ".join(f"{t}={v:.3f}({e}/{g})" for t, v, pe, e, g in vals)
            span = f"[{lo:.3f}, {hi:.3f}]" if len(vals) > 1 else f"[{lo:.3f}]"
            print(f"  {level}: I4 {span}  n={len(vals)}   {names}")

    # 与 M4（UML，MiniMax 生成）对照
    print("\n" + "=" * 100)
    print("与 M4（UML，MiniMax 生成，Table IV 值）对照")
    print("=" * 100)
    m4 = {"L0": 0.614, "L1": 0.429}
    m2 = {"L0": 0.557, "L1": 0.600}
    for key, levels in sorted(by_cond.items()):
        gen, cond = key
        if gen != "MiniMax":
            continue
        for level, vals in sorted(levels.items()):
            vs = sorted(vals, key=lambda x: x[1])
            lo, hi = vs[0][1], vs[-1][1]
            mv = m4.get(level)
            if mv is None:
                continue
            inside = lo <= mv <= hi
            print(f"  {cond:24s} {level}: 区间[{lo:.3f},{hi:.3f}]  M4={mv:.3f}  "
                  f"-> M4 {'落在区间内' if inside else '在区间外'}；"
                  f"M2={m2.get(level)} {'也在区间内' if lo <= m2.get(level, -1) <= hi else '不在区间内'}")

    outp = ROOT / "experiment_kit" / "prompt_rerun" / "rerun_i4_range.json"
    outp.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n写入: {outp}")


if __name__ == "__main__":
    main()
