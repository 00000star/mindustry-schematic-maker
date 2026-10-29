"""
Algorithmic Compact Layout Generator for Mindustry v7.
Generates ultra-compact, continuous-flow defense fortifications and modular factories.
All generated schematics are statically validated before delivery.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

try:
    from .rules import get_block_physics
    from .generator import SchematicBuilder
    from .validator import validate_schematic, ValidationResult
    from .sim import trace_supply
except ImportError:
    try:
        from core.rules import get_block_physics
        from core.generator import SchematicBuilder
        from core.validator import validate_schematic, ValidationResult
        from core.sim import trace_supply
    except ImportError:
        from rules import get_block_physics
        from generator import SchematicBuilder
        from validator import validate_schematic, ValidationResult
        from sim import trace_supply


def build_compact_defense(
    turret_name: str,
    target_count: int = 12,
    cooled: bool = False,
    wall_type: str = "titanium-wall",
) -> Dict[str, Any]:
    """
    Generate an ultra-compact, verified defensive fortification.
    
    When cooled=True:
      Vertical continuous-flow alternating columns:
      Ammo Router | Turret Col | Water Conduit Col | Turret Col | Ammo Router
      Every turret is flanked by ammo on one side and water on the other.
      Unified bottom inlets for Ammo, Water, and Power/Mender.
      Frontline: Solid row of wall_type.
      
    When cooled=False:
      High-density central router/underflow manifold with flanked turrets.
    """
    phys = get_block_physics(turret_name)
    turret_size = phys.size
    pairs = max(1, math.ceil(target_count / 2))
    actual_turret_count = pairs * 2

    # Choose default ammo
    ammo_item = "copper"
    if phys.ammo_options:
        if "copper" in phys.ammo_options:
            ammo_item = "copper"
        elif "coal" in phys.ammo_options:
            ammo_item = "coal"
        else:
            ammo_item = sorted(list(phys.ammo_options))[0]

    title = f"Compact {'Cooled ' if cooled else ''}{turret_name.capitalize()} Defense ({actual_turret_count}x)"
    desc = f"Verified compact {turret_name} fortification ({actual_turret_count} turrets) with continuous-flow manifold."
    builder = SchematicBuilder(name=title, description=desc)

    if cooled:
        # ======================================================================
        # Water-Cooled Continuous-Flow Architecture
        # ======================================================================
        # Width: 2 * turret_size + 3
        # Left Ammo: x = 0
        # Left Turret: x = 1 .. turret_size
        # Center Water: x = turret_size + 1
        # Right Turret: x = turret_size + 2 .. 2 * turret_size + 1
        # Right Ammo: x = 2 * turret_size + 2
        total_w = (2 * turret_size) + 3
        left_ammo_x = 0
        left_turret_x = 1
        center_water_x = turret_size + 1
        right_turret_x = turret_size + 2
        right_ammo_x = total_w - 1

        # Row 0: Utilities & Inlets
        # Power Node & Mender flanking the bottom water inlet
        builder.add("conveyor", left_ammo_x, 0, rotation=1)
        builder.add("power-node", left_turret_x, 0)
        builder.add("conduit", center_water_x, 0, rotation=1)
        builder.add("mender", right_turret_x, 0)

        # Row 1: Bottom Bridge Jumper (Single unified Ammo inlet at (0, 1))
        if turret_size == 1:
            # For 1x1: Jump directly from x=1 to x=4 (dx = 3 <= 4)
            builder.add("router", left_ammo_x, 1)
            builder.add("bridge-conveyor", left_turret_x, 1, config=("point2", 3, 0))
            builder.add("conduit", center_water_x, 1, rotation=1)
            builder.add("bridge-conveyor", right_ammo_x, 1, config=("point2", -1, -1))
        else:
            # For 2x2: Jump from x=1 to x=right_ammo_x - 1 (dx = 4 <= 4)
            term_x = right_ammo_x - 1
            builder.add("router", left_ammo_x, 1)
            builder.add("bridge-conveyor", left_turret_x, 1, config=("point2", term_x - left_turret_x, 0))
            builder.add("conduit", center_water_x, 1, rotation=1)
            builder.add("bridge-conveyor", term_x, 1, config=("point2", -1, -1))
            builder.add("router", right_ammo_x, 1)

        # Turret & Manifold Rows: y = 2 to 2 + pairs * turret_size - 1
        start_y = 2
        total_rows = pairs * turret_size

        for r in range(total_rows):
            curr_y = start_y + r
            builder.add("router", left_ammo_x, curr_y)
            builder.add("liquid-router", center_water_x, curr_y)
            builder.add("router", right_ammo_x, curr_y)

        for p in range(pairs):
            t_y = start_y + (p * turret_size)
            builder.add(turret_name, left_turret_x, t_y, rotation=1)
            builder.add(turret_name, right_turret_x, t_y, rotation=1)

        # Top Frontline Walls: solid row at start_y + total_rows
        wall_y = start_y + total_rows
        for wx in range(total_w):
            builder.add(wall_type, wx, wall_y)

        # Inlets
        builder.inlet(left_ammo_x, 0, ammo_item)
        builder.inlet(center_water_x, 0, "water")
        builder.inlet(left_turret_x, 0, "power")

    else:
        # ======================================================================
        # Uncooled High-Density Manifold Architecture
        # ======================================================================
        # For 1x1 turrets:
        # Col 0: Left Turret | Col 1: Ammo Router | Col 2: Right Turret
        # Width: 3
        # For 2x2 turrets:
        # Left Turret (x=0,1) | Ammo Router (x=2) | Right Turret (x=3,4)
        # Width: 5
        total_w = (2 * turret_size) + 1
        left_turret_x = 0
        center_ammo_x = turret_size
        right_turret_x = turret_size + 1

        # Row 0: Utilities & Inlets
        builder.add("power-node", left_turret_x, 0)
        builder.add("conveyor", center_ammo_x, 0, rotation=1)  # Ammo inlet pushing North
        builder.add("mender", right_turret_x, 0)

        # Turret & Manifold Rows: y = 1 to 1 + pairs * turret_size - 1
        start_y = 1
        total_rows = pairs * turret_size

        for r in range(total_rows):
            curr_y = start_y + r
            builder.add("router", center_ammo_x, curr_y)

        for p in range(pairs):
            t_y = start_y + (p * turret_size)
            builder.add(turret_name, left_turret_x, t_y, rotation=1)
            builder.add(turret_name, right_turret_x, t_y, rotation=1)

        # Top Frontline Walls
        wall_y = start_y + total_rows
        for wx in range(total_w):
            builder.add(wall_type, wx, wall_y)

        # Inlets
        builder.inlet(center_ammo_x, 0, ammo_item)
        builder.inlet(left_turret_x, 0, "power")

    # Static Validation Gate
    schem = builder.build()
    validation = validate_schematic(schem, inlets=builder.inlets)
    if not validation.is_valid:
        raise ValueError(f"Generated compact defense failed validation: {'; '.join(validation.errors)}")

    # Supply Verification Gate
    supply_report = trace_supply(schem, inlets=builder.inlets)
    missing = supply_report.missing_demands(include_optional=cooled)
    if missing:
        missing_desc = [f"{m['block']} at ({m['x']},{m['y']}) missing {m['missing']}" for m in missing]
        raise ValueError(f"Generated defense has unsupplied consumers: {'; '.join(missing_desc)}")

    return schem


def build_compact_factory(
    factory_type: str = "silicon-smelter",
    count: int = 4,
) -> Dict[str, Any]:
    """
    Generate a compact, ratio-balanced modular factory layout with perimeter belts.
    Supported factories: silicon-smelter, graphite-press, kiln, cryofluid-mixer.
    """
    cleaned = factory_type.strip().lower().replace(" ", "-")
    phys = get_block_physics(cleaned)
    f_size = phys.size

    title = f"Compact {cleaned.replace('-', ' ').title()} Factory ({count}x)"
    desc = f"Optimized modular {cleaned} production facility with {count} crafters."
    builder = SchematicBuilder(name=title, description=desc)

    # Standard linear modular layout:
    # Row 0: Output conveyor line (West to East)
    # Rows 1 to f_size: Factory crafters
    # Row f_size + 1: Input conveyor/router distribution line
    # Row f_size + 2: Power nodes line
    width_per_unit = f_size + 1
    total_w = count * width_per_unit

    # Row 0: Output conveyor line
    for x in range(total_w):
        builder.add("conveyor", x, 0, rotation=0)

    # Factories and distribution
    for i in range(count):
        bx = i * width_per_unit
        # Add crafter
        builder.add(cleaned, bx, 1, rotation=0)

        # Input distribution in row f_size + 1
        builder.add("router", bx, f_size + 1, rotation=0)
        for dx in range(1, width_per_unit):
            builder.add("conveyor", bx + dx, f_size + 1, rotation=0)

        # Power node in row f_size + 2
        builder.add("power-node", bx + 1, f_size + 2, rotation=0)

    # Declare Inlets
    if phys.solid_inputs:
        for inp in sorted(phys.solid_inputs):
            builder.inlet(0, f_size + 1, inp)
    builder.inlet(1, f_size + 2, "power")

    schem = builder.build()
    validation = validate_schematic(schem, inlets=builder.inlets)
    if not validation.is_valid:
        raise ValueError(f"Generated factory failed validation: {'; '.join(validation.errors)}")

    return schem
