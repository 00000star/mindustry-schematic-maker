"""
Algorithmic Universal Schematic Synthesis Engine for Mindustry v7.
Generates multi-input industrial factories, fail-safe power plants,
and universal compact defense fortifications across all block sizes.
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


def synthesize_compact_defense(
    turret_name: str,
    target_count: int = 12,
    cooled: bool = True,
    wall_type: str = "titanium-wall",
) -> Dict[str, Any]:
    """
    Generate an ultra-compact, verified defensive fortification
    supporting multi-size turrets (1x1, 2x2, 3x3).
    
    When cooled=True:
      Vertical continuous-flow alternating columns:
      Left Ammo | Left Turret | Center Water | Right Turret | Right Ammo
      Every turret is flanked by ammo on one side and water on the other.
      Unified bottom inlets for Ammo, Water, and Power/Mender.
      Frontline: Solid row of wall_type.
      
    When cooled=False:
      High-density central router manifold with flanked turrets.
    """
    cleaned = turret_name.strip().lower().replace(" ", "-")
    phys = get_block_physics(cleaned)
    turret_size = phys.size
    pairs = max(1, math.ceil(target_count / 2))
    actual_turret_count = pairs * 2

    # Choose default ammo
    ammo_item = "copper"
    if phys.ammo_options:
        for preferred in ("copper", "graphite", "titanium", "coal", "blast-compound", "plastanium"):
            if preferred in phys.ammo_options:
                ammo_item = preferred
                break
        else:
            ammo_item = sorted(list(phys.ammo_options))[0]

    turret_title = cleaned.replace("-", " ").title()
    title = f"Compact {'Cooled ' if cooled else ''}{turret_title} Defense ({actual_turret_count}x)"
    desc = f"Verified compact {cleaned} fortification ({actual_turret_count} turrets) with continuous-flow manifold."
    builder = SchematicBuilder(name=title, description=desc)

    if cooled:
        total_w = (2 * turret_size) + 3
        left_ammo_x = 0
        left_turret_x = 1
        center_water_x = turret_size + 1
        right_turret_x = turret_size + 2
        right_ammo_x = total_w - 1

        # Row 0: Utilities & Inlets
        builder.add("conveyor", left_ammo_x, 0, rotation=1)
        builder.add("power-node", left_turret_x, 0)
        builder.add("conduit", center_water_x, 0, rotation=1)
        builder.add("mender", right_turret_x, 0)

        # Row 1: Bottom Bridge Jumper (Single unified Ammo inlet at (0, 0))
        if turret_size == 1:
            builder.add("router", left_ammo_x, 1)
            builder.add("bridge-conveyor", left_turret_x, 1, rotation=0, config=("point2", 3, 0))
            builder.add("conduit", center_water_x, 1, rotation=1)
            builder.add("bridge-conveyor", right_ammo_x, 1, rotation=0, config=("point2", -1, -1))
        elif turret_size == 2:
            term_x = right_ammo_x - 1
            builder.add("router", left_ammo_x, 1)
            builder.add("bridge-conveyor", left_turret_x, 1, rotation=0, config=("point2", 4, 0))
            builder.add("conduit", center_water_x, 1, rotation=1)
            builder.add("bridge-conveyor", term_x, 1, rotation=0, config=("point2", -1, -1))
            builder.add("router", right_ammo_x, 1)
        else:
            builder.add("router", left_ammo_x, 1)
            builder.add("conveyor", 1, 1, rotation=0)
            builder.add("bridge-conveyor", 2, 1, rotation=0, config=("point2", 4, 0))
            builder.add("conduit", center_water_x, 1, rotation=1)
            builder.add("bridge-conveyor", 6, 1, rotation=0, config=("point2", -1, -1))
            builder.add("conveyor", 7, 1, rotation=0)
            builder.add("router", right_ammo_x, 1)

        # Turret & Manifold Rows
        start_y = 2
        total_rows = pairs * turret_size

        for r in range(total_rows):
            curr_y = start_y + r
            builder.add("router", left_ammo_x, curr_y)
            builder.add("liquid-router", center_water_x, curr_y)
            builder.add("router", right_ammo_x, curr_y)

        for p in range(pairs):
            t_y = start_y + (p * turret_size)
            builder.add(cleaned, left_turret_x, t_y, rotation=1)
            builder.add(cleaned, right_turret_x, t_y, rotation=1)

        # Top Frontline Walls
        wall_y = start_y + total_rows
        for wx in range(total_w):
            builder.add(wall_type, wx, wall_y)

        # Inlets
        builder.inlet(left_ammo_x, 0, ammo_item)
        builder.inlet(center_water_x, 0, "water")
        builder.inlet(left_turret_x, 0, "power")

    else:
        total_w = (2 * turret_size) + 1
        left_turret_x = 0
        center_ammo_x = turret_size
        right_turret_x = turret_size + 1

        # Row 0: Utilities & Inlets
        builder.add("power-node", left_turret_x, 0)
        builder.add("conveyor", center_ammo_x, 0, rotation=1)
        builder.add("mender", right_turret_x, 0)

        # Turret & Manifold Rows
        start_y = 1
        total_rows = pairs * turret_size

        for r in range(total_rows):
            curr_y = start_y + r
            builder.add("router", center_ammo_x, curr_y)

        for p in range(pairs):
            t_y = start_y + (p * turret_size)
            builder.add(cleaned, left_turret_x, t_y, rotation=1)
            builder.add(cleaned, right_turret_x, t_y, rotation=1)

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


def synthesize_factory(
    recipe_name: str = "silicon-smelter",
    count: int = 4,
) -> Dict[str, Any]:
    """
    Synthesize an industrial factory layout with ratio-balanced routing.
    Supports:
      - Dual-solid input factories (silicon-smelter, kiln, phase-weaver)
      - Solid + Liquid factories (cryofluid-mixer, plastanium-compressor)
      - Single-solid factories (graphite-press)
    """
    cleaned = recipe_name.strip().lower().replace(" ", "-")
    if cleaned in ("silicon", "silicon-smelter"):
        crafter_type = "silicon-smelter"
    elif cleaned in ("metaglass", "kiln", "metaglass-kiln"):
        crafter_type = "kiln"
    elif cleaned in ("phase", "phase-weaver", "phase-fabric"):
        crafter_type = "phase-weaver"
    elif cleaned in ("graphite", "graphite-press"):
        crafter_type = "graphite-press"
    elif cleaned in ("cryofluid", "cryofluid-mixer", "cryo"):
        crafter_type = "cryofluid-mixer"
    elif cleaned in ("plastanium", "plastanium-compressor", "plast"):
        crafter_type = "plastanium-compressor"
    else:
        crafter_type = cleaned

    phys = get_block_physics(crafter_type)
    title = f"Synthesized {crafter_type.replace('-', ' ').title()} Factory ({count}x)"
    desc = f"Verified {crafter_type} industrial facility ({count} units) with continuous-flow routing."
    builder = SchematicBuilder(name=title, description=desc)

    solid_inputs = sorted(list(phys.solid_inputs))
    liquid_inputs = sorted(list(phys.liquid_inputs))
    produces_liquids = bool(phys.produces_liquids)

    # --------------------------------------------------------------------------
    # Case 1: Solid + Liquid Factories (e.g. cryofluid-mixer, plastanium-compressor)
    # --------------------------------------------------------------------------
    if liquid_inputs and solid_inputs:
        width_per_unit = 3
        total_w = count * width_per_unit
        liq_in = liquid_inputs[0]
        solid_in = solid_inputs[0]

        # Row 0: Output line sweeping East
        out_block = "conduit" if produces_liquids else "conveyor"
        for x in range(total_w):
            builder.add(out_block, x, 0, rotation=0)

        for i in range(count):
            bx = i * width_per_unit
            # Crafter 2x2 at (bx, 1)
            builder.add(crafter_type, bx, 1, rotation=0)

            # Row 3: Liquid line. Liquid router at (bx, 3) feeding South into crafter (bx, 2)
            builder.add("liquid-router", bx, 3)
            builder.add("conduit", bx + 1, 3, rotation=0)
            builder.add("conduit", bx + 2, 3, rotation=0)

            # Bridge transmitter at (bx + 2, 4) jumping South to (bx + 2, 2)
            builder.add("bridge-conveyor", bx + 2, 4, rotation=3, config=("point2", 0, -2))
            # Bridge receiver at (bx + 2, 2) facing West into crafter
            builder.add("bridge-conveyor", bx + 2, 2, rotation=2, config=("point2", -1, -1))

            # Row 5: Solid line
            builder.add("conveyor", bx, 5, rotation=0)
            builder.add("conveyor", bx + 1, 5, rotation=0)
            builder.add("router", bx + 2, 5)

            # Row 6: Power node line
            if phys.requires_power:
                builder.add("power-node", bx + 1, 6)

        builder.inlet(0, 3, liq_in)
        builder.inlet(0, 5, solid_in)
        if phys.requires_power:
            builder.inlet(1, 6, "power")

    # --------------------------------------------------------------------------
    # Case 2: Dual-Solid Input Factories (e.g. silicon-smelter, kiln, phase-weaver)
    # --------------------------------------------------------------------------
    elif len(solid_inputs) >= 2:
        width_per_unit = 2
        total_w = count * width_per_unit
        in_a = solid_inputs[0]
        in_b = solid_inputs[1]

        # Row 0: Output conveyor line sweeping East
        for x in range(total_w):
            builder.add("conveyor", x, 0, rotation=0)

        for i in range(count):
            bx = i * width_per_unit
            # Crafter 2x2 at (bx, 1)
            builder.add(crafter_type, bx, 1, rotation=0)

            # Row 3: Input A line (Router at bx feeds South into crafter, Junction at bx+1)
            builder.add("router", bx, 3)
            builder.add("junction", bx + 1, 3)

            # Row 4: Input B line (Conveyor at bx feeds East into Router at bx+1, which feeds South)
            builder.add("conveyor", bx, 4, rotation=0)
            builder.add("router", bx + 1, 4)

            # Row 5: Power node line
            if phys.requires_power:
                builder.add("power-node", bx, 5)

        builder.inlet(0, 3, in_a)
        builder.inlet(0, 4, in_b)
        if phys.requires_power:
            builder.inlet(0, 5, "power")

    # --------------------------------------------------------------------------
    # Case 3: Single-Solid Factory (e.g. graphite-press)
    # --------------------------------------------------------------------------
    else:
        width_per_unit = 2
        total_w = count * width_per_unit
        solid_in = solid_inputs[0] if solid_inputs else "coal"

        # Row 0: Output conveyor sweeping East
        for x in range(total_w):
            builder.add("conveyor", x, 0, rotation=0)

        for i in range(count):
            bx = i * width_per_unit
            builder.add(crafter_type, bx, 1, rotation=0)
            builder.add("router", bx, 3)
            builder.add("conveyor", bx + 1, 3, rotation=0)
            if phys.requires_power:
                builder.add("power-node", bx, 4)

        builder.inlet(0, 3, solid_in)
        if phys.requires_power:
            builder.inlet(0, 4, "power")

    # Static Validation Gate
    schem = builder.build()
    validation = validate_schematic(schem, inlets=builder.inlets)
    if not validation.is_valid:
        raise ValueError(f"Generated factory 