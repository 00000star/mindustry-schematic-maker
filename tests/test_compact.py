"""
Unit Test Suite for Mindustry Compact Layouts & Static CLI Verification (tests/test_compact.py).
Tests algorithmic compact defense generation (Duo and Salvo), 100% supply fulfillment,
and CLI check command integration.
"""

import os
import sys
import unittest
import subprocess

# Ensure current and parent dirs are in sys.path
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
if CUR_DIR not in sys.path:
    sys.path.insert(0, CUR_DIR)

try:
    from compact import build_compact_defense, build_compact_factory
    from validator import validate_schematic
    from sim import trace_supply
    from codec import encode_schematic, decode_schematic
except ImportError:
    from core.compact import build_compact_defense, build_compact_factory
    from core.validator import validate_schematic
    from core.sim import trace_supply
    from core.codec import encode_schematic, decode_schematic


class TestCompactDefense(unittest.TestCase):
    """Test suite for compact defense layouts and automated validation gates."""

    def test_compact_cooled_duo_defense(self):
        """Verify 12-Duo water-cooled compact defense is 100% supplied with ammo and water."""
        schem = build_compact_defense("duo", target_count=12, cooled=True)
        self.assertEqual(schem["width"], 5)
        self.assertEqual(schem["height"], 9)

        duos = [t for t in schem["tiles"] if t["block"] == "duo"]
        self.assertEqual(len(duos), 12)

        # Static validation
        val_result = validate_schematic(schem, inlets=schem.get("inlets"))
        self.assertTrue(val_result.is_valid, f"Validation errors: {val_result.errors}")
        self.assertEqual(len(val_result.errors), 0)

        # Supply tracing
        report = trace_supply(schem, inlets=schem.get("inlets"))
        self.assertEqual(len(report.leaks()), 0)
        self.assertEqual(len(report.missing_demands(include_optional=True)), 0)

        # Verify every duo has both copper and water
        for duo in duos:
            pos = (duo["x"], duo["y"])
            supp = report.supplied_resources.get(pos, set())
            self.assertIn("copper", supp, f"Duo at {pos} missing copper")
            self.assertIn("water", supp, f"Duo at {pos} missing water")

    def test_compact_cooled_salvo_defense(self):
        """Verify 4-Salvo water-cooled compact defense is 100% supplied with ammo and water."""
        schem = build_compact_defense("salvo", target_count=4, cooled=True)
        self.assertEqual(schem["width"], 7)
        self.assertEqual(schem["height"], 7)

        salvos = [t for t in schem["tiles"] if t["block"] == "salvo"]
        self.assertEqual(len(salvos), 4)

        # Static validation
        val_result = validate_schematic(schem, inlets=schem.get("inlets"))
        self.assertTrue(val_result.is_valid, f"Validation errors: {val_result.errors}")
        self.assertEqual(len(val_result.errors), 0)

        # Supply tracing
        report = trace_supply(schem, inlets=schem.get("inlets"))
        self.assertEqual(len(report.leaks()), 0)
        self.assertEqual(len(report.missing_demands(include_optional=True)), 0)

        # Verify each 2x2 salvo has both copper and water
        for salvo in salvos:
            pos = (salvo["x"], salvo["y"])
            supp = report.supplied_resources.get(pos, set())
            self.assertIn("copper", supp, f"Salvo at {pos} missing copper")
            self.assertIn("water", supp, f"Salvo at {pos} missing water")

    def test_cli_check_command(self):
        """Verify CLI check command validates schematics and formats terminal checklist correctly."""
        schem = build_compact_defense("duo", target_count=12, cooled=True)
        _, b64_str = encode_schematic(schem)

        msch_path = os.path.join(CUR_DIR, "msch")
        if not os.path.exists(msch_path):
            msch_path = os.path.join(os.path.dirname(CUR_DIR), "msch")

        res = subprocess.run(
            [sys.executable, msch_path, "check", b64_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self.assertEqual(res.returncode, 0, f"CLI check failed: {res.stderr}\n{res.stdout}")
        self.assertIn("[STATUS]: PASS", res.stdout)
        self.assertIn("Tier A", res.stdout)
        self.assertIn("Tier B", res.stdout)
        self.assertIn("Tier C", res.stdout)


if __name__ == "__main__":
    unittest.main()
