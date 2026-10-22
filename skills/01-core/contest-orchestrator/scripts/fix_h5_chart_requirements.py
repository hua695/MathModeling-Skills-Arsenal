#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 H5 描述中补充图表需求清单的约束说明"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\references\modes\full-contest-harness.md")
content = file.read_text(encoding="utf-8")

old = "图表需求清单（`chart_requirements.yaml`）和 `paper_narrative.yaml`"
new = "图表需求清单（`chart_requirements.yaml`，只定义正文主张、图号占位、目标小问、所需结果字段和 argument_goal，不定义数据图图型、视觉编码或版式）和 `paper_narrative.yaml`"

if old in content:
    content = content.replace(old, new)
    file.write_text(content, encoding="utf-8")
    print("✓ H5 描述中已补充图表需求清单约束说明")
else:
    print("✗ 未找到匹配")
