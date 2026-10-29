"""
Mindustry v7 Physical Rules Table, Resource Graph & Transport Primitives.
Provides data-only specifications of block physics, ports, resource requirements,
and direction-aware output target resolution.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Mindustry rotation vectors: 0: East (+X), 1: North (+Y), 2: West (-X), 3: South (-Y)
ROTATION_VECTORS: Dict[int, Tuple[int, int]] = {
    0: (1, 0),
    1: (0, 1),
    2: (-1, 0),
    3: (0, -1),
}

# Reverse direction vectors: map (dx, dy) to rotation integer
VECTOR_TO_ROTATION: Dict[Tuple[int, int], int] = {
    (1, 0): 0,
    (0, 1): 1,
    (-1, 0): 2,
    (0, -1): 3,
}

# All vanilla Mindustry items
ALL_ITEMS: Set[str] = {
    "copper", "lead", "metaglass", "graphite", "sand", "coal",
    "titanium", "thorium", "scrap", "silicon", "plastanium",
    "phase-fabric", "surge-alloy", "spore-pod", "blast-compound", "pyratite"
}

# All vanilla Mindustry liquids
ALL_LIQUIDS: Set[str] = {
    "water", "slag", "oil", "cryofluid"
}


class BlockPhysics:
    """Detailed physical specification and resource input/output contract for a block."""

    def __init__(
        self,
        name: str,
        size: int,
        category: str,
        transport_type: Optional[str] = None,  # 'item', 'liquid', 'power', None
        solid_inputs: Optional[List[str]] = None,
        ammo_options: Optional[List[str]] = None,
        liquid_ammo_options: Optional[List[str]] = None,
        optional_items: Optional[List[str]] = None,
        liquid_inputs: Optional[List[str]] = None,
        optional_liquids: Optional[List[str]] = None,
        requires_power: bool = False,
        produces_items: Optional[List[str]] = None,
        produces_liquids: Optional[List[str]] = None,
        produces_power: bool = False,
        power_range: float = 0.0,
        bridge_range: int = 0,
        rotatable: bool = False,
    ):
        self.name = name
        self.size = size
        self.category = category
        self.transport_type = transport_type
        self.solid_inputs = set(solid_inputs or [])
        self.ammo_options = set(ammo_options or [])
        self.liquid_ammo_options = set(liquid_ammo_options or [])
        self.optional_items = set(optional_items or [])
        self.liquid_inputs = set(liquid_inputs or [])
        self.optional_liquids = set(optional_liquids or [])
        self.requires_power = requires_power
        self.produces_items = set(produces_items or [])
        self.produces_liquids = set(produces_liquids or [])
        self.produces_power = produces_power
        self.power_range = float(power_range)
        self.bridge_range = int(bridge_range)
        self.rotatable = rotatable

    @property
    def is_consumer(self) -> bool:
        return bool(
            self.solid_inputs
            or self.ammo_options
            or self.liquid_ammo_options
            or self.liquid_inputs
            or self.requires_power
        )


# Global block physics registry
RULES_TABLE: Dict[str, BlockPhysics] = {
    # --------------------------------------------------------------------------
    # Item Transport
    # --------------------------------------------------------------------------
    "conveyor": BlockPhysics(
        name="conveyor", size=1, category="distribution", transport_type="item",
        rotatable=True
    ),
    "titanium-conveyor": BlockPhysics(
        name="titanium-conveyor", size=1, category="distribution", transport_type="item",
        rotatable=True
    ),
    "armored-conveyor": BlockPhysics(
        name="armored-conveyor", size=1, category="distribution", transport_type="item",
        rotatable=True
    ),
    "plastanium-conveyor": BlockPhysics(
        name="plastanium-conveyor", size=1, category="distribution", transport_type="item",
        rotatable=True
    ),
    "junction": BlockPhysics(
        name="junction", size=1, category="distribution", transport_type="item",
        rotatable=False
    ),
    "router": BlockPhysics(
        name="router", size=1, category="distribution", transport_type="item",
        rotatable=False
    ),
    "distributor": BlockPhysics(
        name="distributor", size=2, category="distribution", transport_type="item",
        rotatable=False
    ),
    "overflow-gate": BlockPhysics(
        name="overflow-gate", size=1, category="distribution", transport_type="item",
        rotatable=False
    ),
    "underflow-gate": BlockPhysics(
        name="underflow-gate", size=1, category="distribution", transport_type="item",
        rotatable=False
    ),
    "sorter": BlockPhysics(
        name="sorter", size=1, category="distribution", transport_type="item",
        rotatable=True
    ),
    "inverted-sorter": BlockPhysics(
        name="inverted-sorter", size=1, category="distribution", transport_type="item",
        rotatable=True
    ),
    "bridge-conveyor": BlockPhysics(
        name="bridge-conveyor", size=1, category="distribution", transport_type="item",
        bridge_range=4, rotatable=True
    ),

    # --------------------------------------------------------------------------
    # Liquid Transport
    # --------------------------------------------------------------------------
    "conduit": BlockPhysics(
        name="conduit", size=1, category="liquid", transport_type="liquid",
        rotatable=True
    ),
    "pulse-conduit": BlockPhysics(
        name="pulse-conduit", size=1, category="liquid", transport_type="liquid",
        rotatable=True
    ),
    "plated-conduit": BlockPhysics(
        name="plated-conduit", size=1, category="liquid", transport_type="liquid",
        rotatable=True
    ),
    "liquid-router": BlockPhysics(
        name="liquid-router", size=1, category="liquid", transport_type="liquid",
        rotatable=False
    ),
    "liquid-junction": BlockPhysics(
        name="liquid-junction", size=1, category="liquid", transport_type="liquid",
        rotatable=False
    ),
    "bridge-conduit": BlockPhysics(
        name="bridge-conduit", size=1, category="liquid", transport_type="liquid",
        bridge_range=4, rotatable=True
    ),

    # --------------------------------------------------------------------------
    # Power
    # --------------------------------------------------------------------------
    "power-node": BlockPhysics(
        name="power-node", size=1, category="power", transport_type="power",
        power_range=6.0
    ),
    "power-node-large": BlockPhysics(
        name="power-node-large", size=2, category="power", transport_type="power",
        power_range=15.0
    ),
    "surge-tower": BlockPhysics(
        name="surge-tower", size=2, category="power", transport_type="power",
        power_range=30.0
    ),
    "battery": BlockPhysics(
        name="battery", size=1, category="power", transport_type="power"
    ),
    "battery-large": BlockPhysics(
        name="battery-large", size=3, category="power", transport_type="power"
    ),
    "solar-panel": BlockPhysics(
        name="solar-panel", size=1, category="power", transport_type="power",
        produces_power=True
    ),
    "solar-panel-large": BlockPhysics(
        name="solar-panel-large", size=3, category="power", transport_type="power",
        produces_power=True
    ),
    "combustion-generator": BlockPhysics(
        name="combustion-generator", size=2, category="power", transport_type="power",
        solid_inputs=["coal"], produces_power=True
    ),

    # --------------------------------------------------------------------------
    # Consumers: Turrets
    # --------------------------------------------------------------------------
    "duo": BlockPhysics(
        name="duo", size=1, category="turret",
        ammo_options=["copper", "lead", "graphite", "silicon"],
        optional_liquids=["water"],
        rotatable=True
    ),
    "salvo": BlockPhysics(
        name="salvo", size=2, category="turret",
        ammo_options=["copper", "lead", "graphite", "silicon", "thorium", "pyratite"],
        optional_liquids=["water", "cryofluid"],
        rotatable=True
    ),
    "scorch": BlockPhysics(
        name="scorch", size=1, category="turret",
        ammo_options=["coal", "pyratite"],
        optional_liquids=["water", "cryofluid"],
        rotatable=True
    ),
    "hail": BlockPhysics(
        name="hail", size=1, category="turret",
        ammo_options=["graphite", "silicon", "pyratite"],
        optional_liquids=["water", "cryofluid"],
        rotatable=True
    ),
    "lancer": BlockPhysics(
        name="lancer", size=2, category="turret",
        requires_power=True,
        optional_liquids=["water", "cryofluid"],
        rotatable=True
    ),
    "arc": BlockPhysics(
        name="arc", size=1, category="turret",
        requires_power=True,
        optional_liquids=["water", "cryofluid"],
        rotatable=True
    ),
    "wave": BlockPhysics(
        name="wave", size=2, category="turret",
        liquid_ammo_options=["water", "slag", "oil", "cryofluid"],
        rotatable=True
    ),

    # --------------------------------------------------------------------------
    # Consumers: Defense & Support
    # --------------------------------------------------------------------------
    "mender": BlockPhysics(
        name="mender", size=1, category="defense",
        requires_power=True, optional_items=["silicon"]
    ),
    "mend-projector": BlockPhysics(
        name="mend-projector", size=2, category="defense",
        requires_power=True, optional_items=["phase-fabric"]
    ),
    "overdrive-projector": BlockPhysics(
        name="overdrive-projector", size=2, category="defense",
        requires_power=True, optional_items=["phase-fabric"]
    ),
    "force-projector": BlockPhysics(
        name="force-projector", size=3, category="defense",
        requires_power=True, optional_liquids=["water", "cryofluid"]
    ),

    # --------------------------------------------------------------------------
    # Production & Crafting
    # --------------------------------------------------------------------------
    "silicon-smelter": BlockPhysics(
        name="silicon-smelter", size=2, category="production",
        solid_inputs=["sand", "coal"], requires_power=True,
        produces_items=["silicon"]
    ),
    "graphite-press": BlockPhysics(
        name="graphite-press", size=2, category="production",
        solid_inputs=["coal"],
        produces_items=["graphite"]
    ),
    "kiln": BlockPhysics(
        name="kiln", size=2, category="production",
        solid_inputs=["sand", "lead"], requires_power=True,
        produces_items=["metaglass"]
    ),
    "cryofluid-mixer": BlockPhysics(
        name="cryofluid-mixer", size=2, category="production",
        solid_inputs=["titanium"], liquid_inputs=["water"], requires_power=True,
        produces_liquids=["cryofluid"]
    ),
    "thorium-reactor": BlockPhysics(
        name="thorium-reactor", size=3, category="power", transport_type="power",
        solid_inputs=["thorium"], liquid_inputs=["cryofluid"], produces_power=True
    ),

    # --------------------------------------------------------------------------
    # Walls (Pure Barriers)
    # --------------------------------------------------------------------------
    "copper-wall": BlockPhysics("copper-wall", 1, "defense"),
    "copper-wall-large": BlockPhysics("copper-wall-large", 2, "defense"),
    "titanium-wall": BlockPhysics("titanium-wall", 1, "defense"),
    "titanium-wall-large": BlockPhysics("titanium-wall-large", 2, "defense"),
    "thorium-wall": BlockPhysics("thorium-wall", 1, "defense"),
    "thorium-wall-large": BlockPhysics("thorium-wall-large", 2, "defense"),
    "surge-wall": BlockPhysics("surge-wall", 1, "defense"),
    "surge-wall-large": BlockPhysics("surge-wall-large", 2, "defense"),
}


def get_block_physics(name: str) -> BlockPhysics:
    """Retrieve block physics definition, defaulting to inert 1x1 block if unrecognized."""
    cleaned = name.strip().lower().replace(" ", "-")
    if cleaned in RULES_TABLE:
        return RULES_TABLE[cleaned]
    return BlockPhysics(cleaned, 1, "unknown")


def can_accept(block_name: str, resource_type: str) -> bool:
    """
    Check if a block can accept a specified resource.
    resource_type can be:
    - 'item' (any solid item), or a specific item ('copper', 'coal', etc.)
    - 'liquid' (any liquid), or a specific liquid ('water', 'cryofluid', etc.)
    - 'power'
    """
    phys = get_block_physics(block_name)
    res = resource_type.strip().lower()

    if res == "power":
        return phys.requires_power or phys.transport_type == "power"

    # Solid item acceptance
    if res == "item" or res in ALL_ITEMS:
        # Item transport accepts all items
        if phys.transport_type == "item":
            return True
        # Turret ammos
        if phys.ammo_options:
            if res == "item" or res in phys.ammo_options:
                return True
        # Consumer solid inputs
        if phys.solid_inputs:
            if res == "item" or res in phys.solid_inputs:
                return True
        # Optional booster items
        if phys.optional_items:
            if res == "item" or res in phys.optional_items:
                return True
        return False

    # Liquid acceptance
    if res == "liquid" or res in ALL_LIQUIDS:
        # Liquid transport accepts all liquids
        if phys.transport_type == "liquid":
            return True
        # Turret liquid ammos
        if phys.liquid_ammo_options:
            if res == "liquid" or res in phys.liquid_ammo_options:
                return True
        # Consumer liquid inputs
        if phys.liquid_inputs:
            if res == "liquid" or res in phys.liquid_inputs:
                return True
        # Optional coolants
        if phys.optional_liquids:
            if res == "liquid" or res in phys.optional_liquids:
                return True
        return False

    return False


def _build_cell_map(grid_or_schematic: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[Tuple[int, int], Dict[str, Any]]:
    """Convert schematic or tile list into a fast cell -> tile dictionary."""
    if isinstance(grid_or_schematic, dict) and "tiles" in grid_or_schematic:
        tiles = grid_or_schematic["tiles"]
    elif isinstance(grid_or_schematic, list):
        tiles = grid_or_schematic
    elif isinstance(grid_or_schematic, dict):
        # Already a cell map
        return grid_or_schematic
    else:
        return {}

    cell_map: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for t in tiles:
        b_name = t.get("block", "")
        phys = get_block_physics(b_name)
        tx, ty = t.get("x", 0), t.get("y", 0)
        size = phys.size
        for dx in range(size):
            for dy in range(size):
                cell_map[(tx + dx, ty + dy)] = t
    return cell_map


def get_output_targets(
    tile: Dict[str, Any],
    came_from: Optional[Tuple[int, int]] = None,
    grid: Optional[Any] = None,
) -> List[Tuple[int, int]]:
    """
    Compute coordinates (tx, ty) where resources exiting 'tile' can travel.
    Takes into account conveyor rotation, router splitting, junction pass-through,
    underflow/overflow logic, and bridge conveyor targets.
    """
    b_name = tile.get("block", "")
    phys = get_block_physics(b_name)
    tx, ty = tile.get("x", 0), tile.get("y", 0)
    rot = tile.get("rotation", 0) % 4
    config = tile.get("config")

    cell_map = _build_cell_map(grid) if grid is not None else {}

    # 1. Unidirectional Transport (conveyors, conduits)
    if b_name in (
        "conveyor", "titanium-conveyor", "armored-conveyor", "plastanium-conveyor",
        "conduit", "pulse-conduit", "plated-conduit"
    ):
        dx, dy = ROTATION_VECTORS[rot]
        return [(tx + dx, ty + dy)]

    # 2. Junctions: pass straight through from came_from direction
    if b_name in ("junction", "liquid-junction"):
        if came_from is None:
            # If inlet directly on junction, can exit all 4 sides
            return [(tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)]
        fx, fy = came_from
        dx = tx - fx
        dy = ty - fy
        return [(tx + dx, ty + dy)]

    # 3. Routers & Liquid Routers: distribute to orthogonal neighbors except came_from
    if b_name in ("router", "liquid-router"):
        neighbors = [(tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)]
        if came_from is not None:
            came_from_tile = cell_map.get(came_from) if cell_map else None
            if came_from_tile is not None:
                neighbors = [n for n in neighbors if cell_map.get(n) is not came_from_tile]
            else:
                neighbors = [n for n in neighbors if n != came_from]
        if cell_map:
            res_kind = "liquid" if b_name == "liquid-router" else "item"
            valid_neighbors = []
            for n in neighbors:
                if n in cell_map:
                    n_tile = cell_map[n]
                    if not can_accept(n_tile.get("block", ""), res_kind):
                        continue
                    # If neighbor is a conveyor/conduit pointing into this router, it cannot accept reverse flow
                    n_phys = get_block_physics(n_tile.get("block", ""))
                    if n_phys.rotatable and n_phys.transport_type in ("item", "liquid"):
                        n_rot = int(n_tile.get("rotation", 0)) % 4
                        n_dx, n_dy = ROTATION_VECTORS[n_rot]
                        if (n[0] + n_dx, n[1] + n_dy) == (tx, ty):
                            continue
                valid_neighbors.append(n)
            neighbors = valid_neighbors
        return neighbors

    # 4. Distributors (2x2 Router)
    if b_name == "distributor":
        perimeter = [
            (tx - 1, ty), (tx - 1, ty + 1),
            (tx + 2, ty), (tx + 2, ty + 1),
            (tx, ty - 1), (tx + 1, ty - 1),
            (tx, ty + 2), (tx + 1, ty + 2),
        ]
        if came_from is not None:
            came_from_tile = cell_map.get(came_from) if cell_map else None
            if came_from_tile is not None:
                perimeter = [p for p in perimeter if cell_map.get(p) is not came_from_tile]
            else:
                perimeter = [p for p in perimeter if p != came_from]
        if cell_map:
            perimeter = [p for p in perimeter if p not in cell_map or can_accept(cell_map[p].get("block", ""), "item")]
        return perimeter

    # 5. Overflow Gate: straight ahead first; if blocked or off-grid, sideways
    if b_name == "overflow-gate":
        if came_from is None:
            return [(tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)]
        fx, fy = came_from
        fwd_dx, fwd_dy = tx - fx, ty - fy
        straight = (tx + fwd_dx, ty + fwd_dy)
        side1 = (tx - fwd_dy, ty + fwd_dx)
        side2 = (tx + fwd_dy, ty - fwd_dx)

        straight_tile = cell_map.get(straight)
        if straight_tile and can_accept(straight_tile.get("block", ""), "item"):
            return [straight]
        return [side1, side2]

    # 6. Underflow Gate: sideways first; if both blocked, straight ahead
    if b_name == "underflow-gate":
        if came_from is None:
            return [(tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)]
        fx, fy = came_from
        fwd_dx, fwd_dy = tx - fx, ty - fy
        straight = (tx + fwd_dx, ty + fwd_dy)
        side1 = (tx - fwd_dy, ty + fwd_dx)
        side2 = (tx + fwd_dy, ty - fwd_dx)

        side1_tile = cell_map.get(side1)
        side2_tile = cell_map.get(side2)
        side1_acc = side1_tile and can_accept(side1_tile.get("block", ""), "item")
        side2_acc = side2_tile and can_accept(side2_tile.get("block", ""), "item")

        if side1_acc or side2_acc:
            res = []
            if side1_acc:
                res.append(side1)
            if side2_acc:
                res.append(side2)
            return res
        return [straight]

    # 7. Bridge Conveyor / Bridge Conduit
    if b_name in ("bridge-conveyor", "bridge-conduit"):
        dx, dy = 0, 0
        if isinstance(config, (list, tuple)):
            if len(config) == 3 and config[0] == "point2":
                dx, dy = int(config[1]), int(config[2])
            elif len(config) == 2:
                dx, dy = int(config[0]), int(config[1])
        
        if (dx, dy) == (-1, -1) or (dx == 0 and dy == 0):
            # Terminus / receiver bridge outputs to orthogonal neighbors
            neighbors = [(tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)]
            if came_from is not None:
                neighbors = [n for n in neighbors if n != came_from]
            if cell_map:
                res_kind = "liquid" if b_name == "bridge-conduit" else "item"
                neighbors = [n for n in neighbors if n not in cell_map or can_accept(cell_map[n].get("block", ""), res_kind)]
            return neighbors
        else:
            # Transmitter bridge links directly to target receiver
            return [(tx + dx, ty + dy)]

    # 8. Sorters: straight or sideways
    if b_name in ("sorter", "inverted-sorter"):
        dx, dy = ROTATION_VECTORS[rot]
        return [(tx + dx, ty + dy)]

    # Default fallback: for multi-tile factories producing items/liquids,
    # outputs can leave perimeter cells that do not point into the factory.
    if phys.produces_items or phys.produces_liquids:
        factory_cells = {(tx + dx, ty + dy) for dx in range(phys.size) for dy in range(phys.size)}
        candidates = []
        for ox in range(phys.size):
            candidates.append((tx + ox, ty - 1))
            candidates.append((tx + ox, ty + phys.size))
        for oy in range(phys.size):
            candidates.append((tx - 1, ty + oy))
            candidates.append((tx + phys.size, ty + oy))

        if came_from is not None:
            came_from_tile = cell_map.get(came_from) if cell_map else None
            if came_from_tile is not None:
                candidates = [p for p in candidates if cell_map.get(p) is not came_from_tile]
            else:
                candidates = [p for p in candidates if p != came_from]

        perimeter = []
        for cx, cy in candidates:
            if cell_map:
                neighbor_tile = cell_map.get((cx, cy))
                if neighbor_tile:
                    n_bname = neighbor_tile.get("block", "")
                    n_phys = get_block_physics(n_bname)
                    if n_phys.rotatable and n_phys.transport_type in ("item", "liquid"):
                        n_rot = neighbor_tile.get("rotation", 0) % 4
                        n_dx, n_dy = ROTATION_VECTORS[n_rot]
                        if (cx + n_dx, cy + n_dy) in factory_cells:
                            # Neighbor conveyor points directly into factory; cannot emit against flow!
                            continue
                    # Production blocks output to conveyors or downstream consumers, not into distribution routers
                    if n_bname in ("router", "junction", "distributor", "liquid-router", "liquid-junction"):
                        continue
            perimeter.append((cx, cy))
        return perimeter

    return []
