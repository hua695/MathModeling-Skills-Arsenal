import pytest

from scripts.visual_qa import render_preview


def test_render_preview_accepts_png_path(tmp_path):
    path = tmp_path / "figure.png"
    path.write_bytes(b"png fixture")

    assert render_preview(str(path)) == str(path)


def test_render_preview_rejects_image_pdf_path(tmp_path):
    path = tmp_path / "figure.pdf"
    path.write_bytes(b"%PDF-1.7 fixture")

    with pytest.raises(RuntimeError, match="正式图片只允许 SVG 和 PNG"):
        render_preview(str(path))
