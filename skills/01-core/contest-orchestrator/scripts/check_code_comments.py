#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_code_comments.py — 代码注释质量检查
检测AI生成代码的通病：缺少必要注释、注释包含元话语/负向回响/内部讨论。
检查Python文件：文件头说明、函数docstring、复杂逻辑行内注释、关键参数说明、注释内容红线。

用法: python scripts/check_code_comments.py <代码目录或文件> [--strict]
返回每项 PASS/WARN，供 H5 解题后自检使用。
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

# 注释内容红线禁词（注释中出现这些词说明不是纯粹技术说明）
COMMENT_REDLINE_PATTERNS = [
    # 内部讨论话语
    r"经讨论", r"讨论后", r"我们认为", r"大家一致", r"团队决定",
    r"agent建议", r"agent说", r"用户要求", r"用户说", r"按要求",
    # AI思考过程
    r"首先", r"其次", r"然后", r"最后", r"接下来", r"让我", r"我来",
    r"经过分析", r"分析后", r"考虑到", r"综上所述", r"由此可知",
    # 元话语
    r"本文将", r"本节将", r"本章将", r"以下代码", r"以下函数", r"以下是",
    r"接下来我们", r"我们将", r"本文介绍", r"本节介绍",
    # 负向回响
    r"之前用", r"之前尝试", r"原来的", r"旧版本", r"v1", r"v2", r"v3",
    r"修正了", r"修复了", r"改了", r"换成", r"不用", r"放弃", r"失败",
    # AI协作痕迹
    r"agent", r"prompt", r"审查", r"修改清单", r"由H\d", r"生成",
    r"AI生成", r"模型输出", r"调用了", r"子agent",
]

# 关键参数关键词（这些参数应该有注释说明含义和来源）
KEY_PARAMETER_PATTERNS = [
    r"T0|T_init|initial_temp", r"alpha|cooling", r"max_iter|n_iter|num_iter",
    r"pop_size|population", r"crossover|cross_rate", r"mutation|mut_rate",
    r"learning_rate|lr", r"batch_size", r"n_estimators|n_trees",
    r"threshold|tol|epsilon", r"seed|random_state", r"n_folds|cv",
    r"penalty|C|lambda", r"n_clusters|k", r"window|lag",
]


def find_python_files(path: Path) -> list[Path]:
    """Find all Python files in directory or return single file."""
    if path.is_file() and path.suffix == ".py":
        return [path]
    if path.is_dir():
        return sorted(path.rglob("*.py"))
    return []


def has_file_header_comment(source: str) -> bool:
    """Check if file has a header comment (first non-import lines have a docstring or comment)."""
    lines = source.split("\n")
    # Skip shebang, encoding declaration, empty lines
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if not line or line.startswith("#!") or line.startswith("# -*-") or line.startswith("# coding"):
            idx += 1
            continue
        break
    if idx >= len(lines):
        return False
    # Check if first meaningful line is a module docstring
    if lines[idx].strip().startswith('"""') or lines[idx].strip().startswith("'''"):
        return True
    # Check if first meaningful line is a comment
    if lines[idx].strip().startswith("#"):
        return True
    return False


def get_functions_without_docstring(tree: ast.AST, source: str) -> list[tuple[str, int, int]]:
    """Find functions/methods longer than 10 lines without docstring.
    Returns list of (name, lineno, end_lineno).
    """
    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip __init__ and very short functions
            if node.name.startswith("__") and node.name.endswith("__"):
                continue
            end_lineno = node.end_lineno or node.lineno
            length = end_lineno - node.lineno + 1
            if length < 10:
                continue
            # Check for docstring
            has_doc = False
            if node.body and isinstance(node.body[0], ast.Expr):
                if isinstance(node.body[0].value, (ast.Constant, ast.Str)):
                    has_doc = True
            if not has_doc:
                results.append((node.name, node.lineno, end_lineno))
    return results


def get_complex_functions_without_inline_comments(tree: ast.AST, source: str) -> list[tuple[str, int]]:
    """Find complex functions (loop nesting >2 or conditional branches >3) without inline comments.
    Returns list of (name, lineno).
    """
    results = []
    lines = source.split("\n")

    def count_nesting(node: ast.AST) -> int:
        """Count maximum loop/if nesting in a function body."""
        max_depth = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While, ast.If)):
                # Count depth by walking parents
                depth = 1
                parent = child
                while hasattr(parent, "parent"):
                    parent = parent.parent
                    if isinstance(parent, (ast.For, ast.While, ast.If)):
                        depth += 1
                max_depth = max(max_depth, depth)
        return max_depth

    # Set parent references
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("__") and node.name.endswith("__"):
                continue
            nesting = count_nesting(node)
            if nesting < 3:
                continue
            # Check for inline comments in function body
            start = node.lineno - 1
            end = (node.end_lineno or node.lineno)
            has_inline_comment = False
            for i in range(start, min(end, len(lines))):
                line = lines[i].strip()
                if "#" in line and not line.startswith("#"):
                    has_inline_comment = True
                    break
                if line.startswith("#") and i > start:
                    has_inline_comment = True
                    break
            if not has_inline_comment:
                results.append((node.name, node.lineno))
    return results


def scan_comment_redlines(source: str) -> list[tuple[int, str, str]]:
    """Scan comments for redline patterns.
    Returns list of (lineno, matched_pattern, line_content).
    """
    results = []
    lines = source.split("\n")
    for i, line in enumerate(lines, 1):
        # Extract comment part
        comment_start = line.find("#")
        if comment_start == -1:
            continue
        # Skip shebang and encoding
        stripped = line.strip()
        if stripped.startswith("#!") or stripped.startswith("# -*-") or stripped.startswith("# coding"):
            continue
        comment = line[comment_start:]
        for pattern in COMMENT_REDLINE_PATTERNS:
            if re.search(pattern, comment, re.IGNORECASE):
                results.append((i, pattern, stripped[:80]))
                break
    return results


def check_file(filepath: Path, strict: bool = False) -> dict:
    """Check a single Python file for comment quality."""
    result = {
        "file": str(filepath),
        "checks": {},
        "warnings": [],
        "passed": True,
    }
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        result["warnings"].append(f"无法读取文件: {exc}")
        result["passed"] = False
        return result

    # 1. File header comment
    has_header = has_file_header_comment(source)
    result["checks"]["file_header"] = "PASS" if has_header else "WARN"
    if not has_header:
        result["warnings"].append(f"{filepath.name}: 缺少文件头说明（文件开头应有1-3行注释或docstring说明这个文件做什么）")

    # 2. Parse AST for function checks
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        result["warnings"].append(f"{filepath.name}: 语法错误，无法解析: {exc}")
        result["checks"]["syntax"] = "FAIL"
        result["passed"] = False
        return result

    # 3. Functions without docstring
    no_doc_funcs = get_functions_without_docstring(tree, source)
    result["checks"]["function_docstring"] = "PASS" if not no_doc_funcs else "WARN"
    for name, lineno, end in no_doc_funcs:
        result["warnings"].append(f"{filepath.name}:{lineno} 函数 {name}（{end-lineno+1}行）缺少docstring，应说明功能、参数和返回值")

    # 4. Complex functions without inline comments
    complex_no_comments = get_complex_functions_without_inline_comments(tree, source)
    result["checks"]["complex_inline_comment"] = "PASS" if not complex_no_comments else "WARN"
    for name, lineno in complex_no_comments:
        result["warnings"].append(f"{filepath.name}:{lineno} 复杂函数 {name}（嵌套>3层）缺少行内注释，应说明关键逻辑为什么这么做")

    # 5. Comment redlines
    redlines = scan_comment_redlines(source)
    result["checks"]["comment_redline"] = "PASS" if not redlines else "WARN"
    for lineno, pattern, line in redlines:
        result["warnings"].append(f"{filepath.name}:{lineno} 注释包含红线内容（{pattern}）: {line} — 注释必须是纯粹技术说明，禁止元话语/负向回响/内部讨论/AI协作痕迹")

    # Determine overall status
    if result["warnings"]:
        result["passed"] = not strict
        result["status"] = "BLOCK" if strict else "WARN"
    else:
        result["status"] = "PASS"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="代码目录或Python文件")
    parser.add_argument("--strict", action="store_true", help="严格模式：有WARN则返回非零退出码")
    parser.add_argument("--out", default=None, help="输出JSON报告路径")
    args = parser.parse_args()

    path = Path(args.path).resolve()
    py_files = find_python_files(path)

    if not py_files:
        print(json.dumps({"error": "未找到Python文件", "path": str(path)}, ensure_ascii=False, indent=2))
        return 1

    file_results = []
    all_warnings = []
    for py_file in py_files:
        # Skip test files and __init__.py with minimal content
        if py_file.name.startswith("test_") or py_file.name == "__init__.py":
            content = py_file.read_text(encoding="utf-8", errors="replace")
            if len(content.strip()) < 50:
                continue
        result = check_file(py_file, args.strict)
        file_results.append(result)
        all_warnings.extend(result["warnings"])

    total_files = len(file_results)
    files_with_warnings = sum(1 for r in file_results if r["warnings"])
    total_warnings = len(all_warnings)

    report = {
        "schema_version": "1.0",
        "path": str(path),
        "strict": args.strict,
        "summary": {
            "total_files": total_files,
            "files_with_warnings": files_with_warnings,
            "total_warnings": total_warnings,
        },
        "files": file_results,
        "warnings": all_warnings,
        "status": "PASS" if total_warnings == 0 else ("BLOCK" if args.strict else "WARN"),
    }

    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and total_warnings > 0:
        return 1
    return 0


if __name__ == "__main__":
    import json
    raise SystemExit(main())
