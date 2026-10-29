"""
Mindustry v7 3-Tier Static Schematic Validator.
Tier A: Structural geometry (overlap detection, normalization, bounding box).
Tier B: Link integrity (bridge pairing, range, orthogonal orientation, collision detection).
Tier C: Supply verification (consumer satisfaction, liquid purity, leak detection).
"""

from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from .rules import get_block_physics, ROTATION_VECTORS
    from .sim import trace_supply, SupplyReport
except ImportError:
    try:
        from core.rules import get_block_physics, ROTATION_VECTORS
        from core.sim import trace_supply, SupplyReport
    except ImportError:
        from rules import get_block_physics, ROTATION_VECTORS
        from sim import trace_supply, SupplyReport


class ValidationResult:
    """Represents the outcome of a 3-tier schematic validation run."""

    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str]):
        self.is_valid = is_valid
        self.errors = list(errors)
        self.warnings = list(warnings)

    def __repr__(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        return f"<ValidationResult {status}: {len(self.errors)} errors, {len(self.warnings)} warnings>"


def validate_schematic(
    schematic: Dict[str, Any],
    inlets: Optional[List[Tuple[int, int, str]]] = None,
    strict: bool = False,
) -> ValidationResult:
    """
    Perform complete 3-tier static validation on a Mindustry schematic.
    
    Tier A: Structural validation:
      - No two blocks occupy the same cell. Multi-tile footprints reserve [x, x+size-1] x [y, y+size-1].
      - Coordinates normalized (min_x >= 0, min_y >= 0, starting at origin).
      - Dimensions match actual bounds.
      
    Tier B: Link validation:
      - Bridge conveyors and bridge conduits must link to identical block types.
      - Bridge range <= 4 Manhattan tiles and strictly orthogonal (dx=0 or dy=0).
      - No head-on conveyor or conduit collisions.
      
    Tier C: Supply validation:
      - Consumers must be fully supplied via trace_supply().
      - Liquid purity maintained (no cross-contamination).
      - No resource leaks.
    """
    errors: List[str] = []
    warnings: List[str] = []

    tiles = schematic.get("tiles", [])
    if not tiles:
        warnings.append("Schematic contains no tiles.")
        return ValidationResult(is_valid=True, errors=errors, warnings=warnings)

    # ==========================================================================
    # Tier A: Structural Validation
    # ==========================================================================
    occupied_cells: Dict[Tuple[int, int], Dict[str, Any]] = {}
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for idx, t in enumerate(tiles):
        b_name = t.get("block", "")
        phys = get_block_physics(b_name)
        tx = t.get("x")
        ty = t.get("y")

        if tx is None or ty is None:
            errors.append(f"Tile {idx} ('{b_name}') missing x or y coordinates.")
            continue

        tx = int(tx)
        ty = int(ty)
        size = phys.size

        # Check coordinate bounds
        min_x = min(min_x, tx)
        min_y = min(min_y, ty)
        max_x = max(max_x, tx + size)
        max_y = max(max_y, ty + size)

        # Check multi-cell footprint collisions
        for dx in range(size):
            for dy in range(size):
                cell = (tx + dx, ty + dy)
                if cell in occupied_cells:
                    other = occupied_cells[cell]
                    errors.append(
                        f"Block overlap at ({cell[0]}, {cell[1]}): "
                        f"'{b_name}' at ({tx}, {ty}) collides with '{other.get('block')}' at ({other.get('x')}, {other.get('y')})."
                    )
                else:
                    occupied_cells[cell] = t

    # Normalization check
    if min_x < 0 or min_y < 0:
        errors.append(f"Coordinates not normalized: min_x={min_x}, min_y={min_y} (must be >= 0).")
    elif min_x > 0 or min_y > 0:
        msg = f"Coordinates not anchored to origin (0, 0): offset is ({min_x}, {min_y})."
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)

    # Dimension bounds check
    actual_w = int(max_x - min_x) if max_x >= min_x else 0
    actual_h = int(max_y - min_y) if max_y >= min_y else 0
    declared_w = schematic.get("width")
    declared_h = schematic.get("height")

    if declared_w is not None and declared_w != actual_w:
        errors.append(f"Dimension mismatch: declared width is {declared_w}, actual is {actual_w}.")
    if declared_h is not None and declared_h != actual_h:
        errors.append(f"Dimension mismatch: declared height is {declared_h}, actual is {actual_h}.")

    # ==========================================================================
    # Tier B: Link & Topology Validation
    # ==========================================================================
    directional_transport = {
        "conveyor", "titanium-conveyor", "armored-conveyor", "plastanium-conveyor",
        "conduit", "pulse-conduit", "plated-conduit"
    }

    # 1. Head-on conveyor collisions
    for t in tiles:
        b_name = t.get("block", "")
        if b_name in directional_transport:
            tx, ty = int(t.get("x", 0)), int(t.get("y", 0))
            rot = int(t.get("rotation", 0)) % 4
            dx, dy = ROTATION_VECTORS[rot]
            front_cell = (tx + dx, ty + dy)

            target_tile = occupied_cells.get(front_cell)
            if target_tile and target_tile.get("block") in directional_transport:
                # Check target tile direction
                tgt_x, tgt_y = int(target_tile.get("x", 0)), int(target_tile.get("y", 0))
                tgt_rot = int(target_tile.get("rotation", 0)) % 4
                tgt_dx, tgt_dy = ROTATION_VECTORS[tgt_rot]
                tgt_front = (tgt_x + tgt_dx, tgt_y + tgt_dy)

                if tgt_front == (tx, ty):
                    # They point into each other! Head-on collision
                    collision_id = tuple(sorted([(tx, ty), (tgt_x, tgt_y)]))
                    err = f"Head-on conveyor collision between ({tx}, {ty}) and ({tgt_x}, {tgt_y})."
                    if err not in errors:
                        errors.append(err)

    # 2. Bridge conveyors & Bridge conduits
    for t in tiles:
        b_name = t.get("block", "")
        if b_name in ("bridge-conveyor", "bridge-conduit"):
            tx, ty = int(t.get("x", 0)), int(t.get("y", 0))
            config = t.get("config")

            dx, dy = 0, 0
            if isinstance(config, (list, tuple)):
                if len(config) == 3 and config[0] == "point2":
                    dx, dy = int(config[1]), int(config[2])
                elif len(config) == 2:
                    dx, dy = int(config[0]), int(config[1])

            # (-1, -1) indicates terminus receiver bridge
            if (dx, dy) == (-1, -1):
                continue

            if dx == 0 and dy == 0:
                warnings.append(f"Unlinked bridge at ({tx}, {ty}).")
                continue

            # Check orthogonality
            if dx != 0 and dy != 0:
                errors.append(
                    f"Diagonal bridge connection at ({tx}, {ty}): offset ({dx}, {dy}) is not orthogonal."
                )

            # Check range (Manhattan distance <= 4)
            manhattan_dist = abs(dx) + abs(dy)
            if manhattan_dist > 4:
                errors.append(
                    f"Bridge at ({tx}, {ty}) out of range: offset ({dx}, {dy}) distance {manhattan_dist} > 4."
                )

            # Check target block type
            target_pos = (tx + dx, ty + dy)
            target_tile = occupied_cells.get(target_pos)
            if not target_tile:
                errors.append(
                    f"Bridge at ({tx}, {ty}) points to empty cell at ({target_pos[0]}, {target_pos[1]})."
                )
            elif target_tile.get("block") != b_name:
                errors.append(
                    f"Bridge type mismatch at ({tx}, {ty}): '{b_name}' links to '{target_tile.get('block')}' at ({target_pos[0]}, {target_pos[1]})."
                )

    # ==========================================================================
    # Tier C: Supply & Purity Validation via Simulator
    # ==========================================================================
    report: SupplyReport = trace_supply(schematic, inlets=inlets)

    # Check missing demands
    missing = report.missing_demands(include_optional=strict)
    for m in missing:
        errors.append(
            f"Unsupplied consumer '{m['block']}' at ({m['x']}, {m['y']}): missing {', '.join(m['missing'])}."
        )

    # Check leaks
    leaks = report.leaks()
    for leak in leaks:
        errors.append(f"Supply leak: {leak}")

    is_valid = (len(errors) == 0)
    if strict and warnings:
        is_valid = False

    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
