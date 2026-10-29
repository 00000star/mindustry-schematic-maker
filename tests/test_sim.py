"""
Unit Test Suite for Mindustry Supply Simulator & Flow Tracer (core/sim.py).
Tests solid item flow, liquid branching, liquid purity, missing demand detection,
and coolant tracking.
"""

import os
import sys
import unittest

# Ensure current and parent dirs are in sys.path
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
if CUR_DIR not in sys.path:
    sys.path.insert(0, CUR_DIR)

try:
    from sim import trace_supply, SupplyReport
    from generator import SchematicBuilder
except ImportError:
    from core.sim import trace_supply, SupplyReport
    from core.generator import SchematicBuilder


class TestSupplySimulator(unittest.TestCase):
    """Test suite for supply simulation, flow tracing, and demand checking."""

    def test_single_conveyor_to_duo(self):
        """Verify that copper flowing on a single conveyor supplies a Duo turret."""
        builder = SchematicBuilder("Single Conveyor Duo")
        # Conveyor at (0, 0) facing East (rot=0) into Duo at (1, 0)
        builder.add("conveyor", 0, 0, rotation=0)
        builder.add("duo", 1, 0, rotation=0)
        builder.inlet(0, 0, "copper")

        schem = builder.build()
        report: SupplyReport = trace_supply(schem)

        # Duo at (1, 0) should be supplied with copper
        self.assertIn("copper", report.supplied_resources.get((1, 0), set()))
        self.assertEqual(len(report.missing_demands()), 0)
        self.assertEqual(len(report.leaks()), 0)
        self.assertTrue(report.is_fully_supplied())

    def test_broken_duo_layout(self):
        """Verify that a broken conveyor gap or disconnected liquid conduit reports missing ammo/coolant."""
        # Scenario A: Missing ammo due to disconnected gap
        builder_gap = SchematicBuilder("Broken Duo Gap")
        # Conveyor at (0, 0) facing East, but Duo is at (2, 0) with gap at (1, 0)
        builder_gap.add("conveyor", 0, 0, rotation=0)
        builder_gap.add("duo", 2, 0, rotation=0)
        builder_gap.inlet(0, 0, "copper")

        schem_gap = builder_gap.build()
        report_gap = trace_supply(schem_gap)

        self.assertFalse(report_gap.is_fully_supplied())
        missing_gap = report_gap.missing_demands()
        self.assertGreater(len(missing_gap), 0)
        self.assertEqual(missing_gap[0]["block"], "duo")
        self.assertEqual(missing_gap[0]["missing"], ["ammo"])
        self.assertEqual(missing_gap[0]["type"], "ammo")

        # Scenario B: Disconnected water conduit when coolant is declared
        builder_coolant = SchematicBuilder("Broken Water Duo")
        # Conveyor delivers copper to Duo at (1, 0)
        builder_coolant.add("conveyor", 0, 0, rotation=0)
        builder_coolant.add("duo", 1, 0, rotation=0)
        builder_coolant.inlet(0, 0, "copper")
        # Water conduit at (0, 2) facing West (away from duo)
        builder_coolant.add("conduit", 0, 2, rotation=2)
        builder_coolant.inlet(0, 2, "water")

        schem_coolant = builder_coolant.build()
        report_coolant = trace_supply(schem_coolant)

        missing_coolant = report_coolant.missing_demands(include_optional=True)
        # Should detect Duo at (1, 0) missing water coolant
        coolant_entries = [m for m in missing_coolant if m["type"] == "coolant"]
        self.assertGreater(len(coolant_entries), 0)
        self.assertEqual(coolant_entries[0]["block"], "duo")
        self.assertIn("water", coolant_entries[0]["missing"])

    def test_liquid_router_branching(self):
        """Verify liquid router splits water into orthogonal conduit branches without leaks."""
        builder = SchematicBuilder("Liquid Router Branching")
        # Input conduit at (0, 1) facing East (rot=0) into liquid router at (1, 1)
        builder.add("conduit", 0, 1, rotation=0)
        builder.add("liquid-router", 1, 1, rotation=0)
        # North branch: conduit at (1, 2) facing North (rot=1) into Wave turret at (1, 3) (2x2)
        builder.add("conduit", 1, 2, rotation=1)
        builder.add("wave", 1, 3, rotation=1)
        # South branch: conduit at (1, 0) facing South (rot=3)
        builder.add("conduit", 1, 0, rotation=3)

        builder.inlet(0, 1, "water")
        schem = builder.build()
        report = trace_supply(schem)

        # Wave turret at (1, 3) should receive water
        self.assertIn("water", report.supplied_resources.get((1, 3), set()))
        # South branch conduit should also receive water
        self.assertIn("water", report.supplied_resources.get((1, 0), set()))
        self.assertEqual(len(report.leaks()), 0)
        self.assertTrue(report.is_fully_supplied())

    def test_liquid_cross_contamination(self):
        """Verify that mixing water and cryofluid in the same conduit network is detected as a leak."""
        builder = SchematicBuilder("Contaminated Network")
        builder.add("conduit", 0, 0, rotation=0)
        builder.add("liquid-router", 1, 0, rotation=0)
        builder.add("conduit", 1, 1, rotation=3)  # points down into liquid router

        # Two different liquids fed into the same network
        builder.inlet(0, 0, "water")
        builder.inlet(1, 1, "cryofluid")

        schem = builder.build()
        report = trace_supply(schem)

        leaks = report.leaks()
        self.assertGreater(len(leaks), 0)
        self.assertTrue(any("contamination" in l.lower() for l in leaks))


if __name__ == "__main__":
    unittest.main()
