# 中文完整使用示范

## 1. 用户请求

```text
请使用 $tech-route-maker，把 examples/academic-paper-demo/brief.md 制作为可编辑的论文方法技术路线图。
```

## 2. 来源与领域确认

Agent 先建立来源清单，只提取源文件明确支持的事实，再用一个组合问题确认尚未确定的交付选项。本案例确认：

- 学科：计算机科学与新能源工程。
- 方向：光伏缺陷检测中的计算机视觉。
- 数据：RGB 与红外多模态图像。
- 方法：深度学习目标检测与特征融合。
- 用途：论文方法图或答辩方法总览。
- 版式：`cn-research-method-matrix`。
- 风格：`research-ppt-blue`。
- 输出：PPTX、SVG、Draw.io、Draw.io XML、Excalidraw、Mermaid、HTML、Markdown、JSON。

## 3. 证据模型

`outputs/tech-route.json` 中每个可见节点都引用 `source_1`，locator 能在 `brief.md` 中找到，来源 SHA-256 同时记录在 `metadata.source_files` 与 `metadata.source_hashes`。推断内容不会计入证据覆盖率。

## 4. 校验与生成

```bash
python -m pip install -e .
trm ingest examples/academic-paper-demo/brief.md --output-dir evidence-pack
trm validate examples/academic-paper-demo/outputs/tech-route.json --strict
trm render examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs --formats pptx,svg,drawio,drawio-code,excalidraw,mermaid,html,markdown,json
python scripts/verify_outputs.py examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs
```

严格校验应显示：领域上下文完整、来源哈希已验证、证据覆盖率 100%、推断覆盖率 0%、无未解决问题。

## 5. 可编辑交付物

- `tech-route.pptx`：PowerPoint/WPS 原生形状。
- `tech-route.svg`：可编辑矢量文字与图形。
- `tech-route.drawio`：可编辑 Draw.io 单元格。
- `tech-route.drawio-code.xml`：可粘贴到 [draw.io](https://app.diagrams.net/) 的 XML。
- `tech-route.excalidraw`：可编辑白板场景。
- `tech-route.mmd`：文本化 Mermaid。
- `tech-route.html`：包含证据信息的网页预览。
- `TECH_ROUTE.md`：文档版本。
- `tech-route.json`：唯一结构源文件。
- `QUALITY_REPORT.md`：质量与人工复核报告。

## 6. 人工二次修改

不能把第一次生成结果不加检查地直接用于投稿、答辩或申报。应在可编辑文件中继续核对术语、事实、证据、路线逻辑、文字长度、字体、颜色、间距和学校或期刊模板要求。
