## Description: <br>
Captures learnings, errors, corrections, and feature requests in local markdown logs so agents can improve future work. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[pskoett](https://clawhub.ai/user/pskoett) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and AI coding-agent users use this skill to capture corrections, command failures, knowledge gaps, and feature requests as local markdown entries that can be reviewed, resolved, or promoted into durable project guidance. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Persistent learning files can accidentally capture secrets, private keys, raw transcripts, environment variables, or full command output. <br>
Mitigation: Log only short, sanitized summaries by default and redact sensitive values before writing to .learnings/ files. <br>
Risk: Optional hook scripts can add reminders broadly or inspect command output for error patterns when enabled. <br>
Mitigation: Review hook scripts before enabling them, prefer project-level or activator-only configuration, and avoid global hooks unless reminders are intended in every session. <br>
Risk: Cross-session sharing can expose sensitive context if raw transcripts or command output are forwarded. <br>
Mitigation: Use cross-session sharing only in trusted environments and send concise sanitized summaries plus relevant file paths instead of raw transcripts. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/pskoett/skills/self-improving-agent) <br>
- [OpenClaw Integration](references/openclaw-integration.md) <br>
- [Hook Setup Guide](references/hooks-setup.md) <br>
- [Entry Examples](references/examples.md) <br>
- [Agent Skills Specification](https://agentskills.io/specification) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with inline shell commands, configuration snippets, and local markdown file templates] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces local .learnings/ entries and optional hook reminders; users should review entries before promotion or reuse.] <br>

## Skill Version(s): <br>
3.0.24 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
