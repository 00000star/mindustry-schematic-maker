"""
Pure Python Mindustry v7 Schematic Binary Codec.
Provides lossless encoding and decoding conforming to official Mindustry v7 format.
"""

import base64
import io
import os
import struct
import zlib
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from .blocks import get_block, get_item_id, get_liquid_id
except ImportError:
    try:
        from core.blocks import get_block, get_item_id, get_liquid_id
    except ImportError:
        from blocks import get_block, get_item_id, get_liquid_id

# TypeIO Object Type IDs
TYPE_NULL = 0
TYPE_INT = 1
TYPE_LONG = 2
TYPE_FLOAT = 3
TYPE_STRING = 4
TYPE_CONTENT = 5
TYPE_INT_SEQ = 6
TYPE_POINT2 = 7
TYPE_POINT2_ARRAY = 8
TYPE_BOOL = 10
TYPE_DOUBLE = 11
TYPE_BYTE_ARRAY = 14

CONTENT_TYPE_ITEM = 0
CONTENT_TYPE_BLOCK = 1
CONTENT_TYPE_LIQUID = 2
CONTENT_TYPE_STATUS = 3
CONTENT_TYPE_UNIT = 4


def _write_utf(buf: io.BytesIO, s: str) -> None:
    """Write length-prefixed modified UTF-8 string."""
    encoded = s.encode("utf-8")
    buf.write(struct.pack(">H", len(encoded)))
    buf.write(encoded)


def _read_utf(buf: io.BytesIO) -> str:
    """Read length-prefixed UTF-8 string."""
    length_bytes = buf.read(2)
    if len(length_bytes) < 2:
        return ""
    length, = struct.unpack(">H", length_bytes)
    return buf.read(length).decode("utf-8", errors="replace")


def write_type_object(buf: io.BytesIO, obj: Any) -> None:
    """Serialize a configuration object using Mindustry TypeIO protocol."""
    if obj is None:
        buf.write(struct.pack(">B", TYPE_NULL))
        return

    # Boolean
    if isinstance(obj, bool):
        buf.write(struct.pack(">B", TYPE_BOOL))
        buf.write(struct.pack(">B", 1 if obj else 0))
        return

    # Integer
    if isinstance(obj, int):
        buf.write(struct.pack(">B", TYPE_INT))
        buf.write(struct.pack(">i", obj))
        return

    # Float
    if isinstance(obj, float):
        buf.write(struct.pack(">B", TYPE_FLOAT))
        buf.write(struct.pack(">f", obj))
        return

    # String
    if isinstance(obj, str):
        buf.write(struct.pack(">B", TYPE_STRING))
        buf.write(struct.pack(">B", 1))  # non-null flag
        _write_utf(buf, obj)
        return

    # Raw byte array
    if isinstance(obj, (bytes, bytearray)):
        buf.write(struct.pack(">B", TYPE_BYTE_ARRAY))
        buf.write(struct.pack(">i", len(obj)))
        buf.write(obj)
        return

    # Tagged tuple forms
    if isinstance(obj, tuple):
        tag = obj[0]
        if tag == "content":
            # ("content", content_type, content_id)
            ctype, cid = obj[1], obj[2]
            buf.write(struct.pack(">B", TYPE_CONTENT))
            buf.write(struct.pack(">bh", ctype, cid))
            return
        elif tag == "point2":
            # ("point2", x, y)
            x, y = obj[1], obj[2]
            buf.write(struct.pack(">B", TYPE_POINT2))
            buf.write(struct.pack(">ii", int(x), int(y)))
            return
        elif tag == "point2_array":
            # ("point2_array", [(dx, dy), ...])
            pts = obj[1]
            buf.write(struct.pack(">B", TYPE_POINT2_ARRAY))
            buf.write(struct.pack(">B", len(pts)))
            for dx, dy in pts:
                packed = ((int(dx) & 0xFFFF) << 16) | (int(dy) & 0xFFFF)
                buf.write(struct.pack(">I", packed))
            return
        elif tag == "bytes":
            raw = obj[1]
            buf.write(struct.pack(">B", TYPE_BYTE_ARRAY))
            buf.write(struct.pack(">i", len(raw)))
            buf.write(raw)
            return

    # Fallback to string representation if unrecognized
    buf.write(struct.pack(">B", TYPE_STRING))
    buf.write(struct.pack(">B", 1))
    _write_utf(buf, str(obj))


def read_type_object(buf: io.BytesIO) -> Any:
    """Deserialize a configuration object using Mindustry TypeIO protocol."""
    type_byte = buf.read(1)
    if not type_byte:
        return None
    obj_type, = struct.unpack(">B", type_byte)

    if obj_type == TYPE_NULL:
        return None
    elif obj_type == TYPE_INT:
        return struct.unpack(">i", buf.read(4))[0]
    elif obj_type == TYPE_LONG:
        return struct.unpack(">q", buf.read(8))[0]
    elif obj_type == TYPE_FLOAT:
        return struct.unpack(">f", buf.read(4))[0]
    elif obj_type == TYPE_STRING:
        exists, = struct.unpack(">B", buf.read(1))
        return _read_utf(buf) if exists != 0 else None
    elif obj_type == TYPE_CONTENT:
        ctype, cid = struct.unpack(">bh", buf.read(3))
        return ("content", ctype, cid)
    elif obj_type == TYPE_POINT2:
        x, y = struct.unpack(">ii", buf.read(8))
        return ("point2", x, y)
    elif obj_type == TYPE_POINT2_ARRAY:
        len_pts, = struct.unpack(">B", buf.read(1))
        pts = []
        for _ in range(len_pts):
            val, = struct.unpack(">i", buf.read(4))
            dx = (val >> 16) & 0xFFFF
            if dx >= 0x8000:
                dx -= 0x10000
            dy = val & 0xFFFF
            if dy >= 0x8000:
                dy -= 0x10000
            pts.append((dx, dy))
        return ("point2_array", pts)
    elif obj_type == TYPE_BOOL:
        val, = struct.unpack(">B", buf.read(1))
        return bool(val)
    elif obj_type == TYPE_DOUBLE:
        return struct.unpack(">d", buf.read(8))[0]
    elif obj_type == TYPE_BYTE_ARRAY:
        blen, = struct.unpack(">i", buf.read(4))
        return buf.read(blen)
    else:
        # Unknown/unhandled type
        return None


def encode_schematic(schematic: Dict[str, Any]) -> Tuple[bytes, str]:
    """
    Encode a schematic dictionary into binary v7 .msch format and Base64.
    Automatically normalizes coordinates (min_x = 0, min_y = 0) and
    calculates width/height based on tile footprints.
    Returns (raw_bytes, base64_str).
    """
    tiles = schematic.get("tiles", [])
    if not tiles:
        raise ValueError("Cannot encode schematic with no tiles.")

    # 1. Normalize coordinates
    min_x = min(t["x"] for t in tiles)
    min_y = min(t["y"] for t in tiles)

    normalized_tiles = []
    max_x = 0
    max_y = 0

    for t in tiles:
        nx = t["x"] - min_x
        ny = t["y"] - min_y
        binfo = get_block(t["block"])
        max_x = max(max_x, nx + binfo.size)
        max_y = max(max_y, ny + binfo.size)
        normalized_tiles.append({
            "block": t["block"],
            "x": nx,
            "y": ny,
            "config": t.get("config"),
            "rotation": t.get("rotation", 0),
        })

    width = schematic.get("width", max_x)
    height = schematic.get("height", max_y)
    width = max(width, max_x)
    height = max(height, max_y)

    # 2. Build unique block map
    block_map: List[str] = []
    block_indices: Dict[str, int] = {}
    for t in normalized_tiles:
        b = t["block"]
        if b not in block_indices:
            block_indices[b] = len(block_map)
            block_map.append(b)

    # 3. Build Tags dictionary
    tags: Dict[str, str] = dict(schematic.get("tags", {}))
    if "name" in schematic and "name" not in tags:
        tags["name"] = schematic["name"]
    if "description" in schematic and "description" not in tags:
        tags["description"] = schematic["description"]
    if "name" not in tags:
        tags["name"] = "Schematic"
    if "description" not in tags:
        tags["description"] = ""

    # 4. Binary serialization of payload
    payload = io.BytesIO()
    payload.write(struct.pack(">hh", width, height))

    # Tags
    payload.write(struct.pack(">B", len(tags)))
    for k, v in tags.items():
        _write_utf(payload, str(k))
        _write_utf(payload, str(v))

    # Block Map
    payload.write(struct.pack(">B", len(block_map)))
    for b in block_map:
        _write_utf(payload, b)

    # Tiles
    payload.write(struct.pack(">i", len(normalized_tiles)))
    for t in normalized_tiles:
        b_idx = block_indices[t["block"]]
        payload.write(struct.pack(">B", b_idx))
        payload.write(struct.pack(">hh", t["x"], t["y"]))
        write_type_object(payload, t.get("config"))
        payload.write(struct.pack(">b", t.get("rotation", 0)))

    # 5. Compress payload with zlib deflate (level 9)
    raw_payload = payload.getvalue()
    compressed = zlib.compress(raw_payload, level=9)

    # 6. Prepend Mindustry v7 header b"msch\x01"
    raw_msch = b"msch\x01" + compressed
    b64_str = base64.b64encode(raw_msch).decode("ascii")

    return raw_msch, b64_str


def decode_schematic(data_or_path: Union[str, bytes]) -> Dict[str, Any]:
    """
    Decode a Mindustry schematic from raw bytes, base64 string, or file path.
    Supports Android Scoped Storage (/Android/data) via root fallback if needed.
    Returns structured schematic dict.
    """
    raw_bytes: bytes

    if isinstance(data_or_path, str):
        cleaned = data_or_path.strip()

        # Check for Base64 schematic string first
        # Mindustry v7 schematics in Base64 start with "bXNjaAF" (header b"msch\x01")
        if cleaned.startswith("bXNjaAF") or cleaned.startswith("b64:"):
            if cleaned.startswith("b64:"):
                cleaned = cleaned[4:]
            padding = len(cleaned) % 4
            if padding:
                cleaned += "=" * (4 - padding)
            raw_bytes = base64.b64decode(cleaned)
        elif cleaned.endswith(".msch") or "/" in cleaned or "\\" in cleaned:
            # File path logic
            try:
                with open(cleaned, "rb") as f:
                    raw_bytes = f.read()
            except Exception:
                # Root fallback for Android/data protected directories
                import subprocess
                try:
                    res = subprocess.run(
                        ["su", "-c", f"cat '{cleaned}'"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True,
                    )
                    raw_bytes = res.stdout
                except Exception as e:
                    raise FileNotFoundError(f"Could not read schematic file at {cleaned}: {e}")
        else:
            # General Base64 string fallback
            padding = len(cleaned) % 4
            if padding:
                cleaned += "=" * (4 - padding)
            raw_bytes = base64.b64decode(cleaned)
    else:
        raw_bytes = data_or_path

    if len(raw_bytes) < 5 or raw_bytes[:4] != b"msch":
        raise ValueError("Invalid Mindustry schematic header (expected b'msch').")

    version = raw_bytes[4]
    if version != 1:
        raise ValueError(f"Unsupported schematic version: {version}")

    decompressed = zlib.decompress(raw_bytes[5:])
    buf = io.BytesIO(decompressed)

    width, height = struct.unpack(">hh", buf.read(4))

    # Tags
    tags_count, = struct.unpack(">B", buf.read(1))
    tags = {}
    for _ in range(tags_count):
        k = _read_utf(buf)
        v = _read_utf(buf)
        tags[k] = v

    # Block Map
    block_map_count, = struct.unpack(">B", buf.read(1))
    block_map = []
    for _ in range(block_map_count):
        block_map.append(_read_utf(buf))

    # Tiles
    total_tiles, = struct.unpack(">i", buf.read(4))
    tiles = []
    for _ in range(total_tiles):
        b_idx, = struct.unpack(">B", buf.read(1))
        x, y = struct.unpack(">hh", buf.read(4))
        cfg = read_type_object(buf)
        rot, = struct.unpack(">b", buf.read(1))
        block_name = block_map[b_idx] if b_idx < len(block_map) else "unknown"
        tiles.append({
            "block": block_name,
            "x": x,
            "y": y,
          