# Agent Compatibility

`tech-route-maker` uses one canonical workflow: `SKILL.md` plus `tech-route.json`. Agent-specific files only point the host back to that workflow.

## Preferred Installation: GitHub CLI

GitHub CLI 2.96 or newer can install the root skill into many agent hosts. The explicit `SKILL.md` argument is important because this repository keeps the skill at its root.

```bash
gh skill install Stephen-studying/tech-route-maker SKILL.md --agent codex --scope user
```

Common agent values:

| Host | `--agent` value |
|---|---|
| Codex | `codex` |
| Claude Code | `claude-code` |
| Cursor | `cursor` |
| Gemini CLI | `gemini-cli` |
| GitHub Copilot | `github-copilot` |
| Cline | `cline` |
| OpenCode | `opencode` |
| Windsurf | `windsurf` |
| Qwen Code | `qwen-code` |

Use `--scope user` to make the skill available across projects, or `--scope project` to install it only for the current repository. Run `gh skill install --help` for the current complete agent list. If GitHub CLI requests authentication, run `gh auth login` first.

## Local Or Generic Installation

For a local clone:

```bash
gh skill install . SKILL.md --from-local --agent codex --scope user
```

For a host that is not supported by GitHub CLI, provide its skill parent directory explicitly:

```bash
python scripts/install_agent_skill.py --target /path/to/agent/skills --agent custom-agent
```

Windows PowerShell wrapper:

```powershell
.\install.ps1 -Target "C:\path\to\agent\skills" -Agent "custom-agent"
```

Unix wrapper:

```bash
./install.sh /path/to/agent/skills custom-agent
```

The fallback installer copies files, skips repository metadata and generated scratch output, and never guesses an agent's private directory. Use `--dry-run` before installation or `--update` to refresh an existing copy.

## Repository Adapters

| Agent environment | Discovery file |
|---|---|
| Codex / OpenAI-style skills | `SKILL.md`, `agents/openai.yaml` |
| Generic coding agents | `AGENTS.md` |
| Claude-style context | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md`, `.gemini/settings.json` |
| Cursor | `.cursor/rules/tech-route-maker.mdc` |
| GitHub Copilot coding agent | `.github/copilot-instructions.md` |
| Aider-style agents | `.aider.conf.yml` |

## Required Agent Behavior

Every compatible agent must:

1. Read `SKILL.md`.
2. Inspect source evidence without executing untrusted code.
3. Confirm missing domain and delivery choices instead of guessing them.
4. Build `tech-route.json` with source IDs, SHA-256 hashes and evidence locators.
5. Run strict validation before final rendering.
6. Keep inferred nodes and unresolved questions out of final outputs.
7. Render only selected editable formats.
8. Tell the user that generated files require manual factual and visual revision.

---

# Agent 兼容性

推荐使用 GitHub CLI 安装：

```bash
gh skill install Stephen-studying/tech-route-maker SKILL.md --agent codex --scope user
```

把 `codex` 替换为 `claude-code`、`cursor`、`gemini-cli`、`github-copilot` 等目标软件。没有内置支持时，使用通用安装器并明确提供技能父目录；不要让安装脚本猜测不同软件的私有路径。
