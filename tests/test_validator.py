"""
Unit Test Suite for Mindustry Static Validator (core/validator.py).
Tests 3-tier validation: structural collisions, link integrity, and supply verification.
"""

import os
import sys
import unittest

# Ensure current and parent dirs are in sys.path
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
if CUR_DIR not in sys.path:
    sys.path.insert(0, CUR_DIR)

try:
    from validator import validate_schematic, ValidationResult
    from generator import SchematicBuilder
except ImportError:
    from core.validator import validate_schematic, ValidationResult
    from core.generator import SchematicBuilder


class TestStaticValidator(unittest.TestCase):
    """Test suite for Tier A, Tier B, and Tier C validation checks."""

    def test_overlapping_blocks_rejected(self):
        """Tier A: Overlapping block footprints must be rejected."""
        # 1x1 block overlapping with 2x2 block
        builder = SchematicBuilder("Overlapping Blocks")
        # 2x2 silicon smelter at (0, 0) occupies (0, 0), (1, 0), (0, 1), (1, 1)
        builder.add("silicon-smelter", 0, 0)
        # 1x1 duo placed at (1, 1) -> Collision!
        builder.add("duo", 1, 1)

        schem = builder.build()
        result: ValidationResult = validate_schematic(schem)

        self.assertFalse(result.is_valid)
        self.assertTrue(any("overlap" in e.lower() for e in result.errors))

    def test_diagonal_or_out_of_range_bridge_rejected(self):
        """Tier B: Bridges with diagonal offsets or distance > 4 must be rejected."""
        # Diagonal bridge
        builder_diag = SchematicBuilder("Diagonal Bridge")
        builder_diag.add("bridge-conveyor", 0, 0, config=("point2", 1, 1))
        builder_diag.add("bridge-conveyor", 1, 1, config=("point2", -1, -1))

        schem_diag = builder_diag.build()
        res_diag = validate_schematic(schem_diag)
        self.assertFalse(res_diag.is_valid)
        self.assertTrue(any("diagonal" in e.lower() for e in res_diag.errors))

        # Out of range bridge (dx = 5 > 4)
        builder_range = SchematicBuilder("Out of Range Bridge")
        builder_range.add("bridge-conveyor", 0, 0, config=("point2", 5, 0))
        builder_range.add("bridge-conveyor", 5, 0, config=("point2", -1, -1))

        schem_range = builder_range.build()
        res_range = validate_schematic(schem_range)
        self.assertFalse(res_range.is_valid)
        self.assertTrue(any("range" in e.lower() for e in res_range.errors))

    def test_head_on_conveyor_collision_rejected(self):
        """Tier B: Conveyors facing directly into each other must be rejected."""
        builder = SchematicBuilder("Head-on Collision")
        # Conveyor at (0, 0) faces East (pointing to (1, 0))
        builder.add("conveyor", 0, 0, rotation=0)
        # Conveyor at (1, 0) faces West (pointing to (0, 0))
        builder.add("conveyor", 1, 0, rotation=2)

        schem = builder.build()
        result = validate_schematic(schem)

        self.assertFalse(result.is_valid)
        self.assertTrue(any("collision" in e.lower() or "head-on" in e.lower() for e in result.errors))

    def test_valid_schematic_accepted(self):
        """Tier C & Builder: Valid schematic passes validation and build_checked succeeds."""
        builder = SchematicBuilder("Valid Defense")
        # Conveyor at (0, 0) facing East into Duo at (1, 0)
        builder.add("conveyor", 0, 0, rotation=0)
        builder.add("duo", 1, 0, rotation=0)
        # Frontline titanium wall
        builder.add("titanium-wall", 2, 0)
        builder.inlet(0, 0, "copper")

        # build_checked should succeed without throwing ValueError
        schem = builder.build_checked()
        self.assertEqual(schem["name"], "Valid Defense")

        result = validate_schematic(schem)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)


if __name__ == "__main__":
    unittest.main()
