#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run isolated contract replays for mechanistic, optimization, and prediction profiles.

The replay writes only to a temporary directory (or an explicitly supplied
report path).  It exercises scope planning, typed blueprints, evidence and
derivation contracts, symbol/interface checks, and the abstract provenance
gate.  It is intentionally independent of any live contest project.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from capture_run import make_manifest

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

PROFILES = {
    "mechanistic": {
        "family": "mechanistic", "primary": "mechanistic",
        "body": "机理映射与公式推导说明守恒关系，解析路线与数值路线进行交叉验证。",
        "evidence": "mechanism_mapping: {status: pass, text_anchors: ['机理映射']}\n      formula_derivation: {status: pass, text_anchors: ['公式推导']}",
    },
    "optimization": {
        "family": "optimization", "primary": "optimization",
        "body": "决策变量、目标函数和约束条件构成优化模型，采用整数求解器进行可行性检查。",
        "evidence": "decision_variables: {status: pass, text_anchors: ['决策变量']}\n      objective: {status: pass, text_anchors: ['目标函数']}\n      constraints: {status: pass, text_anchors: ['约束条件']}\n      feasibility_check: {status: pass, text_anchors: ['可行性检查']}",
    },
    "prediction": {
        "family": "prediction", "primary": "prediction",
        "body": "数据预处理后划分训练集、验证集和测试集，以统计基线与机器学习模型比较 RMSE 和 MAE。",
        "evidence": "preprocessing: {status: pass, text_anchors: ['数据预处理']}\n      data_split: {status: pass, text_anchors: ['训练集']}\n      baseline: {status: pass, text_anchors: ['基线']}\n      metrics: {status: pass, text_anchors: ['RMSE']}",
    },
}


def run(command: list[str], cwd: Path) -> dict:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    return {"command": command, "returncode": result.returncode,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "tail": ((result.stdout or "") + ("\n" + result.stderr if result.stderr else ""))[-1600:]}


def write_fixture(root: Path, name: str) -> None:
    cfg = PROFILES[name]
    (root / "paper").mkdir(parents=True)
    (root / "results").mkdir()
    (root / "problem.pdf").write_bytes(b"isolated replay input")
    (root / "problem_condition_ledger.yaml").write_text(
        """schema_version: '1.0'
source_file: problem.pdf
title_anchor: isolated replay problem
source_units:
  - id: C-01
    source_location: p1
    source_text: 题目输入数据映射到输出目标和变量。
    roles: [given, task]
    normalized_meaning: 输入数据与输出变量对应
    affected_questions: [Q1]
    downstream_evidence: [variables, constraints, result]
    link_type: supplies
    evidence_level: confirmed
    status: mapped
questions:
  - id: Q1
    source_unit_ids: [C-01]
    inputs: [raw_data.csv]
    task: 建立并求解题目模型
    outputs: [results/q1_results.json]
    reused_by: []
unresolved_conditions: []
""", encoding="utf-8")
    (root / "results" / "q1_results.json").write_text(
        json.dumps({"score": 0.85, "error": 3.2, "improvement_percent": 12.5}, ensure_ascii=False), encoding="utf-8")
    (root / "results" / "sensitivity_result.json").write_text(
        json.dumps({"parameter_pm5_percent": 5, "stable": True}, ensure_ascii=False), encoding="utf-8")
    abstract = (
        "本文针对一个包含多个子任务的研究问题，先将题目条件拆解为问题一和问题二，明确输入、输出和评价目标。\n\n"
        "在关键假设下完成缺失值检查、异常值处理和单位统一，并说明这些简化可能造成的边界误差。"
        "随后分别建立与题目条件对应的模型，使用算法和 Python 求解工具得到可复现结果。"
        "数据来源、变量定义、参数边界和求解步骤均记录在结果文件中，避免将示例数值误写成真实结果。"
        "摘要中的方法描述与正文模型建立章节逐项对应，先说明问题条件，再给出模型选择、算法流程和结果解释。"
        "对于不同子任务，分别说明输入数据、输出指标、参数范围和验证方式，使读者能够根据摘要定位正文证据。\n\n"
        f"问题一采用{cfg['body']}问题二采用对照模型，主要结果为准确率 0.85、误差 3.2、提升 12.5%，"
        "结果来源于 results/q1_results.json。为便于复核，摘要只保留与表格一致的关键数值，并明确每个数值的含义和单位。\n\n"
        "通过项目敏感性计划声明的参数扰动、误差分析和稳定性检验确认结论边界。综合来看，该模型可用于题目场景下的方案比较和决策支持，"
        "但在数据分布超出当前范围时需要重新校准，适用价值由实际结果而不是空泛评价决定。该结论仅适用于题目给定的数据范围，"
        "若输入分布或约束发生变化，应重新运行模型和检验流程后再作决策。"
    )
    tex = (
        "\\begin{abstract}\n" + abstract + "\n\\end{abstract}\n"
        "\\noindent\\textbf{关键词：} 机理模型；优化算法；数据预处理；稳健性分析\n"
        "\\section{符号说明}\n全局符号、含义、单位和变量类型统一登记。\n"
        "\\section{模型建立与求解}\n\\subsection{问题一：模型求解}\\label{subproblem:Q1}\n"
        "本问围绕题目给定数据与约束建立可计算模型，重点回答输入如何映射到输出目标，"
        "并说明本问结果与后续检验之间的联系。\n"
        "\\subsubsection{模型建立}\n"
        "\\textbf{数据处理：}题目输入数据映射到输出目标和变量。假设样本连续，简化会带来边界误差，适用范围限定在给定数据。"
        "符号变量参数及其单位和范围见表1。\\begin{tabular}{llll}\\toprule 符号 & 含义 & 单位 & 类型 \\\\ \\midrule x & 状态 & 1 & state \\\\ \\bottomrule\\end{tabular}。"
        "\\textbf{模型的建立：}候选路线包括解析路线、数值路线和仿真方案，最终选择数值路线，"
        "不采用解析路线的技术依据是本题关系具有非线性。"
        f"{cfg['body']}改进了本题数据下的边界处理。"
        "由题目关系得到变量、目标函数与约束表达。原始关系式描述基础状态；原始式反映基础关系。"
        "\\begin{equation}x=1\\label{eq:q1_00}\\end{equation}\n"
        "由基础关系推导目标关系，得到中间表达式；整理步骤体现边界约束。"
        "\\begin{equation}y=x+1\\label{eq:q1_01}\\end{equation}\n"
        "整理式将边界条件代入，代入边界条件得到结果，最终公式对应输出目标；最终式表示输出目标。"
        "\\begin{equation}z=y+1\\label{eq:q1_02}\\end{equation}\n"
        "综合上述关系，\\textbf{最终求解模型：}\n"
        "\\begin{equation}\\mathcal{M}:\\quad x=1,\\quad y=x+1,\\quad z=y+1\\end{equation}\n"
        "模型中的变量、参数、约束和公式来源与模型契约及代码接口保持一致。\n"
        "\\subsubsection{模型求解与结果分析}\n"
        "\\textbf{模型的求解：}算法选择基于题目约束，初值来自网格搜索，搜索范围受约束处理，"
        "终止条件为收敛容差，并用多起点处理局部最优。求解流程为初值、搜索、约束处理和收敛判断。"
        "数据处理结果已用于模型输入，变量单位和边界保持一致；中间结果包括粗估计和表2的可行性检查。"
        "结果来源为 results/q1_results.json 和求解器输出，主结果见表3。"
        f"{cfg['body']}的结果支持本题数据下的边界处理。"
        "\\textbf{结果分析：}主结果表明，该方案在给定数据范围内满足目标并支持方案比较。"
        "敏感性和扰动分析、残差、置信区间以及交叉验证共同评估稳定性和不确定性。"
        "中文文献依据给出了方法先例；本文改进了本题数据下的边界处理。"
        "模型检验与灵敏度分析表明结论边界清晰，结果可在给定条件下复核。\n"
        "\\section{参考文献}\n\\bibliography{ref}\n"
        "\\appendix\n\\section{附录A 长推导}\n长推导内容见 long_derivation.md。\n"
        "\\begin{table}[ht]\\caption{样本数据}\\label{tab:A-1}\\end{table}\n"
        "\\section{附录B 核心代码}\n\\setmonofont{Consolas}\n\\definecolor{codebg}{gray}{0.96}\n"
        "\\usemintedstyle{vs}\n\\medskip\n"
        "\\begin{minted}[bgcolor=codebg,linenos,breaklines,tabsize=4,fontsize=\\small,framesep=6pt]{python}\n"
        "# 功能：核心计算；输入：数据；输出：结果\nprint(1)\n\\end{minted}\n\\medskip\n"
        "\\section{附录C 支撑材料}\n支撑材料文件清单：solve.py。\\par 编译必须开启 -shell-escape，依赖 Pygments。\n"
    )
    (root / "paper" / "paper.tex").write_text(tex, encoding="utf-8")
    (root / "model_assumptions.md").write_text("假设样本连续；简化离散噪声，边界误差由敏感性分析评估。\n", encoding="utf-8")
    (root / "symbol_table.md").write_text("| x | 状态变量 | 1 | state |\n", encoding="utf-8")
    (root / "solve.py").write_text(
        "# Replay calculation fixture: input data to verified result metrics.\n"
        "RESULTS = {'score': 0.85}\n",
        encoding="utf-8")
    (root / "q1_config.json").write_text(json.dumps({"convergence_tolerance": 1e-6}), encoding="utf-8")
    (root / "long_derivation.md").write_text("真实长推导输入。\n", encoding="utf-8")
    (root / "raw_data.csv").write_text("x,value\n1,42\n2,43\n", encoding="utf-8")
    (root / "appendix_contract.yaml").write_text(
        """schema_version: '1.0'
required_appendix_ids: [A, B, C]
source_inputs:
  program_used: true
  full_source_files: [solve.py]
  long_derivation_files: [long_derivation.md]
  raw_data_files: [raw_data.csv]
  support_material_files: [solve.py]
""", encoding="utf-8")
    (root / "modeling_solution_contract.yaml").write_text(
        "schema_version: '1.1'\ninput_gate:\n"
        "  problem_subquestions: [Q1]\n  assumptions_source: model_assumptions.md\n"
        "  variable_list_source: symbol_table.md\n  code_logic_sources: [solve.py]\n"
        "  code_debug_status: pass\n  result_authority: code_generated\n  allow_fabricated_numbers: false\n"
        "subproblems:\n  - id: Q1\n    text_anchor: '\\label{subproblem:Q1}'\n"
        "    assumption_anchor: '假设样本连续'\n    symbol_table_anchor: '符号变量参数及其单位'\n    symbols:\n"
        "      - {symbol: x, meaning: 状态变量, unit: 1, variable_type: state}\n"
        "      - {symbol: y, meaning: 中间变量, unit: 1, variable_type: intermediate}\n"
        "      - {symbol: z, meaning: 输出变量, unit: 1, variable_type: objective}\n"
        "    formula_chain:\n"
        "      - {id: f0, kind: original, label: eq:q1_00, source_anchor: '原始关系式描述基础状态', meaning_anchor: '原始式反映基础关系', symbols: [x]}\n"
        "      - {id: f1, kind: rearranged, label: eq:q1_01, source_anchor: '整理式将边界条件代入', derivation_anchor: '由基础关系推导目标关系', meaning_anchor: '整理步骤体现边界约束', derived_from: [f0], symbols: [x, y]}\n"
        "      - {id: f2, kind: final, label: eq:q1_02, source_anchor: '最终公式对应输出目标', derivation_anchor: '代入边界条件得到结果', meaning_anchor: '最终式表示输出目标', derived_from: [f1], symbols: [y, z]}\n"
        "    algorithm:\n      name: constrained_search\n      rationale_anchor: '算法选择基于题目约束'\n"
        "      software: [Python]\n      steps_anchor: '求解流程为初值、搜索、约束处理和收敛判断'\n      parameters:\n"
        "        - {name: convergence_tolerance, value: '1e-6', basis: '由题目精度要求与调试收敛曲线确定'}\n"
        "        - {name: initial_strategy, value: grid, basis: '由多起点运行证据确定'}\n"
        "    result_source_files: [results/q1_results.json]\n    numeric_results_policy: external_only\n",
        encoding="utf-8")
    import pymupdf
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "摘要\n关键词：机理模型；优化算法；数据预处理；稳健性分析", fontsize=10)
    pdf.save(str(root / "paper" / "paper.pdf"))
    pdf.close()
    (root / "model_blueprint.yaml").write_text(
        f"schema_version: '1.0'\nproject:\n  composition: single\n  expected_subproblems: [Q1]\n"
        f"subproblems:\n  - id: Q1\n    composition_mode: single\n    models:\n      - id: model_1\n        family: {cfg['family']}\n        modifiers: []\n",
        encoding="utf-8")
    (root / "model_contract.yaml").write_text(
        "schema_version: '2.1'\nevidence_quality: enhanced\nsubproblems:\n"
        "  - id: Q1\n    primary_capability: " + cfg["primary"] + "\n    capabilities: []\n    symbols:\n"
        "      - {name: x, meaning: 状态变量, unit: 1, scope: global}\n    evidence:\n"
        "      problem_mapping: {status: pass, text_anchors: ['题目输入数据映射']}\n"
        "      assumptions: {status: pass, text_anchors: ['假设样本连续']}\n"
        "      symbols_units: {status: pass, text_anchors: ['符号变量参数及其单位']}\n"
        "      route_comparison: {status: pass, text_anchors: ['候选路线包括解析路线']}\n"
        "      algorithm_card: {status: pass, text_anchors: ['算法选择基于题目约束']}\n"
        "      intermediate_results: {status: pass, text_anchors: ['中间结果包括粗估计']}\n"
        "      literature_basis: {status: pass, text_anchors: ['中文文献依据给出了方法先例']}\n"
        "      innovation_delta: {status: pass, text_anchors: ['改进了本题数据下的边界处理']}\n"
        "      result_source: {status: pass, text_anchors: ['结果来源为'], source_files: ['results/q1_results.json']}\n"
        "      reliability: {status: pass, text_anchors: ['敏感性和扰动分析']}\n"
        "      " + cfg["evidence"] + "\n",
        encoding="utf-8")
    (root / "derivation_registry.yaml").write_text(
        "schema_version: '1.0'\nequations:\n"
        "  - {id: eq0, kind: definition, label: eq:q1_00}\n"
        "  - id: eq1\n    kind: derived\n    label: eq:q1_01\n    depends_on: [eq0]\n"
        "    assumptions: ['边界条件满足']\n    derivation_steps: ['由基础关系推导目标关系', '代入边界条件得到结果']\n"
        "  - id: eq2\n    kind: derived\n    label: eq:q1_02\n    depends_on: [eq1]\n"
        "    assumptions: ['边界条件满足']\n    derivation_steps: ['整理式将边界条件代入', '最终公式对应输出目标']\n",
        encoding="utf-8")
    (root / "interface_contract.yaml").write_text("schema_version: '1.0'\ninterfaces: []\n", encoding="utf-8")
    (root / "algorithm_manifest.yaml").write_text(
        "schema_version: '1.0'\nsubproblems:\n  - id: Q1\n    paper_anchor: '算法选择基于题目约束'\n"
        "    algorithm:\n      name: 数值路线\n      code_sources: [solve.py]\n      parameters:\n"
        "        - {name: convergence_tolerance, expected: 1.0e-6, source_file: q1_config.json, json_pointer: /convergence_tolerance}\n",
        encoding="utf-8")
    # Evidence sidecars: one run manifest and one numeric claim map.
    (root / "numeric_source_map.json").write_text(json.dumps({
        "schema_version": "1.0",
        "claims": [
            {"id": "claim:score", "value": 0.85, "source_file": "results/q1_results.json",
             "json_pointer": "/score", "text_anchor": "准确率 0.85"},
            {"id": "claim:error", "value": 3.2, "source_file": "results/q1_results.json",
             "json_pointer": "/error", "text_anchor": "误差 3.2"},
            {"id": "claim:improvement", "value": 12.5, "source_file": "results/q1_results.json",
             "json_pointer": "/improvement_percent", "text_anchor": "提升 12.5%"}
        ]
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_spec = {
        "run_id": f"run.{name}.001", "status": "completed",
        "command": {"argv": ["python", "solve.py", "--profile", name], "cwd": "."},
        "inputs": [{"path": "raw_data.csv", "evidence_id": "ev:input.raw"}],
        "code": [{"path": "solve.py", "evidence_id": "ev:code.solve"}],
        "configs": [{"path": "q1_config.json", "evidence_id": "ev:config.q1"}],
        "outputs": [{"path": "results/q1_results.json", "evidence_id": "ev:result.q1",
                     "source_ids": ["ev:input.raw", "ev:code.solve", "ev:config.q1"]}],
        "evidence": [{"evidence_id": "ev:claim.q1", "kind": "numeric_results",
                      "source_ids": ["ev:result.q1"], "claim": "摘要与正文数值来自结果文件"}],
        "seed": 7, "exit_code": 0
    }
    run_manifest = make_manifest(root, manifest_spec)
    manifest_path = root / ".contest" / "runs" / f"run.{name}.001" / "run_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replay(name: str, keep: bool = False) -> dict:
    raw = Path(tempfile.mkdtemp(prefix=f"contest_orchestrator_replay_{name}_"))
    write_fixture(raw, name)
    scripts = ROOT / "scripts"
    commands = [
        [PY, str(scripts / "scope_router.py"), "--scope", "FULL_CONTEST", "--workspace", str(raw),
         "--out", str(raw / "scope_plan.json")],
        [PY, str(scripts / "check_problem_coverage.py"), str(raw), "--strict", "--require-ledger"],
        [PY, str(scripts / "compile_model_blueprint.py"), str(raw), "--strict"],
        [PY, str(scripts / "check_model_evidence.py"), str(raw), "--strict"],
        [PY, str(scripts / "check_derivation_chain.py"), str(raw), "--strict"],
        [PY, str(scripts / "check_symbol_consistency.py"), str(raw), "--strict"],
        [PY, str(scripts / "check_interface_contract.py"), str(raw), "--strict"],
        [PY, str(scripts / "check_modeling_solution_contract.py"), str(raw), "--strict"],
        [PY, str(scripts / "check_algorithm_manifest.py"), str(raw), "--strict"],
        [PY, str(scripts / "check_dimension_consistency.py"), str(raw), "--strict"],
        [PY, str(scripts / "check_run_manifest.py"), str(raw), "--strict"],
        [PY, str(scripts / "check_stale_evidence.py"), str(raw), "--strict"],
        [PY, str(scripts / "audit_numeric_sources.py"), str(raw), "--paper", "paper/paper.tex",
         "--strict", "--require-map"],
        [PY, str(scripts / "check_abstract_contract.py"), str(raw / "paper"),
         "--project-root", str(raw), "--strict"],
        [PY, str(scripts / "check_paper_narrative.py"), str(raw / "paper"),
         "--strict"],
        [PY, str(scripts / "check_code_comments.py"), str(raw),
         "--strict"],
        [PY, str(scripts / "check_numerical_sanity.py"), str(raw),
         "--strict"],
        [PY, str(scripts.parent.parent / "academic-writing" / "scripts" / "style_check.py"), str(raw / "paper"),
         "--strict"],
        [PY, str(scripts / "check_latex_appendix_contract.py"), str(raw / "paper"),
         "--project-root", str(raw), "--strict"],
    ]
    results = [run(command, raw) for command in commands]
    passed = all(item["status"] == "PASS" for item in results)
    report = {"profile": name, "passed": passed, "root": str(raw), "steps": results}
    if not keep:
        shutil.rmtree(raw, ignore_errors=True)
        report["root"] = "<temporary replay removed>"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES), action="append")
    parser.add_argument("--strict", action="store_true", help="任一 profile 回放失败则返回非零")
    parser.add_argument("--keep", action="store_true", help="保留临时回放目录，便于人工检查")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    names = args.profile or list(PROFILES)
    reports = [replay(name, args.keep) for name in names]
    payload = {"schema_version": "1.0", "passed": all(item["passed"] for item in reports), "replays": reports}
    output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if payload["passed"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
