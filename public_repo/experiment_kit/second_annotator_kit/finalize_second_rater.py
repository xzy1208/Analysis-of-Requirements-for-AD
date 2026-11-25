#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
finalize_second_rater.py —— 第二标注者填完后，跑一致性并回填论文。

用法
----
    python finalize_second_rater.py annotator_form_filled.json
    python finalize_second_rater.py annotator_form_filled.json --out _dryrun
        # --out 指定结果输出目录（演练时用，避免污染正式结果）

产出
----
    second_rater_results.json   κ、一致率、分歧清单（供论文引用）
    paper_patch.md              可直接粘进论文的两句话（中英各一）

口径
----
  * 判别力集（5 条阈值 × 6 模型 = 30 个判断）—— 主集，κ 在此计算
  * 对照集（8 条恒为 1 的原子 × 3 模型 = 24 个判断）—— 只报一致率，
    用于检查是否存在系统性偏差（例如"对某类模型一律给 1"），不混入主 κ
"""
import io
import json
import os
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))


def read_json(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def control_clause(ctl):
    """对照集一致率的措辞 —— 必须随实际数值变，不能一律说"未见系统性偏袒"。

    与 apply_second_rater_to_paper.py 中的同名函数保持一致。
    对照集是 8 条在所有模型里都恒为覆盖的原子；第二标注者若在这里明显打低，
    说明其在明确成立的条目上系统性偏严，而非偏袒覆盖，须如实说明。
    """
    if ctl is None:
        return ("", "")
    x = 100 * ctl
    if ctl >= 0.90:
        return ("on a control set of eight always-covered atoms the agreement was %.1f%%, "
                "indicating no systematic bias toward granting coverage. " % x,
                "在恒为覆盖的对照集上一致率为 %.1f%%，未见系统性偏袒覆盖的倾向。" % x)
    if ctl >= 0.70:
        return ("on a control set of eight always-covered atoms the agreement was %.1f%%, "
                "showing mild strictness rather than a bias toward granting coverage. " % x,
                "在恒为覆盖的对照集上一致率为 %.1f%%，表现为轻度偏严而非偏袒覆盖。" % x)
    return ("on a control set of eight always-covered atoms the agreement was only %.1f%%, so the "
            "second rater is systematically stricter than the primary rater even on unambiguous "
            "cases; the discriminating-set agreement should be read with that offset in mind. " % x,
            "在恒为覆盖的对照集上一致率仅 %.1f%%，说明第二标注者在明确成立的条目上亦系统性偏严，"
            "故判别力集的一致性应结合这一偏移解读。" % x)


def kappa(a, b, weights=None):
    """Cohen's kappa。

    weights=None  → 未加权：配对完全相同记 1，不同记 0。
    weights=True  → 线性加权：配对相同记 1，不同按类别距离线性递减。

    实现要点：未加权不能靠"权重表全 1"来算 —— 那样 obs 会恒等于 1，
    期望一致率也会被算成 1，从而永远返回 κ=1。故未加权走独立分支，
    用精确相等的指示函数。
    """
    cats = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return 0.0, 0.0

    ca = defaultdict(int)
    cb = defaultdict(int)
    for x in a:
        ca[x] += 1
    for y in b:
        cb[y] += 1

    if weights is None:
        # 未加权：一致 = 精确相等
        agree = sum(1 for x, y in zip(a, b) if x == y)
        obs = agree / n
        exp = sum(ca[c] * cb[c] for c in cats) / (n * n)
    else:
        # 线性加权：w[(x,x)]=1，w[(x,y)]=1-|i-j|/(k-1)
        w = {}
        for x in cats:
            for y in cats:
                d = abs(cats.index(x) - cats.index(y))
                w[(x, y)] = 1.0 - d / max(1, len(cats) - 1)
        obs = sum(w[(x, y)] for x, y in zip(a, b)) / n
        exp = sum(w[(x, y)] * ca[x] * cb[y] for x in cats for y in cats) / (n * n)

    if abs(1 - exp) < 1e-12:
        return 1.0, obs
    return (obs - exp) / (1 - exp), obs


def load_sets(form):
    manual = read_json(os.path.join(ROOT, "coverage_manual.json"))
    tpl = read_json(os.path.join(BASE, "labelling_template_discriminating.json"))
    tpl_set = {}
    for r in tpl["rows"]:
        tpl_set[(r["atom_id"], r["model"])] = r["set"]

    disc_a, disc_b = [], []
    ctrl_a, ctrl_b = [], []
    unlabelled = []
    for r in form["rows"]:
        key = (r["atom_id"], r["model"])
        lab = r.get("label")
        if lab in (None, ""):
            unlabelled.append(key)
            continue
        lab = float(lab)
        blk = manual.get(r["model"], {}).get("L1", {})
        prim = None
        for lv in ("L1", "L0"):
            for x in manual.get(r["model"], {}).get(lv, {}).get("rows", []):
                if x["id"] == r["atom_id"]:
                    prim = x["score"]
                    break
            if prim is not None:
                break
        if prim is None:
            continue
        if tpl_set.get(key) == "discriminating":
            disc_a.append(prim)
            disc_b.append(lab)
        else:
            ctrl_a.append(prim)
            ctrl_b.append(lab)
    return (disc_a, disc_b), (ctrl_a, ctrl_b), unlabelled


def main():
    out_dir = BASE
    args = sys.argv[1:]
    if "--out" in args:
        i = args.index("--out")
        out_dir = os.path.join(BASE, args[i + 1])
        args = args[:i] + args[i + 2:]
    if not args:
        print(__doc__)
        sys.exit(1)
    form_path = args[0]
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(BASE, out_dir)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    (da, db), (ca, cb), unlabelled = load_sets(read_json(form_path))

    if unlabelled:
        print("!! 有 %d 个判断未填写，将只对已填写部分计算：" % len(unlabelled))
        for k in unlabelled[:12]:
            print("     %s × %s" % k)
        print()

    res = {}
    if da:
        k_unw, obs_u = kappa(da, db)
        k_lin, obs_l = kappa(da, db, weights=True)
        agree = sum(1 for x, y in zip(da, db) if abs(x - y) < 1e-9)
        res["discriminating"] = {
            "n": len(da), "k_unweighted": round(k_unw, 4), "k_linear": round(k_lin, 4),
            "exact_agreement": round(agree / len(da), 4),
            "primary_mean": round(sum(da) / len(da), 4),
            "secondary_mean": round(sum(db) / len(db), 4),
        }
        print("=== 判别力集（主集）===")
        print("  判断数 %d | 未加权 κ = %.3f | 线性加权 κ = %.3f | 完全一致率 %.1f%%"
              % (len(da), k_unw, k_lin, 100 * agree / len(da)))
    if ca:
        agree = sum(1 for x, y in zip(ca, cb) if abs(x - y) < 1e-9)
        res["control"] = {"n": len(ca), "agreement": round(agree / len(ca), 4)}
        print("=== 对照集（只报一致率，不入主 κ）===")
        print("  判断数 %d | 一致率 %.1f%%" % (len(ca), 100 * agree / len(ca)))
    else:
        res["control"] = {"n": 0, "agreement": None}
        print("=== 对照集：未填写（可选集），已跳过 ===")

    # 分歧清单
    dis = []
    tpl = read_json(os.path.join(BASE, "labelling_template_discriminating.json"))
    idx = {(r["atom_id"], r["model"]): r for r in tpl["rows"]}
    for r in read_json(form_path)["rows"]:
        if r.get("label") in (None, ""):
            continue
        key = (r["atom_id"], r["model"])
        t = idx.get(key)
        if not t:
            continue
        if abs(float(r["label"]) - t["primary_label"]) > 1e-9:
            dis.append({"atom_id": r["atom_id"], "model": r["model"],
                        "primary": float(t["primary_label"]), "secondary": float(r["label"]),
                        "evidence": r.get("evidence", "")})
    res["disagreements"] = dis
    print()
    print("=== 分歧 %d 处 ===" % len(dis))
    for d in dis:
        print("  %-6s x %-5s 主标注 %.1f / 第二标注 %.1f  %s"
              % (d["atom_id"], d["model"], d["primary"], d["secondary"],
                 (d["evidence"] or "")[:60]))

    out = os.path.join(out_dir, "second_rater_results.json")
    io.open(out, "w", encoding="utf-8").write(json.dumps(res, indent=2, ensure_ascii=False))
    print()
    print("已写出 %s" % out)

    # 论文回填句
    if res.get("discriminating"):
        d = res["discriminating"]
        en = ("A second rater independently relabelled the %d discriminating judgements "
              "(the 5 threshold atoms that carry all between-model variation); agreement with the "
              "primary labels was κ = %.3f unweighted (%.3f linearly weighted, %.1f%% exact "
              "agreement)."
              % (d["n"], d["k_unweighted"], d["k_linear"], 100 * d["exact_agreement"]))
        zh = ("第二位标注者独立重标了 %d 个有判别力的判断（承载全部模型间差异的 5 条阈值原子），"
              "与主标注的一致性为未加权 κ = %.3f（线性加权 %.3f，完全一致率 %.1f%%）。"
              % (d["n"], d["k_unweighted"], d["k_linear"], 100 * d["exact_agreement"]))
        ctl = res.get("control", {}).get("agreement")
        en_ctl, zh_ctl = control_clause(ctl)
        if en_ctl:
            en += " " + en_ctl.lstrip()
        zh += zh_ctl
        io.open(os.path.join(out_dir, "paper_patch.md"), "w", encoding="utf-8").write(
            "## 回填论文的句子\n\n**English**\n\n> %s\n\n**中文**\n\n> %s\n" % (en, zh))
        print("已写出 paper_patch.md（可直接粘贴）")


if __name__ == "__main__":
    main()
