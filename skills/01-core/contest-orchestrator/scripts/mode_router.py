#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Select one contest-orchestrator mode before loading mode-specific guidance.

This command is read-only. It emits a JSON routing decision and never opens a
mode file, changes a project, or starts a contest stage.
"""
from __future__ import annotations

import argparse
import json
import sys


MODE_FILES = {
    "full-contest-legacy": "references/modes/full-contest-legacy.md",
    "full-contest-4-18": "references/modes/full-contest-4-18.md",
    "full-contest-harness": "references/modes/full-contest-harness.md",
    "full-contest-mathorcup": "references/modes/full-contest-mathorcup.md",
    "subproblem": "references/modes/subproblem.md",
    "paper": "references/modes/paper.md",
    "figures": "references/modes/figures.md",
    "delivery-audit": "references/modes/delivery-audit.md",
    "skills-optimization": "references/modes/skills-optimization.md",
}

DESCRIPTIONS = {
    "full-contest": "全流程竞赛模式；必须继续选择一种全流程子模式。",
    "full-contest-legacy": "兼容旧流程：按既有 A–G 阶段执行，不启用新增节点。",
    "full-contest-4-18": "已确认的 4.18 稳定节点流程：使用既定 G0–G6 协作门。",
    "full-contest-harness": "Harness 半自动流程：使用 H0–H9；4.18 稳定版，含绑定契约与节点暂停点。",
    "full-contest-mathorcup": "MathorCup 大数据竞赛：M1–M5 数据与实验主线、固定角色和逐节点人工确认。",
    "subproblem": "只处理指定小问及直接依赖，不自动扩展为全文交付。",
    "paper": "只处理论文内容、结构、排版或论文审阅，不重新建模。",
    "figures": "只处理图表规划、生成与来源登记；生成后由用户做视觉确认。",
    "delivery-audit": "只读交付审计，不修改被审计项目。",
    "skills-optimization": "只维护、验证和优化技能规则，不执行竞赛求解。",
}

ALIASES = {
    "full_contest": "full-contest",
    "full-contest-mode": "full-contest",
    "全流程竞赛": "full-contest",
    "全流程竞赛模式": "full-contest",
    "legacy": "full-contest-legacy",
    "4.18": "full-contest-4-18",
    "4.18rc": "full-contest-4-18",
    "full-contest-4-18rc": "full-contest-4-18",
    "harness": "full-contest-harness",
    "mathorcup": "full-contest-mathorcup",
    "mathorcup大数据": "full-contest-mathorcup",
    "大数据竞赛": "full-contest-mathorcup",
    "半自动竞赛": "full-contest-harness",
    "半自动竞赛模式": "full-contest-harness",
    "子问题": "subproblem",
    "论文": "paper",
    "图表": "figures",
    "交付审计": "delivery-audit",
    "技能优化": "skills-optimization",
    "全部": "all",
}

FULL_CONTEST_CHOICES = [
    "full-contest-legacy",
    "full-contest-4-18",
    "full-contest-harness",
    "full-contest-mathorcup",
]


def normalize(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip().lower()
    return ALIASES.get(value, value)


def route(mode: str | None = None, variant: str | None = None) -> dict:
    selected = normalize(mode)
    selected_variant = variant.strip().lower() if variant else None
    if selected is None:
        return {
            "status": "ASK_USER",
            "reason": "必须先选择工作模式；未选择前不读取任何模式文件。",
            "active_mode": None,
            "execution_allowed": False,
            "choices": list(DESCRIPTIONS),
            "descriptions": DESCRIPTIONS,
            "read_files": [],
        }
    if selected == "all":
        return {
            "status": "COMPARE_ONLY",
            "reason": "全部模式仅用于并列阅读、比较或审计；执行前仍需确定一个 active_mode。",
            "active_mode": None,
            "execution_allowed": False,
            "choices": list(DESCRIPTIONS),
            "descriptions": DESCRIPTIONS,
            "read_files": list(MODE_FILES.values()),
        }
    if selected == "full-contest":
        if selected_variant:
            direct_variant = normalize(selected_variant)
            selected = direct_variant if direct_variant in FULL_CONTEST_CHOICES else normalize(
                f"full-contest-{selected_variant}"
            )
        else:
            return {
                "status": "ASK_USER",
                "reason": "全流程竞赛模式必须明确选择一个子模式。",
                "active_mode": None,
                "execution_allowed": False,
                "choices": FULL_CONTEST_CHOICES,
                "descriptions": {key: DESCRIPTIONS[key] for key in FULL_CONTEST_CHOICES},
                "read_files": [],
            }
    if selected not in MODE_FILES:
        raise ValueError(f"未知模式: {mode}")
    return {
        "status": "READY",
        "reason": "已选择唯一 active_mode；只读取该模式文件，其他模式文件保持未加载。",
        "active_mode": selected,
        "execution_allowed": True,
        "choices": [selected],
        "descriptions": {selected: DESCRIPTIONS[selected]},
        "read_files": [MODE_FILES[selected]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", default=None)
    parser.add_argument("--variant", default=None)
    args = parser.parse_args()
    try:
        payload = route(args.mode, args.variant)
    except ValueError as exc:
        payload = {
            "status": "ERROR",
            "reason": str(exc),
            "active_mode": None,
            "execution_allowed": False,
            "choices": list(DESCRIPTIONS),
            "descriptions": DESCRIPTIONS,
            "read_files": [],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 2 if payload["status"] == "ASK_USER" else 0


if __name__ == "__main__":
    raise SystemExit(main())
