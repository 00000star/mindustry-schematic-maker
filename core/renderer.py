"""
Mobile-Friendly ASCII Schematic Preview Renderer.
Strictly constrained to <= 70 columns for mobile terminal display.
"""

from typing import Any, Dict, List
from collections import Counter

try:
    from .blocks import get_block, get_display_char
except ImportError:
    try:
        from core.blocks import get_block, get_display_char
    except ImportError:
        from blocks import get_display_char, get_block


MAX_COLUMNS = 70


def render_schematic_ascii(schematic: Dict[str, Any]) -> str:
    """
    Render a Mindustry schematic as an ASCII preview formatted for mobile screens.
    Every single line is guaranteed to be <= 70 characters wide.
    """
    lines: List[str] = []

    name = schematic.get("name", "Unnamed Schematic")
    width = int(schematic.get("width", 0))
    height = int(schematic.get("height", 0))
    tiles = schematic.get("tiles", [])

    # If width/height not set, calculate from tiles
    if width <= 0 or height <= 0:
        for t in tiles:
            b = get_block(t["block"])
            width = max(width, t["x"] + b.size)
            height = max(height, t["y"] + b.size)

    # 1. Header Card
    border = "=" * 66
    lines.append(f"+{border}+")
    name_str = f"| Mindustry Schematic: {name}"[:67]
    lines.append(f"{name_str:<67}|")
    meta_str = f"| Size: {width}x{height} | Total Tiles: {len(tiles)}"[:67]
    lines.append(f"{meta_str:<67}|")
    lines.append(f"+{border}+")

    # 2. Build 2D Grid
    # Initialize grid with dots
    grid = [["." for _ in range(width)] for _ in range(height)]

    # Populate tiles with footprints
    for t in tiles:
        b_name = t["block"]
        b_info = get_block(b_name)
        bx = t["x"]
        by = t["y"]
        rot = t.get("rotation", 0)
        char = get_display_char(b_name, rot)

        for dy in range(b_info.size):
            for dx in range(b_info.size):
                gx = bx + dx
                gy = by + dy
                if 0 <= gx < width and 0 <= gy < height:
                    grid[gy][gx] = char

    # 3. Render 2D Grid (Y from height-1 down to 0)
    lines.append("Grid Preview:")
    y_width = len(str(height - 1)) if height > 0 else 1
    avail_cols = MAX_COLUMNS - (y_width + 3)  # space for " 0 | "

    # Render row by row
    for y in range(height - 1, -1, -1):
        row_chars = "".join(grid[y])
        # Truncate if grid is wider than available columns
        if len(row_chars) > avail_cols:
            row_chars = row_chars[:avail_cols - 1] + ">"
        y_label = f"{y:>{y_width}} | "
        lines.append(f"{y_label}{row_chars}")

    # X-axis divider
    x_axis_border = "-" * min(width, avail_cols)
    lines.append(f"{' ' * y_width} +-{x_axis_border}")

    # X-axis numbers (tens and units)
    if width > 10:
        tens_line = "".join(str(x // 10) if x >= 10 and x % 5 == 0 else " " for x in range(min(width, avail_cols)))
        lines.append(f"{' ' * y_width}   {tens_line}")
    units_line = "".join(str(x % 10) if x % 5 == 0 or x < 10 else " " for x in range(min(width, avail_cols)))
    lines.append(f"{' ' * y_width}   {units_line}")

    # 4. Bill of Materials
    lines.append("")
    lines.append(f"+{border}+")
    lines.append(f"| Bill of Materials:{' ' * 47}|")
    block_counts = Counter(t["block"] for t in tiles)
    for block_name, count in sorted(block_counts.items(), key=lambda x: -x[1]):
        binfo = get_block(block_name)
        dim_str = f"({binfo.size}x{binfo.size})"
        item_line = f"|  • {block_name:<24} {dim_str:<7} x {count:>3}"[:67]
        lines.append(f"{item_line:<67}|")
    lines.append(f"+{border}+")

    # Hard clamp every line to <= MAX_COLUMNS (70)
    clamped_lines = [line[:MAX_COLUMNS] for line in lines]
    return "\n".join(clamped_lines)
