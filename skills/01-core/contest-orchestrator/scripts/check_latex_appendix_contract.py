#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict LaTeX-only appendix, source-material and minted contract checker.

The checker deliberately validates evidence in the TeX project and a small
``appendix_plan.yaml``/``appendix_contract.yaml`` manifest.  It does not invent source files,
derivations, tables or code.  Non-strict mode is useful while drafting;
strict mode is the formal-delivery gate.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


NO_PROGRAM = "本论文没有用到程序"
NO_SUPPORT = "本论文没有支撑材料"
APPENDIX_RE = re.compile(r"\\appendix\b", re.I)
HEADING_RE = re.compile(
    r"\\(?:section|chapter)\s*\{\s*(?:附录\s*)?([A-C])\s*[^}]*\}", re.I
)
LABEL_RE = re.compile(r"\\label\{\s*(fig|tab):([A-Z])-([0-9]+)\s*\}", re.I)
ANY_LABEL_RE = re.compile(r"\\label\{\s*([^}]+)\s*\}")
APP_REF_RE = re.compile(r"(?:详见|参见|见|见下|附)录\s*([A-Z])|appendix\s*([A-Z])", re.I)
FORBIDDEN_APPENDIX_RE = re.compile(
    r"摘要|问题重述|问题分析|参考文献|赛题全文|题目全文|调试报错|traceback|报错日志|姓名|学校|学号|指导教师|队伍信息",
    re.I,
)
FORBIDDEN_ENV_RE = re.compile(r"\\(?:begin|end)\s*\{(?:lstlisting|verbatim|Verbatim)\}|\\lstinputlisting", re.I)
MINTED_ENV_RE = re.compile(r"\\begin\s*\{minted\}\s*(?:\[([^]]*)\])?\s*\{[^}]+\}(.*?)\\end\s*\{minted\}", re.I | re.S)
MINTED_INPUT_RE = re.compile(r"\\inputminted\s*(?:\[([^]]*)\])?\s*\{[^}]+\}\s*\{([^}]+)\}", re.I)
CODE_APPENDIX_MODES = {"not_applicable", "core_only", "full_source"}


def locate_tex(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = sorted(path.glob("paper*.tex")) or sorted(path.glob("*.tex"))
    if not candidates:
        raise FileNotFoundError(f"未找到 TeX 文件: {path}")
    return candidates[0]


def expand_inputs(text: str, base: Path, seen: set[Path] | None = None) -> str:
    """Inline local TeX inputs for structural appendix checks only.

    Contest papers commonly keep appendix and bibliography in separate input
    files.  Checking only the root TeX falsely reports missing appendices.
    """
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
        return expand_inputs(candidate.read_text(encoding="utf-8", errors="replace"), candidate.parent, seen)

    return pattern.sub(replace, text)


def locate_contract(paper_dir: Path, explicit: str | None, project_root: Path | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return (paper_dir / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    search_roots = [paper_dir]
    if project_root is not None:
        root = project_root.resolve()
        search_roots = [root, root / "01_需求与规划", paper_dir]
    elif paper_dir.name == "paper":
        search_roots.append(paper_dir.parent / "01_需求与规划")
    for search_root in search_roots:
        for name in ("appendix_contract.yaml", "appendix_contract.yml", "appendix_contract.json"):
            candidate = search_root / name
            if candidate.exists():
                return candidate.resolve()
    return None


def locate_plan(paper_dir: Path, explicit: str | None, project_root: Path | None = None) -> Path | None:
    """Find the capability-driven project plan before the legacy contract."""
    if explicit:
        candidate = Path(explicit)
        return (paper_dir / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    search_roots = [paper_dir]
    if project_root is not None:
        root = project_root.resolve()
        search_roots = [root, root / "01_需求与规划", paper_dir]
    elif paper_dir.name == "paper":
        search_roots.append(paper_dir.parent / "01_需求与规划")
    for search_root in search_roots:
        for name in ("appendix_plan.yaml", "appendix_plan.yml", "appendix_plan.json"):
            candidate = search_root / name
            if candidate.exists():
                return candidate.resolve()
    return None


def load_contract(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        value = json.loads(raw)
    else:
        try:
            import yaml
            value = yaml.safe_load(raw)
        except ImportError:
            value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("附录契约必须是对象")
    return value


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _source_config(contract: dict[str, Any]) -> dict[str, Any]:
    value = contract.get("source_inputs")
    return value if isinstance(value, dict) else contract


def _source_lists(contract: dict[str, Any]) -> tuple[list[str], list[str], list[str], list[str]]:
    source = _source_config(contract)
    values = [
        _as_list(source.get("full_source_files")),
        _as_list(source.get("long_derivation_files")),
        _as_list(source.get("raw_data_files")),
        _as_list(source.get("support_material_files")),
    ]
    # A plan may bind evidence directly to a module instead of repeating the
    # same paths under source_inputs.  Merge those real paths for existence and
    # provenance checks; never create a path on the agent's behalf.
    for module in contract.get("appendix_modules", contract.get("modules", [])) or []:
        if not isinstance(module, dict):
            continue
        kind = str(module.get("kind", "")).lower()
        target = 1 if kind in {"derivation", "long_derivation"} else 2 if kind in {"raw_data", "data"} else 0 if kind in {"source_code", "code"} else None
        if target is not None:
            for raw in _as_list(module.get("source_files")):
                if raw not in values[target]:
                    values[target].append(raw)
        for raw in _as_list(module.get("support_materials")):
            if raw not in values[3]:
                values[3].append(raw)
    return tuple(values)  # type: ignore[return-value]


def _core_source_files(contract: dict[str, Any]) -> list[str]:
    """Return source files deliberately shown in the paper appendix.

    New plans declare ``core_source_files`` explicitly.  A source-code module
    with ``include_in_pdf`` enabled is also a core-code declaration.  Legacy
    contracts remain compatible without pretending that their full-source
    inventory is a paper code binding.
    """
    source = _source_config(contract)
    files = _as_list(source.get("core_source_files"))
    for module in contract.get("appendix_modules", contract.get("modules", [])) or []:
        if not isinstance(module, dict):
            continue
        kind = str(module.get("kind", "")).lower()
        if kind in {"source_code", "code"} and module.get("include_in_pdf", True) is not False:
            for raw in _as_list(module.get("source_files")):
                if raw not in files:
                    files.append(raw)
    return files


def _support_source_files(contract: dict[str, Any], full_sources: list[str],
                          support_files: list[str]) -> list[str]:
    """Return complete source files declared as present in support materials."""
    source = _source_config(contract)
    declared = _as_list(source.get("support_source_files"))
    if declared:
        return declared
    support_set = set(support_files)
    return [raw for raw in full_sources if raw in support_set]


def _path_variants(raw: str) -> set[str]:
    value = str(raw).strip().replace("\\_", "_")
    path = Path(value)
    return {item.lower() for item in {value, value.replace("/", "\\"), path.name}}


def _path_in_text(text: str, raw: str) -> bool:
    normalized = text.replace("\\_", "_").lower()
    return any(variant in normalized for variant in _path_variants(raw))


def _path_key(raw: str) -> str:
    return str(raw).replace("\\", "/").strip().lower()


def _code_regions(tail: str) -> list[str]:
    """Collect section-local regions around minted blocks for file binding.

    The previous support-material list must not satisfy a core-code binding;
    regions start at the current appendix section instead of scanning the
    entire appendix tail.
    """
    matches = list(MINTED_ENV_RE.finditer(tail)) + list(MINTED_INPUT_RE.finditer(tail))
    regions: list[str] = []
    for match in matches:
        start = match.start()
        section_positions = [position for position in (
            tail.rfind("\\section", 0, start),
            tail.rfind("\\chapter", 0, start),
        ) if position >= 0]
        region_start = max(section_positions) if section_positions else max(0, start - 400)
        next_positions = [position for position in (
            tail.find("\\section", match.end()),
            tail.find("\\chapter", match.end()),
        ) if position >= 0]
        region_end = min(next_positions) if next_positions else min(len(tail), match.end() + 600)
        regions.append(tail[region_start:region_end])
    return regions


def _manifest_requirements(manifest: dict[str, Any]) -> dict[str, Any]:
    """Resolve conditional appendix obligations from a project plan.

    The final plan may explicitly set ``source_inputs.program_used``.  When it
    does not, a required source-code module or a code capability is sufficient
    evidence that the code branch is active.  No model family alone implies a
    code requirement.
    """
    source = _source_config(manifest)
    modules = manifest.get("appendix_modules", manifest.get("modules", [])) or []
    kinds = {str(item.get("kind", "")).lower() for item in modules if isinstance(item, dict) and item.get("required", False)}
    capabilities = {str(cap).lower() for item in manifest.get("subproblems", []) or []
                    if isinstance(item, dict) for cap in _as_list(item.get("capabilities"))}
    code_caps = {"code", "numerical_fitting", "numerical_simulation", "machine_learning", "optimization_solver"}
    explicit_program = source.get("program_used") if isinstance(source.get("program_used"), bool) else None
    program_used = explicit_program if explicit_program is not None else bool(kinds & {"code", "source_code"} or capabilities & code_caps)
    need_derivation = bool(kinds & {"derivation", "long_derivation"} or "derivation" in capabilities or _as_list(source.get("long_derivation_files")))
    need_raw_data = bool(kinds & {"raw_data", "data"} or "raw_data" in capabilities or _as_list(source.get("raw_data_files")))
    need_support = bool(program_used or _as_list(source.get("support_material_files")))
    mode = str(source.get("appendix_code_mode", "")).strip().lower()
    if not mode:
        mode = "core_only" if program_used else "not_applicable"
    return {"program_used": program_used, "need_derivation": need_derivation,
            "need_raw_data": need_raw_data, "need_support": need_support,
            "explicit_program": explicit_program, "module_kinds": sorted(kinds),
            "appendix_code_mode": mode,
            "explicit_code_mode": "appendix_code_mode" in source}


def _safe_source(root: Path, raw: str) -> tuple[Path | None, str | None]:
    candidate = Path(raw)
    if candidate.is_absolute():
        return None, f"支撑材料路径不得使用绝对路径: {raw}"
    resolved = (root / candidate).resolve()
    if root != resolved and root not in resolved.parents:
        return None, f"支撑材料路径越出项目根目录: {raw}"
    return resolved, None


def _references_position(text: str) -> int | None:
    markers: list[int] = []
    for pattern in (
        r"\\begin\s*\{thebibliography\}",
        r"\\bibliography\s*\{",
        r"\\section\s*\{\s*(?:参考文献|References)",
    ):
        markers.extend(match.start() for match in re.finditer(pattern, text, re.I))
    return min(markers) if markers else None


def _heading_ids(tail: str) -> list[str]:
    explicit = [match.group(1).upper() for match in HEADING_RE.finditer(tail)]
    if explicit:
        return explicit
    # The lightweight CUMCM class renders \thesection as “附录A”, while the
    # source naturally contains \section{标题}.  Treat the first appendix
    # sections as A/B/C rather than requiring duplicated visible titles.
    generic = list(re.finditer(r"\\section\s*\{[^}]+\}", tail, re.I))
    return [chr(ord("A") + index) for index, _ in enumerate(generic)]


def _option_tokens(options: str) -> set[str]:
    return {part.strip().lower().replace(" ", "") for part in options.split(",") if part.strip()}


def _check_minted(tail: str, full_text: str, issues: list[str], warnings: list[str]) -> dict[str, Any]:
    forbidden = FORBIDDEN_ENV_RE.findall(tail)
    if forbidden:
        issues.append("附录代码禁止使用 verbatim/lstlisting，必须统一使用 minted")
    blocks = list(MINTED_ENV_RE.finditer(tail))
    inputs = list(MINTED_INPUT_RE.finditer(tail))
    code_count = len(blocks) + len(inputs)
    if not code_count:
        return {"count": 0, "style": {}}
    required = {"bgcolor=codebg", "linenos", "breaklines", "tabsize=4", "fontsize=\\small", "framesep=6pt"}
    missing_by_block: list[dict[str, Any]] = []
    for index, match in enumerate(blocks, 1):
        options = _option_tokens(match.group(1) or "")
        missing = sorted(required - options)
        lines = len(match.group(2).splitlines())
        chars = len(match.group(2))
        if missing:
            issues.append(f"minted 第{index}个代码块缺少参数: {', '.join(missing)}")
        if "footnotesize" in options or "normalsize" in options:
            issues.append(f"minted 第{index}个代码块字号违规，必须固定为 \\small")
        if lines > 120 or chars > 12000:
            issues.append(f"minted 第{index}个代码块疑似粘贴整套源码，请移至支撑材料压缩包")
        missing_by_block.append({"index": index, "missing_options": missing, "lines": lines, "chars": chars})
    for index, match in enumerate(inputs, 1):
        options = _option_tokens(match.group(1) or "")
        missing = sorted(required - options)
        if missing:
            issues.append(f"inputminted 第{index}个代码块缺少参数: {', '.join(missing)}")
    if not re.search(r"(?:\\setmonofont\s*\{\s*Consolas\s*\}|Consolas)", full_text, re.I):
        warnings.append("附录未在局部源文件中声明 Consolas；请确认导言区已统一设置")
    if not re.search(r"(?:\\usemintedstyle\s*\{\s*vs\s*\}|style\s*=\s*vs)", full_text, re.I):
        issues.append("minted 未声明 VS 主题语法高亮（usemintedstyle{vs} 或 style=vs）")
    if not re.search(r"\\definecolor\s*\{\s*codebg\s*\}", full_text, re.I) and not re.search(r"codebg", full_text, re.I):
        issues.append("未定义 minted 浅灰背景色 codebg")
    if len(re.findall(r"\\medskip\b", tail, re.I)) < code_count * 2:
        issues.append("代码块前后必须使用 \\medskip 保留合理垂直间距")
    return {"count": code_count, "blocks": missing_by_block}


def check(tex: str, paper_dir: Path, contract: dict[str, Any] | None,
          contract_path: Path | None, strict: bool = False,
          manifest_kind: str = "legacy") -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    root = paper_dir.resolve()
    appendix_match = APPENDIX_RE.search(tex)
    full_sources: list[str] = []
    derivations: list[str] = []
    raw_tables: list[str] = []
    support_files: list[str] = []
    core_sources: list[str] = []
    support_sources: list[str] = []
    requirements = {"program_used": True, "need_derivation": True, "need_raw_data": True,
                    "need_support": True, "explicit_program": None, "module_kinds": []}
    program_used = True
    required_sections: list[str] = ["A", "B", "C"]
    if contract is None:
        if strict:
            issues.append("严格附录门禁必须提供 appendix_plan.yaml 或 appendix_contract.yaml/json，禁止凭空生成附录")
    else:
        if manifest_kind == "plan" and strict and str(contract.get("status", "DRAFT")).upper() not in {"READY", "FINAL"}:
            issues.append("appendix_plan 仍为 DRAFT；补齐真实材料、锚点和来源后才能进入严格交付")
        full_sources, derivations, raw_tables, support_files = _source_lists(contract)
        source = _source_config(contract)
        core_sources = _core_source_files(contract)
        support_sources = _support_source_files(contract, full_sources, support_files)
        requirements = _manifest_requirements(contract)
        program_used = bool(requirements["program_used"])
        mode = requirements["appendix_code_mode"]
        if mode not in CODE_APPENDIX_MODES:
            issues.append("source_inputs.appendix_code_mode 必须为 not_applicable、core_only 或 full_source")
        if not program_used and mode != "not_applicable":
            issues.append("未使用程序时 appendix_code_mode 必须为 not_applicable")
        if program_used and mode == "not_applicable":
            issues.append("使用程序时 appendix_code_mode 不能为 not_applicable")
        official = contract.get("official_format") if isinstance(contract.get("official_format"), dict) else {}
        configured = _as_list(official.get("appendix_ids")) or _as_list(contract.get("required_appendix_ids"))
        if configured:
            required_sections = [item.upper() for item in configured]
        elif strict and manifest_kind != "plan":
            issues.append("附录契约缺少必填字段: required_appendix_ids（默认应为 A/B/C）")
        required_inputs = {"full_source_files": (program_used, full_sources),
                           "long_derivation_files": (requirements["need_derivation"], derivations),
                           "raw_data_files": (requirements["need_raw_data"], raw_tables),
                           "support_material_files": (requirements["need_support"], support_files)}
        for key, (needed, value) in required_inputs.items():
            if not needed:
                continue
            if key not in source:
                issues.append(f"附录计划缺少已触发的输入字段: {key}")
            elif not value:
                message = f"附录计划 {key} 为空；已触发的证据类型必须提供真实输入材料"
                (issues if strict else warnings).append(message)
        for label, values in (("完整源码", full_sources), ("长推导", derivations),
                              ("原始数据", raw_tables), ("支撑材料", support_files)):
            for raw in values:
                candidate, error = _safe_source(root, raw)
                if error:
                    issues.append(error)
                elif candidate is not None and not candidate.exists():
                    issues.append(f"{label}文件不存在: {raw}")
        for label, values in (("核心源码", core_sources), ("支撑材料源码", support_sources)):
            for raw in values:
                candidate, error = _safe_source(root, raw)
                if error:
                    issues.append(error)
                elif candidate is not None and not candidate.exists():
                    issues.append(f"{label}文件不存在: {raw}")

    if not appendix_match:
        if full_sources or derivations or raw_tables or contract is not None:
            issues.append("存在附录输入材料但 TeX 未找到 \\appendix")
        else:
            warnings.append("未发现 \\appendix；请确认论文确实不需要附录")
        return _report(issues, warnings, contract_path, required_sections, [], 0,
                       {"manifest_kind": manifest_kind, "requirements": requirements})

    tail = tex[appendix_match.end():]
    ref_pos = _references_position(tex)
    if ref_pos is None:
        issues.append("附录前未检测到参考文献位置，无法证明附录位于参考文献之后")
    elif ref_pos > appendix_match.start():
        issues.append("附录出现在参考文献之前，章节顺序违规")

    headings = _heading_ids(tail)
    missing_sections = [item for item in required_sections if item not in headings]
    if missing_sections:
        issues.append("缺少附录章节: " + ", ".join(f"附录{item}" for item in missing_sections))

    body = tex[:appendix_match.start()]
    for match in APP_REF_RE.finditer(body):
        appendix_id = (match.group(1) or match.group(2) or "").upper()
        if appendix_id and appendix_id not in headings:
            issues.append(f"正文引用附录{appendix_id}，但未找到对应附录章节")

    labels = LABEL_RE.findall(tail)
    all_appendix_labels = [f"{kind.lower()}:{letter.upper()}-{number}" for kind, letter, number in labels]
    duplicates = sorted({label for label in all_appendix_labels if all_appendix_labels.count(label) > 1})
    if duplicates:
        issues.append("附录图表标签重复: " + ", ".join(duplicates))
    body_labels = {match.group(1).strip().lower() for match in ANY_LABEL_RE.finditer(body)}
    conflicts = sorted({label for label in all_appendix_labels if label.lower() in body_labels})
    if conflicts:
        issues.append("附录图表标签与正文冲突: " + ", ".join(conflicts))
    for env in re.finditer(r"\\begin\s*\{(figure|table)\}(.*?)\\end\s*\{\1\}", tail, re.I | re.S):
        if not LABEL_RE.search(env.group(2)):
            issues.append(f"附录 {env.group(1)} 环境缺少 tab:A-1/fig:B-1 格式标签")

    code_info = _check_minted(tail, tex, issues, warnings)
    code_present = code_info.get("count", 0) > 0
    code_regions = _code_regions(tail)
    code_mode = requirements.get("appendix_code_mode", "core_only")
    explicit_code_mode = bool(requirements.get("explicit_code_mode"))
    if contract is not None and code_present != program_used:
        issues.append("附录代码块与附录计划的 program_used 不一致")
    if not code_present and program_used is False and NO_PROGRAM not in tail:
        issues.append(f"无代码附录必须明确写出：{NO_PROGRAM}")
    if code_present and NO_PROGRAM in tail:
        warnings.append("附录同时出现代码块和无程序声明，请确认契约中的 program_used")
    if contract is not None and program_used and explicit_code_mode:
        if not core_sources:
            issues.append("程序题附录必须登记 core_source_files 或核心代码模块 source_files")
        missing_full = sorted({_path_key(raw): raw for raw in core_sources
                               if _path_key(raw) not in {_path_key(item) for item in full_sources}}.values())
        if missing_full:
            issues.append("核心源码必须属于完整源码清单: " + ", ".join(missing_full))
        invalid_support = sorted({_path_key(raw): raw for raw in support_sources
                                  if _path_key(raw) not in {_path_key(item) for item in full_sources}}.values())
        if invalid_support:
            issues.append("支撑材料源码必须属于完整源码清单: " + ", ".join(invalid_support))
        for raw in core_sources:
            if not any(_path_in_text(region, raw) for region in code_regions):
                issues.append(f"核心源码未绑定到附录代码区: {raw}")
        if code_mode == "full_source":
            for raw in full_sources:
                if not any(_path_in_text(region, raw) for region in code_regions):
                    issues.append(f"完整源码未绑定到附录代码区: {raw}")
    if support_files:
        if "支撑材料文件清单" not in tail:
            issues.append("存在支撑材料文件，但附录缺少“支撑材料文件清单”")
        for raw in support_files:
            names = (raw, Path(raw).name, raw.replace("_", "\\_"), Path(raw).name.replace("_", "\\_"))
            if not any(name in tail for name in names):
                issues.append(f"支撑材料未在附录清单中登记: {raw}")
    elif not requirements["need_support"] and NO_SUPPORT not in tail:
        issues.append(f"无支撑材料时必须明确写出：{NO_SUPPORT}")
    if full_sources and code_present:
        for raw in full_sources:
            names = (raw, Path(raw).name, raw.replace("_", "\\_"), Path(raw).name.replace("_", "\\_"))
            if not any(name in tail for name in names):
                issues.append(f"完整源码未在支撑材料清单中登记: {raw}")
    if program_used and full_sources:
        missing_support_sources = sorted(set(full_sources) - set(support_sources))
        if missing_support_sources:
            issues.append("完整源码未纳入支撑材料: " + ", ".join(missing_support_sources))

    forbidden = sorted(set(FORBIDDEN_APPENDIX_RE.findall(tail)))
    if forbidden:
        issues.append("附录混入禁止内容: " + "、".join(forbidden))
    if re.search(r"\\(?:clearpage|newpage)\s*\\(?:clearpage|newpage)", tail, re.I):
        warnings.append("附录存在连续强制分页，可能造成大面积空白")

    return _report(issues, warnings, contract_path, required_sections, headings, code_info.get("count", 0),
                   {"manifest_kind": manifest_kind, "labels": all_appendix_labels, "program_used": program_used,
                    "appendix_code_mode": code_mode, "core_source_files": core_sources,
                    "full_source_files": full_sources, "support_source_files": support_sources,
                    "requirements": requirements,
                    "input_counts": {"full_source_files": len(full_sources),
                                     "long_derivation_files": len(derivations),
                                     "raw_data_files": len(raw_tables),
                                     "support_material_files": len(support_files)}})


def _report(issues: list[str], warnings: list[str], contract_path: Path | None,
            required_sections: list[str], headings: list[str], code_count: int,
            details: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("附录位置在参考文献之后", not any("参考文献之前" in item for item in issues)),
        ("使用附录A/B/C规范编号", all(item in headings for item in required_sections)),
        ("正文附录引用均可解析", not any("正文引用附录" in item for item in issues)),
        ("核心源码已绑定且完整源码已登记", not any("核心源码未绑定" in item or "完整源码未" in item for item in issues)),
        ("代码使用minted浅灰底/彩色高亮/行号/framesep", not any("minted" in item or "verbatim" in item or "lstlisting" in item for item in issues)),
        ("代码字体Consolas且字号为\\small", not any("字号违规" in item or "Consolas" in item for item in issues)),
        ("代码块前后有\\medskip", not any("\\medskip" in item for item in issues)),
        ("附录数据与正文来源一致", not any("文件不存在" in item for item in issues)),
        ("已输出支撑材料文件清单或无支撑材料声明", not any("支撑材料" in item for item in issues)),
        ("附录未混入禁止正文/身份/日志内容", not any("禁止内容" in item for item in issues)),
        ("已提示shell-escape与Pygments", not any("shell-escape" in item for item in issues)),
    ]
    return {"schema_version": "1.0", "passed": not issues, "gate_status": "PASS" if not issues else "BLOCK",
            "issues": issues, "warnings": warnings, "contract": str(contract_path) if contract_path else None,
            "required_appendix_ids": required_sections, "headings": headings, "code_blocks": code_count,
            "details": details, "self_check": [{"item": name, "passed": passed} for name, passed in checks],
            "compile_notice": "编译必须开启 -shell-escape，并确认已安装 Pygments。"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="paper directory or TeX file")
    parser.add_argument("--contract", default=None, help="appendix_contract.yaml/json")
    parser.add_argument("--plan", default=None, help="appendix_plan.yaml/json；优先于旧版 appendix_contract")
    parser.add_argument("--project-root", default=None, help="项目根目录；支撑材料可位于 paper/ 之外")
    parser.add_argument("--strict", action="store_true", help="missing evidence blocks delivery")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    path = Path(args.paper).resolve()
    try:
        tex_path = locate_tex(path)
        explicit_root = Path(args.project_root).resolve() if args.project_root else None
        plan_path = locate_plan(tex_path.parent, args.plan, explicit_root)
        contract_path = plan_path or locate_contract(tex_path.parent, args.contract, explicit_root)
        contract = load_contract(contract_path) if contract_path else None
        manifest_kind = "plan" if plan_path else ("legacy" if contract_path else "none")
        project_root = explicit_root or (contract_path.parent if contract_path else tex_path.parent)
        source = expand_inputs(tex_path.read_text(encoding="utf-8", errors="replace"), tex_path.parent)
        report = check(source, project_root,
                       contract, contract_path, strict=args.strict,
                       manifest_kind=manifest_kind)
        report["tex"] = str(tex_path)
        report["manifest_kind"] = manifest_kind
        if not args.strict and report["issues"]:
            report["warnings"] = report["warnings"] + report["issues"]
            report["issues"] = []
            report["passed"] = True
            report["gate_status"] = "WARN"
    except Exception as exc:
        report = {"schema_version": "1.0", "passed": False, "gate_status": "BLOCK",
                  "issues": [str(exc)], "warnings": [], "self_check": []}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
