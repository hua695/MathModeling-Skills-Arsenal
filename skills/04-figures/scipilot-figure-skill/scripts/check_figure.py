"""
scipilot-figure-skill :: check_figure.py
========================================
Pre-submission figure compliance audit.

逐文件检查：格式（SVG 或 PNG）、像素尺寸/DPI 和 SVG 内嵌位图风险，输出问题清单。
非破坏性——只读、不修改原图。

Usage
-----
    from check_figure import check_figure, print_report
    issues, info = check_figure("figs/fig1.svg", min_dpi=300, target_inches=(3.5, 2.625))
    print_report("figs/fig1.svg", issues, info)

CLI:
    python check_figure.py figs/fig1.svg figs/fig2.png --min-dpi 300
    python check_figure.py figs/*.svg figs/*.png --strict   # 任意 FAIL 即 exit 2
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import Any

VECTOR_FORMATS = {"svg"}
RASTER_OK_FORMATS = {"png"}

# Severity 序号越高越严重
SEVERITY = {"INFO": 0, "WARN": 1, "FAIL": 2}


def _ext(path: str) -> str:
    return os.path.splitext(path)[1].lower().lstrip(".")


def _check_raster(path: str, ext: str, min_dpi: int,
                  target_inches: tuple[float, float] | None) -> tuple[list, dict]:
    """PNG 位图合规性检查。"""
    issues: list[tuple[str, str]] = []
    info: dict[str, Any] = {"category": "raster", "ext": ext}

    try:
        from PIL import Image
    except ImportError:
        issues.append(("INFO",
                       "Pillow 未安装，跳过像素/DPI 检查："
                       "pip install Pillow 后可启用。"))
        return issues, info

    try:
        img = Image.open(path)
        info["size_px"] = img.size  # (w, h)
        dpi = img.info.get("dpi")
        info["dpi"] = dpi
    except Exception as e:
        issues.append(("FAIL", f"无法读取图像：{e}"))
        return issues, info

    if dpi is None:
        issues.append(("WARN",
                       "文件未嵌入 DPI 元数据。期刊往往按 DPI 折算最终尺寸，"
                       "请用 fig.savefig(dpi=300) 显式指定。"))
    else:
        dx = dpi[0] if isinstance(dpi, tuple) else dpi
        # PIL roundtrips DPI as float and may give 299.9994 for a value saved
        # at 300; round before compare to absorb that.
        dx_rounded = round(float(dx))
        if dx_rounded < min_dpi:
            issues.append(("FAIL",
                           f"DPI = {dx_rounded} 低于要求的 {min_dpi}。"
                           "重新 savefig(dpi=...) 一次。"))
        if target_inches is not None:
            tw, th = target_inches
            actual_w_in = info["size_px"][0] / float(dx)
            actual_h_in = info["size_px"][1] / float(dx)
            tol = 0.1  # 英寸容差
            if abs(actual_w_in - tw) > tol or abs(actual_h_in - th) > tol:
                issues.append((
                    "WARN",
                    f"实际尺寸 ≈ {actual_w_in:.2f}×{actual_h_in:.2f} in，"
                    f"目标 {tw}×{th} in。请在画图时直接设 figsize=({tw}, {th})，"
                    "不要在 Word/LaTeX 里二次缩放。"
                ))
    return issues, info


def _check_svg(path: str) -> list[tuple[str, str]]:
    """SVG 简检：警告 base64 嵌入的位图（破坏矢量优势）。"""
    issues: list[tuple[str, str]] = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            head = f.read(50000)
    except Exception as e:
        issues.append(("WARN", f"SVG 读失败: {e}"))
        return issues
    if "data:image/png;base64" in head or "data:image/jpeg;base64" in head:
        issues.append(("WARN",
                       "SVG 中包含 base64 嵌入的位图——会丢失矢量优势。"
                       "检查是否在 plot 中误用了 imshow 或图像贴图。"))
    return issues


def check_figure(path: str, min_dpi: int = 300,
                 target_inches: tuple[float, float] | None = None
                 ) -> tuple[list[tuple[str, str]], dict]:
    """
    审计一张图。返回 (issues, info)。
    issues: [(severity, message), ...]; severity ∈ {INFO, WARN, FAIL}
    info: 元数据字典（格式、像素、DPI 等）
    """
    issues: list[tuple[str, str]] = []
    info: dict[str, Any] = {"path": path}

    if not os.path.exists(path):
        return [("FAIL", f"文件不存在: {path}")], info

    ext = _ext(path)
    info["ext"] = ext
    info["size_bytes"] = os.path.getsize(path)

    if ext in VECTOR_FORMATS:
        info["category"] = "vector"
        issues.extend(_check_svg(path))
    elif ext in RASTER_OK_FORMATS:
        sub_issues, sub_info = _check_raster(path, ext, min_dpi, target_inches)
        issues.extend(sub_issues)
        info.update(sub_info)
    else:
        issues.append(("FAIL", f"图片输出格式不允许: .{ext}；正式图片只允许 SVG 和 PNG。"))

    return issues, info


def print_report(path: str, issues: list, info: dict) -> str:
    """以可读格式打印一张图的审计结果，返回 overall verdict 字符串。"""
    print(f"\n--- {path} ---")
    if "category" in info:
        print(f"  category: {info['category']}  ext: {info['ext']}  "
              f"size: {info.get('size_bytes', '?')} B")
    if info.get("size_px"):
        print(f"  pixels: {info['size_px'][0]}x{info['size_px'][1]}  "
              f"dpi: {info.get('dpi')}")

    if not issues:
        print("  [PASS] 无问题。")
        return "PASS"

    max_sev = max(SEVERITY[s] for s, _ in issues)
    verdict = {2: "FAIL", 1: "WARN", 0: "INFO"}[max_sev]
    for severity, msg in sorted(issues, key=lambda x: -SEVERITY[x[0]]):
        print(f"  [{severity}] {msg}")
    print(f"  >>> verdict: {verdict}")
    return verdict


def _cli() -> int:
    p = argparse.ArgumentParser(description="scipilot-figure-skill compliance checker")
    p.add_argument("paths", nargs="+", help="图文件路径，可用 glob")
    p.add_argument("--min-dpi", type=int, default=300)
    p.add_argument("--width-in", type=float, help="目标宽度(英寸)")
    p.add_argument("--height-in", type=float, help="目标高度(英寸)")
    p.add_argument("--strict", action="store_true",
                   help="任意 FAIL 即 exit code 2")
    args = p.parse_args()

    target = None
    if args.width_in and args.height_in:
        target = (args.width_in, args.height_in)

    expanded: list[str] = []
    for pat in args.paths:
        m = glob.glob(pat)
        expanded.extend(m if m else [pat])

    any_fail = False
    for path in expanded:
        issues, info = check_figure(path, min_dpi=args.min_dpi, target_inches=target)
        verdict = print_report(path, issues, info)
        if verdict == "FAIL":
            any_fail = True

    print()
    if args.strict and any_fail:
        print("[scipilot-figure-skill] strict mode: at least one FAIL — exit 2")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
