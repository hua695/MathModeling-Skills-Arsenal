import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech_route_maker.quality import render_quality_report_markdown  # noqa: E402
from tech_route_maker.validator import (  # noqa: E402
    format_validation_result,
    strict_render_blockers,
    validate_file,
)


SCRIPT_BY_FORMAT = {
    "mermaid": ("render_mermaid.py", "tech-route.mmd"),
    "svg": ("render_svg.py", "tech-route.svg"),
    "png": ("render_png.py", "tech-route.png"),
    "drawio": ("render_drawio.py", "tech-route.drawio"),
    "drawio-code": ("render_drawio_code.py", "tech-route.drawio-code.xml"),
    "excalidraw": ("render_excalidraw.py", "tech-route.excalidraw"),
    "html": ("render_html.py", "tech-route.html"),
    "markdown": ("render_markdown.py", "TECH_ROUTE.md"),
    "pptx": ("render_pptx.py", "tech-route.pptx"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("route_json")
    parser.add_argument("output_dir")
    parser.add_argument("--formats", required=True, help="Comma-separated formats or all")
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Render despite final-quality blockers. Structural validation errors still stop rendering.",
    )
    args = parser.parse_args()
    selected = [x.strip().lower() for x in args.formats.split(",") if x.strip()]
    if "all" in selected:
        selected = list(SCRIPT_BY_FORMAT) + ["json"]
    route, errors, warnings, report = validate_file(args.route_json)
    if errors:
        print(format_validation_result(route, errors, warnings, report), file=sys.stderr)
        raise SystemExit("Rendering stopped because route validation failed.")
    blockers = strict_render_blockers(route, errors, report)
    if blockers and not args.allow_draft:
        details = "\n".join(f"- {item}" for item in blockers)
        raise SystemExit(
            "Final rendering stopped by the quality gate:\n"
            f"{details}\n"
            "Resolve these items or use --allow-draft for a clearly marked working draft."
        )
    if blockers:
        print("Draft rendering enabled. Remaining blockers:", file=sys.stderr)
        for blocker in blockers:
            print(f"- {blocker}", file=sys.stderr)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).resolve().parent
    route["quality_report"] = report
    write_json = False
    for fmt in selected:
        if fmt == "json":
            write_json = True
            continue
        if fmt not in SCRIPT_BY_FORMAT:
            raise SystemExit(f"Unknown format: {fmt}")
        script, filename = SCRIPT_BY_FORMAT[fmt]
        subprocess.check_call([sys.executable, str(script_dir / script), args.route_json, str(out_dir / filename)])
    if write_json:
        target = out_dir / "tech-route.json"
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(route, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"Wrote {target}")
    quality_path = out_dir / "QUALITY_REPORT.md"
    with open(quality_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_quality_report_markdown(report))
    print(f"Wrote {quality_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
