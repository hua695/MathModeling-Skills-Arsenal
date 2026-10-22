# 上游模块使用边界

上游模块已本地化为内部参考资源，不作为独立顶层技能自动加载。

| 模块 | 数模模式 |
|---|---|
| `review-chapter` | 可读-only 审阅，允许生成问题报告 |
| `style-check` | 可读-only 结构和风格对标 |
| `terminology` | 可生成术语问题清单，不直接改公式或变量 |
| `consistency` | 可生成一致性报告 |
| `latex-build` | 可编译隔离副本，失败即阻断 |
| `deai` | 只处理普通正文，之后必须运行保护器 |
| `restructure` | 默认只给方案，需用户授权后执行 |
| `formula-compress` | 数模严格模式禁止自动修改 |
| `expand` | 只能根据已有证据扩写，不得编造结果 |
| `thesis-research` | 不替代 `contest-orchestrator` 的文献门禁 |

其他模块仅在用户明确指定且不触碰数学核心时使用。
