import sys

from route_common import (
    build_layout,
    edge_is_feedback,
    edge_points,
    get_style,
    html_escape,
    load_route,
    save_text,
    show_edge_labels,
    show_node_edges,
    stage_flow_segments,
    wrap_text,
)


FONT = "Arial, Helvetica, sans-serif"


def svg_text(x, y, text, size, fill, anchor="middle", weight="400", extra=""):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-size="{size}" font-family="{FONT}" font-weight="{weight}" fill="{fill}" {extra}>'
        f"{html_escape(text)}</text>"
    )


def rect(x, y, w, h, rx, fill, stroke="none", stroke_width=1.5, dash="", extra=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr} {extra}/>'
    )


def stage_palette(style, index):
    palette = style.get("palette") or [style["stage_fill"]]
    return palette[index % len(palette)]


def has_cjk(text):
    return any("\u3400" <= char <= "\u9fff" for char in str(text or ""))


def text_capacity(text, width, size):
    divisor = size * (1.02 if has_cjk(text) else 0.58)
    return max(5, int(width / max(divisor, 1)))


def draw_wrapped_text(out, text, x, y, width_chars, max_lines, size, fill, weight="400"):
    lines = wrap_text(text, width_chars, max_lines)
    start_y = y - (len(lines) - 1) * (size * 0.58)
    for i, line in enumerate(lines):
        out.append(svg_text(x, start_y + i * (size + 3), line, size, fill, weight=weight))


def draw_title(out, route, layout, style):
    width = layout["width"]
    title = route["title"]
    if layout["orientation"] == "mainline":
        title_size = 32
    elif layout["orientation"] == "a4stage":
        title_size = 27 if has_cjk(title) else 28
    else:
        title_size = 23 if has_cjk(title) else 24
    title_chars = text_capacity(title, width - 190, title_size)
    title_lines = wrap_text(title, title_chars, 2)
    pill_h = 54 + (len(title_lines) - 1) * 28
    pill_y = 18
    if layout["orientation"] == "mainline":
        draw_wrapped_text(out, title, width / 2, 56, title_chars, 2, title_size, style["text"], "700")
    elif layout["orientation"] in {"vertical", "matrix", "a4stage"}:
        title_unit = 18 if has_cjk(title) else 13
        pill_w = min(width - 160, max(460, min(len(title), title_chars) * title_unit + 110))
        out.append(rect((width - pill_w) / 2, pill_y, pill_w, pill_h, 28, "#FFFFFF", stage_palette(style, 1), 2.2, "", 'filter="url(#softShadow)"'))
        draw_wrapped_text(out, title, width / 2, pill_y + pill_h / 2 + 7, title_chars, 2, title_size, style["text"], "700")
    else:
        out.append(rect(64, pill_y + 4, width - 128, pill_h, 18, stage_palette(style, 0), "none"))
        draw_wrapped_text(out, title, width / 2, pill_y + pill_h / 2 + 10, title_chars, 2, title_size, style["text"], "700")
    if route.get("subtitle"):
        subtitle = route["subtitle"]
        subtitle_size = 14 if layout["orientation"] in {"mainline", "a4stage"} else 12
        subtitle_chars = text_capacity(subtitle, width - 190, subtitle_size)
        subtitle_y = 102 if layout["orientation"] == "mainline" else pill_y + pill_h + 27
        draw_wrapped_text(out, subtitle, width / 2, subtitle_y, subtitle_chars, 1, subtitle_size, style["muted"])
    show_reader_path = (route.get("metadata") or {}).get("show_reader_path", False)
    reader_path = route.get("reader_path") or []
    if reader_path and show_reader_path:
        visible = reader_path[:7]
        chip_gap = 10
        chip_w = min(128, max(82, (width - 160 - chip_gap * (len(visible) - 1)) / max(1, len(visible))))
        total_w = len(visible) * chip_w + max(0, len(visible) - 1) * chip_gap
        x = (width - total_w) / 2
        y = 108
        for i, item in enumerate(visible):
            out.append(rect(x + i * (chip_w + chip_gap), y, chip_w, 26, 13, "#FFFFFF", stage_palette(style, i + 1), 1.0))
            draw_wrapped_text(out, item, x + i * (chip_w + chip_gap) + chip_w / 2, y + 17, 15, 1, 10, style["muted"], "600")


def draw_vertical_axis(out, layout, style):
    stages = layout["stages"]
    if not stages:
        return
    axis_x = stages[0].get("axis_x", 100)
    y1 = stages[0]["y"] + 12
    y2 = stages[-1]["y"] + stages[-1]["h"] - 12
    out.append(f'<line x1="{axis_x:.1f}" y1="{y1:.1f}" x2="{axis_x:.1f}" y2="{y2:.1f}" stroke="{style["accent"]}" stroke-width="3" opacity="0.82"/>')
    for stage in stages:
        cy = stage["y"] + stage["h"] / 2
        color = stage_palette(style, stage["index"])
        out.append(f'<circle cx="{axis_x:.1f}" cy="{cy:.1f}" r="7" fill="{style["accent"]}"/>')
        out.append(rect(axis_x - 56, cy - 34, 72, 68, 12, color, "none"))
        draw_wrapped_text(out, stage["title"], axis_x - 20, cy + 4, 4, 3, 15, style["text"], "700")


def draw_stage_regions(out, layout, style):
    for stage in layout["stages"]:
        fill = stage_palette(style, stage["index"])
        dash = style.get("stage_dash", "")
        if stage.get("layout") == "mainline":
            out.append(rect(stage["x"], stage["y"], stage["w"], stage["h"], 16, fill, style["stage_stroke"], 1.0, "", 'opacity="0.72"'))
            main = stage["main_box"]
            out.append(rect(main["x"], main["y"], main["w"], main["h"], 12, style.get("main_fill", "#DBEAFE"), style.get("main_stroke", style["header_fill"]), 1.8))
            draw_wrapped_text(out, stage["title"], main["x"] + main["w"] / 2, main["y"] + main["h"] / 2 + 7, text_capacity(stage["title"], main["w"] - 28, 19), 2, 19, style.get("main_text", style["text"]), "700")
        elif stage.get("layout") == "a4stage":
            out.append(rect(stage["x"], stage["y"], stage["w"], stage["h"], 14, fill, style["stage_stroke"], 1.1, "", 'opacity="0.78"'))
            label = f"{stage['index'] + 1:02d}  {stage['title']}"
            label_w = min(stage["w"] - 96, max(340, len(label) * 20))
            label_x = stage["x"] + (stage["w"] - label_w) / 2
            out.append(rect(label_x, stage["y"] + 20, label_w, 48, 10, style["header_fill"], style["header_fill"], 1.0))
            draw_wrapped_text(out, label, label_x + label_w / 2, stage["y"] + 52, text_capacity(label, label_w - 24, 18), 1, 18, style["header_text"], "700")
        elif stage.get("layout") == "matrix":
            out.append(rect(stage["x"], stage["y"], stage["w"], stage["h"], 18, fill, style["stage_stroke"], 1.4, dash, 'opacity="0.70"'))
            label = stage.get("label_box") or {"x": stage["x"], "y": stage["y"], "w": 140, "h": 42}
            out.append(rect(label["x"], label["y"], label["w"], label["h"], 12, style["header_fill"], style["header_fill"], 1.0, "", 'filter="url(#softShadow)"'))
            draw_wrapped_text(out, stage["title"], label["x"] + label["w"] / 2, label["y"] + label["h"] / 2 + 4, text_capacity(stage["title"], label["w"] - 18, 14), 2, 14, style["header_text"], "700")
        elif stage.get("layout") == "system":
            out.append(rect(stage["x"], stage["y"], stage["w"], stage["h"], 6, fill, style["stage_stroke"], 1.4, dash, 'opacity="0.78"'))
            label = stage.get("label_box") or {"x": stage["x"], "y": stage["y"], "w": 140, "h": stage["h"]}
            out.append(rect(label["x"], label["y"], label["w"], label["h"], 6, style["header_fill"], style["header_fill"], 1.0))
            draw_wrapped_text(out, stage["title"], label["x"] + label["w"] / 2, label["y"] + label["h"] / 2 + 4, text_capacity(stage["title"], label["w"] - 18, 14), 3, 14, style["header_text"], "700")
        elif stage.get("layout") == "campaign":
            out.append(rect(stage["x"], stage["y"], stage["w"], stage["h"], 12, fill, style["stage_stroke"], 1.3, dash, 'opacity="0.88"'))
            out.append(rect(stage["x"], stage["y"], stage["w"], 48, 12, style["header_fill"], style["header_fill"], 1.0))
            draw_wrapped_text(out, stage["title"], stage["x"] + stage["w"] / 2, stage["y"] + 31, text_capacity(stage["title"], stage["w"] - 20, 13), 2, 13, style["header_text"], "700")
        elif layout["orientation"] == "vertical":
            out.append(rect(stage["x"], stage["y"], stage["w"], stage["h"], 22, fill, style["stage_stroke"], 1.6, dash, 'opacity="0.92"'))
            title_w = min(310, max(170, len(stage["title"]) * 16))
            out.append(rect(stage["x"] + 28, stage["y"] - 17, title_w, 34, 10, style["header_fill"], style["header_fill"], 1.0, "", 'filter="url(#softShadow)"'))
            draw_wrapped_text(out, stage["title"], stage["x"] + 28 + title_w / 2, stage["y"] + 6, text_capacity(stage["title"], title_w - 20, 14), 1, 14, style["header_text"], "700")
        else:
            out.append(rect(stage["x"], stage["y"], stage["w"], stage["h"], 14, style["stage_fill"], style["stage_stroke"], 1.3, dash))
            out.append(rect(stage["x"], stage["y"], stage["w"], 42, 12, style["header_fill"], style["header_fill"], 1.0))
            draw_wrapped_text(out, stage["title"], stage["x"] + stage["w"] / 2, stage["y"] + 27, text_capacity(stage["title"], stage["w"] - 20, 13), 2, 13, style["header_text"], "700")


def draw_stage_flow_edges(out, layout, style):
    for x1, y1, x2, y2 in stage_flow_segments(layout):
        out.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{style["line"]}" stroke-width="2.2" marker-end="url(#arrow)" opacity="0.66"/>'
        )


def draw_edges(out, route, layout, style):
    if not show_node_edges(route):
        draw_stage_flow_edges(out, layout, style)
        return
    nodes = layout["nodes"]
    labels_visible = show_edge_labels(route)
    for edge in route["edges"]:
        if not edge.get("valid", True) or edge["from"] not in nodes or edge["to"] not in nodes:
            continue
        a = nodes[edge["from"]]
        b = nodes[edge["to"]]
        points = edge_points(a, b, layout["orientation"])
        if len(points) < 2:
            continue
        commands = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
        commands.extend(f"L {x:.1f} {y:.1f}" for x, y in points[1:])
        path = " ".join(commands)
        dash = ' stroke-dasharray="6 5"' if edge_is_feedback(edge, a, b) else ""
        out.append(f'<path d="{path}" fill="none" stroke="{style["line"]}" stroke-width="2.1" marker-end="url(#arrow)" opacity="0.72"{dash}/>')
        if labels_visible and edge.get("label"):
            segment_index = max(0, len(points) // 2 - 1)
            x1, y1 = points[segment_index]
            x2, y2 = points[segment_index + 1]
            label_x = (x1 + x2) / 2
            label_y = (y1 + y2) / 2 - 8
            out.append(rect(label_x - 31, label_y - 13, 62, 19, 9, "#FFFFFF", style["soft_shadow"], 0.8))
            draw_wrapped_text(out, edge["label"], label_x, label_y + 1, 12, 1, 9, style["muted"], "600")


def draw_nodes(out, route, layout, style):
    nodes = layout["nodes"]
    for stage in route["stages"]:
        for node in stage["nodes"]:
            if node["id"] not in nodes:
                continue
            box = nodes[node["id"]]
            out.append(f'<g class="node" data-node="{html_escape(node["id"])}" style="cursor:pointer">')
            shadow = "" if layout["orientation"] in {"mainline", "a4stage"} else 'filter="url(#softShadow)"'
            out.append(rect(box["x"], box["y"], box["w"], box["h"], 10, style["node_fill"], style["node_stroke"], 1.25, "", shadow))
            tag = str(node.get("tag") or "")
            if tag and layout["orientation"] not in {"mainline", "a4stage"}:
                out.append(f'<circle cx="{box["x"] + 14:.1f}" cy="{box["y"] + 14:.1f}" r="4.2" fill="{style["accent_2"]}" opacity="0.86"/>')
            node_size = 17 if layout["orientation"] == "mainline" else 16 if layout["orientation"] == "a4stage" else 12
            width_chars = text_capacity(node["label"], box["w"] - 28, node_size)
            draw_wrapped_text(out, node["label"], box["x"] + box["w"] / 2, box["y"] + box["h"] / 2 + 5, width_chars, 2, node_size, style["text"], "600")
            out.append("</g>")


def draw_output_bar(out, layout, style):
    bar = layout.get("output_bar")
    if not bar or not bar.get("text"):
        return
    out.append(rect(bar["x"], bar["y"], bar["w"], bar["h"], 16, style.get("output_fill", "#E0F2FE"), style.get("output_stroke", style["header_fill"]), 1.6))
    label = "成果输出：" + str(bar["text"])
    draw_wrapped_text(out, label, bar["x"] + bar["w"] / 2, bar["y"] + bar["h"] / 2 + 6, text_capacity(label, bar["w"] - 80, 18), 2, 18, style["text"], "700")


def make_svg(route):
    layout = build_layout(route)
    route = layout["route"]
    style = get_style(route)
    width = layout["width"]
    height = layout["height"]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{style["line"]}"/></marker>',
        '<filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#CBD5E1" flood-opacity="0.32"/></filter>',
        "</defs>",
        f'<rect width="100%" height="100%" fill="{style["background"]}"/>',
        rect(10, 10, width - 20, height - 20, 18, "none", style.get("canvas_stroke", "#D8E1EA"), 1.0),
    ]
    draw_title(out, route, layout, style)
    if layout["orientation"] == "vertical":
        draw_vertical_axis(out, layout, style)
    draw_stage_regions(out, layout, style)
    draw_edges(out, route, layout, style)
    draw_nodes(out, route, layout, style)
    draw_output_bar(out, layout, style)
    out.append("</svg>")
    return "\n".join(out)


def main():
    if len(sys.argv) != 3:
        print("Usage: python render_svg.py <tech-route.json> <output.svg>")
        return 2
    save_text(sys.argv[2], make_svg(load_route(sys.argv[1])))
    print(f"Wrote {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
