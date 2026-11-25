#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate_sofl_model.py —— SOFL 模型三件套联合校验器

  A. CDFD  结构合法性
  B. Module 语法合法性
  C. CDFD ↔ Module 关联合理性（端口/head 对齐、ext rd/wr 与 store 连线对账、
     pre/post 变量是否有未定义来源、子模块与父模块的引用关系）

用法:
    python validate_sofl_model.py <模块名> [父模块名]
    python validate_sofl_model.py System
    python validate_sofl_model.py BehaviorPlanning System

校验规则全部由工具原生产物逆向确认（System.cdfd.bak_20261117_145538 与
System.fModule.bak_20261117_145538），原生文件 100% 通过。
"""
import io, os, re, sys
import xml.etree.ElementTree as ET

# ── 槽位规则（原生文件逆向确认） ─────────────────────────────────
# 合并 0 基端口索引空间：
#   dataFlow        进程侧 connectorIndex - 1   （connectorIndex 为 1 基）
#   activeDataFlow  进程侧 belongToConnector    （本身即 0 基）
# 输入：索引集合 == {0..inputPorts-1} 且不重复
# 输出：索引集合 == {0..outputPorts-1}，允许重复（一个输出端口可承载多条流）

ALLOWED_OPS = {"=", "<>", ">", ">=", "<", "<="}
FORBIDDEN_WORDS = {"or", "not", "=>", "->", "forall", "exists", "seq of", "set of",
                   "while", "else", "let", "in", "null"}
FIELD_TYPES = {"real", "nat", "String"}

# store → 该 store 所承载的数据项名称（沿用被 store 读流取代的那些边界 activeDataFlow 命名）
STORE_DATA_NAME = {
    "HD_Map_DB": "map_data",
    "Object_Track_DB": "objects",
    "Ego_State_DB": "ego_state",
    "Traffic_Rules_DB": "traffic_rules",
}

SECTIONS = ["constantDeclaration", "typeDeclaration", "variableDeclaration",
            "typeAndStateInvariants", "moduleDecom", "processList", "functions"]


class Report:
    def __init__(self, tag):
        self.tag = tag
        self.err = []
        self.warn = []
        self.info = []

    def e(self, m): self.err.append(m)
    def w(self, m): self.warn.append(m)
    def i(self, m): self.info.append(m)

    def show(self):
        print("=" * 74)
        print(self.tag)
        print("=" * 74)
        for x in self.info:
            print("   · " + x)
        if self.err:
            print("   ── 错误 ──")
            for x in self.err:
                print("   ✗ " + x)
        if self.warn:
            print("   ── 警告 ──")
            for x in self.warn:
                print("   ! " + x)
        if not self.err and not self.warn:
            print("   ✓ 全部通过")
        print()


# ── 解析 head ─────────────────────────────────────────────────────
def parse_head(h):
    """'(in1: T | in2: T )out1: T | out2: T, out2: T' → (inputs, outputs)
       inputs : [(name, type), ...]
       outputs: [[ (name,type), ... ], ...]   每个元素是一个输出端口（可承载多条流）"""
    h = h.strip()
    if not h.startswith("("):
        return None, None
    close = h.find(")")
    if close < 0:
        return None, None
    in_txt, out_txt = h[1:close], h[close + 1:]

    def item(t):
        t = t.strip()
        if ":" in t:
            n, ty = t.split(":", 1)
            return n.strip(), ty.strip()
        return t, ""

    inputs = [item(x) for x in in_txt.split("|")] if in_txt.strip() else []
    ports = []
    for seg in out_txt.split("|"):
        flows = [item(x) for x in seg.split(",") if x.strip()]
        if flows:
            ports.append(flows)
    return inputs, ports


def load(path):
    return io.open(path, encoding="utf-8-sig").read()


# ── A. CDFD ───────────────────────────────────────────────────────
def check_cdfd(path, rep):
    raw = load(path)
    if not raw.startswith("<?xml"):
        rep.e("缺少 XML 声明")
    with open(path, "rb") as f:
        if f.read(3) != b"\xef\xbb\xbf":
            rep.w("文件缺少 UTF-8 BOM（工具原生文件均带 BOM）")
    try:
        root = ET.fromstring(raw)
    except Exception as ex:
        rep.e("XML 解析失败: %s" % ex)
        return None, None

    for tag in re.findall(r"<dataFlow\b[^>]*>", raw):
        extra = set(re.findall(r"([A-Za-z_][\w]*)\s*=", tag)) - {"fromX", "fromY", "toX", "toY"}
        if extra:
            rep.e("dataFlow 含非法属性 %s —— 工具会因此拒绝整个文件（导致连线全没）" % sorted(extra))

    cl, cn = root.find("componentList"), root.find("connectionList")
    if cl is None or cn is None:
        rep.e("缺少 componentList / connectionList")
        return None, None

    shapes, idx = {}, []
    for c in cl:
        si = c.get("shapeIndex")
        idx.append(si)
        shapes[c.get("name")] = (c.tag, si, c)
    dup = sorted({s for s in idx if idx.count(s) > 1})
    if dup:
        rep.e("shapeIndex 重复: %s" % dup)
    procs = {n: v[2] for n, v in shapes.items() if v[0] == "process"}
    stores = {n: v[2] for n, v in shapes.items() if v[0] == "dataStore"}
    nos = [s.get("no") for s in stores.values()]
    if len(set(nos)) != len(nos):
        rep.e("dataStore 的 no 编号重复: %s" % nos)

    ins, outs = {n: [] for n in procs}, {n: [] for n in procs}
    for c in cn:
        fr, to = c.find("from"), c.find("to")
        if fr is None or to is None:
            rep.e("连接 <%s> 缺少 from/to 子元素" % c.tag)
            continue
        for el, side in ((fr, "from"), (to, "to")):
            nm, si = el.get("belongToName"), el.get("shapeIndex")
            if nm and nm not in shapes:
                rep.e("%s 侧引用了不存在的组件 %r" % (side, nm))
            if nm and si != "-1" and si not in idx:
                rep.e("%s 侧 shapeIndex=%s 不存在" % (side, si))
        ft, tt = fr.get("belongToType"), to.get("belongToType")
        tn, fn = to.get("belongToName"), fr.get("belongToName")
        if tt == "ProcessTopBottom" and tn in ins:
            ins[tn].append(("read", int(to.get("connectorIndex")) - 1, fr.get("belongToName")))
        elif tt == "Process" and tn in ins:
            # store 读也可以走编号端口（activeDataFlow 从 DataStore 出发）：
            # 这类按 "read" 归类，端口号取 belongToConnector（0 基），与 dataFlow 的
            # connectorIndex-1 落在同一槽位空间。
            if ft == "DataStore" and fn in stores:
                ins[tn].append(("read", int(to.get("belongToConnector")), fn))
            else:
                ins[tn].append(("active", int(to.get("belongToConnector")), c.get("name")))
        if ft == "ProcessTopBottom" and fn in outs:
            outs[fn].append(("write", int(fr.get("connectorIndex")) - 1, to.get("belongToName")))
        elif ft == "Process" and fn in outs:
            # store 写也可以走编号输出端口（dataFlow 从进程出发、目标是 DataStore）
            if tt == "DataStore" and tn in stores:
                outs[fn].append(("write", int(fr.get("belongToConnector")), tn))
            else:
                outs[fn].append(("active", int(fr.get("belongToConnector")), c.get("name")))

    for name, pr in procs.items():
        ip, op = int(pr.get("inputPorts")), int(pr.get("outputPorts"))
        i = sorted(x[1] for x in ins[name])
        if i != list(range(ip)):
            rep.e("%s 输入端口索引 %s，应为 %s" % (name, i, list(range(ip))))
        elif len({x[1] for x in ins[name]}) != len(i):
            rep.e("%s 输入端口索引重复 %s" % (name, i))
        o = sorted({x[1] for x in outs[name]})
        if o != list(range(op)):
            rep.e("%s 输出端口索引 %s，应为 %s" % (name, o, list(range(op))))
    rep.i("CDFD：%d 个 process / %d 个 dataStore / %d 条连接（dataFlow %d + activeDataFlow %d）"
          % (len(procs), len(stores), len(list(cn)),
             len(re.findall(r"<dataFlow\b", raw)), len(re.findall(r"<activeDataFlow\b", raw))))
    return (procs, stores, ins, outs), root


# ── B. Module ─────────────────────────────────────────────────────
def check_module(path, rep):
    raw = load(path)
    try:
        root = ET.fromstring(raw)
    except Exception as ex:
        rep.e("XML 解析失败: %s" % ex)
        return None
    names = [c.tag for c in root]
    if names != SECTIONS:
        rep.e("模块段顺序/集合不符: %s（应为 %s）" % (names, SECTIONS))

    # 类型声明
    types, fieldnames = {}, set()
    td = root.findtext("typeDeclaration") or ""
    for blk in re.findall(r"(\w+)\s*=\s*composed of(.*?)\bend\b", td, re.S):
        tname, body = blk[0], blk[1]
        if tname in types:
            rep.e("类型 %s 重复声明" % tname)
        fields = {}
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" not in line:
                rep.e("类型 %s 的字段 %r 缺少 ': 类型'" % (tname, line))
                continue
            fn, fty = [x.strip() for x in line.split(":", 1)]
            if fty not in FIELD_TYPES:
                rep.e("类型 %s 字段 %s 的类型 %r 非法（只允许 real/nat/String）" % (tname, fn, fty))
            fields[fn] = fty
            fieldnames.add(fn)
        types[tname] = fields
    for t in re.findall(r"(\w+)\s*=\s*composed of", td):
        if t not in types:
            rep.e("类型 %s 未正常闭合（缺 end）" % t)

    # 变量声明
    vars_ = {}
    for line in (root.findtext("variableDeclaration") or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            rep.e("变量声明 %r 缺少 ': 类型'" % line)
            continue
        v, ty = [x.strip() for x in line.split(":", 1)]
        vars_[v] = ty
        if ty and ty not in types:
            rep.e("变量 %s 的类型 %r 未在 typeDeclaration 中声明" % (v, ty))
    rep.i("Module：%d 个复合类型 / %d 个变量声明 / 类型字段共 %d 个"
          % (len(types), len(vars_), len(fieldnames)))
    return {"types": types, "vars": vars_, "fields": fieldnames, "root": root, "raw": raw}


# ── C. 关联合理性 ────────────────────────────────────────────────
def check_association(cdfd, mod, rep, parent=None, parent_cdfd=None):
    procs, stores, ins, outs = cdfd
    mprocs = {}
    for p in mod["root"].find("processList"):
        mprocs[p.get("name")] = p

    if set(procs) != set(mprocs):
        rep.e("process 集合不一致: 仅 CDFD 有 %s / 仅 Module 有 %s"
              % (sorted(set(procs) - set(mprocs)), sorted(set(mprocs) - set(procs))))
    for n in sorted(set(procs) & set(mprocs)):
        if n != n.strip():
            rep.e("process 名 %r 含首尾空格，CDFD 与 Module 需逐字一致" % n)

    for name in sorted(set(procs) & set(mprocs)):
        pr, mp = procs[name], mprocs[name]
        ip, op = int(pr.get("inputPorts")), int(pr.get("outputPorts"))
        hi, ho = parse_head(mp.get("head"))
        if hi is None:
            rep.e("%s 的 head 无法解析: %r" % (name, mp.get("head")))
            continue
        if len(hi) != ip:
            rep.e("%s head 输入项 %d 个，CDFD inputPorts=%d" % (name, len(hi), ip))
        nports = len(ho)
        if nports != op:
            rep.e("%s head 输出端口 %d 个，CDFD outputPorts=%d" % (name, nports, op))

        # 输入名与顺序
        exp_in = []
        for kind, slot, nm in sorted(ins[name], key=lambda x: x[1]):
            if kind == "read":
                exp_in.append(STORE_DATA_NAME.get(nm, nm))
            else:
                exp_in.append(nm)
        act_in = [x[0] for x in hi]
        if act_in != exp_in:
            rep.e("%s head 输入名/顺序 %s 与 CDFD 槽位推导 %s 不一致" % (name, act_in, exp_in))

        # 输出端口与流
        exp_out = {}
        for kind, slot, nm in outs[name]:
            key = STORE_DATA_NAME.get(nm, nm) if kind == "write" else nm
            exp_out.setdefault(slot, []).append(key)
        got_out = []
        for port in ho:
            got_out.append([x[0] for x in port])
        if got_out != [exp_out.get(i, []) for i in range(op)]:
            rep.e("%s head 输出流 %s 与 CDFD 推导 %s 不一致"
                  % (name, got_out, [exp_out.get(i, []) for i in range(op)]))

        # ext rd / ext wr 与 store 连线对账
        txt = mp.text or ""
        for c in mp:
            txt += (c.text or "") + "\n" + (c.tail or "")
        ext_rd = set(re.findall(r"ext rd (\w+)", txt))
        ext_wr = set(re.findall(r"ext wr (\w+)", txt))
        rd_stores = {nm for kind, slot, nm in ins[name] if kind == "read"}
        wr_stores = {nm for kind, slot, nm in outs[name] if kind == "write"}
        if ext_rd != rd_stores:
            rep.e("%s ext rd %s 与 CDFD 的 store 读连接 %s 不一致" % (name, sorted(ext_rd), sorted(rd_stores)))
        if ext_wr != wr_stores:
            rep.e("%s ext wr %s 与 CDFD 的 store 写连接 %s 不一致" % (name, sorted(ext_wr), sorted(wr_stores)))

        # pre / post 变量来源
        allowed = ({x[0] for x in hi} | {x[0] for p2 in ho for x in p2} | ext_rd | ext_wr)
        used = set()
        for line in txt.splitlines():
            line = line.strip()
            if not (line.startswith("pre ") or line.startswith("if ") or line.startswith("then ")):
                continue
            for base in re.findall(r"\b([A-Za-z_]\w*)\s*\.", line):
                used.add(base)
            body = re.sub(r"[A-Za-z_]\w*\s*\.\s*[A-Za-z_]\w*", " ", line)
            for tok in re.findall(r"\b[A-Za-z_]\w*\b", body):
                if tok in ("pre", "post", "if", "then", "true", "and"):
                    continue
                used.add(tok)
        dangling = sorted(used - allowed - mod["fields"])
        if dangling:
            rep.e("%s 的 pre/post 引用了未定义来源的变量: %s" % (name, dangling))
        if not re.search(r"^\s*pre \S", txt, re.M):
            rep.e("%s 缺少 pre 条件" % name)
        if not re.search(r"^\s*post\s*$", txt, re.M):
            rep.e("%s 缺少 post 条件" % name)

    # store ↔ variableDeclaration
    vs = set(mod["vars"])
    ss = set(stores)
    if vs != ss:
        rep.e("variableDeclaration %s 与 CDFD 的 dataStore %s 不一致" % (sorted(vs), sorted(ss)))

    # 表达式算子白名单
    for pat, desc in [(r"\bor\b", "or"), (r"\bnot\b", "not"), (r"=>", "=>"), (r"\bnull\b", "null"),
                      (r"\bforall\b", "forall"), (r"\bexists\b", "exists"), (r"\bseq of\b", "seq of")]:
        if re.search(pat, mod["raw"]):
            rep.e("规格中出现不支持的记号 %r" % desc)

    # 子模块与父模块关系
    dec = (mod["root"].findtext("moduleDecom") or "").strip()
    if parent:
        if dec != parent:
            rep.e("子模块 moduleDecom=%r，应为父模块名 %r" % (dec, parent))
        if mod["vars"]:
            rep.w("子模块声明了 %s —— 父 store 由子模块逻辑引用，不应重复声明" % sorted(mod["vars"]))
        if stores:
            rep.w("子模块 CDFD 出现了 %d 个 dataStore —— 子图不应重复父 store" % len(stores))
    else:
        if dec:
            rep.w("根模块 moduleDecom 非空（%r）" % dec)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    # 默认校验本仓库 models/M1_manual_human/ 下的产物（工具工程目录会随人工
    # 建模进度被覆盖，当前装的是 M1.1；要校验 M1.1 用 SOFL_BASE 显式指定
    # models/M1_1_manual_plus_thresholds/）
    base = os.environ.get("SOFL_BASE",
                           os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "models", "M1_manual_human"))
    name, parent = args[0], (args[1] if len(args) > 1 else None)
    cdfd_p = os.path.join(base, name + ".cdfd")
    fm_p = os.path.join(base, name + ".fModule")
    rep = Report("SOFL 模型校验：%s%s" % (name, "（父模块 %s）" % parent if parent else ""))
    if not os.path.exists(cdfd_p):
        rep.e("找不到 %s" % cdfd_p); rep.show(); return 1
    if not os.path.exists(fm_p):
        rep.e("找不到 %s" % fm_p); rep.show(); return 1
    c, _ = check_cdfd(cdfd_p, rep)
    m = check_module(fm_p, rep)
    if c and m:
        check_association(c, m, rep, parent=parent)
    rep.show()
    return 1 if rep.err else 0


if __name__ == "__main__":
    sys.exit(main())
