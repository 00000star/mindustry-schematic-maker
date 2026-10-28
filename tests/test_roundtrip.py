"""
Comprehensive Unit Test Suite for Mindustry Schematic Maker.
Covers encoding/decoding roundtrip fidelity, TypeIO serialization,
coordinate normalization, procedural generation, and strict <= 70 column rendering.
"""

import unittest
import os
import sys

# Ensure parent and core packages are in import path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from core.blocks import get_block, get_item_id, get_liquid_id
    from core.codec import encode_schematic, decode_schematic
    from core.renderer import render_schematic_ascii
    from core.generator import (
        SchematicBuilder,
        generate_silicon_factory,
        generate_graphite_press,
        generate_metaglass_kiln,
        generate_cryofluid_mixer,
        generate_thorium_reactor_bank,
        generate_defense_line,
        generate_solar_battery_array,
        compile_from_prompt,
    )
except ImportError:
    from blocks import get_block, get_item_id, get_liquid_id
    from codec import encode_schematic, decode_schematic
    from renderer import render_schematic_ascii
    from generator import (
        SchematicBuilder,
        generate_silicon_factory,
        generate_graphite_press,
        generate_metaglass_kiln,
        generate_cryofluid_mixer,
        generate_thorium_reactor_bank,
        generate_defense_line,
        generate_solar_battery_array,
        compile_from_prompt,
    )


class TestMindustrySchematicMaker(unittest.TestCase):

    def test_minimal_roundtrip(self):
        """Verify minimal 1-tile schematic roundtrip encoding and decoding."""
        builder = SchematicBuilder("Minimal Duo", "Single duo turret")
        builder.add("duo", 0, 0, rotation=0)
        schem = builder.build()

        raw_bytes, b64_str = encode_schematic(schem)
        self.assertTrue(raw_bytes.startswith(b"msch\x01"))
        self.assertGreater(len(b64_str), 0)

        decoded = decode_schematic(raw_bytes)
        self.assertEqual(decoded["name"], "Minimal Duo")
        self.assertEqual(decoded["width"], 1)
        self.assertEqual(decoded["height"], 1)
        self.assertEqual(len(decoded["tiles"]), 1)
        self.assertEqual(decoded["tiles"][0]["block"], "duo")
        self.assertEqual(decoded["tiles"][0]["x"], 0)
        self.assertEqual(decoded["tiles"][0]["y"], 0)

        # Also test decoding from base64 string
        decoded_b64 = decode_schematic(b64_str)
        self.assertEqual(decoded_b64["name"], "Minimal Duo")
        self.assertEqual(len(decoded_b64["tiles"]), 1)

    def test_coordinate_normalization_and_multi_tile_bounds(self):
        """Verify that negative/offset coordinates are normalized and bounds match footprints."""
        builder = SchematicBuilder("Offset Bounds Test")
        # Place a 2x2 silicon-smelter at (-5, 10)
        builder.add("silicon-smelter", -5, 10)
        # Place a 3x3 thorium-reactor at (0, 15)
        builder.add("thorium-reactor", 0, 15)
        schem = builder.build()

        raw_bytes, _ = encode_schematic(schem)
        decoded = decode_schematic(raw_bytes)

        # Min coordinates were (-5, 10).
        # silicon-smelter at (-5 - (-5), 10 - 10) = (0, 0). Size 2x2.
        # thorium-reactor at (0 - (-5), 15 - 10) = (5, 5). Size 3x3.
        # Footprint right = 5 + 3 = 8. Footprint top = 5 + 3 = 8.
        self.assertEqual(decoded["width"], 8)
        self.assertEqual(decoded["height"], 8)

        # Smelter at (0, 0)
        smelter = next(t for t in decoded["tiles"] if t["block"] == "silicon-smelter")
        self.assertEqual(smelter["x"], 0)
        self.assertEqual(smelter["y"], 0)

        # Reactor at (5, 5)
        reactor = next(t for t in decoded["tiles"] if t["block"] == "thorium-reactor")
        self.assertEqual(reactor["x"], 5)
        self.assertEqual(reactor["y"], 5)

    def test_typeio_serialization(self):
        """Verify TypeIO serialization for Point2, Point2Array, Content, String, Bytes, Int."""
        builder = SchematicBuilder("TypeIO Test")
        # Sorter with Content (Item Silicon = 9)
        builder.add("sorter", 0, 0, config=("content", 0, 9))
        # Bridge with Point2 link (dx=3, dy=-2)
        builder.add("bridge-conveyor", 1, 0, config=("point2", 3, -2))
        # Power node with Point2Array connections
        builder.add("power-node", 2, 0, config=("point2_array", [(1, 0), (-2, 3)]))
        # Message block with string
        builder.add("message", 3, 0, config="Automated Plant Online")
        # Micro-processor with raw bytecode
        builder.add("micro-processor", 4, 0, config=b"print \"test\"\nprintflush message1")
        # Switch with boolean / int state
        builder.add("switch", 5, 0, config=1)

        schem = builder.build()
        raw_bytes, _ = encode_schematic(schem)
        decoded = decode_schematic(raw_bytes)

        tiles_by_block = {t["block"]: t for t in decoded["tiles"]}

        # Sorter
        self.assertEqual(tiles_by_block["sorter"]["config"], ("content", 0, 9))
        # Bridge
        self.assertEqual(tiles_by_block["bridge-conveyor"]["config"], ("point2", 3, -2))
        # Power node
        self.assertEqual(
            tiles_by_block["power-node"]["config"],
            ("point2_array", [(1, 0), (-2, 3)]),
        )
        # Message
        self.assertEqual(tiles_by_block["message"]["config"], "Automated Plant Online")
        # Micro-processor
        self.assertEqual(
            tiles_by_block["micro-processor"]["config"],
            b"print \"test\"\nprintflush message1",
        )
        # Switch
        self.assertEqual(tiles_by_block["switch"]["config"], 1)

    def test_renderer_column_constraint(self):
        """Assert that ASCII renderer output never exceeds 70 columns on any line."""
        test_cases = [
            generate_silicon_factory(smelters=6),
            generate_thorium_reactor_bank(reactors=2, with_logic=True),
            generate_defense_line(turret="salvo", count=8),
            generate_solar_battery_array(rows=3, cols=4),
        ]

        for schem in test_cases:
            rendered = render_schematic_ascii(schem)
            self.assertGreater(len(rendered), 0)
            for i, line in enumerate(rendered.splitlines()):
                self.assertLessEqual(
                    len(line),
                    70,
                    f"Line {i} exceeds 70 columns ({len(line)}): '{line}'",
                )

    def test_procedural_templates(self):
        """Verify procedural generator templates produce correct block footprints."""
        # Silicon factory
        silicon = generate_silicon_factory(smelters=4)
        self.assertGreater(silicon["width"], 0)
        self.assertGreater(silicon["height"], 0)
        smelter_count = sum(1 for t in silicon["tiles"] if t["block"] == "silicon-smelter")
        self.assertEqual(smelter_count, 4)

        # Graphite press
        graphite = generate_graphite_press(presses=4)
        press_count = sum(1 for t in graphite["tiles"] if t["block"] == "graphite-press")
        self.assertEqual(press_count, 4)

        # Metaglass kiln
        metaglass = generate_metaglass_kiln(kilns=4)
        kiln_count = sum(1 for t in metaglass["tiles"] if t["block"] == "kiln")
        self.assertEqual(kiln_count, 4)

        # Cryofluid mixer
        cryo = generate_cryofluid_mixer(mixers=2)
        mixer_count = sum(1 for t in cryo["tiles"] if t["block"] == "cryofluid-mixer")
        self.assertEqual(mixer_count, 2)

        # Thorium reactor with logic
        thorium = generate_thorium_reactor_bank(reactors=1, with_logic=True)
        reactor_count = sum(1 for t in thorium["tiles"] if t["block"] == "thorium-reactor")
        proc_count = sum(1 for t in thorium["tiles"] if t["block"] == "micro-processor")
        self.assertEqual(reactor_count, 1)
        self.assertEqual(proc_count, 1)

        # Defense line
        defense = generate_defense_line(turret="salvo", count=4)
        salvo_count = sum(1 for t in defense["tiles"] if t["block"] == "salvo")
        self.assertEqual(salvo_count, 4)

        # Solar battery array
        solar = generate_solar_battery_array(rows=2, cols=3)
        solar_count = sum(1 for t in solar["tiles"] if t["block"] == "solar-panel-large")
        self.assertEqual(solar_count, 6)

    def test_base64_decoding_with_slashes(self):
        """Verify that Base64 strings containing '/' characters are parsed as Base64, not paths."""
        schem = generate_silicon_factory(smelters=4)
        _, b64_str = encode_schematic(schem)
        self.assertIn("/", b64_str, "Generated Base64 string should contain '/' character for test.")
        self.assertTrue(b64_str.startswith("bXNjaAF"))

        # Decode directly from Base64 string containing slashes
        decoded = decode_schematic(b64_str)
        self.assertEqual(decoded["name"], schem["name"])
        self.assertEqual(len(decoded["tiles"]), len(schem["tiles"]))
        self.assertEqual(decoded["width"], schem["width"])
        