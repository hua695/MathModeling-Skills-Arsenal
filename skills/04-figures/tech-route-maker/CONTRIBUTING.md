# Contributing

Thank you for improving `tech-route-maker`. This repository is both an agent skill and a small rendering toolkit, so changes should preserve agent portability, source traceability, and editable outputs.

## Contribution Areas

Useful contributions include:

- Better layout patterns for academic, engineering, and campaign diagrams.
- New visual styles with accessible color palettes.
- Improvements to PPTX, SVG, Draw.io, Excalidraw, Mermaid, HTML, or Markdown renderers.
- Better validation rules for `tech-route.json`.
- More complete examples for papers, thesis proposals, software projects, and campaign workflows.
- Additional adapter files for other agent environments.

## Development Rules

- Keep `SKILL.md` as the source of truth.
- Keep adapter files short and point them back to `SKILL.md`.
- Preserve editability in generated outputs.
- Do not add proprietary templates, copied online diagrams, or paper-specific facts as reusable assets.
- Keep source evidence and inference markers visible in route models.
- Do not execute third-party project code as part of normal route extraction.

## Local Checks

Run these checks before publishing changes:

```bash
python scripts/validate_route.py examples/academic-paper-demo/outputs/tech-route.json
python scripts/render_all.py examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs --formats pptx,svg,drawio,html,markdown,json
```

Recommended additional check:

```bash
python -c "import pathlib; [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in pathlib.Path('scripts').glob('*.py')]; print('source compile OK')"
```

## Pull Requests

In a pull request, describe:

- What changed.
- Which user workflow it improves.
- Which output formats are affected.
- Which checks were run.
- Any compatibility risk for other agent environments.

---

# 贡献说明

感谢改进 `tech-route-maker`。这个仓库既是一个 agent skill，也是一个轻量渲染工具包，因此修改时需要保留跨 agent 可用性、源材料可追溯性和输出可编辑性。

## 适合贡献的方向

可以贡献：

- 更适合学术、工程或广告活动场景的版式。
- 更好的可访问配色和视觉风格。
- PPTX、SVG、Draw.io、Excalidraw、Mermaid、HTML 或 Markdown 渲染器改进。
- 更完善的 `tech-route.json` 校验规则。
- 面向论文、开题报告、软件项目、广告活动的更多案例。
- 面向其他 agent 环境的适配文件。

## 开发规则

- 保持 `SKILL.md` 为核心说明文件。
- 适配文件保持简短，并指向 `SKILL.md`。
- 保证生成结果可编辑。
- 不把专有模板、网络图或某篇论文的特定事实作为通用资产加入仓库。
- 在路线模型中保留 evidence 和 inference 标记。
- 默认不执行第三方项目代码。

## 本地检查

发布前运行：

```bash
python scripts/validate_route.py examples/academic-paper-demo/outputs/tech-route.json
python scripts/render_all.py examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs --formats pptx,svg,drawio,html,markdown,json
```

建议额外检查：

```bash
python -c "import pathlib; [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in pathlib.Path('scripts').glob('*.py')]; print('source compile OK')"
```

## Pull Request 要说明的内容

请说明：

- 改了什么。
- 改进了哪个用户工作流。
- 影响哪些输出格式。
- 运行了哪些检查。
- 是否影响其他 agent 环境兼容性。
