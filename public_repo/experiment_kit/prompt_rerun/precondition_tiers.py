"""前置条件四层分级（T1..T4），用于检验"空洞率"这一指标的构念效度。

动机：`x <> null` 之类的恒真守卫只是"无内容"的一种写法。D1（泛化禁令）把 T1 压到 0，
但把内容换成了模型自己声明的 `valid = 1` 旗标。要判断模型是否真的写好了前置条件，
必须区分四层：

  T1 tautology  —— 类型层面恒真：`x <> null`、`x = x`、`nat 字段 >= 0`、`String <> ""`、`if true`
  T2 flag       —— 有效性旗标 `X.valid = 1` / `X.*_valid = true`
       T2a spec-grounded：规格 E1/E2 明写 "with per-sensor validity flags"
       T2b invented    ：模型自行在每个 composed type 里加的 `valid: nat`
  T3 axiom      —— 领域公理，可满足但无规格内容：`speed >= 0`、`speed_limit >= 0`、
                   经纬度范围 `lon in [-180,180]`
  T4 substantive—— 真正的规格内容：与阈值比较（1.5/3.0/6.0/130…）或字段间关系
                   （`yaw_rate <= yaw_rate_limit`）

只有 T4 是可核验的规格约束；T3 是人机共有的填充；T2b 是 D1 新增的迁移形态。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from analyze_rerun import (from_md, from_fmodule, parse_contracts, collect_types,
                           classify, WS, PROJ)

# 规格 E1/E2 明确声明的传感器有效性旗标
SPEC_FLAGS = re.compile(r"(camera|radar|lidar|gnss|imu|position)_valid$")
FLAG_RE = re.compile(r"^([\w.]+?)\s*(?:=|<>)\s*(1|true|0|false)$", re.I)
NUM_CMP = re.compile(r"^([\w.]+)\s*(<>|>=|<=|>|<|=)\s*(-?\d+(?:\.\d+)?)$")
FIELD_CMP = re.compile(r"^([\w.]+)\s*(<>|>=|<=|>|<|=)\s*([A-Za-z_][\w.]*)$")

LATLON = re.compile(r"\.(longitude|latitude|lon|lat)$")
AXIOM_FIELDS = re.compile(r"(speed|speed_limit|limit|horizon|brake_cmd|decel_req|distance|"
                          r"timestamp|frame_count|count|path_length|ttc)", re.I)

# 规范阈值白名单：这些具体数值来自需求规格，落在 0/1 附近也不当作域公理。
# 与 contract_content_analysis.sub_tier 保持一致——两张表必须共用同一判据，
# 否则同一批前置条件会在两张表里得到不同的"实质"计数。
SUBSTANTIVE_NUMS = {1.5, 2.0, 3.0, 3.5, 4.0, 6.0, 30.0, 130.0}


def tier(clause, types):
    c = clause.strip()
    k = classify(c, types)
    if k:
        return "T1", k
    # SOFL 值默认非空：`x <> ""` 与类型是否可解析无关，一律算恒真
    if re.match(r'^[\w.]+\s*<>\s*""$', c):
        return "T1", "empty_guard"

    m = FLAG_RE.match(c)
    if m:
        fld = m.group(1).split(".")[-1]
        if SPEC_FLAGS.search(fld):
            return "T2a", None
        if re.search(r"valid", fld, re.I):
            return "T2b", None
        # 其他 0/1 旗标（override_accelerate 等）：视为域输入，归 T3
        return "T3", None

    m = NUM_CMP.match(c)
    if m:
        lhs, op, rhs = m.group(1), m.group(2), m.group(3)
        if LATLON.search(lhs) and op in (">=", "<="):
            return "T3", None
        v = float(rhs)
        # 规范阈值优先：白名单里的数值本身就是需求内容
        if abs(v) in SUBSTANTIVE_NUMS:
            return "T4", None
        # 域公理：字段名在白名单中且取值落在 0/1 附近
        if abs(v) in (0.0, 1.0) and op in (">=", ">"):
            if AXIOM_FIELDS.search(lhs.split(".")[-1]):
                return "T3", None
            # 字段名不在域公理白名单：这是一个真实的数值约束，归 T4
            return "T4", None
        if AXIOM_FIELDS.search(lhs.split(".")[-1]) and abs(v) in (0.0, 1.0):
            return "T3", None
        return "T4", None

    if FIELD_CMP.match(c):
        return "T4", None
    return "T4", None


def run(label, path, loader, merge_modules=False):
    code, _ = loader(path)
    types = collect_types(code)
    procs = parse_contracts(code)
    tiers = dict(T1=0, T2a=0, T2b=0, T3=0, T4=0)
    detail = []
    for name, _mod, pres, _posts in procs:
        for c in pres:
            t, sub = tier(c, types)
            tiers[t] += 1
            detail.append((name, c, t, sub))
    n = sum(tiers.values())
    return dict(label=label, file=path.name if path else "System+AEB_Branch", pre=n, tiers=tiers,
                t1_rate=round(tiers["T1"] / n, 3) if n else 0,
                content_rate=round(tiers["T4"] / n, 3) if n else 0,
                t2b_rate=round(tiers["T2b"] / n, 3) if n else 0,
                detail=detail)


def m1_loader(_):
    base = PROJ / "models/M1_manual_human"
    parts = []
    for f in ("System.fModule", "BehaviorPlanning.fModule"):
        txt = (base / f).read_text(encoding="utf-8-sig")
        txt = txt.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        parts.append(txt)
    txt = "\n".join(parts)
    lines = []
    for m in re.finditer(r'<process name="([^"]+)"[^>]*>(.*?)</process>', txt, re.S):
        lines.append(f"process {m.group(1)}(")
        for line in m.group(2).splitlines():
            s = line.strip()
            if s.startswith(("pre", "post", "if ")):
                lines.append(f"  {s}")
        lines.append("end_process")
    return "\n".join(lines), txt


CASES = [
    ("M1 人工基准", None, m1_loader),
    ("M2 MiniMax 无禁令", PROJ / "models/M2_AI_SOFL_single/ADAS_System.fModule", from_fmodule),
    ("M2' (L1)", PROJ / "models/M2_AI_SOFL_single/AEB_Branch.fModule", from_fmodule),
    ("A1 MiniMax+单点禁令", WS / "2026-11-23-18-58-03/NL-RQ-ADAS-v1_SOFL/MiniMax-M3.1-Flash-1.md", from_md),
    ("A2 MiniMax+单点禁令", WS / "2026-11-23-18-57-31/sofl/MiniMax-M3.1-Flash-2.md", from_md),
    ("D1 MiniMax+泛禁令", WS / "2026-11-23-21-34-36/MiniMax-M3.1-Flash+D.md", from_md),
    ("B1 Hunyuan 无禁令", WS / "2026-11-23-18-59-17/Tencent Hunyuan Hy-1.md", from_md),
    ("B2 Hunyuan 无禁令", WS / "2026-11-23-18-59-24/Tencent Hunyuan Hy-2.md", from_md),
    ("C1 Hunyuan+单点禁令", WS / "2026-11-23-21-18-44/Tencent Hunyuan Hy-3.md", from_md),
    ("D2 Hunyuan+泛禁令", PROJ / "experiment_kit/prompt_rerun/outputs/D2_hunyuan_family_ban.md", from_md),
    ("B3 MiniMax无禁令(当前)", PROJ / "experiment_kit/prompt_rerun/outputs/B3_minimax_no_ban_current.md", from_md),
    ("B4 MiniMax无禁令(当前)", PROJ / "experiment_kit/prompt_rerun/outputs/B4_minimax_no_ban_current.md", from_md),
]


def flag_breakdown(path):
    """旗标守卫按"被守卫的信号由谁产生"分类。

    若某信号是本系统某个 process 的输出，它的 valid 旗标由生产者自己置位，
    则 `x.valid = 1` 无法在运行时失败 —— 语义上恒真，但语法上不是恒真式，
    因此任何"按 idiom 列举"的禁令与任何语法检查都抓不到它。
    """
    code, _ = from_md(path)
    produced = set()
    for m in re.finditer(r"process\s+\w+\s*\(([^)]*)\)\s*out:\s*([^\n]+)", code):
        for seg in m.group(2).split(","):
            if ":" in seg:
                produced.add(seg.split(":")[0].strip())
    internal, external = [], []
    for name, _mod, pres, _posts in parse_contracts(code):
        for c in pres:
            m = re.match(r"^([\w.]+?)\.(\w*valid\w*)\s*(?:=|<>)\s*(1|true)$", c, re.I)
            if not m:
                continue
            base = m.group(1).split(".")[0]
            (internal if base in produced else external).append((name, c, base))
    return produced, internal, external


def main():
    results = [run(lbl, p, ld) for lbl, p, ld in CASES]
    # M2 两个 module 合并
    m2 = [r for r in results if r["label"].startswith("M2")]
    if len(m2) == 2:
        merged = dict(label="M2 MiniMax 无禁令", file="ADAS_System+AEB_Branch",
                      pre=sum(r["pre"] for r in m2),
                      tiers={k: sum(r["tiers"][k] for r in m2) for k in m2[0]["tiers"]},
                      detail=sum((r["detail"] for r in m2), []))
        n = merged["pre"]
        merged.update(t1_rate=round(merged["tiers"]["T1"] / n, 3),
                      content_rate=round(merged["tiers"]["T4"] / n, 3),
                      t2b_rate=round(merged["tiers"]["T2b"] / n, 3))
        results = [r for r in results if not r["label"].startswith("M2")] + [merged]

    out = Path(__file__).parent / "precondition_tiers.json"
    out.write_text(json.dumps([{k: v for k, v in r.items() if k != "detail"} | {"detail": r["detail"]}
                               for r in results], ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{'条件':<24}{'pre':>5}{'T1恒真':>8}{'T2b自造旗标':>12}{'T3公理':>8}{'T4真内容':>9}"
          f"{'  内容率':>8}")
    print("-" * 78)
    for r in results:
        t = r["tiers"]
        print(f"{r['label']:<24}{r['pre']:>5}{t['T1']:>8}{t['T2b']:>12}{t['T3']:>8}{t['T4']:>9}"
              f"{r['content_rate']:>9.0%}")
    print("\nT2a(规格内传感器旗标):",
          {r["label"]: r["tiers"]["T2a"] for r in results})
    print("写入:", out)

    produced, internal, external = flag_breakdown(
        WS / "2026-11-23-21-34-36/MiniMax-M3.1-Flash+D.md")
    print(f"\n== D1 旗标守卫来源分解（系统产出信号: {sorted(produced)}）")
    print(f"   守内部产出信号 = {len(internal)}/{len(internal)+len(external)}")
    for n, c, _b in internal:
        print(f"      {n:<28}{c}")
    print(f"   守外部接口输入 = {len(external)}")
    for n, c, _b in external:
        print(f"      {n:<28}{c}")


if __name__ == "__main__":
    main()
