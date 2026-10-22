#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_numerical_sanity.py — 数值合理性检查
检测"代码运行了但结果是错的"：inf/nan、目标值量级异常、结果文件不完整、决策变量超出物理范围。

用法: python scripts/check_numerical_sanity.py <项目根目录> [--strict] [--out report.json]
返回每项 PASS/WARN，供 H5 解题后自检使用。
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

# 结果文件搜索模式
RESULT_FILE_PATTERNS = [
    "result_registry.yaml",
    "result_registry.json",
    "results/**/*.json",
    "results/**/*.csv",
    "04_结果/**/*.json",
    "04_结果/**/*.csv",
    "output/**/*.json",
    "output/**/*.csv",
    "*.json",
    "*.csv",
]

# 目标值字段名（常见的目标函数/结果字段）
OBJECTIVE_FIELD_PATTERNS = [
    r"objective", r"obj", r"cost", r"profit", r"revenue", r"distance",
    r"time", r"duration", r"value", r"score", r"fitness", r"optimal",
    r"目标", r"最优", r"成本", r"利润", r"距离", r"时间", r"收益",
    r"总航行距离", r"遮蔽时长", r"总收益", r"总成本",
]

# 物理量范围（用于检测决策变量超出物理范围）
PHYSICAL_RANGE_HINTS = {
    "probability": (0.0, 1.0),
    "percentage": (0.0, 100.0),
    "speed": (0.0, 3e8),  # 不超过光速
    "distance": (0.0, 1e12),
    "time": (0.0, 1e10),
    "count": (0, 1e12),
}


def find_result_files(root: Path) -> list[Path]:
    """在项目根目录下搜索结果文件。"""
    files = []
    seen = set()
    for pattern in RESULT_FILE_PATTERNS:
        for path in root.glob(pattern):
            if path.is_file() and path.suffix in (".json", ".csv", ".yaml", ".yml"):
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    files.append(path)
    return files


def check_inf_nan_in_json(data: dict | list, path: str = "") -> list[str]:
    """递归检查 JSON 数据中的 inf/nan。"""
    issues = []
    if isinstance(data, dict):
        for key, value in data.items():
            issues.extend(check_inf_nan_in_json(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(data, list):
        for i, value in enumerate(data):
            issues.extend(check_inf_nan_in_json(value, f"{path}[{i}]"))
    elif isinstance(data, float):
        if math.isinf(data):
            issues.append(f"{path}: 值为 inf（无穷大）")
        elif math.isnan(data):
            issues.append(f"{path}: 值为 nan（非数字）")
    return issues


def check_inf_nan_in_csv(text: str, filename: str) -> list[str]:
    """检查 CSV 文件中的 inf/nan。"""
    issues = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if re.search(r"\b(inf|nan|infinity)\b", line, re.IGNORECASE):
            issues.append(f"{filename} 第{i+1}行: 检测到 inf/nan 值: {line.strip()[:100]}")
    return issues


def check_objective_magnitude(data: dict | list, path: str = "") -> list[str]:
    """检查目标值量级是否异常。"""
    issues = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()
            # 检查是否是目标值字段
            is_objective = any(re.search(pattern, key_lower) for pattern in OBJECTIVE_FIELD_PATTERNS)
            if is_objective and isinstance(value, (int, float)) and not isinstance(value, bool):
                if math.isinf(value) or math.isnan(value):
                    continue  # 已经在 inf/nan 检查中覆盖
                abs_value = abs(value)
                # 量级异常检测：过大或过小
                if abs_value > 1e15:
                    issues.append(
                        f"{path}.{key}: 目标值 {value} 量级过大（>1e15），"
                        f"可能是单位错误或计算溢出"
                    )
                elif abs_value < 1e-15 and value != 0:
                    issues.append(
                        f"{path}.{key}: 目标值 {value} 量级过小（<1e-15），"
                        f"可能是单位错误或数值不稳定"
                    )
            issues.extend(check_objective_magnitude(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(data, list):
        for i, value in enumerate(data):
            issues.extend(check_objective_magnitude(value, f"{path}[{i}]"))
    return issues


def check_file_completeness(filepath: Path) -> list[str]:
    """检查结果文件是否完整（非空、有内容、格式正确）。"""
    issues = []
    if filepath.stat().st_size == 0:
        issues.append(f"{filepath.name}: 文件为空（0 字节）")
        return issues

    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        issues.append(f"{filepath.name}: 读取文件失败: {exc}")
        return issues

    if len(text.strip()) < 10:
        issues.append(f"{filepath.name}: 文件内容过少（<10 字符），可能不完整")

    # JSON 格式检查
    if filepath.suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            issues.append(f"{filepath.name}: JSON 格式错误: {exc}")

    # CSV 格式检查：行数和列数一致性
    if filepath.suffix == ".csv":
        lines = [line for line in text.split("\n") if line.strip()]
        if len(lines) < 2:
            issues.append(f"{filepath.name}: CSV 行数过少（<2 行），可能不完整")
        else:
            header_cols = len(lines[0].split(","))
            for i, line in enumerate(lines[1:], 2):
                cols = len(line.split(","))
                if cols != header_cols:
                    issues.append(
                        f"{filepath.name} 第{i}行: 列数不一致（表头 {header_cols} 列，当前 {cols} 列）"
                    )
                    break  # 只报告第一个不一致

    return issues


def check_physical_range(data: dict | list, path: str = "") -> list[str]:
    """检查决策变量是否超出物理范围。"""
    issues = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()
            for range_name, (min_val, max_val) in PHYSICAL_RANGE_HINTS.items():
                if range_name in key_lower and isinstance(value, (int, float)) and not isinstance(value, bool):
                    if value < min_val or value > max_val:
                        issues.append(
                            f"{path}.{key}: 值 {value} 超出物理范围 [{min_val}, {max_val}]"
                            f"（{range_name}）"
                        )
            issues.extend(check_physical_range(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(data, list):
        for i, value in enumerate(data):
            issues.extend(check_physical_range(value, f"{path}[{i}]"))
    return issues


def check(root: Path, strict: bool = False) -> dict:
    """主检查函数。"""
    if not root.exists():
        return {"passed": False, "gate_status": "FAIL", "error": f"项目目录不存在: {root}",
                "result_files_scanned": 0, "warnings": [], "warning_count": 0,
                "checks": {"inf_nan": "FAIL", "objective_magnitude": "FAIL",
                           "file_completeness": "FAIL", "physical_range": "FAIL"}}

    result_files = find_result_files(root)
    all_warnings = []
    checks = {
        "inf_nan": "PASS",
        "objective_magnitude": "PASS",
        "file_completeness": "PASS",
        "physical_range": "PASS",
    }

    if not result_files:
        all_warnings.append("未找到任何结果文件（.json/.csv/.yaml），请确认结果已输出")
        checks["file_completeness"] = "WARN"
    else:
        for filepath in result_files:
            # 1. 文件完整性检查
            completeness_issues = check_file_completeness(filepath)
            if completeness_issues:
                all_warnings.extend(completeness_issues)
                checks["file_completeness"] = "WARN"

            # 读取文件内容
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # 2. inf/nan 检查
            if filepath.suffix == ".json":
                try:
                    data = json.loads(text)
                    inf_nan_issues = check_inf_nan_in_json(data, filepath.name)
                    if inf_nan_issues:
                        all_warnings.extend(inf_nan_issues[:10])  # 最多报告10个
                        checks["inf_nan"] = "WARN"
                except json.JSONDecodeError:
                    pass  # 已经在完整性检查中覆盖
            elif filepath.suffix == ".csv":
                inf_nan_issues = check_inf_nan_in_csv(text, filepath.name)
                if inf_nan_issues:
                    all_warnings.extend(inf_nan_issues[:10])
                    checks["inf_nan"] = "WARN"

            # 3. 目标值量级检查（仅 JSON）
            if filepath.suffix == ".json":
                try:
                    data = json.loads(text)
                    magnitude_issues = check_objective_magnitude(data, filepath.name)
                    if magnitude_issues:
                        all_warnings.extend(magnitude_issues[:10])
                        checks["objective_magnitude"] = "WARN"
                except json.JSONDecodeError:
                    pass

            # 4. 物理范围检查（仅 JSON）
            if filepath.suffix == ".json":
                try:
                    data = json.loads(text)
                    physical_issues = check_physical_range(data, filepath.name)
                    if physical_issues:
                        all_warnings.extend(physical_issues[:10])
                        checks["physical_range"] = "WARN"
                except json.JSONDecodeError:
                    pass

    passed = len(all_warnings) == 0
    gate_status = "PASS" if passed else ("BLOCK" if strict else "WARN")

    return {
        "schema_version": "1.0",
        "passed": passed,
        "gate_status": gate_status,
        "strict": strict,
        "project_root": str(root),
        "result_files_scanned": len(result_files),
        "warnings": all_warnings,
        "warning_count": len(all_warnings),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="项目根目录")
    parser.add_argument("--strict", action="store_true", help="WARN 也视为不通过")
    parser.add_argument("--out", default=None, help="输出 JSON 报告路径")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    report = check(root, args.strict)

    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 打印摘要
    print(f"数值合理性检查: {report['gate_status']}")
    print(f"扫描结果文件: {report['result_files_scanned']} 个")
    c = report["checks"]
    print(f"检查项: inf_nan={c['inf_nan']}, objective_magnitude={c['objective_magnitude']}, "
          f"file_completeness={c['file_completeness']}, physical_range={c['physical_range']}")
    if report["warnings"]:
        print(f"\n发现 {report['warning_count']} 个问题:")
        for w in report["warnings"][:20]:
            print(f"  - {w}")
        if len(report["warnings"]) > 20:
            print(f"  ... 还有 {len(report['warnings']) - 20} 个问题，详见报告")

    return 0 if report["passed"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
