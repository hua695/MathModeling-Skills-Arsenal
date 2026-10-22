# Team Interface（与编程手的分工协议）

## 目录协议
```
/项目
  /data  raw.csv clean.csv
  /model model.py params.json
  /result table.csv figure/
  /paper main.md appendix.md reference.bib
  /checkpoint state.json
  /log decision_current.md
  /registry variable_registry.json formula_registry.json figure_registry.json
  report.md
```

## registry（⭐ 解决"同一变量三个名字"事故）
```
variable_registry.json:
  { "γ*": {"code": "gamma_star", "paper": "γ*", "table": "γ*"}, ... }

formula_registry.json:  公式编号 ↔ 含义 ↔ 代码实现
figure_registry.json:   图号 ↔ caption ↔ 数据源JSON
```
用途：正文/附录/代码/表格引用同一符号，杜绝"γ 叫 gamma、代码叫 g、表叫 rate"。

## param_changelog
任何参数变更，编程手必须记录，论文手回执确认，并同步 registry。

## 其他
- 结果/布局 schema 定死。
- 单一版本控制：旧版进归档不删除。
- 同步点：每半天。
