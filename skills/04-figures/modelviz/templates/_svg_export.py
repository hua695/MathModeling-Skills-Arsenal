"""Small output helper for templates that assemble raster panels."""

from __future__ import annotations

from base64 import b64encode
from pathlib import Path

from PIL import Image


def save_png_as_svg(png_path: str | Path, svg_path: str | Path) -> str:
    """Wrap a rendered PNG in an SVG container without creating another format."""

    source = Path(png_path)
    target = Path(svg_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        width, height = image.size
    encoded = b64encode(source.read_bytes()).decode("ascii")
    content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<image width="{width}" height="{height}" '
        f'preserveAspectRatio="none" '
        f'xlink:href="data:image/png;base64,{encoded}" />'
        "</svg>"
    )
    target.write_text(content, encoding="utf-8")
    return str(target)
