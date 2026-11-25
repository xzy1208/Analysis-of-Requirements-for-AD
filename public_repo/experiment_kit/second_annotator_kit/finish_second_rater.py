#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
finish_second_rater.py —— 第二标注者材料收回后的完整流程入口。

用法
----
    python finish_second_rater.py <annotator_form_filled.json>            # 演练
    python finish_second_rater.py <annotator_form_filled.json> --apply    # 写入论文

流程
----
    1. finalize_second_rater.py  → κ、一致率、分歧清单、second_rater_results.json
    2. apply_second_rater_to_paper.py → 中英两版六处改写（Threat 4 / §V-A2 / 附录表）
    3. check_citations.py --both → 引用完整性复核（改稿后必查）

铁律：默认**只演练不写盘**。加 --apply 才改论文。
      第 2 步内部对每个替换断言命中数恰为 1，命中数不符即报错、不写文件。
"""
import io
import os
import subprocess
import sys

BASE = r"C:\Users\zct11\WorkBuddy\2026-11-11-20-16-46"
KIT = os.path.join(BASE, "experiment_kit", "second_annotator_kit")
PY = sys.executable


def run(cmd, cwd=BASE, title=""):
    if title:
        print("\n" + "=" * 74)
        print(">> " + title)
        print("=" * 74)
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    sys.stdout.write(r.stdout or "")
    if r.stderr:
        sys.stderr.write(r.stderr)
    return r.returncode


def main():
    args = [a for a in sys.argv[1:] if a != "--apply"]
    apply = "--apply" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(1)
    filled = args[0]
    if not os.path.isabs(filled):
        filled = os.path.join(BASE, filled)
    if not os.path.exists(filled):
        raise SystemExit("找不到 %s" % filled)

    print("填答表：%s" % filled)
    print("模式：%s" % ("**写入论文**" if apply else "演练（不改论文）"))

    # 1. κ
    rc = run([PY, os.path.join(KIT, "finalize_second_rater.py"), filled],
             cwd=KIT, title="步骤 1/3  计算 κ 与分歧清单")
    if rc != 0:
        sys.exit(rc)

    # 2. 回填论文
    cmd = [PY, os.path.join(BASE, "apply_second_rater_to_paper.py")]
    if apply:
        cmd.append("--apply")
    rc = run(cmd, cwd=BASE, title="步骤 2/3  回填论文（中英两版六处）")
    if rc != 0:
        print("\n!! 回填失败，论文未改动。")
        sys.exit(rc)

    # 3. 引用完整性
    rc = run([PY, os.path.join(BASE, "check_citations.py"), "--both"],
             cwd=BASE, title="步骤 3/3  引用完整性复核")
    if rc != 0:
        print("\n!! 引用完整性有问题，请检查。")
        sys.exit(rc)

    print("\n" + "=" * 74)
    if apply:
        print("全部完成：κ 已算出，论文中英两版已更新，引用完整性全绿。")
        print("请再通读一遍 Threat 4 段落（中英各一），确认措辞与实测数值相符。")
    else:
        print("演练完成，未改动任何文件。确认无误后加 --apply 重跑。")
    print("=" * 74)


if __name__ == "__main__":
    main()
