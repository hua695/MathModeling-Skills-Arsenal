# Contributing

Report a concrete task, skill name, host environment, reproduction steps and expected versus observed behavior. Use synthetic or redistribution-permitted inputs. Remove credentials, private papers and personal paths before sharing.

For changes:

1. Read AGENTS.md and MEMORY.md; preserve skill names, licenses and unrelated edits.
2. Keep instructions scoped. Add a script only when deterministic execution helps the task.
3. Run `python scripts/check_repository.py`, the affected tests and any required external-tool checks.
4. Describe what changed, what was actually verified and any remaining limitation. Do not present workflow tests as competition-performance evidence.

The Actions workflow runs repository hygiene and affected Harness/MathorCup behavior tests. The full orchestrator release audit has separately documented blockers in [validation](docs/validation.md); a green focused workflow does not certify a stable release.

New examples should include source/data rights, runnable commands, expected artifacts and the meaning of any reported number. Label synthetic data and upstream artwork explicitly. Keep third-party LICENSE files with their resources.
