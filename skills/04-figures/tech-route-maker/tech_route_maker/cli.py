import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import __version__
from .ingest import build_evidence_pack
from .quality import render_quality_report_markdown
from .registry import SUPPORTED_LAYOUTS, SUPPORTED_STYLES
from .schema import PRESETS, SUPPORTED_FORMATS, make_template_route
from .sources import attach_source_hashes
from .validator import format_validation_result, strict_render_blockers, validate, validate_file


def repo_root():
    return Path(__file__).resolve().parents[1]


def command_validate(args):
    route, errors, warnings, report = validate_file(args.route_json)
    print(format_validation_result(route, errors, warnings, report))
    blockers = strict_render_blockers(route, errors, report) if args.strict else []
    if blockers and not errors:
        print("Strict final-render blockers:")
        for blocker in blockers:
            print(f"- {blocker}")
    return 1 if errors or blockers else 0


def command_render(args):
    root = repo_root()
    render_all = root / "scripts" / "render_all.py"
    if not render_all.exists():
        raise SystemExit(f"Cannot find renderer: {render_all}")
    cmd = [
        sys.executable,
        str(render_all),
        args.route_json,
        args.output_dir,
        "--formats",
        args.formats,
    ]
    if args.allow_draft:
        cmd.append("--allow-draft")
    subprocess.check_call(cmd)
    return 0


def command_init(args):
    route = make_template_route(args.preset)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    source_path = output.parent / "source.md"
    if not source_path.exists():
        source_path.write_text(
            "# Project source\n\n"
            "## Project goal\n\nReplace this text with the authoritative project objective.\n\n"
            "## Source materials\n\nList the documents, data, materials, constraints, and expected outputs.\n",
            encoding="utf-8",
        )
    attach_source_hashes(route, output.parent)
    _errors, _warnings, report = validate(route, route_path=output.resolve())
    route["quality_report"] = report
    output.write_text(json.dumps(route, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.quality_report:
        quality_path = output.with_name("QUALITY_REPORT.md")
        quality_path.write_text(render_quality_report_markdown(report), encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Wrote {source_path}")
    return 0


def command_ingest(args):
    manifest_path, evidence_path, manifest = build_evidence_pack(args.sources, args.output_dir)
    print(f"Sources indexed: {manifest['source_count']}")
    print(f"Wrote {manifest_path}")
    print(f"Wrote {evidence_path}")
    return 0 if manifest["source_count"] else 1


def command_doctor(_args):
    root = repo_root()
    checks = {
        "version": __version__,
        "repo_root": str(root),
        "python": sys.version.split()[0],
        "scripts_dir": str(root / "scripts"),
        "render_all_exists": (root / "scripts" / "render_all.py").exists(),
        "validate_route_exists": (root / "scripts" / "validate_route.py").exists(),
        "supported_formats": SUPPORTED_FORMATS,
        "presets": sorted(PRESETS),
        "layouts": sorted(SUPPORTED_LAYOUTS),
        "styles": sorted(SUPPORTED_STYLES),
    }
    for key, value in checks.items():
        print(f"{key}: {value}")
    return 0 if checks["render_all_exists"] and checks["validate_route_exists"] else 1


def build_parser():
    parser = argparse.ArgumentParser(prog="trm", description="Render editable technical route diagrams.")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="Validate a tech-route.json file.")
    validate_parser.add_argument("route_json")
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail when the route is not ready for final rendering.",
    )
    validate_parser.set_defaults(func=command_validate)

    render_parser = sub.add_parser("render", help="Render editable outputs from a route JSON file.")
    render_parser.add_argument("route_json")
    render_parser.add_argument("output_dir")
    render_parser.add_argument("--formats", required=True, help="Comma-separated formats or all")
    render_parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Render a working draft even when final-quality checks are incomplete.",
    )
    render_parser.set_defaults(func=command_render)

    init_parser = sub.add_parser("init", help="Create a starter tech-route.json file.")
    init_parser.add_argument("--preset", default="academic-method", choices=sorted(PRESETS))
    init_parser.add_argument("--output", default="tech-route.json")
    init_parser.add_argument("--quality-report", action="store_true")
    init_parser.set_defaults(func=command_init)

    ingest_parser = sub.add_parser("ingest", help="Hash source files and build an evidence pack.")
    ingest_parser.add_argument("sources", nargs="+", help="Files or directories to inventory.")
    ingest_parser.add_argument("--output-dir", default="evidence-pack")
    ingest_parser.set_defaults(func=command_ingest)

    doctor_parser = sub.add_parser("doctor", help="Print local environment and renderer checks.")
    doctor_parser.set_defaults(func=command_doctor)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
