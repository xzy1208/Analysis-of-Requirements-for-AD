#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate_cdfd.py —— SOFL CDFD 槽位一致性校验器。

规则（由工具原生产物 System.cdfd.bak_20261117_145538 逆向确认，原生文件 100% 通过）：

  合并 0 基端口索引空间：
    · dataFlow        进程侧 connectorIndex - 1     （connectorIndex 为 1 基）
    · activeDataFlow  进程侧 belongToConnector      （本身即 0 基）
  输入：索引集合必须恰好 == {0 .. inputPorts-1}，且不得重复（一个输入端口只接一条流）
  输出：索引集合必须恰好 == {0 .. outputPorts-1}，允许重复（一个输出端口可承载多条流）

同时校验：
  · <dataFlow> 只允许 fromX/fromY/toX/toY 四个属性（多写 name/type 会导致工具整体加载失败）
  · 所有 belongToName / shapeIndex 都能在 componentList 中找到
  · shapeIndex 全局唯一
  · variableDeclaration 与 <dataStore> 名字逐字一致（对 .fModule）
"""
import io, os, re, sys
import xml.etree.ElementTree as ET


def load(path):
    return ET.fromstring(io.open(path, encoding="utf-8-sig").read())


def validate_cdfd(path):
    errs, warns = [], []
    raw = io.open(path, encoding="utf-8-sig").read()
    root = ET.fromstring(raw)

    # 1. dataFlow 属性白名单
    for tag in re.findall(r"<dataFlow\b[^>]*>", raw):
        extra = set(re.findall(r"([A-Za-z_][\w]*)\s*=", tag)) - {"fromX", "fromY", "toX", "toY"}
        if extra:
            errs.append("dataFlow 含非法属性 %s" % sorted(extra))

    cl = root.find("componentList")
    cn = root.find("connectionList")
    if cl is None or cn is None:
        errs.append("缺少 componentList 或 connectionList")
        return errs, warns

    shapes = {}
    idx = []
    for c in cl:
        si = c.get("shapeIndex")
        idx.append(si)
        shapes[c.get("name")] = (c.tag, si, c)
    dup = [s for s in set(idx) if idx.count(s) > 1]
    if dup:
        errs.append("shapeIndex 重复: %s" % dup)

    procs = {n: v for n, v in shapes.items() if v[0] == "process"}
    ins = {n: [] for n in procs}
    outs = {n: [] for n in procs}

    for c in cn:
        fr, to = c.find("from"), c.find("to")
        if fr is None or to is None:
            errs.append("连接 %s 缺少 from/to" % c.tag)
            continue
        for el, side in ((fr, "from"), (to, "to")):
            nm = el.get("belongToName")
            if nm and nm not in shapes:
                errs.append("%s 侧引用了不存在的组件 %s" % (side, nm))
            si = el.get("shapeIndex")
            if nm and si != "-1" and si not in idx:
                errs.append("%s 侧 shapeIndex=%s 不存在" % (side, si))

        ft, tt = fr.get("belongToType"), to.get("belongToType")
        tn, fn = to.get("belongToName"), fr.get("belongToName")

        if tt == "ProcessTopBottom" and tn in ins:
            ins[tn].append(int(to.get("connectorIndex")) - 1)
        elif tt == "Process" and tn in ins:
            ins[tn].append(int(to.get("belongToConnector")))
        if ft == "ProcessTopBottom" and fn in outs:
            outs[fn].append(int(fr.get("connectorIndex")) - 1)
        elif ft == "Process" and fn in outs:
            outs[fn].append(int(fr.get("belongToConnector")))

    for name, pr in procs.items():
        ip = int(pr[2].get("inputPorts"))
        op = int(pr[2].get("outputPorts"))
        i = ins[name]
        if sorted(i) != list(range(ip)):
            errs.append("%s 输入端口: 实际 %s，期望 %s" % (name, sorted(i), list(range(ip))))
        elif len(set(i)) != len(i):
            errs.append("%s 输入端口有重复索引 %s" % (name, i))
        o = outs[name]
        if sorted(set(o)) != list(range(op)):
            errs.append("%s 输出端口: 实际 %s，期望 %s" % (name, sorted(set(o)), list(range(op))))

    # 变量声明 ↔ dataStore 名字一致
    fmod = os.path.splitext(path)[0] + ".fModule"
    if os.path.exists(fmod):
        fm = io.open(fmod, encoding="utf-8-sig").read()
        m = re.search(r"<variableDeclaration>(.*?)</variableDeclaration>", fm, re.S)
        vars_ = []
        if m:
            vars_ = [l.strip().split(":")[0].strip()
                     for l in m.group(1).splitlines() if ":" in l]
        stores = {n for n, v in shapes.items() if v[0] == "dataStore"}
        miss = stores - set(vars_)
        extra = set(vars_) - stores
        if miss:
            errs.append("dataStore 未在 variableDeclaration 声明: %s" % sorted(miss))
        if extra:
            errs.append("variableDeclaration 声明了不存在的 store: %s" % sorted(extra))
    return errs, warns


def main(paths):
    bad = 0
    for p in paths:
        e, w = validate_cdfd(p)
        tag = "✓" if not e else "✗"
        print("%s %-60s" % (tag, os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p)))
        for x in e:
            print("      - " + x)
            bad += 1
    print("\n不合规项: %d" % bad)
    return bad


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        base = r"C:\Users\zct11\Desktop\Autonomous-driving\bisect"
        args = [os.path.join(base, d, "System.cdfd")
                for d in sorted(os.listdir(base))] + \
               [r"C:\Users\zct11\Desktop\Autonomous-driving\System.cdfd"]
    sys.exit(1 if main(args) else 0)
