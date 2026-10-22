#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞赛提交结构门禁（delivery_gate.py）——实现 delivery_gate.md 的 competition_gates 强制检查

用法:
    python scripts/delivery_gate.py <论文目录> [--competition guosai|huashu|mcm_icm] [--pdf 论文.pdf]

检查项（依据 core/competition_gates.yaml 对应竞赛节）:
    P1 页数实测   pypdf 实测 PDF 总页数；若编译产物 .aux 含 markers（AbstractStart/BodyStart/...）
                 则精确核对：摘要页数 ≤ abstract_max_pages、按 profile 计数的正文页数 ≤ page_limit；markers 缺失 → WARN 人工复核
    P2 目录       toc_allowed=false 且 tex 含 \\tableofcontents → FAIL
    P3 禁身份字段 forbidden_identity_terms 命中 tex 或 PDF 文本 → FAIL
    P4 占位符     placeholder_patterns 命中 tex → FAIL
    P5 参考文献   \\bibitem/\\cite 数量 ≥ reference_min
    P6 附录代码   仅当 appendix_plan/appendix_contract 的 program_used=true 时附录须含代码标记
    P7 标题自拟   forbidden_title_patterns 命中标题 → FAIL（guosai/huashu）
    P8 PDF 新鲜度 PDF 修改时间须晚于 tex（防提交旧 PDF）

输出: 控制台 PASS/FAIL + 明细；delivery_gate_report.json 落盘（供 Paper-Critic Compliance 引用）

原则: 页数用编译产物实测，禁止字符估算代替最终门禁（借鉴 Meta-model-agent gate_contracts.py）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from figure_registry import layout_validation_errors

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

try:
    import yaml
except ImportError:
    sys.exit("缺少依赖: pip install pyyaml")
try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("缺少依赖: pip install pypdf")

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "core" / "competition_gates.yaml"
CONFIG_KEYS = ("page_limit", "abstract_max_pages", "toc_allowed", "reference_min", "reference_max",
               "reference_recommended_min", "reference_recommended_max",
               "forbidden_identity_terms", "placeholder_patterns", "appendix_code_required",
               "forbidden_title_patterns", "forbidden_artifact_terms", "markers",
               "body_includes_abstract", "body_includes_references", "body_count_mode",
               "whole_paper_max_pages", "non_image_pdf_required",
               "pdf_max_size_mb")


def load_config(path: Path, competition: str) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if competition not in data:
        default = data.get("default")
        if not isinstance(default, dict):
            sys.exit(f"[FATAL] competition_gates.yaml 无 '{competition}' 节，且没有可用 default profile")
        # Unknown competitions use the explicit neutral default: no national
        # citation quota is inherited silently.  The report records fallback
        # so the user can add an official profile when needed.
        cfg = dict(default)
        cfg["_profile_fallback"] = True
        return cfg
    return data[competition]


def _load_appendix_manifest(workspace: Path, tex: str) -> dict | None:
    """Load the project appendix plan, falling back to the legacy contract."""
    candidates = [workspace / "appendix_plan.yaml", workspace / "appendix_plan.yml",
                  workspace / "appendix_plan.json", workspace / "appendix_contract.yaml",
                  workspace / "appendix_contract.yml", workspace / "appendix_contract.json"]
    paper_dir = workspace / "paper"
    candidates += [paper_dir / path.name for path in candidates]
    for path in candidates:
        if not path.exists():
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            value = json.loads(raw) if path.suffix.lower() == ".json" else yaml.safe_load(raw)
            if isinstance(value, dict):
                value["_manifest_path"] = str(path)
                return value
        except (OSError, ValueError, TypeError, yaml.YAMLError):
            continue
    return None


def appendix_code_required(workspace: Path, tex: str, config: dict) -> bool:
    """Resolve the code gate from actual project evidence, not the题型名.

    A project plan/contract may explicitly set ``program_used``.  A required
    source-code module or code capability also activates the branch.  The
    competition config remains a compatibility fallback, but defaults are no
    longer forced globally.
    """
    manifest = _load_appendix_manifest(workspace, tex)
    if manifest is not None:
        source = manifest.get("source_inputs") if isinstance(manifest.get("source_inputs"), dict) else manifest
        if isinstance(source.get("program_used"), bool):
            return bool(source["program_used"])
        modules = manifest.get("appendix_modules", manifest.get("modules", [])) or []
        required_kinds = {str(item.get("kind", "")).lower() for item in modules
                          if isinstance(item, dict) and item.get("required", False)}
        capabilities = {str(cap).lower() for item in manifest.get("subproblems", []) or []
                        if isinstance(item, dict) for cap in (item.get("capabilities", []) or [])}
        return bool(required_kinds & {"code", "source_code"} or
                    capabilities & {"code", "numerical_fitting", "numerical_simulation",
                                    "machine_learning", "optimization_solver"})
    return bool(config.get("appendix_code_required", False))


def pdf_pages(pdf: Path) -> int | None:
    try:
        return len(PdfReader(str(pdf)).pages)
    except Exception:
        return None


def pdf_text(pdf: Path) -> str:
    try:
        return "\n".join((page.extract_text() or "") for page in PdfReader(str(pdf)).pages)
    except Exception:
        return ""


def visual_sanity_checks(pdf: Path, issues: list, warns: list, info: list):
    """拦截空白页、异常大留白和重复章节编号。"""
    try:
        reader = PdfReader(str(pdf))
        blank_pages = []
        duplicate_headings = []
        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            compact = re.sub(r"\s+", " ", text).strip()
            images = len(getattr(page, "images", []) or [])
            if len(compact) < 20 and images == 0:
                blank_pages.append(idx)
            # Restrict duplicate-number detection to line-start headings.
            # Numeric audit tables legitimately contain adjacent values such
            # as ``60.0022 60.0022`` and must not be treated as repeated
            # section headings.
            for m in re.finditer(r"(?m)^\s*(\d+\.\d+)\s+\1(?:\s|$)", text):
                duplicate_headings.append((idx, m.group(1)))
            for m in re.finditer(r"(?m)^\s*([A-D]\.\d+)\s+\1(?:\s|$)", text):
                duplicate_headings.append((idx, m.group(1)))
        if blank_pages:
            issues.append(f"P9 视觉契约: 检测到疑似空白页 {blank_pages}")
        else:
            info.append("P9 视觉契约: 未检测到无文字且无图像的空白页")
        # Text extraction alone lets a page with only one short paragraph at
        # the top pass as nonblank.  Use positioned text and drawing objects to
        # catch the historical large-whitespace failure without penalising
        # tables or normal short final appendix pages.
        try:
            import pymupdf
            sparse_pages = []
            doc = pymupdf.open(str(pdf))
            for idx, page in enumerate(doc, start=1):
                body_blocks = []
                for block in page.get_text("blocks"):
                    x0, y0, x1, y1, text = block[:5]
                    compact = re.sub(r"\s+", "", text)
                    if y0 > page.rect.height * 0.88 and compact.isdigit():
                        continue
                    if compact:
                        body_blocks.append((y0, y1, compact))
                if not body_blocks:
                    continue
                chars = sum(len(item[2]) for item in body_blocks)
                content_bottom = max(item[1] for item in body_blocks)
                has_drawings = bool(page.get_drawings())
                if chars < 260 and content_bottom < page.rect.height * 0.32 and not has_drawings:
                    sparse_pages.append(idx)
            if sparse_pages:
                issues.append(f"P9 视觉契约: 检测到大面积异常留白页 {sparse_pages}")
            else:
                info.append("P9 视觉契约: 未检测到内容仅堆在页首的大面积异常留白")
        except ImportError:
            warns.append("P9 视觉契约: 未安装 pymupdf，跳过大面积留白定位")
        except Exception as exc:
            warns.append(f"P9 视觉契约: 大面积留白检查失败（{exc}）")
        if duplicate_headings:
            issues.append(f"P9 视觉契约: 检测到重复章节编号 {duplicate_headings}")
    except Exception as exc:
        warns.append(f"P9 视觉契约: 自动检查失败，需人工复核（{exc}）")


def figure_registry_checks(workspace: Path, issues: list, warns: list, info: list,
                           project_root: Path | None = None):
    """检查图表来源、格式和视觉 QA 留痕，避免来源字段与实际产物不一致。"""
    candidates = [workspace / "figure_registry.json", workspace.parent / "figure_registry.json"]
    if project_root is not None:
        candidates.extend([project_root / "figure_registry.json",
                           project_root / "05_输出与交付" / "figure_registry.json"])
    registry = next((path for path in candidates if path.exists()), candidates[0])
    if not registry.exists():
        issues.append("P10 图表来源: 未找到 figure_registry.json")
        return
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("schema_version") not in {"2.0", 2.0}:
            issues.append("P10 图表来源: registry schema_version 必须为 2.0（旧格式先迁移）")
        entries = data.get("figures", data)
        if isinstance(entries, list):
            entries = {str(item.get("id", i)): item for i, item in enumerate(entries) if isinstance(item, dict)}
        if not isinstance(entries, dict) or not entries:
            issues.append("P10 图表来源: figure_registry.json 没有图表条目")
            return
        missing = []
        bad = []
        source_root = registry.parent if project_root is None else project_root
        for key, item in entries.items():
            if not isinstance(item, dict):
                bad.append(f"{key}: 元数据不是对象")
                continue
            kind = item.get("kind", item.get("type"))
            generator = str(item.get("generator", item.get("generated_by", ""))).strip().lower()
            source = item.get("source_files", item.get("data_source"))
            required = {"kind": kind, "generator": generator, "formats": item.get("formats"),
                        "source_files": source, "script": item.get("script"), "qa_status": item.get("qa_status")}
            missing_fields = [field for field, value in required.items() if not value]
            if missing_fields:
                missing.append(f"{key}: {missing_fields}")
            normalized_kind = str(kind).lower()
            if normalized_kind in {"data", "chart", "plot", "flow", "flowchart", "schematic", "drawio"}:
                if str(item.get("insertion_format", "")).lower() != "svg":
                    bad.append(f"{key}: 图片 insertion_format 必须为 svg")
                formats = {str(value).lower() for value in item.get("formats", []) or []}
                if formats != {"png", "svg"}:
                    bad.append(f"{key}: 图片 formats 必须严格为 svg、png，禁止 pdf")
                bad.extend(layout_validation_errors(str(key), item))
            if normalized_kind in {"data", "chart", "plot"}:
                if generator != "modelviz":
                    bad.append(f"{key}: 数据图必须 generator=modelviz，实际 {generator or 'missing'}")
                if item.get("semantic_qa") != "scipilot-figure-skill":
                    bad.append(f"{key}: 数据图必须 semantic_qa=scipilot-figure-skill")
                if item.get("decision_author") != "scipilot-figure-skill":
                    bad.append(f"{key}: 数据图必须登记 SciPilot 图表决策卡作者")
                decision_card = item.get("decision_card")
                if not decision_card or not (source_root / str(decision_card)).exists():
                    bad.append(f"{key}: 数据图缺少可用的 SciPilot 图表决策卡")
            if normalized_kind in {"flowchart", "flow"} and generator != "tech-route-maker":
                bad.append(f"{key}: 流程图必须由 tech-route-maker 生成，实际 {generator or 'missing'}")
            if normalized_kind == "schematic" and generator != "tikz-scientific-figures":
                bad.append(f"{key}: 示意图必须由 tikz-scientific-figures 生成，实际 {generator or 'missing'}")
            if normalized_kind == "drawio" and (generator != "drawio-diagram" or item.get("user_requested") is not True):
                bad.append(f"{key}: Draw.io 仅允许用户明确请求且必须 generator=drawio-diagram")
            if generator == "tech-route-maker":
                role = str(item.get("diagram_role", "")).lower()
                if role not in {"problem_analysis_flowchart", "technical_roadmap"}:
                    bad.append(f"{key}: tech-route-maker 仅允许问题分析流程图或技术路线框图")
                if not str(item.get("script", "")).lower().endswith(".json"):
                    bad.append(f"{key}: tech-route-maker 必须登记 tech-route.json 源文件")
            if isinstance(source, str):
                source = [part.strip() for part in source.replace("；", ",").split(",") if part.strip()]
            for source_path in source or []:
                candidate = source_root / str(source_path)
                if not candidate.exists():
                    bad.append(f"{key}: source_files 不存在 {source_path}")
            script = item.get("script")
            if script:
                script_path = source_root / str(script)
                if not script_path.exists():
                    bad.append(f"{key}: script 不存在 {script}")
            for fmt in item.get("formats", []):
                if str(fmt).lower() not in {"png", "svg"}:
                    bad.append(f"{key}: 不支持格式 {fmt}")
            if item.get("qa_status") not in {"pass", "reviewed"}:
                bad.append(f"{key}: qa_status={item.get('qa_status')}")
        if missing:
            issues.append(f"P10 图表来源: 缺少元数据 {missing}")
        if bad:
            issues.append(f"P10 图表来源: 元数据不合规 {bad}")
        if not missing and not bad:
            info.append(f"P10 图表来源: {len(entries)} 张图的来源与 QA 元数据完整")
    except Exception as exc:
        issues.append(f"P10 图表来源: registry 无法解析（{exc}）")


def delivery_manifest_check(workspace: Path, issues: list, warns: list, info: list):
    manifest = workspace / "delivery_manifest.json"
    if not manifest.exists():
        warns.append("P11 交付路径: 未找到 delivery_manifest.json，无法确认稳定工作区")
        return
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if not data.get("canonical") or not data.get("passed") or data.get("issues"):
            issues.append(f"P11 交付路径: manifest 未通过 {data.get('issues', [])}")
        else:
            info.append("P11 交付路径: 稳定工作区 manifest 已通过")
    except Exception as exc:
        issues.append(f"P11 交付路径: manifest 无法解析（{exc}）")


def pdf_text_layer_check(pdf: Path, issues: list, warns: list, info: list,
                         require_text_layer: bool = False):
    """检查中文 PDF 是否有可搜索的 Unicode 文本层。"""
    try:
        import pymupdf
        text = "".join(page.get_text() for page in pymupdf.open(str(pdf)))
        replacement = text.count("\ufffd")
        cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
        if replacement:
            issues.append(f"P12 PDF 文本层: 检测到 {replacement} 个替换字符，中文可能不可搜索")
        elif require_text_layer and cjk == 0:
            issues.append("P12 PDF 文本层: 未检测到可提取文本，不符合非图片 PDF 要求")
        elif cjk < 100:
            warns.append(f"P12 PDF 文本层: 可提取中文字符偏少（{cjk}），需人工确认字体映射")
        else:
            info.append(f"P12 PDF 文本层: Unicode 中文可提取（{cjk} 字符）")
    except ImportError:
        warns.append("P12 PDF 文本层: 未安装 pymupdf，跳过 Unicode 检查")
    except Exception as exc:
        warns.append(f"P12 PDF 文本层: 检查失败（{exc}）")


def supporting_material_size_check(workspace: Path, cfg: dict,
                                   issues: list, info: list):
    """Check discovered ZIP/RAR support packages against the profile limit."""
    limit = cfg.get("supporting_materials", {}).get("max_size_mb")
    if limit is None:
        return
    candidates = set(workspace.glob("support_materials_*.zip"))
    candidates.update(workspace.glob("support_materials_*.rar"))
    candidates.update(workspace.parent.glob("support_materials_*.zip"))
    candidates.update(workspace.parent.glob("support_materials_*.rar"))
    for archive in sorted(path.resolve() for path in candidates if path.is_file()):
        size_mb = archive.stat().st_size / (1024 * 1024)
        if size_mb > float(limit):
            issues.append(f"P13 支撑材料: {archive.name} 为 {size_mb:.2f} MB，超过 {limit} MB")
        else:
            info.append(f"P13 支撑材料: {archive.name} 为 {size_mb:.2f} MB")


def aux_label_page(workspace: Path, label: str, preferred_stem: str | None = None) -> int | None:
    """从与目标 PDF 对应的 .aux 读取 \\label{xxx} 对应页码。"""
    aux_files = sorted(workspace.glob("*.aux"))
    if preferred_stem:
        preferred = workspace / f"{preferred_stem}.aux"
        if preferred.is_file():
            aux_files = [preferred] + [aux for aux in aux_files if aux != preferred]
    for aux in aux_files:
        text = aux.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\\newlabel\{" + re.escape(label) + r"(?:Label)?\}\{\{[^}]*\}\{(\d+)\}", text)
        if m:
            return int(m.group(1))
    return None


def appendix_start_page(pdf: Path) -> int | None:
    """自动定位附录起始页：逐页扫描 PDF 文本，找"附录"标题行（行首、短行）。无需用户加 label。"""
    try:
        reader = PdfReader(str(pdf))
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            for line in text.split("\n"):
                s = line.strip()
                if s.startswith("附录") and len(s) <= 24:
                    return i + 1
    except Exception:
        pass
    # Some XeLaTeX PDFs expose Chinese text to PyMuPDF but not to pypdf.
    # Use the same short-line rule as the primary path so page counting stays consistent.
    try:
        import pymupdf
        document = pymupdf.open(pdf)
        for i, page in enumerate(document):
            for line in page.get_text().splitlines():
                s = line.strip()
                if s.startswith("附录") and len(s) <= 24:
                    document.close()
                    return i + 1
        document.close()
    except Exception:
        pass
    return None


def tex_sources(workspace: Path) -> list[Path]:
    return sorted(path for path in workspace.rglob("*.tex") if path.is_file())


def tex_corpus(workspace: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in tex_sources(workspace))


def extract_citation_keys(tex: str) -> set[str]:
    """Return unique keys used by citation commands, excluding ``\\nocite``.

    Counting every entry in a .bib file is unsafe: an unused bibliography pool
    must not satisfy the competition minimum.  Optional prenote/postnote
    arguments are accepted for common natbib/biblatex commands.
    """
    command = r"\\(?:cite|citep|citet|parencite|textcite|footcite|autocite|supercite|citeauthor|citeyear)"
    pattern = re.compile(command + r"(?:\s*\[[^]]*\]){0,2}\s*\{([^}]*)\}")
    keys: set[str] = set()
    for match in pattern.finditer(tex):
        keys.update(key.strip() for key in match.group(1).split(",") if key.strip())
    return keys


def citation_stats(workspace: Path, tex: str) -> dict:
    """Compute unique cited bibliography keys and unknown/unused keys."""
    bib_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in workspace.glob("*.bib"))
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib_text))
    cited_keys = extract_citation_keys(tex)
    if bib_keys:
        unknown = sorted(cited_keys - bib_keys)
        cited_bib = sorted(cited_keys & bib_keys)
        unused = sorted(bib_keys - cited_keys)
        count = len(cited_bib)
    else:
        bibitem_keys = set(re.findall(r"\\bibitem(?:\[[^]]*\])?\{([^}]+)\}", tex))
        unknown = sorted(cited_keys - bibitem_keys) if bibitem_keys else []
        cited_bib = sorted(cited_keys & bibitem_keys) if bibitem_keys else []
        unused = sorted(bibitem_keys - cited_keys) if bibitem_keys else []
        count = len(cited_bib) if bibitem_keys else 0
    return {
        "bib_entry_count": len(bib_keys),
        "unique_cited_keys": cited_bib,
        "unique_cited_count": count,
        "unused_bib_keys": unused,
        "unknown_citation_keys": unknown,
    }


def page_checks(workspace: Path, pdf: Path, cfg: dict, issues: list, warns: list, info: list):
    total = pdf_pages(pdf)
    if total is None:
        issues.append("P1 页数: PDF 无法解析")
        return
    info.append(f"P1 页数: PDF 总页数 {total}")
    whole_limit = cfg.get("whole_paper_max_pages")
    if whole_limit:
        info.append(f"P1 提交文件总页数: {total}（要求上限 {whole_limit}）")
        if total > whole_limit:
            issues.append(f"P1 页数: 提交文件总页数 {total} 页 > 限制 {whole_limit} 页")
    markers = cfg.get("markers") or {}
    limit = cfg.get("page_limit")
    minimum = cfg.get("body_min_pages")
    abstract_limit = cfg.get("abstract_max_pages")
    if cfg.get("body_count_mode") == "through_references_before_appendix" and limit:
        appendix = appendix_start_page(pdf)
        end = appendix - 1 if appendix else total
        if cfg.get("body_includes_abstract", True):
            start = aux_label_page(workspace, markers.get("abstract_start", "AbstractStart"), pdf.stem) or 1
            scope = "含摘要、参考文献"
        else:
            abstract_end = aux_label_page(workspace, markers.get("abstract_end", "AbstractEnd"), pdf.stem)
            start = (abstract_end + 1) if abstract_end is not None else aux_label_page(
                workspace, markers.get("body_start", "BodyStart"), pdf.stem
            )
            scope = "正文主体、AI声明和参考文献，摘要不计"
        if start is None:
            warns.append("P1 页数: 未找到正文起始页标签，正文页数需人工复核")
        else:
            body = max(0, end - start + 1)
            info.append(f"P1 正文页数（{scope}，附录前）: {body}（要求上限 {limit}）")
            if body > limit:
                issues.append(f"P1 页数: 正文（{scope}）{body} 页 > 限制 {limit} 页")
    elif markers and limit:
        start_label = (markers.get("abstract_start", "AbstractStart")
                       if cfg.get("body_includes_abstract") else markers.get("body_start", "BodyStart"))
        start = aux_label_page(workspace, start_label, pdf.stem)
        end = aux_label_page(workspace, markers.get("body_end", "BodyEnd"), pdf.stem)
        if start is not None and end is not None:
            body = end - start + 1
            range_text = f"{minimum}-{limit}" if minimum else f"上限 {limit}"
            info.append(f"P1 正文页数（aux 实测）: {body}（要求 {range_text}）")
            if minimum and body < minimum:
                issues.append(f"P1 页数: 正文 {body} 页 < 下限 {minimum} 页")
            if body > limit:
                issues.append(f"P1 页数: 正文 {body} 页 > 限制 {limit} 页")
        else:
            warns.append("P1 页数: 未找到 BodyStart/BodyEnd aux 标签，正文页数需人工复核")
    elif limit:
        warns.append(f"P1 页数: 无 markers 配置或页数限制缺失，正文页数需人工复核（总页数 {total}）")
    if markers and abstract_limit:
        start = aux_label_page(workspace, markers.get("abstract_start", "AbstractStart"), pdf.stem)
        end = aux_label_page(workspace, markers.get("abstract_end", "AbstractEnd"), pdf.stem)
        if start is not None and end is not None:
            apages = end - start + 1
            info.append(f"P1 摘要页数（aux 实测）: {apages}（限制 {abstract_limit}）")
            if apages > abstract_limit:
                issues.append(f"P1 页数: 摘要 {apages} 页 > 限制 {abstract_limit} 页")
        else:
            warns.append("P1 页数: 未找到 AbstractStart/AbstractEnd aux 标签，摘要页数需人工复核")

    # P1b 附录页数（用户硬性 2026-08-15: 附录 13-20 页）——自动定位，无需用户加 label
    amin = cfg.get("appendix_min_pages")
    amax = cfg.get("appendix_max_pages")
    if amin or amax:
        appendix, how = None, ""
        if markers:
            bend = aux_label_page(workspace, markers.get("body_end", "BodyEnd"), pdf.stem)
            if bend is not None and total:
                appendix, how = total - bend, "(BodyEnd aux)"
        if appendix is None and total:
            astart = appendix_start_page(pdf)
            if astart:
                appendix, how = total - astart + 1, f"(PDF 检测'附录'标题页 {astart})"
        if appendix is not None:
            info.append(f"P1b 附录页数: {appendix}（要求 {amin}-{amax}）{how}")
            if appendix < amin:
                issues.append(f"P1b 附录页数: {appendix} 页 < 下限 {amin} 页（附录太薄）")
            if amax and appendix > amax:
                issues.append(f"P1b 附录页数: {appendix} 页 > 上限 {amax} 页")
        else:
            warns.append("P1b 附录页数: 无法定位附录起始（PDF 无'附录'标题且无 BodyEnd aux），需人工复核")


def main():
    ap = argparse.ArgumentParser(description="竞赛提交结构门禁")
    ap.add_argument("workspace", help="论文目录（含 .tex / .pdf / .aux）")
    ap.add_argument("--competition", default="guosai", help="竞赛节: guosai|huashu|mcm_icm")
    ap.add_argument("--pdf", default=None, help="PDF 文件名（默认取目录内最新 .pdf）")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--project-root", default=None,
                    help="标准项目根目录，用于解析图表注册表及其相对来源路径")
    ap.add_argument("--visual-check", action="store_true",
                    help="显式启用自动版面视觉检查；默认跳过，由用户肉眼检查")
    args = ap.parse_args()

    ws = Path(args.workspace)
    if not ws.is_dir():
        sys.exit(f"[FATAL] 目录不存在: {ws}")
    cfg = load_config(Path(args.config), args.competition)

    pdf = ws / args.pdf if args.pdf else max(ws.glob("*.pdf"), key=lambda p: p.stat().st_mtime, default=None)
    if pdf is None:
        sys.exit("[FATAL] 未找到 PDF（--pdf 指定或目录内 *.pdf）")

    issues, warns, info = [], [], []
    if cfg.get("_profile_fallback"):
        warns.append(f"未找到竞赛 profile '{args.competition}'，已使用 neutral default；请按官方规则补充 profile")
    tex = tex_corpus(ws)

    # P0 PDF 完整性（截断/损坏检测——2025C 实战教训：截断 PDF（尾部无 %%EOF）门禁放行）
    try:
        with open(pdf, "rb") as f:
            f.seek(max(0, pdf.stat().st_size - 2048))
            tail = f.read()
        if b"%%EOF" not in tail:
            issues.append(f"P0 PDF 完整性: 文件尾部无 %%EOF（疑似截断/编译未完成），{pdf.name}")
        else:
            _ = PdfReader(str(pdf)).pages
            info.append(f"P0 PDF 完整性: OK（%%EOF 存在且可解析）")
    except Exception as e:
        issues.append(f"P0 PDF 完整性: 无法解析 PDF（{e}）")

    # P1 页数实测
    page_checks(ws, pdf, cfg, issues, warns, info)
    if args.visual_check:
        visual_sanity_checks(pdf, issues, warns, info)
    else:
        info.append("P9 视觉契约: SKIPPED_USER_OPT_IN（自动视觉检查默认关闭，由用户肉眼检查）")
    project_root = Path(args.project_root).resolve() if args.project_root else None
    figure_registry_checks(ws, issues, warns, info, project_root)
    delivery_manifest_check(ws, issues, warns, info)
    pdf_text_layer_check(pdf, issues, warns, info, bool(cfg.get("non_image_pdf_required")))
    if cfg.get("pdf_max_size_mb") is not None:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        if size_mb > float(cfg["pdf_max_size_mb"]):
            issues.append(f"P13 论文 PDF: {size_mb:.2f} MB > 限制 {cfg['pdf_max_size_mb']} MB")
        else:
            info.append(f"P13 论文 PDF: {size_mb:.2f} MB")
    supporting_material_size_check(ws, cfg, issues, info)

    # P2 目录
    if cfg.get("toc_allowed") is False and "\\tableofcontents" in tex:
        issues.append("P2 目录: 本竞赛禁止目录，tex 含 \\tableofcontents")

    # P3 禁身份字段（tex + PDF 文本双扫）
    forbidden = cfg.get("forbidden_identity_terms") or []
    hits = [t for t in forbidden if t.lower() in tex.lower() or t.lower() in pdf_text(pdf).lower()]
    if hits:
        issues.append(f"P3 身份字段: 命中 {hits}")

    # P4 占位符
    ph = cfg.get("placeholder_patterns") or []
    hits = [p for p in ph if p in tex]
    if hits:
        issues.append(f"P4 占位符: 残留 {hits}")

    # P4.5 论文不得泄漏内部交付索引或模板占位字段。
    # 必须扫描最终 PDF，而不只扫描 tex：生成器可能在后处理阶段插入这些文字。
    forbidden_artifacts = cfg.get("forbidden_artifact_terms") or []
    artifact_hits = [term for term in forbidden_artifacts if term in pdf_text(pdf) or term in tex]
    if artifact_hits:
        issues.append(f"P4.5 内部交付/占位文字: 残留 {artifact_hits}")

    # P5 参考文献：只按正文实际调用的唯一键计数；未使用的 .bib 条目不能
    # 充数，也不能安静地留在正式文献表中，避免“文末堆积、正文不出现”。
    # 文献数量是竞赛 profile 的规则，不是全局规则。None/缺失表示仅做
    # 唯一引用、未知键、未使用条目和元数据一致性审计，不设置数量门槛。
    ref_min_raw = cfg.get("reference_min")
    ref_max_raw = cfg.get("reference_max")
    ref_recommended_min_raw = cfg.get("reference_recommended_min")
    ref_recommended_max_raw = cfg.get("reference_recommended_max")
    ref_min = int(ref_min_raw) if ref_min_raw not in (None, "") else 0
    ref_max = int(ref_max_raw) if ref_max_raw not in (None, "", 0) else None
    ref_recommended_min = int(ref_recommended_min_raw) if ref_recommended_min_raw not in (None, "") else None
    ref_recommended_max = int(ref_recommended_max_raw) if ref_recommended_max_raw not in (None, "") else None
    citation_report = citation_stats(ws, tex)
    refs = citation_report["unique_cited_count"]
    if citation_report["unknown_citation_keys"]:
        issues.append("P5 参考文献: 正文引用键不存在于文献库 "
                      f"{citation_report['unknown_citation_keys']}")
    if cfg.get("unused_bib_is_failure", True) and citation_report["unused_bib_keys"]:
        issues.append("P5 参考文献: 文献库存在未被正文调用的条目 "
                      f"{citation_report['unused_bib_keys']}")
    if ref_min or ref_max:
        ref_requirement = f"{ref_min}-{ref_max or '不限'}"
    else:
        ref_requirement = "按 profile 不设数量门槛"
    info.append(f"P5 参考文献: {refs} 条（要求 {ref_requirement}）")
    if refs < ref_min:
        issues.append(f"P5 参考文献: {refs} < 下限 {ref_min}")
    if ref_max and refs > ref_max:
        issues.append(f"P5 参考文献: {refs} > 上限 {ref_max}")
    if ref_recommended_min and ref_recommended_max:
        recommendation = f"推荐 {ref_recommended_min}-{ref_recommended_max}"
        if not ref_recommended_min <= refs <= ref_recommended_max:
            warns.append(f"P5 参考文献: {refs} 条，{recommendation}，不阻断交付")
        else:
            info.append(f"P5 参考文献: 满足{recommendation}")

    # P6 附录代码：只在项目实际使用程序/数值求解时启用。
    if appendix_code_required(ws, tex, cfg):
        appx = tex.split("\\appendix", 1)
        if len(appx) != 2:
            issues.append("P6 附录代码: TeX 缺少 \\appendix，不能用正文代码冒充附录")
        else:
            appendix = appx[1]
            code_marks = (r"\\begin\{lstlisting\}", r"\\lstinputlisting", r"\\begin\{verbatim\}",
                          r"\\begin\{minted\}", r"\\inputminted", "CODE_FILE", "```python", "```matlab")
            if not any(re.search(mark, appendix) if mark.startswith(r"\\") else mark in appendix for mark in code_marks):
                issues.append("P6 附录代码: 附录未见实际代码环境（lstlisting/verbatim/minted/CODE_FILE）")

    # P7 标题自拟
    title_patterns = cfg.get("forbidden_title_patterns") or []
    title_m = re.search(r"\\title\{([^}]*)\}", tex) or re.search(r"^#\s*(.+)$", tex, re.M)
    title = title_m.group(1).strip() if title_m else ""
    if title:
        hits = [p for p in title_patterns if p in title]
        if hits:
            issues.append(f"P7 标题自拟: 标题命中禁用词 {hits}（标题='{title[:30]}'）")

    # P8 PDF 新鲜度
    pdf_mtime = pdf.stat().st_mtime
    stale = [t.name for t in tex_sources(ws) if t.stat().st_mtime > pdf_mtime]
    if stale:
        issues.append(f"P8 PDF 新鲜度: 下列 tex 晚于 PDF，禁止交付旧版: {stale}")

    report = {"competition": args.competition, "pdf": str(pdf), "passed": not issues,
              "visual_check_requested": args.visual_check,
              "visual_check_status": "EXECUTED" if args.visual_check else "SKIPPED_USER_OPT_IN",
              "issues": issues, "warnings": warns, "info": info,
              "citation_stats": citation_report}
    (ws / "delivery_gate_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    for line in info:
        print(f"  [info] {line}")
    for line in warns:
        print(f"  [WARN] {line}")
    for line in issues:
        print(f"  [FAIL] {line}")
    verdict = "PASS 可提交" if not issues else "FAIL 打回修复"
    print(f"\n[{verdict}]（{args.competition} · 报告: delivery_gate_report.json）")
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
