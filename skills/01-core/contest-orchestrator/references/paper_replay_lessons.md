# 论文实战复盘：版面与交付门禁

本文件记录已复现、且可以转化为通用门禁的论文问题。它不是论文内容，不应被复制到最终 PDF。

## 已确认的问题

| 问题 | 直接原因 | 应在何处拦截 |
|---|---|---|
| 模板作者占位文字出现在首页 | `\author{...}` 沿用生成器占位值 | P4 占位符 + PDF 视觉检查 |
| “参考文献索引”出现在末页 | 生成器把内部交付说明追加成独立章节 | P4.5 最终 PDF 全文扫描 |
| 长公式越过右边界 | 单行 `\[...\]` 未按可用宽度拆分 | LaTeX warning 检查，正文 overfull 直接 FAIL |
| 修改源文件后旧 PDF 仍被交付 | 只检查单个 tex 会漏掉结果、图片和注册表变化 | delivery manifest 的源文件新鲜度 |
| 附录代码/审计文字误判为正文问题 | 文本检查未区分正文、参考文献和附录 | 结构定位后分级阈值，代码附录单独处理 |
| Windows PowerShell 中文输出乱码 | 脚本沿用系统默认编码输出 | CLI 入口统一重配置 UTF-8，并保留 JSON 报告 |
| 正文页数不足但结构字符比例已通过 | 只看模型章节比例，未在写作阶段检查 PDF 实测正文页数 | 编译后同时跑硬性页数门禁；不足时补真实建模逻辑，禁止空白填充 |
| `[H]` 浮动体造成大面积留白 | 图表被强制固定在当前位置，后续文字被推页 | 源文件层 `check_tex_layout_patterns.py --strict` 拦截 |
| 公式/表格引用漏写 | 只依赖最后一次 XeLaTeX 日志人工发现 | `check_tex_references.py` 展开所有 `input/include` 后提前阻断 |
| 正式交付 PDF 与最新源文件不一致 | 重新编译后只更新论文目录，未同步正式交付目录和索引 | `check_formal_delivery_drift.py --strict` 比对哈希与 `FINAL_INDEX.md` |

## 交付前规则

1. 生成器不得输出模板作者、交付索引、参考文献索引、交付核对清单等内部文字。
2. 必须对最终 PDF 扫描内部交付/占位术语；仅扫描 `.tex` 不足以证明成品安全。
3. 必须读取编译日志中的两种 overfull 格式：`lines N--M` 与 `detected at line N`。
4. 正文 overfull 超过阈值时阻断交付；附录可按独立阈值记录 WARN，但不得掩盖正文越界。
5. PDF 新鲜度必须覆盖 tex、bib、结果 JSON/CSV、图像和图表注册表；报告文件本身不作为源文件。
6. 修复必须修改源头（模板或生成脚本），不能只用 PDF 后处理遮盖问题。

## 验收证据

- `scripts/latex_warning_check.py`：对两种 XeLaTeX/MiKTeX overfull 日志格式有回归测试。
- `scripts/visual_critic.py`：对“参考文献索引”等内部交付文字返回 P0。
- `scripts/delivery_gate.py`：最终 PDF 与 TeX 同时执行 P4.5 内部文字扫描。
- `scripts/delivery_manifest.py`：结果、图像和注册表参与 PDF 新鲜度检查。
