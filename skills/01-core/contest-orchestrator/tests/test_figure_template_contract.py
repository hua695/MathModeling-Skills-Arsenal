import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import check_visual_evidence


EXPECTED_TEMPLATE_IDS = {
    "problem-analysis-flow",
    "contest-mainline-route",
    "model-structure-roadmap",
    "algorithm-iteration-flow",
    "validation-loop",
    "model-summary-frame",
    "variable-objective-constraint",
    "coordinate-angle-coverage",
    "free-body-mechanism",
    "validation-sensitivity-schematic",
}


class FigureTemplateContractTests(unittest.TestCase):
    def setUp(self):
        self.skill_root = Path(check_visual_evidence.__file__).resolve().parents[1]
        self.catalog_path = self.skill_root / "references" / "figure_template_catalog.yaml"

    def test_catalog_contains_route_bound_starters_with_real_hashes(self):
        catalog = yaml.safe_load(self.catalog_path.read_text(encoding="utf-8"))
        entries = catalog.get("templates", [])
        by_id = {item.get("template_id"): item for item in entries}
        self.assertEqual(set(by_id), EXPECTED_TEMPLATE_IDS)
        self.assertEqual(len(entries), len(by_id))
        for template_id, entry in by_id.items():
            with self.subTest(template_id=template_id):
                route = entry.get("generation_route")
                self.assertIn(route, {"tech-route-maker", "tikz-scientific-figures"})
                starter_source = entry.get("starter_source")
                self.assertIsInstance(starter_source, str)
                starter_path = (self.skill_root.parent / starter_source).resolve()
                self.assertTrue(starter_path.is_file(), starter_path)
                expected_hash = entry.get("template_sha256")
                self.assertRegex(expected_hash or "", r"^[0-9a-f]{64}$")
                actual_hash = hashlib.sha256(starter_path.read_bytes()).hexdigest()
                self.assertEqual(actual_hash, expected_hash)

                if route == "tech-route-maker":
                    payload = json.loads(starter_path.read_text(encoding="utf-8"))
                    provenance = payload.get("metadata", {}).get("contest_template", {})
                    self.assertEqual(provenance.get("template_id"), template_id)
                    self.assertEqual(provenance.get("starter_source"), starter_source)
                    self.assertIn("template_sha256", provenance)
                    self.assertIn(str(provenance.get("template_sha256")), {"", "<computed-at-generation>"})
                else:
                    source = starter_path.read_text(encoding="utf-8")
                    self.assertIn(f"contest-template-id: {template_id}", source)
                    self.assertIn("contest-template-sha256:", source)

    def test_catalog_routes_are_unique_and_have_fixture_contract(self):
        catalog = yaml.safe_load(self.catalog_path.read_text(encoding="utf-8"))
        entries = catalog.get("templates", [])
        for entry in entries:
            with self.subTest(template_id=entry.get("template_id")):
                self.assertTrue(entry.get("fixture_id"))
                self.assertGreaterEqual(int(entry.get("min_visible_elements", 0)), 2)
                self.assertIn(entry.get("canvas_orientation"), {"horizontal", "vertical", "square"})

    def test_project_gate_checks_starter_markers_and_fixture_report(self):
        catalog = yaml.safe_load(self.catalog_path.read_text(encoding="utf-8"))
        entry = next(item for item in catalog["templates"] if item["template_id"] == "algorithm-iteration-flow")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            script_path = root / "figures" / "algorithm" / "tech-route.json"
            report_path = root / "figures" / "algorithm" / "template_fixture.yaml"
            script_path.parent.mkdir(parents=True)
            script_path.write_text(json.dumps({
                "metadata": {"contest_template": {
                    "template_id": entry["template_id"],
                    "starter_source": entry["starter_source"],
                    "template_sha256": entry["template_sha256"],
                }}
            }), encoding="utf-8")
            report_path.write_text(yaml.safe_dump({
                "status": "passed",
                "template_id": entry["template_id"],
                "template_sha256": entry["template_sha256"],
                "visual_qa": "passed",
            }), encoding="utf-8")
            figure = {
                "generator": "tech-route-maker",
                "template_id": entry["template_id"],
                "starter_source": entry["starter_source"],
                "template_sha256": entry["template_sha256"],
                "script": "figures/algorithm/tech-route.json",
                "layout_mode": "single",
                "canvas_profile": {"orientation": "horizontal", "target_layout": "single", "top_level_node_limit": 7},
                "visible_element_map": [
                    {"element": "输入", "role": "node", "evidence_refs": ["source#/input"]},
                    {"element": "输出", "role": "edge", "evidence_refs": ["source#/output"]},
                ],
                "template_fixture": {
                    "fixture_id": entry["fixture_id"],
                    "status": "passed",
                    "report": "figures/algorithm/template_fixture.yaml",
                },
                "visual_qa": "passed",
            }
            errors = []
            check_visual_evidence._validate_registry_template_execution(
                figure,
                [{
                    "template_id": entry["template_id"],
                    "visible_element_map": figure["visible_element_map"],
                    "canvas_profile": figure["canvas_profile"],
                }],
                label="figure_registry 图表 fig-algorithm",
                project_root=root,
                errors=errors,
            )
            self.assertEqual(errors, [])

            figure["template_fixture"]["status"] = "failed"
            errors = []
            check_visual_evidence._validate_registry_template_execution(
                figure,
                [{
                    "template_id": entry["template_id"],
                    "visible_element_map": figure["visible_element_map"],
                    "canvas_profile": figure["canvas_profile"],
                }],
                label="figure_registry 图表 fig-algorithm",
                project_root=root,
                errors=errors,
            )
            self.assertTrue(any("template_fixture.status" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
