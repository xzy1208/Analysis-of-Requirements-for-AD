#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_preview.py —— 把论文 Markdown 渲染为单文件 HTML 预览（内嵌 SVG 图片、表格全部渲染）。

用法：python build_preview.py [输入.md ...]
默认渲染 paper_draft_v2_中文审核版.md 与 paper_draft_v2.md，输出同名 _preview.html。
"""
import base64
import io
import os
import re
import sys

import markdown

BASE = os.path.dirname(os.path.abspath(__file__))

CSS = """
:root {
  --bg: #ffffff; --fg: #1a1a1a; --muted: #5b6470; --line: #d8dee6;
  --accent: #1f5fa9; --code-bg: #f5f7fa; --tbl-head: #eef2f7;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #16181d; --fg: #e8eaed; --muted: #9aa4b2; --line: #333842;
    --accent: #7fb2f0; --code-bg: #1e222a; --tbl-head: #232833;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 40px 24px; background: var(--bg); color: var(--fg);
  font-family: "Georgia", "Times New Roman", "Songti SC", serif;
  font-size: 16px; line-height: 1.75; max-width: 1100px; margin-inline: auto;
}
h1 { font-size: 26px; line-height: 1.35; border-bottom: 2px solid var(--line); padding-bottom: 10px; }
h2 { font-size: 21px; margin-top: 38px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
h3 { font-size: 17px; margin-top: 26px; color: var(--accent); }
h4 { font-size: 15px; margin-top: 20px; }
p { margin: 10px 0; text-align: justify; }
a { color: var(--accent); }
hr { border: none; border-top: 1px solid var(--line); margin: 30px 0; }
code { background: var(--code-bg); padding: 1px 5px; border-radius: 4px;
       font-family: "JetBrains Mono", Consolas, monospace; font-size: 13.5px; }
pre { background: var(--code-bg); padding: 12px 14px; border-radius: 8px; overflow-x: auto;
      border: 1px solid var(--line); }
pre code { background: none; padding: 0; font-size: 13px; line-height: 1.55; }
table { border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 13.5px;
        font-family: "Helvetica Neue", Arial, "PingFang SC", sans-serif; }
th, td { border: 1px solid var(--line); padding: 6px 9px; text-align: left; vertical-align: top; }
th { background: var(--tbl-head); font-weight: 600; }
tr:nth-child(even) td { background: rgba(127,127,127,0.045); }
blockquote { border-left: 3px solid var(--accent); margin: 12px 0; padding: 2px 14px;
             color: var(--muted); }
img, svg { max-width: 100%; height: auto; display: block; margin: 14px auto; }
figure { margin: 18px 0; }
.toc { background: var(--code-bg); border: 1px solid var(--line); border-radius: 8px; padding: 12px 16px; }
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>{css}</style></head>
<body>{body}</body></html>
"""


def inline_images(md_text, base_dir):
    """把图片引用替换为自洽内容，使预览 HTML 单文件可分发。

    - SVG：直接内联 <svg>（保持矢量、可缩放）
    - PNG/JPG：以 base64 data URI 内联
    - 文件不存在：保留原引用（用于占位图）
    """
    def repl(m):
        alt, path = m.group(1), m.group(2)
        fp = os.path.join(base_dir, path)
        if not os.path.exists(fp):
            return m.group(0)          # 占位图等缺失文件：保留原样
        ext = os.path.splitext(path)[1].lower()
        if ext == ".svg":
            svg = io.open(fp, encoding="utf-8-sig").read()
            svg = re.sub(r"<\?xml[^>]*\?>", "", svg).strip()
            # PlantUML/Graphviz 输出的 svg 自带宽高属性，需放开才能自适应容器
            svg = re.sub(r'\s*preserveAspectRatio="none"', "", svg)
            return '<figure><div class="svg-wrap">%s</div><figcaption>%s</figcaption></figure>' % (svg, alt)
        if ext in (".png", ".jpg", ".jpeg"):
            mime = "image/png" if ext == ".png" else "image/jpeg"
            with open(fp, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            return ('<figure><img src="data:%s;base64,%s" alt="%s">'
                    '<figcaption>%s</figcaption></figure>' % (mime, b64, alt, alt))
        return m.group(0)

    # alt 里可能含方括号（如 "[11, Fig. 2]"），因此用非贪婪匹配到最后一个 "](" 之前
    return re.sub(r"!\[(.*?)\]\(([^)\s]+)\)", repl, md_text)


def build(src):
    base = os.path.dirname(os.path.abspath(src))
    md_text = io.open(src, encoding="utf-8").read()
    md_text = inline_images(md_text, base)
    html_body = markdown.markdown(
        md_text, extensions=["tables", "fenced_code", "toc", "sane_lists"])
    title = re.search(r"^#\s+(.*)$", md_text, re.M)
    title = title.group(1) if title else os.path.basename(src)
    out = os.path.splitext(src)[0] + "_preview.html"
    io.open(out, "w", encoding="utf-8").write(
        TEMPLATE.format(title=title, css=CSS, body=html_body,
                        lang="zh" if "中文" in os.path.basename(src) else "en"))
    print("生成:", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        args = [os.path.join(BASE, "paper_draft_v2_中文审核版.md"),
                os.path.join(BASE, "paper_draft_v2.md")]
    for a in args:
        build(a)
