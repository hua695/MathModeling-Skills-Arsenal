#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
style_check.py — 写作风格客观检查
用六项客观指标检测"AI 生成感"：句长均匀度、段落长度均匀度、列表堆砌、机械过渡词、跨章节短语重复、套话密度。

用法: python scripts/style_check.py <paper.tex 或 论文目录> [--strict] [--out report.json]
返回每项 PASS/WARN，供 H8 论文写作后自检使用。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from statistics import mean, pstdev

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

# 机械过渡词（AI 写作常用的固定逻辑连接词）
MECHANICAL_TRANSITIONS = [
    "首先", "其次", "然后", "最后", "接下来", "综上所述", "综上",
    "由此可见", "因此", "因而", "所以", "于是",
    "一方面", "另一方面", "不仅如此", "与此同时",
    "firstly", "secondly", "thirdly", "finally", "in conclusion",
    "therefore", "thus", "hence", "consequently",
]

# 套话（无信息含量的空洞表述）
STOCK_PHRASES = [
    "具有重要意义", "具有重要的理论和实际意义", "具有重要的现实意义",
    "为XX提供了参考", "为相关领域提供了新思路", "为XX提供了理论依据",
    "本文深入研究了", "本文对XX进行了深入研究", "本文系统地研究了",
    "随着XX的发展", "近年来，XX得到了广泛关注", "XX一直是研究的热点",
    "取得了显著的效果", "效果良好", "精度较高", "性能优越",
    "has important significance", "provides a reference for",
    "in recent years", "with the development of",
]

# LaTeX 环境排除（这些环境内的文本不参与风格检查）
EXCLUDE_ENVS = [
    r"\\begin\{equation\}.*?\\end\{equation\}",
    r"\\begin\{align\}.*?\\end\{align\}",
    r"\\begin\{gather\}.*?\\end\{gather\}",
    r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}",
    r"\\begin\{verbatim\}.*?\\end\{verbatim\}",
    r"\\begin\{algorithm\}.*?\\end\{algorithm\}",
    r"\\begin\{algorithmic\}.*?\\end\{algorithmic\}",
    r"\\begin\{table\}.*?\\end\{table\}",
    r"\\begin\{figure\}.*?\\end\{figure\}",
    r"\$.*?\$",  # 行内公式
    r"\\\(.*?\\\)",
    r"\\\[.*?\\\]",
]


def find_tex_file(path: Path) -> Path | None:
    """找到主 TeX 文件。"""
    if path.is_file() and path.suffix == ".tex":
        return path
    if path.is_dir():
        candidates = list(path.glob("paper.tex")) + list(path.glob("main.tex")) + list(path.glob("*.tex"))
        if candidates:
            return candidates[0]
    return None


def clean_text(text: str) -> str:
    """清理 LaTeX 文本，移除公式、代码、图表等环境，只保留正文。"""
    cleaned = text
    # 移除排除环境
    for pattern in EXCLUDE_ENVS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # 移除 LaTeX 命令（如 \section{...} 保留内容，\textbf{...} 保留内容）
    cleaned = re.sub(r"\\(?:section|subsection|subsubsection|chapter|paragraph|textbf|textit|emph|underline)\*?\{([^}]*)\}", r"\1", cleaned)
    # 移除其他 LaTeX 命令
    cleaned = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", cleaned)
    # 移除注释
    cleaned = re.sub(r"%[^\n]*", "", cleaned)
    # 移除多余空白
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def split_sentences(text: str) -> list[str]:
    """将文本分割成句子。"""
    # 中文句号、问号、感叹号，英文句号、问号、感叹号
    sentences = re.split(r"(?<=[。！？.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


def split_paragraphs(text: str) -> list[str]:
    """将文本分割成段落。"""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if len(p.strip()) > 20]


def check_sentence_length_uniformity(text: str) -> dict:
    """检查句长均匀度：AI 写的句子长度都差不多，人类写的波动大。"""
    sentences = split_sentences(text)
    if len(sentences) < 10:
        return {"status": "PASS", "score": None, "message": f"句子数量不足（{len(sentences)} < 10），无法判断"}

    lengths = [len(s) for s in sentences]
    avg_len = mean(lengths)
    std_len = pstdev(lengths)
    cv = std_len / (avg_len + 1e-10)  # 变异系数

    # CV < 0.2 说明句子长度太均匀（AI 生成感强）
    if cv < 0.2:
        return {
            "status": "WARN",
            "score": cv,
            "avg_length": avg_len,
            "std": std_len,
            "message": f"句长过于均匀（CV={cv:.3f} < 0.2），平均句长 {avg_len:.1f} 字，"
                       f"建议长短句结合，增加句长变化"
        }
    return {
        "status": "PASS",
        "score": cv,
        "avg_length": avg_len,
        "std": std_len,
        "message": f"句长变化正常（CV={cv:.3f}），平均句长 {avg_len:.1f} 字"
    }


def check_paragraph_length_uniformity(text: str) -> dict:
    """检查段落长度均匀度：AI 写的段落长度都差不多，人类写的波动大。"""
    paragraphs = split_paragraphs(text)
    if len(paragraphs) < 5:
        return {"status": "PASS", "score": None, "message": f"段落数量不足（{len(paragraphs)} < 5），无法判断"}

    lengths = [len(p) for p in paragraphs]
    avg_len = mean(lengths)
    std_len = pstdev(lengths)
    cv = std_len / (avg_len + 1e-10)

    # CV < 0.25 说明段落长度太均匀
    if cv < 0.25:
        return {
            "status": "WARN",
            "score": cv,
            "avg_length": avg_len,
            "std": std_len,
            "message": f"段落长度过于均匀（CV={cv:.3f} < 0.25），平均段长 {avg_len:.1f} 字，"
                       f"建议段落长度有变化，重要内容展开写，次要内容简写"
        }
    return {
        "status": "PASS",
        "score": cv,
        "avg_length": avg_len,
        "std": std_len,
        "message": f"段落长度变化正常（CV={cv:.3f}），平均段长 {avg_len:.1f} 字"
    }


def check_list_heavy(text: str, raw_text: str) -> dict:
    """检查列表堆砌：连续 3 个以上列表项，AI 写作常用列表堆砌。"""
    # 检测 itemize/enumerate 环境
    list_pattern = r"\\begin\{(?:itemize|enumerate)\}(.*?)\\end\{(?:itemize|enumerate)\}"
    list_matches = re.findall(list_pattern, raw_text, flags=re.DOTALL)

    total_items = 0
    heavy_lists = 0
    for match in list_matches:
        items = re.findall(r"\\item", match)
        total_items += len(items)
        if len(items) >= 5:
            heavy_lists += 1

    # 检测文本中的数字列表（1. 2. 3. 或 - - -）
    text_list_pattern = r"(?:^|\n)\s*(?:\d+\.|[-*])\s+"
    text_lists = re.findall(text_list_pattern, text)

    total_list_items = total_items + len(text_lists)
    list_ratio = total_list_items / (len(split_sentences(text)) + 1e-10)

    if heavy_lists > 0 or list_ratio > 0.3:
        return {
            "status": "WARN",
            "total_items": total_list_items,
            "heavy_lists": heavy_lists,
            "list_ratio": list_ratio,
            "message": f"列表堆砌：共 {total_list_items} 个列表项，{heavy_lists} 个长列表（≥5项），"
                       f"列表/句子比 {list_ratio:.1%}，建议减少列表，用文字叙述替代"
        }
    return {
        "status": "PASS",
        "total_items": total_list_items,
        "heavy_lists": heavy_lists,
        "list_ratio": list_ratio,
        "message": f"列表使用正常：共 {total_list_items} 个列表项，列表/句子比 {list_ratio:.1%}"
    }


def check_mechanical_transitions(text: str) -> dict:
    """检查机械过渡词密度：AI 写作常用固定逻辑连接词。"""
    total_count = 0
    found_words = {}
    for word in MECHANICAL_TRANSITIONS:
        count = len(re.findall(re.escape(word), text, re.IGNORECASE))
        if count > 0:
            found_words[word] = count
            total_count += count

    sentences = split_sentences(text)
    density = total_count / (len(sentences) + 1e-10)

    # 密度 > 0.15 说明机械过渡词太多
    if density > 0.15:
        top_words = sorted(found_words.items(), key=lambda x: -x[1])[:5]
        return {
            "status": "WARN",
            "total_count": total_count,
            "density": density,
            "top_words": top_words,
            "message": f"机械过渡词过多：共 {total_count} 个，密度 {density:.1%}，"
                       f"高频词：{', '.join(f'{w}({c})' for w, c in top_words)}，"
                       f"建议减少固定逻辑连接词，用自然过渡替代"
        }
    return {
        "status": "PASS",
        "total_count": total_count,
        "density": density,
        "message": f"机械过渡词正常：共 {total_count} 个，密度 {density:.1%}"
    }


def check_cross_section_repetition(raw_text: str) -> dict:
    """检查跨章节短语重复：同一句话在多个章节出现。"""
    # 按章节分割
    section_pattern = r"\\(?:section|subsection)\*?\{([^}]*)\}"
    sections = re.split(section_pattern, raw_text)

    # sections[0] 是第一章前的内容，之后是 [标题1, 内容1, 标题2, 内容2, ...]
    section_texts = {}
    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        content = sections[i + 1] if i + 1 < len(sections) else ""
        # 清理内容
        cleaned = clean_text(content)
        # 提取长度 > 15 的句子
        sentences = [s for s in split_sentences(cleaned) if len(s) > 15]
        section_texts[title] = sentences

    if len(section_texts) < 2:
        return {"status": "PASS", "message": "章节数量不足，无法检查跨章节重复"}

    # 检查重复句子
    repeated = []
    all_sentences = {}
    for title, sentences in section_texts.items():
        for s in sentences:
            # 归一化（移除标点和空白）
            normalized = re.sub(r"[^\w]", "", s)
            if normalized in all_sentences:
                if all_sentences[normalized] != title:
                    repeated.append({
                        "sentence": s[:50] + "..." if len(s) > 50 else s,
                        "sections": [all_sentences[normalized], title]
                    })
            else:
                all_sentences[normalized] = title

    if len(repeated) > 3:
        return {
            "status": "WARN",
            "repeated_count": len(repeated),
            "examples": repeated[:3],
            "message": f"跨章节短语重复：{len(repeated)} 处，建议避免相同句子在多个章节出现，"
                       f"不同章节应有不同的表述角度"
        }
    return {
        "status": "PASS",
        "repeated_count": len(repeated),
        "message": f"跨章节短语重复正常：{len(repeated)} 处"
    }


def check_stock_phrases(text: str) -> dict:
    """检查套话密度：无信息含量的空洞表述。"""
    total_count = 0
    found_phrases = {}
    for phrase in STOCK_PHRASES:
        # 处理 "XX" 通配符
        pattern = phrase.replace("XX", r"\S+")
        count = len(re.findall(pattern, text, re.IGNORECASE))
        if count > 0:
            found_phrases[phrase] = count
            total_count += count

    sentences = split_sentences(text)
    density = total_count / (len(sentences) + 1e-10)

    if total_count > 3 or density > 0.05:
        top_phrases = sorted(found_phrases.items(), key=lambda x: -x[1])[:5]
        return {
            "status": "WARN",
            "total_count": total_count,
            "density": density,
            "top_phrases": top_phrases,
            "message": f"套话过多：共 {total_count} 处，密度 {density:.1%}，"
                       f"高频套话：{', '.join(f'{p}({c})' for p, c in top_phrases)}，"
                       f"建议删除无信息含量的空洞表述，用具体内容替代"
        }
    return {
        "status": "PASS",
        "total_count": total_count,
        "density": density,
        "message": f"套话使用正常：共 {total_count} 处，密度 {density:.1%}"
    }


def check(path: Path, strict: bool = False) -> dict:
    """主检查函数。"""
    tex_file = find_tex_file(path)
    if tex_file is None:
        return {"passed": False, "gate_status": "FAIL", "error": f"未找到 TeX 文件: {path}"}

    try:
        raw_text = tex_file.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"passed": False, "gate_status": "FAIL", "error": f"读取 TeX 文件失败: {exc}"}

    cleaned_text = clean_text(raw_text)

    # 六项检查
    checks = {}
    all_warnings = []

    # 1. 句长均匀度
    result = check_sentence_length_uniformity(cleaned_text)
    checks["sentence_length_uniformity"] = result["status"]
    if result["status"] == "WARN":
        all_warnings.append(result["message"])

    # 2. 段落长度均匀度
    result = check_paragraph_length_uniformity(cleaned_text)
    checks["paragraph_length_uniformity"] = result["status"]
    if result["status"] == "WARN":
        all_warnings.append(result["message"])

    # 3. 列表堆砌
    result = check_list_heavy(cleaned_text, raw_text)
    checks["list_heavy"] = result["status"]
    if result["status"] == "WARN":
        all_warnings.append(result["message"])

    # 4. 机械过渡词
    result = check_mechanical_transitions(cleaned_text)
    checks["mechanical_transitions"] = result["status"]
    if result["status"] == "WARN":
        all_warnings.append(result["message"])

    # 5. 跨章节短语重复
    result = check_cross_section_repetition(raw_text)
    checks["cross_section_repetition"] = result["status"]
    if result["status"] == "WARN":
        all_warnings.append(result["message"])

    # 6. 套话密度
    result = check_stock_phrases(cleaned_text)
    checks["stock_phrases"] = result["status"]
    if result["status"] == "WARN":
        all_warnings.append(result["message"])

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
        "checks": checks,
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
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 打印摘要
    print(f"写作风格检查: {report['gate_status']}")
    print(f"检查项:")
    for name, status in report["checks"].items():
        print(f"  {name}: {status}")
    if report["warnings"]:
        print(f"\n发现 {report['warning_count']} 个问题:")
        for w in report["warnings"]:
            print(f"  - {w}")

    return 0 if report["passed"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
