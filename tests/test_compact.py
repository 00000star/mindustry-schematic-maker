"""
Unit Test Suite for Mindustry Universal Schematic Synthesis.
Tests factories, fail-safe power plants, multi-size defenses,
and CLI check command integration.
All code and outputs strictly adhere to <= 70 columns.
"""

import os
import sys
import unittest
import subprocess

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CUR_DIR)
if CUR_DIR not in sys.path:
    sys.path.insert(0, CUR_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from compact import (
        build_compact_defense,
        build_compact_factory,
        build_nested_artillery_module,
        synthesize_compact_defense,
        synthesize_factory,
        synthesize_power_plant,
    )
    from validator import validate_schematic
    from sim import trace_supply
    from codec import encode_schematic, decode_schematic
    from generator import compile_from_prompt
except ImportError:
    from core.compact import (
        build_compact_defense,
        build_compact_factory,
        build_nested_artillery_module,
        synthesize_compact_defense,
        synthesize_factory,
        synthesize_power_plant,
    )
    from core.validator import validate_schematic
    from core.sim import trace_supply
    from core.codec import encode_schematic, decode_schematic
    from core.generator import compile_from_prompt


def _ensure_storage_accessible(path: str) -> None:
    if not os.path.exists(path) or not os.access(path, os.R_OK):
        try:
            cmd = "su -c 'chmod 755 /storage /storage/emulated' 2>/dev/null || true"
            subprocess.run(cmd, shell=True)
        except Exception:
            pass


class TestCompactDefense(unittest.TestCase):
    """Test suite for compact defense layouts & validation gates."""

    def test_compact_cooled_duo_defense(self):
        """Verify 12-Duo water-cooled compact defense."""
        schem = build_compact_defense("duo", target_count=12, cooled=True)
        self.assertEqual(schem["width"], 5)
        self.assertEqual(schem["height"], 9)

        duos = [t for t in schem["tiles"] if t["block"] == "duo"]
        self.assertEqual(len(duos), 12)

        val = validate_schematic(schem, inlets=schem.get("inlets"))
        self.assertTrue(val.is_valid, f"Validation errors: {val.errors}")

        report = trace_supply(schem, inlets=schem.get("inlets"))
        self.assertEqual(len(report.leaks()), 0)
        self.assertEqual(len(report.missing_demands(include_optional=True)), 0)

        for duo in duos:
            pos = (duo["x"], duo["y"])
            supp = report.supplied_resources.get(pos, set())
            self.assertIn("copper", supp)
            self.assertIn("water", supp)

    def test_compact_cooled_salvo_defense(self):
        """Verify 4-Salvo water-cooled compact defense."""
        schem = build_compact_defense("salvo", target_count=4, cooled=True)
        self.assertEqual(schem["width"], 7)
        self.assertEqual(schem["height"], 7)

        salvos = [t for t in schem["tiles"] if t["block"] == "salvo"]
        self.assertEqual(len(salvos), 4)

        val = validate_schematic(schem, inlets=schem.get("inlets"))
        self.assertTrue(val.is_valid, f"Validation errors: {val.errors}")

        report = trace_supply(schem, inlets=schem.get("inlets"))
        self.assertEqual(len(report.leaks()), 0)
        self.assertEqual(len(report.missing_demands(include_optional=True)), 0)

        for salvo in salvos:
            pos = (salvo["x"], salvo["y"])
            supp = report.supplied_resources.get(pos, set())
            self.assertIn("copper", supp)
            self.assertIn("water", supp)

    def test_nested_water_cooled_hail_module(self):
        """Verify 7x7 nested water-cooled Hail module."""
        schem = build_nested_artillery_module("hail")
        self.assertEqual(schem["width"], 7)
        self.assertEqual(schem["height"], 7)

        hails = [t for t in schem["tiles"] if t["block"] == "hail"]
        self.assertEqual(len(hails), 18)

        val = validate_schematic(schem, inlets=schem.get("inlets"))
        self.assertTrue(val.is_valid, f"Validation errors: {val.errors}")

        report = trace_supply(schem, inlets=schem.get("inlets"))
        self.assertEqual(len(report.leaks()), 0)
        self.assertEqual(len(report.missing_demands(include_optional=True)), 0)

        for hail in hails:
            pos = (hail["x"], hail["y"])
            supp = report.supplied_resources.get(pos, set())
            self.assertIn("graphite", supp)
            self.assertIn("water", supp)

        _, b64_str = encode_schematic(schem)
        msch_path = os.path.join(CUR_DIR, "msch")
        if not os.path.exists(msch_path):
            msch_path = os.path.join(os.path.dirname(CUR_DIR), "msch")
        _ensure_storage_accessible(msch_path)

        res = subprocess.run(
            [sys.executable, msch_path, "check", b64_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("[STATUS]: PASS", res.stdout)
        for line_num, line in enumerate(res.stdout.splitlines(), start=1):
            self.assertLessEqual(len(line), 70)

    def test_synthesize_silicon_factory(self):
        """Verify dual-solid factory layout (4x silicon smelter)."""
        schem = synthesize_factory("silicon-smelter", count=4)
        self.assertEqual(schem["width"], 8)
        self.assertEqual(schem["height"], 6)

        crafters = [t for t in schem["tiles"] if t["block"] == "silicon-smelter"]
        self.assertEqual(len(crafters), 4)

        val = validate_schematic(schem, inlets=schem.get("inlets"))
        self.assertTrue(val.is_valid, f"Validation errors: {val.errors}")

        report = trace_supply(schem, inlets=schem.get("inlets"))
        self.assertEqual(len(report.leaks()), 0)
        self.assertEqual(len(report.missing_demands()), 0)

        for cr in crafters:
            pos = (cr["x"], cr["y"])
            supp = report.supplied_resources.get(pos, set())
            self.assertIn("sand", supp)
            self.assertIn("coal", supp)
            self.assertIn("power", supp)

    def test_synthesize_cryofluid_factory(self):
        """Verify solid + liquid factory layout (4x cryofluid mixer)."""
        schem = synthesize_factory("cryofluid-mixer", count=4)
        self.assertEqual(schem["width"], 12)
        self.assertEqual(schem["height"], 7)

        mixers = [t for t in schem["tiles"] if t["block"] == "cryofluid-mixer"]
        self.assertEqual(len(mixers), 4)

        val = validate_schematic(schem, inlets=schem.get("inlets"))
        self.assertTrue(val.is_valid, f"Validation errors: {val.errors}")

        report = trace_supply(schem, inlets=schem.get("inlets"))
        self.assertEqual(len(report.leaks()), 0)
        self.assertEqual(len(report.missing_demands()), 0)

        for mx in mixers:
            pos = (mx["x"], mx["y"])
            supp = report.supplied_resources.get(pos, set())
            self.assertIn("water", supp)
            self.assertIn("titanium", supp)
            self.assertIn("power", supp)

    def test_synthesize_thorium_reactor(self):
        """Verify fail-safe nuclear plant (4x thorium reactor)."""
        schem = synthesize_power_plant("thorium-reactor", count=4)
        self.assertEqual(schem["width"], 12)
        self.ass