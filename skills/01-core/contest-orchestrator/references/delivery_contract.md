# Delivery contract

The canonical command is:

```text
python scripts/delivery_all.py <stable-project-root> --competition guosai --strict
```

The command compiles before selecting a PDF, rejects temporary roots, validates the model/replay artifacts, audits figures and citations, checks PDF text/layout, writes a hash-based manifest, and emits `delivery_all_report.json`.

`FAIL` blocks delivery. In strict mode `WARN` also blocks delivery. A final PDF must be newer than every TeX/BibTeX/image source that can affect it.

When an attached official formatting document conflicts with the generic competition defaults, keep the generic defaults unchanged and provide a project-local YAML/JSON profile via `--gate-config` and `--hard-requirements`. The profiles must be saved with the project and cited in its planning evidence.

严格流程还要求可执行范围计划（如提供）通过摘要和输入门校验；在 `FULL_CONTEST --strict` 下启用逐小问模型证据检查，并在建模章节、源文件版面/引用、附录/代码、匿名和正式交付防漂移检查前运行结构化模型证据图、推导登记表和模型蓝图/符号/接口检查。`delivery_all.py` 将结构化 `[WARN]` 记录归类为 `WARN`；严格模式会阻断这些警告，而不只依赖子进程退出码。仅当项目启用类型化模型蓝图契约时使用 `--blueprint-strict`。只读审计使用 `scripts/audit_project.py`，该脚本在隔离副本中运行且不写入源项目。
