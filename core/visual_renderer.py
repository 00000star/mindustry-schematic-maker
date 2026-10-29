"""
Pure Python Mindustry Schematic PNG Visual Renderer.
Zero third-party dependencies (uses only standard library struct and zlib).
Renders high-detail pixel graphics with block chassis, directional turrets,
glowing projectors, power nodes, and validated bridge connection vectors.
"""

import math
import struct
import zlib
from typing import Any, Dict, List, Optional, Tuple

try:
    from .blocks import get_block
    from .rules import get_block_physics
    from .sim import trace_supply
except ImportError:
    try:
        from core.blocks import get_block
        from core.rules import get_block_physics
        from core.sim import trace_supply
    except ImportError:
        from blocks import get_block
        from rules import get_block_physics
        from sim import trace_supply


# Palette Definitions (RGBA)
COLOR_BG = (30, 32, 36, 255)            # #1e2024 Dark Slate
COLOR_GRID = (42, 45, 51, 255)          # #2a2d33 Grid lines
COLOR_WALL = (112, 136, 221, 255)       # #7088dd Titanium Wall
COLOR_WALL_BORDER = (75, 98, 179, 255)  # Darker wall border
COLOR_WALL_CORE = (139, 162, 237, 255)  # Lighter wall inner highlight

COLOR_DUO_CHASSIS = (58, 61, 69, 255)   # #3a3d45 Dark gray chassis
COLOR_DUO_RING = (38, 40, 46, 255)      # Ring
COLOR_DUO_BARREL = (200, 204, 212, 255) # #c8ccd4 Light gray dual barrels

COLOR_ROUTER = (85, 85, 94, 255)        # #55555e Router body
COLOR_ROUTER_CROSS = (138, 138, 152, 255) # Cross marker

COLOR_GATE = (68, 85, 102, 255)         # #445566 Underflow / Overflow
COLOR_GATE_MARK = (119, 153, 187, 255)  # Gate chevron

COLOR_OVERDRIVE = (229, 170, 50, 255)   # #e5aa32 Warm amber glowing circle
COLOR_OVERDRIVE_CORE = (255, 235, 127, 255) # Core
COLOR_OVERDRIVE_AURA = (229, 170, 50, 45)   # Transparent aura ring

COLOR_MENDER = (68, 187, 119, 255)      # #44bb77 Emerald green
COLOR_MENDER_CROSS = (255, 255, 255, 255) # Medical cross

COLOR_POWER = (255, 238, 85, 255)       # #ffee55 Glowing yellow
COLOR_POWER_BASE = (56, 56, 44, 255)    # Node base

COLOR_CONVEYOR = (194, 122, 66, 255)    # #c27a42 Dark copper
COLOR_CONVEYOR_ARROW = (255, 187, 136, 255)

COLOR_CONDUIT = (70, 110, 170, 255)     # Conduit blue
COLOR_CONDUIT_MARK = (120, 170, 230, 255)

COLOR_BRIDGE = (110, 95, 80, 255)       # Bridge body
COLOR_BRIDGE_GOLD = (255, 215, 0, 255)  # #ffd700 Valid bridge link
COLOR_BRIDGE_RED = (255, 51, 51, 255)   # #ff3333 Invalid/missing bridge link


class Canvas:
    """Pure Python RGBA Pixel Canvas with 2D geometric drawing primitives."""

    def __init__(self, width: int, height: int, bg_color=COLOR_BG):
        self.width = width
        self.height = height
        self.pixels = bytearray(bg_color * (width * height))

    def set_pixel(self, x: int, y: int, r: int, g: int, b: int, a: int = 255):
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = (y * self.width + x) * 4
            if a >= 255:
                self.pixels[idx] = r
                self.pixels[idx + 1] = g
                self.pixels[idx + 2] = b
                self.pixels[idx + 3] = 255
            else:
                alpha = a / 255.0
                inv_a = 1.0 - alpha
                self.pixels[idx] = int(r * alpha + self.pixels[idx] * inv_a)
                self.pixels[idx + 1] = int(g * alpha + self.pixels[idx + 1] * inv_a)
                self.pixels[idx + 2] = int(b * alpha + self.pixels[idx + 2] * inv_a)
                self.pixels[idx + 3] = 255

    def fill_rect(self, x0: int, y0: int, w: int, h: int, color):
        r, g, b = color[:3]
        a = color[3] if len(color) > 3 else 255
        x1 = min(self.width, x0 + w)
        y1 = min(self.height, y0 + h)
        x0 = max(0, x0)
        y0 = max(0, y0)
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.set_pixel(x, y, r, g, b, a)

    def draw_rect(self, x0: int, y0: int, w: int, h: int, color, fill_color=None):
        if fill_color:
            self.fill_rect(x0, y0, w, h, fill_color)
        r, g, b = color[:3]
        a = color[3] if len(color) > 3 else 255
        x1 = x0 + w - 1
        y1 = y0 + h - 1
        for x in range(x0, x0 + w):
            self.set_pixel(x, y0, r, g, b, a)
            self.set_pixel(x, y1, r, g, b, a)
        for y in range(y0, y0 + h):
            self.set_pixel(x0, y, r, g, b, a)
            self.set_pixel(x1, y, r, g, b, a)

    def draw_circle(self, cx: int, cy: int, radius: int, color, fill: bool = False):
        r, g, b = color[:3]
        a = color[3] if len(color) > 3 else 255
        r2 = radius * radius
        if fill:
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                        self.set_pixel(x, y, r, g, b, a)
        else:
            inner_r2 = max(0, radius - 1) ** 2
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    d2 = (x - cx) ** 2 + (y - cy) ** 2
                    if inner_r2 <= d2 <= r2:
                        self.set_pixel(x, y, r, g, b, a)

    def draw_diamond(self, cx: int, cy: int, radius: int, color):
        """Draw a filled diamond shape centered at (cx, cy)."""
        r, g, b = color[:3]
        a = color[3] if len(color) > 3 else 255
        for dy in range(-radius, radius + 1):
            span = radius - abs(dy)
            for dx in range(-span, span + 1):
                self.set_pixel(cx + dx, cy + dy, r, g, b, a)

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color, dotted: bool = False):
        """Bresenham's line algorithm with support for dotted patterns and 2px stroke."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        r, g, b = color[:3]
        a = color[3] if len(color) > 3 else 255
        step = 0
        while True:
            if not dotted or (step % 6 < 4):
                self.set_pixel(x0, y0, r, g, b, a)
                self.set_pixel(x0 + 1, y0, r, g, b, a)
                self.set_pixel(x0, y0 + 1, r, g, b, a)
            step += 1
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def to_png_bytes(self) -> bytes:
        """Encode raw RGBA buffer into standard compliant PNG format."""
        def make_chunk(tag: bytes, data: bytes) -> bytes:
            crc = zlib.crc32(tag + data) & 0xFFFFFFFF
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

        ihdr = make_chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 6, 0, 0, 0))

        row_len = self.width * 4
        raw_scanlines = bytearray()
        for y in range(self.height):
            raw_scanlines.append(0)  # Filter byte 0 (None)
            offset = y * row_len
            raw_scanlines.extend(self.pixels[offset:offset + row_len])

        idat = make_chunk(b"IDAT", zlib.compress(bytes(raw_scanlines), level=9))
        iend = make_chunk(b"IEND", b"")

        return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend


def render_schematic_png(schematic: Dict[str, Any], cell_size: int = 28) -> bytes:
    """
    Render a Mindustry schematic dictionary into a visual PNG graphic.
    Features detailed block chassis, turret rotations, and verified bridge link vectors.
    """
    width = int(schematic.get("width", 0))
    height = int(schematic.get("height", 0))
    tiles = schematic.get("tiles", [])

    if width <= 0 or height <= 0:
        for t in tiles:
            b = get_block(t["block"])
            width = max(width, t["x"] + b.size)
            height = max(height, t["y"] + b.size)

    width = max(1, width)
    height = max(1, height)

    img_w = width * cell_size
    img_h = height * cell_size

    canvas = Canvas(img_w, img_h, bg_color=COLOR_BG)

    # 1. Draw Grid Lines
    for gx in range(width + 1):
        x = min(img_w - 1, gx * cell_size)
        canvas.draw_line(x, 0, x, img_h - 1, COLOR_GRID)
    for gy in range(height + 1):
        y = min(img_h - 1, gy * cell_size)
        canvas.draw_line(0, y, img_w - 1, y, COLOR_GRID)

    # Coordinate transformation: Mindustry (0,0) is bottom-left
    def tile_to_pixel(tx: int, ty: int, size: int = 1) -> Tuple[int, int]:
        px = tx * cell_size
        py = (height - ty - size) * cell_size
        return px, py

    # Tile map for fast link destination lookups
    tile_map = {(t["x"], t["y"]): t for t in tiles}

    # 2. Render Blocks
    for t in tiles:
        b_name = t["block"]
        b_info = get_block(b_name)
        size = b_info.size
        rot = t.get("rotation", 0)
        px, py = tile_to_pixel(t["x"], t["y"], size)
        pw = size * cell_size
        ph = size * cell_size

        # Inset margins
        m = 1
        bx, by, bw, bh = px + m, py + m, pw - (2 * m), ph - (2 * m)
        cx, cy = px + (pw // 2), py + (ph // 2)

        if "wall" in b_name:
            canvas.draw_rect(bx, by, bw, bh, COLOR_WALL_BORDER, fill_color=COLOR_WALL)
            canvas.fill_rect(bx + 4, by + 4, bw - 8, bh - 8, COLOR_WALL_CORE)

        elif b_name == "duo":
            canvas.draw_rect(bx, by, bw, bh, (45, 48, 55, 255), fill_color=COLOR_DUO_CHASSIS)
            canvas.draw_circle(cx, cy, 7, COLOR_DUO_RING, fill=True)
            # Draw dual barrels pointing in rotation direction
            # rot: 0: East, 1: North, 2: West, 3: South
            if rot == 1:  # North (up)
                canvas.fill_rect(cx - 3, cy - 8, 2, 8, COLOR_DUO_BARREL)
                canvas.fill_rect(cx + 1, cy - 8, 2, 8, COLOR_DUO_BARREL)
            elif rot == 0:  # East (right)
                canvas.fill_rect(cx, cy - 3, 8, 2, COLOR_DUO_BARREL)
                canvas.fill_rect(cx, cy + 1, 8, 2, COLOR_DUO_BARREL)
            elif rot == 3:  # South (down)
                canvas.fill_rect(cx - 3, cy, 2, 8, COLOR_DUO_BARREL)
                canvas.fill_rect(cx + 1, cy, 2, 8, COLOR_DUO_BARREL)
            elif rot == 2:  # West (left)
                canvas.fill_rect(cx - 8, cy - 3, 8, 2, COLOR_DUO_BARREL)
                canvas.fill_rect(cx - 8, cy + 1, 8, 2, COLOR_DUO_BARREL)

        elif b_name == "hail":
            canvas.draw_rect(bx, by, bw, bh, (45, 48, 55, 255), fill_color=(80, 85, 95, 255))
            canvas.draw_circle(cx, cy, 6, (120, 125, 135, 255), fill=True)
            canvas.draw_circle(cx, cy, 4, (40, 42, 48, 255), fill=True)
            # Mortar / artillery barrel pointing in rot direction
            if rot == 1:  # North
                canvas.fill_rect(cx - 2, cy - 8, 4, 8, (160, 165, 175, 255))
            elif rot == 0:  # East
                canvas.fill_rect(cx, cy - 2, 8, 4, (160, 165, 175, 255))
            elif rot == 3:  # South
                canvas.fill_rect(cx - 2, cy, 4, 8, (160, 165, 175, 255))
            elif rot == 2:  # West
                canvas.fill_rect(cx - 8, cy - 2, 8, 4, (160, 165, 175, 255))

        elif b_name == "liquid-router":
            canvas.draw_rect(bx, by, bw, bh, (40, 70, 110, 255), fill_color=(50, 90, 150, 255))
            canvas.fill_rect(cx - 2, by + 3, 4, bh - 6, (90, 160, 230, 255))
            canvas.fill_rect(bx + 3, cy - 2, bw - 6, 4, (90, 160, 230, 255))
            canvas.draw_circle(cx, cy, 4, (30, 60, 100, 255), fill=True)

        elif b_name == "router":
            canvas.draw_rect(bx, by, bw, bh, (60, 60, 70, 255), fill_color=COLOR_ROUTER)
            # Cross
            canvas.fill_rect(cx - 2, by + 3, 4, bh - 6, COLOR_ROUTER_CROSS)
            canvas.fill_rect(bx + 3, cy - 2, bw - 6, 4, COLOR_ROUTER_CROSS)
            canvas.draw_circle(cx, cy, 4, (40, 40, 50, 255), fill=True)

        elif "gate" in b_name:
            canvas.draw_rect(bx, by, bw, bh, (50, 65, 80, 255), fill_color=COLOR_GATE)
            # Chevron
            canvas.draw_line(cx - 5, cy - 4, cx, cy, COLOR_GATE_MARK)
            canvas.draw_line(cx, cy, cx + 5, cy - 4, COLOR_GATE_MARK)
            canvas.draw_line(cx - 5, cy + 4, cx, cy, COLOR_GATE_MARK)
            canvas.draw_line(cx, cy, cx + 5, cy + 4, COLOR_GATE_MARK)

        elif "overdrive" in b_name:
            # Check if adjacent cell is occupied
            is_single_slot = tile_map.get((t["x"] + 1, t["y"])) is not None
            draw_w = cell_size if is_single_slot else pw
            draw_h = cell_size if is_single_slot else ph
            canvas.draw_rect(bx, by, draw_w - (2 * m), draw_h - (2 * m), (70, 60, 40, 255), fill_color=(45, 40, 30, 255))
            draw_cx = bx + (draw_w // 2)
            draw_cy = by + (draw_h // 2)
            canvas.draw_circle(draw_cx, draw_cy, max(4, draw_w // 2 - 2), COLOR_OVERDRIVE_AURA, fill=True)
            canvas.draw_circle(draw_cx, draw_cy, max(3, draw_w // 3), COLOR_OVERDRIVE, fill=True)
            canvas.draw_circle(draw_cx, draw_cy, max(1, draw_w // 5), COLOR_OVERDRIVE_CORE, fill=True)

        elif "mender" in b_name:
            canvas.draw_rect(bx, by, bw, bh, (35, 80, 50, 255), fill_color=COLOR_MENDER)
            # Medical cross
            canvas.fill_rect(cx - 2, cy - 6, 4, 12, COLOR_MENDER_CROSS)
            canvas.fill_rect(cx - 6, cy - 2, 12, 4, COLOR_MENDER_CROSS)

        elif "power" in b_name or b_name == "node":
            canvas.draw_rect(bx, by, bw, bh, (70, 70, 40, 255), fill_color=COLOR_POWER_BASE)
            canvas.draw_circle(cx, cy, 5, COLOR_POWER, fill=True)
            canvas.draw_circle(cx, cy, 2, (255, 255, 255, 255), fill=True)

        elif "bridge" in b_name:
            canvas.draw_rect(bx, by, bw, bh, (80, 70, 60, 255), fill_color=COLOR_BRIDGE)
            # Slit
            canvas.draw_circle(cx, cy, 5, (40, 35, 30, 255), fill=True)

        elif "conduit" in b_name:
            canvas.draw_rect(bx, by, bw, bh, (50, 80, 130, 255), fill_color=COLOR_CONDUIT)
            canvas.draw_circle(cx, cy, 4, COLOR_CONDUIT_MARK, fill=True)

        elif "conveyor" in b_name:
            canvas.draw_rect(bx, by, bw, bh, (140, 90, 50, 255), fill_color=COLOR_CONVEYOR)
            # Directional Arrow
            if rot == 0:  # East
                canvas.draw_line(cx - 4, cy - 4, cx + 2, cy, COLOR_CONVEYOR_ARROW)
                canvas.draw_line(cx - 4, cy + 4, cx + 2, cy, COLOR_CONVEYOR_ARROW)
            elif rot == 1:  # North
                canvas.draw_line(cx - 4, cy + 4, cx, cy - 2, COLOR_CONVEYOR_ARROW)
                canvas.draw_line(cx + 4, cy + 4, cx, cy - 2, COLOR_CONVEYOR_ARROW)
            elif rot == 2:  # West
                canvas.draw_line(cx + 4, cy - 4, cx - 2, cy, COLOR_CONVEYOR_ARROW)
                canvas.draw_line(cx + 4, cy + 4, cx - 2, cy, COLOR_CONVEYOR_ARROW)
            elif rot == 3:  # South
                canvas.draw_line(cx - 4, cy - 4, cx, cy + 2, COLOR_CONVEYOR_ARROW)
                canvas.draw_line(cx + 4, cy - 4, cx, cy + 2, COLOR_CONVEYOR_ARROW)

        else:
            # Generic block fallback
            canvas.draw_rect(bx, by, bw, bh, (100, 100, 100, 255), fill_color=(60, 60, 65, 255))

    # 3. Render Validated Bridge Vectors (Dotted overlay lines)
    for t in tiles:
        b_name = t["block"]
        if "bridge" in b_name:
            cfg = t.get("config")
            if isinstance(cfg, tuple) and len(cfg) >= 3 and cfg[0] == "point2":
                dx, dy = int(cfg[1]), int(cfg[2])
                if (dx, dy) != (-1, -1) and (dx != 0 or dy != 0):
                    dst_x = t["x"] + dx
                    dst_y = t["y"] + dy

                    src_px, src_py = tile_to_pixel(t["x"], t["y"], 1)
                    dst_px, dst_py = tile_to_pixel(dst_x, dst_y, 1)

                    src_cx = src_px + (cell_size // 2)
                    src_cy = src_py + (cell_size // 2)
                    dst_cx = dst_px + (cell_size // 2)
                    dst_cy = dst_py + (cell_size // 2)

                    # Validation: Target tile must exist and be a bridge block
                    target_tile = tile_map.get((dst_x, dst_y))
                    is_valid = target_tile is not None and "bridge" in target_tile["block"]

                    line_color = COLOR_BRIDGE_GOLD if is_valid else COLOR_BRIDGE_RED

                    # Draw dotted bridge line
                    canvas.draw_line(src_cx, src_cy, dst_cx, dst_cy, line_color, dotted=True)
                    # Destination target ring
                    canvas.draw_circle(dst_cx, dst_cy, 4, line_color, fill=False)

    # 4. Render Visual Supply Overlays (Ammo, Coolant & Consumer Health Indicators)
    try:
        supply_report = trace_supply(schematic)
        missing_set = {(m["x"], m["y"]) for m in supply_report.missing_demands(include_optional=True)}

        for t in tiles:
            b_name = t["block"]
            phys = get_block_physics(b_name)
            ox, oy = t.get("x", 0), t.get("y", 0)
            size = phys.size
            px, py = tile_to_pixel(ox, oy, size)
            bw, bh = size * cell_size, size * cell_size
            supplied = supply_report.supplied_resources.get((ox, oy), set())

            # Indicator A: Orange diamond indicator on blocks receiving ammo
            has_ammo = bool(supplied.intersection(phys.ammo_options) or "ammo" in supplied or "copper" in supplied or "lead" in supplied or "coal" in supplied)
            if has_ammo:
                diamond_x = px + 6
                diamond_y = py + 6
                canvas.draw_diamond(diamond_x, diamond_y, radius=3, color=(230, 126, 34, 255))

            # Indicator B: Blue droplet indicator on blocks receiving water
            has_water = bool("water" in supplied or "cryofluid" in supplied or "liquid" in supplied)
            if has_water:
                droplet_x = px + 6
                droplet_y = py + bh - 6
                canvas.draw_circle(droplet_x, droplet_y, radius=3, color=(52, 152, 219, 255), fill=True)

            # Indicator C: Consumer health status
            if phys.is_consumer:
                cx_dot = px + bw - 6
                cy_dot = py + 6
                if (ox, oy) in missing_set:
                    # Red warning dot/border on consumers missing ammo or coolant
                    canvas.draw_circle(cx_dot, cy_dot, radius=3, color=(231, 76, 60, 255), fill=True)
                    canvas.draw_rect(px, py, bw, bh, border_color=(231, 76, 60, 160))
                else:
                    # Green dot/halo on consumers that are 100% fully supplied
                    canvas.draw_circle(cx_dot, cy_dot, radius=3, color=(46, 204, 113, 255), fill=True)
                    canvas.draw_circle(cx_dot, cy_dot, radius=5, color=(46, 204, 113, 90), fill=False)
    except Exception:
        pass

    return canvas.to_png_bytes()
