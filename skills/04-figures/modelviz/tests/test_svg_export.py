from pathlib import Path

from PIL import Image

from templates._svg_export import save_png_as_svg


def test_save_png_as_svg_creates_svg_wrapper(tmp_path: Path):
    png_path = tmp_path / "figure.png"
    svg_path = tmp_path / "figure.svg"
    Image.new("RGB", (16, 9), "white").save(png_path)

    result = save_png_as_svg(png_path, svg_path)

    assert result == str(svg_path)
    assert png_path.exists()
    assert svg_path.read_text(encoding="utf-8").startswith('<svg ')


def test_python_templates_do_not_emit_image_pdf():
    template_root = Path(__file__).parents[1] / "templates"

    for template in template_root.rglob("*.py"):
        assert "pdf" not in template.read_text(encoding="utf-8").lower()
