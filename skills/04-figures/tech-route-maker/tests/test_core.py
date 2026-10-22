import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from render_pptx import write_pptx  # noqa: E402
from route_common import build_layout, get_style  # noqa: E402
from tech_route_maker.quality import build_quality_report  # noqa: E402
from tech_route_maker.schema import ROUTE_VERSION, make_template_route  # noqa: E402
from tech_route_maker.sources import attach_source_hashes, verify_sources  # noqa: E402
from tech_route_maker.validator import strict_render_blockers, validate  # noqa: E402


class CoreTests(unittest.TestCase):
    def test_current_schema_version(self):
        self.assertEqual(ROUTE_VERSION, "0.3.0")

    def test_inference_does_not_inflate_evidence_coverage(self):
        report = build_quality_report(make_template_route())
        self.assertEqual(report["evidence_coverage"], 0.5)
        self.assertEqual(report["inferred_coverage"], 0.5)
        self.assertEqual(report["accounted_coverage"], 1.0)

    def test_mainline_and_a4_layouts_keep_six_nodes(self):
        path = ROOT / "examples" / "engineering-energy-system-demo" / "outputs" / "tech-route.json"
        route = json.loads(path.read_text(encoding="utf-8"))
        first_stage = route["stages"][0]
        originals = list(first_stage["nodes"])
        for index, node in enumerate(originals, start=4):
            duplicate = copy.deepcopy(node)
            duplicate["id"] = f"extra_{index}"
            duplicate["label"] = f"Extra node {index}"
            first_stage["nodes"].append(duplicate)
        for layout_name in ("cn-ppt-mainline-route", "cn-a4-stage-route"):
            route["layout"] = layout_name
            layout = build_layout(route)
            rendered_ids = set(layout["nodes"])
            self.assertTrue({node["id"] for node in first_stage["nodes"]}.issubset(rendered_ids))

    def test_unknown_layout_and_style_fail(self):
        route = make_template_route()
        route["layout"] = "not-a-real-layout"
        with self.assertRaises(ValueError):
            build_layout(route)
        route = make_template_route()
        route["style"] = "not-a-real-style"
        with self.assertRaises(ValueError):
            get_style(route)

    def test_source_hash_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text(
                "# Source\n\n## Project goal\nGoal.\n\n## Source materials\nMaterials.\n",
                encoding="utf-8",
            )
            route = make_template_route()
            attach_source_hashes(route, root)
            report, _ = verify_sources(route, base_dir=root)
            self.assertEqual(report["status"], "verified")
            (root / "source.md").write_text("changed", encoding="utf-8")
            report, _ = verify_sources(route, base_dir=root)
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["hash_mismatches"], ["source_1"])

    def test_missing_locator_text_does_not_count_as_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text(
                "# Source\n\n## Project goal\nGoal.\n\n## Source materials\nMaterials.\n",
                encoding="utf-8",
            )
            route = make_template_route()
            route["stages"][0]["nodes"][0]["evidence"][0]["locator"] = "Missing locator"
            attach_source_hashes(route, root)
            _errors, _warnings, report = validate(route, route_path=root / "tech-route.json")
            self.assertEqual(report["evidence_coverage"], 0.25)
            self.assertTrue(report["evidence_issues"])

    def test_template_is_blocked_from_final_rendering(self):
        route = make_template_route()
        errors, _warnings, report = validate(route)
        blockers = strict_render_blockers(route, errors, report)
        self.assertTrue(blockers)
        self.assertIn("Domain context must be complete before final rendering.", blockers)

    def test_pptx_generation_is_deterministic(self):
        route_path = ROOT / "examples" / "academic-paper-demo" / "outputs" / "tech-route.json"
        route = json.loads(route_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.pptx"
            second = Path(directory) / "second.pptx"
            write_pptx(route, first)
            write_pptx(route, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
