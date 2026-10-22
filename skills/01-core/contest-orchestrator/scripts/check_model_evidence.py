#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate per-subproblem modeling evidence contracts against the paper source."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - environment diagnostic is reported
    yaml = None

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

from check_modeling_contract import expand_inputs, locate_tex

DEFAULT_COMMON = [
    "problem_mapping", "assumptions", "symbols_units", "result_source", "reliability"
]
ENHANCED_COMMON = [
    "problem_mapping", "assumptions", "symbols_units", "route_comparison",
    "algorithm_card", "intermediate_results", "literature_basis", "innovation_delta",
    "result_source", "reliability"
]
DEFAULT_CAPABILITIES = {
    "mechanistic": ["mechanism_mapping", "formula_derivation"],
    "inverse_identification": ["identifiability", "independent_route"],
    "nonlinear_fitting": ["objective", "parameter_initialization", "termination"],
    "optimization": ["decision_variables", "objective", "constraints", "feasibility_check"],
    "multiobjective": ["objective_tradeoff", "selection_rule"],
    "prediction": ["preprocessing", "data_split", "baseline", "metrics"],
    "evaluation": ["indicator_meaning", "normalization", "weight_source", "ranking_rule"],
    "dynamics": ["state_equation", "initial_boundary", "numerical_method"],
    "simulation": ["scenario_design", "stability_check"],
    "uncertainty": ["sensitivity_or_uncertainty"],
    "robustness": ["robustness_check"],
}
CAPABILITY_ANCHORS = {
    "problem_mapping": r"题目|输入|输出|映射|数据",
    "assumptions": r"假设|假定|合理性|适用范围|误差边界",
    "symbols_units": r"符号|单位|变量|参数",
    "result_source": r"结果|结果文件|JSON|CSV|求解输出|表\s*\d+|图\s*\d+",
    "reliability": r"敏感性|扰动|残差|误差|置信|鲁棒|稳定性|不确定性",
    "mechanism_mapping": r"机理|物理|守恒|反射|传热|状态关系",
    "formula_derivation": r"推导|由.{0,20}式|可得|代入|整理|公式",
    "identifiability": r"可辨识|辨识性|唯一解|参数相关|可识别",
    "independent_route": r"独立路线|解析法|直接计算|数值拟合|交叉印证|两种方法",
    "objective": r"目标函数|损失函数|残差平方|优化目标|最小化|最大化",
    "parameter_initialization": r"初值|初始化|初始参数|网格初值",
    "termination": r"终止条件|收敛条件|迭代停止|容差|最大迭代",
    "decision_variables": r"决策变量|变量取值|配置变量|选择变量",
    "constraints": r"约束|边界|可行域|功率平衡|容量上限",
    "feasibility_check": r"可行性|可行解|约束校验|满足约束",
    "objective_tradeoff": r"权衡|Pareto|多目标|折中|目标冲突",
    "selection_rule": r"选择规则|优选|膝点|综合评分|词典序",
    "preprocessing": r"预处理|缺失|异常值|标准化|归一化|特征工程|清洗",
    "data_split": r"训练集|验证集|测试集|时间划分|交叉验证",
    "baseline": r"基线|baseline|参照模型|对照模型",
    "metrics": r"RMSE|MAE|MAPE|R\^?2|准确率|召回率|F1|评价指标",
    "indicator_meaning": r"指标含义|指标意义|评价维度|正向化|逆向化",
    "normalization": r"归一化|标准化|无量纲|正向化|逆向化",
    "weight_source": r"权重来源|主观权重|客观权重|熵权|AHP|权重确定",
    "ranking_rule": r"排序规则|排名|TOPSIS|综合评价|决策规则",
    "state_equation": r"状态方程|微分方程|守恒方程|动力学方程",
    "initial_boundary": r"初值|边界条件|初始条件",
    "numerical_method": r"数值积分|步长|求解器|龙格|Runge|容差",
    "scenario_design": r"场景|情景|仿真方案|参数组合",
    "stability_check": r"稳定性|步长敏感|守恒|数值误差",
    "sensitivity_or_uncertainty": r"敏感性|扰动|不确定性|置信区间|误差传播",
    "robustness_check": r"鲁棒|稳健|约束扰动|场景扰动|稳定性",
    "route_comparison": r"候选|备选|路线|方案|选择|采用|舍弃|不采用|比较|理由",
    "algorithm_card": r"算法|求解器|适配|初值|初始化|搜索范围|搜索区间|约束处理|终止条件|收敛|局部最优|过拟合|奇异",
    "intermediate_results": r"中间结果|中间量|粗估计|初始估计|阶段性|迭代轨迹|参数表|可行性检查|收敛值|表\s*\d+|图\s*\d+",
}

# These checks measure evidence density, not mathematical truth.  Semantic
# correctness remains a Critic responsibility.
QUALITY_RULES = {
    "problem_mapping": (50, (r"题目|条件|输入|数据", r"输出|目标|变量|映射"), False),
    "assumptions": (50, (r"假设|假定", r"简化|忽略|误差|边界|适用"), False),
    "symbols_units": (30, (r"符号|变量|参数", r"单位|范围|边界"), False),
    "route_comparison": (100, (r"候选|备选|路线|方案", r"选择|采用", r"舍弃|不采用|比较|理由"), False),
    "algorithm_card": (120, (r"算法|求解器", r"初值|初始化|搜索范围|搜索区间", r"约束处理|可行域", r"终止条件|收敛", r"局部最优|过拟合|奇异|重启"), False),
    "intermediate_results": (80, (r"中间结果|中间量|粗估计|初始估计|阶段性|迭代轨迹|参数表", r"表\s*\d+|图\s*\d+|数值|可行性|收敛"), True),
    # A literature mention alone is not evidence.  The two groups require a
    # concrete method/algorithm/parameter basis and an explicit adaptation to
    # this problem's data, constraints, or boundary.
    "literature_basis": (70, (r"文献|参考|论文", r"方法|算法|参数|依据|先例"), False),
    "innovation_delta": (60, (r"改进|调整|扩展|创新|适配|修正|借鉴", r"本题|题目|约束|数据|边界|结果"), False),
    "result_source": (50, (r"结果来源|结果文件|求解输出|代码|数据表|JSON|CSV|复现", r"结果|输出|表\s*\d+|图\s*\d+"), False),
    "reliability": (80, (r"敏感性|扰动|残差|误差|置信|交叉验证", r"鲁棒|稳定性|不确定性|误差传播|重复"), False),
}

CAPABILITY_REGISTRY = Path(__file__).resolve().parents[1] / "planner" / "capability_registry.yaml"


def _capability_map() -> dict[str, list[str]]:
    """Load the shipped registry, with a safe fallback for isolated copies."""
    if yaml is not None and CAPABILITY_REGISTRY.exists():
        try:
            payload = yaml.safe_load(CAPABILITY_REGISTRY.read_text(encoding="utf-8")) or {}
            capabilities = payload.get("capabilities", {})
            if isinstance(capabilities, dict):
                loaded = {str(name): list(value.get("required", []))
                          for name, value in capabilities.items() if isinstance(value, dict)}
                if loaded:
                    return loaded
        except Exception:
            pass
    return DEFAULT_CAPABILITIES


def _common_required(enhanced: bool = False) -> list[str]:
    if enhanced:
        if yaml is not None and CAPABILITY_REGISTRY.exists():
            try:
                payload = yaml.safe_load(CAPABILITY_REGISTRY.read_text(encoding="utf-8")) or {}
                values = payload.get("enhanced_common_required", [])
                if isinstance(values, list) and values:
                    return [str(value) for value in values]
            except Exception:
                pass
        return ENHANCED_COMMON
    if yaml is not None and CAPABILITY_REGISTRY.exists():
        try:
            payload = yaml.safe_load(CAPABILITY_REGISTRY.read_text(encoding="utf-8")) or {}
            values = payload.get("common_required", [])
            if isinstance(values, list) and values:
                return [str(value) for value in values]
        except Exception:
            pass
    return DEFAULT_COMMON


def _discover_card(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).resolve()
    candidates = [root / "model_contract.yaml", root / "model_evidence_card.yaml",
                  root / "model_evidence_cards.yaml",
                  root / "01_需求与规划" / "model_contract.yaml",
                  root / "01_需求与规划" / "model_evidence_card.yaml",
                  root / "01_需求与规划" / "model_evidence_cards.yaml",
                  root / "03_文档" / "model_contract.yaml",
                  root / "03_文档" / "paper" / "model_contract.yaml"]
    return next((p for p in candidates if p.exists()), None)


def _load_yaml(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取模型契约")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("模型契约根节点必须是 mapping")
    return value


def _required_for(item: dict, enhanced: bool = False) -> list[str]:
    required = list(_common_required(enhanced))
    capability_map = _capability_map()
    capabilities = []
    primary = item.get("primary_capability")
    if primary:
        capabilities.append(primary)
    capabilities.extend(item.get("capabilities", []) or [])
    for capability in capabilities:
        required.extend(capability_map.get(str(capability), []))
    return list(dict.fromkeys(required))


def _version_at_least(value: object, target: tuple[int, ...]) -> bool:
    numbers = tuple(int(part) for part in re.findall(r"\d+", str(value)))
    numbers = numbers + (0,) * max(0, len(target) - len(numbers))
    return numbers[:len(target)] >= target


def _quality_for(key: str, value: object, chunk: str) -> dict:
    rule = QUALITY_RULES.get(key)
    if rule is None:
        return {"checked": False, "passed": True, "chars": len(re.sub(r"\s+", "", chunk))}
    default_min, groups, needs_number = rule
    custom = value if isinstance(value, dict) else {}
    try:
        minimum = max(0, int(custom.get("min_chars", default_min)))
    except (TypeError, ValueError):
        minimum = default_min
    compact = re.sub(r"\s+", "", chunk)
    matched = [pattern for pattern in groups if re.search(pattern, chunk, re.I)]
    checks = [len(compact) >= minimum, len(matched) == len(groups)]
    number_ok = (not needs_number) or bool(re.search(r"[-+]?\d+(?:\.\d+)?", chunk))
    checks.append(number_ok)
    return {"checked": True, "passed": all(checks), "chars": len(compact),
            "minimum_chars": minimum, "matched_groups": len(matched),
            "required_groups": len(groups), "number_evidence": number_ok}


def _capability_names(item: dict) -> list[str]:
    values = []
    if item.get("primary_capability"):
        values.append(str(item["primary_capability"]))
    values.extend(str(value) for value in (item.get("capabilities", []) or []))
    return list(dict.fromkeys(values))


def _anchor_ok(text: str, anchor: str) -> bool:
    anchor = re.sub(r"\s+", "", str(anchor))
    compact = re.sub(r"\s+", "", text)
    # Chinese evidence anchors are often only two or three characters (e.g.
    # "假设", "残差"). Require a short but meaningful anchor without rejecting
    # normal CJK labels; ASCII anchors still need four characters.
    min_length = 2 if any("\u4e00" <= char <= "\u9fff" for char in anchor) else 4
    return len(anchor) >= min_length and anchor in compact


def _chinese_number(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    digits = {char: index for index, char in enumerate("一二三四五六七八九", 1)}
    if value == "十":
        return 10
    if value.startswith("十"):
        return 10 + digits.get(value[1:], 0)
    if "十" in value:
        left, right = value.split("十", 1)
        return digits.get(left, 0) * 10 + digits.get(right, 0)
    return digits.get(value)


def _heading_number(title: str) -> str | None:
    match = re.search(r"Q\s*([0-9]+)|问题\s*([一二三四五六七八九十百零一二三四五六七八九]+)", title, re.I)
    if not match:
        return None
    number = match.group(1) or _chinese_number(match.group(2))
    return f"Q{number}" if number else None


def _subproblem_spans(text: str, ids: list[str]) -> dict[str, tuple[int, int]]:
    # Stable source labels are preferred over natural-language headings.
    labeled = list(re.finditer(r"\\label\{subproblem:(Q\d+)\}", text, re.I))
    if labeled:
        spans = {}
        for index, marker in enumerate(labeled):
            qid = marker.group(1).upper()
            if qid not in ids:
                continue
            heading = text.rfind("\\subsection", 0, marker.start())
            start = heading if heading >= 0 else marker.start()
            candidates = [labeled[index + 1].start() if index + 1 < len(labeled) else len(text)]
            # Keep the final question bounded by the next top-level section
            # so that appendix code or later validation prose cannot satisfy
            # (or falsely fail) its modeling evidence checks.
            next_section = re.search(r"\\section\*?\{", text[marker.end():])
            if next_section:
                candidates.append(marker.end() + next_section.start())
            end = min(candidates)
            spans[qid] = (start, end)
        if spans:
            return spans
    headings = list(re.finditer(r"\\subsection\*?\{([^{}]*)\}", text))
    matches = []
    for heading in headings:
        title = heading.group(1)
        if re.search(r"问题\s*[一二三四五六七八九十\d]+|Q\s*[1-9]\b", title, re.I):
            matches.append(heading)
    spans = {}
    for index, heading in enumerate(matches):
        title = heading.group(1)
        qid = _heading_number(title)
        if not qid:
            continue
        if qid in ids:
            spans[qid] = (heading.start(), matches[index + 1].start() if index + 1 < len(matches) else len(text))
    return spans


def _within(path: Path, roots: list[Path]) -> bool:
    candidate = path.resolve()
    return any(candidate == root.resolve() or root.resolve() in candidate.parents for root in roots)


def _source_exists(source: str, root: Path, card_path: Path) -> bool:
    candidates = [(root / source).resolve(), (card_path.parent / source).resolve()]
    roots = [root.resolve(), card_path.parent.resolve()]
    return any(path.exists() and _within(path, roots) for path in candidates)


SENSITIVITY_REPORT_NAMES = ("sensitivity_report.yaml", "sensitivity_report.yml",
                             "robustness_report.yaml", "robustness_report.yml")
SENSITIVITY_REQUIRED_FIELDS = ("schema_version", "status", "results")

# 方法选择质量检查：baseline-first、方法选择理由、防炫技
COMPLEX_CAPABILITIES = {"deep_learning", "reinforcement_learning", "heuristic", "metaheuristic"}
METHOD_JUSTIFICATION_REQUIRED = ("core_conflict", "method_role", "simple_method_failure",
                                  "complex_method_target", "cost_benefit")


def _check_method_selection(item: dict, qid: str) -> list[str]:
    """Check method selection quality: baseline-first, justification, anti-flashy.

    Returns list of warning messages (empty if method selection is adequate).
    """
    warnings = []
    method_selection = item.get("method_selection") if isinstance(item.get("method_selection"), dict) else {}

    # 1. Baseline check: 每个子问题必须有简单基线
    baseline = method_selection.get("baseline")
    if not baseline:
        warnings.append(
            f"{qid}: 缺少 baseline（简单基线模型）。每个子问题必须先建立简单基线，再考虑复杂方法。"
            f"参考 references/method_selection_core.md 的 baseline-first 原则。"
        )
    elif isinstance(baseline, dict):
        if not baseline.get("baseline_method"):
            warnings.append(f"{qid}: baseline 缺少 baseline_method（基线方法名称）")
        if not baseline.get("baseline_result"):
            warnings.append(f"{qid}: baseline 缺少 baseline_result（基线结果）")

    # 2. Method justification check: 方法选择理由
    justification = method_selection.get("method_justification")
    if not justification:
        warnings.append(
            f"{qid}: 缺少 method_justification（方法选择理由）。必须说明为什么选这个方法、为什么不用更简单的方法。"
        )
    elif isinstance(justification, dict):
        missing = [field for field in METHOD_JUSTIFICATION_REQUIRED if not justification.get(field)]
        if missing:
            warnings.append(f"{qid}: method_justification 缺少字段: {', '.join(missing)}")

    # 3. Complexity upgrade check: 使用复杂方法时必须有升级记录
    capabilities = _capability_names(item)
    using_complex = any(cap in COMPLEX_CAPABILITIES for cap in capabilities)
    if using_complex:
        upgrade = method_selection.get("complexity_upgrade")
        if not upgrade:
            warnings.append(
                f"{qid}: 使用复杂方法但缺少 complexity_upgrade（复杂度升级记录）。"
                f"必须记录上一层的哪个缺陷促使升级，禁止跳跃式选择方法。"
            )
        elif isinstance(upgrade, dict):
            if not upgrade.get("upgrade_from") or not upgrade.get("upgrade_to"):
                warnings.append(f"{qid}: complexity_upgrade 缺少 upgrade_from 或 upgrade_to")
            if not upgrade.get("upgrade_reason"):
                warnings.append(f"{qid}: complexity_upgrade 缺少 upgrade_reason（升级原因）")

    # 4. Decision impact test: 使用复杂方法时必须评估对最终决策的影响
    if using_complex:
        impact = method_selection.get("decision_impact")
        if not impact:
            warnings.append(
                f"{qid}: 使用复杂方法但缺少 decision_impact（决策影响测试）。"
                f"必须评估换成简单方法是否改变最终结论。等级<2 建议降级。"
            )
        elif isinstance(impact, dict):
            level = impact.get("impact_level")
            if level is not None:
                try:
                    if int(level) < 2:
                        warnings.append(
                            f"{qid}: decision_impact 等级为 {level}（<2），复杂方法对最终决策影响低，建议降级为简单方法。"
                        )
                except (ValueError, TypeError):
                    pass

    return warnings


def _check_sensitivity_report(root: Path, qid: str) -> list[str]:
    """Check sensitivity/robustness report exists and has valid format.

    Called only when subproblem declares optimization capability.
    Returns list of warning messages (empty if report exists and is valid).
    """
    warnings = []
    report_path = None
    for name in SENSITIVITY_REPORT_NAMES:
        candidate = root / name
        if candidate.is_file():
            report_path = candidate
            break
    if report_path is None:
        # Also check common subdirectories
        for subdir in ("results", "04_结果", "validation", "05_验证"):
            for name in SENSITIVITY_REPORT_NAMES:
                candidate = root / subdir / name
                if candidate.is_file():
                    report_path = candidate
                    break
            if report_path:
                break
    if report_path is None:
        warnings.append(
            f"{qid}: optimization 能力子问题缺少灵敏度/鲁棒性报告（sensitivity_report.yaml 或 robustness_report.yaml）。"
            f"请运行 pyomo/scripts/sensitivity_analysis.py 或 heuristic-algorithms/scripts/robustness_check.py 生成报告。"
        )
        return warnings
    # Validate report format
    try:
        report = _load_yaml(report_path)
    except Exception as exc:
        warnings.append(f"{qid}: 灵敏度报告格式解析失败: {exc}")
        return warnings
    if not isinstance(report, dict):
        warnings.append(f"{qid}: 灵敏度报告根节点必须为对象")
        return warnings
    missing = [field for field in SENSITIVITY_REQUIRED_FIELDS if field not in report]
    if missing:
        warnings.append(f"{qid}: 灵敏度报告缺少必需字段: {', '.join(missing)}")
    if report.get("schema_version") != "1.0":
        warnings.append(f"{qid}: 灵敏度报告 schema_version 必须为 1.0（当前: {report.get('schema_version')}）")
    # P0-02: status 只允许 verified，拒绝 completed/manual_required 空证据通路
    status = report.get("status")
    if status != "verified":
        warnings.append(f"{qid}: 灵敏度报告 status 必须为 verified（当前: {status}）；completed/manual_required 为空证据通路，不得通过")
    # P0-02: 报告必须绑定 subproblem_id，禁止 Q1 报告满足 Q2
    report_qid = report.get("subproblem_id")
    if report_qid and str(report_qid).upper() != qid.upper():
        warnings.append(f"{qid}: 灵敏度报告 subproblem_id({report_qid}) 与当前子问题({qid}) 不匹配，禁止跨小问复用")
    results = report.get("results")
    if results is not None and not isinstance(results, list):
        warnings.append(f"{qid}: 灵敏度报告 results 必须为列表")
    elif isinstance(results, list) and status == "verified":
        # P0-02: 每个扰动点的 objective/feasible/decision_change 必须非空或有明确 not_applicable_reason
        for ridx, result in enumerate(results):
            if not isinstance(result, dict):
                warnings.append(f"{qid}: 灵敏度报告 results[{ridx}] 必须为对象")
                continue
            points = result.get("perturbation_points")
            if isinstance(points, list):
                for pidx, point in enumerate(points):
                    if not isinstance(point, dict):
                        continue
                    for field in ("objective", "feasible", "decision_change"):
                        value = point.get(field)
                        reason = point.get(f"{field}_not_applicable_reason")
                        if value is None and not (isinstance(reason, str) and reason.strip()):
                            warnings.append(
                                f"{qid}: 灵敏度报告 results[{ridx}].perturbation_points[{pidx}].{field} 为空且未提供 not_applicable_reason；"
                                f"verified 状态要求所有扰动点有真实数值或明确的不可用原因"
                            )
    return warnings


def validate(root: Path, card_path: Path | None, strict: bool) -> dict:
    report = {"schema_version": "1.0", "strict": strict, "passed": True,
              "gate_status": "PASS", "issues": [], "warnings": [], "cards": []}
    if card_path is None or not card_path.exists():
        message = "缺少 model_contract.yaml（结构化模型契约）"
        (report["issues"] if strict else report["warnings"]).append(message)
        report["passed"] = not strict
        report["gate_status"] = "BLOCK" if strict else "WARN"
        return report
    try:
        payload = _load_yaml(card_path)
        tex_root = root
        if not list(tex_root.glob("*.tex")):
            tex_root = next((candidate for candidate in (root / "03_文档" / "paper", root / "paper")
                             if candidate.is_dir()), root)
        tex = locate_tex(tex_root)
        text = expand_inputs(tex.read_text(encoding="utf-8", errors="replace"), tex.parent)
    except Exception as exc:
        report["issues"].append(str(exc))
        report["passed"] = False
        report["gate_status"] = "BLOCK"
        return report
    items = payload.get("subproblems")
    if not isinstance(items, list) or not items:
        report["issues"].append("model_contract.yaml 缺少非空 subproblems 列表")
        report["passed"] = False
        report["gate_status"] = "BLOCK"
        return report
    ids = [str(item.get("id", "")) for item in items if isinstance(item, dict)]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"Q\d+", qid) for qid in ids):
        report["issues"].append("subproblems.id 必须唯一且符合 Q1/Q2 格式")
    expected = payload.get("expected_subproblems")
    if expected is None and isinstance(payload.get("project"), dict):
        expected = payload["project"].get("expected_subproblems")
    if isinstance(expected, list) and {str(value) for value in expected} != set(ids):
        report["issues"].append("契约 expected_subproblems 与 subproblems.id 不一致")
    if _version_at_least(payload.get("schema_version", "1.0"), (2, 1)):
        # The capture already includes the canonical ``Q`` prefix (Q1, Q2, ...).
        # Do not prepend another Q, otherwise every valid label becomes QQ1 and
        # enhanced contracts are rejected even when the source is correctly
        # labelled.
        stable_labels = {match.group(1).upper() for match in re.finditer(r"\\label\{subproblem:(Q\d+)\}", text, re.I)}
        if set(ids) != stable_labels:
            report["issues"].append("v2.1 契约要求正文使用完整 subproblem:Qn 稳定标签")
    enhanced = (str(payload.get("evidence_quality", "")).lower() == "enhanced"
                or _version_at_least(payload.get("schema_version", "1.0"), (2, 1)))
    report["evidence_quality"] = "enhanced" if enhanced else "legacy"
    if enhanced:
        report["warnings"].append(
            "启用增强证据质量检查：需补充路线比较、算法卡和中间结果"
        )
    spans = _subproblem_spans(text, ids)
    for item in items:
        if not isinstance(item, dict):
            report["issues"].append("subproblems 中存在非 mapping 项")
            continue
        qid = str(item.get("id", ""))
        chunk = text[slice(*spans[qid])] if qid in spans else ""
        required = _required_for(item, enhanced)
        evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
        missing, anchor_fail, source_fail, quality_fail = [], [], [], []
        statuses = {}
        quality = {}
        for key in required:
            value = evidence.get(key)
            if isinstance(value, bool):
                status = "pass" if value else "fail"
                anchors = [key]
                sources = []
            elif isinstance(value, dict):
                status = str(value.get("status", ""))
                anchors = value.get("text_anchors", value.get("anchors", [])) or []
                sources = value.get("source_files", value.get("sources", [])) or []
            else:
                status, anchors, sources = "", [], []
            if isinstance(anchors, str):
                anchors = [anchors]
            if isinstance(sources, str):
                sources = [sources]
            statuses[key] = status
            if status != "pass":
                missing.append(key)
            evidence_chunk = chunk
            marker = value.get("marker") if isinstance(value, dict) else None
            if marker:
                pattern = (r"%\s*CO-EVIDENCE-BEGIN\s+" + re.escape(str(marker))
                           + r"\s*\n?(.*?)%\s*CO-EVIDENCE-END\s+" + re.escape(str(marker)))
                match = re.search(pattern, chunk, re.S | re.I)
                if match:
                    evidence_chunk = match.group(1)
                else:
                    anchor_fail.append(key)
            if (not anchors) or not all(isinstance(anchor, str) and _anchor_ok(evidence_chunk, anchor)
                                                        for anchor in anchors):
                if key not in anchor_fail:
                    anchor_fail.append(key)
            for source in sources:
                if not _source_exists(str(source), root, card_path):
                    source_fail.append(f"{key}:{source}")
            if enhanced and status == "pass":
                quality_item = _quality_for(key, value, evidence_chunk)
                quality[key] = quality_item
                if not quality_item["passed"]:
                    quality_fail.append(key)
        unknown = [name for name in _capability_names(item) if name not in _capability_map()]
        if unknown:
            report["issues"].append(f"{qid} 使用未注册能力: {', '.join(unknown)}")
        report["cards"].append({"id": qid, "capabilities": _capability_names(item),
                                "required": required, "statuses": statuses,
                                "missing": missing, "anchor_fail": anchor_fail,
                                "source_fail": source_fail, "quality": quality,
                                "quality_fail": quality_fail})
        if missing:
            report["issues"].append(f"{qid} 缺少必需证据: {', '.join(missing)}")
        if anchor_fail:
            report["issues"].append(f"{qid} 证据锚点未在本子问题正文出现: {', '.join(anchor_fail)}")
        if source_fail:
            report["issues"].append(f"{qid} 证据来源文件不存在或超出项目根目录: {', '.join(source_fail)}")
        if quality_fail:
            report["issues"].append(f"{qid} 证据段落信息密度不足: {', '.join(quality_fail)}")
        # Task 6: optimization capability requires sensitivity/robustness report
        caps = _capability_names(item)
        if "optimization" in caps or "robustness" in caps or "uncertainty" in caps:
            sens_warnings = _check_sensitivity_report(root, qid)
            report["warnings"].extend(sens_warnings)
        # 方法选择质量检查：baseline-first、方法选择理由、防炫技
        # 保持 WARN 级别：方法选择是主观判断，不直接阻塞交付，由人工确认
        method_warnings = _check_method_selection(item, qid)
        report["warnings"].extend(method_warnings)
    if not report["issues"]:
        report["passed"] = True
        report["gate_status"] = "PASS"
    elif not strict:
        report["warnings"].extend(report["issues"])
        report["issues"] = []
        report["passed"] = True
        report["gate_status"] = "WARN"
    else:
        report["passed"] = False
        report["gate_status"] = "BLOCK"
    report["card"] = str(card_path)
    report["tex"] = str(tex)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_or_paper")
    parser.add_argument("--card", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_or_paper).resolve()
    paper_root = root if root.is_dir() and list(root.glob("*.tex")) else root / "03_文档" / "paper"
    report = validate(root if root.is_dir() else root.parent, _discover_card(root, args.card), args.strict)
    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
