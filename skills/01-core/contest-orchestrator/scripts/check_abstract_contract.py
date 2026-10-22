#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check abstract evidence, numeric provenance, and keyword contract.

This is a source-aware gate rather than a prose generator.  It refuses a
strict abstract when one of the six required evidence groups is absent or a
number cannot be traced to a result/sensitivity artifact.  The numeric
checklist is written beside the report and is never inserted into the paper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


NUM_RE = re.compile(
    r"(?<![-A-Za-z0-9.])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:%|[A-Za-zμΩ℃°]+)?"
)
QUESTION_RE = re.compile(r"问题\s*[一二三四五六七八九十百\d]+|Q\s*[1-9]\d*", re.I)
ABSTRACT_RE = re.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", re.I | re.S)
KEYWORD_RE = re.compile(r"关键词\s*[:：]?(.*)", re.I)

EVIDENCE_RULES: dict[str, tuple[str, ...]] = {
    "problem_decomposition": (r"问题|子问题|任务|目标", r"Q\s*[1-9]|问题\s*[一二三四五六七八九十\d]+"),
    "assumptions_preprocessing": (
        r"假设|假定|数据预处理|预处理|缺失|异常值|归一化|标准化|清洗|特征工程",
    ),
    "model_algorithm_tool": (
        r"模型|方程|目标函数|回归|分类|优化|评价|仿真|预测",
        r"算法|求解|迭代|拟合|反演|搜索|遗传|粒子群|随机森林|XGBoost|ARIMA|牛顿|线性规划",
    ),
    "quantified_results": (r"结果|得到|达到|误差|成本|厚度|精度|准确率|目标值",),
    "validation": (r"敏感性|稳健|鲁棒|误差|残差|交叉验证|扰动|置信|稳定性|不确定性",),
    "application_value": (r"应用|实际|推广|适用|价值|决策|部署|建议|边界|局限",),
}


def _locate_pdf(target: Path) -> Path:
    if target.is_file() and target.suffix.lower() == ".pdf":
        return target
    if not target.is_dir():
        raise FileNotFoundError(f"论文路径不存在: {target}")
    candidates = [target / "paper.pdf", target / "paper" / "paper.pdf"]
    candidates.extend(sorted(target.glob("*.pdf")))
    candidates.extend(sorted((target / "paper").glob("*.pdf")) if (target / "paper").exists() else [])
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(f"未找到论文 PDF: {target}")


def _locate_source(paper_dir: Path) -> Path | None:
    candidates = [paper_dir / "paper.tex", paper_dir / "paper_pandoc.tex"]
    candidates.extend(sorted(paper_dir.glob("*.tex")))
    candidates = [path.resolve() for path in candidates if path.exists()]
    for path in candidates:
        text = path.read_text(encoding="utf-8", errors="replace")
        if ABSTRACT_RE.search(text):
            return path
        for raw in re.findall(r"\\(?:input|include)\{([^{}]+)\}", text):
            child = Path(raw.strip())
            if child.suffix == "":
                child = child.with_suffix(".tex")
            child = (path.parent / child).resolve()
            if child.exists() and ABSTRACT_RE.search(child.read_text(encoding="utf-8", errors="replace")):
                return child
    return candidates[0] if candidates else None


def _pdf_text(pdf: Path) -> str:
    try:
        import pymupdf
    except Exception as exc:  # pragma: no cover - environment diagnostic
        raise RuntimeError(f"缺少 pymupdf，无法提取摘要文本: {exc}") from exc
    with pymupdf.open(str(pdf)) as document:
        return "\n".join(page.get_text() for page in document)


def _abstract_text(source: Path | None, pdf_text: str) -> tuple[str, str]:
    if source is not None:
        text = source.read_text(encoding="utf-8", errors="replace")
        match = ABSTRACT_RE.search(text)
        if match:
            return match.group(1), "tex"
    match = re.search(r"摘要(.*?)(?:关键词|关键字)", pdf_text, re.S)
    if match:
        return match.group(1), "pdf"
    return "", "missing"


def _clean(text: str) -> str:
    # Keep percentage values such as ``12.5%``; only strip a standalone
    # TeX comment marker that is not preceded by a digit.
    text = re.sub(r"(?m)(?<![\\\d])%[^\n]*$", "", text)
    text = re.sub(r"\\[a-zA-Z]+(?:\[[^]]*\]|\{[^}]*\})?", " ", text)
    return re.sub(r"\s+", "", text)


def _keywords(pdf_text: str, source_text: str | None) -> list[str]:
    text = source_text or pdf_text
    match = re.search(r"关键词\s*[:：]?([^\n]+)", text, re.I)
    if not match:
        match = re.search(r"\\keywords\s*\{([^}]*)\}", text, re.I)
    if not match:
        return []
    value = match.group(1).replace("\\textbf", "")
    return [item.strip(" {}\\[]（）()") for item in re.split(r"(?:\\quad|[、,，;；|｜]+)", value) if item.strip(" {}\\[]（）()")]


def _numeric_tokens(text: str) -> list[str]:
    return list(dict.fromkeys(NUM_RE.findall(text)))


def _numeric_keys(token: str) -> set[Decimal]:
    raw = token.replace(",", "")
    is_percent = raw.endswith("%")
    raw = raw.rstrip("%")
    raw = re.sub(r"[A-Za-zμΩ℃°]+$", "", raw)
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return set()
    values = {value.normalize()}
    if is_percent:
        values.add((value / Decimal("100")).normalize())
    else:
        values.add((value * Decimal("100")).normalize())
    return values


def _source_files(root: Path) -> list[Path]:
    patterns = (
        "results/**/*.json", "results/**/*.csv", "results/**/*.yaml", "results/**/*.yml",
        "**/sensitivity*.json", "**/*_results.json", "**/baseline*.json", "**/metrics*.json",
    )
    files: set[Path] = set()
    for pattern in patterns:
        files.update(path.resolve() for path in root.glob(pattern) if path.is_file())
    # Standard governed projects keep results under a Chinese-named delivery
    # directory.  Discover any directory literally named ``results`` instead
    # of assuming a flat English layout.
    for directory in root.rglob("results"):
        if directory.is_dir():
            files.update(path.resolve() for path in directory.rglob("*")
                         if path.is_file() and path.suffix.lower() in {".json", ".csv", ".yaml", ".yml"})
    return sorted(files)


def _provenance(tokens: list[str], root: Path) -> list[dict]:
    source_files = _source_files(root)
    source_values: dict[Path, set[Decimal]] = {}
    for path in source_files:
        try:
            values: set[Decimal] = set()
            for source_token in NUM_RE.findall(path.read_text(encoding="utf-8", errors="replace")):
                values.update(_numeric_keys(source_token))
            source_values[path] = values
        except OSError:
            source_values[path] = set()
    rows = []
    for token in tokens:
        keys = _numeric_keys(token)
        raw = re.sub(r"[%A-Za-zμΩ℃°]+$", "", token)
        decimal_places = len(raw.partition(".")[2]) if "." in raw else 0
        tolerance = Decimal("0.5") * (Decimal(10) ** -decimal_places)
        matches = [
            str(path.relative_to(root)) for path, values in source_values.items()
            if keys & values or any(abs(left - right) <= tolerance for left in keys for right in values)
        ]
        rows.append({"token": token, "source_files": matches, "status": "PASS" if matches else "UNVERIFIED"})
    return rows


def _evidence(abstract: str) -> dict:
    compact = _clean(abstract)
    values = {}
    for key, groups in EVIDENCE_RULES.items():
        values[key] = {
            "passed": all(re.search(pattern, compact, re.I) for pattern in groups),
            "matched": [pattern for pattern in groups if re.search(pattern, compact, re.I)],
            "required_groups": len(groups),
        }
    values["quantified_results"]["number_count"] = len(_numeric_tokens(abstract))
    values["quantified_results"]["passed"] = bool(_numeric_tokens(abstract)) and values["quantified_results"]["passed"]
    questions = [match.group(0) for match in QUESTION_RE.finditer(compact)]
    values["question_markers"] = {"count": len(questions), "markers": questions}
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n|\\par\b", abstract)
                  if _clean(part).strip()]
    values["paragraph_count"] = len(paragraphs)
    values["final_summary"] = bool(paragraphs and re.search(r"综合|总体|应用|适用|局限|价值", _clean(paragraphs[-1]), re.I))
    return values


OPTIMIZATION_METHOD_RE = re.compile(
    r"线性规划|整数规划|混合整数|非线性规划|动态规划|目标规划|多目标|鲁棒优化|随机优化|"
    r"单纯形|分支定界|割平面|内点法|梯度下降|牛顿|拉格朗日|遗传算法|粒子群|模拟退火|"
    r"模型|算法|求解|方法|建模",
    re.I,
)
OPTIMIZATION_RESULT_RE = re.compile(
    r"最优|最佳|最小|最大|目标值|成本|收益|利润|误差|精度|准确率|可行|不可行|满足约束|"
    r"\d+\.?\d*\s*(?:万元|元|%|个|件|吨|kg|km|m|s|小时|天)",
    re.I,
)
OPTIMIZATION_OBJECTIVE_RE = re.compile(
    r"目标函数|最小化|最大化|minimize|maximize|成本最小|收益最大|利润最大|能耗最低|"
    r"约束|限制|边界|容量|供需|平衡|时间窗口|资源约束",
    re.I,
)


def _check_optimization_abstract(abstract: str, capabilities: list[str] | None = None) -> dict:
    """Capability-driven abstract check for optimization (B-type) problems.

    When capabilities include 'optimization', verifies the abstract covers:
    method/model per subproblem, quantified result or feasibility conclusion,
    objective function and constraint types.  Returns missing fields list.
    """
    if not capabilities or "optimization" not in capabilities:
        return {"status": "skipped", "capabilities": capabilities or [], "missing": []}
    compact = _clean(abstract)
    missing = []
    if not OPTIMIZATION_METHOD_RE.search(compact):
        missing.append("method_or_model")
    if not OPTIMIZATION_RESULT_RE.search(compact):
        missing.append("quantified_result_or_feasibility")
    if not OPTIMIZATION_OBJECTIVE_RE.search(compact):
        missing.append("objective_or_constraints")
    return {
        "status": "checked",
        "capabilities": capabilities,
        "missing": missing,
        "passed": not missing,
    }


NUMERIC_EXCLUDE_RE = re.compile(
    r"(?:20\d{2}|19\d{2})"  # years
    r"|(?:图|表|Fig|Table|公式|式|Eq|Equation)\s*[\d一二三四五六七八九十]+"
    r"|(?:第\s*[\d一二三四五六七八九十]+\s*[章节条])"
    r"|(?:\[\d+\])"  # reference numbers
    r"|(?:\\(?:label|ref|cite)\{[^}]*\})",
    re.I,
)


def _numeric_density_diagnostic(abstract: str) -> dict:
    """Numeric density as WARN-level diagnostic (not BLOCK).

    Excludes years, formula/figure/table/section numbers, and reference
    numbers.  Returns count and level=WARN.
    """
    compact = _clean(abstract)
    # Remove excluded patterns before counting
    cleaned = NUMERIC_EXCLUDE_RE.sub(" ", compact)
    tokens = _numeric_tokens(cleaned)
    return {
        "level": "WARN",
        "numeric_count": len(tokens),
        "tokens": tokens[:20],
        "note": "数字密度仅作诊断，不作为通用 BLOCK；数字质量以来源映射和逐问结果覆盖为准",
    }


def check(target: Path, project_root: Path | None = None, strict: bool = False,
          capabilities: list[str] | None = None) -> dict:
    pdf = _locate_pdf(target)
    paper_dir = pdf.parent
    root = (project_root or paper_dir.parent).resolve()
    card_candidates = (root / "abstract_argument_card.yaml", paper_dir / "abstract_argument_card.yaml")
    abstract_card_path = next((candidate for candidate in card_candidates if candidate.is_file()), None)
    abstract_card_hash = (
        hashlib.sha256(abstract_card_path.read_bytes()).hexdigest()
        if abstract_card_path is not None else None
    )
    pdf_text = _pdf_text(pdf)
    source = _locate_source(paper_dir)
    source_text = source.read_text(encoding="utf-8", errors="replace") if source else None
    abstract, source_kind = _abstract_text(source, pdf_text)
    compact = _clean(abstract)
    keywords = _keywords(pdf_text, source_text)
    evidence = _evidence(abstract)
    numeric = _provenance(_numeric_tokens(abstract), root)
    issues: list[str] = []
    warnings: list[str] = []
    if not abstract:
        issues.append("未找到摘要正文")
    if not 550 <= len(compact) <= 800:
        issues.append(f"摘要有效字数 {len(compact)} 不在 550-800 范围")
    if not 4 <= len(keywords) <= 5:
        issues.append(f"关键词数量 {len(keywords)} 不在 4-5 范围")
    for key, value in evidence.items():
        if isinstance(value, dict) and value.get("passed") is False:
            issues.append(f"摘要缺少内容要素: {key}")
    if evidence.get("paragraph_count", 0) < 4:
        issues.append("摘要未形成背景、方法、分问结果、总评四段结构")
    if not evidence.get("final_summary"):
        issues.append("摘要最后一段缺少独立总评或应用边界")
    if not numeric:
        issues.append("摘要没有量化结果")
    unverified = [row["token"] for row in numeric if row["status"] != "PASS"]
    if unverified:
        issues.append("摘要存在无法追溯到结果/敏感性文件的数字: " + ", ".join(unverified))
    # Capability-driven optimization abstract check (B-type)
    opt_check = _check_optimization_abstract(abstract, capabilities)
    if opt_check.get("status") == "checked" and opt_check.get("missing"):
        issues.append("optimization 能力摘要缺少要素: " + ", ".join(opt_check["missing"]))
    # Numeric density as WARN-level diagnostic (not BLOCK)
    density = _numeric_density_diagnostic(abstract)
    warnings.append(f"数字密度诊断: {density['numeric_count']} 个有效数字（排除年份/图表/公式/参考文献编号）")
    report = {
        "schema_version": "1.0",
        "strict": strict,
        "passed": not issues,
        "gate_status": "BLOCK" if issues else ("WARN" if warnings else "PASS"),
        "paper": str(pdf),
        "abstract_source": source_kind,
        "abstract_chars": len(compact),
        "keyword_count": len(keywords),
        "keywords": keywords,
        "evidence": evidence,
        "numeric_values": numeric,
        "optimization_check": opt_check,
        "numeric_density": density,
        "capabilities": capabilities or [],
        "abstract_argument_card": str(abstract_card_path) if abstract_card_path is not None else None,
        "abstract_argument_card_sha256": abstract_card_hash,
        "issues": issues,
        "warnings": warnings,
        "manual_notice": "本报告只生成核对清单；摘要仍需人工逐条回到正文核对数字来源，不得直接提交。",
    }
    if not strict and issues:
        report["warnings"] = issues
        report["issues"] = []
        report["passed"] = True
        report["gate_status"] = "WARN"
    return report


def _discover_capabilities(paper_path: Path, explicit: str | None) -> list[str] | None:
    """Resolve capabilities from CLI override or model_contract.yaml.

    CLI --capabilities takes precedence.  Otherwise look for model_contract.yaml
    in the paper directory or project root and extract subproblem capabilities.
    """
    if explicit:
        return [c.strip() for c in explicit.split(",") if c.strip()]
    # Try to discover model_contract.yaml
    candidates = []
    if paper_path.is_dir():
        candidates.append(paper_path / "model_contract.yaml")
        candidates.append(paper_path.parent / "model_contract.yaml")
    else:
        candidates.append(paper_path.parent / "model_contract.yaml")
        candidates.append(paper_path.parent.parent / "model_contract.yaml")
    for candidate in candidates:
        if candidate.is_file():
            try:
                import yaml as _yaml
                contract = _yaml.safe_load(candidate.read_text(encoding="utf-8", errors="replace")) or {}
                caps = set()
                for sp in contract.get("subproblems", []) or []:
                    if isinstance(sp, dict):
                        for c in sp.get("capabilities", []) or []:
                            caps.add(str(c).strip().lower())
                if caps:
                    return sorted(caps)
            except Exception:
                pass
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="PDF 文件或含 paper.pdf 的论文目录")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--capabilities", default=None,
                        help="逗号分隔的能力列表（如 optimization,robustness）；优先使用此参数，否则自动从 model_contract.yaml 读取")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    paper_path = Path(args.paper).resolve()
    capabilities = _discover_capabilities(paper_path, args.capabilities)
    try:
        report = check(paper_path, Path(args.project_root).resolve() if args.project_root else None,
                        args.strict, capabilities=capabilities)
    except Exception as exc:
        report = {"schema_version": "1.0", "strict": args.strict, "passed": False,
                  "gate_status": "BLOCK", "issues": [str(exc)], "warnings": [],
                  "capabilities": capabilities or []}
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out = Path(args.out).resolve() if args.out else paper_path.parent / "abstract_contract_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(output, encoding="utf-8")
    checklist = out.with_name("abstract_numeric_checklist.json")
    checklist.write_text(json.dumps({"paper": report.get("paper"), "numbers": report.get("numeric_values", []),
                                     "manual_notice": report.get("manual_notice")}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
