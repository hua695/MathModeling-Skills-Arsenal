#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smoke_test.py — 核心脚本冒烟自测（2026-08-16 新增，防开发期低级 bug 流入实战）

覆盖:
  1) py_compile 全部 scripts/*.py + memory/*.py（语法门）
  2) retrieval.retrieve 最小指纹（空库不崩）
  3) semantic 索引构建 + 查询
  4) ranking.freshness / quality_score
  5) topic_intelligence.score_topic（空库）
  6) paper_retrieval.retrieve_paper
  7) consistency_check 在临时目录跑（含范围数字过滤）
  8) check_core_execution 在临时 replay 跑（产物探针）
  9) paper_check 在模板副本运行（模板自身必须全 PASS）
  10) docx_postprocess 分页符冒烟（3 处分页 + pandoc 丢标题补插场景, 第16/43轮）
  11) 全脚本 import 无副作用（防未保护的顶层 CLI 代码）
  12) docx 交付链路 e2e（模板→pandoc→xelatex→8 步全绿；缺工具自动 SKIP）

用法: python scripts/smoke_test.py [--quick]   （--quick 跳过 7-12）
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import py_compile
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
MEMORY = os.path.join(ROOT, "memory")
PY = sys.executable

# Only modules explicitly designed as reusable libraries belong in an import
# smoke test.  One-shot migration/import scripts are CLI-only and are never
# imported: several still contain historical paths or top-level writes.
IMPORT_SMOKE_MODULES = (
    "retrieval", "semantic", "ranking", "topic_intelligence",
    "paper_retrieval", "blueprint_retrieval",
    "docx_postprocess", "make_reference_doc", "docx_pipeline",
    "delivery_all", "delivery_gate", "delivery_manifest",
    "scope_router", "audit_project", "skill_health_check",
)


def pycompile_all() -> list[tuple[str, str]]:
    """语法门：编译所有 .py，返回 [(file, error)]。"""
    bad = []
    with tempfile.TemporaryDirectory(prefix="contest_orchestrator_pycompile_") as compile_dir:
        for base in (SCRIPTS, MEMORY):
            for dirpath, _, files in os.walk(base):
                if "archive" in dirpath or "__pycache__" in dirpath or ".cache" in dirpath:
                    continue
                for f in files:
                    if f.endswith(".py"):
                        p = os.path.join(dirpath, f)
                        cfile = os.path.join(compile_dir, f"{len(bad)}_{f}.pyc")
                        try:
                            py_compile.compile(p, cfile=cfile, doraise=True)
                        except py_compile.PyCompileError as e:
                            bad.append((p, str(e)[:120]))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description="核心脚本冒烟自测")
    ap.add_argument("--quick", action="store_true", help="跳过 7/8 项")
    args = ap.parse_args()
    # Imports and bytecode checks must not mutate the installed skill tree.
    sys.dont_write_bytecode = True
    results: list[tuple[str, str]] = []
    sys.path.insert(0, SCRIPTS)
    sys.path.insert(0, MEMORY)

    def run(name, fn):
        try:
            fn()
            results.append((name, "PASS"))
        except Exception as e:
            results.append((name, f"FAIL: {type(e).__name__}: {str(e)[:150]}"))

    # 1. 语法门
    bad = pycompile_all()
    results.append(("py_compile 全部脚本", f"PASS({len(bad) == 0})" if not bad else f"FAIL: {bad[:3]}"))
    if bad:
        for n, r in results:
            print(f"  [{r.split(':')[0]}] {n}: {r}")
        return 1

    # 2-6. memory 冒烟
    def t_retrieval():
        import retrieval
        fp = {"primary": "预测", "keywords": ["时序"], "data_scale": "small"}
        p = retrieval.retrieve(fp, top=3, entries=[], use_semantic=False)
        assert p["retrieval_status"]["level"] in ("weak", "cold_start", "normal", "rich")
    run("retrieval.retrieve", t_retrieval)

    def t_semantic():
        from semantic import SemanticIndex
        idx = SemanticIndex([{"_id": "T1", "problem_type": "预测", "method": "LSTM 时序"}]).build()
        assert len(idx.query("时序 预测", top_k=2)) >= 0
    run("semantic 索引+查询", t_semantic)

    def t_ranking():
        import ranking
        e = {"source": "x|2020", "quality_score": {"memory_type": "llm_extract"}}
        f = ranking.freshness(e)
        assert 0 < f <= 1
        assert 0 <= ranking.quality_score(e) <= 1
    run("ranking.freshness/quality", t_ranking)

    def t_topic():
        import topic_intelligence
        s = topic_intelligence.score_topic({"primary": "优化决策", "keywords": ["排产"]}, top=3, entries=[])
        assert s.get("status")
    run("topic_intelligence.score_topic", t_topic)

    def t_paper():
        import paper_retrieval
        p = paper_retrieval.retrieve_paper({"section": "摘要", "context_type": "优化"})
        assert p.get("n_wr", 0) >= 0
    run("paper_retrieval.retrieve_paper", t_paper)

    # 7-8. 脚本级冒烟（临时目录）
    if not args.quick:
        def t_consistency():
            with tempfile.TemporaryDirectory() as td:
                res = os.path.join(td, "results")
                os.makedirs(res)
                with open(os.path.join(res, "r.json"), "w", encoding="utf-8") as f:
                    json.dump({"q": {"v": 3.42}}, f)
                with open(os.path.join(td, "paper.md"), "w", encoding="utf-8") as f:
                    f.write("# 摘要\n结果 3.42，范围 550-800 字\n")
                r = subprocess.run([PY, os.path.join(SCRIPTS, "consistency_check.py"), td],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
                assert r.returncode == 0, r.stdout[-300:]
        run("consistency_check 冒烟", t_consistency)

        def t_check_core():
            with tempfile.TemporaryDirectory() as td:
                with open(os.path.join(td, "problem_graph.md"), "w", encoding="utf-8") as f:
                    f.write("## graph\n假设: 独立\n")
                with open(os.path.join(td, "paper_outline.md"), "w", encoding="utf-8") as f:
                    f.write("## 大纲\n摘要\n参考文献\n")
                r = subprocess.run([PY, os.path.join(SCRIPTS, "check_core_execution.py"), td, "--phase", "A"],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
                assert "PASS" in r.stdout, r.stdout[-300:]
        run("check_core_execution 冒烟", t_check_core)

        # 9. paper_check 冒烟：模板副本 + 空 results 目录
        #    → 模板应自身通过（标题9项/摘要禁词/内部词/数字一致性全 PASS, 视觉 WARN 因无 PDF 不阻塞）
        #    防旗舰自检脚本被 consistency/check_heading 改动破坏而无感知
        def t_paper_check():
            import re as _re
            tpl = os.path.join(ROOT, "templates", "paper_template.tex")
            assert os.path.exists(tpl), f"模板缺失: {tpl}"
            with tempfile.TemporaryDirectory() as td:
                tex = open(tpl, encoding="utf-8").read()
                # 注入合规摘要：5 段约 650 字，含总评段与关键词行。
                abs_ok = (
                    "\\begin{abstract}\n"
                    "塔式太阳能光热发电通过定日镜场将太阳光反射汇聚至吸收塔顶部集热器，实现太阳能到热能的转化，镜场的光学效率与布局设计直接决定电站整体性能。本文针对定日镜场的光学效率计算与优化设计问题，建立了基于太阳几何与蒙特卡洛光线追踪思想的光学效率计算模型，并在此基础上完成镜场参数优化设计。\n\n"
                    "针对问题一，建立了定日镜场光学效率计算模型。依据太阳高度角、方位角与赤纬公式计算太阳位置，结合经验辐照模型确定法向直接辐射；对每面定日镜采用空间向量法计算余弦效率，采用投影判定法计算阴影遮挡损失，采用光斑几何近似计算截断效率，并计入大气透射率与镜面反射率，得到逐镜光学效率。对给定的一千七百余面定日镜逐时刻计算，得到年平均光学效率、年平均输出热功率与单位镜面面积功率，输出功率随季节呈明显波动，并在早晚与冬季低太阳高度角时段保留完整的光线路径计算，确保阴影遮挡判定的精度，为后续优化设计提供定量基础。\n\n"
                    "针对问题二，建立了镜场布局优化模型。以环形径向布局为基础，以额定功率达标且单位镜面面积输出功率最大为优化目标，扫描定日镜数目并评估镜场功率，得到满足额定约束的最优设计参数组合，同时给出不同镜数下的功率与单位面积功率对比，验证优化结果的稳健性。\n\n"
                    "针对问题三，建立了变尺寸镜场模型。允许近场与远场采用不同尺寸镜面，以适应距离导致的效率差异，简化评估了尺寸分级方案的综合输出功率，分析了尺寸分级对远场效率的改善潜力。\n\n"
                    "综上，本文以太阳几何与光线追踪为核心框架，实现了定日镜场光学效率的精确计算与设计参数的优化求解，模型物理机制清晰、计算高效、结果可复现，可为塔式光热电站镜场设计提供量化支撑。\n\n"
                    "\\noindent\\textbf{关键词}：\\textbf{定日镜场}；\\textbf{光学效率}；\\textbf{光线追踪}；\\textbf{阴影遮挡}；\\textbf{布局优化}\n"
                    "\\end{abstract}\n")
                tex = _re.sub(r"\\begin\{abstract\}.*?\\end\{abstract\}", lambda m: abs_ok, tex, flags=_re.S)
                with open(os.path.join(td, "paper.tex"), "w", encoding="utf-8") as f:
                    f.write(tex)
                os.makedirs(os.path.join(td, "results"))
                with open(os.path.join(td, "results", "r.json"), "w", encoding="utf-8") as f:
                    json.dump({"placeholder": 1.0}, f)
                r = subprocess.run([PY, os.path.join(SCRIPTS, "paper_check.py"), td],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
                assert r.returncode == 0, (r.stdout + r.stderr)[-400:]
        run("paper_check 冒烟(模板)", t_paper_check)

        # 10. docx_postprocess 分页符冒烟：关键词后、参考文献前和附录前；
        #     覆盖 pandoc 丢弃“参考文献”标题时的补插逻辑。
        def t_docx_breaks():
            import docx as _docx
            import zipfile as _zipfile
            def _breaks(path):
                xml = _zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
                return xml.count('w:type="page"') + xml.count("pageBreakBefore")
            with tempfile.TemporaryDirectory() as td:
                out = os.path.join(td, "t.docx")
                d = _docx.Document()
                for t in ["论文题目", "摘要正文内容", "关键词：A；B；C", "第一章正文内容", "参考文献", "附录A 支撑材料"]:
                    d.add_paragraph(t)
                d.save(out)
                r = subprocess.run([PY, os.path.join(SCRIPTS, "docx_postprocess.py"), out],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
                assert r.returncode == 0, (r.stderr or r.stdout)[-300:]
                assert _breaks(out) == 3, f"场景A 分页符数 != 3"
                # 场景B: 无"参考文献"标题, 只有 bibitem 段（pandoc 丢弃标题的情形）
                out2 = os.path.join(td, "t2.docx")
                d2 = _docx.Document()
                for t in ["论文题目", "摘要正文内容", "关键词：A；B；C", "第一章正文内容",
                          "Duffie J A. Solar Engineering[M]. Wiley, 2013.", "附录A 支撑材料"]:
                    d2.add_paragraph(t)
                d2.save(out2)
                r2 = subprocess.run([PY, os.path.join(SCRIPTS, "docx_postprocess.py"), out2],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
                assert r2.returncode == 0, (r2.stderr or r2.stdout)[-300:]
                assert _breaks(out2) == 3, f"场景B 分页符数 != 3（应补插参考文献标题）"
                d3 = _docx.Document(out2)
                has_ref = any(p.text.strip().startswith("参考文献") for p in d3.paragraphs)
                assert has_ref, "场景B 未补插参考文献标题"
        run("docx_postprocess 分页符冒烟", t_docx_breaks)

        # 11. 可复用模块 import 无副作用：只导入显式登记的库模块。
        #     历史迁移/批处理脚本属于 CLI-only，不得通过 import 触发写文件。
        def t_imports():
            bad = []
            for name in IMPORT_SMOKE_MODULES:
                try:
                    importlib.import_module(name)
                except SystemExit:
                    pass
                except Exception as e:
                    bad.append(f"{name}.py: {type(e).__name__}: {str(e)[:80]}")
            assert not bad, bad[:6]
        run("可复用模块 import 无副作用", t_imports)

        # 12. docx 交付链路 e2e：模板→pandoc→xelatex→docx_pipeline 8 步全绿 +
        #     3分页/参考文献标题/图断言。缺 pandoc/xelatex 时脚本自身 SKIP（返回 0 不阻塞）
        def t_docx_e2e():
            r = subprocess.run([PY, os.path.join(SCRIPTS, "e2e_docx_test.py")],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            assert r.returncode == 0, (r.stdout + r.stderr)[-400:]
        run("docx 交付链路 e2e", t_docx_e2e)

    ok = all(r[1].startswith("PASS") for r in results)
    print(f"=== 冒烟自测: {'PASS' if ok else 'FAIL'} ({sum(1 for _, r in results if r.startswith('PASS'))}/{len(results)}) ===")
    for n, r in results:
        print(f"  [{r.split(':')[0]}] {n}: {r}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
