"""
scipilot-figure-skill :: export_figure.py
=========================================
Unified figure export to SVG and PNG at exact final size.

- SVG is the formal vector source for LaTeX insertion.
- PNG is the raster preview and visual-QA artifact at the requested DPI.
- Optional grayscale preview checks colorblind safety.

Usage
-----
    from export_figure import export_figure
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([0,1,2],[3,1,4])

    paths = export_figure(
        fig,
        basename="figs/fig1_main",
        formats=["svg", "png"],
        size_inches=(3.5, 2.625),   # 强制成 Nature 单栏尺寸
        dpi=600,
        grayscale_preview=True,
    )
    # -> ['figs/fig1_main.svg', 'figs/fig1_main.png',
    #     'figs/fig1_main_grayscale.png']

CLI: ``python export_figure.py demo`` 生成一张演示图并多格式导出。
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable

import matplotlib.pyplot as plt


VECTOR_FORMATS = {"svg"}
RASTER_FORMATS = {"png"}
SUPPORTED_FORMATS = VECTOR_FORMATS | RASTER_FORMATS
DEFAULT_FORMATS = ("svg", "png")


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def export_figure(
    fig,
    basename: str,
    formats: Iterable[str] | None = None,
    dpi: int = 300,
    size_inches: tuple[float, float] | None = None,
    grayscale_preview: bool = False,
    tight: bool = True,
    pad_inches: float = 0.05,
    transparent: bool = False,
) -> list[str]:
    """
    Export a matplotlib Figure to one or more formats at exact final size.

    Args:
        fig: matplotlib Figure object.
        basename: 输出路径前缀（不含扩展名）；可包含子目录，自动创建。
        formats: list/tuple of extensions. Only ['svg', 'png'] are allowed.
            Default: ['svg', 'png'].
        dpi: raster 格式分辨率；建议 300（普通）/ 600（IEEE 等）。
        size_inches: (width, height) 英寸；指定后会 fig.set_size_inches() 强制
            最终尺寸。强烈建议传入——保证导出后不必在 Word/LaTeX 里二次缩放。
        grayscale_preview: 额外生成一张 _grayscale.png 供色盲安全检查。
        tight: 是否走 bbox_inches='tight'（裁掉留白）。
        pad_inches: tight 模式下保留的边距（英寸）。
        transparent: 透明背景（PPT/海报可能需要）。

    Returns:
        实际写出的文件路径列表。
    """
    if formats is None:
        formats = DEFAULT_FORMATS
    formats = [f.lower().lstrip(".") for f in formats]
    unknown = [f for f in formats if f not in SUPPORTED_FORMATS]
    if unknown:
        raise ValueError(f"Unsupported formats: {unknown}. "
                         f"Supported: {sorted(SUPPORTED_FORMATS)}")

    if size_inches is not None:
        if len(size_inches) != 2:
            raise ValueError("size_inches must be (width, height)")
        fig.set_size_inches(*size_inches)

    plt.rcParams["svg.fonttype"] = "none"  # 文本仍可编辑，期刊通常更欢迎

    saved: list[str] = []
    for fmt in formats:
        path = f"{basename}.{fmt}"
        _ensure_parent(path)
        kwargs: dict = {
            "bbox_inches": "tight" if tight else None,
            "pad_inches": pad_inches,
            "transparent": transparent,
        }
        if fmt in RASTER_FORMATS:
            kwargs["dpi"] = dpi
        fig.savefig(path, **kwargs)
        saved.append(path)
        print(f"[scipilot-figure-skill] wrote {path}")

    if grayscale_preview:
        gray_path = _grayscale_from(fig, basename, dpi=dpi)
        if gray_path:
            saved.append(gray_path)
    return saved


def _grayscale_from(fig, basename: str, dpi: int) -> str | None:
    """
    导出灰度预览版用于色盲安全检查。
    优先用 PIL 转灰度；找不到 PIL 时退化为重新画图（关闭颜色）。
    """
    try:
        from PIL import Image
    except ImportError:
        print("[scipilot-figure-skill] Pillow not available; "
              "grayscale preview skipped.", file=sys.stderr)
        return None

    png_path = f"{basename}.png"
    _ensure_parent(png_path)
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")

    gray_path = f"{basename}_grayscale.png"
    Image.open(png_path).convert("L").save(gray_path)
    print(f"[scipilot-figure-skill] wrote {gray_path} (grayscale preview)")
    return gray_path


def _demo(out_basename: str) -> None:
    """Generate a small demo figure for quick smoke testing."""
    import numpy as np
    rng = np.random.default_rng(7)
    x = np.linspace(0, 10, 50)
    y1 = np.sin(x) + rng.normal(0, 0.1, x.size)
    y2 = np.cos(x) + rng.normal(0, 0.1, x.size)

    fig, ax = plt.subplots(figsize=(3.5, 2.625))
    ax.plot(x, y1, label="sin", marker="o", markersize=3)
    ax.plot(x, y2, label="cos", marker="s", markersize=3, linestyle="--")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(frameon=False)

    paths = export_figure(
        fig, out_basename,
        formats=["svg", "png"],
        size_inches=(3.5, 2.625),
        dpi=300,
        grayscale_preview=True,
    )
    print("\nDemo done. Files:")
    for p in paths:
        print(f"  {p}")


def _cli() -> int:
    p = argparse.ArgumentParser(description="scipilot-figure-skill figure exporter")
    p.add_argument("cmd", choices=["demo"], help="`demo`: 导出 SVG、PNG 和灰度预览")
    p.add_argument("--out", default="./scipilot_demo",
                   help="输出 basename (默认 ./scipilot_demo)")
    args = p.parse_args()
    if args.cmd == "demo":
        _demo(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
