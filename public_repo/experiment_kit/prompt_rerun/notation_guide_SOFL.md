# SOFL 建模指南（重跑共用，Prompt A / B 唯一差异见各自文件末尾的「附加约束」）

你的任务：为随附的自然语言需求规格 `NL-RQ-ADAS-v1_spec.md` 构建一套 SOFL 形式化规格。
**只建模规格中写明的内容**；规格未提及之处不得发明函数、存储、信号或阈值，
如有必要的设计决定，记入 open-issues 列表。

## 交付物
1. **两个 module**：`ADAS_System`（Level 0，整车级）与 `AEB_Branch`（Level 1，F3 的 AEB 分支细化）。
2. 每个 module 配一张 **CDFD**（条件数据流图）：process、data store、外部终端与数据流连线。
3. 每个 process 在 module 中给出完整契约。

## Module 语法要求
- module head 按端口列出数据流及其类型，格式：
  `( 入1: 类型 | 入2: 类型 ) 出1: 类型 | 出2: 类型, 出2b: 类型`
  （`|` 分端口，同端口多条流用 `,` 分隔；条目为 `名: 类型`）。
- 类型声明用：
  ```
  Name = composed of
      field1: real,
      field2: nat,
      field3: String
  end
  ```
  可嵌套引用其它 composed 类型。
- 每个过程：
  ```
  process 名(入参) out: 出参
  ext rd 存储名 / ext wr 存储名
  pre  <谓词>
  post if <守卫> then <谓词>
  end_process
  ```
- pre/post 中可用的算子：`and`、`=`、`<>`、`>`、`>=`、`<=`、`<`、点号字段访问。
- 不要使用 `or`、`not`、`=>`、量词、`seq of`。
- 数据存储访问：只读用 `ext rd`，会写用 `ext wr`；与 CDFD 中的读写连线一致。

## CDFD 要求
- Level 0 恰好包含规格 §5 的 7 个功能、4 个数据存储（D1–D4）、外部接口（E1–E9），
  不许增删。
- Level 1 恰好细化 F3 的 AEB 分支为 F3.1 → F3.2 → F3.3（规格 §6）。
- 每条数据流两端必须连到已声明的元素；process→store 用读写连线。
- 数据依赖按规格 §5.1 的强制清单连线；`route` 同时供给 F3 与 F5。

## 契约要求（对应规格 §9 R-G-1）
- 每个功能给出：precondition（写明所需数据）、postcondition（写明产出数据）、
  以及至少一条**量化**约束（规格 §7/§8 给了阈值的输出必须落在约束里；
  没有阈值的功能给定性 postcondition）。
- 规范阈值 N-1…N-7 只能取自规格 §7 的表；假设值 A-1…A-7 只能取自 §8。
- 每条 R-xx 要求在模型中可追溯（注明对应子句号）。
