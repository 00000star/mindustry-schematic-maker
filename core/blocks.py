"""
Mindustry v7 Block Catalog and Item/Liquid Mappings.
Provides dimensions, categories, rotatability, and ID lookup helpers.
"""

from typing import Dict, Optional, NamedTuple


class BlockInfo(NamedTuple):
    name: str
    size: int
    category: str
    rotatable: bool
    char: str


# Item mapping: Mindustry v7 standard IDs
ITEMS: Dict[str, int] = {
    "copper": 0,
    "lead": 1,
    "metaglass": 2,
    "graphite": 3,
    "sand": 4,
    "coal": 5,
    "titanium": 6,
    "thorium": 7,
    "scrap": 8,
    "silicon": 9,
    "plastanium": 10,
    "phase-fabric": 11,
    "surge-alloy": 12,
    "spore-pod": 13,
    "blast-compound": 14,
    "pyratite": 15,
}

ITEM_NAMES: Dict[int, str] = {v: k for k, v in ITEMS.items()}

# Liquid mapping: Mindustry v7 standard IDs
LIQUIDS: Dict[str, int] = {
    "water": 0,
    "slag": 1,
    "oil": 2,
    "cryofluid": 3,
}

LIQUID_NAMES: Dict[int, str] = {v: k for k, v in LIQUIDS.items()}

# Direction arrows for rotatable distribution blocks
# 0: East (>), 1: North (^), 2: West (<), 3: South (v)
ROTATION_ARROWS = {0: ">", 1: "^", 2: "<", 3: "v"}


# Full catalog of Mindustry v7 vanilla blocks
BLOCKS: Dict[str, BlockInfo] = {
    # Distribution
    "conveyor": BlockInfo("conveyor", 1, "distribution", True, ">"),
    "titanium-conveyor": BlockInfo("titanium-conveyor", 1, "distribution", True, ">"),
    "armored-conveyor": BlockInfo("armored-conveyor", 1, "distribution", True, ">"),
    "plastanium-conveyor": BlockInfo("plastanium-conveyor", 1, "distribution", True, ">"),
    "junction": BlockInfo("junction", 1, "distribution", False, "+"),
    "bridge-conveyor": BlockInfo("bridge-conveyor", 1, "distribution", True, "="),
    "router": BlockInfo("router", 1, "distribution", False, "R"),
    "distributor": BlockInfo("distributor", 2, "distribution", False, "D"),
    "sorter": BlockInfo("sorter", 1, "distribution", True, "S"),
    "inverted-sorter": BlockInfo("inverted-sorter", 1, "distribution", True, "I"),
    "overflow-gate": BlockInfo("overflow-gate", 1, "distribution", False, "O"),
    "underflow-gate": BlockInfo("underflow-gate", 1, "distribution", False, "U"),
    "mass-driver": BlockInfo("mass-driver", 3, "distribution", True, "M"),
    "item-source": BlockInfo("item-source", 1, "distribution", False, "*"),
    "item-void": BlockInfo("item-void", 1, "distribution", False, "X"),
    "unloader": BlockInfo("unloader", 1, "distribution", True, "u"),

    # Liquids
    "conduit": BlockInfo("conduit", 1, "liquid", True, "c"),
    "pulse-conduit": BlockInfo("pulse-conduit", 1, "liquid", True, "c"),
    "plated-conduit": BlockInfo("plated-conduit", 1, "liquid", True, "c"),
    "liquid-router": BlockInfo("liquid-router", 1, "liquid", False, "r"),
    "liquid-container": BlockInfo("liquid-container", 2, "liquid", False, "T"),
    "liquid-tank": BlockInfo("liquid-tank", 3, "liquid", False, "T"),
    "liquid-junction": BlockInfo("liquid-junction", 1, "liquid", False, "+"),
    "bridge-conduit": BlockInfo("bridge-conduit", 1, "liquid", True, "="),
    "liquid-source": BlockInfo("liquid-source", 1, "liquid", False, "*"),
    "liquid-void": BlockInfo("liquid-void", 1, "liquid", False, "X"),

    # Power
    "combustion-generator": BlockInfo("combustion-generator", 2, "power", False, "G"),
    "thermal-generator": BlockInfo("thermal-generator", 2, "power", False, "G"),
    "steam-generator": BlockInfo("steam-generator", 2, "power", False, "G"),
    "differential-generator": BlockInfo("differential-generator", 3, "power", False, "G"),
    "rtg-generator": BlockInfo("rtg-generator", 2, "power", False, "G"),
    "solar-panel": BlockInfo("solar-panel", 1, "power", False, "s"),
    "solar-panel-large": BlockInfo("solar-panel-large", 3, "power", False, "S"),
    "thorium-reactor": BlockInfo("thorium-reactor", 3, "power", False, "N"),
    "impact-reactor": BlockInfo("impact-reactor", 4, "power", False, "I"),
    "battery": BlockInfo("battery", 1, "power", False, "b"),
    "battery-large": BlockInfo("battery-large", 3, "power", False, "B"),
    "power-node": BlockInfo("power-node", 1, "power", False, "p"),
    "power-node-large": BlockInfo("power-node-large", 2, "power", False, "P"),
    "surge-tower": BlockInfo("surge-tower", 2, "power", False, "T"),
    "diode": BlockInfo("diode", 1, "power", True, "d"),

    # Production & Crafting
    "graphite-press": BlockInfo("graphite-press", 2, "production", False, "g"),
    "multi-press": BlockInfo("multi-press", 3, "production", False, "G"),
    "silicon-smelter": BlockInfo("silicon-smelter", 2, "production", False, "m"),
    "silicon-crucible": BlockInfo("silicon-crucible", 3, "production", False, "M"),
    "kiln": BlockInfo("kiln", 2, "production", False, "k"),
    "plastanium-compressor": BlockInfo("plastanium-compressor", 2, "production", False, "C"),
    "phase-weaver": BlockInfo("phase-weaver", 2, "production", False, "W"),
    "surge-smelter": BlockInfo("surge-smelter", 3, "production", False, "A"),
    "cryofluid-mixer": BlockInfo("cryofluid-mixer", 2, "production", False, "c"),
    "pyratite-mixer": BlockInfo("pyratite-mixer", 2, "production", False, "y"),
    "blast-mixer": BlockInfo("blast-mixer", 2, "production", False, "B"),
    "melter": BlockInfo("melter", 1, "production", False, "l"),
    "separator": BlockInfo("separator", 2, "production", False, "e"),
    "disassembler": BlockInfo("disassembler", 3, "production", False, "E"),
    "spore-press": BlockInfo("spore-press", 2, "production", False, "P"),
    "pulverizer": BlockInfo("pulverizer", 1, "production", False, "z"),
    "coal-centrifuge": BlockInfo("coal-centrifuge", 2, "production", False, "f"),
    "incinerator": BlockInfo("incinerator", 1, "production", False, "x"),

    # Defense & Walls
    "copper-wall": BlockInfo("copper-wall", 1, "defense", False, "#"),
    "copper-wall-large": BlockInfo("copper-wall-large", 2, "defense", False, "#"),
    "titanium-wall": BlockInfo("titanium-wall", 1, "defense", False, "#"),
    "titanium-wall-large": BlockInfo("titanium-wall-large", 2, "defense", False, "#"),
    "plastanium-wall": BlockInfo("plastanium-wall", 1, "defense", False, "#"),
    "plastanium-wall-large": BlockInfo("plastanium-wall-large", 2, "defense", False, "#"),
    "thorium-wall": BlockInfo("thorium-wall", 1, "defense", False, "#"),
    "thorium-wall-large": BlockInfo("thorium-wall-large", 2, "defense", False, "#"),
    "phase-wall": BlockInfo("phase-wall", 1, "defense", False, "#"),
    "phase-wall-large": BlockInfo("phase-wall-large", 2, "defense", False, "#"),
    "surge-wall": BlockInfo("surge-wall", 1, "defense", False, "#"),
    "surge-wall-large": BlockInfo("surge-wall-large", 2, "defense", False, "#"),
    "door": BlockInfo("door", 1, "defense", False, "D"),
    "door-large": BlockInfo("door-large", 2, "defense", False, "D"),
    "mender": BlockInfo("mender", 1, "defense", False, "+"),
    "mend-projector": BlockInfo("mend-projector", 2, "defense", False, "+"),
    "force-projector": BlockInfo("force-projector", 3, "defense", False, "F"),
    "overdrive-projector": BlockInfo("overdrive-projector", 2, "defense", False, "O"),
    "overdrive-dome": BlockInfo("overdrive-dome", 3, "defense", False, "O"),
    "radar": BlockInfo("radar", 1, "defense", False, "o"),

    # Turrets
    "duo": BlockInfo("duo", 1, "turret", False, "t"),
    "scatter": BlockInfo("scatter", 2, "turret", False, "T"),
    "scorch": BlockInfo("scorch", 1, "turret", False, "t"),
    "hail": BlockInfo("hail", 1, "turret", False, "t"),
    "wave": BlockInfo("wave", 2, "turret", False, "T"),
    "lancer": BlockInfo("lancer", 2, "turret", False, "L"),
    "arc": BlockInfo("arc", 1, "turret", False, "a"),
    "parallax": BlockInfo("parallax", 2, "turret", False, "T"),
    "swarmer": BlockInfo("swarmer", 2, "turret", False, "S"),
    "salvo": BlockInfo("salvo", 2, "turret", False, "S"),
    "fuse": BlockInfo("fuse", 3, "turret", False, "F"),
    "ripple": BlockInfo("ripple", 3, "turret", False, "R"),
    "cyclone": BlockInfo("cyclone", 3, "turret", False, "C"),
    "foreshadow": BlockInfo("foreshadow", 4, "turret", False, "X"),
    "spectre": BlockInfo("spectre", 4, "turret", False, "X"),
    "meltdown": BlockInfo("meltdown", 4, "turret", False, "X"),
    "segment": BlockInfo("segment", 2, "turret", False, "T"),
    "tsunami": BlockInfo("tsunami", 2, "turret", False, "T"),

    # Logic
    "message": BlockInfo("message", 1, "logic", False, "?"),
    "switch": BlockInfo("switch", 1, "logic", False, "!"),
    "micro-processor": BlockInfo("micro-processor", 1, "logic", False, "l"),
    "logic-processor": BlockInfo("logic-processor", 2, "logic", False, "L"),
    "hyper-processor": BlockInfo("hyper-processor", 3, "logic", False, "H"),
    "memory-cell": BlockInfo("memory-cell", 1, "logic", False, "c"),
    "memory-bank": BlockInfo("memory-bank", 2, "logic", False, "M"),
    "logic-display": BlockInfo("logic-display", 3, "logic", False, "D"),
    "large-logic-display": BlockInfo("large-logic-display", 6, "logic", False, "D"),
    "metaglass-kiln": BlockInfo("kiln", 2, "production", False, "k"),
}


def get_block(name: str) -> BlockInfo:
    """
    Retrieve block metadata by internal name.
    Falls back to a default 1x1 non-rotatable block if unknown.
    """
    cleaned = name.strip().lower().replace(" ", "-")
    if cleaned == "metaglass-kiln":
        cleaned = "kiln"
    if cleaned in BLOCKS:
        return BLOCKS[cleaned]
    return BlockInfo(cleaned, 1, "unknown", False, "?")


def get_item_id(name: str) -> Optional[int]:
    """Retrieve item ID by name."""
    cleaned = name.strip().lower().replace(" ", "-")
    return ITEMS.get(cleaned)


def get_item_name(item_id: int) -> Optional[str]:
    """Retrieve item name by ID."""
    return ITEM_NAMES.get(item_id)


def get_liquid_id(name: str) -> Optional[int]:
    """Retrieve liquid ID by name."""
    cleaned = name.strip().lower().replace(" ", "-")
    return LIQUIDS.get(cleaned)


def get_liquid_name(liquid_id: int) -> Optional[str]:
    """Retrieve liquid name by ID."""
    return LIQUID_NAMES.get(liquid_id)


def get_display_char(block_name: str, rotation: int = 0) -> str:
    """Return appropriate single character display for grid rendering."""
    block = get_block(block_name)
    if block.rotatable and block.category in ("distribution", "liquid"):
        return ROTATION_ARROWS.get(rotation % 4, block.char)
    return block.char
