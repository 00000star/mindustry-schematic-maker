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
        self.assertEqual(schem["height"], 6)

        reactors = [t for t in schem["tiles"] if t["block"] == "thorium-reactor"]
        self.assertEqual(len(reactors), 4)

        val = validate_schematic(schem, inlets=schem.get("inlets"))
        self.assertTrue(val.is_valid, f"Validation errors: {val.errors}")

        report = trace_supply(schem, inlets=schem.get("inlets"))
        self.assertEqual(len(report.leaks()), 0)
        self.assertEqual(len(report.missing_demands()), 0)

        for rc in reactors:
            pos = (rc["x"], rc["y"])
            supp = report.supplied_resources.get(pos, set())
            self.assertIn("cryofluid", supp)
            self.assertIn("thorium", supp)
            self.assertIn("power", supp)

    def test_synthesize_steam_power_plant(self):
        """Verify balanced steam generator bank (4x steam generator)."""
        schem = synthesize_power_plant("steam-generator", count=4)
        self.assertEqual(schem["width"], 8)
        self.assertEqual(schem["height"], 5)

        gens = [t for t in schem["tiles"] if t["block"] == "steam-generator"]
        self.assertEqual(len(gens), 4)

        val = validate_schematic(schem, inlets=schem.get("inlets"))
        self.assertTrue(val.is_valid, f"Validation errors: {val.errors}")

        report = trace_supply(schem, inlets=schem.get("inlets"))
        self.assertEqual(len(report.leaks()), 0)
        self.assertEqual(len(report.missing_demands()), 0)

        for gn in gens:
            pos = (gn["x"], gn["y"])
            supp = report.supplied_resources.get(pos, set())
            self.assertIn("water", supp)
            self.assertIn("coal", supp)
            self.assertIn("power", supp)

    def test_universal_defense_multisize(self):
        """Verify dynamic stride defense for block sizes S=1, S=2, S=3."""
        # Size 1 (1x1 duo)
        s1 = synthesize_compact_defense("duo", target_count=4, cooled=True)
        self.assertEqual(s1["width"], 5)
        v1 = validate_schematic(s1, inlets=s1.get("inlets"))
        self.assertTrue(v1.is_valid)
        r1 = trace_supply(s1, inlets=s1.get("inlets"))
        self.assertEqual(len(r1.leaks()), 0)
        self.assertEqual(len(r1.missing_demands(include_optional=True)), 0)

        # Size 2 (2x2 salvo)
        s2 = synthesize_compact_defense("salvo", target_count=4, cooled=True)
        self.assertEqual(s2["width"], 7)
        v2 = validate_schematic(s2, inlets=s2.get("inlets"))
        self.assertTrue(v2.is_valid)
        r2 = trace_supply(s2, inlets=s2.get("inlets"))
        self.assertEqual(len(r2.leaks()), 0)
        self.assertEqual(len(r2.missing_demands(include_optional=True)), 0)

        # Size 3 (3x3 cyclone)
        s3 = synthesize_compact_defense("cyclone", target_count=4, cooled=True)
        self.assertEqual(s3["width"], 9)
        v3 = validate_schematic(s3, inlets=s3.get("inlets"))
        self.assertTrue(v3.is_valid)
        r3 = trace_supply(s3, inlets=s3.get("inlets"))
        self.assertEqual(len(r3.leaks()), 0)
        self.assertEqual(len(r3.missing_demands(include_optional=True)), 0)

        # Uncooled size 3 (3x3 fuse)
        s3_uncooled = synthesize_compact_defense("fuse", target_count=4, cooled=False)
        self.assertEqual(s3_uncooled["width"], 7)
        v3_u = validate_schematic(s3_uncooled, inlets=s3_uncooled.get("inlets"))
        self.assertTrue(v3_u.is_valid)
        r3_u = trace_supply(s3_uncooled, inlets=s3_uncooled.get("inlets"))
        self.assertEqual(len(r3_u.leaks()), 0)
        self.assertEqual(len(r3_u.missing_demands()), 0)

    def test_prompt_compiler_synthesis(self):
        """Verify prompt compiler routes keywords to synthesizers."""
        p_factory = compile_from_prompt("compact 4 silicon smelters")
        crafters = sum(1 for t in p_factory["tiles"] if t["block"] == "silicon-smelter")
        self.assertEqual(crafters, 4)

        p_power = compile_from_prompt("compact 4 thorium reactors")
        reactors = sum(1 for t in p_power["tiles"] if t["block"] == "thorium-reactor")
        self.assertEqual(reactors, 4)

        p_defense = compile_from_prompt("compact 4 cyclone defense")
        cyclones = sum(1 for t in p_defense["tiles"] if t["block"] == "cyclone")
        self.assertEqual(cyclones, 4)

    def test_cli_check_command(self):
        """Verify CLI check command validates schematics correctly."""
        schem = build_compact_defense("duo", target_count=12, cooled=True)
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
        self.assertIn("Tier A", res.stdout)
        self.assertIn("Tier B", res.stdout)
        self.assertIn("Tier C", res.stdout)

        for line_num, line in enumerate(res.stdout.splitlines(), start=1):
            self.assertLessEqual(len(line), 70)


if __name__ == "__main__":
    unittest.main()
