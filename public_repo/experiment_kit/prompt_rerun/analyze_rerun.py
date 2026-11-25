"""重跑实验（Prompt A: MiniMax+禁令 / Prompt B: Hunyuan 无禁令）统一量化。

输入：4 份新产出的 md（A1/A2 = MiniMax+禁令，B1/B2 = Hunyuan 无禁令）
      + M2（MiniMax 无禁令，历史基线，工具 XML 格式）
输出：rerun_analysis.json + 控制台表格

空洞守卫口径（与论文 score_models_v2.py 的 I4 一致，并扩展到同义反复族）：
- null_guard     `x <> null` / `x = null`
- selfeq_guard   `x = x`（同义反复）
- nat_ge0_guard  `natField >= 0`（nat 恒真）
- empty_guard    `String <> ""`（SOFL 值默认非空）
- true_guard     `if true then`（守卫恒真）
- vacuous_rate   空洞子句 / 全部 pre+post 子句
量化约束 = 含 ≥2 或非整数阈值（3.0/1.5/6.0/130/3.5…）的子句，排除 0/1 这类标志位。
"""
import json
import re
from pathlib import Path

WS = Path(r"C:/Users/zct11/WorkBuddy")
PROJ = WS / "2026-11-11-20-16-46"

FILES = {
    "A1 MiniMax+禁令": WS / "2026-11-23-18-58-03/NL-RQ-ADAS-v1_SOFL/MiniMax-M3.1-Flash-1.md",
    "A2 MiniMax+禁令": WS / "2026-11-23-18-57-31/sofl/MiniMax-M3.1-Flash-2.md",
    "B1 Hunyuan 无禁令": WS / "2026-11-23-18-59-17/Tencent Hunyuan Hy-1.md",
    "B2 Hunyuan 无禁令": WS / "2026-11-23-18-59-24/Tencent Hunyuan Hy-2.md",
    "C1 Hunyuan+禁令": WS / "2026-11-23-21-18-44/Tencent Hunyuan Hy-3.md",
    "D1 MiniMax+泛禁令": WS / "2026-11-23-21-34-36/MiniMax-M3.1-Flash+D.md",
    "D2 Hunyuan+泛禁令": PROJ / "experiment_kit/prompt_rerun/outputs/D2_hunyuan_family_ban.md",
    "B3 MiniMax无禁令(当前)": PROJ / "experiment_kit/prompt_rerun/outputs/B3_minimax_no_ban_current.md",
    "B4 MiniMax无禁令(当前)": PROJ / "experiment_kit/prompt_rerun/outputs/B4_minimax_no_ban_current.md",
}

TYPE_RE = re.compile(r"^(\w+)\s*=\s*composed of\s*$")
FIELD_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)\s*[,)]?\s*$")
PROC_RE = re.compile(r"^\s*process\s+([\w.]+)\s*\(", re.M)
MODULE_RE = re.compile(r"^\s*module\s+(\w+)", re.M)


def code_blocks(text):
    return "\n".join(re.findall(r"```[a-zA-Z]*\n(.*?)```", text, re.S))


def collect_types(text):
    types, cur = {}, None
    for line in text.splitlines():
        s = line.strip()
        m = TYPE_RE.match(s)
        if m:
            cur = m.group(1)
            types.setdefault(cur, {})
            continue
        if cur:
            if s == "end":
                cur = None
                continue
            f = FIELD_RE.match(line)
            if f:
                types[cur][f.group(1)] = f.group(2)
    return types


def field_prim(field, types):
    hits = {ft for t in types.values() for fn, ft in t.items() if fn == field and ft not in types}
    return hits.pop() if len(hits) == 1 else None


def split_and(line):
    parts, buf, instr, i = [], [], False, 0
    while i < len(line):
        if line[i] == '"':
            instr = not instr
        if not instr and line.startswith(" and ", i):
            parts.append("".join(buf))
            buf = []
            i += 5
            continue
        buf.append(line[i])
        i += 1
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


CMP_RE = re.compile(r"^([\w.]+)\s*(<>|=|>=|<=|>|<)\s*(.+)$")
NUM_RE = re.compile(r"(?:>=|<=|>|<|=)\s*(-?\d+(?:\.\d+)?)")


def classify(clause, types):
    c = clause.strip()
    if c.lower() in ("true", "1 = 1"):
        return "true_guard"
    m = CMP_RE.match(c)
    if not m:
        return None
    lhs, op, rhs = m.group(1), m.group(2), m.group(3).strip()
    if rhs.lower() == "null":
        return "null_guard"
    if rhs == '""' and field_prim(lhs.split(".")[-1], types) == "String":
        return "empty_guard"
    if lhs == rhs:
        return "selfeq_guard"
    if op == ">=" and rhs == "0" and field_prim(lhs.split(".")[-1], types) == "nat":
        return "nat_ge0_guard"
    return None


def is_quantified(clause):
    for n in NUM_RE.findall(clause):
        try:
            v = float(n)
        except ValueError:
            continue
        if abs(v) not in (0.0, 1.0):
            return True
    return False


def parse_contracts(code):
    """返回 [(procName, module, pres, posts)]，按 module 位置归属。"""
    mods = [(m.start(), m.group(1)) for m in MODULE_RE.finditer(code)]
    out = []
    for m in PROC_RE.finditer(code):
        name = m.group(1)
        module = None
        for pos, mn in mods:
            if pos < m.start():
                module = mn
        seg = code[m.end():]
        end = re.search(r"end_process", seg)
        body = seg[: end.start()] if end else seg[:5000]
        pres, posts = [], []
        for line in body.splitlines():
            s = line.strip()
            if s.startswith("pre "):
                pres += split_and(s[4:])
            elif s.startswith("post") or s.startswith("if "):
                rest = s[4:].strip() if s.startswith("post") else s
                if not rest:
                    continue
                mm = re.match(r"if\s+(.*?)\s+then\s+(.*)$", rest)
                if mm:
                    posts += split_and(mm.group(1)) + split_and(mm.group(2))
                else:
                    posts += split_and(rest)
        out.append((name, module, pres, posts))
    return out


def from_md(path):
    raw = path.read_text(encoding="utf-8")
    return code_blocks(raw), raw


def from_fmodule(path):
    txt = path.read_text(encoding="utf-8-sig").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    lines = []
    td = re.search(r"<typeDeclaration>(.*?)</typeDeclaration>", txt, re.S)
    if td:
        lines.append(td.group(1))
    for m in re.finditer(r'<process name="([^"]+)"[^>]*>(.*?)</process>', txt, re.S):
        lines.append(f"process {m.group(1)}(")
        for line in m.group(2).splitlines():
            s = line.strip()
            if s.startswith(("pre", "post", "if ", "ext ")):
                lines.append(f"  {s}")
        lines.append("end_process")
    return "\n".join(lines), txt


THRESHOLDS = {
    "N-1 130 km/h": 130.0, "N-2 TTC 2.0": 2.0, "A-1 6.0": 6.0, "A-2 brake 4.0": 4.0,
    "A-4 yaw 3.5": 3.5, "A-5 3.0": 3.0, "A-5 1.5": 1.5, "A-6 ±1.0": 1.0,
}
BANNED_OPS = {"or": r"\bor\b", "not": r"\bnot\b", "=>": r"=>", "seq of": r"seq of",
              "list of": r"list of", "forall": r"[∀∃]|\bforall\b|\bexists\b"}


def analyse(label, path, loader):
    code, raw = loader(path)
    types = collect_types(code)
    procs = parse_contracts(code)
    stats = dict(null_guard=0, selfeq_guard=0, nat_ge0_guard=0, empty_guard=0, true_guard=0, other=0)
    quant = 0
    pre_n = post_n = 0
    eff_pre = 0
    modules = {}
    for name, module, pres, posts in procs:
        pre_n += len(pres)
        post_n += len(posts)
        mod = modules.setdefault(module or "?", dict(processes=0, pre=0, post=0, vacuous=0))
        mod["processes"] += 1
        mod["pre"] += len(pres)
        mod["post"] += len(posts)
        if any(classify(c, types) is None for c in pres):
            eff_pre += 1
        for c in pres + posts:
            k = classify(c, types)
            stats[k or "other"] += 1
            if k:
                mod["vacuous"] += 1
            if is_quantified(c) and k is None:
                quant += 1
    vac = sum(v for k, v in stats.items() if k != "other")
    total = pre_n + post_n
    return dict(label=label, file=path.name, processes=len(procs), pre=pre_n, post=post_n,
                effective_pre=eff_pre,
                clauses=total, guards=stats, vacuous=vac,
                vacuous_rate=round(vac / total, 3) if total else 0.0,
                quantified=quant, types=len(types),
                thresholds_hit=[k for k, v in THRESHOLDS.items()
                                if re.search((rf"(?<![\d.]){int(v)}(?:\.0+)?(?![\d])" if float(v).is_integer()
                                              else rf"(?<![\d.]){v}(?![\d])"), code)],
                banned_ops=[k for k, pat in BANNED_OPS.items() if re.search(pat, code)],
                const_block=bool(re.search(r"^\s*const\b|\bconstantDeclaration\b|^[A-Z_]{3,}\s*[:=]", code, re.M)),
                valid_field=bool(re.search(r"^\s*valid\s*:\s*nat", code, re.M)),
                literal_null_in_doc=len(re.findall(r"<>\s*null", raw)),
                modules=modules)


def main():
    results = [analyse(lbl, p, from_md) for lbl, p in FILES.items()]
    m2 = PROJ / "models/M2_AI_SOFL_single"
    for mod in ("ADAS_System", "AEB_Branch"):
        results.append(analyse(f"M2 MiniMax 无禁令/{mod}", m2 / f"{mod}.fModule", from_fmodule))

    merged = {}
    for r in results:
        if r["label"].startswith("M2"):
            key = "M2 MiniMax 无禁令"
            m = merged.setdefault(key, dict(label=key, processes=0, pre=0, post=0, clauses=0,
                                            guards=dict(null_guard=0, selfeq_guard=0, nat_ge0_guard=0,
                                                        empty_guard=0, true_guard=0, other=0),
                                            vacuous=0, quantified=0, types=0, valid_field=False,
                                            literal_null_in_doc=0, modules={}, effective_pre=0,
                                            thresholds_hit=[], banned_ops=[], const_block=False))
            for k in ("processes", "pre", "post", "clauses", "vacuous", "quantified", "effective_pre"):
                m[k] += r[k]
            for k in m["guards"]:
                m["guards"][k] += r["guards"][k]
            for k in ("thresholds_hit", "banned_ops"):
                m.setdefault(k, [])
                m[k] = sorted(set(m[k]) | set(r.get(k, [])))
            m["types"] += r["types"]
            m["literal_null_in_doc"] += r["literal_null_in_doc"]
            m["modules"].update(r["modules"])
    if "M2 MiniMax 无禁令" in merged:
        m = merged["M2 MiniMax 无禁令"]
        m["vacuous_rate"] = round(m["vacuous"] / m["clauses"], 3) if m["clauses"] else 0.0
        results = [r for r in results if not r["label"].startswith("M2")] + [m]

    out = PROJ / "experiment_kit/prompt_rerun/rerun_analysis.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    hdr = (f"{'条件':<22}{'proc':>5}{'pre':>5}{'post':>5}{'null':>6}{'x=x':>6}{'nat>=0':>7}"
           f"{'空串':>5}{'true':>6}{'空洞率':>8}{'有效pre':>8}{'禁用':>5}")
    print(hdr)
    print("-" * 82)
    for r in results:
        g = r["guards"]
        print(f"{r['label']:<22}{r['processes']:>5}{r['pre']:>5}{r['post']:>5}{g['null_guard']:>6}"
              f"{g['selfeq_guard']:>6}{g['nat_ge0_guard']:>7}{g['empty_guard']:>5}"
              f"{g['true_guard']:>6}{r['vacuous_rate']:>8.1%}{r['effective_pre']:>4}/{r['processes']}"
              f"{len(r['banned_ops']):>9}")
    for r in results:
        print(f"\n{r['label']}: 阈值 {r['thresholds_hit']}")
        print(f"  禁用算子/记法: {r['banned_ops']}  const块={r['const_block']}  valid字段={r['valid_field']}")
    print("\n写入:", out)


if __name__ == "__main__":
    main()
