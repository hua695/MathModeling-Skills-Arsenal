"""Portable fallback installer for agents without `gh skill install`."""

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "evidence-pack",
    "output",
    "tech_route_maker.egg-info",
}


def files_to_install(destination):
    destination = destination.resolve()
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        try:
            path.resolve().relative_to(destination)
            continue
        except ValueError:
            pass
        files.append(path)
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Install tech-route-maker into an explicit agent skill directory."
    )
    parser.add_argument("--target", required=True, help="Parent directory that stores agent skills.")
    parser.add_argument("--name", default="tech-route-maker")
    parser.add_argument("--agent", default="generic", help="Label recorded in installation metadata.")
    parser.add_argument("--update", action="store_true", help="Update files in an existing installation.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    destination = target / args.name
    if destination.exists() and not args.update:
        raise SystemExit(f"Destination exists: {destination}. Use --update to refresh it.")
    files = files_to_install(destination)
    if args.dry_run:
        print(f"Would install {len(files)} files to {destination}")
        return 0

    destination.mkdir(parents=True, exist_ok=True)
    for source in files:
        relative = source.relative_to(ROOT)
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
    metadata = {
        "skill": "tech-route-maker",
        "agent": args.agent,
        "source": str(ROOT),
        "file_count": len(files),
        "update_mode": bool(args.update),
    }
    (destination / "INSTALLATION.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Installed {len(files)} files to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
