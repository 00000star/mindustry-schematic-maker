"""
Mindustry v7 Supply Simulator & Flow Tracer.
Performs BFS/Flood-fill tracing for solid items, liquids, and power grids.
Detects missing demands, network leaks, and liquid contamination.
"""

import math
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from .rules import (
        ALL_ITEMS, ALL_LIQUIDS, BlockPhysics, can_accept,
        get_block_physics, get_output_targets
    )
except ImportError:
    try:
        from core.rules import (
            ALL_ITEMS, ALL_LIQUIDS, BlockPhysics, can_accept,
            get_block_physics, get_output_targets
        )
    except ImportError:
        from rules import (
            ALL_ITEMS, ALL_LIQUIDS, BlockPhysics, can_accept,
            get_block_physics, get_output_targets
        )


class SupplyReport:
    """Detailed summary of resource delivery, missing demands, and leaks across a schematic."""

    def __init__(self, schematic: Dict[str, Any]):
        self.schematic = schematic
        # Map: (origin_x, origin_y) -> set of supplied resource names
        self.supplied_resources: Dict[Tuple[int, int], Set[str]] = {}
        self._leaks: List[str] = []
        self._cell_liquids: Dict[Tuple[int, int], str] = {}
        self._expected_coolant: bool = False

    def add_leak(self, msg: str) -> None:
        if msg not in self._leaks:
            self._leaks.append(msg)

    def leaks(self) -> List[str]:
        """Returns list of leak descriptions: items into non-items, liquids into non-liquids, etc."""
        return list(self._leaks)

    def missing_demands(self, include_optional: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Returns list of consumers with missing ammo, coolant, or power.
        Each entry: {
            "x": int,
            "y": int,
            "block": str,
            "missing": List[str],  # e.g. ["ammo"], ["water", "titanium"], ["power"]
            "type": str            # "ammo", "resource", "coolant", "power"
        }
        """
        if include_optional is None:
            # If coolant was explicitly introduced or conduits exist, check coolant
            check_coolant = self._expected_coolant
        else:
            check_coolant = include_optional

        missing_list: List[Dict[str, Any]] = []

        for tile in self.schematic.get("tiles", []):
            b_name = tile.get("block", "")
            phys = get_block_physics(b_name)
            ox, oy = tile.get("x", 0), tile.get("y", 0)
            supplied = self.supplied_resources.get((ox, oy), set())

            # 1. Ammo Demands (for turrets)
            if phys.ammo_options or phys.liquid_ammo_options:
                has_solid_ammo = bool(supplied.intersection(phys.ammo_options) or "item" in supplied or "ammo" in supplied)
                has_liquid_ammo = bool(supplied.intersection(phys.liquid_ammo_options) or "liquid" in supplied)
                if not (has_solid_ammo or has_liquid_ammo):
                    missing_list.append({
                        "x": ox,
                        "y": oy,
                        "block": b_name,
                        "missing": ["ammo"],
                        "type": "ammo"
                    })

            # 2. Solid Input Demands (for production / reactors)
            if phys.solid_inputs:
                missing_solids = [
                    item for item in sorted(phys.solid_inputs)
                    if item not in supplied and "item" not in supplied
                ]
                if missing_solids:
                    missing_list.append({
                        "x": ox,
                        "y": oy,
                        "block": b_name,
                        "missing": missing_solids,
                        "type": "resource"
                    })

            # 3. Liquid Input Demands (for mixers, reactors)
            if phys.liquid_inputs:
                missing_liquids = [
                    liq for liq in sorted(phys.liquid_inputs)
                    if liq not in supplied and "liquid" not in supplied
                ]
                if missing_liquids:
                    missing_list.append({
                        "x": ox,
                        "y": oy,
                        "block": b_name,
                        "missing": missing_liquids,
                        "type": "resource"
                    })

            # 4. Optional Coolant (for turrets)
            if check_coolant and phys.optional_liquids:
                has_coolant = bool(supplied.intersection(phys.optional_liquids) or "liquid" in supplied)
                if not has_coolant:
                    missing_list.append({
                        "x": ox,
                        "y": oy,
                        "block": b_name,
                        "missing": sorted(list(phys.optional_liquids)),
                        "type": "coolant"
                    })

            # 5. Power Demands
            if phys.requires_power:
                if "power" not in supplied:
                    missing_list.append({
                        "x": ox,
                        "y": oy,
                        "block": b_name,
                        "missing": ["power"],
                        "type": "power"
                    })

        return missing_list

    def is_fully_supplied(self) -> bool:
        """True if every consumer has all required resources and zero leaks."""
        demands = self.missing_demands()
        return len(demands) == 0 and len(self._leaks) == 0


def _autodetect_inlets(schematic: Dict[str, Any]) -> List[Tuple[int, int, str]]:
    """
    Autodetect inlet candidates: blocks on the perimeter with no incoming
    connections from inside the schematic.
    """
    tiles = schematic.get("tiles", [])
    if not tiles:
        return []

    # Map each cell (cx, cy) to its tile
    cell_to_tile: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for t in tiles:
        phys = get_block_physics(t.get("block", ""))
        tx, ty = t.get("x", 0), t.get("y", 0)
        for dx in range(phys.size):
            for dy in range(phys.size):
                cell_to_tile[(tx + dx, ty + dy)] = t

    # Bounding box
    min_x = min(t.get("x", 0) for t in tiles)
    min_y = min(t.get("y", 0) for t in tiles)
    max_x = max(t.get("x", 0) + get_block_physics(t.get("block", "")).size for t in tiles)
    max_y = max(t.get("y", 0) + get_block_physics(t.get("block", "")).size for t in tiles)

    # Calculate internal incoming targets
    internal_incoming_targets: Set[Tuple[int, int]] = set()
    for t in tiles:
        b_name = t.get("block", "")
        phys = get_block_physics(b_name)
        # Directed transport (conveyors, conduits), bridges, and producers create internal feeds
        if phys.rotatable or "bridge" in b_name or phys.produces_items or phys.produces_liquids:
            targets = get_output_targets(t, came_from=None, grid=cell_to_tile)
            for tgt in targets:
                if tgt in cell_to_tile:
                    internal_incoming_targets.add(tgt)

    # Discover what resources consumers in this schematic need
    needed_items: Set[str] = set()
    needed_liquids: Set[str] = set()
    has_power_consumers = False
    has_power_generators = False

    for t in tiles:
        phys = get_block_physics(t.get("block", ""))
        needed_items.update(phys.solid_inputs)
        if phys.ammo_options:
            if "copper" in phys.ammo_options:
                needed_items.add("copper")
            elif "graphite" in phys.ammo_options:
                needed_items.add("graphite")
            elif "coal" in phys.ammo_options:
                needed_items.add("coal")
            else:
                needed_items.add(sorted(list(phys.ammo_options))[0])
        needed_liquids.update(phys.liquid_inputs)
        if phys.optional_liquids:
            needed_liquids.add("water")
        if phys.requires_power:
            has_power_consumers = True
        if phys.produces_power:
            has_power_generators = True

    inlets: List[Tuple[int, int, str]] = []

    for t in tiles:
        b_name = t.get("block", "")
        phys = get_block_physics(b_name)
        tx, ty = t.get("x", 0), t.get("y", 0)
        
        # Check if any cell of this tile is on the perimeter
        is_perimeter = False
        for dx in range(phys.size):
            for dy in range(phys.size):
                cx, cy = tx + dx, ty + dy
                if cx == min_x or cx == max_x - 1 or cy == min_y or cy == max_y - 1:
                    is_perimeter = True
                    break
            if is_perimeter:
                break

        if not is_perimeter:
            continue

        # Check if this tile receives inputs from inside the schematic
        has_internal_incoming = False
        for dx in range(phys.size):
            for dy in range(phys.size):
                if (tx + dx, ty + dy) in internal_incoming_targets:
                    has_internal_incoming = True
                    break
            if has_internal_incoming:
                break

        if has_internal_incoming:
            continue

        # Inlet candidate found!
        if phys.transport_type == "item":
            if needed_items:
                for item in sorted(needed_items):
                    inlets.append((tx, ty, item))
            else:
                inlets.append((tx, ty, "copper"))

        elif phys.transport_type == "liquid":
            if needed_liquids:
                for liq in sorted(needed_liquids):
                    inlets.append((tx, ty, liq))
            else:
                inlets.append((tx, ty, "water"))

        elif phys.transport_type == "power" and has_power_consumers and not has_power_generators:
            inlets.append((tx, ty, "power"))

    return inlets


def trace_supply(
    schematic: Dict[str, Any],
    inlets: Optional[List[Tuple[int, int, str]]] = None,
) -> SupplyReport:
    """
    Trace resource flows through a Mindustry schematic using BFS flood-fill.
    Verifies solid items, liquids (with single-liquid purity checking),
    and power network connectivity.
    """
    report = SupplyReport(schematic)
    tiles = schematic.get("tiles", [])
    if not tiles:
        return report

    # 1. Build grid lookup maps
    cell_to_tile: Dict[Tuple[int, int], Dict[str, Any]] = {}
    origin_to_tile: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for t in tiles:
        b_name = t.get("block", "")
        phys = get_block_physics(b_name)
        ox, oy = t.get("x", 0), t.get("y", 0)
        origin_to_tile[(ox, oy)] = t
        report.supplied_resources[(ox, oy)] = set()
        for dx in range(phys.size):
            for dy in range(phys.size):
                cell_to_tile[(ox + dx, oy + dy)] = t

    # 2. Determine inlets
    active_inlets: List[Tuple[int, int, str]] = []
    if inlets is not None:
        active_inlets = list(inlets)
    elif schematic.get("inlets"):
        active_inlets = [
            (int(i[0]), int(i[1]), str(i[2]))
            for i in schematic["inlets"]
        ]
    else:
        active_inlets = _autodetect_inlets(schematic)

    # Track if coolant was provided
    for _, _, res in active_inlets:
        if res in ALL_LIQUIDS or res == "liquid":
            report._expected_coolant = True

    # 3. Simulate power distribution
    # Find all power generators or power inlets
    powered_origins: Set[Tuple[int, int]] = set()

    for ix, iy, res in active_inlets:
        if res == "power":
            tile = cell_to_tile.get((ix, iy))
            if tile:
                powered_origins.add((tile.get("x", 0), tile.get("y", 0)))

    for t in tiles:
        phys = get_block_physics(t.get("block", ""))
        ox, oy = t.get("x", 0), t.get("y", 0)
        if phys.produces_power:
            powered_origins.add((ox, oy))

    # BFS expand power node network
    power_queue = deque(list(powered_origins))
    connected_power_blocks: Set[Tuple[int, int]] = set(powered_origins)

    while power_queue:
        curr_ox, curr_oy = power_queue.popleft()
        curr_tile = origin_to_tile.get((curr_ox, curr_oy))
        if not curr_tile:
            continue
        curr_phys = get_block_physics(curr_tile.get("block", ""))
        curr_size = curr_phys.size
        curr_center_x = curr_ox + (curr_size / 2.0)
        curr_center_y = curr_oy + (curr_size / 2.0)
        p_range = curr_phys.power_range

        # Connect to other buildings
        for other_origin, other_tile in origin_to_tile.items():
            if other_origin in connected_power_blocks:
                continue
            other_phys = get_block_physics(other_tile.get("block", ""))
            other_size = other_phys.size
            other_center_x = other_origin[0] + (other_size / 2.0)
            other_center_y = other_origin[1] + (other_size / 2.0)

            # Check adjacency (sharing any perimeter cell)
            is_adjacent = False
            for dx in range(curr_size):
                for dy in range(curr_size):
                    cx, cy = curr_ox + dx, curr_oy + dy
                    for odx in range(other_size):
                        for ody in range(other_size):
                            ocx, ocy = other_origin[0] + odx, other_origin[1] + ody
                            if abs(cx - ocx) + abs(cy - ocy) == 1:
                                is_adjacent = True
                                break
                        if is_adjacent:
                            break
                    if is_adjacent:
                        break
                if is_adjacent:
                    break

            # Check node range
            in_range = False
            if p_range > 0:
                dist = math.hypot(curr_center_x - other_center_x, curr_center_y - other_center_y)
                if dist <= p_range:
                    in_range = True

            if is_adjacent or in_range:
                connected_power_blocks.add(other_origin)
                # If the newly connected building can forward power, add to queue
                if other_phys.transport_type == "power" or other_phys.power_range > 0:
                    power_queue.append(other_origin)

    for p_origin in connected_power_blocks:
        report.supplied_resources[p_origin].add("power")

    # 4. Multi-round simulation for solid items and liquids (to handle producers)
    max_passes = 4
    for _ in range(max_passes):
        # Gather all current injection sources (inlets + active producers)
        current_injections: List[Tuple[int, int, Optional[Tuple[int, int]], str]] = []

        # From inlets
        for ix, iy, res in active_inlets:
            if res != "power":
                current_injections.append((ix, iy, None, res))

        # From producers whose input requirements are currently satisfied
        for t in tiles:
            ox, oy = t.get("x", 0), t.get("y", 0)
            phys = get_block_physics(t.get("block", ""))
            supplied = report.supplied_resources.get((ox, oy), set())

            # Check if producer has all inputs
            can_produce = True
            if phys.requires_power and "power" not in supplied:
                can_produce = False
            if phys.solid_inputs and not phys.solid_inputs.issubset(supplied) and "item" not in supplied:
                can_produce = False
            if phys.liquid_inputs and not phys.liquid_inputs.issubset(supplied) and "liquid" not in supplied:
                can_produce = False

            if can_produce:
                for prod_item in phys.produces_items:
                    for px, py in get_output_targets(t, came_from=None, grid=cell_to_tile):
                        target_t = cell_to_tile.get((px, py))
                        if target_t:
                            if not can_accept(target_t.get("block", ""), prod_item):
                                continue
                            tgt_origin = (target_t.get("x", 0), target_t.get("y", 0))
                            tgt_supplied = report.supplied_resources.get(tgt_origin, set())
                            if phys.solid_inputs.intersection(tgt_supplied):
                                continue
                        current_injections.append((px, py, (ox, oy), prod_item))
                for prod_liq in phys.produces_liquids:
                    for px, py in get_output_targets(t, came_from=None, grid=cell_to_tile):
                        target_t = cell_to_tile.get((px, py))
                        if target_t:
                            if not can_accept(target_t.get("block", ""), prod_liq):
                                continue
                            tgt_origin = (target_t.get("x", 0), target_t.get("y", 0))
                            tgt_supplied = report.supplied_resources.get(tgt_origin, set())
                            if phys.liquid_inputs.intersection(tgt_supplied):
                                continue
                        current_injections.append((px, py, (ox, oy), prod_liq))

        # BFS Queue: (curr_x, curr_y, came_from, resource_name)
        queue = deque(current_injections)
        visited: Set[Tuple[int, int, Optional[Tuple[int, int]], str]] = set()
        edge_cache: Dict[Tuple[int, int, Optional[Tuple[int, int]]], List[Tuple[int, int]]] = {}

        while queue:
            cx, cy, came_from, res = queue.popleft()
            state = (cx, cy, came_from, res)
            if state in visited:
                continue
            visited.add(state)

            tile = cell_to_tile.get((cx, cy))
            if tile is None:
                # Off grid / empty cell
                continue

            ox, oy = tile.get("x", 0), tile.get("y", 0)
            b_name = tile.get("block", "")
            phys = get_block_physics(b_name)

            # Check acceptance
            if not can_accept(b_name, res):
                report.add_leak(
                    f"Resource '{res}' cannot enter '{b_name}' at ({cx}, {cy})"
                )
                continue

            # Liquid purity check
            if res in ALL_LIQUIDS or res == "liquid":
                existing_liquid = report._cell_liquids.get((cx, cy))
                if existing_liquid and existing_liquid != res and res != "liquid" and existing_liquid != "liquid":
                    report.add_leak(
                        f"Liquid contamination: '{res}' mixed with '{existing_liquid}' at ({cx}, {cy})"
                    )
                    continue
                report._cell_liquids[(cx, cy)] = res

            # Mark supplied
            report.supplied_resources[(ox, oy)].add(res)

            # If transport, forward to output targets
            is_item_transport = (phys.transport_type == "item" and (res in ALL_ITEMS or res == "item"))
            is_liquid_transport = (phys.transport_type == "liquid" and (res in ALL_LIQUIDS or res == "liquid"))

            if is_item_transport or is_liquid_transport:
                edge_key = (ox, oy, came_from)
                if edge_key in edge_cache:
                    targets = edge_cache[edge_key]
                else:
                    targets = get_output_targets(tile, came_from=came_from, grid=cell_to_tile)
                    edge_cache[edge_key] = targets
                for tx, ty in targets:
                    queue.append((tx, ty, (cx, cy), res))

    return report
