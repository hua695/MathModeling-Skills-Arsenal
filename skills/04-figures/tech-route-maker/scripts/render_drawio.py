import sys

from route_common import (
    build_layout,
    get_style,
    html_escape,
    load_route,
    save_text,
    show_edge_labels,
    show_node_edges,
    stage_flow_segments,
)


def palette_item(style, index):
    palette = style.get("palette") or [style["stage_fill"]]
    return palette[index % len(palette)]


def make_drawio(route):
    layout = build_layout(route)
    route = layout["route"]
    style = get_style(route)
    nodes = layout["nodes"]
    page_w = max(1200, int(layout["width"] + 80))
    page_h = max(800, int(layout["height"] + 80))
    dashed = "dashed=1;dashPattern=8 6;" if style.get("stage_dash") else ""
    title_font = 30 if layout["orientation"] == "mainline" else 28 if layout["orientation"] == "a4stage" else 24
    node_font = 16 if layout["orientation"] == "mainline" else 15 if layout["orientation"] == "a4stage" else 12
    parts = [
        '<mxfile host="app.diagrams.net" modified="2026-06-19T00:00:00.000Z" agent="tech-route-maker" version="24.7.8">',
        '<diagram id="tech-route" name="Tech Route">',
        f'<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{page_w}" pageHeight="{page_h}" math="0" shadow="0">',
        "<root>",
        '<mxCell id="0"/>',
        '<mxCell id="1" parent="0"/>',
    ]
    parts.append(f'<mxCell id="title" value="{html_escape(route["title"])}" style="text;html=1;strokeColor=none;fillColor=none;fontSize={title_font};fontStyle=1;fontColor={style["text"]};" vertex="1" parent="1"><mxGeometry x="40" y="20" width="{layout["width"] - 80}" height="48" as="geometry"/></mxCell>')
    for stage in layout["stages"]:
        sid = f'stage_{stage["id"]}'
        stage_value = "" if stage.get("label_box") else html_escape(stage["title"])
        if stage.get("layout") in {"mainline", "a4stage"}:
            stage_value = ""
        parts.append(f'<mxCell id="{sid}" value="{stage_value}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={palette_item(style, stage["index"])};strokeColor={style["stage_stroke"]};fontColor={style["text"]};fontStyle=1;verticalAlign=top;spacingTop=8;opacity=80;{dashed}" vertex="1" parent="1"><mxGeometry x="{stage["x"]:.0f}" y="{stage["y"]:.0f}" width="{stage["w"]:.0f}" height="{stage["h"]:.0f}" as="geometry"/></mxCell>')
        if stage.get("layout") == "mainline":
            main = stage["main_box"]
            parts.append(f'<mxCell id="{sid}_main" value="{html_escape(stage["title"])}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={style.get("main_fill", "#DBEAFE")};strokeColor={style.get("main_stroke", style["header_fill"])};fontColor={style.get("main_text", style["text"])};fontStyle=1;fontSize=18;" vertex="1" parent="1"><mxGeometry x="{main["x"]:.0f}" y="{main["y"]:.0f}" width="{main["w"]:.0f}" height="{main["h"]:.0f}" as="geometry"/></mxCell>')
        elif stage.get("layout") == "a4stage":
            label = f'{stage["index"] + 1:02d}  {stage["title"]}'
            label_w = min(stage["w"] - 96, max(340, len(label) * 20))
            label_x = stage["x"] + (stage["w"] - label_w) / 2
            parts.append(f'<mxCell id="{sid}_header" value="{html_escape(label)}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={style["header_fill"]};strokeColor={style["header_fill"]};fontColor={style["header_text"]};fontStyle=1;fontSize=18;" vertex="1" parent="1"><mxGeometry x="{label_x:.0f}" y="{stage["y"] + 20:.0f}" width="{label_w:.0f}" height="48" as="geometry"/></mxCell>')
        elif stage.get("label_box"):
            label = stage["label_box"]
            parts.append(f'<mxCell id="{sid}_label" value="{html_escape(stage["title"])}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={style["header_fill"]};strokeColor={style["header_fill"]};fontColor={style["header_text"]};fontStyle=1;" vertex="1" parent="1"><mxGeometry x="{label["x"]:.0f}" y="{label["y"]:.0f}" width="{label["w"]:.0f}" height="{label["h"]:.0f}" as="geometry"/></mxCell>')
        elif layout["orientation"] == "vertical":
            label_w = min(stage["w"] * 0.34, 230)
            parts.append(f'<mxCell id="{sid}_tab" value="{html_escape(stage["title"])}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={style["header_fill"]};strokeColor={style["header_fill"]};fontColor={style["header_text"]};fontStyle=1;" vertex="1" parent="1"><mxGeometry x="{stage["x"] + 28:.0f}" y="{stage["y"] - 17:.0f}" width="{label_w:.0f}" height="34" as="geometry"/></mxCell>')
            axis_x = stage.get("axis_x")
            if axis_x is not None:
                parts.append(f'<mxCell id="{sid}_axis" value="{html_escape(stage["title"])}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={palette_item(style, stage["index"])};strokeColor={palette_item(style, stage["index"])};fontColor={style["text"]};fontStyle=1;" vertex="1" parent="1"><mxGeometry x="{axis_x - 58:.0f}" y="{stage["y"] + stage["h"] / 2 - 32:.0f}" width="82" height="64" as="geometry"/></mxCell>')
    for stage in route["stages"]:
        for node in stage["nodes"]:
            if node["id"] not in nodes:
                continue
            box = nodes[node["id"]]
            detail = html_escape(node.get("detail", ""))
            value = html_escape(node["label"])
            parts.append(f'<mxCell id="{node["id"]}" value="{value}" tooltip="{detail}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={style["node_fill"]};strokeColor={style["node_stroke"]};fontColor={style["text"]};fontSize={node_font};arcSize=12;" vertex="1" parent="1"><mxGeometry x="{box["x"]:.0f}" y="{box["y"]:.0f}" width="{box["w"]:.0f}" height="{box["h"]:.0f}" as="geometry"/></mxCell>')
    if show_node_edges(route):
        labels_visible = show_edge_labels(route)
        for edge in route["edges"]:
            if not edge.get("valid", True):
                continue
            edge_label = edge.get("label", "") if labels_visible else ""
            parts.append(f'<mxCell id="{edge["id"]}" value="{html_escape(edge_label)}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor={style["line"]};fontColor={style["muted"]};" edge="1" parent="1" source="{edge["from"]}" target="{edge["to"]}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    else:
        for index, (x1, y1, x2, y2) in enumerate(stage_flow_segments(layout), start=1):
            parts.append(f'<mxCell id="stage_flow_{index}" value="" style="edgeStyle=none;rounded=0;curved=0;html=1;endArrow=block;endFill=1;strokeColor={style["line"]};fontColor={style["muted"]};" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{x1:.0f}" y="{y1:.0f}" as="sourcePoint"/><mxPoint x="{x2:.0f}" y="{y2:.0f}" as="targetPoint"/></mxGeometry></mxCell>')
    bar = layout.get("output_bar")
    if bar and bar.get("text"):
        parts.append(f'<mxCell id="output_bar" value="{html_escape("成果输出：" + str(bar["text"]))}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={style.get("output_fill", "#E0F2FE")};strokeColor={style.get("output_stroke", style["header_fill"])};fontColor={style["text"]};fontStyle=1;fontSize=17;" vertex="1" parent="1"><mxGeometry x="{bar["x"]:.0f}" y="{bar["y"]:.0f}" width="{bar["w"]:.0f}" height="{bar["h"]:.0f}" as="geometry"/></mxCell>')
    parts.extend(["</root>", "</mxGraphModel>", "</diagram>", "</mxfile>"])
    return "\n".join(parts)


def main():
    if len(sys.argv) != 3:
        print("Usage: python render_drawio.py <tech-route.json> <output.drawio>")
        return 2
    save_text(sys.argv[2], make_drawio(load_route(sys.argv[1])))
    print(f"Wrote {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
