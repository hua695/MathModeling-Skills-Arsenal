# Schema Migration To v0.3.0

## Required Changes

1. Set `route_version` to `0.3.0`.
2. Give every `metadata.source_files` entry a stable `id`.
3. Add a SHA-256 as `source_files[].sha256` and a matching structured `metadata.source_hashes` record.
4. Use `kind: source`, `source_id`, `path`, `locator` and `quote_or_note` in each node evidence item.
5. Resolve or remove inferred nodes and unresolved questions before final rendering.
6. Replace unsupported layout or style identifiers with values listed in `references/layout-patterns.md` and `references/visual-styles.md`.

## Recommended Workflow

```bash
trm ingest path/to/source-files --output-dir evidence-pack
trm validate path/to/tech-route.json --strict
trm render path/to/tech-route.json output --formats pptx,svg,drawio,json
```

Use `--allow-draft` only for an unfinished route. The quality report keeps inferred coverage separate from verified evidence coverage.
