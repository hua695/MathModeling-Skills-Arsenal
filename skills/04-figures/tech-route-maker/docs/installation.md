# Installation

`tech-route-maker` can be used as a skill folder, a repository context, or a normal local rendering toolkit.

## GitHub CLI Skill Installation

GitHub CLI 2.96 or newer installs the root skill into a selected host:

```bash
gh skill install Stephen-studying/tech-route-maker SKILL.md --agent codex --scope user
```

Replace `codex` with `claude-code`, `cursor`, `gemini-cli`, `github-copilot`, or another value shown by `gh skill install --help`. See [Agent compatibility](agent-compatibility.md).

## Manual Codex / OpenAI-Style Installation

Place the repository folder under the agent's skills directory:

```text
skills/
  tech-route-maker/
    SKILL.md
    agents/openai.yaml
    scripts/
    references/
    examples/
```

Then ask:

```text
Use $tech-route-maker to create an editable technical route diagram from my source.
```

## Generic Agent Context

Open the repository root in the agent. The agent should read:

- `AGENTS.md`
- `SKILL.md`
- relevant files under `references/`

## Claude, Gemini, Cursor, Copilot, Aider

Use the adapter files already included in the repository:

- `CLAUDE.md`
- `GEMINI.md`
- `.gemini/settings.json`
- `.cursor/rules/tech-route-maker.mdc`
- `.github/copilot-instructions.md`
- `.aider.conf.yml`

## Local Rendering Toolkit

Use the backward-compatible scripts without package installation:

```bash
python scripts/validate_route.py <route-json>
python scripts/render_all.py <route-json> <output-dir> --formats pptx,svg,drawio,drawio-code,html,markdown,json
```

Or install the local CLI:

```bash
pip install -e .
trm doctor
trm ingest source-files --output-dir evidence-pack
trm validate examples/academic-paper-demo/outputs/tech-route.json --strict
trm render examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs --formats pptx,svg,drawio,drawio-code,excalidraw,mermaid,html,markdown,json
```

## Output Reminder

Rendered diagrams are editable drafts. Users should revise the PPTX, SVG, Draw.io or imported Draw.io XML outputs before academic submission, defense use, course delivery or engineering handoff.
