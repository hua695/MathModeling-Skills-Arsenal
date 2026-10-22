#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx_pipeline.py — docx 生成与质检一键流程(2026-08-15 用户要求: 稳定执行, 一条命令跑完)
用法:
  python scripts/docx_pipeline.py <paper_pandoc.tex> <paper.pdf> [-o paper.docx] [--visual-check]
步骤(任一 FAIL 退出码 1, 不交付):
  1) pandoc --reference-doc=reference.docx  (样式模板: 宋体小四/TNR/黑体标题[黑色]/图题表题小五)
  2) docx_postprocess.py  (显式分页符/题目图片居中/三线表/Consolas 9pt/关键词前空行)
  3) docx_highlight.py    (Pygments 高亮, 与 PDF minted 同引擎同配色)
  4) docx_codebox.py      (浅灰底 #F5F5F5 + 细黑边框 + 灰色行号)
  5) check_docx_consistency.py  (数字一致性: PDF↔docx 数值缺失=0; 公式残留=0; 乱码=0)
  6) visual_critic.py     (仅 --visual-check 启用)
  7) check_visual_contract.py (仅 --visual-check 启用)
"""
import os
import subprocess
import sys
import tempfile

SCRIPTS = os.path.dirname(os.path.abspath(__file__))


def safe_print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('ascii', 'replace').decode('ascii'))


def configure_utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, 'reconfigure', None)
        if reconfigure is not None:
            reconfigure(encoding='utf-8', errors='replace')


def run(cmd, label):
    safe_print(f'--- [{label}] ---')
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = (r.stdout or '').strip()
    err = (r.stderr or '').strip()
    if out:
        safe_print(out[-600:])
    if err:
        safe_print('stderr: ' + err[-300:])
    ok = r.returncode == 0
    safe_print(f'[{label}] -> {"PASS" if ok else "FAIL"}')
    return ok


def visual_check_requested(argv):
    """Return whether the caller explicitly requested automatic visual QA."""
    return '--visual-check' in argv


def main():
    configure_utf8_stdio()
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    tex = os.path.abspath(sys.argv[1])
    pdf = os.path.abspath(sys.argv[2])
    out = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != '-o' else os.path.join(os.path.dirname(tex), 'paper.docx')
    if len(sys.argv) > 4 and sys.argv[3] == '-o':
        out = os.path.abspath(sys.argv[4])
    out = os.path.abspath(out)
    visual_check = visual_check_requested(sys.argv[1:])
    workdir = os.path.dirname(tex)
    py = sys.executable
    resource_paths = os.pathsep.join(
        path for path in (workdir, os.path.join(workdir, 'figs'), os.path.join(workdir, 'figures'))
        if os.path.isdir(path)
    ) or workdir

    with tempfile.TemporaryDirectory(prefix='contest_orchestrator_reference_') as template_dir:
        ref_doc = os.path.join(template_dir, 'reference.docx')
        ok1 = run([py, os.path.join(SCRIPTS, 'make_reference_doc.py'), '--output', ref_doc], 'reference-doc 模板')
        ok2 = run(['pandoc', tex, '-o', out, f'--resource-path={resource_paths}',
                   f'--reference-doc={ref_doc}'], 'pandoc 转换')
        ok3 = run([py, os.path.join(SCRIPTS, 'docx_postprocess.py'), out], '后处理(分页/居中/三线表)')
        ok4 = run([py, os.path.join(SCRIPTS, 'docx_highlight.py'), out], '代码高亮(同引擎)')
        ok5 = run([py, os.path.join(SCRIPTS, 'docx_codebox.py'), out], '代码块美化(底/框/行号)')
        ok6 = run([py, os.path.join(SCRIPTS, 'check_docx_consistency.py'), pdf, out], 'docx 质量兜底')
        if visual_check:
            ok7 = run([py, os.path.join(SCRIPTS, 'visual_critic.py'), out], 'visual_critic')
            ok8 = run([py, os.path.join(SCRIPTS, 'check_visual_contract.py'), out], 'check_visual_contract')
        else:
            safe_print('--- [visual_critic] ---')
            safe_print('SKIPPED_USER_OPT_IN: automatic visual QA is disabled by default; user visual review is the substitute')
            safe_print('--- [check_visual_contract] ---')
            safe_print('SKIPPED_USER_OPT_IN: automatic visual QA is disabled by default; user visual review is the substitute')
            ok7 = ok8 = True

    all_ok = all([ok1, ok2, ok3, ok4, ok5, ok6, ok7, ok8])
    visual_status = 'EXECUTED' if visual_check else 'SKIPPED_USER_OPT_IN'
    print(f'===== docx 管线: {"PASS" if all_ok else "FAIL"}; visual={visual_status} -> {out} =====')
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
