"""Source manifest, hashing, and local verification helpers."""

import hashlib
from pathlib import Path


TEXT_SUFFIXES = {
    ".c",
    ".cpp",
    ".csv",
    ".h",
    ".html",
    ".java",
    ".js",
    ".json",
    ".md",
    ".py",
    ".rst",
    ".tex",
    ".toml",
    ".ts",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_repo_root(start):
    start = Path(start).resolve()
    if start.is_file():
        start = start.parent
    for candidate in (start,) + tuple(start.parents):
        if (candidate / "pyproject.toml").exists() or (candidate / ".git").exists():
            return candidate
    return None


def resolve_source_path(raw_path, route_path=None, base_dir=None):
    path = Path(str(raw_path or ""))
    if not str(path):
        return None
    candidates = []
    if path.is_absolute():
        candidates.append(path)
    else:
        if base_dir:
            candidates.append(Path(base_dir) / path)
        if route_path:
            route_path = Path(route_path).resolve()
            candidates.append(route_path.parent / path)
            root = find_repo_root(route_path)
            if root:
                candidates.append(root / path)
        package_root = Path(__file__).resolve().parents[1]
        candidates.extend([package_root / path, Path.cwd() / path])

    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if resolved.exists() and resolved.is_file():
            return resolved
    return None


def _hash_lookup(route):
    lookup = {}
    metadata = route.get("metadata") or {}
    for item in metadata.get("source_hashes") or []:
        if not isinstance(item, dict):
            continue
        value = item.get("value") or item.get("sha256")
        if not value:
            continue
        if item.get("source_id"):
            lookup[("id", str(item["source_id"]))] = str(value).lower()
        if item.get("path"):
            lookup[("path", str(item["path"]))] = str(value).lower()
    return lookup


def expected_source_hash(record, route):
    direct = record.get("sha256")
    if direct:
        return str(direct).lower()
    lookup = _hash_lookup(route)
    source_id = str(record.get("id") or record.get("source_id") or "")
    raw_path = str(record.get("path") or "")
    return lookup.get(("id", source_id)) or lookup.get(("path", raw_path))


def verify_sources(route, route_path=None, base_dir=None):
    metadata = route.get("metadata") or {}
    records = metadata.get("source_files") or []
    report_records = []
    resolved_sources = {}
    missing = []
    unhashed = []
    mismatches = []
    duplicate_ids = []
    seen_ids = set()

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            report_records.append({"index": index, "status": "invalid-record"})
            continue
        source_id = str(record.get("id") or record.get("source_id") or f"source_{index}")
        raw_path = str(record.get("path") or "")
        if source_id in seen_ids:
            duplicate_ids.append(source_id)
        seen_ids.add(source_id)
        resolved = resolve_source_path(raw_path, route_path=route_path, base_dir=base_dir)
        expected = expected_source_hash(record, route)
        item = {
            "source_id": source_id,
            "path": raw_path,
            "kind": str(record.get("kind") or "document"),
            "expected_sha256": expected or "",
        }
        if not resolved:
            item["status"] = "missing"
            missing.append(source_id)
            report_records.append(item)
            continue
        actual = sha256_file(resolved)
        item["actual_sha256"] = actual
        if not expected:
            item["status"] = "unhashed"
            unhashed.append(source_id)
        elif actual != expected:
            item["status"] = "hash-mismatch"
            mismatches.append(source_id)
        else:
            item["status"] = "verified"

        text = None
        if resolved.suffix.lower() in TEXT_SUFFIXES:
            try:
                text = resolved.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = resolved.read_text(encoding="utf-8", errors="replace")
        resolved_sources[source_id] = {
            "path": resolved,
            "raw_path": raw_path,
            "kind": item["kind"],
            "text": text,
            "status": item["status"],
        }
        report_records.append(item)

    declared_count = len(records)
    verified_count = sum(item.get("status") == "verified" for item in report_records)
    if not declared_count:
        status = "missing"
    elif verified_count == declared_count and not duplicate_ids:
        status = "verified"
    elif missing or mismatches:
        status = "failed"
    else:
        status = "unverified"
    report = {
        "status": status,
        "declared_count": declared_count,
        "verified_count": verified_count,
        "missing_sources": missing,
        "unhashed_sources": unhashed,
        "hash_mismatches": mismatches,
        "duplicate_source_ids": duplicate_ids,
        "records": report_records,
    }
    return report, resolved_sources


def attach_source_hashes(route, base_dir):
    metadata = route.setdefault("metadata", {})
    hashes = []
    for index, record in enumerate(metadata.get("source_files") or [], start=1):
        if not isinstance(record, dict):
            continue
        source_id = str(record.get("id") or record.get("source_id") or f"source_{index}")
        record["id"] = source_id
        resolved = resolve_source_path(record.get("path"), base_dir=base_dir)
        if not resolved:
            continue
        value = sha256_file(resolved)
        record["sha256"] = value
        hashes.append(
            {
                "source_id": source_id,
                "path": str(record.get("path") or ""),
                "algorithm": "sha256",
                "value": value,
            }
        )
    metadata["source_hashes"] = hashes
    return route
