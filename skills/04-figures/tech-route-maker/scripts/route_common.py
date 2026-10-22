import copy
import json
import math
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech_route_maker.registry import SUPPORTED_LAYOUTS, layout_family  # noqa: E402


STYLES = {
    "academic-blue": {
        "background": "#FFFFFF",
        "text": "#1F2937",
        "muted": "#64748B",
        "line": "#2563EB",
        "stage_fill": "#EFF6FF",
        "stage_stroke": "#93C5FD",
        "header_fill": "#1D4ED8",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#60A5FA",
        "palette": ["#DBEAFE", "#E0F2FE", "#EEF2FF", "#ECFDF5", "#FFF7ED", "#FDF2F8"],
    },
    "blue-green-research": {
        "background": "#FFFFFF",
        "text": "#12333A",
        "muted": "#527078",
        "line": "#0F766E",
        "stage_fill": "#ECFEFF",
        "stage_stroke": "#5EEAD4",
        "header_fill": "#0E7490",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#14B8A6",
        "palette": ["#CFFAFE", "#CCFBF1", "#DCFCE7", "#E0F2FE", "#F0FDFA", "#F7FEE7"],
    },
    "monochrome-paper": {
        "background": "#FFFFFF",
        "text": "#111111",
        "muted": "#555555",
        "line": "#111111",
        "stage_fill": "#F5F5F5",
        "stage_stroke": "#777777",
        "header_fill": "#222222",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#333333",
        "palette": ["#F8F8F8", "#EEEEEE", "#E5E5E5", "#DDDDDD", "#D4D4D4", "#CCCCCC"],
    },
    "defense-color": {
        "background": "#FFFFFF",
        "text": "#172033",
        "muted": "#4B5563",
        "line": "#7C3AED",
        "stage_fill": "#F8FAFC",
        "stage_stroke": "#CBD5E1",
        "header_fill": "#4338CA",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#8B5CF6",
        "palette": ["#DBEAFE", "#EDE9FE", "#DCFCE7", "#FEF3C7", "#FFE4E6", "#CCFBF1"],
    },
    "minimal-gray": {
        "background": "#FFFFFF",
        "text": "#242424",
        "muted": "#6B7280",
        "line": "#475569",
        "stage_fill": "#F8FAFC",
        "stage_stroke": "#CBD5E1",
        "header_fill": "#334155",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#94A3B8",
        "palette": ["#F8FAFC", "#F1F5F9", "#E2E8F0", "#F8FAFC", "#F1F5F9", "#E2E8F0"],
    },
    "nature-editorial": {
        "background": "#FFFFFF",
        "text": "#17201D",
        "muted": "#5B6670",
        "line": "#2F5D62",
        "stage_fill": "#F7FAF8",
        "stage_stroke": "#A7C4BC",
        "header_fill": "#2F5D62",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#7AA6A1",
        "palette": ["#E8F3F1", "#EEF2E6", "#F7EEE3", "#EAF0F6", "#F2EAF3", "#F6F4EA"],
    },
    "accessible-high-contrast": {
        "background": "#FFFFFF",
        "text": "#000000",
        "muted": "#333333",
        "line": "#000000",
        "stage_fill": "#FFFFFF",
        "stage_stroke": "#000000",
        "header_fill": "#000000",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#000000",
        "palette": ["#FFFFFF", "#F2F2F2", "#E6E6E6", "#FFFFFF", "#F2F2F2", "#E6E6E6"],
    },
    "dark-technical": {
        "background": "#0B1020",
        "text": "#E5E7EB",
        "muted": "#AAB2C0",
        "line": "#38BDF8",
        "stage_fill": "#111827",
        "stage_stroke": "#334155",
        "header_fill": "#0F766E",
        "header_text": "#FFFFFF",
        "node_fill": "#111827",
        "node_stroke": "#38BDF8",
        "palette": ["#172554", "#164E63", "#064E3B", "#3B0764", "#451A03", "#4C0519"],
    },
    "soft-pastel": {
        "background": "#FFFFFF",
        "text": "#334155",
        "muted": "#64748B",
        "line": "#64748B",
        "stage_fill": "#FFFBF7",
        "stage_stroke": "#E5E7EB",
        "header_fill": "#A78BFA",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#C4B5FD",
        "palette": ["#FDE2E4", "#E2F0CB", "#CDE7F0", "#F7D9C4", "#D8E2DC", "#E8DAEF"],
    },
    "schematic-precision": {
        "background": "#FFFFFF",
        "text": "#111827",
        "muted": "#4B5563",
        "line": "#1F2937",
        "stage_fill": "#F9FAFB",
        "stage_stroke": "#9CA3AF",
        "header_fill": "#374151",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#111827",
        "palette": ["#F9FAFB", "#F3F4F6", "#EEF2FF", "#ECFEFF", "#F0FDF4", "#FFFBEB"],
    },
    "editorial-clarity": {
        "background": "#FFFFFF",
        "text": "#18212F",
        "muted": "#687386",
        "line": "#2563EB",
        "stage_fill": "#FFFFFF",
        "stage_stroke": "#E2E8F0",
        "header_fill": "#1E40AF",
        "header_text": "#FFFFFF",
        "node_fill": "#F8FAFC",
        "node_stroke": "#CBD5E1",
        "palette": ["#EFF6FF", "#F8FAFC", "#ECFDF5", "#F8FAFC", "#FFF7ED", "#F8FAFC"],
    },
    "mechanism-snapshot": {
        "background": "#FFFFFF",
        "text": "#1E293B",
        "muted": "#64748B",
        "line": "#C2410C",
        "stage_fill": "#FFF7ED",
        "stage_stroke": "#FDBA74",
        "header_fill": "#C2410C",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#FB923C",
        "palette": ["#FFEDD5", "#FEF3C7", "#ECFCCB", "#E0F2FE", "#FDE68A", "#FED7AA"],
    },
    "evidence-infographic": {
        "background": "#FFFFFF",
        "text": "#172033",
        "muted": "#475569",
        "line": "#7C3AED",
        "stage_fill": "#FAF5FF",
        "stage_stroke": "#C4B5FD",
        "header_fill": "#6D28D9",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#A78BFA",
        "palette": ["#EDE9FE", "#DBEAFE", "#DCFCE7", "#FEF3C7", "#FCE7F3", "#CCFBF1"],
    },
    "premium-scientific": {
        "background": "#FFFFFF",
        "text": "#17201D",
        "muted": "#59636A",
        "line": "#315C61",
        "stage_fill": "#F8FAF9",
        "stage_stroke": "#B8C7C1",
        "header_fill": "#315C61",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#8BAAA5",
        "palette": ["#E8F3F1", "#F2EFE6", "#EAF0F6", "#F6F1E8", "#EDF4EA", "#F3EEF4"],
    },
    "advertising-clean-campaign": {
        "background": "#FFFFFF",
        "text": "#111827",
        "muted": "#5B6472",
        "line": "#E11D48",
        "stage_fill": "#FFF7F7",
        "stage_stroke": "#FDA4AF",
        "header_fill": "#E11D48",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#FB7185",
        "palette": ["#FFE4E6", "#FEF3C7", "#DBEAFE", "#DCFCE7", "#FCE7F3", "#E0F2FE"],
    },
    "proposal-pastel-route": {
        "background": "#FFFFFF",
        "text": "#162033",
        "muted": "#5B6472",
        "line": "#2C6A93",
        "stage_fill": "#F8FBFC",
        "stage_stroke": "#6FAEC3",
        "header_fill": "#7BCFD0",
        "header_text": "#122033",
        "node_fill": "#FFFFFF",
        "node_stroke": "#9FB6C4",
        "palette": ["#D9F2F2", "#F7E0E8", "#FFF1C7", "#DDECF9", "#E6F4D7", "#F6E7D7"],
        "accent": "#F36E78",
        "accent_2": "#F7C744",
        "accent_3": "#67C7A5",
        "stage_dash": "6 6",
    },
    "grant-linework": {
        "background": "#FFFFFF",
        "text": "#111111",
        "muted": "#555555",
        "line": "#111111",
        "stage_fill": "#FFFFFF",
        "stage_stroke": "#222222",
        "header_fill": "#FFFFFF",
        "header_text": "#111111",
        "node_fill": "#FFFFFF",
        "node_stroke": "#222222",
        "palette": ["#FFFFFF", "#F7F7F7", "#FFFFFF", "#F7F7F7", "#FFFFFF", "#F7F7F7"],
        "accent": "#111111",
        "accent_2": "#666666",
        "accent_3": "#999999",
        "stage_dash": "7 5",
    },
    "wide-collaboration-map": {
        "background": "#FFFFFF",
        "text": "#111827",
        "muted": "#526070",
        "line": "#2D5CA8",
        "stage_fill": "#F8FBFF",
        "stage_stroke": "#AFC4E8",
        "header_fill": "#2D5CA8",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#8BADE3",
        "palette": ["#DCE9FF", "#DFF2E3", "#E9EEFF", "#FFF1D6", "#E4F6F5", "#FCE3E8"],
        "accent": "#2D5CA8",
        "accent_2": "#5E9F3B",
        "accent_3": "#D94E4E",
        "stage_dash": "8 6",
    },
    "cn-polished-pastel-academic": {
        "background": "#FFFFFF",
        "text": "#13243A",
        "muted": "#5D6B7A",
        "line": "#4C8CBF",
        "stage_fill": "#F8FBFC",
        "stage_stroke": "#78B5C7",
        "header_fill": "#64C7C8",
        "header_text": "#102033",
        "node_fill": "#FFFFFF",
        "node_stroke": "#A8B8C5",
        "palette": ["#DDF3F3", "#F9E3EB", "#FFF1C9", "#DDECF8", "#E7F5DA", "#F7E8D9"],
        "accent": "#F36F7B",
        "accent_2": "#F6C54B",
        "accent_3": "#5CC5A8",
        "stage_dash": "7 6",
        "canvas_stroke": "#D8E5EE",
    },
    "cn-blue-green-proposal": {
        "background": "#FFFFFF",
        "text": "#152E3A",
        "muted": "#57717A",
        "line": "#2F7CA6",
        "stage_fill": "#F7FBFB",
        "stage_stroke": "#7CB7C6",
        "header_fill": "#5AA6D6",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#9EB7C8",
        "palette": ["#D8F0EA", "#DDEBFB", "#EAF4D9", "#FFF0D4", "#F6E2E8", "#E6F3F6"],
        "accent": "#3EA8C8",
        "accent_2": "#6AA43A",
        "accent_3": "#E58B3A",
        "stage_dash": "7 6",
    },
    "cn-soft-grant-report": {
        "background": "#FFFFFF",
        "text": "#172033",
        "muted": "#59636A",
        "line": "#315C88",
        "stage_fill": "#FAFCFD",
        "stage_stroke": "#AEBECC",
        "header_fill": "#4E7FB0",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#AAB8C5",
        "palette": ["#E7F0F7", "#F5E5E2", "#F7F1D8", "#E6F2DF", "#EAE7F4", "#F7ECE1"],
        "accent": "#4E7FB0",
        "accent_2": "#D34B4B",
        "accent_3": "#6E9B49",
        "stage_dash": "8 6",
    },
    "cn-reviewer-linework": {
        "background": "#FFFFFF",
        "text": "#111111",
        "muted": "#555555",
        "line": "#222222",
        "stage_fill": "#FFFFFF",
        "stage_stroke": "#333333",
        "header_fill": "#F4F4F4",
        "header_text": "#111111",
        "node_fill": "#FFFFFF",
        "node_stroke": "#222222",
        "palette": ["#FFFFFF", "#F8F8F8", "#FFFFFF", "#F4F4F4", "#FFFFFF", "#F8F8F8"],
        "accent": "#111111",
        "accent_2": "#666666",
        "accent_3": "#999999",
        "stage_dash": "8 5",
        "canvas_stroke": "#BBBBBB",
    },
    "cn-defense-poster": {
        "background": "#FFFFFF",
        "text": "#101A2B",
        "muted": "#5E6B78",
        "line": "#4E86B8",
        "stage_fill": "#F9FBFC",
        "stage_stroke": "#8EB7C8",
        "header_fill": "#2F6FA8",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#A7B7C6",
        "palette": ["#DCECF7", "#DDF0EA", "#FFF0CB", "#F6E0E8", "#E7F3D7", "#EEE7F4"],
        "accent": "#5AB7C9",
        "accent_2": "#F3C64E",
        "accent_3": "#E96C72",
        "stage_dash": "7 6",
    },
    "research-ppt-blue": {
        "background": "#F8FAFC",
        "text": "#0F172A",
        "muted": "#64748B",
        "line": "#64748B",
        "stage_fill": "#FFFFFF",
        "stage_stroke": "#E2E8F0",
        "header_fill": "#2563EB",
        "header_text": "#FFFFFF",
        "node_fill": "#FFFFFF",
        "node_stroke": "#CBD5E1",
        "main_fill": "#DBEAFE",
        "main_stroke": "#2563EB",
        "main_text": "#1E3A8A",
        "output_fill": "#E0F2FE",
        "output_stroke": "#2563EB",
        "palette": ["#EFF6FF", "#F0FDF4", "#FEFCE8", "#FFF7ED", "#FDF2F8", "#EEF2FF"],
        "accent": "#2563EB",
        "accent_2": "#1D4ED8",
        "accent_3": "#64748B",
        "canvas_stroke": "#CBD5E1",
        "soft_shadow": "#E2E8F0",
    },
}

STYLE_DEFAULTS = {
    "accent": "#2563EB",
    "accent_2": "#0F766E",
    "accent_3": "#F59E0B",
    "stage_dash": "",
    "canvas_stroke": "#D8E1EA",
    "soft_shadow": "#E7ECF2",
}

STYLE_ALIASES = {
    "presentation-clean": "defense-color",
    "nature-style-editorial": "nature-editorial",
    "high-contrast-accessible": "accessible-high-contrast",
    "premium-scientific": "premium-scientific",
    "advertising-clean-campaign": "advertising-clean-campaign",
    "cn-thesis-pastel": "cn-polished-pastel-academic",
    "cn-grant-pastel": "cn-soft-grant-report",
    "cn-linework": "cn-reviewer-linework",
    "formal-research-ppt": "research-ppt-blue",
}


def load_route(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_text(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def slug(value, fallback):
    value = str(value or "")
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip()).strip("_").lower()
    return value or fallback


def wrap_text(value, width=18, max_lines=3):
    text = str(value or "").strip()
    if not text:
        return [""]
    parts = []
    current = ""
    for token in re.split(r"(\s+)", text):
        if not token:
            continue
        if token.isspace():
            if current and len(current) < width:
                current += " "
            continue
        if len(token) > width:
            if current:
                parts.append(current.rstrip())
                current = ""
            for i in range(0, len(token), width):
                parts.append(token[i : i + width])
            continue
        if len(current) + len(token) > width and current:
            parts.append(current.rstrip())
            current = token
        else:
            current += token
    if current:
        parts.append(current.rstrip())
    if len(parts) > max_lines:
        parts = parts[: max_lines - 1] + [parts[max_lines - 1][: max(1, width - 1)] + "..."]
    return parts or [text]


def normalize_route(route):
    data = copy.deepcopy(route)
    data["title"] = str(data.get("title") or "Project Technical Route")
    data["subtitle"] = str(data.get("subtitle") or "")
    data["layout"] = data.get("layout") or "horizontal-stages"
    data["style"] = data.get("style") or data.get("theme") or "academic-blue"
    if data["layout"] not in SUPPORTED_LAYOUTS:
        supported = ", ".join(sorted(SUPPORTED_LAYOUTS))
        raise ValueError(f"Unsupported layout '{data['layout']}'. Supported layouts: {supported}")
    canonical_style = STYLE_ALIASES.get(data["style"], data["style"])
    if canonical_style not in STYLES:
        supported = ", ".join(sorted(set(STYLES) | set(STYLE_ALIASES)))
        raise ValueError(f"Unsupported style '{data['style']}'. Supported styles: {supported}")
    data["metadata"] = data.get("metadata") or {}
    stages = []
    node_ids = set()
    for si, stage in enumerate(data.get("stages") or []):
        sid = slug(stage.get("id") or stage.get("title") or stage.get("name"), f"stage_{si + 1}")
        title = str(stage.get("title") or stage.get("label") or stage.get("name") or f"Stage {si + 1}")
        nodes = []
        for ni, node in enumerate(stage.get("nodes") or []):
            if isinstance(node, str):
                node = {"label": node}
            nid = slug(node.get("id") or node.get("label"), f"{sid}_node_{ni + 1}")
            base = nid
            offset = 2
            while nid in node_ids:
                nid = f"{base}_{offset}"
                offset += 1
            node_ids.add(nid)
            normalized_node = copy.deepcopy(node)
            normalized_node.update(
                {
                    "id": nid,
                    "label": str(node.get("label") or node.get("title") or f"Node {ni + 1}"),
                    "detail": str(node.get("detail") or node.get("summary") or ""),
                    "tag": str(node.get("tag") or stage.get("tag") or "step"),
                    "evidence": node.get("evidence") if isinstance(node.get("evidence"), list) else [],
                    "confidence": node.get("confidence") or "medium",
                    "is_inferred": bool(node.get("is_inferred", False)),
                }
            )
            nodes.append(normalized_node)
        stages.append(
            {
                "id": sid,
                "title": title,
                "summary": str(stage.get("summary") or ""),
                "nodes": nodes,
            }
        )
    data["stages"] = stages
    valid_ids = {node["id"] for stage in stages for node in stage["nodes"]}
    edges = []
    for ei, edge in enumerate(data.get("edges") or []):
        if not isinstance(edge, dict):
            continue
        source = slug(edge.get("from") or edge.get("source"), f"missing_from_{ei}")
        target = slug(edge.get("to") or edge.get("target"), f"missing_to_{ei}")
        normalized_edge = copy.deepcopy(edge)
        normalized_edge.update(
            {
                "id": slug(edge.get("id"), f"edge_{ei + 1}"),
                "from": source,
                "to": target,
                "label": str(edge.get("label") or edge.get("title") or "next"),
                "kind": str(edge.get("kind") or "flow"),
                "confidence": edge.get("confidence") or "medium",
                "evidence": edge.get("evidence") if isinstance(edge.get("evidence"), list) else [],
                "valid": source in valid_ids and target in valid_ids,
            }
        )
        edges.append(normalized_edge)
    if not edges:
        last = None
        count = 1
        for stage in stages:
            for node in stage["nodes"]:
                if last:
                    edges.append({"id": f"edge_{count}", "from": last, "to": node["id"], "label": "next", "kind": "flow", "valid": True})
                    count += 1
                last = node["id"]
    data["edges"] = edges
    return data


def get_style(route):
    requested = route.get("style") or "academic-blue"
    name = STYLE_ALIASES.get(requested, requested)
    if name not in STYLES:
        supported = ", ".join(sorted(set(STYLES) | set(STYLE_ALIASES)))
        raise ValueError(f"Unsupported style '{requested}'. Supported styles: {supported}")
    style = copy.deepcopy(STYLES[name])
    for key, value in STYLE_DEFAULTS.items():
        style.setdefault(key, value)
    style["name"] = requested
    return style


def flatten_nodes(route):
    return [node for stage in route["stages"] for node in stage["nodes"]]


def build_layout(route):
    route = normalize_route(route)
    layout_name = route.get("layout", "horizontal-stages")
    if layout_name not in SUPPORTED_LAYOUTS:
        supported = ", ".join(sorted(SUPPORTED_LAYOUTS))
        raise ValueError(f"Unsupported layout '{layout_name}'. Supported layouts: {supported}")
    stages = route["stages"]
    margin = 64
    title_h = 102
    node_h = 62
    header_h = 42
    gap = 38
    node_gap = 16
    nodes = {}
    stage_boxes = []

    matrix_layouts = {
        "academic-method-framework",
        "proposal-matrix-route",
        "cn-research-method-matrix",
        "cn-paper-framework-canvas",
    }
    system_layouts = {
        "software-system-route",
        "engineering-architecture-route",
        "engineering-architecture",
        "cn-wide-project-map",
    }
    campaign_layouts = {"campaign-strategy-map"}
    mainline_layouts = {"cn-ppt-mainline-route", "ppt-mainline-route", "research-ppt-mainline"}
    a4_stage_layouts = {"cn-a4-stage-route", "a4-stage-route"}

    if layout_name in mainline_layouts:
        width = 1920
        height = 1080
        margin_x = 70
        stage_gap = 22
        stage_y = 160
        stage_h = 600
        main_h = 88
        support_h = 82
        support_gap = 34
        stage_w = (width - margin_x * 2 - max(0, len(stages) - 1) * stage_gap) / max(1, len(stages))
        for si, stage in enumerate(stages):
            x = margin_x + si * (stage_w + stage_gap)
            main_box = {
                "x": x + 14,
                "y": stage_y + 24,
                "w": stage_w - 28,
                "h": main_h,
            }
            stage_boxes.append(
                {
                    "id": stage["id"],
                    "title": stage["title"],
                    "x": x,
                    "y": stage_y,
                    "w": stage_w,
                    "h": stage_h,
                    "index": si,
                    "layout": "mainline",
                    "main_box": main_box,
                }
            )
            visible_nodes = stage["nodes"]
            cols = 1 if len(visible_nodes) <= 3 else 2
            support_gap_x = 12
            support_gap_y = 24
            support_w = (stage_w - 44 - (cols - 1) * support_gap_x) / cols
            for ni, node in enumerate(visible_nodes):
                row = ni // cols
                col = ni % cols
                ny = main_box["y"] + main_h + 52 + row * (support_h + support_gap_y)
                nodes[node["id"]] = {
                    "x": x + 22 + col * (support_w + support_gap_x),
                    "y": ny,
                    "w": support_w,
                    "h": support_h,
                    "stage": stage["id"],
                    "role": "support",
                }
        final_output = route.get("final_output") or route["metadata"].get("final_output", "")
        return {
            "width": int(width),
            "height": int(height),
            "layout_name": layout_name,
            "orientation": "mainline",
            "stages": stage_boxes,
            "nodes": nodes,
            "route": route,
            "output_bar": {
                "x": margin_x,
                "y": 805,
                "w": width - margin_x * 2,
                "h": 108,
                "text": final_output,
            },
        }

    if layout_name in a4_stage_layouts:
        width = 1240
        margin_x = 78
        stage_w = width - margin_x * 2
        y = 180
        row_gap = 48
        header_h = 56
        node_h = 86
        node_gap = 18
        for si, stage in enumerate(stages):
            count = max(1, len(stage["nodes"]))
            cols = 1 if count == 1 else min(3, count)
            rows = int(math.ceil(count / cols))
            node_w = (stage_w - 72 - (cols - 1) * node_gap) / cols
            stage_h = header_h + 58 + rows * node_h + max(0, rows - 1) * node_gap + 38
            stage_boxes.append(
                {
                    "id": stage["id"],
                    "title": stage["title"],
                    "x": margin_x,
                    "y": y,
                    "w": stage_w,
                    "h": stage_h,
                    "index": si,
                    "layout": "a4stage",
                }
            )
            for ni, node in enumerate(stage["nodes"]):
                row = ni // cols
                col = ni % cols
                nx = margin_x + 36 + col * (node_w + node_gap)
                ny = y + header_h + 58 + row * (node_h + node_gap)
                nodes[node["id"]] = {"x": nx, "y": ny, "w": node_w, "h": node_h, "stage": stage["id"], "role": "support"}
            y += stage_h + row_gap
        final_output = route.get("final_output") or route["metadata"].get("final_output", "")
        output_h = 96
        height = max(1754, int(y + (output_h + 90 if final_output else 80)))
        return {
            "width": int(width),
            "height": int(height),
            "layout_name": layout_name,
            "orientation": "a4stage",
            "stages": stage_boxes,
            "nodes": nodes,
            "route": route,
            "output_bar": {
                "x": margin_x,
                "y": y + 10,
                "w": stage_w,
                "h": output_h,
                "text": final_output,
            },
        }

    if layout_name in matrix_layouts:
        if layout_name.startswith("cn-"):
            width = 1380
            content_x = 250
            content_w = 1046
            label_x = 58
            label_w = 148
            y = title_h + 58
            row_gap = 30
            node_h = 64
            node_gap = 18
        else:
            width = 1280
            content_x = 228
            content_w = 980
            label_x = 62
            label_w = 128
            y = title_h + 44
            row_gap = 24
            node_h = 60
            node_gap = 16
        for si, stage in enumerate(stages):
            count = max(1, len(stage["nodes"]))
            cols = 1 if count == 1 else min(3, count)
            rows = int(math.ceil(count / cols))
            node_w = (content_w - 72 - (cols - 1) * node_gap) / cols
            row_h = max(126 if layout_name.startswith("cn-") else 112, 34 + rows * node_h + max(0, rows - 1) * node_gap + 38)
            label_box = {
                "x": label_x,
                "y": y + row_h / 2 - 28,
                "w": label_w,
                "h": 56,
            }
            stage_boxes.append(
                {
                    "id": stage["id"],
                    "title": stage["title"],
                    "x": content_x,
                    "y": y,
                    "w": content_w,
                    "h": row_h,
                    "index": si,
                    "layout": "matrix",
                    "label_box": label_box,
                }
            )
            for ni, node in enumerate(stage["nodes"]):
                row = ni // cols
                col = ni % cols
                if count == 1:
                    node_w_single = min(760, content_w - 110)
                    nx = content_x + (content_w - node_w_single) / 2
                    nw = node_w_single
                else:
                    nx = content_x + 36 + col * (node_w + node_gap)
                    nw = node_w
                ny = y + 32 + row * (node_h + node_gap)
                nodes[node["id"]] = {"x": nx, "y": ny, "w": nw, "h": node_h, "stage": stage["id"]}
            y += row_h + row_gap
        height = y + 40
        return {
            "width": int(width),
            "height": int(height),
            "layout_name": layout_name,
            "orientation": "matrix",
            "stages": stage_boxes,
            "nodes": nodes,
            "route": route,
        }

    if layout_name in system_layouts:
        if layout_name == "cn-wide-project-map":
            width = 1500
            content_x = 270
            content_w = 1120
            label_x = 58
            label_w = 168
            y = title_h + 54
            row_gap = 22
            node_h = 60
            node_gap = 18
        else:
            width = 1320
            content_x = 238
            content_w = 1008
            label_x = 58
            label_w = 146
            y = title_h + 48
            row_gap = 18
            node_h = 58
            node_gap = 18
        for si, stage in enumerate(stages):
            count = max(1, len(stage["nodes"]))
            cols = min(4, count)
            rows = int(math.ceil(count / cols))
            node_w = (content_w - 70 - (cols - 1) * node_gap) / cols
            row_h = max(104, 28 + rows * node_h + max(0, rows - 1) * node_gap + 28)
            label_box = {
                "x": label_x,
                "y": y,
                "w": label_w,
                "h": row_h,
            }
            stage_boxes.append(
                {
                    "id": stage["id"],
                    "title": stage["title"],
                    "x": content_x,
                    "y": y,
                    "w": content_w,
                    "h": row_h,
                    "index": si,
                    "layout": "system",
                    "label_box": label_box,
                }
            )
            for ni, node in enumerate(stage["nodes"]):
                row = ni // cols
                col = ni % cols
                nx = content_x + 35 + col * (node_w + node_gap)
                ny = y + 28 + row * (node_h + node_gap)
                nodes[node["id"]] = {"x": nx, "y": ny, "w": node_w, "h": node_h, "stage": stage["id"]}
            y += row_h + row_gap
        height = y + 44
        return {
            "width": int(width),
            "height": int(height),
            "layout_name": layout_name,
            "orientation": "system",
            "stages": stage_boxes,
            "nodes": nodes,
            "route": route,
        }

    if layout_name in campaign_layouts:
        width = 1360
        height = 690
        margin = 60
        top = title_h + 74
        gap = 22
        stage_w = (width - margin * 2 - max(0, len(stages) - 1) * gap) / max(1, len(stages))
        stage_h = 390
        for si, stage in enumerate(stages):
            x = margin + si * (stage_w + gap)
            stage_boxes.append(
                {
                    "id": stage["id"],
                    "title": stage["title"],
                    "x": x,
                    "y": top,
                    "w": stage_w,
                    "h": stage_h,
                    "index": si,
                    "layout": "campaign",
                }
            )
            node_w = stage_w - 34
            for ni, node in enumerate(stage["nodes"]):
                nx = x + 17
                ny = top + 68 + ni * (node_h + node_gap)
                nodes[node["id"]] = {"x": nx, "y": ny, "w": node_w, "h": node_h, "stage": stage["id"]}
        return {
            "width": int(width),
            "height": int(height),
            "layout_name": layout_name,
            "orientation": "campaign",
            "stages": stage_boxes,
            "nodes": nodes,
            "route": route,
        }

    vertical = layout_name in {
        "vertical-research-route",
        "proposal-phase-axis",
        "cn-proposal-poster-route",
        "cn-grant-application-route",
        "cn-monochrome-linework-route",
    }
    if vertical:
        if layout_name.startswith("cn-"):
            width = 1060
            axis_x = 96
            stage_x = 194
            stage_w = 790
            y = title_h + 62
            gap = 42
            node_h = 64
            node_gap = 18
            header_h = 52
        else:
            width = 1120
            axis_x = 102
            stage_x = 202
            stage_w = 842
            y = title_h + 36
        for si, stage in enumerate(stages):
            count = max(1, len(stage["nodes"]))
            cols = 1 if count == 1 else min(3, count)
            rows = int(math.ceil(max(1, len(stage["nodes"])) / cols))
            node_w = (stage_w - 70 - (cols - 1) * node_gap) / cols
            sh = header_h + rows * node_h + max(0, rows - 1) * node_gap + (54 if layout_name.startswith("cn-") else 42)
            stage_boxes.append(
                {
                    "id": stage["id"],
                    "title": stage["title"],
                    "x": stage_x,
                    "y": y,
                    "w": stage_w,
                    "h": sh,
                    "index": si,
                    "axis_x": axis_x,
                    "layout": "vertical",
                }
            )
            for ni, node in enumerate(stage["nodes"]):
                row = ni // cols
                col = ni % cols
                nx = stage_x + 35 + col * (node_w + node_gap)
                ny = y + header_h + 18 + row * (node_h + node_gap)
                nodes[node["id"]] = {"x": nx, "y": ny, "w": node_w, "h": node_h, "stage": stage["id"]}
            y += sh + gap
        height = y + 48
    else:
        max_nodes = max([len(s["nodes"]) for s in stages] + [1])
        if layout_name in {"campaign-funnel", "creative-production-pipeline"}:
            width = 1320
            height = 620
            gap = 28
        elif layout_name in {"engineering-architecture", "layered-architecture", "timeline-swimlane", "wide-collaboration-map"}:
            width = 1340
            height = 580
            gap = 30
        else:
            width = max(1180, min(1520, margin * 2 + len(stages) * 214 + max(0, len(stages) - 1) * gap))
            height = 610
        required_stage_h = header_h + 18 + max_nodes * node_h + max(0, max_nodes - 1) * node_gap + 24
        height = max(height, title_h + margin + required_stage_h + margin)
        stage_w = (width - margin * 2 - max(0, len(stages) - 1) * gap) / max(1, len(stages))
        stage_w = max(150, stage_w)
        stage_h = required_stage_h
        for si, stage in enumerate(stages):
            x = margin + si * (stage_w + gap)
            y = title_h + margin
            stage_boxes.append(
                {
                    "id": stage["id"],
                    "title": stage["title"],
                    "x": x,
                    "y": y,
                    "w": stage_w,
                    "h": stage_h,
                    "index": si,
                    "layout": "horizontal",
                }
            )
            node_w = max(116, stage_w - 42)
            for ni, node in enumerate(stage["nodes"]):
                nx = x + (stage_w - node_w) / 2
                ny = y + header_h + 18 + ni * (node_h + node_gap)
                nodes[node["id"]] = {"x": nx, "y": ny, "w": node_w, "h": node_h, "stage": stage["id"]}
    return {
        "width": int(width),
        "height": int(height),
        "layout_name": layout_name,
        "orientation": "vertical" if vertical else "horizontal",
        "stages": stage_boxes,
        "nodes": nodes,
        "route": route,
    }


def center(box):
    return (box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)


def node_port(box, side):
    if side == "left":
        return box["x"], box["y"] + box["h"] / 2
    if side == "right":
        return box["x"] + box["w"], box["y"] + box["h"] / 2
    if side == "top":
        return box["x"] + box["w"] / 2, box["y"]
    return box["x"] + box["w"] / 2, box["y"] + box["h"]


def _compact_points(points):
    compacted = []
    for x, y in points:
        if not compacted or abs(compacted[-1][0] - x) > 0.5 or abs(compacted[-1][1] - y) > 0.5:
            compacted.append((x, y))
    return compacted


def _horizontal_edge_points(source, target):
    sx, sy = center(source)
    tx, ty = center(target)
    if tx >= sx:
        x1, y1 = node_port(source, "right")
        x2, y2 = node_port(target, "left")
        if abs(y1 - y2) < 4:
            return [(x1, y1), (x2, y2)]
        mid_x = (x1 + x2) / 2
        return [(x1, y1), (mid_x, y1), (mid_x, y2), (x2, y2)]
    x1, y1 = node_port(source, "left")
    x2, y2 = node_port(target, "right")
    lane_y = max(28, min(source["y"], target["y"]) - 42)
    return [(x1, y1), (x1, lane_y), (x2, lane_y), (x2, y2)]


def _vertical_edge_points(source, target):
    sx, sy = center(source)
    tx, ty = center(target)
    if ty >= sy:
        x1, y1 = node_port(source, "bottom")
        x2, y2 = node_port(target, "top")
        if abs(x1 - x2) < 4:
            return [(x1, y1), (x2, y2)]
        mid_y = (y1 + y2) / 2
        return [(x1, y1), (x1, mid_y), (x2, mid_y), (x2, y2)]
    x1, y1 = node_port(source, "top")
    x2, y2 = node_port(target, "top")
    lane_y = max(28, min(source["y"], target["y"]) - 46)
    return [(x1, y1), (x1, lane_y), (x2, lane_y), (x2, y2)]


def edge_points(source, target, orientation):
    sx, sy = center(source)
    tx, ty = center(target)
    same_band = abs(sy - ty) < 38
    same_stage = source.get("stage") == target.get("stage")
    if same_band:
        points = _horizontal_edge_points(source, target)
    elif orientation in {"vertical", "matrix", "system"} or same_stage:
        points = _vertical_edge_points(source, target)
    else:
        points = _horizontal_edge_points(source, target)
    return _compact_points(points)


def edge_is_feedback(edge, source, target):
    return (
        edge.get("kind") == "feedback"
        or target["x"] + target["w"] / 2 < source["x"] + source["w"] / 2
        or target["y"] + target["h"] / 2 < source["y"] + source["h"] / 2
    )


def show_edge_labels(route):
    overrides = route.get("renderer_overrides") or {}
    metadata = route.get("metadata") or {}
    return bool(overrides.get("show_edge_labels") or metadata.get("show_edge_labels"))


def show_node_edges(route):
    overrides = route.get("renderer_overrides") or {}
    metadata = route.get("metadata") or {}
    return bool(overrides.get("show_node_edges") or metadata.get("show_node_edges"))


def stage_flow_segments(layout):
    stages = layout.get("stages") or []
    orientation = layout.get("orientation", "horizontal")
    segments = []
    for source, target in zip(stages, stages[1:]):
        if orientation == "mainline":
            source_box = source.get("main_box") or source
            target_box = target.get("main_box") or target
            x1 = source_box["x"] + source_box["w"]
            y1 = source_box["y"] + source_box["h"] / 2
            x2 = target_box["x"]
            y2 = target_box["y"] + target_box["h"] / 2
        elif orientation in {"horizontal", "campaign"}:
            x1 = source["x"] + source["w"]
            y1 = source["y"] + source["h"] / 2
            x2 = target["x"]
            y2 = target["y"] + target["h"] / 2
        else:
            x1 = source["x"] + source["w"] / 2
            y1 = source["y"] + source["h"]
            x2 = target["x"] + target["w"] / 2
            y2 = target["y"]
        segments.append((x1, y1, x2, y2))
    return segments


def html_escape(value):
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
