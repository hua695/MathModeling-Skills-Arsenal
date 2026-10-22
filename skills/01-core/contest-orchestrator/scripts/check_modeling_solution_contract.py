#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate prerequisites and evidence for a modeling-and-solving chapter.

The checker does not write prose or invent results.  A project opts in by
providing ``modeling_solution_contract.yaml``.  In strict mode the contract
must identify the problem inputs, assumptions, symbols, debugged code, a
per-question derivation chain, algorithm rationale/parameters, and external
result files.  The TeX is then cross-checked through explicit anchors.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - diagnosed in the report
    yaml = None

from check_modeling_contract import expand_inputs, locate_tex

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

QUESTION_RE = re.compile(r"Q\d+", re.I)
RESULT_NUMBER_RE = re.compile(r"(?:结果|得到|最优|准确率|误差|精度|成本|厚度)\s*(?:为|是|达到|=|：|:)\s*[-+]?\d")
CODE_ENV_RE = re.compile(r"\\begin\{(?:lstlisting|verbatim|minted)\}.*?\\end\{(?:lstlisting|verbatim|minted)\}", re.S | re.I)
ALLOWED_DEBUG = {"pass", "passed", "verified", "debugged", "complete"}


def _discover(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return (candidate if candidate.is_absolute() else root / candidate).resolve()
    candidates = (root / "modeling_solution_contract.yaml",
                  root / "01_需求与规划" / "modeling_solution_contract.yaml",
                  root / "03_文档" / "modeling_solution_contract.yaml",
                  root / "paper" / "modeling_solution_contract.yaml")
    return next((path.resolve() for path in candidates if path.exists()), None)


def _load(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取 modeling_solution_contract.yaml")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("modeling_solution_contract.yaml 根节点必须是 mapping")
    return value


def _safe_path(root: Path, raw: object) -> Path:
    candidate = Path(str(raw))
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"输入路径越出项目根目录: {raw}")
    return resolved


def _source(root: Path) -> tuple[Path, str]:
    tex_root = root if list(root.glob("*.tex")) else next(
        (candidate for candidate in (root / "03_文档" / "paper", root / "paper") if candidate.is_dir()), root)
    tex = locate_tex(tex_root)
    return tex, expand_inputs(tex.read_text(encoding="utf-8", errors="replace"), tex.parent)


def _spans(text: str, ids: list[str]) -> dict[str, str]:
    markers = list(re.finditer(r"\\label\{subproblem:(Q\d+)\}", text, re.I))
    if markers:
        result = {}
        for index, marker in enumerate(markers):
            qid = marker.group(1).upper()
            if qid not in ids:
                continue
            heading = text.rfind("\\subsection", 0, marker.start())
            candidates = [markers[index + 1].start() if index + 1 < len(markers) else len(text)]
            # A final labeled subproblem must end at the next top-level
            # section, not at EOF.  Otherwise validation/appendix material
            # (including legitimate minted code) is incorrectly attributed
            # to the last modeling subsection.
            next_section = re.search(r"\\section\*?\{", text[marker.end():])
            if next_section:
                candidates.append(marker.end() + next_section.start())
            end = min(candidates)
            result[qid] = text[heading if heading >= 0 else marker.start():end]
        if result:
            return result
        # Once explicit subproblem labels exist, never reuse the whole paper
        # as evidence for a missing question.  That made Q1 text accidentally
        # satisfy Q2 in mixed-question papers.
        return result
    # A single unlabeled section is retained for backward compatibility.  A
    # multi-question contract must provide explicit scope labels.
    return {ids[0]: text} if len(ids) == 1 else {}


def _anchor(chunk: str, value: object) -> bool:
    expected = str(value or "").strip()
    if not expected:
        return False
    if expected in chunk:
        return True
    # Formatting a numeric range as ``\textendash{}`` is semantically
    # equivalent to the source-contract spelling ``--``.  Normalize only
    # dashes so typography cleanups cannot invalidate a genuine evidence
    # anchor; all other anchor text still has to match literally.
    def normalize_dash(text: str) -> str:
        return (text.replace(r"\textendash{}", "--")
                    .replace(r"\textendash", "--")
                    .replace("–", "--")
                    .replace("—", "--"))
    return normalize_dash(expected) in normalize_dash(chunk)


def _issue(report: dict, message: str, *, strict: bool) -> None:
    (report["issues"] if strict else report["warnings"]).append(message)


def validate(root: Path, contract_path: Path | None, strict: bool = False) -> dict:
    root = root.resolve()
    report = {"schema_version": "1.0", "strict": strict, "passed": True,
              "gate_status": "PASS", "issues": [], "warnings": [],
              "input_gate": {}, "subproblems": [], "self_check": []}
    if contract_path is None or not contract_path.exists():
        _issue(report, "缺少 modeling_solution_contract.yaml：建模求解章节不得凭题目直接生成", strict=strict)
        report["passed"] = not report["issues"]
        report["gate_status"] = "BLOCK" if report["issues"] else "WARN"
        return report
    try:
        payload = _load(contract_path)
        tex, text = _source(root)
    except Exception as exc:
        report["issues"].append(str(exc))
        report["passed"] = False
        report["gate_status"] = "BLOCK"
        return report
    strong_derivation = str(payload.get("schema_version", "1.0")) >= "1.1"

    gate = payload.get("input_gate") if isinstance(payload.get("input_gate"), dict) else {}
    required_gate = ("problem_subquestions", "assumptions_source", "variable_list_source",
                     "code_logic_sources", "code_debug_status", "result_authority")
    gate_missing = [key for key in required_gate if not gate.get(key)]
    for key in gate_missing:
        _issue(report, f"前置输入契约缺少 {key}：不得直接生成建模求解内容", strict=strict)
    qids = [str(value).upper() for value in gate.get("problem_subquestions", [])] if isinstance(gate.get("problem_subquestions"), list) else []
    if not qids or any(not QUESTION_RE.fullmatch(qid) for qid in qids):
        _issue(report, "problem_subquestions 必须是非空的 Q1/Q2/... 列表", strict=strict)
    source_items = [gate.get("assumptions_source"), gate.get("variable_list_source")]
    code_sources = gate.get("code_logic_sources") if isinstance(gate.get("code_logic_sources"), list) else []
    source_items.extend(code_sources)
    source_status = []
    for raw in source_items:
        try:
            path = _safe_path(root, raw)
            ok = path.is_file()
            source_status.append({"path": str(path), "exists": ok})
            if not ok:
                _issue(report, f"前置输入文件不存在: {raw}", strict=strict)
        except Exception as exc:
            source_status.append({"path": str(raw), "exists": False})
            _issue(report, str(exc), strict=strict)
    debug_status = str(gate.get("code_debug_status", "")).lower()
    if debug_status not in ALLOWED_DEBUG:
        _issue(report, "code_debug_status 未确认已调试完成；请先传入可运行代码逻辑", strict=strict)
    if str(gate.get("result_authority", "")).lower() not in {"user_provided", "code_generated", "user_or_code_verified"}:
        _issue(report, "result_authority 必须明确为 user_provided、code_generated 或 user_or_code_verified", strict=strict)
    if gate.get("allow_fabricated_numbers", False) is True:
        _issue(report, "禁止允许 AI 编造求解数值：allow_fabricated_numbers 必须为 false", strict=strict)
    report["input_gate"] = {"problem_subquestions": qids, "sources": source_status,
                             "code_debug_status": debug_status,
                             "result_authority": gate.get("result_authority"),
                             "allow_fabricated_numbers": gate.get("allow_fabricated_numbers", False)}

    items = payload.get("subproblems") if isinstance(payload.get("subproblems"), list) else []
    ids = [str(item.get("id", "")).upper() for item in items if isinstance(item, dict)]
    if set(ids) != set(qids) or len(ids) != len(set(ids)):
        _issue(report, "契约中的 subproblems 与 input_gate.problem_subquestions 不一致", strict=strict)
    spans = _spans(text, ids or qids)
    for item in items:
        if not isinstance(item, dict):
            _issue(report, "subproblems 中存在非 mapping 项", strict=strict)
            continue
        qid = str(item.get("id", "")).upper()
        chunk = spans.get(qid, "")
        row = {"id": qid, "passed": True, "issues": [], "checks": {}}
        def local(message: str) -> None:
            row["issues"].append(message)
            row["passed"] = False

        row["checks"]["question_anchor"] = bool(chunk) and _anchor(chunk, item.get("text_anchor"))
        if not row["checks"]["question_anchor"]:
            local(f"{qid} 缺少对应正文小问锚点")
        symbols = item.get("symbols") if isinstance(item.get("symbols"), list) else []
        symbol_names = set()
        for symbol in symbols:
            if not isinstance(symbol, dict) or not all(symbol.get(key) for key in ("symbol", "meaning", "unit", "variable_type")):
                local(f"{qid} 符号表条目必须包含 symbol/meaning/unit/variable_type")
            elif str(symbol["symbol"]) in symbol_names:
                local(f"{qid} 符号重复: {symbol['symbol']}")
            else:
                symbol_names.add(str(symbol["symbol"]))
        row["checks"]["symbol_table"] = bool(symbols) and not row["issues"]
        table_anchor = item.get("symbol_table_anchor")
        if not _anchor(chunk, table_anchor):
            local(f"{qid} 缺少符号说明表正文锚点")
        if not all(command in text for command in ("\\toprule", "\\midrule", "\\bottomrule")):
            local(f"{qid} 符号说明表不是可识别的三线表（缺少 top/mid/bottomrule）")
        row["checks"]["symbol_table"] = bool(symbols) and _anchor(chunk, table_anchor) and not any("符号说明表" in issue or "符号表" in issue for issue in row["issues"])
        chain = item.get("formula_chain") if isinstance(item.get("formula_chain"), list) else []
        kinds = {str(entry.get("kind", "")).lower() for entry in chain if isinstance(entry, dict)}
        if len(chain) < 3 or "original" not in kinds or "final" not in kinds or not ({"rearranged", "intermediate"} & kinds):
            local(f"{qid} formula_chain 必须包含 original→rearranged/intermediate→final 完整推导链")
        formula_ids = set()
        labels_in_text = [match.group(1) for match in re.finditer(r"\\label\{([^}]+)\}", chunk)]
        previous_label_index = -1
        for entry in chain:
            if not isinstance(entry, dict):
                local(f"{qid} 公式链条存在非 mapping 项")
                continue
            fid = str(entry.get("id", ""))
            if not fid or fid in formula_ids:
                local(f"{qid} 公式 id 缺失或重复: {fid}")
            formula_ids.add(fid)
            for key in ("source_anchor", "meaning_anchor"):
                if not _anchor(chunk, entry.get(key)):
                    local(f"{qid} 公式 {fid} 缺少正文锚点: {key}；需要文字解释而非孤立公式")
            label = str(entry.get("label", ""))
            if label and label not in labels_in_text:
                local(f"{qid} 公式标签不存在于正文: {label}")
            if label in labels_in_text:
                index = labels_in_text.index(label)
                if index < previous_label_index:
                    local(f"{qid} 公式编号/标签顺序不递增: {label}")
                previous_label_index = index
            entry_symbols = entry.get("symbols") if isinstance(entry.get("symbols"), list) else []
            if any(str(value) not in symbol_names for value in entry_symbols):
                local(f"{qid} 公式 {fid} 使用了符号表外变量（缺少符号表定义）")
            if str(entry.get("kind", "")).lower() == "final" and not entry.get("derived_from"):
                local(f"{qid} 最终公式 {fid} 未登记 derived_from，存在空降最终公式风险")
            if strong_derivation and str(entry.get("kind", "")).lower() != "original":
                parents = entry.get("derived_from") if isinstance(entry.get("derived_from"), list) else []
                prior_ids = formula_ids - {fid}
                if not parents or any(str(parent) not in prior_ids for parent in parents):
                    local(f"{qid} 公式 {fid} 的 derived_from 必须引用前序公式")
                derivation_anchor = entry.get("derivation_anchor")
                if not _anchor(chunk, derivation_anchor):
                    local(f"{qid} 公式 {fid} 缺少实质整理/推导步骤锚点；不能只写‘由式得到’")
        equations = re.findall(r"\\begin\{equation\}(.*?)\\end\{equation\}", chunk, re.S | re.I)
        reserved = {"sin", "cos", "tan", "exp", "log", "ln", "max", "min", "arg", "argmin", "argmax", "mathrm", "text", "frac", "left", "right"}
        formula_tokens = set()
        for equation in equations:
            equation = re.sub(r"\\label\{[^}]*\}", " ", equation)
            equation = re.sub(r"\\(?:operatorname|mathrm|mathbf|mathbb|text)\{[^}]*\}", " ", equation)
            cleaned = re.sub(r"\\[A-Za-z]+", " ", equation)
            formula_tokens.update(re.findall(r"(?<![A-Za-z])([A-Za-z](?:_[A-Za-z0-9]+)?)", cleaned))
        unknown_symbols = sorted(token for token in formula_tokens if token not in symbol_names and token not in reserved)
        # TeX token extraction is intentionally lightweight and cannot safely
        # distinguish every command subscript from a mathematical variable.
        # Keep potential omissions visible for review, but do not turn this
        # heuristic into a false strict-mode rejection.
        if unknown_symbols:
            row["symbol_diagnostics"] = unknown_symbols
        row["checks"]["derivation_chain"] = bool(chain) and not any("公式" in issue or "formula_chain" in issue for issue in row["issues"])
        row["checks"]["formula_meaning"] = all(_anchor(chunk, entry.get("meaning_anchor")) for entry in chain if isinstance(entry, dict))
        algorithm = item.get("algorithm") if isinstance(item.get("algorithm"), dict) else {}
        for key in ("name", "rationale_anchor", "software", "steps_anchor", "parameters"):
            if not algorithm.get(key):
                local(f"{qid} algorithm 缺少 {key}；不能只写算法名称")
        for parameter in algorithm.get("parameters", []) if isinstance(algorithm.get("parameters"), list) else []:
            if not isinstance(parameter, dict) or not parameter.get("name") or not (parameter.get("value") or parameter.get("value_placeholder")):
                local(f"{qid} 算法参数必须列出名称与取值/占位值")
            elif not parameter.get("basis"):
                local(f"{qid} 参数 {parameter.get('name')} 缺少取值依据，请补充题目、文献或调试依据")
        for key in ("rationale_anchor", "steps_anchor"):
            if algorithm.get(key) and not _anchor(chunk, algorithm[key]):
                local(f"{qid} 算法 {key} 未在正文出现")
        row["checks"]["algorithm"] = bool(algorithm) and not any("algorithm" in issue or "算法" in issue for issue in row["issues"])
        row["checks"]["algorithm_parameters"] = bool(algorithm.get("parameters")) and not any("参数" in issue for issue in row["issues"])
        result_files = item.get("result_source_files") if isinstance(item.get("result_source_files"), list) else []
        for raw in result_files:
            try:
                if not _safe_path(root, raw).is_file():
                    local(f"{qid} 结果来源文件不存在: {raw}")
            except Exception as exc:
                local(str(exc))
        if not result_files:
            local(f"{qid} 缺少 result_source_files；真实数值必须来自用户/代码结果")
        if str(item.get("numeric_results_policy", "external_only")) != "external_only":
            local(f"{qid} numeric_results_policy 必须为 external_only，禁止 AI 编造数值")
        # Competition papers should present each subproblem's computed result
        # next to its model and algorithm.  A number is only unsafe when the
        # subproblem has no declared external result artifact to trace it to.
        # Earlier logic rejected every such number, contradicting the writing
        # contract and encouraging a misleading separation of model and result.
        if RESULT_NUMBER_RE.search(chunk) and not result_files:
            local(f"{qid} 建模求解正文出现直接写入数值结果但未绑定外部结果文件")
        if len(CODE_ENV_RE.findall(chunk)) > 0 and sum(len(value) for value in CODE_ENV_RE.findall(chunk)) > 1200:
            local(f"{qid} 正文包含大段源代码，应移至附录并保留复现指引")
        row["checks"]["results_external"] = bool(result_files) and item.get("numeric_results_policy", "external_only") == "external_only"
        row["checks"]["assumption_link"] = bool(item.get("assumption_anchor")) and _anchor(chunk, item.get("assumption_anchor"))
        if not row["checks"]["assumption_link"]:
            local(f"{qid} 未登记并核验模型假设如何作用于公式/约束")
        report["subproblems"].append(row)

    checks = [
        ("小问拆分", bool(qids) and set(ids) == set(qids)),
        ("符号表与公式一致", all(row["checks"].get("symbol_table") for row in report["subproblems"])),
        ("公式推导链", all(row["checks"].get("derivation_chain") for row in report["subproblems"])),
        ("公式物理含义说明", all(row["checks"].get("formula_meaning") for row in report["subproblems"])),
        ("算法选择理由", all(row["checks"].get("algorithm") for row in report["subproblems"])),
        ("算法参数及依据", all(row["checks"].get("algorithm_parameters") for row in report["subproblems"])),
        ("正文无大段源代码", all(not any("大段源代码" in issue for issue in row["issues"]) for row in report["subproblems"])),
        ("假设进入建模", all(row["checks"].get("assumption_link") for row in report["subproblems"])),
    ]
    report["self_check"] = [{"item": name, "status": "PASS" if passed else "FAIL"} for name, passed in checks]
    for row in report["subproblems"]:
        for issue in row["issues"]:
            _issue(report, issue, strict=strict)
    report["tex"] = str(tex)
    report["contract"] = str(contract_path)
    report["passed"] = not report["issues"]
    report["gate_status"] = "BLOCK" if report["issues"] else ("WARN" if report["warnings"] else "PASS")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--contract", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    try:
        report = validate(root, _discover(root, args.contract), args.strict)
    except Exception as exc:
        report = {"schema_version": "1.0", "strict": args.strict, "passed": False,
                  "gate_status": "BLOCK", "issues": [str(exc)], "warnings": [], "self_check": []}
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out = Path(args.out).resolve() if args.out else root / "modeling_solution_contract_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
