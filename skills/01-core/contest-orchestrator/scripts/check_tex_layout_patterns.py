#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detect source-level LaTeX patterns that commonly create sparse pages."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def locate_tex(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = sorted(path.glob("paper*.tex")) or sorted(path.glob("*.tex"))
    if not candidates:
        raise FileNotFoundError(f"未找到 TeX 文件: {path}")
    return candidates[0]


def expand_inputs(text: str, base: Path, seen: set[Path] | None = None) -> str:
    """Inline local inputs so layout checks cover split chapter files."""
    seen = set() if seen is None else seen
    pattern = re.compile(r"\\(?:input|include)\{([^{}]+)\}")

    def replace(match: re.Match[str]) -> str:
        candidate = (base / match.group(1).strip())
        if not candidate.suffix:
            candidate = candidate.with_suffix(".tex")
        candidate = candidate.resolve()
        if candidate in seen or not candidate.is_file():
            return match.group(0)
        seen.add(candidate)
        return expand_inputs(candidate.read_text(encoding="utf-8", errors="replace"), candidate.parent, seen)

    return pattern.sub(replace, text)


def uncomment(text: str) -> str:
    return re.sub(r"(?m)(?<!\\)%.*$", "", text)


COMMAND_DEFINITION_RE = re.compile(
    r"\\(?:NewDocumentCommand|RenewDocumentCommand|DeclareDocumentCommand|"
    r"newcommand|renewcommand|providecommand)\*?\b"
)


def _matching_group_end(text: str, opening: int) -> int | None:
    """Return the closing brace for a TeX group, preserving source offsets."""
    depth = 0
    index = opening
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _skip_optional_argument(text: str, index: int) -> int:
    """Skip a simple bracketed optional argument after a command definition."""
    if index >= len(text) or text[index] != "[":
        return index
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return index


def mask_command_definitions(text: str) -> str:
    """Mask LaTeX command-definition bodies before scanning正文浮动体.

    Layout macros legitimately contain figure environments and SVG calls. They
    are implementation code, not paper content, so keeping their newlines but
    masking their characters prevents false positives while preserving line
    numbers for real正文 issues.
    """
    masked = list(text)
    for match in COMMAND_DEFINITION_RE.finditer(text):
        command = match.group(0).lower()
        index = match.end()
        groups: list[tuple[int, int]] = []
        while index < len(text) and len(groups) < 3:
            while index < len(text) and text[index].isspace():
                index += 1
            index = _skip_optional_argument(text, index)
            while index < len(text) and text[index].isspace():
                index += 1
            if index >= len(text) or text[index] != "{":
                break
            end = _matching_group_end(text, index)
            if end is None:
                break
            groups.append((index, end))
            index = end + 1

        required_groups = 3 if "documentcommand" in command else 2
        if len(groups) != required_groups:
            continue
        body_end = groups[-1][1]
        for position in range(match.start(), body_end + 1):
            if masked[position] != "\n":
                masked[position] = " "
    return "".join(masked)


def line_no(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


LAYOUT_COMMANDS = {
    "PaperFigure": "single",
    "PaperTwoColumn": "side_by_side",
    "PaperWrapFigure": "wrap_short",
    "PaperTallFigure": "tall_constrained",
}


def _length_fraction(value: str, unit: str) -> float | None:
    match = re.fullmatch(
        rf"\s*(0?(?:\.\d+)|1(?:\.0+)?)\s*\\{unit}\s*", value, re.I
    )
    return float(match.group(1)) if match else None


def check(text: str) -> dict:
    source = mask_command_definitions(uncomment(text))
    issues: list[dict] = []
    warnings: list[dict] = []
    layout_modes = {mode: 0 for mode in set(LAYOUT_COMMANDS.values())}

    layout_command_re = re.compile(r"\\(PaperFigure|PaperTwoColumn|PaperWrapFigure|PaperTallFigure)\b")
    for match in layout_command_re.finditer(source):
        layout_modes[LAYOUT_COMMANDS[match.group(1)]] += 1

    raw_image_re = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\s*\{([^{}]+)\}", re.I)
    for match in raw_image_re.finditer(source):
        issues.append({
            "kind": "raw_image_insert",
            "line": line_no(source, match.start()),
            "message": "正文图片必须使用 SVG 路线和 \\includesvg，不得直接使用 \\includegraphics。",
        })

    svg_re = re.compile(r"\\includesvg(?:\[[^\]]*\])?\s*\{([^{}]+)\}", re.I)
    for match in svg_re.finditer(source):
        image_path = match.group(1).strip().lower()
        if image_path.endswith((".png", ".pdf", ".jpg", ".jpeg", ".eps", ".tif", ".tiff")):
            issues.append({
                "kind": "svg_wrong_argument",
                "line": line_no(source, match.start()),
                "message": "\\includesvg 的路径应省略扩展名并指向 SVG 资产，不得传入 PNG/PDF 等图片扩展名。",
            })

    svg_options_re = re.compile(r"\\includesvg\[(?P<options>[^\]]*)\]\s*\{", re.I)
    for match in svg_options_re.finditer(source):
        options = match.group("options")
        option_map = {}
        for part in options.split(","):
            if "=" in part:
                name, value = part.split("=", 1)
                option_map[name.strip().lower()] = value.strip()
        width = option_map.get("width")
        width_fraction = _length_fraction(width, "textwidth") if width else None
        if width and (width.lower() == r"\textwidth" or (width_fraction is not None and width_fraction > 0.85)):
            issues.append({
                "kind": "svg_width_unconstrained",
                "line": line_no(source, match.start()),
                "message": "SVG 宽度不得铺满或超过 0.85\\textwidth；使用受控版面宏或缩小后再排版。",
            })
        height = option_map.get("height")
        height_fraction = _length_fraction(height, "textheight") if height else None
        if height and (height.lower() == r"\textheight" or (height_fraction is not None and height_fraction > 0.4)):
            issues.append({
                "kind": "svg_height_unconstrained",
                "line": line_no(source, match.start()),
                "message": "SVG 高度不得超过 0.4\\textheight；使用 PaperTallFigure 或拆分图形。",
            })

    hard_float = re.compile(r"\\begin\{(?:figure|table)\}\s*\[H\]", re.I)
    for match in hard_float.finditer(source):
        issues.append({
            "kind": "hard_float",
            "line": line_no(source, match.start()),
            "message": "正文图表使用 [H]，可能把后续内容强制推到下一页；优先使用 [!htbp] 并通过尺寸/结构修复版面。",
        })

    page_break = r"\\(?:clearpage|newpage|pagebreak(?:\s*\[[^]]+\])?)"
    consecutive = re.compile(page_break + r"\s*" + page_break, re.I | re.S)
    for match in consecutive.finditer(source):
        issues.append({
            "kind": "consecutive_page_break",
            "line": line_no(source, match.start()),
            "message": "检测到连续强制分页；这通常会制造空白页或不必要留白。",
        })

    manual_space = re.compile(r"\\vspace\*?\{\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|in|pt)\s*\}", re.I)
    for match in manual_space.finditer(source):
        value, unit = float(match.group(1)), match.group(2).lower()
        points = value * {"cm": 28.3465, "mm": 2.83465, "in": 72.0, "pt": 1.0}[unit]
        if points >= 24:
            warnings.append({
                "kind": "large_manual_space",
                "line": line_no(source, match.start()),
                "message": f"检测到约 {points:.1f}pt 的手工垂直留白；确认不是用于凑页数。",
            })

    # 附录位置：附录中的图不受"图前引出/图后解释"强制约束
    appendix_match = re.search(r"\\appendix", source, re.I)
    appendix_pos = appendix_match.start() if appendix_match else -1

    def in_appendix(pos: int) -> bool:
        return appendix_pos != -1 and pos > appendix_pos

    # 浮动体开始/结束位置
    float_start_re = re.compile(r"\\begin\{(?:figure|table)\}", re.I)
    float_end_re = re.compile(r"\\end\{(?:figure|table)\}", re.I)
    float_starts = list(float_start_re.finditer(source))
    float_ends = list(float_end_re.finditer(source))

    # 4. 连续浮动体检测：两个浮动体之间无正文段落
    for i in range(len(float_starts) - 1):
        # 找到前一个浮动体的结束位置
        prev_end = None
        for fe in float_ends:
            if fe.start() > float_starts[i].start():
                prev_end = fe
                break
        if not prev_end:
            continue
        between = source[prev_end.end():float_starts[i + 1].start()]
        # 中间只有空白、注释、\label、\caption等，无正文文字（中文或3个以上英文字母）
        if not re.search(r"[\u4e00-\u9fff]|[a-zA-Z]{3,}", between):
            issues.append({
                "kind": "consecutive_floats",
                "line": line_no(source, float_starts[i + 1].start()),
                "message": "检测到连续浮动体，中间缺少正文段落；图片堆在一起会导致论证断裂，请在两图之间加过渡文字。",
            })

    # 5. 图前无引出检测（附录除外）
    intro_re = re.compile(r"\\ref\{|\\cref\{|如图|见图|图\\?ref|图\\?cref|所示|见表|如表|给出|如下图|如上图|结果图", re.I)
    for match in float_starts:
        if in_appendix(match.start()):
            continue
        # 向前找最近的非空非注释行
        pos = match.start()
        line_start = source.rfind("\n", 0, pos) + 1
        prev_line_end = line_start - 1
        prev_line = ""
        while prev_line_end > 0:
            prev_line_start = source.rfind("\n", 0, prev_line_end) + 1
            candidate = source[prev_line_start:prev_line_end].strip()
            if candidate and not candidate.startswith("%"):
                prev_line = candidate
                break
            prev_line_end = prev_line_start - 1
        if prev_line and not intro_re.search(prev_line):
            issues.append({
                "kind": "figure_no_intro",
                "line": line_no(source, match.start()),
                "message": "图前缺少引出句；读者不知道为什么出现这张图。请在图前加'如图X所示'或\\ref/\\cref引用。",
            })

    # 6. 图后无解释检测（附录除外，连续浮动体已被上一项检测）
    section_re = re.compile(r"\\(?:section|subsection|subsubsection|chapter)\*?\{", re.I)
    for i, match in enumerate(float_ends):
        if in_appendix(match.start()):
            continue
        # 检查下一个是否是浮动体开始（若是则跳过，连续浮动体已检测）
        next_float = float_start_re.search(source, match.end())
        next_section = section_re.search(source, match.end())
        if next_float and (not next_section or next_float.start() < next_section.start()):
            continue
        # 向后找直到下一个\section或文档结束
        if next_section:
            between = source[match.end():next_section.start()]
        else:
            between = source[match.end():]
        if not re.search(r"[\u4e00-\u9fff]|[a-zA-Z]{3,}", between):
            issues.append({
                "kind": "figure_no_explanation",
                "line": line_no(source, match.start()),
                "message": "图后缺少解释句；图片成了纯装饰，论证断裂。请在图后对关键结论做至少一句解释。",
            })

    return {"schema_version": "1.2", "passed": not issues,
            "gate_status": "BLOCK" if issues else ("WARN" if warnings else "PASS"),
            "issues": issues, "warnings": warnings, "layout_modes": layout_modes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper")
    parser.add_argument("--strict", action="store_true", help="将源文件版面反模式作为阻断项")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    try:
        tex = locate_tex(Path(args.paper).resolve())
        report = check(expand_inputs(tex.read_text(encoding="utf-8", errors="replace"), tex.parent))
        report["tex"] = str(tex)
        if not args.strict and report["issues"]:
            report["warnings"].extend(report["issues"])
            report["issues"] = []
            report["passed"] = True
            report["gate_status"] = "WARN"
    except Exception as exc:
        report = {"schema_version": "1.0", "passed": False, "gate_status": "BLOCK",
                  "issues": [{"kind": "runtime", "message": str(exc)}], "warnings": []}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
