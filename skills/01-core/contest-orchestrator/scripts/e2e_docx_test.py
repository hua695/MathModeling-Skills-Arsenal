#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
e2e_docx_test.py — docx 交付链路端到端回归

模板 → pandoc 风格 tex → xelatex PDF → docx_pipeline 8 步 → 全绿断言：
  - docx_pipeline 退出码 0（8 步全 PASS）
  - 3 处分页（关键词后 pbb + 参考文献前/附录前 br）
  - "参考文献"标题存在（pandoc 丢弃标题时由 docx_postprocess 补插）
  - 图存在（graphicspath 正确传递）
  - 文献内容存在

用于保护图题、分页、graphicspath、文献边界和退出码的完整交付链路。

用法: python scripts/e2e_docx_test.py
依赖: pandoc + xelatex（缺失则 SKIP 返回 0; 均有则真实断言）
"""
from __future__ import annotations

import base64
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SCRIPTS = os.path.dirname(os.path.abspath(__file__))

TEX_FIXTURE = r"""\documentclass[12pt]{article}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{listings}
\usepackage{amsmath}
\usepackage{geometry}
\geometry{margin=2.5cm}
\graphicspath{{figs/}}
\title{基于测试方法的光学效率计算模型}
\date{}
\begin{document}
\maketitle
\begin{abstract}
塔式太阳能光热发电通过定日镜场将太阳光反射汇聚至吸收塔顶部集热器，实现太阳能到热能的转化，镜场的光学效率与布局设计直接决定电站整体性能。本文针对定日镜场的光学效率计算与优化设计问题，建立了基于太阳几何与光线追踪思想的光学效率计算模型，并在此基础上完成镜场参数优化设计。

针对问题一，建立了定日镜场光学效率计算模型。依据太阳高度角、方位角与赤纬公式计算太阳位置，结合经验辐照模型确定法向直接辐射；对每面定日镜采用空间向量法计算余弦效率，采用投影判定法计算阴影遮挡损失，采用光斑几何近似计算截断效率，并计入大气透射率与镜面反射率，得到逐镜光学效率。对给定的一千七百余面定日镜逐时刻计算，得到年平均光学效率与年平均输出热功率，输出功率随季节呈明显波动，并在早晚与冬季低太阳高度角时段保留完整的光线路径计算，确保阴影遮挡判定的精度，为后续优化设计提供定量基础。

针对问题二，建立了镜场布局优化模型。以环形径向布局为基础，以额定功率达标且单位镜面面积输出功率最大为优化目标，扫描定日镜数目并评估镜场功率，得到满足额定约束的最优设计参数组合，同时给出不同镜数下的功率与单位面积功率对比，验证优化结果的稳健性。

针对问题三，建立了变尺寸镜场模型。允许近场与远场采用不同尺寸镜面，以适应距离导致的效率差异，简化评估了尺寸分级方案的综合输出功率，分析了尺寸分级对远场效率的改善潜力。

综上，本文以太阳几何与光线追踪为核心框架，实现了定日镜场光学效率的精确计算与设计参数的优化求解，模型物理机制清晰、计算高效、结果可复现，可为塔式光热电站镜场设计提供量化支撑。

\textbf{关键词}：\textbf{定日镜场}；\textbf{光学效率}；\textbf{光线追踪}；\textbf{阴影遮挡}；\textbf{布局优化}
\end{abstract}

\section{问题重述}
定日镜场通过镜面反射实现太阳能汇聚，镜场设计需满足额定功率约束。

\section{模型建立与求解}
\begin{equation}
\eta = \eta_{sb}\,\eta_{cos}\,\eta_{at}\,\eta_{trunc}\,\eta_{ref}
\end{equation}
\begin{figure}[h]
\centering
\includegraphics[width=0.5\textwidth]{fig1.png}
\caption{镜场布局示意}
\end{figure}
由图可知，环形布局下镜面沿径向排布，遮挡关系清晰，该布局可有效控制遮挡损失。

\begin{lstlisting}[language=Python]
def compute_eta(sun, mirror):
    return sun * mirror
\end{lstlisting}

\section{结论}
本文建立了定日镜场光学效率计算与优化模型，模型可复现，结果由代码生成。

\begin{thebibliography}{9}
\bibitem{duffie} Duffie J A, Beckman W A. Solar Engineering of Thermal Processes[M]. Wiley, 2013.
\bibitem{zhang} 张平. 太阳能塔式光热镜场光学效率计算方法[J]. 技术与市场, 2021, 28(6): 5-8.
\end{thebibliography}

\appendix
\section{支撑材料文件列表}
\section{核心源代码}
\section{公式推导}
\section{数据验证报告}
\section{AI 工具使用说明}
\end{document}
"""


def _make_png(path: Path) -> None:
    """最小合法 PNG（40x30 灰色块），零依赖。"""
    w, h = 40, 30
    raw = b"".join(b"\x00" + bytes([120] * w) for _ in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", __import__("zlib").crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", __import__("zlib").compress(raw))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def main() -> int:
    for exe in ("pandoc", "xelatex"):
        if shutil.which(exe) is None:
            print(f"[SKIP] 缺 {exe}（docx 交付链路 e2e 需要 pandoc+xelatex）")
            return 0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "figs").mkdir()
        _make_png(td / "figs" / "fig1.png")
        tex = td / "paper_pandoc.tex"
        tex.write_text(TEX_FIXTURE, encoding="utf-8")

        r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-shell-escape", "paper_pandoc.tex"],
                           cwd=td, capture_output=True, text=True, encoding="utf-8", errors="replace")
        pdf = td / "paper_pandoc.pdf"
        if not pdf.exists():
            print(f"[FAIL] xelatex 未产出 PDF: {(r.stdout or '')[-300:]}")
            return 1

        out = td / "paper.docx"
        r2 = subprocess.run([sys.executable, os.path.join(SCRIPTS, "docx_pipeline.py"),
                             str(tex), str(pdf), "-o", str(out)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r2.returncode != 0:
            print(f"[FAIL] docx_pipeline 8 步未全绿: {(r2.stdout or '')[-800:]}")
            return 1

        xml = zipfile.ZipFile(str(out)).read("word/document.xml").decode("utf-8")
        n_breaks = xml.count('w:type="page"') + xml.count("pageBreakBefore")
        assert n_breaks >= 3, f"分页符 {n_breaks} < 3（关键词后/参考文献前/附录前）"

        import docx as _docx
        texts = [p.text.strip() for p in _docx.Document(str(out)).paragraphs]
        assert any(t.startswith("参考文献") for t in texts), "缺参考文献标题"
        assert any("Duffie" in t for t in texts), "缺文献内容"
        assert "w:drawing" in xml or "pic:pic" in xml, "缺图（graphicspath 修复失效）"

        print(f"[PASS] docx 交付链路 e2e: 分页{n_breaks}/参考文献/图/8步全绿")
        return 0


if __name__ == "__main__":
    sys.exit(main())
