#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
make_discriminating_sample.py —— 生成"判别力导向"的第二标注者抽样集。

背景
----
44 条原子需求里，真正承载模型间差异的只有很少几条：

  * Level 0 的 31 条：全部模型得分恒为 1（结构由规格强制规定）→ 零判别力
  * Level 1 的 13 条：8 条恒为 1（AEB-1..6、TH-2、TH-7）→ 零判别力
  * 只有 TH-1 / TH-3 / TH-4 / TH-5 / TH-6 这 5 条在不同模型间取值不同

随机抽 13 条会大量抽到恒为 1 的条目：标注者花掉大部分时间标"显然的 1"，
却几乎没有检验到任何有争议的判断。本脚本改为：

  * 主集：5 条有判别力的阈值 × 6 个有 Level-1 的模型 = 30 个判断
  * 对照集：随机 8 条恒为 1 的条目（用于检验是否存在系统性偏差，例如
    标注者是否对某类模型一律给 1），并单独报告其一致率

这样 38 个判断即可覆盖全部有争议的判断，且每个判断都有可解释的模型差异
作为核对依据。
"""
import io
import json
import os
import random

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
SEED = 20261124

DISCRIMINATING = ["TH-1", "TH-3", "TH-4", "TH-5", "TH-6"]
L1_MODELS = ["M1", "M1.1", "M2", "M3", "M4", "M5"]


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def main():
    manual = load(os.path.join(ROOT, "coverage_manual.json"))
    atoms = load(os.path.join(ROOT, "atomic_requirements_human.json"))
    atom_by_id = {a["id"]: a for a in atoms}

    # 找出恒为 1 的条目（L0 全部 + L1 的 8 条），用于对照集
    always_one = []
    for mid, blocks in manual.items():
        for lv, blk in blocks.items():
            for r in blk["rows"]:
                if r["score"] == 1:
                    always_one.append(r["id"])
    always_one = sorted(set(always_one))
    rng = random.Random(SEED)
    control_ids = sorted(rng.sample(always_one, 8))

    rows = []
    for aid in DISCRIMINATING:
        for mid in L1_MODELS:
            blk = manual.get(mid, {}).get("L1", {})
            prim = next((r["score"] for r in blk.get("rows", []) if r["id"] == aid), None)
            rows.append({
                "atom_id": aid,
                "model": mid,
                "level": "L1",
                "primary_label": prim,          # 供核对脚本用；发给标注者前应删除
                "label": "",                    # ← 标注者填 1 / 0.5 / 0
                "evidence": "",                 # ← 标注者填一句话证据
                "set": "discriminating",
            })
    for aid in control_ids:
        for mid in (["M1", "M3", "M4"]):
            lv = "L0" if any(r["id"] == aid for r in manual["M1"]["L0"]["rows"]) else "L1"
            blk = manual.get(mid, {}).get(lv, {})
            prim = next((r["score"] for r in blk.get("rows", []) if r["id"] == aid), None)
            rows.append({
                "atom_id": aid,
                "model": mid,
                "level": lv,
                "primary_label": prim,
                "label": "",
                "evidence": "",
                "set": "control",
            })

    out = {
        "_readme": (
            "第二标注者填写 label（1 / 0.5 / 0）与 evidence（一句话证据，指认模型元素或文件位置）。"
            "primary_label 仅供核对脚本使用，发放前请整列删除。"
            "discriminating 集 = 全部有判别力的判断；control 集 = 随机抽取的恒为 1 条目，"
            "用于检查是否存在系统性偏差，其一致率单独报告，不计入主 κ。"),
        "atoms": {aid: {"id": aid,
                        "category": atom_by_id.get(aid, {}).get("category"),
                        "text": atom_by_id.get(aid, {}).get("text"),
                        "source_clause": atom_by_id.get(aid, {}).get("source_clause"),
                        "criticality": atom_by_id.get(aid, {}).get("criticality")}
                  for aid in DISCRIMINATING + control_ids},
        "rows": rows,
    }
    p = os.path.join(BASE, "labelling_template_discriminating.json")
    io.open(p, "w", encoding="utf-8").write(json.dumps(out, indent=2, ensure_ascii=False))

    n_disc = sum(1 for r in rows if r["set"] == "discriminating")
    n_ctrl = sum(1 for r in rows if r["set"] == "control")
    print("已写出 labelling_template_discriminating.json")
    print("  判别力集：%d 个判断（%d 条原子 × %d 模型）"
          % (n_disc, len(DISCRIMINATING), len(L1_MODELS)))
    print("  对照集  ：%d 个判断（%d 条恒为 1 的原子 × 3 模型）" % (n_ctrl, len(control_ids)))
    print("  合计 %d 个判断（原随机方案同样抽 13 条原子，但判别力覆盖仅 3/13）" % len(rows))
    print("  对照集原子：%s" % ", ".join(control_ids))


if __name__ == "__main__":
    main()
