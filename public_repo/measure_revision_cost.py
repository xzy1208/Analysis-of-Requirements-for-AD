#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
measure_revision_cost.py —— 测算 M1 → M1.1 的人工修订成本。

M1.1 = 人工 SOFL 模型（M1）补入 §7 规范阈值与 §8 假设所要求的契约后的版本。
修订成本用两个互补的度量：

  1. 契约级：新增/修改的契约条数 ÷ 修订后的契约总条数
     —— 「一个熟悉该记法的人把阈值表落进既有模型，需要动多少比例的契约」
  2. 变更级：实际发生的编辑操作数（新增条款、修改条款、新增类型字段、
     新增数据字段、新增追溯行），以及每个阈值各自需要的编辑动作数。

编辑操作数按「原子编辑」计：一次对某一 process 契约某一行的增删改 = 1 次；
一次对某个 composed type 的字段增删 = 1 次；一条追溯记录 = 1 次。
这与研究计划中原定的度量「修改处数 / 总契约条数」一致，并补足了
「类型字段」与「追溯」两类不落在契约里的改动。
"""
import io
import json
import os
import re
import difflib

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"
M1 = os.path.join(BASE, "models", "M1_manual_human")
M11 = os.path.join(BASE, "models", "M1_1_manual_plus_thresholds")


def read(p):
    return io.open(p, encoding="utf-8-sig").read()


def contracts(text):
    """抽出 (process, kind, body) 契约条目：kind ∈ {pre, post}。"""
    out = []
    cur = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r'<process name="([^"]+)"', s)
        if m:
            cur = m.group(1)
            continue
        if s.startswith("pre "):
            out.append((cur, "pre", s[4:].strip()))
        elif s.startswith("if ") and " then " in s:
            guard, eff = s.split(" then ", 1)
            out.append((cur, "post", guard.strip() + " => " + eff.strip()))
    return out


def types(text):
    """抽出 {类型名: [字段,...]}。"""
    out = {}
    td = re.search(r"<typeDeclaration>(.*?)</typeDeclaration>", text, re.S)
    if not td:
        return out
    for m in re.finditer(r"(\w+)\s*=\s*composed of(.*?)\bend", td.group(1), re.S):
        fields = [l.strip().split(":")[0].strip()
                  for l in m.group(2).splitlines() if ":" in l]
        out[m.group(1)] = fields
    return out


def mes_traces(model_dir, mid):
    p = os.path.join(model_dir, "MES_%s_L0.json" % mid)
    if not os.path.exists(p):
        return []
    d = json.load(io.open(p, encoding="utf-8-sig"))
    return d.get("traceability", [])


def diff_ops(a, b):
    """两个契约集合之间的编辑操作数（新增 + 修改；相同的不计）。"""
    ca = set(contracts(a))
    cb = set(contracts(b))
    added = cb - ca
    # 修改：同一 process+kind 下 body 不同 → 记 1 次修改（删除旧 + 新增新）
    by_key_a, by_key_b = {}, {}
    for p, k, body in ca:
        by_key_a.setdefault((p, k), set()).add(body)
    for p, k, body in cb:
        by_key_b.setdefault((p, k), set()).add(body)
    modified = 0
    for key in by_key_a:
        if key in by_key_b and by_key_a[key] != by_key_b[key]:
            # 交集保留；差集按新增计
            pass
    return added, cb


def main():
    res = {}
    for lvl, fname in (("L0", "System.fModule"), ("L1", "BehaviorPlanning.fModule")):
        ta, tb = read(os.path.join(M1, fname)), read(os.path.join(M11, fname))
        ca, cb = contracts(ta), contracts(tb)
        set_a, set_b = set(ca), set(cb)
        added = set_b - set_a
        removed = set_a - set_b

        # 修改：同 (process, kind) 且 body 不同 → 计为 1 次修改
        ka, kb = {}, {}
        for p, k, body in ca:
            ka.setdefault((p, k), []).append(body)
        for p, k, body in cb:
            kb.setdefault((p, k), []).append(body)
        modified = 0
        for key in ka:
            if key in kb:
                common = set(ka[key]) & set(kb[key])
                if len(ka[key]) != len(common) or len(kb[key]) != len(common):
                    modified += max(len(ka[key]) - len(common),
                                    len(kb[key]) - len(common))

        type_a, type_b = types(ta), types(tb)
        new_fields = 0
        field_detail = []
        for t, fs in type_b.items():
            old = type_a.get(t, [])
            extra = [f for f in fs if f not in old]
            if extra:
                new_fields += len(extra)
                field_detail.append((t, extra))

        res[lvl] = {
            "contracts_before": len(ca),
            "contracts_after": len(cb),
            "contracts_added": len(added),
            "contracts_removed": len(removed),
            "contracts_modified": modified,
            "contract_edits": len(added) + len(removed) + modified,
            "new_type_fields": new_fields,
            "new_field_detail": field_detail,
            "added_detail": sorted("%s | %s | %s" % (p, k, b) for p, k, b in added),
        }

    # 追溯行变化
    tr1 = mes_traces(M1, "M1")
    tr11 = mes_traces(M11, "M1.1")
    s1 = set(t.get("requirement", "") for t in tr1)
    s11 = set(t.get("requirement", "") for t in tr11)
    res["traceability"] = {
        "m1_rows": len(tr1), "m11_rows": len(tr11),
        "added": sorted(s11 - s1), "removed": sorted(s1 - s11),
    }

    # 汇总
    total_contract_edits = sum(res[l]["contract_edits"] for l in ("L0", "L1"))
    total_after = sum(res[l]["contracts_after"] for l in ("L0", "L1"))
    total_fields = sum(res[l]["new_type_fields"] for l in ("L0", "L1"))
    total_tr = len(res["traceability"]["added"])

    res["summary"] = {
        "contract_edits": total_contract_edits,
        "contracts_after": total_after,
        "contract_edit_ratio": round(total_contract_edits / total_after, 4),
        "new_type_fields": total_fields,
        "traceability_rows_added": total_tr,
        "total_edits": total_contract_edits + total_fields + total_tr,
    }

    out = os.path.join(BASE, "revision_cost_m1_to_m1_1.json")
    io.open(out, "w", encoding="utf-8").write(
        json.dumps(res, indent=2, ensure_ascii=False))

    print("=" * 84)
    print("M1 → M1.1 人工修订成本")
    print("=" * 84)
    for lvl in ("L0", "L1"):
        r = res[lvl]
        print("%s: 契约 %d → %d（新增 %d / 删除 %d / 修改 %d）；新增类型字段 %d"
              % (lvl, r["contracts_before"], r["contracts_after"],
                 r["contracts_added"], r["contracts_removed"],
                 r["contracts_modified"], r["new_type_fields"]))
        for t, fs in r["new_field_detail"]:
            print("     类型 %s 新增字段: %s" % (t, ", ".join(fs)))
        for d in r["added_detail"]:
            print("     + %s" % d)
    tr = res["traceability"]
    print("追溯行: M1 %d → M1.1 %d（新增 %s）"
          % (tr["m1_rows"], tr["m11_rows"], ", ".join(tr["added"])))
    s = res["summary"]
    print("-" * 84)
    print("契约级修订率 = %d / %d = %.1f%%"
          % (s["contract_edits"], s["contracts_after"], s["contract_edit_ratio"] * 100))
    print("全部编辑操作 = %d（契约 %d + 类型字段 %d + 追溯行 %d）"
          % (s["total_edits"], s["contract_edits"], s["new_type_fields"],
             s["traceability_rows_added"]))
    print("\n已写出 revision_cost_m1_to_m1_1.json")


if __name__ == "__main__":
    main()
