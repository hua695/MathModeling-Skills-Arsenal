#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_paper_narrative.py — 论文叙事质量检查
检测"建模手写论文"问题：非建模章节公式堆砌、结果数值无解释、建模求解章节缺小节、算法细节在正文、推导前后无语言衔接。

用法: python scripts/check_paper_narrative.py <paper.tex 或 论文目录> [--strict]
返回每项 PASS/WARN，供 H8 写作后自检使用。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

# 非建模章节标题（这些章节应该禁公式堆砌）
NARRATIVE_SECTION_PATTERNS = [
    r"问题重述", r"问题分析", r"模型假设", r"符号说明",
    r"模型的分析与检验", r"模型检验", r"灵敏度分析",
    r"模型的评价", r"模型评价", r"改进与推广", r"结论",
    r"参考文献", r"附录",
]

# 建模求解章节标题（这些章节允许全链路推导）
MODELING_SECTION_PATTERNS = [
    r"模型建立与求解", r"模型的建立与求解", r"问题.*的模型",
    r"建模与求解", r"模型建立", r"模型求解",
]

# 结果解释关键词（数值后面应该跟这些词之一）
RESULT_EXPLANATION_WORDS = [
    "意味着", "表明", "说明", "这说明", "这表明", "这意味着",
    "可以看出", "由此可见", "因此", "因而", "从而",
    "表示", "代表", "反映", "体现", "揭示",
]

# 问题级章节开头的自然承接词；它们表达论证依赖，不是写作流程话术。
CHAPTER_HANDOFF_WORDS = [
    "基于", "据此", "在此基础上", "进一步", "由问题", "利用前问", "结合前问",
    "延续", "因此", "由此", "为回答", "承接", "根据上述结果",
]

# 算法细节环境（这些应该在附录，不应该在正文建模求解章节之外）
ALGORITHM_ENV_PATTERNS = [
    r"\\begin\{algorithm\}", r"\\begin\{algorithmic\}",
    r"\\begin\{lstlisting\}", r"\\begin\{verbatim\}",
]

QUESTION_SECTION_RE = re.compile(r"^\s*问题\s*(?:[一二三四五六七八九十]+|\d+)")


def find_tex_file(path: Path) -> Path | None:
    """Find the main TeX file."""
    if path.is_file() and path.suffix == ".tex":
        return path
    if path.is_dir():
        candidates = list(path.glob("paper.tex")) + list(path.glob("main.tex")) + list(path.glob("*.tex"))
        if candidates:
            return candidates[0]
    return None


def split_sections(text: str) -> list[tuple[str, str, str]]:
    """Split text into hierarchical sections with nested content included."""
    sections = []
    # Match \section{...}, \subsection{...}, \subsubsection{...}
    pattern = re.compile(r"\\(section|subsection|subsubsection)\*?\{([^}]*)\}", re.IGNORECASE)
    matches = list(pattern.finditer(text))
    for i, match in enumerate(matches):
        level = match.group(1).lower()
        title = match.group(2).strip()
        start = match.end()
        level_number = {"section": 1, "subsection": 2, "subsubsection": 3}[level]
        end = len(text)
        for next_match in matches[i + 1:]:
            next_level = next_match.group(1).lower()
            next_level_number = {"section": 1, "subsection": 2, "subsubsection": 3}[next_level]
            if next_level_number <= level_number:
                end = next_match.start()
                break
        content = text[start:end]
        sections.append((level, title, content))
    return sections


def is_narrative_section(title: str) -> bool:
    """Check if a section title is a narrative (non-modeling) section."""
    for pattern in NARRATIVE_SECTION_PATTERNS:
        if re.search(pattern, title):
            return True
    return False


def is_modeling_section(title: str) -> bool:
    """Check if a section title is a modeling/solving section."""
    for pattern in MODELING_SECTION_PATTERNS:
        if re.search(pattern, title):
            return True
    return False


def count_formulas(content: str) -> int:
    """Count display math environments in content."""
    count = 0
    # \begin{equation}...\end{equation}
    count += len(re.findall(r"\\begin\{equation\*?\}", content))
    # \begin{align}...\end{align}
    count += len(re.findall(r"\\begin\{align\*?\}", content))
    # \begin{gather}...\end{gather}
    count += len(re.findall(r"\\begin\{gather\*?\}", content))
    # \[...\]
    count += len(re.findall(r"\\\[", content))
    return count


def check_narrative_formula_density(sections: list[tuple[str, str, str]]) -> list[str]:
    """Check narrative sections for formula overload."""
    warnings = []
    for level, title, content in sections:
        if level != "section":
            continue
        if not is_narrative_section(title):
            continue
        formula_count = count_formulas(content)
        # Narrative sections should have at most 2 display formulas
        if formula_count > 2:
            warnings.append(
                f"叙事章节「{title}」公式密度过高：{formula_count} 个展示公式（建议≤2）。"
                f"非建模章节应使用叙事蓝图，禁公式堆砌。"
            )
    return warnings


def check_result_explanation(text: str) -> list[str]:
    """Check if core numerical results have explanations."""
    warnings = []
    # Find sentences ending with a number+unit followed by period (no explanation)
    # Pattern: number (with optional decimal) + optional unit + 。/；/\.
    # This is a heuristic, not perfect
    pattern = re.compile(
        r"(\d+(?:\.\d+)?)\s*(万元|亿元|元|秒|分钟|小时|天|个|件|吨|米|千米|公里|%|百分比|倍|次|项|种|类)?"
        r"(?!\.\d)"
        r"\s*(?:。|；|\.)"
    )
    matches = list(pattern.finditer(text))
    no_explanation_count = 0
    for match in matches:
        # Check if the sentence contains an explanation word
        sentence_start = max(0, match.start() - 100)
        sentence = text[sentence_start:match.end()]
        has_explanation = any(word in sentence for word in RESULT_EXPLANATION_WORDS)
        if not has_explanation:
            no_explanation_count += 1
    if no_explanation_count > 5:
        warnings.append(
            f"检测到 {no_explanation_count} 处数值结果可能缺少解释（数值后直接句号，无'意味着/表明/说明'等解释词）。"
            f"核心数值后面必须跟一句意义解读，不只是报数字。"
        )
    return warnings


def check_modeling_section_structure(sections: list[tuple[str, str, str]]) -> list[str]:
    """Check the question bridge, two-section layout, model box, and result meaning."""
    warnings = []
    for level, title, content in sections:
        if level != "section":
            continue
        if not is_modeling_section(title):
            continue
        question_matches = list(re.finditer(r"\\subsection\*?\{([^}]*)\}", content))
        if not question_matches:
            warnings.append(f"建模求解章节「{title}」缺少问题级小节")
            continue
        for index, match in enumerate(question_matches):
            question_title = match.group(1).strip()
            end = question_matches[index + 1].start() if index + 1 < len(question_matches) else len(content)
            question_text = content[match.end():end]
            inner_matches = list(re.finditer(r"\\subsubsection\*?\{([^}]*)\}", question_text))
            inner_titles = [item.group(1).strip() for item in inner_matches]
            bridge_end = inner_matches[0].start() if inner_matches else len(question_text)
            bridge = question_text[:bridge_end]
            bridge_visible = re.sub(
                r"(?s)\\begin\{.*?\}|\\end\{.*?\}|\\[A-Za-z]+(?:\*|\[[^]]*\])?(?:\{[^{}]*\})?",
                "",
                bridge,
            )
            if len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", bridge_visible)) < 30:
                warnings.append(f"问题「{question_title}」缺少充分的问题引入与建模思路段")
            for required in ("模型建立", "模型求解与结果分析"):
                if required not in inner_titles:
                    warnings.append(f"问题「{question_title}」缺少「{required}」小节")
            allowed_extra = {"灵敏度分析", "稳健性分析", "灵敏度与稳健性分析"}
            extras = [item for item in inner_titles if item not in {"模型建立", "模型求解与结果分析"}]
            for extra in extras:
                if extra not in allowed_extra:
                    warnings.append(f"问题「{question_title}」存在未登记的额外编号小节「{extra}」")
                else:
                    extra_index = inner_titles.index(extra)
                    extra_start = inner_matches[extra_index].end()
                    extra_end = inner_matches[extra_index + 1].start() if extra_index + 1 < len(inner_matches) else len(question_text)
                    if not re.search(r"扰动|敏感性|稳健性|变化率|稳定性", question_text[extra_start:extra_end]):
                        warnings.append(f"问题「{question_title}」的「{extra}」缺少独立扰动或稳定性证据")
            if "模型建立" in inner_titles:
                model_index = inner_titles.index("模型建立")
                model_start = inner_matches[model_index].end()
                model_end = inner_matches[model_index + 1].start() if model_index + 1 < len(inner_matches) else len(question_text)
                model_text = question_text[model_start:model_end]
                if "最终求解模型" not in model_text:
                    warnings.append(f"问题「{question_title}」的模型建立小节末尾缺少最终求解模型框")
                elif not re.search(r"\\begin\{(?:equation|align|gather|multline|cases)\}|\\\[|\\\(|\$\$", model_text[model_text.find("最终求解模型"):], re.I):
                    warnings.append(f"问题「{question_title}」的最终求解模型框缺少数学表达式")
            if "模型求解与结果分析" in inner_titles:
                solve_index = inner_titles.index("模型求解与结果分析")
                solve_start = inner_matches[solve_index].end()
                solve_end = inner_matches[solve_index + 1].start() if solve_index + 1 < len(inner_matches) else len(question_text)
                solve_text = question_text[solve_start:solve_end]
                if not re.search(r"结果|方案|数值|表|图", solve_text):
                    warnings.append(f"问题「{question_title}」的模型求解与结果分析小节缺少结果呈现")
                if not any(word in solve_text for word in RESULT_EXPLANATION_WORDS):
                    warnings.append(f"问题「{question_title}」的模型求解与结果分析小节缺少结果意义解释")
    return warnings


def check_question_section_hierarchy(sections: list[tuple[str, str, str]]) -> list[str]:
    """Require every modeling question to live under the single core chapter."""
    warnings = []
    for level, title, _ in sections:
        if level == "section" and QUESTION_SECTION_RE.search(title):
            warnings.append(
                f"问题级章节「{title}」不能作为一级章节；应统一归入「模型建立与求解」，"
                "并作为二级问题标题，其下只保留“模型建立”和“模型求解与结果分析”两节。"
            )
    return warnings


def check_global_assumptions_symbol_layout(sections: list[tuple[str, str, str]]) -> list[str]:
    """Reject a combined assumptions-and-symbols top-level chapter."""
    warnings = []
    for level, title, _ in sections:
        if level != "section":
            continue
        if re.search(r"模型假设\s*(?:与|及|、)\s*(?:统一)?符号|符号说明\s*(?:与|及)\s*模型假设", title):
            warnings.append(
                f"一级章节「{title}」合并了模型假设与符号说明；两者必须分别设置为全局一级章节。"
            )
    return warnings


def check_chapter_handoff_language(sections: list[tuple[str, str, str]]) -> list[str]:
    """Warn when consecutive modeling-question openings lack a reader handoff."""
    warnings = []
    for level, title, content in sections:
        if level != "section" or not is_modeling_section(title):
            continue
        question_matches = list(re.finditer(r"\\subsection\*?\{([^}]*)\}", content))
        for index in range(1, len(question_matches)):
            current = question_matches[index]
            end = question_matches[index + 1].start() if index + 1 < len(question_matches) else len(content)
            question_text = content[current.end():end]
            first_inner = re.search(r"\\subsubsection\*?\{([^}]*)\}", question_text)
            bridge = question_text[:first_inner.start()] if first_inner else question_text[:500]
            if not any(word in bridge for word in CHAPTER_HANDOFF_WORDS):
                warnings.append(
                    f"章节承接不足：问题「{current.group(1).strip()}」开头未说明与前一问题的论证关系。"
                    "应先交代前置结果如何成为本问输入，再进入模型建立。"
                )
        modeling_indices = [index for index, item in enumerate(sections)
                            if item[0] == "section" and is_modeling_section(item[1])]
        current_index = next((index for index, item in enumerate(sections) if item == (level, title, content)), None)
        if current_index is not None and current_index in modeling_indices and current_index > modeling_indices[0]:
            first_inner = re.search(r"\\subsection\*?\{([^}]*)\}", content)
            bridge = content[:first_inner.start()] if first_inner else content[:500]
            if not any(word in bridge for word in CHAPTER_HANDOFF_WORDS):
                warnings.append(
                    f"章节承接不足：建模章节「{title}」开头未连接前置章节结论。"
                )
    return warnings


def check_algorithm_in_body(sections: list[tuple[str, str, str]]) -> list[str]:
    """Check if algorithm details (pseudocode, code listings) are in body sections."""
    warnings = []
    for level, title, content in sections:
        if level != "section":
            continue
        # Skip appendix sections
        if "附录" in title or "appendix" in title.lower():
            continue
        for pattern in ALGORITHM_ENV_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                warnings.append(
                    f"正文章节「{title}」包含算法伪代码/代码清单环境。"
                    f"算法实现细节（伪代码、参数表、调优过程）应放附录，正文只用自然语言概括算法思路。"
                )
                break
    return warnings


def check_consecutive_formulas(text: str) -> list[str]:
    """Check for 3+ consecutive formulas without text between them."""
    warnings = []
    # Pattern: formula environment followed by optional whitespace and another formula
    # This is simplified: count formula environments separated only by whitespace/labels
    pattern = re.compile(
        r"(\\begin\{(?:equation|align|gather)\*?\}|\\\[)"
        r"[\s\S]*?"
        r"(\\end\{(?:equation|align|gather)\*?\}|\\\])"
        r"[\s\\label{}]*"
        r"(?=(\\begin\{(?:equation|align|gather)\*?\}|\\\[))",
        re.IGNORECASE
    )
    consecutive_count = 0
    for match in pattern.finditer(text):
        between = text[match.end():match.end() + 200]
        # Check if there's meaningful text between formulas (more than just labels/whitespace)
        text_between = re.sub(r"\\label\{[^}]*\}", "", between)
        text_between = re.sub(r"[\s\\%]", "", text_between)
        if len(text_between) < 10:
            consecutive_count += 1
    if consecutive_count >= 3:
        warnings.append(
            f"检测到 {consecutive_count} 处连续公式（公式之间缺少文字衔接）。"
            f"推导前后必须有语言衔接：推导前说清楚为什么要建立这个模型，推导后说清楚结果意味着什么。"
        )
    return warnings


def check(path: Path, strict: bool = False) -> dict:
    """Main check function."""
    tex_file = find_tex_file(path)
    if tex_file is None:
        return {"passed": False, "gate_status": "FAIL", "error": f"未找到 TeX 文件: {path}"}

    try:
        text = tex_file.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"passed": False, "gate_status": "FAIL", "error": f"读取 TeX 文件失败: {exc}"}

    sections = split_sections(text)
    all_warnings = []

    # 1. Narrative section formula density
    all_warnings.extend(check_narrative_formula_density(sections))

    # 2. Result explanation
    all_warnings.extend(check_result_explanation(text))

    # 3. Modeling section structure
    all_warnings.extend(check_modeling_section_structure(sections))

    # 3b. One modeling spine; questions must not become isolated top-level chapters.
    all_warnings.extend(check_question_section_hierarchy(sections))

    # 3c. Global assumptions and symbol table are separate support chapters.
    all_warnings.extend(check_global_assumptions_symbol_layout(sections))

    # 4. Algorithm in body
    all_warnings.extend(check_algorithm_in_body(sections))

    # 5. Consecutive formulas
    all_warnings.extend(check_consecutive_formulas(text))

    # 6. Chapter handoff language between core modeling questions
    all_warnings.extend(check_chapter_handoff_language(sections))

    passed = len(all_warnings) == 0
    gate_status = "PASS" if passed else ("BLOCK" if strict else "WARN")

    return {
        "schema_version": "1.0",
        "passed": passed,
        "gate_status": gate_status,
        "strict": strict,
        "tex_file": str(tex_file),
        "warnings": all_warnings,
        "warning_count": len(all_warnings),
        "checks": {
            "narrative_formula_density": "PASS" if not any("公式密度过高" in w for w in all_warnings) else "WARN",
            "result_explanation": "PASS" if not any("缺少解释" in w for w in all_warnings) else "WARN",
            "modeling_section_structure": "PASS" if not any(
                "问题级小节" in w or "问题「" in w or "一级章节" in w for w in all_warnings
            ) else "WARN",
            "global_assumptions_symbol_layout": "PASS" if not any(
                "合并了模型假设与符号说明" in w for w in all_warnings
            ) else "WARN",
            "algorithm_in_body": "PASS" if not any("包含算法伪代码" in w for w in all_warnings) else "WARN",
            "consecutive_formulas": "PASS" if not any("连续公式" in w for w in all_warnings) else "WARN",
            "chapter_handoff": "PASS" if not any("章节承接不足" in w for w in all_warnings) else "WARN",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="论文 TeX 文件或目录")
    parser.add_argument("--strict", action="store_true", help="WARN 也视为不通过")
    parser.add_argument("--out", default=None, help="输出 JSON 报告路径")
    args = parser.parse_args()

    path = Path(args.paper).resolve()
    report = check(path, args.strict)

    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        import json
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"=== 论文叙事质量检查: {path} ===")
    print(f"状态: {report['gate_status']}（{report['warning_count']} 个警告）")
    print()
    for check_name, status in report.get("checks", {}).items():
        print(f"  [{status}] {check_name}")
    print()
    if report["warnings"]:
        print("详细警告:")
        for i, warning in enumerate(report["warnings"], 1):
            print(f"  {i}. {warning}")
    print()
    print(f"===== 叙事质量检查: {report['gate_status']} =====")

    return 0 if report["passed"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
