"""Deterministic source inventory and text extraction for agent workflows."""

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .sources import TEXT_SUFFIXES, sha256_file


SKIP_DIRS = {".git", ".idea", ".vscode", "__pycache__", "build", "dist", "node_modules", "output"}
MAX_EXCERPT_CHARS = 12000


def discover_files(inputs):
    files = []
    seen = set()
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        candidates = [path] if path.is_file() else path.rglob("*") if path.is_dir() else []
        for candidate in candidates:
            if not candidate.is_file() or any(part in SKIP_DIRS for part in candidate.parts):
                continue
            key = str(candidate).lower()
            if key not in seen:
                seen.add(key)
                files.append(candidate)
    return sorted(files, key=lambda item: str(item).lower())


def extract_docx_text(path):
    with zipfile.ZipFile(path) as archive:
        data = archive.read("word/document.xml")
    root = ElementTree.fromstring(data)
    text = []
    for element in root.iter():
        if element.tag.endswith("}t") and element.text:
            text.append(element.text)
        elif element.tag.endswith("}p"):
            text.append("\n")
    return "".join(text).strip()


def extract_text(path):
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="replace"), "text"
    if suffix == ".docx":
        try:
            return extract_docx_text(path), "docx"
        except (KeyError, zipfile.BadZipFile, ElementTree.ParseError):
            return "", "docx-unreadable"
    return "", "binary"


def build_evidence_pack(inputs, output_dir):
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    files = discover_files(inputs)
    records = []
    markdown = [
        "# Evidence Pack",
        "",
        "This inventory records immutable source hashes before route extraction.",
        "Binary PDFs and images remain valid sources, but an agent must inspect them with an appropriate document or vision tool.",
        "",
    ]

    for index, path in enumerate(files, start=1):
        source_id = f"source_{index}"
        text, extraction = extract_text(path)
        truncated = len(text) > MAX_EXCERPT_CHARS
        excerpt = text[:MAX_EXCERPT_CHARS]
        record = {
            "id": source_id,
            "path": str(path),
            "kind": "document" if extraction != "binary" else "binary",
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "text_extraction": extraction,
            "text_chars": len(text),
            "excerpt_truncated": truncated,
        }
        records.append(record)
        markdown.extend(
            [
                f"## {source_id}: {path.name}",
                "",
                f"- Path: `{path}`",
                f"- SHA-256: `{record['sha256']}`",
                f"- Extraction: `{extraction}`",
                f"- Size: {record['size_bytes']} bytes",
                "",
            ]
        )
        if excerpt:
            markdown.extend(["### Extracted text", "", "```text", excerpt, "```", ""])
        else:
            markdown.extend(
                [
                    "No plain text was extracted. Inspect this source directly before creating evidence locators.",
                    "",
                ]
            )

    manifest = {
        "manifest_version": "1.0",
        "source_count": len(records),
        "sources": records,
    }
    manifest_path = output_dir / "source-manifest.json"
    evidence_path = output_dir / "EVIDENCE_PACK.md"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence_path.write_text("\n".join(markdown).rstrip() + "\n", encoding="utf-8")
    return manifest_path, evidence_path, manifest
