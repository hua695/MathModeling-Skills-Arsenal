# Quick Start

## 1. Install The Skill

With GitHub CLI 2.96 or newer:

```bash
gh skill install Stephen-studying/tech-route-maker SKILL.md --agent codex --scope user
```

Replace `codex` with the target host. See [Agent compatibility](agent-compatibility.md).

## 2. Install The Local CLI

```bash
git clone https://github.com/Stephen-studying/tech-route-maker.git
cd tech-route-maker
python -m pip install -e .
trm doctor
```

## 3. Verify A Complete Demo

```bash
trm validate examples/academic-paper-demo/outputs/tech-route.json --strict
trm render examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs --formats pptx,svg,drawio,drawio-code,excalidraw,mermaid,html,markdown,json
python scripts/verify_outputs.py examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs
```

The strict command should report complete domain context, verified sources, 100% evidence coverage and 0% inferred coverage.

## 4. Start A New Route

```bash
trm ingest path/to/source-files --output-dir evidence-pack
trm init --preset academic-method --output work/tech-route.json --quality-report
```

Then:

1. Review `evidence-pack/source-manifest.json` and `EVIDENCE_PACK.md`.
2. Fill `work/source.md` and `work/tech-route.json` from authoritative evidence.
3. Confirm discipline, subfield, project type, research object, method family, constraints, metrics, target medium, formats, layout and style with the user.
4. Run `trm validate work/tech-route.json --strict`.
5. Render only after all final-quality blockers are resolved.

Use `trm render ... --allow-draft` only when the user explicitly wants an unfinished draft. Inferred nodes and unresolved questions must remain visible in the quality report and must not be presented as source evidence.

## Draw.io Copy Code

```bash
trm render examples/drawio-copy-code-demo/outputs/tech-route.json examples/drawio-copy-code-demo/outputs --formats drawio,drawio-code,svg,json
```

Open [diagrams.net / draw.io](https://app.diagrams.net/), create a blank diagram, choose **Extras > Edit Diagram**, paste all text from `tech-route.drawio-code.xml`, and confirm. The resulting cells remain editable.

## Manual Review

Generated PPTX, SVG and Draw.io files are editable drafts, not finished submission figures. Review facts, terminology, evidence, route logic, wording, colors, spacing, font sizes and target-template requirements before formal use.
