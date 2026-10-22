import json
import sys

from route_common import build_layout, center, get_style, load_route, save_text, show_node_edges, stage_flow_segments


def element_id(prefix, value):
    return f"{prefix}_{str(value).replace('-', '_')}"


def make_excalidraw(route):
    layout = build_layout(route)
    route = layout["route"]
    style = get_style(route)
    nodes = layout["nodes"]
    title_font = 32 if layout["orientation"] == "mainline" else 28 if layout["orientation"] == "a4stage" else 24
    node_font = 17 if layout["orientation"] == "mainline" else 16 if layout["orientation"] == "a4stage" else 14
    elements = []
    elements.append({
        "id": "title",
        "type": "text",
        "x": 90,
        "y": 22,
        "width": layout["width"] - 180,
        "height": 48,
        "angle": 0,
        "strokeColor": style["text"],
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "text": route["title"],
        "fontSize": title_font,
        "fontFamily": 1,
        "textAlign": "center",
        "verticalAlign": "middle",
        "containerId": None,
        "originalText": route["title"],
        "lineHeight": 1.25,
    })
    for stage in layout["stages"]:
        elements.append({
            "id": element_id("stage", stage["id"]),
            "type": "rectangle",
            "x": stage["x"],
            "y": stage["y"],
            "width": stage["w"],
            "height": stage["h"],
            "angle": 0,
            "strokeColor": style["stage_stroke"],
            "backgroundColor": style["stage_fill"],
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
        })
        if stage.get("label_box"):
            label = stage["label_box"]
            elements.append({
                "id": element_id("stage_label", stage["id"]),
                "type": "rectangle",
                "x": label["x"],
                "y": label["y"],
                "width": label["w"],
                "height": label["h"],
                "angle": 0,
                "strokeColor": style["header_fill"],
                "backgroundColor": style["header_fill"],
                "fillStyle": "solid",
                "strokeWidth": 1,
                "strokeStyle": "solid",
                "roughness": 0,
                "opacity": 100,
            })
        if stage.get("layout") not in {"mainline", "a4stage"}:
            elements.append({
                "id": element_id("stage_text", stage["id"]),
                "type": "text",
                "x": (stage.get("label_box") or stage)["x"] + 12,
                "y": (stage.get("label_box") or stage)["y"] + 10,
                "width": (stage.get("label_box") or stage)["w"] - 24,
                "height": min(42, (stage.get("label_box") or stage)["h"] - 12),
                "angle": 0,
                "strokeColor": style["header_text"] if stage.get("label_box") else style["text"],
                "backgroundColor": "transparent",
                "fillStyle": "solid",
                "strokeWidth": 1,
                "strokeStyle": "solid",
                "roughness": 0,
                "opacity": 100,
                "text": stage["title"],
                "fontSize": 15,
                "fontFamily": 1,
                "textAlign": "center",
                "verticalAlign": "middle",
                "containerId": None,
                "originalText": stage["title"],
                "lineHeight": 1.25,
            })
        if stage.get("layout") == "mainline":
            main = stage["main_box"]
            elements.append({
                "id": element_id("stage_main", stage["id"]),
                "type": "rectangle",
                "x": main["x"],
                "y": main["y"],
                "width": main["w"],
                "height": main["h"],
                "angle": 0,
                "strokeColor": style.get("main_stroke", style["header_fill"]),
                "backgroundColor": style.get("main_fill", "#DBEAFE"),
                "fillStyle": "solid",
                "strokeWidth": 2,
                "strokeStyle": "solid",
                "roughness": 0,
                "opacity": 100,
            })
            elements.append({
                "id": element_id("stage_main_text", stage["id"]),
                "type": "text",
                "x": main["x"] + 10,
                "y": main["y"] + 18,
                "width": main["w"] - 20,
                "height": main["h"] - 18,
                "angle": 0,
                "strokeColor": style.get("main_text", style["text"]),
                "backgroundColor": "transparent",
                "fillStyle": "solid",
                "strokeWidth": 1,
                "strokeStyle": "solid",
                "roughness": 0,
                "opacity": 100,
                "text": stage["title"],
                "fontSize": 19,
                "fontFamily": 1,
                "textAlign": "center",
                "verticalAlign": "middle",
                "containerId": None,
                "originalText": stage["title"],
                "lineHeight": 1.25,
            })
        elif stage.get("layout") == "a4stage":
            label = f"{stage['index'] + 1:02d}  {stage['title']}"
            label_w = min(stage["w"] - 96, max(340, len(label) * 20))
            label_x = stage["x"] + (stage["w"] - label_w) / 2
            elements.append({
                "id": element_id("stage_header", stage["id"]),
                "type": "rectangle",
                "x": label_x,
                "y": stage["y"] + 20,
                "width": label_w,
                "height": 48,
                "angle": 0,
                "strokeColor": style["header_fill"],
                "backgroundColor": style["header_fill"],
                "fillStyle": "solid",
                "strokeWidth": 1,
                "strokeStyle": "solid",
                "roughness": 0,
                "opacity": 100,
            })
            elements.append({
                "id": element_id("stage_header_text", stage["id"]),
                "type": "text",
                "x": label_x + 12,
                "y": stage["y"] + 31,
                "width": label_w - 24,
                "height": 40,
                "angle": 0,
                "strokeColor": style["header_text"],
                "backgroundColor": "transparent",
                "fillStyle": "solid",
                "strokeWidth": 1,
                "strokeStyle": "solid",
                "roughness": 0,
                "opacity": 100,
                "text": label,
                "fontSize": 18,
                "fontFamily": 1,
                "textAlign": "center",
                "verticalAlign": "middle",
                "containerId": None,
                "originalText": label,
                "lineHeight": 1.25,
            })
    if show_node_edges(route):
        edge_items = []
        for edge in route["edges"]:
            if not edge.get("valid", True) or edge["from"] not in nodes or edge["to"] not in nodes:
                continue
            x1, y1 = center(nodes[edge["from"]])
            x2, y2 = center(nodes[edge["to"]])
            edge_items.append((element_id("edge", edge["id"]), x1, y1, x2, y2))
    else:
        edge_items = [(f"stage_flow_{index}", x1, y1, x2, y2) for index, (x1, y1, x2, y2) in enumerate(stage_flow_segments(layout), start=1)]
    for edge_id, x1, y1, x2, y2 in edge_items:
        elements.append({
            "id": edge_id,
            "type": "arrow",
            "x": x1,
            "y": y1,
            "width": x2 - x1,
            "height": y2 - y1,
            "angle": 0,
            "strokeColor": style["line"],
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "points": [[0, 0], [x2 - x1, y2 - y1]],
            "lastCommittedPoint": [x2 - x1, y2 - y1],
            "startBinding": None,
            "endBinding": None,
            "startArrowhead": None,
            "endArrowhead": "arrow",
        })
    for stage in route["stages"]:
        for node in stage["nodes"]:
            if node["id"] not in nodes:
                continue
            box = nodes[node["id"]]
            elements.append({
                "id": element_id("node", node["id"]),
                "type": "rectangle",
                "x": box["x"],
                "y": box["y"],
                "width": box["w"],
                "height": box["h"],
                "angle": 0,
                "strokeColor": style["node_stroke"],
                "backgroundColor": style["node_fill"],
                "fillStyle": "solid",
                "strokeWidth": 1,
                "strokeStyle": "solid",
                "roughness": 0,
                "opacity": 100,
            })
            elements.append({
                "id": element_id("node_text", node["id"]),
                "type": "text",
                "x": box["x"] + 8,
                "y": box["y"] + 15,
                "width": box["w"] - 16,
                "height": box["h"] - 16,
                "angle": 0,
                "strokeColor": style["text"],
                "backgroundColor": "transparent",
                "fillStyle": "solid",
                "strokeWidth": 1,
                "strokeStyle": "solid",
                "roughness": 0,
                "opacity": 100,
                "text": node["label"],
                "fontSize": node_font,
                "fontFamily": 1,
                "textAlign": "center",
                "verticalAlign": "middle",
                "containerId": None,
                "originalText": node["label"],
                "lineHeight": 1.25,
            })
    bar = layout.get("output_bar")
    if bar and bar.get("text"):
        text = "成果输出：" + str(bar["text"])
        elements.append({
            "id": "output_bar",
            "type": "rectangle",
            "x": bar["x"],
            "y": bar["y"],
            "width": bar["w"],
            "height": bar["h"],
            "angle": 0,
            "strokeColor": style.get("output_stroke", style["header_fill"]),
            "backgroundColor": style.get("output_fill", "#E0F2FE"),
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
        })
        elements.append({
            "id": "output_bar_text",
            "type": "text",
            "x": bar["x"] + 24,
            "y": bar["y"] + 24,
            "width": bar["w"] - 48,
            "height": bar["h"] - 30,
            "angle": 0,
            "strokeColor": style["text"],
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "text": text,
            "fontSize": 18,
            "fontFamily": 1,
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": None,
            "originalText": text,
            "lineHeight": 1.25,
        })
    scene = {"type": "excalidraw", "version": 2, "source": "tech-route-maker", "elements": elements, "appState": {"viewBackgroundColor": style["background"]}, "files": {}}
    return json.dumps(scene, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) != 3:
        print("Usage: python render_excalidraw.py <tech-route.json> <output.excalidraw>")
        return 2
    save_text(sys.argv[2], make_excalidraw(load_route(sys.argv[1])))
    print(f"Wrote {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
