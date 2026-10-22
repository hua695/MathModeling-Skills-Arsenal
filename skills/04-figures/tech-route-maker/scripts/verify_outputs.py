"""Structural and content-parity checks for generated editable outputs."""

import argparse
import html
import json
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from route_common import build_layout, load_route  # noqa: E402


OUTPUT_FILES = {
    "json": "tech-route.json",
    "svg": "tech-route.svg",
    "png": "tech-route.png",
    "drawio": "tech-route.drawio",
    "drawio-code": "tech-route.drawio-code.xml",
    "excalidraw": "tech-route.excalidraw",
    "mermaid": "tech-route.mmd",
    "html": "tech-route.html",
    "markdown": "TECH_ROUTE.md",
    "pptx": "tech-route.pptx",
}

# Formats that are binary/raster and cannot be text-parsed for label verification
BINARY_FORMATS = {"png"}


class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def normalized(value):
    return re.sub(r"\s+", "", html.unescape(str(value or ""))).casefold()


def rects_overlap(first, second):
    return not (
        first["x"] + first["w"] <= second["x"]
        or second["x"] + second["w"] <= first["x"]
        or first["y"] + first["h"] <= second["y"]
        or second["y"] + second["h"] <= first["y"]
    )


def verify_layout(route):
    layout = build_layout(route)
    expected = {node["id"] for stage in route["stages"] for node in stage["nodes"]}
    actual = set(layout["nodes"])
    errors = []
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append("Layout dropped nodes: " + ", ".join(missing))
    if extra:
        errors.append("Layout created unknown nodes: " + ", ".join(extra))

    stage_lookup = {stage["id"]: stage for stage in layout["stages"]}
    by_stage = {}
    for node_id, box in layout["nodes"].items():
        by_stage.setdefault(box.get("stage"), []).append((node_id, box))
        stage = stage_lookup.get(box.get("stage"))
        if stage and not (
            box["x"] >= stage["x"] - 1
            and box["y"] >= stage["y"] - 1
            and box["x"] + box["w"] <= stage["x"] + stage["w"] + 1
            and box["y"] + box["h"] <= stage["y"] + stage["h"] + 1
        ):
            errors.append(f"Node box leaves its stage boundary: {node_id}")
    for stage_id, boxes in by_stage.items():
        for index, (first_id, first) in enumerate(boxes):
            for second_id, second in boxes[index + 1 :]:
                if rects_overlap(first, second):
                    errors.append(f"Node boxes overlap in {stage_id}: {first_id}, {second_id}")
    return errors


def xml_text(path):
    root = ElementTree.parse(path).getroot()
    parts = list(root.itertext())
    parts.extend(value for element in root.iter() for value in element.attrib.values())
    return " ".join(parts)


def pptx_text(path):
    parts = []
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"Corrupt PPTX member: {bad}")
        for name in archive.namelist():
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                root = ElementTree.fromstring(archive.read(name))
                parts.extend(element.text or "" for element in root.iter() if element.tag.endswith("}t"))
    return " ".join(parts)


def output_text(output_format, path):
    if output_format in {"svg", "drawio", "drawio-code"}:
        return xml_text(path)
    if output_format == "pptx":
        return pptx_text(path)
    if output_format == "excalidraw":
        data = json.loads(path.read_text(encoding="utf-8"))
        return " ".join(
            str(element.get("text") or element.get("originalText") or "")
            for element in data.get("elements") or []
        )
    if output_format == "json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return " ".join(
            str(node.get("label") or "")
            for stage in data.get("stages") or []
            for node in stage.get("nodes") or []
        )
    if output_format == "html":
        collector = TextCollector()
        collector.feed(path.read_text(encoding="utf-8"))
        return " ".join(collector.parts)
    return path.read_text(encoding="utf-8")


def verify_editability(output_format, path, node_count):
    errors = []
    if output_format == "pptx":
        with zipfile.ZipFile(path) as archive:
            media = [name for name in archive.namelist() if name.startswith("ppt/media/")]
            if media:
                errors.append(f"{path.name} contains embedded media instead of shape-only route content")
            slide_names = [
                name
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            ]
            if not slide_names:
                errors.append(f"{path.name} has no editable slide XML")
    elif output_format == "svg":
        root = ElementTree.parse(path).getroot()
        images = [element for element in root.iter() if element.tag.split("}")[-1] == "image"]
        if images:
            errors.append(f"{path.name} contains raster image elements")
    elif output_format in {"drawio", "drawio-code"}:
        root = ElementTree.parse(path).getroot()
        vertices = [element for element in root.iter("mxCell") if element.get("vertex") == "1"]
        if len(vertices) < node_count:
            errors.append(f"{path.name} has fewer editable cells than route nodes")
    elif output_format == "excalidraw":
        data = json.loads(path.read_text(encoding="utf-8"))
        text_elements = [element for element in data.get("elements") or [] if element.get("type") == "text"]
        if len(text_elements) < node_count:
            errors.append(f"{path.name} has fewer editable text elements than route nodes")
    return errors


def verify_outputs(route, output_dir, formats):
    labels = [node["label"] for stage in route["stages"] for node in stage["nodes"]]
    errors = []
    for output_format in formats:
        filename = OUTPUT_FILES.get(output_format)
        if not filename:
            errors.append(f"Unknown QA format: {output_format}")
            continue
        path = output_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"Missing or empty output: {path}")
            continue
        if output_format in BINARY_FORMATS:
            # Binary formats (PNG) only need file existence and non-zero size;
            # text label verification is not applicable to raster images.
            continue
        try:
            content = normalized(output_text(output_format, path))
        except (ElementTree.ParseError, json.JSONDecodeError, zipfile.BadZipFile, ValueError) as exc:
            errors.append(f"Cannot parse {path.name}: {exc}")
            continue
        missing = [label for label in labels if normalized(label) not in content]
        if missing:
            errors.append(f"{path.name} is missing labels: {', '.join(missing)}")
        errors.extend(verify_editability(output_format, path, len(labels)))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("route_json")
    parser.add_argument("output_dir")
    parser.add_argument("--formats", default=",".join(OUTPUT_FILES))
    args = parser.parse_args()
    route = load_route(args.route_json)
    formats = [item.strip() for item in args.formats.split(",") if item.strip()]
    errors = verify_layout(route)
    errors.extend(verify_outputs(route, Path(args.output_dir), formats))
    if errors:
        print("Output verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    node_count = sum(len(stage["nodes"]) for stage in route["stages"])
    print(f"Output verification OK: {node_count} nodes across {len(formats)} formats.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
