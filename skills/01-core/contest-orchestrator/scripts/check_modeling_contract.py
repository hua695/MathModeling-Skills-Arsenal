#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check the universal modeling chapter contract without modifying a paper."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MODEL_RE = re.compile(r"模型建立与求解|模型建立|model\s+(?:formulation|establishment|solution)", re.I)
VALIDATION_RE = re.compile(r"模型检验|灵敏度分析|模型评价|validation|sensitivity", re.I)
REFERENCE_RE = re.compile(r"参考文献|bibliography|thebibliography|printbibliography", re.I)
APPENDIX_RE = re.compile(r"附录|appendix", re.I)
LEAK_RE = re.compile(r"为什么选择|选择该模型的原因|模型选型依据|舍弃(?:了)?(?:其他|其余)|为何选用", re.I)
HEADING_RE = re.compile(r"\\subsection\*?\{([^{}]*)\}|\\subsubsection\*?\{([^{}]*)\}")
SUBSUBSECTION_RE = re.compile(r"\\subsubsection\*?\{([^{}]*)\}")
PROBLEM_BOUNDARY_RE = re.compile(r"\\subsection\*?\{([^{}]*)\}")
PROBLEM_RE = re.compile(r"(?:问题|problem|question)\s*[一二三四五六七八九十\d]+|(?<![A-Za-z_])Q\s*[1-9]\b", re.I)
DEFAULT_PROFILES = {
    "mechanistic_optimization": {"required_sections": ["思路", "假设", "模型", "求解", "结果"],
                                  "required_evidence": ["assumptions", "derivation", "algorithm", "result", "reliability"]},
    "data_prediction": {"required_sections": ["思路", "数据", "模型", "求解", "结果"],
                         "required_evidence": ["assumptions", "preprocessing", "baseline", "split", "metrics", "reliability"]},
    "evaluation_decision": {"required_sections": ["思路", "指标", "权重", "求解", "结果"],
                             "required_evidence": ["assumptions", "indicator_meaning", "weight_source", "result", "reliability"]},
    "simulation_dynamics": {"required_sections": ["思路", "状态方程", "初值", "求解", "结果"],
                             "required_evidence": ["assumptions", "derivation", "initial_boundary", "numerical_method", "result", "reliability"]},
    "hybrid": {"required_sections": ["思路", "接口", "模型", "求解", "结果"],
               "required_evidence": ["assumptions", "derivation", "algorithm", "result", "reliability", "interface"]},
    "statistical_inference": {"required_sections": ["思路", "数据结构", "指标", "推断", "结果"],
                               "required_evidence": ["assumptions", "preprocessing", "indicator_meaning", "result", "reliability"]},
    "classification": {"required_sections": ["思路", "数据", "分类模型", "阈值", "结果"],
                        "required_evidence": ["assumptions", "preprocessing", "split", "baseline", "metrics", "result", "reliability"]},
    "grouping_threshold": {"required_sections": ["思路", "分组变量", "阈值规则", "求解", "结果"],
                            "required_evidence": ["assumptions", "preprocessing", "indicator_meaning", "result", "reliability"]},
    "network_graph": {"required_sections": ["思路", "网络定义", "模型", "求解", "结果"],
                       "required_evidence": ["assumptions", "variable_definition", "derivation", "algorithm", "result", "reliability"]},
    "uncertainty": {"required_sections": ["思路", "不确定性来源", "传播方法", "结果"],
                    "required_evidence": ["assumptions", "uncertainty_source", "result", "reliability"]},
}
EVIDENCE_PATTERNS = {
    "assumptions": r"假设|假定|合理性|适用范围|误差边界|忽略",
    "derivation": r"推导|由.{0,12}式|可得|公式|equation|\\begin\{equation",
    "algorithm": r"算法|求解器|初值|搜索区间|终止条件|迭代|收敛|局部最优|超参数",
    "result": r"结果|表\s*\d+|图\s*\d+|RMSE|MAE|R\^?2|最优|拟合|预测",
    "reliability": r"敏感性|扰动|残差|误差|置信|交叉验证|鲁棒|稳定性|不确定性",
    "preprocessing": r"预处理|缺失|异常值|标准化|归一化|特征工程|清洗",
    "baseline": r"基线|baseline|参照模型|对照模型",
    "split": r"训练集|验证集|测试集|交叉验证|时间划分",
    "metrics": r"RMSE|MAE|MAPE|R\^?2|准确率|召回率|F1|评价指标",
    "indicator_meaning": r"指标含义|指标意义|评价维度|正向化|逆向化",
    "weight_source": r"权重来源|主观权重|客观权重|熵权|AHP|权重确定",
    "weight_sensitivity": r"权重敏感|排序稳定|权重扰动",
    "initial_boundary": r"初值|边界条件|初始条件",
    "numerical_method": r"数值积分|步长|求解器|龙格|Runge|稳定性",
    "step_sensitivity": r"步长敏感|步长扰动|守恒|残差",
    "interface": r"接口变量|子问题接口|耦合|传递变量|组合约束",
    "cross_model_consistency": r"交叉验证|交叉印证|一致性|模型对比|路线对比",
    "uncertainty": r"不确定性|置信区间|区间估计|风险",
    "uncertainty_source": r"不确定性来源|误差来源|噪声来源|参数不确定",
    "effect_size": r"效应量|差异量|效果量|影响大小",
    "diagnostics": r"诊断|残差诊断|正态性|方差齐性|拟合优度",
    "row_grain": r"一行数据|样本粒度|观测单位|记录粒度",
    "repeated_measure_handling": r"重复测量|主体ID|个体内|聚类稳健",
    "class_balance": r"类别不平衡|类别比例|少数类|重采样",
    "imbalance_strategy": r"不平衡处理|类别权重|过采样|欠采样|SMOTE",
    "threshold_strategy": r"阈值选择|分类阈值|决策阈值|代价敏感",
    "leakage_audit": r"数据泄漏|目标泄漏|时间泄漏|主体泄漏",
    "group_definition": r"分组定义|组别定义|分组变量",
    "threshold_selection": r"阈值确定|阈值选择|截点确定",
    "decision_interface": r"决策接口|决策规则|预测到决策|行动规则",
    "node_edge_definition": r"节点定义|边定义|节点与边|网络构造",
    "weight_meaning": r"权重含义|边权|权重表示",
    "complexity_analysis": r"复杂度|时间复杂度|计算复杂度",
    "distribution_or_scenario": r"分布假设|情景设计|场景设计|概率分布",
    "coverage_statement": r"覆盖率|适用范围|区间覆盖",
}


def locate_tex(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = sorted(path.glob("paper*.tex")) or sorted(path.glob("*.tex"))
    if not candidates:
        raise FileNotFoundError(f"未找到 TeX 文件: {path}")
    return candidates[0]


def clean_tex(text: str) -> str:
    return re.sub(r"(?m)^\s*%.*$", "", text)


def expand_inputs(text: str, base: Path, seen: set[Path] | None = None) -> str:
    r"""Inline local \input/\include files for structural checks only."""
    seen = set() if seen is None else seen
    pattern = re.compile(r"\\(?:input|include)\{([^{}]+)\}")

    def replace(match: re.Match[str]) -> str:
        candidate = base / match.group(1).strip()
        if candidate.suffix == "":
            candidate = candidate.with_suffix(".tex")
        candidate = candidate.resolve()
        if candidate in seen or not candidate.exists() or not candidate.is_file():
            return match.group(0)
        seen.add(candidate)
        try:
            child = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return match.group(0)
        return expand_inputs(child, candidate.parent, seen)

    return pattern.sub(replace, text)


def section_spans(text: str) -> list[tuple[str, int, int]]:
    matches = list(re.finditer(r"\\section\*?\{([^{}]*)\}", text))
    return [(m.group(1), m.start(), matches[i + 1].start() if i + 1 < len(matches) else len(text))
            for i, m in enumerate(matches)]


def load_profile(name: str, config_path: str | None = None) -> dict:
    profile = dict(DEFAULT_PROFILES.get(name, DEFAULT_PROFILES["mechanistic_optimization"]))
    path = Path(config_path) if config_path else Path(__file__).resolve().parents[1] / "planner" / "modeling_profiles.yaml"
    try:
        import yaml
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        configured = ((payload.get("profiles") or {}).get(name) or {})
        for key in ("required_sections", "required_evidence"):
            if configured.get(key):
                profile[key] = list(configured[key])
    except Exception:
        pass
    return profile


def _modeling_structure_issues(chunk: str, problem_header_end: int) -> list[str]:
    """Check the reader-facing shape of one question in strict mode."""
    issues: list[str] = []
    inner_headings = list(SUBSUBSECTION_RE.finditer(chunk))
    lead_end = inner_headings[0].start() if inner_headings else len(chunk)
    lead = chunk[problem_header_end:lead_end]
    lead_visible = re.sub(r"(?s)\\begin\{.*?\}|\\end\{.*?\}|\\[A-Za-z]+(?:\*|\[[^]]*\])?(?:\{[^{}]*\})?", "", lead)
    visible_count = len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", lead_visible))
    if visible_count < 30:
        issues.append("问题引入与建模思路段缺失或过短")

    titles = [match.group(1).strip() for match in inner_headings]
    if "模型建立" not in titles:
        issues.append("缺少独立的模型建立小节")
    if "模型求解与结果分析" not in titles:
        issues.append("缺少独立的模型求解与结果分析小节")

    model_index = titles.index("模型建立") if "模型建立" in titles else None
    if model_index is not None:
        model_start = inner_headings[model_index].end()
        model_end = inner_headings[model_index + 1].start() if model_index + 1 < len(inner_headings) else len(chunk)
        model_text = chunk[model_start:model_end]
        marker = model_text.find("最终求解模型")
        if marker < 0:
            issues.append("模型建立小节末尾缺少最终求解模型框")
        elif not re.search(r"\\begin\{(?:equation|align|gather|multline|cases)\}|\\\[|\\\(|\$\$", model_text[marker:], re.I):
            issues.append("最终求解模型框缺少可计算的数学表达式")
    return issues


def _problem_reports(model_text: str, profile: dict, strict: bool) -> list[dict]:
    headings = list(HEADING_RE.finditer(model_text))
    reports = []
    # Only subsection headings count as problem boundaries; occurrences such as
    # “问题一中……” in prose must not create phantom Q1 records.
    problem_headers = [h for h in PROBLEM_BOUNDARY_RE.finditer(model_text)
                       if PROBLEM_RE.search(h.group(1) or "")]
    if not problem_headers:
        return []
    required = list(profile.get("required_sections", []))
    for index, match in enumerate(problem_headers, 1):
        start = match.start()
        end = problem_headers[index].start() if index < len(problem_headers) else len(model_text)
        chunk = model_text[start:end]
        missing = [term for term in required if term not in chunk]
        structure_issues = _modeling_structure_issues(chunk, match.end() - start) if strict else []
        evidence_keys = list(profile.get("required_evidence", []))
        evidence = {
            key: bool(re.search(EVIDENCE_PATTERNS.get(key, re.escape(key)), chunk, re.I))
            for key in evidence_keys
        }
        evidence_missing = [key for key, found in evidence.items() if not found]
        result_evidence = len(re.findall(r"结果|表\s*\d+|图\s*\d+|RMSE|MAE|R\^?2|最优|拟合", chunk, re.I))
        reports.append({"problem_id": f"Q{index}", "heading": match.group(1) or match.group(2),
                        "sections": [h.group(1) or h.group(2) for h in headings if start <= h.start() < end],
                        "missing": missing, "evidence": evidence, "evidence_missing": evidence_missing,
                        "structure_issues": structure_issues,
                        "result_evidence": result_evidence,
                        "passed": not strict or (not missing and not evidence_missing and not structure_issues)})
    return reports


def _pdf_page_ratio(pdf_path: Path | None) -> tuple[float, dict] | None:
    """Use rendered pages when a fresh PDF is available; otherwise fall back."""
    if pdf_path is None or not pdf_path.exists():
        return None
    try:
        import pymupdf
        with pymupdf.open(str(pdf_path)) as document:
            pages = [page.get_text("text") for page in document]
    except Exception:
        return None
    if not pages:
        return None
    def heading_page(pattern: re.Pattern[str]) -> int | None:
        # Match standalone section-heading lines rather than prose mentions.
        # A heading can begin near the bottom of a page, so do not restrict the
        # scan to the first 16 lines; exact matching prevents false positives.
        exact_by_pattern = {
            id(MODEL_RE): {"模型建立与求解", "模型建立", "model formulation", "model establishment"},
            id(VALIDATION_RE): {"模型检验与灵敏度分析", "模型评价与推广", "validation", "sensitivity"},
            id(REFERENCE_RE): {"参考文献", "bibliography", "thebibliography", "printbibliography"},
        }
        exact = exact_by_pattern.get(id(pattern), set())
        for index, text in enumerate(pages):
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            for line in lines:
                normalized = re.sub(r"\s+", " ", line).strip()
                normalized_key = normalized.casefold()
                exact_keys = {item.casefold() for item in exact}
                if normalized_key in exact_keys or (not exact and pattern.fullmatch(normalized)):
                    return index
        return None

    model_page = heading_page(MODEL_RE)
    if model_page is None:
        return None
    body_start = (0 if pages and re.search(r"摘要", pages[0]) else
                  next((i for i, text in enumerate(pages)
                        if re.search(r"问题重述|问题分析|问题理解|problem\s+(?:restatement|analysis)", text, re.I)), 0))
    ref_page = heading_page(REFERENCE_RE) or len(pages)
    appendix_page = heading_page(re.compile(r"附录(?:[A-Z]|\s|$)|appendix", re.I)) or ref_page
    body_end = min(ref_page, appendix_page)
    validation_page = next((i for i in range(model_page + 1, len(pages))
                            if heading_page(VALIDATION_RE) == i or heading_page(REFERENCE_RE) == i), body_end)
    body_pages = max(1, body_end - body_start)
    model_pages = max(0, min(validation_page, body_end) - model_page)
    if model_pages == 0:
        return None
    return model_pages / body_pages, {
        "measurement": "pdf_rendered_page_count",
        "pdf": str(pdf_path.resolve()), "model_start_page": model_page + 1,
        "model_end_page_exclusive": min(validation_page, body_end) + 1,
        "body_start_page": body_start + 1, "body_end_page_exclusive": body_end + 1,
        "model_pages": model_pages, "body_pages": body_pages,
    }


def check(text: str, profile: str = "mechanistic_optimization", minimum: float = 0.45,
          maximum: float = 0.55, warning_below: float = 0.42, *, strict: bool = False,
          profile_config: str | None = None, pdf_path: Path | None = None) -> dict:
    source = clean_tex(text)
    spans = section_spans(source)
    model = next((s for s in spans if MODEL_RE.search(s[0])), None)
    validation = next((s for s in spans if VALIDATION_RE.search(s[0])), None)
    references = next((s for s in spans if REFERENCE_RE.search(s[0])), None)
    appendix_pos = next((m.start() for m in APPENDIX_RE.finditer(source)), None)
    body_end = min((x[1] for x in (references,) if x), default=appendix_pos or len(source))
    body_end = body_end if body_end > 0 else len(source)
    model_len = 0
    model_text = ""
    if model:
        model_end = validation[1] if validation and validation[1] > model[1] else body_end
        model_len = max(0, model_end - model[1])
        model_text = source[model[1]:model_end]
    body_start = spans[0][1] if spans else 0
    body_len = max(1, body_end - body_start)
    ratio = model_len / body_len if model else 0.0
    measurement = "tex_structural_character_count"
    page_details = None
    pdf_ratio = _pdf_page_ratio(pdf_path)
    if pdf_ratio is not None:
        ratio, page_details = pdf_ratio
        measurement = page_details["measurement"]
    issues: list[str] = []
    warnings: list[str] = []
    if not model:
        issues.append("未识别模型建立与求解章节")
    elif ratio < warning_below:
        issues.append(f"模型章节占正文结构比例 {ratio:.1%} 低于阻断阈值 {warning_below:.0%}")
    elif ratio < minimum:
        warnings.append(f"模型章节占比 {ratio:.1%} 低于目标下限 {minimum:.0%}")
    elif ratio > maximum:
        warnings.append(f"模型章节占比 {ratio:.1%} 高于目标上限 {maximum:.0%}")
    if validation:
        leaked = LEAK_RE.findall(source[validation[1]:validation[2]])
        if leaked:
            issues.append("检验章节包含模型选型叙事: " + "、".join(sorted(set(leaked))))
    subs = [a or b for a, b in HEADING_RE.findall(model_text)] if model else []
    structure_terms = ("思路", "约束", "求解", "结果")
    missing_structure = [term for term in structure_terms if model and term not in model_text]
    if missing_structure:
        warnings.append("模型章节可能缺少固定结构要素: " + "、".join(missing_structure))
    cfg = load_profile(profile, profile_config)
    subproblems = _problem_reports(model_text, cfg, strict)
    if strict:
        symbol_heading_count = len(re.findall(r"\\(?:section|subsection)\*?\{[^{}]*符号说明[^{}]*\}", source))
        if symbol_heading_count != 1:
            issues.append(f"全局符号说明必须在前文统一出现一次，当前 {symbol_heading_count} 次")
        for item in subproblems:
            if not item["passed"]:
                missing = (item["missing"] + item.get("structure_issues", [])
                           + [f"证据:{key}" for key in item["evidence_missing"]])
                issues.append(f"{item['problem_id']} 缺少建模模板证据: " + "、".join(missing))
    status = "BLOCK" if issues else ("WARN" if warnings else "PASS")
    return {"schema_version": "2.0", "profile": profile, "passed": not issues,
            "gate_status": status, "issues": issues, "warnings": warnings,
            "model_section": model[0] if model else None,
            "validation_section": validation[0] if validation else None,
            "model_ratio": round(ratio, 4), "measurement": measurement,
            "page_details": page_details,
            "thresholds": {"min": minimum, "max": maximum, "warning_below": warning_below},
            "subsection_count": len(subs), "subproblems": subproblems,
            "body_characters": body_len, "model_characters": model_len,
            "profile_requirements": cfg.get("required_evidence", [])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper")
    parser.add_argument("--profile", default="mechanistic_optimization")
    parser.add_argument("--config", default=None, help="competition_gates.yaml")
    parser.add_argument("--profile-config", default=None, help="modeling_profiles.yaml")
    parser.add_argument("--pdf", default=None, help="freshly compiled PDF; enables rendered-page ratio")
    parser.add_argument("--competition", default="guosai")
    parser.add_argument("--contract-strict", action="store_true", help="按 profile 对每个问题执行结构证据门禁")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    try:
        tex = locate_tex(Path(args.paper).resolve())
        minimum, maximum, warning_below = 0.45, 0.55, 0.42
        if args.config:
            try:
                import yaml
                cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")).get(args.competition, {})
                minimum = float(cfg.get("model_chapter_ratio_min", minimum))
                maximum = float(cfg.get("model_chapter_ratio_max", maximum))
                warning_below = float(cfg.get("model_chapter_ratio_warning_below", warning_below))
            except Exception:
                pass
        source = expand_inputs(tex.read_text(encoding="utf-8", errors="replace"), tex.parent)
        report = check(source, args.profile, minimum, maximum, warning_below,
                       strict=args.contract_strict, profile_config=args.profile_config,
                       pdf_path=Path(args.pdf).resolve() if args.pdf else None)
        report["tex"] = str(tex)
    except Exception as exc:
        report = {"schema_version": "2.0", "passed": False, "gate_status": "BLOCK",
                  "issues": [str(exc)], "warnings": [], "subproblems": []}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
