"""pre+post 契约内容分析（增量证据，不改 Table IV / VII 的现有分数）。

背景：评审指出，现有 Finding 只统计前置条件的实质率（D1 0/38、D2 1/32），
就断言"内容丢失"是不完整的——D2 还有 171 条后置条件没有分析，内容可能
只是移到了 post。本脚本对 pre 与 post 分别统计实质子句比例，验证该结论。

判据（统一用于 pre 与 post，按子句判定）：
  T1 vacuous     类型层恒真：`x <> null`/`x = x`/`nat >= 0`/`x <> ''`/`if true`
  T2 flag        有效性旗标 `valid = 1`（含规格内传感器旗标与自造 valid）
  T3 axiom       域公理：非负值、经纬度范围、`count = 0/>0` 这类计数分支
  T4 substantive 阈值比较（1.5/3.0/6.0/130/3.5...）或字段间关系或枚举/常量赋值

注意：post 的 `warning.active = 1`、`target_speed = 0`、`warning_type = "none"`
是把输出约束到具体值/枚举，属于 T4；guard 里的 `object_count > 0` 虽是
计数分支，但对 post 而言它划分了情形，也计入 T4（作为触发条件的内容）。
脚本对两者都报告：strict（只谓词）与 with_guard（守卫+谓词）两种口径。
"""
import io, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from analyze_rerun import (from_md, from_fmodule, code_blocks, parse_contracts,
                           collect_types, split_and, classify, WS, PROJ)

# ---------- 判据 ----------
NUM_CMP = re.compile(r'^([\w.]+)\s*(<>|>=|<=|>|<|=)\s*(-?\d+(?:\.\d+)?)$')
STR_CMP = re.compile(r'^([\w.]+)\s*(=|<>)\s*"([^"]*)"$')
FIELD_CMP = re.compile(r'^([\w.]+)\s*(<>|>=|<=|>|<|=)\s*([A-Za-z_][\w.]*)$')
FLAG_RE = re.compile(r'^([\w.]+?)\s*(?:=|<>)\s*(1|true|0|false)$', re.I)
LATLON = re.compile(r'\.(longitude|latitude|lon|lat)$')
AXIOM_FIELD = re.compile(r'(speed|speed_limit|limit|horizon|brake|decel|distance|timestamp|frame_count|count|path_length|ttc)', re.I)
# 非整数阈值（真正的规范值）或整数 >1（如 130）视为实质
SUBSTANTIVE_NUMS = {1.5, 2.0, 3.0, 3.5, 4.0, 6.0, 30.0, 130.0}


def sub_tier(clause, types):
    """实质内容判据 —— 复用 precondition_tiers.tier()，确保与 Table VII-c 同源。

    历史原因：本脚本曾自带一套 sub_tier 判据（带 SUBSTANTIVE_NUMS 白名单），
    与 precondition_tiers.tier() 略有差异，导致同一批前置条件在两张表里
    得到不同的"实质"计数（例如 risk_level.risk_value >= 0：VII-c 记 T3、
    VII-d 记 T4）。现统一为单一判据。
    """
    from precondition_tiers import tier as _tier
    t = _tier(clause, types)
    if t is None:
        return "T4"
    # tier 返回 ("T1"|"T2a"|"T2b"|"T3"|"T4", detail)
    # 归并为本文的四类：T1 空洞 / T2 旗标 / T3 域公理 / T4 实质
    code = t[0]
    if code == "T1":
        return "T1"
    if code in ("T2a", "T2b"):
        return "T2"
    if code == "T3":
        return "T3"
    return "T4"


def parse_full(code):
    """返回 [(proc, module, pres, [(guard, consequent), ...])]。"""
    mods = [(m.start(), m.group(1)) for m in re.finditer(r'^\s*module\s+(\w+)', code, re.M)]
    out = []
    for m in re.finditer(r'^\s*process\s+([\w.]+)\s*\(', code, re.M):
        name = m.group(1)
        module = None
        for pos, mn in mods:
            if pos < m.start():
                module = mn
        seg = code[m.end():]
        end = re.search(r'end_process', seg)
        body = seg[:end.start()] if end else seg[:5000]
        pres, pairs = [], []
        for line in body.splitlines():
            s = line.strip()
            if s.startswith('pre '):
                pres += split_and(s[4:])
            elif s.startswith('post') or s.startswith('if '):
                rest = s[4:].strip() if s.startswith('post') else s
                if not rest:
                    continue
                mm = re.match(r'if\s+(.*?)\s+then\s+(.*)$', rest)
                if mm:
                    pairs.append((split_and(mm.group(1)), split_and(mm.group(2))))
                else:
                    pairs.append(([], split_and(rest)))
        out.append((name, module, pres, pairs))
    return out


def analyse(label, path, loader):
    code, _ = loader(path)
    types = collect_types(code)
    procs = parse_full(code)
    pre = {'T1': 0, 'T2': 0, 'T3': 0, 'T4': 0}
    post_strict = {'T1': 0, 'T2': 0, 'T3': 0, 'T4': 0}
    post_guard = {'T1': 0, 'T2': 0, 'T3': 0, 'T4': 0}
    for _n, _mod, pres, pairs in procs:
        for c in pres:
            pre[sub_tier(c, types)] += 1
        for guards, cons in pairs:
            for c in cons:
                post_strict[sub_tier(c, types)] += 1
            for c in guards:
                post_guard[sub_tier(c, types)] += 1
    def rate(d):
        n = sum(d.values())
        return (round(d['T4']/n, 3) if n else 0), n
    ps, nps = rate(post_strict)
    pg, npg = rate(post_guard)
    # 合并 post（guard + consequent）
    post_all = {k: post_strict[k] + post_guard[k] for k in pre}
    pa, npa = rate(post_all)
    pr, npr = rate(pre)
    return dict(label=label, pre=pre, pre_rate=pr, pre_n=npr,
                post_strict=post_strict, post_strict_rate=ps, post_strict_n=nps,
                post_guard=post_guard, post_guard_rate=pg, post_guard_n=npg,
                post_all=post_all, post_all_rate=pa, post_all_n=npa)


CASES = [
    ('D2 Hunyuan family ban', PROJ / 'experiment_kit/prompt_rerun/outputs/D2_hunyuan_family_ban.md', from_md),
    ('B3 MiniMax no ban (current)', PROJ / 'experiment_kit/prompt_rerun/outputs/B3_minimax_no_ban_current.md', from_md),
    ('B4 MiniMax no ban (current)', PROJ / 'experiment_kit/prompt_rerun/outputs/B4_minimax_no_ban_current.md', from_md),
    ('D1 MiniMax family ban', WS / '2026-11-23-21-34-36/MiniMax-M3.1-Flash+D.md', from_md),
    ('A2 MiniMax single ban', WS / '2026-11-23-18-57-31/sofl/MiniMax-M3.1-Flash-2.md', from_md),
    ('C1 Hunyuan single ban', WS / '2026-11-23-21-18-44/Tencent Hunyuan Hy-3.md', from_md),
    ('B2 Hunyuan no ban', WS / '2026-11-23-18-59-24/Tencent Hunyuan Hy-2.md', from_md),
    ('B1 Hunyuan no ban', WS / '2026-11-23-18-59-17/Tencent Hunyuan Hy-1.md', from_md),
]


def m2_loader(_):
    """M2 的两个模块合并（L0 + L1），与 Table VII-c 的合并口径一致。"""
    base = PROJ / 'models/M2_AI_SOFL_single'
    parts = []
    for f in ('ADAS_System.fModule', 'AEB_Branch.fModule'):
        t = (base / f).read_text(encoding='utf-8-sig').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        parts.append(t)
    lines = []
    for m in re.finditer(r'<process name="([^"]+)"[^>]*>(.*?)</process>', '\n'.join(parts), re.S):
        lines.append(f'process {m.group(1)}(')
        for line in m.group(2).splitlines():
            s = line.strip()
            if s.startswith(('pre', 'post', 'if ')):
                lines.append(f'  {s}')
        lines.append('end_process')
    return '\n'.join(lines), '\n'.join(parts)


def m1_loader(_):
    base = PROJ / 'models/M1_manual_human'
    parts = []
    for f in ('System.fModule', 'BehaviorPlanning.fModule'):
        t = (base / f).read_text(encoding='utf-8-sig').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        parts.append(t)
    lines = []
    for m in re.finditer(r'<process name="([^"]+)"[^>]*>(.*?)</process>', '\n'.join(parts), re.S):
        lines.append(f'process {m.group(1)}(')
        for line in m.group(2).splitlines():
            s = line.strip()
            if s.startswith(('pre', 'post', 'if ')):
                lines.append(f'  {s}')
        lines.append('end_process')
    return '\n'.join(lines), '\n'.join(parts)


def main():
    results = [analyse(l, p, ld) for l, p, ld in CASES]
    results.append(analyse('M1 manual', None, m1_loader))
    results.append(analyse('M2 MiniMax no ban', None, m2_loader))
    out = Path(__file__).parent / 'contract_content_results.json'
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"{'条件':<26}{'pre实质率':>10}{'post实质率(strict)':>19}{'post(含guard)':>15}{'pre n':>7}{'post n':>8}")
    print('-' * 88)
    for r in results:
        print(f"{r['label']:<26}{r['pre_rate']:>10.1%}{r['post_strict_rate']:>19.1%}"
              f"{r['post_all_rate']:>15.1%}{r['pre_n']:>7}{r['post_strict_n']:>8}")
    print('\n说明：strict = 只算 then 后的谓词；含 guard = 守卫 + 谓词。')
    print('写入:', out)


if __name__ == '__main__':
    main()
