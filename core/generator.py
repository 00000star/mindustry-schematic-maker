"""
Procedural Mindustry Schematic Generator and Natural Language Compiler.
Generates production-grade, mathematically aligned factory layouts,
reactor banks with logic safety failsafes, and defensive fortifications.
"""

import re
from typing import Any, Dict, List, Optional

try:
    from .blocks import get_block, ITEMS, LIQUIDS
except ImportError:
    try:
        from core.blocks import get_block, ITEMS, LIQUIDS
    except ImportError:
        from blocks import get_block, ITEMS, LIQUIDS


class SchematicBuilder:
    """Fluent API for constructing Mindustry schematics tile-by-tile."""

    def __init__(self, name: str = "Custom Schematic", description: str = ""):
        self.name = name
        self.description = description
        self.tags: Dict[str, str] = {
            "name": name,
            "description": description,
        }
        self.tiles: List[Dict[str, Any]] = []

    def set_tag(self, key: str, value: str) -> "SchematicBuilder":
        self.tags[key] = str(value)
        return self

    def add(
        self,
        block: str,
        x: int,
        y: int,
        rotation: int = 0,
        config: Any = None,
    ) -> "SchematicBuilder":
        """Add a single block to the schematic."""
        self.tiles.append({
            "block": block,
            "x": int(x),
            "y": int(y),
            "rotation": int(rotation),
            "config": config,
        })
        return self

    def add_conveyor_line(
        self,
        start_x: int,
        start_y: int,
        length: int,
        direction: int = 0,
        conveyor_type: str = "conveyor",
    ) -> "SchematicBuilder":
        """
        Add a straight line of conveyors.
        Direction: 0: +X (East), 1: +Y (North), 2: -X (West), 3: -Y (South)
        """
        dx = 1 if direction == 0 else (-1 if direction == 2 else 0)
        dy = 1 if direction == 1 else (-1 if direction == 3 else 0)

        for i in range(length):
            cx = start_x + (i * dx)
            cy = start_y + (i * dy)
            self.add(conveyor_type, cx, cy, rotation=direction)
        return self

    def add_wall_row(
        self,
        start_x: int,
        start_y: int,
        length: int,
        horizontal: bool = True,
        wall_type: str = "copper-wall",
    ) -> "SchematicBuilder":
        """Add a row of defensive walls."""
        binfo = get_block(wall_type)
        step = binfo.size
        for i in range(0, length, step):
            wx = start_x + (i if horizontal else 0)
            wy = start_y + (0 if horizontal else i)
            self.add(wall_type, wx, wy, rotation=0)
        return self

    def build(self) -> Dict[str, Any]:
        """Compile and return normalized schematic dictionary."""
        if not self.tiles:
            return {
                "name": self.name,
                "description": self.description,
                "width": 0,
                "height": 0,
                "tags": self.tags,
                "tiles": [],
            }

        # Calculate bounding dimensions
        min_x = min(t["x"] for t in self.tiles)
        min_y = min(t["y"] for t in self.tiles)
        max_x = max(t["x"] + get_block(t["block"]).size for t in self.tiles)
        max_y = max(t["y"] + get_block(t["block"]).size for t in self.tiles)

        return {
            "name": self.name,
            "description": self.description,
            "width": max_x - min_x,
            "height": max_y - min_y,
            "tags": self.tags,
            "tiles": list(self.tiles),
        }


# ==============================================================================
# Procedural Factory & Base Templates
# ==============================================================================

def generate_silicon_factory(smelters: int = 4) -> Dict[str, Any]:
    """
    Generate an optimized modular Silicon Smelter factory.
    Uses router/conveyor input line for Coal & Sand and an output line for Silicon.
    """
    builder = SchematicBuilder(
        name=f"Silicon Factory ({smelters}x)",
        description=f"Modular automated silicon production with {smelters} smelters."
    )

    # Smelters are 2x2.
    # Grid:
    # Row 0: Output conveyor line (West to East)
    # Row 1-2: Smelters
    # Row 3: Input conveyor line with routers (Sand + Coal)
    # Row 4: Power nodes
    for i in range(smelters):
        base_x = i * 3
        # Smelter (2x2)
        builder.add("silicon-smelter", base_x, 1)

        # Output conveyor below
        builder.add("conveyor", base_x, 0, rotation=0)
        builder.add("conveyor", base_x + 1, 0, rotation=0)
        builder.add("conveyor", base_x + 2, 0, rotation=0)

        # Input distribution above (Router at center, conveyor link)
        builder.add("router", base_x, 3, rotation=0)
        builder.add("conveyor", base_x + 1, 3, rotation=0)
        builder.add("conveyor", base_x + 2, 3, rotation=0)

        # Power node
        builder.add("power-node", base_x + 2, 1, rotation=0)

    # Final output conveyor extension
    builder.add("conveyor", smelters * 3, 0, rotation=0)
    return builder.build()


def generate_graphite_press(presses: int = 4) -> Dict[str, Any]:
    """Generate a clean compact Graphite Press array with router manifold."""
    builder = SchematicBuilder(
        name=f"Graphite Factory ({presses}x)",
        description=f"Automated graphite production with {presses} presses."
    )
    for i in range(presses):
        base_x = i * 3
        builder.add("graphite-press", base_x, 1)
        # Output conveyor
        builder.add("conveyor", base_x, 0, rotation=0)
        builder.add("conveyor", base_x + 1, 0, rotation=0)
        builder.add("conveyor", base_x + 2, 0, rotation=0)

        # Input router & conveyor
        builder.add("router", base_x, 3, rotation=0)
        builder.add("conveyor", base_x + 1, 3, rotation=0)
        builder.add("conveyor", base_x + 2, 3, rotation=0)

        # Power node
        builder.add("power-node", base_x + 2, 1, rotation=0)

    return builder.build()


def generate_metaglass_kiln(kilns: int = 4) -> Dict[str, Any]:
    """Generate an automated Metaglass Kiln production line."""
    builder = SchematicBuilder(
        name=f"Metaglass Kiln Line ({kilns}x)",
        description=f"Dual-input metaglass kiln array for lead and sand."
    )
    for i in range(kilns):
        base_x = i * 3
        builder.add("kiln", base_x, 1)
        # Output
        builder.add("conveyor", base_x, 0, rotation=0)
        builder.add("conveyor", base_x + 1, 0, rotation=0)
        builder.add("conveyor", base_x + 2, 0, rotation=0)
        # Input manifold
        builder.add("router", base_x, 3, rotation=0)
        builder.add("conveyor", base_x + 1, 3, rotation=0)
        builder.add("conveyor", base_x + 2, 3, rotation=0)
        # Power
        builder.add("power-node", base_x + 2, 1, rotation=0)

    return builder.build()


def generate_cryofluid_mixer(mixers: int = 2) -> Dict[str, Any]:
    """Generate a Cryofluid Mixer setup with titanium feed and water conduits."""
    builder = SchematicBuilder(
        name=f"Cryofluid Plant ({mixers}x)",
        description=f"Continuous cryofluid production with {mixers} mixers."
    )
    for i in range(mixers):
        base_x = i * 4
        builder.add("cryofluid-mixer", base_x, 1)

        # Water input conduit (North)
        builder.add("conduit", base_x, 3, rotation=3)
        # Titanium input conveyor (South)
        builder.add("conveyor", base_x, 0, rotation=1)

        # Output cryofluid conduit (East)
        builder.add("conduit", base_x + 2, 1, rotation=0)
        builder.add("conduit", base_x + 2, 2, rotation=0)

        # Power
        builder.add("power-node", base_x + 3, 1, rotation=0)

    return builder.build()


def generate_thorium_reactor_bank(
    reactors: int = 1,
    with_logic: bool = True,
) -> Dict[str, Any]:
    """
    Generate a safe Thorium Nuclear Reactor bank.
    Includes cryofluid feed, thorium input line, battery buffer, and
    optional microprocessor anti-meltdown logic controller.
    """
    builder = SchematicBuilder(
        name=f"Thorium Reactor ({reactors}x Safe)",
        description="Nuclear thorium generator with automated failsafe."
    )

    # Reactor is 3x3
    for i in range(reactors):
        rx = i * 5
        builder.add("thorium-reactor", rx, 1)

        # Cryofluid feed conduit
        builder.add("conduit", rx, 0, rotation=1)
        builder.add("conduit", rx + 1, 0, rotation=1)

        # Thorium feed conveyor
        builder.add("conveyor", rx + 2, 0, rotation=1)

        # Power nodes and battery buffer
        builder.add("power-node-large", rx + 3, 1)
        builder.add("battery", rx + 3, 3)

        if with_logic:
            # Micro-processor at (rx, 4) with failsafe logic code
            # MLOG: read cryofluid level from reactor, disable if cryofluid < 10
            mlog_code = (
                "sensor cryo reactor1 @cryofluid\n"
                "op greaterThan safe cryo 10\n"
                "control enabled reactor1 safe 0 0 0\n"
            )
            builder.add(
                "micro-processor",
                rx,
                4,
                rotation=0,
                config=("bytes", mlog_code.encode("utf-8")),
            )

    return builder.build()


def generate_defense_line(turret: str = "salvo", count: int = 4) -> Dict[str, Any]:
    """Generate a fortified defensive perimeter with walls, turrets, and ammo routing."""
    turret_name = turret.strip().lower()
    binfo = get_block(turret_name)
    tsize = binfo.size

    builder = SchematicBuilder(
        name=f"Defense Line ({count}x {turret_name.capitalize()})",
        description=f"Fortified combat line with {count} {turret_name} turrets and walls."
    )

    total_width = count * tsize

    # 1. Front Wall line (Titanium Wall)
    for x in range(total_width):
        builder.add("titanium-wall", x, tsize + 1)

    # 2. Turrets
    for i in range(count):
        tx = i * tsize
        builder.add(turret_name, tx, 1)

    # 3. Ammo conveyor & router line behind turrets
    for x in range(total_width):
        if x % tsize == 0:
            builder.add("router", x, 0)
        else:
            builder.add("conveyor", x, 0, rotation=0)

    # 4. Mender support
    builder.add("mender", total_width, 1)
    builder.add("power-node", total_width, 0)

    return builder.build()


def generate_scorch_bunker(count: int = 5) -> Dict[str, Any]:
    """
    Generate an optimized Scorch Killbox Choke layout.
    Scorch has extreme point-blank DPS but short range (6 tiles) and flames
    do NOT pass through walls. This layout uses open frontline line-of-sight
    with flank walls creating a deadly choke funnel, and an alternating
    Router/Overflow-Gate manifold feeding every turret.
    Layout:
      - y=3: Front Line - Flank walls at x=0 and x=count+1. Center (x=1..count) is OPEN.
      - y=2: Combat Line - Flank walls at x=0 and x=count+1. Center (x=1..count): Scorches (rotation=1 North).
      - y=1: Ammo Manifold - Flank walls at x=0 and x=count+1. Center (x=1..count): alternating Router and Overflow-Gate.
      - y=0: Support / Rear - Flank walls at x=0 and x=count+1. Ammo input conveyor at (1, 0) (rotation=1 North).
             Mender at center, Power Node adjacent.
    """
    builder = SchematicBuilder(
        name=f"Scorch Killbox Choke ({count}x)",
        description=f"Deadly close-range choke with {count} North-facing Scorches, open line-of-sight, flank walls, and router-overflow ammo manifold."
    )

    right_flank_x = count + 1

    # 1. Flank Walls on left (x=0) and right (x=count+1)
    for y in range(4):
        builder.add("titanium-wall", 0, y)
        builder.add("titanium-wall", right_flank_x, y)

    # 2. Combat Line (y=2): Scorches facing North (rotation=1)
    # y=3 is intentionally left OPEN in front of scorches (x=1..count) for unobstructed line of sight
    for x in range(1, count + 1):
        builder.add("scorch", x, 2, rotation=1)

    # 3. Ammo Manifold (y=1): Alternating router and overflow-gate
    for x in range(1, count + 1):
        if (x - 1) % 2 == 0:
            builder.add("router", x, 1)
        else:
            builder.add("overflow-gate", x, 1)

    # 4. Support / Rear (y=0)
    # Ammo input conveyor feeding the first router at (1, 1)
    builder.add("conveyor", 1, 0, rotation=1)

    # Mender at center (for count=5, center is x=3)
    center_x = max(2, (count + 2) // 2)
    builder.add("mender", center_x, 0)

    # Power Node adjacent to mender
    node_x = center_x + 1 if center_x + 1 < right_flank_x else center_x - 1
    if node_x == 1:  # Don't overwrite conveyor at (1, 0)
        node_x = center_x + 1
    builder.add("power-node", node_x, 0)

    return builder.build()


def generate_water_cooled_duo_fortress(width: int = 8) -> Dict[str, Any]:
    """
    High-density defensive fortress packing 13 Water-Cooled Duos behind frontline
    Titanium Walls with continuous router-overflow ammo feed and bridge conduit liquid cooling.
    """
    builder = SchematicBuilder(
        name="Water-Cooled Duo Fortress (13x)",
        description="High-density defensive fortress packing 13 Water-Cooled Duos behind frontline Titanium Walls with continuous router-overflow ammo feed and bridge conduit liquid cooling."
    )

    # Row 5 (y=5): 8x titanium-wall at x=0..7
    for x in range(8):
        builder.add("titanium-wall", x, 5)

    # Row 4 (y=4): x=1,4,7 are conduit (rotation=1 North); x=0,2,3,5,6 are duo (rotation=1 North)
    for x in range(8):
        if x in (1, 4, 7):
            builder.add("conduit", x, 4, rotation=1)
        else:
            builder.add("duo", x, 4, rotation=1)

    # Row 3 (y=3): x=0,2,4,6 are router (rot=0); x=1,3,5,7 are overflow-gate (rot=0)
    for x in range(8):
        if x in (0, 2, 4, 6):
            builder.add("router", x, 3, rotation=0)
        else:
            builder.add("overflow-gate", x, 3, rotation=0)

    # Row 2 (y=2): 8x duo at x=0..7 (rot=1 North)
    for x in range(8):
        builder.add("duo", x, 2, rotation=1)

    # Row 1 (y=1): x=1,4,7 are bridge-conduit (rot=1 North, config=('point2', 0, 3)); x=0,2,3,5,6 are conduit (rot=0 East)
    for x in range(8):
        if x in (1, 4, 7):
            builder.add("bridge-conduit", x, 1, rotation=1, config=("point2", 0, 3))
        else:
            builder.add("conduit", x, 1, rotation=0)

    # Row 0 (y=0):
    # (0, 0): bridge-conveyor (rot=1 North, config=('point2', 0, 3)) [ammo inlet]
    # (7, 0): conduit (rot=1 North) [water inlet]
    # (1, 0), (2, 0), (5, 0), (6, 0): titanium-wall
    # (3, 0): mender
    # (4, 0): power-node
    builder.add("bridge-conveyor", 0, 0, rotation=1, config=("point2", 0, 3))
    builder.add("conduit", 7, 0, rotation=1)
    for x in (1, 2, 5, 6):
        builder.add("titanium-wall", x, 0)
    builder.add("mender", 3, 0)
    builder.add("power-node", 4, 0)

    return builder.build()


def generate_solar_battery_array(rows: int = 2, cols: int = 3) -> Dict[str, Any]:
    """Generate a clean compact solar panel and battery grid."""
    builder = SchematicBuilder(
        name=f"Solar Array ({rows}x{cols})",
        description=f"Clean renewable energy grid with {rows*cols} large solar panels."
    )
    for r in range(rows):
        for c in range(cols):
            x = c * 4
            y = r * 4
            # Large solar panel is 3x3
            builder.add("solar-panel-large", x, y)
            # Battery in gap
            builder.add("battery", x + 3, y)
            builder.add("power-node", x + 3, y + 1)

    return builder.build()


def generate_community_duo_fortress() -> Dict[str, Any]:
    """
    High-density defensive fortress with 16 Duos powered by central Overdrive Projector
    (1.5x fire rate) and Underflow Gate manifolds behind frontline Titanium Walls.
    Learned from community architectures with 100% paired bridge conveyors.
    """
    builder = SchematicBuilder(
        name="Community Duo Fortress (Overdriven)",
        description="High-density defensive fortress with 16 Duos powered by central Overdrive Projector (1.5x fire rate) and Underflow Gate manifolds behind frontline Titanium Walls."
    )

    # Row 6 (y=6): 7x titanium-wall frontline defense
    for x in range(7):
        builder.add("titanium-wall", x, 6)

    # Row 5 (y=5): duos at x=0, 1, 3, 5, 6; routers at x=2, 4
    for x in (0, 1, 3, 5, 6):
        builder.add("duo", x, 5, rotation=1)
    builder.add("router", 2, 5, rotation=0)
    builder.add("router", 4, 5, rotation=0)

    # Row 4 (y=4): duos at x=0, 1, 3, 5, 6; underflow-gates at x=2, 4
    for x in (0, 1, 3, 5, 6):
        builder.add("duo", x, 4, rotation=1)
    builder.add("underflow-gate", 2, 4, rotation=0)
    builder.add("underflow-gate", 4, 4, rotation=0)

    # Row 3 (y=3): Ammo bus with paired bridges and central Overdrive Projector
    # Hop 1: x=0 -> x=2 (+2, 0)
    # Hop 2: x=2 -> x=4 (+2, 0)
    # Hop 3: x=4 -> x=6 (+2, 0)
    builder.add("bridge-conveyor", 0, 3, rotation=0, config=("point2", 2, 0))
    builder.add("duo", 1, 3, rotation=1)
    builder.add("bridge-conveyor", 2, 3, rotation=0, config=("point2", 2, 0))
    builder.add("overdrive-projector", 3, 3, rotation=0)
    builder.add("bridge-conveyor", 4, 3, rotation=0, config=("point2", 2, 0))
    builder.add("duo", 5, 3, rotation=1)
    builder.add("bridge-conveyor", 6, 3, rotation=0, config=("point2", -1, -1))

    # Row 2 (y=2): duos at x=0, 1, 3, 5, 6; underflow-gates at x=2, 4
    for x in (0, 1, 3, 5, 6):
        builder.add("duo", x, 2, rotation=1)
    builder.add("underflow-gate", 2, 2, rotation=0)
    builder.add("underflow-gate", 4, 2, rotation=0)

    # Row 1 (y=1): duos at x=0, 1, 3, 5, 6; routers at x=2, 4
    for x in (0, 1, 3, 5, 6):
        builder.add("duo", x, 1, rotation=1)
    builder.add("router", 2, 1, rotation=0)
    builder.add("router", 4, 1, rotation=0)

    # Row 0 (y=0): Base anchors, Mender and Power Node
    for x in (0, 1, 4, 5, 6):
        builder.add("titanium-wall", x, 0)
    builder.add("mender", 2, 0)
    builder.add("power-node", 3, 0)

    return builder.build()


# ==============================================================================
# Natural Language Prompt Compiler
# ==============================================================================

def compile_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Parse a natural language prompt and procedurally compile
    the corresponding Mindustry schematic.
    Examples:
      - "4 silicon smelter"
      - "8 graphite presses"
      - "thorium reactor with logic"
      - "defense line salvo 6"
      - "solar battery array"
    """
    text = prompt.lower().strip()

    # Extract first integer count from prompt (default to 4 if none specified)
    count = 4
    match = re.search(r"\b(\d+)\b", text)
    if match:
        count = max(1, min(int(match.group(1)), 32))

    # Match prompt intents
    if "duo" in text and ("fortress" in text or "overdrive" in text or "defense" in text or "community" in text or "water" in text):
        return generate_community_duo_fortress()

    elif "scorch" in text or "scrotch" in text or "killbox" in text or "choke" in text:
        return generate_scorch_bunker(count=count)

    elif "silicon" in text or "smelter" in text:
        return generate_silicon_factory(smelters=count)

    elif "graphite" in text or "press" in text:
        return generate_graphite_press(presses=count)

    elif "metaglass" in text or "kiln" in text:
        return generate_metaglass_kiln(kilns=count)

    elif "cryo" in text or "cryofluid" in text:
        mixers = max(1, count // 2 if count > 2 else count)
        return generate_cryofluid_mixer(mixers=mixers)

    elif "thorium" in text or "reactor" in text or "nuclear" in text or "nuke" in text:
        reactors = max(1, count if count <= 4 else count // 2)
        with_logic = "no logic" not in text and "without logic" not in text
        return generate_thorium_reactor_bank(reactors=reactors, with_logic=with_logic)

    elif "solar" in text or "battery" in text or "power" in text:
        cols = max(2, min(count, 5))
        rows = 2
        return generate_solar_battery_array(rows=rows, cols=cols)

    elif ("water" in text or "cooled" in text or "coolant" in text) and "duo" in text:
        return generate_water_cooled_duo_fortress(width=8)

    elif "defense" in text or "wall" in text or "turret" in text or "salvo" in text or "duo" in text or "scatter" in text or "lancer" in text:
        turret = "salvo"
        for candidate in ["duo", "scatter", "lancer", "salvo", "fuse", "cyclone", "ripple"]:
            if candidate in text:
                turret = candidate
                break
        return generate_defense_line(turret=turret, count=count)

    else:
        # Default fallback: silicon factory
        return generate_silicon_factory(smelters=count)
