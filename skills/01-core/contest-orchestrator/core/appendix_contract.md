# 附录章节强制门禁（LaTeX）

附录检查以 `scripts/check_latex_appendix_contract.py` 为执行依据。新项目优先使用项目根目录的
`appendix_plan.yaml`（也接受 `.yml`/`.json`），旧项目继续兼容 `appendix_contract.yaml`。
附录计划由子问题的实际能力和真实产物决定，不把代码、原始数据或 A/B/C 内容强制套给所有题型。
严格交付时，已触发的证据类型缺失必须停止，不能由 Agent 凭空编造代码、表格、推导或数值。执行命令为：

```text
python scripts/check_latex_appendix_contract.py <paper-dir> --project-root <project-root> --strict \
  --out <report-dir>/latex_appendix_contract_report.json
```

编译含 `minted` 的论文必须开启 `-shell-escape`，并安装 Pygments。

## 允许内容与边界

程序题采用“双层代码”契约：论文附录展示与每个小问直接相关的核心代码、入口函数和
输入/输出说明；支撑材料包保留能够独立运行的完整源码、数据和批量结果。两层都必须
登记真实路径和对应小问，不得以核心片段代替完整源码包。`source_inputs.appendix_code_mode`
默认为 `core_only`；只有 profile 或项目明确选择 `full_source` 时，才要求论文附录通过
`minted`/`inputminted` 嵌入完整源码。

论文附录还可以包含长推导、代表性数据表、必要补充图表、验证材料、复现命令和支撑材料
文件清单。附录禁止摘要、问题重述、模型核心正文、参考文献、赛题全文、调试日志及
姓名/学校/学号等身份信息。

## 顺序、编号和引用

- `\appendix` 必须位于参考文献之后；A/B/C 仅是竞赛官方格式适配层，编号由
  `official_format.appendix_ids` 或旧契约 `required_appendix_ids` 配置，不代表固定内容。
- 每个项目模块应登记 `kind`、`used_by`、`required`、`source_files` 和正文锚点；混合题按模块并集去重，
  但仍绑定到具体子问题。`source_code` 模块的 `source_files` 表示论文附录中的核心代码文件。
- `source_inputs.core_source_files` 必须是展示在论文附录代码区的核心文件；
  `source_inputs.full_source_files` 是支撑材料包中的完整可运行源文件；
  `source_inputs.support_source_files` 登记完整源码在支撑材料中的对应文件。
- 附录图表使用 `\label{tab:A-1}`、`\label{fig:B-1}` 等标签，不能与正文标签冲突。
- 正文中的“详见附录X/参见附录X”必须能解析到实际附录章节。
- 必须输出支撑材料清单；无程序写“本论文没有用到程序”，无支撑材料写“本论文没有支撑材料”。

正文必须保留核心模型逻辑、关键公式、主要结论、主结果图和结果分析。只有在计划声明
`source_inputs.program_used: false` 时，附录才强制给出“本论文没有用到程序”；没有支撑材料时才要求
“本论文没有支撑材料”。

## 能力驱动模块

常见模块包括 `derivation`、`source_code`、`optimization`、`prediction`、`evaluation`、`simulation`、
`auxiliary_validation`、`raw_data` 和 `interface`。题型 profile 只提供默认能力，最终是否启用模块以
`appendix_plan.yaml` 的子问题 `capabilities`、`appendix_modules` 和 `source_inputs` 为准。

可用 `python scripts/appendix_planner.py <project_root> --out appendix_plan_report.json` 生成只读草稿；
使用 `--write` 才会写入缺失的计划文件，且不会覆盖已有计划。计划处于 `DRAFT` 时不能冒充正式证据，
必须补齐真实路径、锚点和支撑材料后再进入严格交付。

## minted 代码规范

- 所有代码片段只能使用 `minted`；禁止 `verbatim`、`Verbatim`、`lstlisting` 和 `lstinputlisting`。
- 每个代码块必须有 `bgcolor=codebg,linenos,breaklines,tabsize=4,fontsize=\small,framesep=6pt`，
  使用 VS 主题高亮、Consolas 等宽字体；代码块前后使用 `\medskip`，不改变代码块内部行距。
- 不允许 `\normalsize`、`\footnotesize` 或在 `core_only` 模式下把完整工程源码嵌入论文；
  完整源码路径必须登记在 `full_source_files`、`support_source_files` 和支撑材料清单中。
- `core_only` 模式下，每个 `core_source_files` 必须在附录代码区绑定到对应的
  `minted`/`inputminted` 代码块；`full_source` 模式下，每个 `full_source_files` 也必须绑定。
- 代码片段需有简短功能/输入/输出注释，不能出现姓名、学校等身份信息；支撑材料运行结果必须和正文、附录一致。

## 普通文字、数据和推导

- 附录普通文字与正文保持同一行距（国赛常用 1.5 倍）；不通过连续 `\clearpage`/`\newpage` 凑页数。
- 长推导、样本表和计算结果必须与正文一致；大批量原始数据放入支撑材料，不把附录当垃圾桶。

## 自检交付物

检查器报告固定输出：附录顺序、A/B/C 编号、正文引用解析、源码清单、minted 样式、字号与字体、
`\medskip`、数据一致性、支撑材料声明、禁止内容、shell-escape/Pygments 提示共 11 项自检清单。
正文、附录、源文件和 PDF 元数据仍须统一匿名；不得出现内部交付索引。
