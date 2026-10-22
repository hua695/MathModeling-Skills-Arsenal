#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
heuristic-algorithms robustness_check.py — B 题启发式算法鲁棒性检查工具

面向国赛 B 题（优化决策类），对 GA/SA/PSO/蒙特卡洛等启发式算法执行
随机种子敏感性分析、参数鲁棒性评估、多初值稳定性检验和收敛曲线分析。

输入：
  --config  robustness_plan.yaml  （包含算法配置、参数范围、随机种子数、评估指标）

输出：
  robustness_report.yaml  （包含种子敏感性、参数鲁棒性、收敛稳定性、结论）

用法：
  python scripts/robustness_check.py --config robustness_plan.yaml --out robustness_report.yaml
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

SCHEMA_VERSION = "1.0"
ALLOWED_ALGORITHMS = {"ga", "sa", "pso", "monte_carlo", "greedy", "tabu", "nsga2", "combined"}
ALLOWED_METRICS = {"best_fitness", "mean_fitness", "convergence_rate", "stability_score", "feasibility_rate"}


def load_mapping(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    if yaml is not None:
        value = yaml.safe_load(raw)
        if not isinstance(value, dict):
            raise ValueError(f"计划必须是对象: {path}")
        return value
    raise RuntimeError("读取 YAML 需要 PyYAML；也可以提供 JSON 计划")


def validate_plan(plan: dict[str, Any]) -> list[str]:
    errors = []
    if plan.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version 必须为 {SCHEMA_VERSION}")
    algorithm = plan.get("algorithm")
    if algorithm not in ALLOWED_ALGORITHMS:
        errors.append(f"algorithm 必须为 {sorted(ALLOWED_ALGORITHMS)}，当前: {algorithm}")
    n_seeds = plan.get("n_random_seeds")
    if not isinstance(n_seeds, int) or n_seeds < 3:
        errors.append(f"n_random_seeds 必须为 >=3 的整数，当前: {n_seeds}")
    parameters = plan.get("parameters")
    if not isinstance(parameters, list) or not parameters:
        errors.append("parameters 必须是非空列表")
    else:
        for idx, param in enumerate(parameters):
            if not isinstance(param, dict):
                errors.append(f"parameters[{idx}] 必须为对象")
                continue
            for field in ("name", "baseline", "range"):
                if field not in param:
                    errors.append(f"parameters[{idx}] 缺少 {field}")
    metrics = plan.get("evaluation_metrics")
    if not isinstance(metrics, list) or not metrics:
        errors.append("evaluation_metrics 必须是非空列表")
    else:
        unknown = [m for m in metrics if m not in ALLOWED_METRICS]
        if unknown:
            errors.append(f"evaluation_metrics 包含未知类型: {unknown}")
    stopping_criteria = plan.get("stopping_criteria")
    if not isinstance(stopping_criteria, dict):
        errors.append("stopping_criteria 必须为对象（max_iterations / max_evaluations / tolerance）")
    return errors


def compute_stability(fitness_values: list[float]) -> dict[str, Any]:
    """Compute stability statistics from multiple random seed runs."""
    if not fitness_values:
        return {"status": "no_data", "mean": None, "std": None, "cv": None, "min": None, "max": None}
    mean = statistics.mean(fitness_values)
    std = statistics.stdev(fitness_values) if len(fitness_values) > 1 else 0.0
    cv = (std / abs(mean)) if mean != 0 else float("inf")
    return {
        "status": "computed",
        "mean": round(mean, 6),
        "std": round(std, 6),
        "cv": round(cv, 6),
        "min": round(min(fitness_values), 6),
        "max": round(max(fitness_values), 6),
        "range": round(max(fitness_values) - min(fitness_values), 6),
        "n_runs": len(fitness_values),
    }


def run_robustness_check(plan: dict[str, Any]) -> dict[str, Any]:
    """Execute robustness check for heuristic algorithms.

    Generates a structured report template.  Actual algorithm execution
    requires the user's model and algorithm implementation; this tool
    validates the plan and produces the report skeleton with computed
    stability statistics if result data is provided.
    """
    algorithm = plan.get("algorithm", "unknown")
    n_seeds = plan.get("n_random_seeds", 5)
    parameters = plan.get("parameters", [])
    metrics = plan.get("evaluation_metrics", [])

    # Check if pre-computed results are provided
    seed_results = plan.get("seed_results")
    parameter_results = plan.get("parameter_sweep_results")

    seed_sensitivity = {"status": "manual_required", "note": "需人工执行多随机种子运行后填写结果"}
    if isinstance(seed_results, list) and seed_results:
        fitness_values = [r.get("best_fitness") for r in seed_results if isinstance(r, dict) and "best_fitness" in r]
        if fitness_values:
            seed_sensitivity = compute_stability(fitness_values)
            seed_sensitivity["status"] = "computed_from_provided_results"
            seed_sensitivity["seed_results"] = seed_results

    parameter_robustness = []
    for param in parameters:
        name = param.get("name", "unknown")
        baseline = param.get("baseline")
        prange = param.get("range", [])
        param_entry = {
            "parameter": name,
            "baseline": baseline,
            "test_range": prange,
            "status": "manual_required",
            "note": "需人工执行参数扫描后填写结果",
        }
        if isinstance(parameter_results, dict) and name in parameter_results:
            sweep = parameter_results[name]
            if isinstance(sweep, list) and sweep:
                fitness_values = [r.get("best_fitness") for r in sweep if isinstance(r, dict) and "best_fitness" in r]
                if fitness_values:
                    param_entry["sweep_results"] = compute_stability(fitness_values)
                    param_entry["status"] = "computed_from_provided_results"
        parameter_robustness.append(param_entry)

    # Convergence analysis
    convergence = {"status": "manual_required", "note": "需人工记录收敛曲线后分析"}
    convergence_data = plan.get("convergence_data")
    if isinstance(convergence_data, dict):
        convergence["status"] = "provided"
        convergence["data_summary"] = {
            "has_curve": "curves" in convergence_data,
            "n_points": len(convergence_data.get("curves", [])),
        }

    # Overall conclusion
    overall_stable = seed_sensitivity.get("cv") is not None and seed_sensitivity["cv"] < 0.05
    conclusion = (
        "算法在多随机种子下表现稳定（CV < 5%），可用于竞赛结果报告"
        if overall_stable
        else "算法在多随机种子下稳定性不足（CV >= 5% 或未计算），需增加运行次数或调整参数后重新评估"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "completed" if seed_sensitivity.get("status") == "computed_from_provided_results" else "manual_required",
        "algorithm": algorithm,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_random_seeds": n_seeds,
        "evaluation_metrics": metrics,
        "seed_sensitivity": seed_sensitivity,
        "parameter_robustness": parameter_robustness,
        "convergence_analysis": convergence,
        "overall_stable": overall_stable,
        "conclusion": conclusion,
        "recommendation": (
            "结果可直接用于论文" if overall_stable
            else "建议增加随机种子运行次数至 >=10，或调整算法参数后重新执行鲁棒性检查"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="启发式算法鲁棒性检查工具（B 题优化决策类）")
    parser.add_argument("--config", required=True, help="robustness_plan.yaml 路径")
    parser.add_argument("--out", required=True, help="输出 robustness_report.yaml 路径")
    parser.add_argument("--strict", action="store_true", help="严格模式：计划校验失败时返回非零")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    if not config_path.is_file():
        print(f"ERROR: 配置文件不存在: {config_path}", file=sys.stderr)
        return 1

    try:
        plan = load_mapping(config_path)
    except Exception as exc:
        print(f"ERROR: 配置文件读取失败: {exc}", file=sys.stderr)
        return 1

    errors = validate_plan(plan)
    if errors:
        print("=== 鲁棒性计划校验失败 ===", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        if args.strict:
            return 1

    report = run_robustness_check(plan)

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if yaml is not None:
        out_path.write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    else:
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"=== 鲁棒性检查报告已生成: {out_path} ===")
    print(f"  状态: {report['status']}")
    print(f"  算法: {report['algorithm']}")
    print(f"  随机种子数: {report['n_random_seeds']}")
    print(f"  整体稳定: {report['overall_stable']}")
    print(f"  结论: {report['conclusion']}")
    return 0 if not errors or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
