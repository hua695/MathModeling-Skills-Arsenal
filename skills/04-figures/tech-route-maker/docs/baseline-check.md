# Baseline Check

## Environment

- Date: 2026-07-02
- OS: Windows
- Python version: 3.8.2rc2
- Branch: `refactor/research-engineering-focus`

## Commands

### Compile scripts

Command:

```powershell
python -m py_compile scripts\*.py
```

Result: failed in PowerShell because the wildcard was passed literally to Python.

Notes:

- Error: `OSError: [Errno 22] Invalid argument: 'scripts\\*.py'`
- This is a command-shell compatibility issue, not a script syntax issue.

Command:

```powershell
Get-ChildItem scripts -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

Result: passed when Python was allowed to write `.pyc` files.

Notes:

- The same command failed in the restricted sandbox because `.pyc` writes were denied.
- It passed after rerunning with normal filesystem permissions.

### Validate examples

Commands:

```powershell
python scripts\validate_route.py examples\academic-paper-demo\outputs\tech-route.json
python scripts\validate_route.py examples\thesis-proposal-demo\outputs\tech-route.json
python scripts\validate_route.py examples\software-architecture-demo\outputs\tech-route.json
python scripts\validate_route.py examples\campaign-route-demo\outputs\tech-route.json
```

Result: passed.

Notes:

- Each command returned `Validation passed with 0 warning(s).`

### Render example

Command:

```powershell
python scripts\render_all.py examples\academic-paper-demo\outputs\tech-route.json baseline-render-academic --formats pptx,svg,drawio,html,markdown,json
```

Result: passed.

Notes:

- Generated `tech-route.pptx`
- Generated `tech-route.svg`
- Generated `tech-route.drawio`
- Generated `tech-route.html`
- Generated `TECH_ROUTE.md`
- Generated `tech-route.json`

## Issues Found

- [ ] PowerShell users should avoid `python -m py_compile scripts\*.py`; use `Get-ChildItem` or `compileall` instead.
- [ ] OneDrive-backed worktrees may deny `.pyc` cache writes inside restricted sandboxes.
- [ ] Existing schema validates old route files but does not yet require version, confidence, assumptions, unresolved questions, or structured quality reporting.
