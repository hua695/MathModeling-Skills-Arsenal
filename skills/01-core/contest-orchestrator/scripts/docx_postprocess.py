# -*- coding: utf-8 -*-
"""docx 后处理：分页、图片居中、三线表和代码字体。"""
from __future__ import annotations

import sys
import re
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def _is_appendix_heading(text: str) -> bool:
    """识别“附录”及其带编号/标题的常见写法。"""
    return text == "附录" or text.startswith("附录")


def _is_appendix_marker(text: str) -> bool:
    """识别 pandoc 丢弃 \\appendix 标记后常见的首个附录标题。"""
    return _is_appendix_heading(text) or text.startswith((
        "支撑材料", "核心源代码", "公式推导", "数据验证", "AI 工具", "代码附录"
    ))


def _looks_like_reference_entry(text: str) -> bool:
    """识别 pandoc 丢失标题后留下的常见参考文献条目。"""
    return bool(re.search(r"\[\d+\]|\[[A-Z]\]|doi\s*:", text, re.IGNORECASE))


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    """Apply deterministic post-processing to one DOCX in place."""
    _configure_utf8_stdio()
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: python docx_postprocess.py <input.docx>", file=sys.stderr)
        return 2

    src = Path(args[0]).expanduser()
    if not src.is_file():
        print(f"Input DOCX not found: {src}", file=sys.stderr)
        return 2

    doc = docx.Document(str(src))
    log: list[str] = []
    appendix_marker_index: int | None = None

    # pandoc 偶尔丢弃“参考文献”标题；在第一条可识别文献前补回标题。
    if not any(p.text.strip().startswith("参考文献") for p in doc.paragraphs):
        for paragraph in doc.paragraphs:
            if _looks_like_reference_entry(paragraph.text.strip()):
                heading = paragraph.insert_paragraph_before("参考文献")
                try:
                    heading.style = "Heading 1"
                except KeyError:
                    pass
                log.append("补插标题: 参考文献")
                break

    # pandoc 还可能丢弃 LaTeX 的 \\appendix 标记；在参考文献之后识别
    # 常见的附录首标题，保证“参考文献”和“附录”之间仍有结构分页。
    reference_index = next(
        (i for i, p in enumerate(doc.paragraphs)
         if p.text.strip().startswith("参考文献")),
        None,
    )
    if reference_index is not None:
        for index, paragraph in enumerate(doc.paragraphs[reference_index + 1:], reference_index + 1):
            if _is_appendix_marker(paragraph.text.strip()):
                appendix_marker_index = index
                break

    # 1) 在关键词、参考文献和附录标题前插入显式分页符。
    targets: list[str] = []
    for index, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if text.startswith("关键词") and "kw" not in targets:
            targets.append("kw")
        elif text.startswith("参考文献") and "ref" not in targets:
            targets.append("ref")
        elif (_is_appendix_heading(text) or index == appendix_marker_index) and "app" not in targets:
            targets.append("app")

    indices: list[int] = []
    for kind in targets:
        for index, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if kind == "kw" and text.startswith("关键词"):
                indices.append(index)
                break
            if kind == "ref" and text.startswith("参考文献"):
                indices.append(index)
                break
            if kind == "app" and (_is_appendix_heading(text) or index == appendix_marker_index):
                indices.append(index)
                break

    for index in sorted(indices, reverse=True):
        paragraph = doc.paragraphs[index]
        run = paragraph.insert_paragraph_before("").add_run("")
        page_break = OxmlElement("w:br")
        page_break.set(qn("w:type"), "page")
        run._r.append(page_break)
        log.append(f"显式分页 @段落{index}: {paragraph.text[:12]}")

    # 2) 摘要与关键词之间保留一个空行。
    for index, paragraph in enumerate(doc.paragraphs):
        if paragraph.text.strip().startswith("关键词"):
            previous = doc.paragraphs[index - 1] if index > 0 else None
            if previous is None or previous.text.strip() != "":
                paragraph.insert_paragraph_before("")
                log.append("空行: 关键词前")
            break

    # 3) 图片和题目居中。
    figure_count = 0
    for paragraph in doc.paragraphs:
        if paragraph._element.findall("." + "//" + qn("w:drawing")):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            figure_count += 1
    if doc.paragraphs and doc.paragraphs[0].text.strip():
        doc.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    log.append(f"图片居中 {figure_count}; 题目居中")

    # 4) 三线表：只保留顶线、底线和表头下线。
    for table in doc.tables:
        properties = table._tbl.tblPr
        alignment = properties.find(qn("w:jc"))
        if alignment is None:
            alignment = OxmlElement("w:jc")
            properties.append(alignment)
        alignment.set(qn("w:val"), "center")
        borders = properties.find(qn("w:tblBorders"))
        if borders is None:
            borders = OxmlElement("w:tblBorders")
            properties.append(borders)
        for side, value, size in (("top", "single", "12"), ("bottom", "single", "12")):
            element = borders.find(qn("w:" + side))
            if element is None:
                element = OxmlElement("w:" + side)
                borders.append(element)
            element.set(qn("w:val"), value)
            element.set(qn("w:sz"), size)
        for side in ("left", "right", "insideH", "insideV"):
            element = borders.find(qn("w:" + side))
            if element is not None:
                borders.remove(element)
        if len(table.rows) > 1:
            for cell in table.rows[0].cells:
                cell_properties = cell._tc.get_or_add_tcPr()
                cell_borders = cell_properties.find(qn("w:tcBorders"))
                if cell_borders is None:
                    cell_borders = OxmlElement("w:tcBorders")
                    cell_properties.append(cell_borders)
                bottom = cell_borders.find(qn("w:bottom"))
                if bottom is None:
                    bottom = OxmlElement("w:bottom")
                    cell_borders.append(bottom)
                bottom.set(qn("w:val"), "single")
                bottom.set(qn("w:sz"), "6")

    # 5) 代码块统一为 Consolas 9pt。
    code_count = 0
    for paragraph in doc.paragraphs:
        if paragraph.style and "Source Code" in paragraph.style.name:
            for run in paragraph.runs:
                run.font.name = "Consolas"
                run.font.size = docx.shared.Pt(9)
                properties = run._element.get_or_add_rPr()
                fonts = properties.find(qn("w:rFonts"))
                if fonts is None:
                    fonts = OxmlElement("w:rFonts")
                    properties.append(fonts)
                fonts.set(qn("w:ascii"), "Consolas")
                fonts.set(qn("w:hAnsi"), "Consolas")
            code_count += 1
    log.append(f"代码 Consolas 9pt: {code_count} 段")

    doc.save(str(src))
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
