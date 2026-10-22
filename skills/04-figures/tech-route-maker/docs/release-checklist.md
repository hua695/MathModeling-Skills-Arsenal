# Release Checklist

## Validation

- [ ] Compile `scripts/*.py`, `tech_route_maker/*.py` and `tests/*.py` on Python 3.8, 3.11 and 3.12.
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `python scripts/check_text_integrity.py`.
- [ ] Run `trm doctor` and `trm ingest docs --output-dir <temporary-directory>`.
- [ ] Run `trm validate <route> --strict` for every `examples/*-demo` route.
- [ ] Render all nine formats for every demo.
- [ ] Run `scripts/verify_outputs.py` for node preservation, overlap checks, parse checks and label parity.
- [ ] Run the Skill Creator validator on `SKILL.md`.
- [ ] Test `gh skill install ... SKILL.md` with at least one user-scope agent target.

## Documentation

- [ ] README first screen states the research/engineering focus and manual-editing warning.
- [ ] Chinese and English guides describe the same strict-quality behavior.
- [ ] Installation commands use the current GitHub CLI syntax.
- [ ] Schema docs say `0.3.0` and explain source IDs, hashes, evidence and inference separation.
- [ ] Layout docs list only implemented renderer identifiers.
- [ ] `docs/release-notes-v0.3.0.md` is current.

## GitHub Surface

- [ ] Description: `Evidence-grounded editable technical route diagrams for research and engineering projects.`
- [ ] Topics include `agent-skill`, `technical-route`, `research-diagram`, `engineering-diagram`, `pptx`, `svg`, `drawio`, `mermaid`, `academic-writing`, `ai-agents` and `workflow`.
- [ ] README banner, Gallery links and Draw.io URL render correctly.
- [ ] GitHub Actions pass on `main`.
- [ ] Create tag `v0.3.0`.
- [ ] Publish title `v0.3.0 - Evidence Integrity And Reliable Rendering`.
- [ ] Use `docs/release-notes-v0.3.0.md` as release notes.
