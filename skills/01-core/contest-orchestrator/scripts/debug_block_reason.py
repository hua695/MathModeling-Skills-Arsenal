#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""撤销临时恢复的 H4 状态设置，并打印 BLOCK 原因"""
from pathlib import Path
import sys
sys.path.insert(0, r"C:\Users\USER\.agents\skills\contest-orchestrator\scripts")
import tempfile
import yaml
from pathlib import Path as P

# 撤销临时恢复
file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\tests\test_harness_control.py")
content = file.read_text(encoding="utf-8")
old = '            payload["nodes"]["H3"]["status"] = "approved"\n            payload["nodes"]["H4"]["status"] = "approved"  # H4已并入H5，但状态历史校验需要\n            payload["harness_run_id"]'
new = '            payload["nodes"]["H3"]["status"] = "approved"\n            payload["harness_run_id"]'
if old in content:
    content = content.replace(old, new)
    file.write_text(content, encoding="utf-8")
    print("✓ 已撤销临时恢复")

# 打印 BLOCK 原因
import check_harness_control as checker
with tempfile.TemporaryDirectory() as raw:
    root = P(raw)
    control = root / ".contest" / "harness_control.yaml"
    reviews = root / ".contest" / "reviews"
    reviews.mkdir(parents=True)
    (root / "problem_statement.md").write_text("题面预载", encoding="utf-8")
    (root / "unified_problem_package.yaml").write_text("subproblems: [Q1]", encoding="utf-8")
    (root / "original_problem.pdf").write_bytes("原始题面内容".encode("utf-8"))
    payload = checker.default_control()
    payload["problem_scope"] = {"subproblems": ["Q1"]}
    payload["solver_instance_id"] = "solver-001"
    payload["nodes"]["H3"]["status"] = "approved"
    payload["harness_run_id"] = "run-20260831-001"
    payload["bootstrap"]["invocations"] = [
        {"skill": "superpowers:using-superpowers", "task_id": "H0-bootstrap", "purpose": "bootstrap",
         "completed": True, "status": "completed", "created": ["H1"], "agent_ids": {"H1": "H1-agent-01"}},
        {"skill": "superpowers:using-superpowers", "task_id": "sp-spawn-001", "purpose": "spawn_roles",
         "completed": True, "status": "completed", "after_node": "H1",
         "created": ["H5", "H6", "H7", "H8"],
         "agent_ids": {"H5": "H5-agent-01", "H6": "H6-agent-01", "H7": "H7-agent-01", "H8": "H8-agent-01"}},
    ]
    control.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    report = checker.check_harness_control(root, through="H2")
    print(f"\n状态: {report['status']}")
    print(f"\nFailures ({len(report.get('failures', []))}):")
    for f in report.get("failures", [])[:10]:
        print(f"  - {f}")
    print(f"\nMissing ({len(report.get('missing', []))}):")
    for m in report.get("missing", [])[:10]:
        print(f"  - {m}")
