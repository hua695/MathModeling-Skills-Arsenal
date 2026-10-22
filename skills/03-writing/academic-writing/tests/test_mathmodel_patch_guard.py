import tempfile
import unittest
from pathlib import Path

from scripts.mathmodel_patch_guard import compare


BASE = r"""\section{测试}
这是原始正文。结果为 12.5\%。
\begin{equation}\label{eq:test} d = 7.405\,\mathrm{\mu m} \end{equation}
见式~\eqref{eq:test} 和文献~\cite{refA}。
\begin{tabular}{cc}\toprule A & B \\\midrule 1 & 2 \\\bottomrule\end{tabular}
"""


class PatchGuardTests(unittest.TestCase):
    def make_pair(self, after_text=BASE, bib=r"@article{refA, title={T}}"):
        before = Path(tempfile.mkdtemp())
        after = Path(tempfile.mkdtemp())
        for root, text in ((before, BASE), (after, after_text)):
            (root / "paper.tex").write_text(text, encoding="utf-8")
            (root / "refs.bib").write_text(bib, encoding="utf-8")
        return before, after

    def test_prose_change_passes(self):
        before, after = self.make_pair(BASE.replace("原始正文", "修改后的正文"))
        self.assertTrue(compare(before, after)["passed"])

    def test_formula_change_fails(self):
        before, after = self.make_pair(BASE.replace("7.405", "7.406"))
        self.assertFalse(compare(before, after)["passed"])

    def test_citation_change_fails(self):
        before, after = self.make_pair(BASE.replace("refA", "refB"))
        self.assertFalse(compare(before, after)["passed"])

    def test_table_structure_change_fails(self):
        before, after = self.make_pair(BASE.replace("\\bottomrule", ""))
        self.assertFalse(compare(before, after)["passed"])

    def test_bib_change_fails(self):
        before, after = self.make_pair()
        (after / "refs.bib").write_text(r"@article{refA, title={Changed}}", encoding="utf-8")
        self.assertFalse(compare(before, after)["passed"])


if __name__ == "__main__":
    unittest.main()
