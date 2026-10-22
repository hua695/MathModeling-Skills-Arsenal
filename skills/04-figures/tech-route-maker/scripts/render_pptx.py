import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from route_common import (
    build_layout,
    edge_is_feedback,
    edge_points,
    get_style,
    load_route,
    show_node_edges,
    stage_flow_segments,
    wrap_text,
)


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
LANDSCAPE_W = 12192000
LANDSCAPE_H = 6858000
PORTRAIT_W = 6858000
PORTRAIT_H = 12192000


def color(value):
    return str(value or "#000000").replace("#", "").upper()


def tx_body(text, font_size=1200, font_color="111827", bold=False, max_chars=18):
    paras = []
    for line in wrap_text(text, max_chars, 4):
        b = ' b="1"' if bold else ""
        paras.append(
            f'<a:p><a:pPr algn="ctr"/><a:r><a:rPr lang="zh-CN" sz="{font_size}"{b}>'
            f'<a:solidFill><a:srgbClr val="{color(font_color)}"/></a:solidFill></a:rPr>'
            f"<a:t>{escape(line)}</a:t></a:r></a:p>"
        )
    return f'<p:txBody><a:bodyPr wrap="square" anchor="ctr"/><a:lstStyle/>{"".join(paras)}</p:txBody>'


def rect_shape(shape_id, name, x, y, w, h, text, fill, stroke, font_color, font_size=1200, bold=False, radius=True, dash=False, max_chars=18):
    geom = "roundRect" if radius else "rect"
    dash_xml = '<a:prstDash val="dash"/>' if dash else ""
    return f"""
<p:sp>
  <p:nvSpPr><p:cNvPr id="{shape_id}" name="{escape(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>
    <a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="{color(fill)}"/></a:solidFill>
    <a:ln w="12700"><a:solidFill><a:srgbClr val="{color(stroke)}"/></a:solidFill>{dash_xml}</a:ln>
  </p:spPr>
  {tx_body(text, font_size, font_color, bold, max_chars)}
</p:sp>"""


def line_shape(shape_id, x1, y1, x2, y2, stroke, arrow=True, dash=False):
    off_x = min(x1, x2)
    off_y = min(y1, y2)
    ext_x = max(abs(x2 - x1), 1)
    ext_y = max(abs(y2 - y1), 1)
    flip_h = ' flipH="1"' if x2 < x1 else ""
    flip_v = ' flipV="1"' if y2 < y1 else ""
    arrow_xml = '<a:headEnd type="triangle"/>' if arrow else ""
    dash_xml = '<a:prstDash val="dash"/>' if dash else ""
    return f"""
<p:cxnSp>
  <p:nvCxnSpPr><p:cNvPr id="{shape_id}" name="Connector {shape_id}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
  <p:spPr>
    <a:xfrm{flip_h}{flip_v}><a:off x="{int(off_x)}" y="{int(off_y)}"/><a:ext cx="{int(ext_x)}" cy="{int(ext_y)}"/></a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:ln w="19050"><a:solidFill><a:srgbClr val="{color(stroke)}"/></a:solidFill>{dash_xml}{arrow_xml}</a:ln>
  </p:spPr>
</p:cxnSp>"""


def scale_box(box, scale, ox, oy):
    return {
        "x": ox + box["x"] * scale,
        "y": oy + box["y"] * scale,
        "w": box["w"] * scale,
        "h": box["h"] * scale,
    }


def palette_item(style, index):
    palette = style.get("palette") or [style["stage_fill"]]
    return palette[index % len(palette)]


def slide_size_for(layout):
    if layout["orientation"] == "vertical" and str(layout.get("layout_name", "")).startswith("cn-"):
        return PORTRAIT_W, PORTRAIT_H
    if layout["height"] > layout["width"] * 1.18:
        return PORTRAIT_W, PORTRAIT_H
    return LANDSCAPE_W, LANDSCAPE_H


def make_slide(route):
    layout = build_layout(route)
    route = layout["route"]
    style = get_style(route)
    slide_w, slide_h = slide_size_for(layout)
    scale = min((slide_w - 500000) / layout["width"], (slide_h - 520000) / layout["height"])
    ox = (slide_w - layout["width"] * scale) / 2
    oy = (slide_h - layout["height"] * scale) / 2
    nodes = {nid: scale_box(box, scale, ox, oy) for nid, box in layout["nodes"].items()}
    shapes = []
    sid = 2
    title_w = slide_w - 2 * max(360000, ox + 420000)
    title_x = (slide_w - title_w) / 2
    title_fill = style["background"] if layout["orientation"] in {"mainline", "a4stage"} else palette_item(style, 0)
    title_stroke = style["background"] if layout["orientation"] in {"mainline", "a4stage"} else style["stage_stroke"]
    title_size = 2900 if layout["orientation"] == "mainline" else 2500 if layout["orientation"] == "a4stage" else 2100
    shapes.append(rect_shape(sid, "Title Band", title_x, oy + 70000, title_w, 500000, route["title"], title_fill, title_stroke, style["text"], title_size, True, False if layout["orientation"] in {"mainline", "a4stage"} else True, False, 34))
    sid += 1
    if route.get("subtitle"):
        sub_w = min(slide_w - 700000, title_w)
        subtitle_size = 1050 if layout["orientation"] in {"mainline", "a4stage"} else 850
        shapes.append(rect_shape(sid, "Subtitle", (slide_w - sub_w) / 2, oy + 560000, sub_w, 210000, route["subtitle"], style["background"], style["background"], style["muted"], subtitle_size, False, False, False, 44))
        sid += 1
    if layout["orientation"] == "vertical" and layout["stages"]:
        y1 = oy + (layout["stages"][0]["y"] + 10) * scale
        y2 = oy + (layout["stages"][-1]["y"] + layout["stages"][-1]["h"] - 10) * scale
        axis_x = ox + layout["stages"][0].get("axis_x", 100) * scale
        shapes.append(line_shape(sid, axis_x, y1, axis_x, y2, style["accent"], arrow=False))
        sid += 1
        for stage in layout["stages"]:
            box = scale_box({"x": stage.get("axis_x", 100) - 58, "y": stage["y"] + stage["h"] / 2 - 33, "w": 82, "h": 66}, scale, ox, oy)
            shapes.append(rect_shape(sid, f"Axis {stage['title']}", box["x"], box["y"], box["w"], box["h"], stage["title"], palette_item(style, stage["index"]), palette_item(style, stage["index"]), style["text"], 900, True, True))
            sid += 1
    for stage in layout["stages"]:
        box = scale_box(stage, scale, ox, oy)
        if stage.get("layout") == "mainline":
            shapes.append(rect_shape(sid, f"Stage {stage['title']}", box["x"], box["y"], box["w"], box["h"], "", palette_item(style, stage["index"]), style["stage_stroke"], style["text"], 800, False, True, False))
            sid += 1
            main = scale_box(stage["main_box"], scale, ox, oy)
            shapes.append(rect_shape(sid, f"Main {stage['title']}", main["x"], main["y"], main["w"], main["h"], stage["title"], style.get("main_fill", "#DBEAFE"), style.get("main_stroke", style["header_fill"]), style.get("main_text", style["text"]), 1550, True, True, False, 10))
            sid += 1
            continue
        if stage.get("layout") == "a4stage":
            shapes.append(rect_shape(sid, f"Stage {stage['title']}", box["x"], box["y"], box["w"], box["h"], "", palette_item(style, stage["index"]), style["stage_stroke"], style["text"], 800, False, True, False))
            sid += 1
            label = f"{stage['index'] + 1:02d}  {stage['title']}"
            label_w = min(box["w"] - 720000, max(2800000, len(label) * 190000))
            label_x = box["x"] + (box["w"] - label_w) / 2
            shapes.append(rect_shape(sid, f"Header {stage['title']}", label_x, box["y"] + 190000, label_w, 430000, label, style["header_fill"], style["header_fill"], style["header_text"], 1450, True, True, False, 14))
            sid += 1
            continue
        shapes.append(rect_shape(sid, f"Stage {stage['title']}", box["x"], box["y"], box["w"], box["h"], "", palette_item(style, stage["index"]), style["stage_stroke"], style["text"], 1000, False, True, bool(style.get("stage_dash"))))
        sid += 1
        if stage.get("label_box"):
            label = scale_box(stage["label_box"], scale, ox, oy)
            shapes.append(rect_shape(sid, f"Label {stage['title']}", label["x"], label["y"], label["w"], label["h"], stage["title"], style["header_fill"], style["header_fill"], style["header_text"], 1050, True, True))
            sid += 1
        else:
            header_w = min(box["w"] * 0.34, 1850000)
            shapes.append(rect_shape(sid, f"Header {stage['title']}", box["x"] + 220000, box["y"] - 120000 if layout["orientation"] == "vertical" else box["y"], header_w, max(260000, 38 * scale), stage["title"], style["header_fill"], style["header_fill"], style["header_text"], 1100, True, True))
            sid += 1
    if show_node_edges(route):
        for edge in route["edges"]:
            if not edge.get("valid", True) or edge["from"] not in nodes or edge["to"] not in nodes:
                continue
            a = nodes[edge["from"]]
            b = nodes[edge["to"]]
            points = edge_points(a, b, layout["orientation"])
            dashed = edge_is_feedback(edge, a, b)
            for index in range(len(points) - 1):
                x1, y1 = points[index]
                x2, y2 = points[index + 1]
                shapes.append(line_shape(sid, x1, y1, x2, y2, style["line"], arrow=index == len(points) - 2, dash=dashed))
                sid += 1
    else:
        for x1, y1, x2, y2 in stage_flow_segments(layout):
            shapes.append(line_shape(sid, ox + x1 * scale, oy + y1 * scale, ox + x2 * scale, oy + y2 * scale, style["line"], arrow=True))
            sid += 1
    for stage in route["stages"]:
        for node in stage["nodes"]:
            if node["id"] not in nodes:
                continue
            box = nodes[node["id"]]
            node_size = 1320 if layout["orientation"] == "mainline" else 1250 if layout["orientation"] == "a4stage" else 930
            shapes.append(rect_shape(sid, f"Node {node['id']}", box["x"], box["y"], box["w"], box["h"], node["label"], style["node_fill"], style["node_stroke"], style["text"], node_size, False, True, False, 12))
            sid += 1
    bar = layout.get("output_bar")
    if bar and bar.get("text"):
        output = scale_box(bar, scale, ox, oy)
        shapes.append(rect_shape(sid, "Output", output["x"], output["y"], output["w"], output["h"], "成果输出：" + str(bar["text"]), style.get("output_fill", "#E0F2FE"), style.get("output_stroke", style["header_fill"]), style["text"], 1400, True, True, False, 40))
        sid += 1
    return slide_w, slide_h, f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(shapes)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def write_pptx(route, output):
    slide_w, slide_h, slide = make_slide(route)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/><Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/><Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/><Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>""",
        "ppt/presentation.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst><p:sldSz cx="{slide_w}" cy="{slide_h}" type="custom"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>""",
        "ppt/_rels/presentation.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>""",
        "ppt/slides/slide1.xml": slide,
        "ppt/slides/_rels/slide1.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>""",
        "ppt/slideMasters/slideMaster1.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>""",
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>""",
        "ppt/slideLayouts/slideLayout1.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>""",
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>""",
        "ppt/theme/theme1.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="{A_NS}" name="TechRouteMaker"><a:themeElements><a:clrScheme name="TechRoute"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F2937"/></a:dk2><a:lt2><a:srgbClr val="F8FAFC"/></a:lt2><a:accent1><a:srgbClr val="2563EB"/></a:accent1><a:accent2><a:srgbClr val="0F766E"/></a:accent2><a:accent3><a:srgbClr val="7C3AED"/></a:accent3><a:accent4><a:srgbClr val="F59E0B"/></a:accent4><a:accent5><a:srgbClr val="EF4444"/></a:accent5><a:accent6><a:srgbClr val="64748B"/></a:accent6><a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink></a:clrScheme><a:fontScheme name="Arial"><a:majorFont><a:latin typeface="Arial"/></a:majorFont><a:minorFont><a:latin typeface="Arial"/></a:minorFont></a:fontScheme><a:fmtScheme name="TechRoute"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>""",
        "docProps/core.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"><dc:creator>tech-route-maker</dc:creator><cp:lastModifiedBy>tech-route-maker</cp:lastModifiedBy></cp:coreProperties>""",
        "docProps/app.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>tech-route-maker</Application><PresentationFormat>Widescreen</PresentationFormat><Slides>1</Slides></Properties>""",
    }
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            zf.writestr(info, content)


def main():
    if len(sys.argv) != 3:
        print("Usage: python render_pptx.py <tech-route.json> <output.pptx>")
        return 2
    write_pptx(load_route(sys.argv[1]), sys.argv[2])
    print(f"Wrote {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
