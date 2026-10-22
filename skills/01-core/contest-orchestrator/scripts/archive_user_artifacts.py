# -*- coding: utf-8 -*-
"""将明确标记为历史/备份/运行产物迁移到外部归档目录。

默认只预览。只有显式传入 ``--apply`` 才会移动文件；移动前会生成映射和 SHA-256，
目标必须位于技能根目录之外。运行时迁移只处理明确列出的项目缓存；不处理活动经验库、
回放库或知识库源文件。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    if path.is_file():
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    else:
        for child in sorted(path.rglob("*")):
            if child.is_file():
                h.update(str(child.relative_to(path)).encode("utf-8"))
                with child.open("rb") as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b""):
                        h.update(chunk)
    return h.hexdigest()


def candidate_paths(root: Path, include: str) -> list[Path]:
    paths: list[Path] = []
    if include in {"history", "all"}:
        for rel in (Path("scripts/archive"), Path("scripts/public_overrides"),
                    Path("contribution"), Path(".learnings")):
            p = root / rel
            if p.exists():
                paths.append(p)
        paths.extend(sorted(root.glob("CHANGELOG_*.md")))
        paths.extend(sorted(root.glob("SKILL_v*_backup.md")))
        for rel in (
            Path("memory/memory_change_log.md"),
            Path("memory/math_blueprints/CHANGELOG.md"),
            Path("memory/shadow_log.jsonl"),
            Path("memory/retrieval.py.bak_v381_fix"),
            Path("memory/calibration_db/draft_L0_simulated.yaml"),
            Path("memory/calibration_db/draft_L1.yaml"),
            Path("output_contract.md"),
            Path("presentation_polish.md"),
        ):
            p = root / rel
            if p.exists():
                paths.append(p)
        # 仅一次性历史回收脚本；运行期导入/合并脚本不在此列表中。
        for rel in (
            Path("scripts/import_2019C_external.py"),
            Path("scripts/import_huashu2021A.py"),
            Path("scripts/import_huashu2021B.py"),
            Path("scripts/re_tag_wr.py"),
            Path("scripts/monitor_triple_deviation.py"),
            Path("scripts/ab_compare_2025B.py"),
            Path("scripts/ab_compare_phaseb.py"),
            Path("docs/视觉通道配置_2026-08.md"),
        ):
            p = root / rel
            if p.exists():
                paths.append(p)
    if include in {"project-backups", "all"}:
        paths.extend(sorted(root.glob("competition_replay_backup_*")))
    if include in {"runtime-artifacts", "all"}:
        for rel in (
            Path("competition_replay"),
            Path("docs/audits"),
            Path("05_输出与交付"),
        ):
            path = root / rel
            if path.exists():
                paths.append(path)
        paths.extend(sorted(root.glob("SKILL_v*_full.md")))
    return list(dict.fromkeys(paths))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="归档历史脚本、replay 备份或已验证的技能内运行产物；默认只预览。")
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--archive-root",
        default=str(Path.home() / "Workspace" / "Project_01_数模空间" / "99_技能归档"),
    )
    parser.add_argument(
        "--include",
        choices=("history", "project-backups", "runtime-artifacts", "all"),
        default="all",
        help=("history=历史脚本/备份；project-backups=replay备份；"
              "runtime-artifacts=技能内 replay/审计/旧全文；all=三者。"),
    )
    parser.add_argument("--apply", action="store_true", help="确认后执行移动。")
    parser.add_argument("--dry-run", action="store_true", help="只生成计划（默认行为）。")
    args = parser.parse_args(argv)

    root = Path(args.skill_root).expanduser().resolve()
    archive_root = Path(args.archive_root).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"技能根目录不存在: {root}")
    if archive_root == root or root in archive_root.parents:
        parser.error("归档目录必须位于技能根目录之外")
    paths = candidate_paths(root, args.include)
    if not paths:
        print("未发现符合条件的历史/备份产物。")
        return 0

    batch = archive_root / f"contest-orchestrator-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    plan = []
    for source in paths:
        target = batch / source.relative_to(root)
        plan.append({
            "source": str(source),
            "target": str(target),
            "sha256_before": sha256(source),
            "kind": "directory" if source.is_dir() else "file",
        })

    apply_changes = bool(args.apply and not args.dry_run)
    if apply_changes:
        batch.mkdir(parents=True, exist_ok=False)
        for item in plan:
            source = Path(item["source"])
            target = Path(item["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            item["sha256_after"] = sha256(target)
            item["verified"] = item["sha256_before"] == item["sha256_after"]
            if not item["verified"]:
                raise RuntimeError(f"归档后哈希不一致: {target}")
        manifest = {
            "schema_version": "1.0",
            "moved_at": datetime.now(timezone.utc).isoformat(),
            "skill_root": str(root),
            "archive_batch": str(batch),
            "items": plan,
        }
        (batch / "archive_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    status = "已移动" if apply_changes else "预计移动"
    print(f"{status} {len(plan)} 个历史/备份路径 → {batch}")
    for item in plan:
        print(f"- {item['source']} -> {item['target']}")
    if not apply_changes:
        print("预览完成，未修改技能目录；确认目标后再传入 --apply。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
