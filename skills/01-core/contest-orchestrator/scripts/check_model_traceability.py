#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit model-to-code/data/figure and literature-method traceability.

The literature part deliberately stays conservative: a generated map is only
an input record.  Formal delivery requires the agent to resolve every
``pending_agent_decision`` to adopt/adapt/reject and to explain the resulting
model change in the modeling section.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - JSON projects remain supported
    yaml = None


def locate_tex(root: Path) -> Path:
    if root.is_file():
        return root
    candidates = sorted(root.glob("paper*.tex")) or sorted(root.glob("*.tex"))
    if not candidates:
        for folder in (root / "paper", root / "03_文档" / "paper", root / "03_文档"):
            candidates = sorted(folder.glob("paper*.tex")) if folder.is_dir() else []
            if candidates:
                break
    if not candidates:
        candidates = sorted(root.rglob("paper*.tex"))
    if not candidates:
        raise FileNotFoundError(f"未找到 TeX 文件: {root}")
    return candidates[0]


def expand_inputs(text: str, base: Path, seen: set[Path] | None = None) -> str:
    seen = set() if seen is None else seen
    pattern = re.compile(r"\\(?:input|include)\{([^{}]+)\}")
    def replace(match: re.Match[str]) -> str:
        path = base / match.group(1).strip()
        if not path.suffix:
            path = path.with_suffix(".tex")
        path = path.resolve()
        if path in seen or not path.is_file():
            return match.group(0)
        seen.add(path)
        return expand_inputs(path.read_text(encoding="utf-8", errors="replace"), path.parent, seen)
    return pattern.sub(replace, text)


def _first_file(root: Path, name: str) -> Path | None:
    direct = root / name
    if direct.is_file():
        return direct
    matches = sorted(root.rglob(name))
    return matches[0] if matches else None


def _load_mapping(path: Path) -> dict:
    if path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
    elif yaml is not None:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        raise RuntimeError("缺少 PyYAML，无法读取 YAML 文献方法迁移表")
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} 根节点必须是 mapping")
    return value


def _modeling_text(source: str) -> str:
    """Return a bounded modeling-section slice for citation/use checks."""
    start = re.search(r"\\(?:section|chapter)\*?\{[^}]*模型建立与求解[^}]*\}", source)
    if not start:
        return source
    tail = source[start.end():]
    end = re.search(r"\\(?:section|chapter)\*?\{", tail)
    return tail[:end.start()] if end else tail


def _required_chinese_count(competition: str | None) -> int:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(competition or "").strip().lower()).strip("_")
    aliases = {"guosai", "cumcm", "cumcmthesis", "cumcm_2026", "cumcm2026",
               "national_mathematical_modeling", "national_modeling"}
    return 2 if normalized in aliases else 0


def _literature_method_check(root: Path, source: str, strict: bool,
                             competition: str = "guosai") -> dict:
    """Validate profile-specific Chinese count and method decisions."""
    required_profile_count = _required_chinese_count(competition)
    report = {"status": "WARN", "passed": True, "issues": [], "warnings": [],
              "map": None, "path": None, "resolved_decisions": 0}
    pause_path = _first_file(root, "literature_pause.json")
    if pause_path is not None:
        try:
            pause_payload = _load_mapping(pause_path)
            if str(pause_payload.get("status", "")).upper() == "PAUSE":
                report["issues"].append("文献阶段仍处于 PAUSE：中文文献闸门尚未解锁")
        except Exception as exc:
            report["warnings"].append(f"literature_pause.json 解析失败: {exc}")
    map_path = _first_file(root, "method_transfer_map.json")
    if map_path is None:
        if required_profile_count == 0:
            report["status"] = "PASS"
            report["warnings"].append("当前竞赛 profile 未配置中文文献数量门禁；无 method_transfer_map 时不阻断")
            return report
        message = "缺少 method_transfer_map.json：无法证明中文文献方法已迁移到各子问题"
        (report["issues"] if strict else report["warnings"]).append(message)
        report["passed"] = not strict
        report["status"] = "BLOCK" if strict else "WARN"
        return report
    report["path"] = str(map_path)
    try:
        payload = _load_mapping(map_path)
    except Exception as exc:
        report["issues"].append(f"文献方法迁移表解析失败: {exc}")
        report["passed"] = False
        report["status"] = "BLOCK"
        return report
    report["map"] = payload
    # The competition profile is authoritative. A legacy map's default of 2
    # must not leak into MCM/ICM or other neutral profiles.
    required = required_profile_count
    verified = int(payload.get("verified_chinese_count", 0) or 0)
    references = payload.get("references", [])
    if not isinstance(references, list):
        report["issues"].append("文献方法迁移表 references 必须是列表")
        references = []
    if verified < required or len(references) < required:
        report["issues"].append(f"中文文献方法迁移表仅记录 {verified} 篇，最低要求为 {required} 篇")
    by_subproblem = payload.get("by_subproblem", {})
    modeling = _modeling_text(source)
    reference_by_id = {
        str(item.get("ref_ID")): item for item in references if isinstance(item, dict)
    }
    reference_keys = {}
    seen_keys = set()
    for item in references if isinstance(references, list) else []:
        if not isinstance(item, dict):
            continue
        ref_id = str(item.get("ref_ID", ""))
        key = str(item.get("citation_key", "")).strip()
        if not key:
            report["issues"].append(f"文献 {ref_id or '?'} 缺少 citation_key")
            continue
        if key in seen_keys:
            report["issues"].append(f"citation_key 重复: {key}")
        seen_keys.add(key)
        reference_keys[ref_id] = key
    if not isinstance(by_subproblem, dict) or not by_subproblem:
        report["issues"].append("文献方法迁移表缺少 by_subproblem，未按子问题登记方法去向")
    for qid, entries in (by_subproblem.items() if isinstance(by_subproblem, dict) else []):
        if not isinstance(entries, list) or not entries:
            report["issues"].append(f"{qid} 没有中文文献方法登记")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                report["issues"].append(f"{qid} 存在非 mapping 方法登记")
                continue
            decision = str(entry.get("decision", "")).lower()
            if decision not in {"adopt", "adapt", "reject"}:
                report["issues"].append(f"{qid} 文献 {entry.get('ref_ID', '?')} 尚未决定 adopt/adapt/reject")
                continue
            report["resolved_decisions"] += 1
            if decision in {"adopt", "adapt"} and not str(entry.get("method", "")).strip():
                report["issues"].append(f"{qid} 的 {decision} 登记缺少 method")
            if decision == "adapt" and not str(entry.get("innovation_delta", "")).strip():
                report["issues"].append(f"{qid} 的 adapt 登记缺少 innovation_delta")
            if decision == "reject" and not str(entry.get("reason", "")).strip():
                report["issues"].append(f"{qid} 的 reject 登记缺少 reason")
            if decision in {"adopt", "adapt"}:
                method = str(entry.get("method", "")).strip()
                # Require at least one meaningful method token to occur in the
                # modeling section; a generic word like “方法” is not enough.
                terms = [term for term in re.split(r"[，,、；;|/\s]+", method)
                         if len(term) >= 2]
                if terms and not any(term.lower() in modeling.lower() for term in terms):
                    report["issues"].append(f"{qid} 的 {decision} 方法未在模型建立与求解正文出现: {method}")
                ref = reference_by_id.get(str(entry.get("ref_ID")), {})
                citation_key = str(entry.get("citation_key") or ref.get("citation_key") or "").strip()
                if not citation_key:
                    report["issues"].append(f"{qid} 的 {decision} 文献缺少 citation_key，无法绑定正文引用")
                else:
                    expected_key = reference_keys.get(str(entry.get("ref_ID")))
                    if expected_key and citation_key != expected_key:
                        report["issues"].append(
                            f"{qid} 的文献 {entry.get('ref_ID')} citation_key={citation_key} "
                            f"与 references.yaml 中的 {expected_key} 不一致"
                        )
                    elif not expected_key:
                        report["issues"].append(
                            f"{qid} 的文献 {entry.get('ref_ID')} 不存在可绑定的 references citation_key"
                        )
                    cite_key_hit = bool(re.search(
                        r"\\(?:cite|citep|citet|parencite|supercite)\s*"
                        r"(?:\[[^]]*\])?\s*\{[^}]*\b" + re.escape(citation_key) + r"\b[^}]*\}",
                        modeling
                    ))
                    numeric_hit = bool(re.search(r"\[\s*" + re.escape(str(entry.get("ref_ID"))) + r"\s*\]", modeling))
                    if not (cite_key_hit or numeric_hit):
                        report["issues"].append(
                            f"{qid} 的 {decision} 文献未在模型正文引用 citation_key={citation_key} 或 ref_ID={entry.get('ref_ID')}"
                        )

    if report["resolved_decisions"]:
        if not re.search(r"\\(?:cite|citep|citet|parencite|supercite)\s*\{[^}]+\}|\[[0-9]{1,3}\]", modeling):
            report["issues"].append("模型建立与求解章节没有发现与文献方法对应的正文引用")
        if not re.search(r"文献|参考|依据|先例", modeling):
            report["issues"].append("模型建立与求解章节没有说明文献方法承担的作用")
        if not re.search(r"采用|借鉴|改进|适配|扩展|创新|舍弃|不采用", modeling):
            report["issues"].append("模型建立与求解章节没有记录文献方法的采用、改造或舍弃")
    else:
        report["warnings"].append("尚无已解析的文献方法决策，无法验证建模章节映射")
    if report["issues"] and not strict:
        report["warnings"].extend(report["issues"])
        report["issues"] = []
    report["passed"] = not report["issues"]
    report["status"] = "BLOCK" if report["issues"] else ("WARN" if report["warnings"] else "PASS")
    return report


def check(root: Path, strict: bool = False, competition: str = "guosai") -> dict:
    tex = locate_tex(root)
    source = expand_inputs(tex.read_text(encoding="utf-8", errors="replace"), tex.parent)
    issues: list[str] = []
    warnings: list[str] = []
    sources: list[str] = [str(tex)]
    listings = re.findall(r"\\lstinputlisting(?:\[[^]]*\])?\{([^{}]+)\}", source)
    for raw in listings:
        candidate = (tex.parent / raw).resolve()
        sources.append(str(candidate))
        if not candidate.is_file():
            issues.append(f"附录代码源文件不存在: {raw}")
            continue
        code = candidate.read_text(encoding="utf-8", errors="replace")
        missing = [label for label in ("功能", "输入", "输出") if label not in code]
        if missing:
            warnings.append(f"代码 {raw} 缺少可复现头部字段: {', '.join(missing)}")
    required_artifacts = {
        "assumptions": ["model_assumptions.md", "symbol_table.md"],
        "results": ["results", "sensitivity_results.json"],
        "figures": ["figure_registry.json"],
    }
    evidence: dict[str, list[str]] = {}
    for key, candidates in required_artifacts.items():
        found = []
        for raw in candidates:
            matches = list(root.rglob(raw))
            if matches:
                found.extend(str(item) for item in matches[:3])
        evidence[key] = found
        if not found:
            warnings.append(f"未发现可选追溯证据: {key}")
    # Formula references and listings are structural signals, not proof of numerical validity.
    if re.search(r"\\(?:ref|eqref)\{", source) and not re.search(r"\\label\{", source):
        warnings.append("正文存在公式/图表引用，但未发现对应 label")
    if strict and warnings:
        issues.extend(warnings)
        warnings = []
    literature_method = _literature_method_check(root, source, strict, competition)
    if literature_method["issues"]:
        issues.extend(literature_method["issues"])
    if literature_method["warnings"]:
        warnings.extend(literature_method["warnings"])
    return {"schema_version": "1.1", "passed": not issues,
            "gate_status": "BLOCK" if issues else ("WARN" if warnings else "PASS"),
            "issues": issues, "warnings": warnings, "sources": sources, "evidence": evidence,
            "listings": listings, "tex": str(tex), "literature_method": literature_method}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--competition", default="guosai",
                        help="竞赛 profile；仅 guosai/cumcm 强制中文文献方法迁移")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    try:
        report = check(Path(args.project_root).resolve(), args.strict, args.competition)
    except Exception as exc:
        report = {"schema_version": "1.0", "passed": False, "gate_status": "BLOCK",
                  "issues": [str(exc)], "warnings": [], "sources": [], "evidence": {}}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = Path(args.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
