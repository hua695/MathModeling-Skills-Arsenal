import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from scripts.export_figure import export_figure


def test_export_defaults_to_svg_and_png_only(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    basename = tmp_path / "figure"

    paths = export_figure(fig, str(basename))

    assert {path.rsplit(".", 1)[1] for path in paths} == {"svg", "png"}
    assert (tmp_path / "figure.svg").exists()
    assert (tmp_path / "figure.png").exists()
    assert not (tmp_path / "figure.pdf").exists()
    plt.close(fig)


def test_export_rejects_pdf_format(tmp_path):
    fig, _ = plt.subplots()

    with pytest.raises(ValueError, match="Unsupported formats"):
        export_figure(fig, str(tmp_path / "figure"), formats=["pdf"])

    plt.close(fig)
