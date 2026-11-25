#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_handover.py —— 生成「发给第二标注者」的独立交付目录。

为什么要有这一步
----------------
工具包目录 `second_annotator_kit/` 里同时放着：
  * 可以发给标注者的：annotator_workbook.md、annotator_form.json
  * **绝对不能发给标注者的**：labelling_template_discriminating.json（含 primary_label，即答案）
    以及上一级目录的 coverage_manual.json（全部主标注）
如果直接把工具包整个目录打包发出去，等于把答案一起寄过去了。

本脚本只把可发材料复制到 `handover/`，并在写出后做**泄题扫描**：
  1. 交付目录内不得出现 "primary_label" 字样；
  2. annotator_form.json 的每行不得含有任何 label 之外的主标注字段；
  3. 所有交付文件不得出现主标注答案的成串序列；
  4. 逐个文件计算 sha256 写入 MANIFEST.txt，便于核对收到的材料是否完整。

用法
----
    python build_handover.py
    # → handover/ 目录，可整体压缩发给标注者
"""
import io
import json
import os
import re
import shutil
import hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
OUT = os.path.join(BASE, "handover")

# 可发给标注者的文件（相对 BASE）
COPY = ["annotator_workbook.md", "annotator_form.json"]

# 交付目录里绝不能出现的词（泄题哨兵）
FORBIDDEN = ["primary_label", "coverage_manual", "labelling_template",
             "second_rater_results", "paper_patch"]

ANNOTATOR_README = r"""# 需求覆盖度第二标注 · 材料说明

感谢帮忙。这批活儿大约 **30–45 分钟**，具体做什么看下面。

---

## 一、你要做什么

判断**若干条需求，在某个模型里有没有被写到**。

每个任务是一对「需求 + 模型」，共 54 个判断：

| 集合 | 数量 | 说明 |
|---|---:|---|
| `discriminating` | 30 | **必做**。承载全部有争议的判断（5 条阈值需求 × 6 个模型） |
| `control` | 24 | 可选，但**建议做**。这批需求在所有模型里都应有覆盖，用来检查你是不是对某类模型一律给「已覆盖」 |

---

## 二、材料

| 文件 | 用途 |
|---|---|
| `annotator_workbook.md` | **工作手册**。评分规则 + 54 张判定卡，每张卡已附好候选条款 |
| `annotator_form.json` | **填答表**。你在 `label` 填分数、在 `evidence` 写一句理由 |

**你不需要通读模型全文** —— 每张判定卡上已经把该模型里与这条需求相关的条款
自动摘好并排好序，直接看卡就行。只有当卡片上的候选明显跑题、而你怀疑模型里
其实有内容时，才需要翻原始产物（手册第四节列了路径）。

---

## 三、评分档位

| 分数 | 含义 | 判据 |
|---|---|---|
| **1** | 覆盖 | 模型里有条款明确表达了这条需求的语义 |
| **0.5** | 部分覆盖 | 模型提到了相关的东西，但缺了关键部分 |
| **0** | 未覆盖 | 模型里找不到对应语义 |

### 规则一（重要）：推导值算不算覆盖

一条需求如果是由另一条需求**推导**出来的，那么当模型只写出了那个推导结果、
没写推导依据时，**算「1」（覆盖）**——只要这个推导关系在该模型里有说明
（追溯表、注释、文档里写过"由 X 推导"即可）。如果没有说明，按「0.5」或「0」处理。

> 这条规则是本次标注的核心分歧点，也是我们最想知道你判断的地方。
> 遇到拿不准的，**按你第一反应的读法填**，并在 evidence 里写明理由。
> 不要迎合任何"标准答案"——我们要的是你的独立判断。

### 规则二：模型自称实现了这条需求

每条需求都给了它在规格里的**来源条款编号**（如 `N-4`、`F3.1`、`R-SCOPE-1`）。
候选条款里凡是带这个编号的行——追溯表里的 `[N-4] …`、文档表格里的 `| N-4 | … |`——
都是**模型自己声明"我实现了这条需求"**。看到这类行时请当作强证据，
但也要核对它下面的载体条款是否真的写出了该需求的语义。

### 规则三：1 与 0.5 的界线 —— 要素分解测试

「明确写出」与「部分写出」的分界不是语气强弱，而是**这条需求的要素有没有被写全**。
每条需求下面都列出了它的要素（要素划分来自规格原文，与任何标注结果无关）。
把要素逐个对到模型条款上：

| 情形 | 分数 |
|---|---|
| 每个要素都在条款里被写出 | **1** |
| 模型触及了这条需求，但至少有一个要素没写出来 | **0.5** |
| 一个要素都没写出来 | **0** |

「被写出」包含两种情形，**都算写出**：
数值/条件直接出现在契约里；或数值/条件出现在追溯表/文档里，且追溯说明写清了它与本需求的对应关系。

「没写出来」有三种典型形态，**都要判 0.5、不判 1**：
只有信号名没有约束；只覆盖一半职责；要素落在别处（由父模块或相邻元素实现）。

> **规则一优先于规则三**：可由推导覆盖、且推导关系有说明的要素即视为"已写出"；
> 规则三只用来判断**要素是否齐全**。
>
> **适用条件与排除条件不计入要素**：需求里"在……情形下""（……除外）"是对要求适用范围的限定，
> 不是模型需要另行编码的断言 —— 模型把这些限定也编码进去反而是过度约束。

---

## 四、怎么填

**推荐填 JSON**（用 VS Code / 任意文本编辑器都行）。在 `annotator_form.json` 里，
每一行的 `label` 填 `1` / `0.5` / `0`，`evidence` 写一句话：

> `evidence` 要指出你依据哪个元素、哪条条款、怎么对应的。
> 例如：`C-F3-4 postcondition 写了 decel_req>=6.0，与 N-3 的 30 km/h 经 A-1 推导对应`

填完把文件改名为 **`annotator_form_filled.json`** 发回即可。

**也可以直接填手册**：在 `annotator_workbook.md` 每张卡的
`→ **label** = \`___\`    **evidence** = ______` 处手写，然后用表格或文字把结果告诉我也行。
（两种都行，填 JSON 更省事。）

---

## 五、纪律

- **不要**去查论文正文、结论表，或任何标注结果文件。
- **提问请在开始前一次性问完**（规格里的缩写、术语含义等），标注过程中不要逐条问。
- 材料里如果出现你觉得**矛盾或说不通**的地方，照实记下来——这本身也是有用的信息。
- 拿不准就照第一反应填，并在 evidence 里写理由。

---

## 六、交回

把填好的 `annotator_form_filled.json` 发回就行。
如果你还写了别的观察（矛盾点、拿不准的地方），一并说明更好。
"""


def sha256(p):
    h = hashlib.sha256()
    with io.open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # ---- 复制可发材料 ----
    for rel in COPY:
        src = os.path.join(BASE, rel)
        if not os.path.exists(src):
            raise SystemExit("缺少 %s，请先跑 build_annotator_workbook.py" % rel)
        shutil.copy2(src, os.path.join(OUT, rel))

    # ⚠️ 填答表必须**强制清空**后再交付。
    # 源文件 annotator_form.json 可能已经被填过（作者自己试填、或上一轮标注残留），
    # 直接复制会把这些打分连同 evidence 一起发给第二标注者 —— 那既不是空白模板，
    # 也等于泄露了别人的判断。交付副本一律清空。
    fp = os.path.join(OUT, "annotator_form.json")
    f = json.load(io.open(fp, encoding="utf-8-sig"))
    cleared = 0
    for r in f["rows"]:
        if r.get("label") not in ("", None) or r.get("evidence"):
            cleared += 1
        r["label"] = ""
        r["evidence"] = ""
    io.open(fp, "w", encoding="utf-8").write(json.dumps(f, indent=2, ensure_ascii=False))
    if cleared:
        print("注意：源填答表中有 %d 行已被填写，交付副本已清空为空白模板。" % cleared)

    io.open(os.path.join(OUT, "给标注者的说明.md"), "w", encoding="utf-8").write(
        ANNOTATOR_README)

    # ---- 填写示例（只含格式示例，不含任何真实判断）----
    form = json.load(io.open(os.path.join(OUT, "annotator_form.json"), encoding="utf-8-sig"))
    ex = json.loads(json.dumps(form))
    ex["_readme"] = ("这是**格式示例**，不是真实判断，仅示范 label 与 evidence 怎么写。"
                     "真实的 54 行里 label 全为空。")
    if ex["rows"]:
        ex["rows"][0]["label"] = "1"
        ex["rows"][0]["evidence"] = "（示例行）F3.1 的 postcondition 写了 ego_state.speed<=130.0，与 N-1 的 130 km/h 上限对应"
    io.open(os.path.join(OUT, "填写示例.json"), "w", encoding="utf-8").write(
        json.dumps(ex, indent=2, ensure_ascii=False))

    # ---- 泄题扫描 ----
    problems = []
    for fn in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, fn)
        try:
            txt = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for w in FORBIDDEN:
            if w in txt:
                # 给标注者的说明里若提到这些词不算泄题（那是在警告不要去看）
                if fn == "给标注者的说明.md" and w in ("coverage_manual",):
                    continue
                problems.append("%s 含禁用词 '%s'" % (fn, w))

    # 表单结构检查：不得有除 label/evidence 之外的答案字段，且 label 必须全空
    f2 = json.load(io.open(os.path.join(OUT, "annotator_form.json"), encoding="utf-8-sig"))
    allowed = {"atom_id", "model", "level", "set", "label", "evidence"}
    for r in f2["rows"]:
        extra = set(r.keys()) - allowed
        if extra:
            problems.append("表单行含额外字段 %s" % sorted(extra))
        if r.get("label") not in ("", None):
            problems.append("表单中 label 非空：%s x %s" % (r["atom_id"], r["model"]))

    # 主标注答案序列不得出现在交付材料里。
    # 注意：「标准答案」一词在手册的纪律段出现是**正常的**（"不必迎合任何标准答案"），
    # 因此只查真正指向答案的标记：primary_label / primary label / 主标注 / 参考答案。
    man_path = os.path.join(ROOT, "coverage_manual.json")
    if os.path.exists(man_path):
        wb = io.open(os.path.join(OUT, "annotator_workbook.md"), encoding="utf-8").read()
        for pat in (r"primary_label", r"primary\s+label", r"主标注", r"参考答案"):
            if re.search(pat, wb):
                problems.append("workbook 出现答案标记 '%s'" % pat)

    if problems:
        print("!! 泄题扫描发现问题，未完成交付：")
        for x in problems:
            print("   -", x)
        raise SystemExit(1)

    # ---- MANIFEST ----
    lines = ["# 交付清单（发给标注者时整个目录一起发）", ""]
    for fn in sorted(os.listdir(OUT)):
        if fn == "MANIFEST.txt":
            continue
        p = os.path.join(OUT, fn)
        lines.append("- `%s`  (%d bytes)  sha256=%s" % (fn, os.path.getsize(p), sha256(p)))
    lines += ["", "生成自 `experiment_kit/second_annotator_kit/build_handover.py`；",
              "泄露检查已通过（表单无预填答案）。"]
    io.open(os.path.join(OUT, "MANIFEST.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print("已生成交付目录：%s" % OUT)
    for fn in sorted(os.listdir(OUT)):
        print("  %-24s %7d bytes" % (fn, os.path.getsize(os.path.join(OUT, fn))))
    print("泄题扫描通过。")


if __name__ == "__main__":
    main()
