#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
init_b_project.py — B 题（优化决策类）项目初始化工具

从 templates/b_project_template/ 复制配置模板到新项目目录，
自动填充项目名称、日期等基本信息，生成 README。

用法:
  python scripts/init_b_project.py <项目目录> [--name "项目名称"] [--date "2026-09-XX"]

示例:
  python scripts/init_b_project.py "C:\Users\me\Workspace\2026国赛B题" --name "2026国赛B题"
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_ROOT / "templates" / "b_project_template"


def init_project(project_dir: Path, name: str | None = None, date: str | None = None) -> dict:
    """从模板初始化 B 题项目"""
    if not TEMPLATE_DIR.exists():
        raise RuntimeError(f"模板目录不存在: {TEMPLATE_DIR}")

    project_dir = project_dir.resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    project_name = name or project_dir.name
    project_date = date or datetime.now().strftime("%Y-%m-%d")

    # 复制模板文件
    copied = []
    for src in TEMPLATE_DIR.rglob("*"):
        if src.is_file():
            rel = src.relative_to(TEMPLATE_DIR)
            dst = project_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(str(rel))
        elif src.is_dir():
            # rglob 只产出文件项，空目录需显式创建，否则 paper/ 与 figures/ 会丢失
            (project_dir / src.relative_to(TEMPLATE_DIR)).mkdir(parents=True, exist_ok=True)

    # 替换模板中的占位符
    placeholders = {
        "PLACEHOLDER_PROJECT_NAME": project_name,
        "PLACEHOLDER_DATE": project_date,
        "2026-09-XX": project_date,
    }

    replaced = 0
    for yaml_file in project_dir.rglob("*.yaml"):
        try:
            text = yaml_file.read_text(encoding="utf-8")
            for old, new in placeholders.items():
                if old in text:
                    text = text.replace(old, new)
                    replaced += 1
            yaml_file.write_text(text, encoding="utf-8")
        except Exception:
            pass

    # 重算任务卡 SHA-256：占位符替换改变了任务卡内容，模板预置的哈希随之失效
    control_path = project_dir / ".contest" / "harness_control.yaml"
    if yaml is not None and control_path.is_file():
        try:
            control = yaml.safe_load(control_path.read_text(encoding="utf-8")) or {}
            control_text = control_path.read_text(encoding="utf-8")
            for record in control.get("dispatch_records") or []:
                if not isinstance(record, dict):
                    continue
                card_rel = record.get("task_card_path")
                old_sha = record.get("task_card_sha256")
                if not card_rel or not old_sha:
                    continue
                card_path = project_dir / card_rel
                if not card_path.is_file():
                    continue
                new_sha = hashlib.sha256(card_path.read_bytes()).hexdigest()
                if new_sha != old_sha:
                    control_text = control_text.replace(old_sha, new_sha)
            control_path.write_text(control_text, encoding="utf-8")
        except Exception:
            pass

    # 生成 README
    readme = f"""# {project_name}

B 题（优化决策类）数学建模项目，基于 contest-orchestrator skill 模板初始化。

## 项目结构

```
{project_dir.name}/
├── .contest/                    # 主控配置
│   ├── harness_control.yaml     # 节点状态、dispatch_records
│   ├── approval_log.yaml        # 用户批准日志
│   ├── status_history.yaml      # 状态转移历史
│   ├── reviews/                 # 各节点审查包（H2-H9）
│   └── task_cards/              # 各节点任务卡（H1, H5-H8）
├── paper/                       # 论文素材
├── figures/                     # 图表
├── results/                     # 结果文件
│   ├── input_manifest.yaml      # H9 输入清单
│   └── sensitivity_report.yaml  # 灵敏度/鲁棒性报告
├── run_manifest.yaml             # H5 可复现运行、正式记录与结果哈希
├── problem_profile.yaml         # 题型画像
├── model_blueprint.yaml         # 模型蓝图
├── model_contract.yaml          # 模型契约
├── validation_contract.yaml     # 验证契约
├── h6_verification_scope.yaml   # H6 验证范围卡
├── appendix_plan.yaml            # H8 附录覆盖与双层代码计划
├── paper_material_readiness.yaml # 论文素材准入
├── result_interpretation_cards.yaml # H5 核心结果解释卡
├── model_summary_cards.yaml      # H5→H6→H8 最终求解模型卡
├── paper_argument_blueprint.yaml # H8 论证蓝图
├── paper_author_brief.yaml       # H8 作者简报
├── chapter_writing_card.yaml     # H8 当前章节写作卡
├── paper_continuity_context.yaml # H8 轻量全文连续性包
├── evidence_gap_matrix.yaml     # 证据缺口矩阵
├── global_interface_check.yaml  # 全局接口检查
├── paper_claim_coverage.yaml    # 主张覆盖表
├── paper_narrative.yaml         # 论文叙事蓝图
├── visual_argument_plan.yaml    # H7 读者优先视觉论证计划
├── visual_evidence_packet.yaml  # H5→H6→H7 轻量视觉证据单元包
└── figure_registry.yaml         # 图表登记
```

## 快速开始

1. **题意理解（H1）**：填写 problem_statement.md，运行 check_problem_coverage.py
2. **建模与求解（H2-H5，H4已并入H5）**：阶段一填写 model_blueprint.yaml、model_contract.yaml、chart_requirements.yaml；阶段二-四运行 pyomo 或 heuristic-algorithms，生成 run_manifest.yaml 与 sensitivity_report.yaml，并运行 check_h5_result_traceability.py --strict
3. **验证（H6）**：填写 h6_verification_scope.yaml、validation_contract.yaml、global_interface_check.yaml，并核验 visual_evidence_packet.yaml；普通正文、排版和图表美化不派发 H6
4. **图表（H7）**：读取经 H6 核验的 visual_evidence_packet.yaml；由 H7 图表 agent 生成带 figure_intent、template_id、visible_element_map 和 canvas_profile 的 visual_argument_plan.yaml，提交 H7_visual_plan_review_packet.yaml 并取得 approval_log.yaml 中 H7_VISUAL_PLAN 的用户批准；流程图/TikZ 图必须从 contest starter catalog 选择并复制 starter，登记 starter_source、template_sha256、template_fixture 和 visual_qa；数据结果图登记 ModelViz 的实际模板 ID 与源哈希；最后写入 figure_registry.yaml
5. **论文（H8）**：由 academic-writing 生成论证蓝图、作者简报和问题引入/双小节结构；论文 agent 读取经 H6 核验的 model_summary_cards.yaml，依据 chapter_writing_card.yaml 和 paper_continuity_context.yaml 逐章写作
6. **交付（H9）**：运行 check_harness_control.py --through H9

## 检查命令

```bash
# 全流程检查
python scripts/check_harness_control.py <项目目录> --through H9

# 题目条件覆盖检查
python scripts/check_problem_coverage.py <项目目录>

# 题型画像路由
python scripts/route_problem_profile.py <项目目录>
```

## 注意事项

- 所有 YAML 文件中的 SHA256 哈希需要在文件创建后重新计算
- user_approval 需要在每个节点审查包修改后重新获得用户批准
- B 题（优化决策类）必须包含灵敏度/鲁棒性报告（P0-02 硬门禁）
- 详细配置说明见 contest-orchestrator/references/b_project_gotchas.md

初始化日期: {project_date}
"""
    (project_dir / "README.md").write_text(readme, encoding="utf-8")

    return {
        "project_dir": str(project_dir),
        "project_name": project_name,
        "project_date": project_date,
        "files_copied": len(copied),
        "placeholders_replaced": replaced,
        "status": "success",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="B 题（优化决策类）项目初始化工具")
    parser.add_argument("project_dir", help="新项目目录路径")
    parser.add_argument("--name", default=None, help="项目名称（默认使用目录名）")
    parser.add_argument("--date", default=None, help="项目日期（默认今天，格式 YYYY-MM-DD）")
    args = parser.parse_args()

    try:
        result = init_project(Path(args.project_dir), args.name, args.date)
        print(f"=== B 题项目初始化完成 ===")
        print(f"  项目目录: {result['project_dir']}")
        print(f"  项目名称: {result['project_name']}")
        print(f"  项目日期: {result['project_date']}")
        print(f"  复制文件: {result['files_copied']} 个")
        print(f"  替换占位符: {result['placeholders_replaced']} 处")
        print(f"\n下一步: 阅读 {result['project_dir']}/README.md")
        return 0
    except Exception as exc:
        print(f"初始化失败: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
