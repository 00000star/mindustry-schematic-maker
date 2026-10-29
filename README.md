# Mindustry Schematic Maker (`msch`)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-22%2F22%20passing-brightgreen.svg)](tests/)
[![Mindustry](https://img.shields.io/badge/Mindustry-v7%20Build%20146-orange.svg)](https://mindustrygame.github.io/)

Automated, closed-loop schematic generation, 3-tier static validation, and pure-Python supply simulation engine for **Mindustry v7 Serpulo**. **Zero external dependencies.**

Optimized specifically for mobile displays and terminal environments (strict `<= 70` column output) with native Android Scoped Storage game sync.

---

## Key Features

- **Zero External Dependencies**:
  Built entirely using the Python standard library (`zlib`, `struct`, `base64`, `json`, `argparse`, `math`, `collections`).
- **3-Tier Static Validation Pipeline**:
  * **Tier A (Geometry)**: Multi-tile footprint bounds, non-negative coordinates, and collision/overlap prevention.
  * **Tier B (Link Integrity)**: Strict orthogonal bridge link vectors (`dx == 0` or `dy == 0`), max bridge distance bounds (<= 4 tiles), and head-on conveyor collision rejection.
  * **Tier C (Supply & Fluid Purity)**: Consumer supply verification, power network connectivity, and zero liquid cross-contamination.
- **BFS Flood-Fill Supply Simulation**:
  Simulates resource propagation through conveyors, routers, conduits, liquid-routers, and bridge transport. Proves 100% ammo, coolant, and power delivery to every consumer block.
- **Algorithmic Compact Fortifications & Factories**:
  Procedural alternating continuous-flow defense modules and ratio-balanced factory layouts with perimeter belts.
- **Pure-Python Visual PNG Rendering**:
  Native RGBA rasterizer exporting high-res schematic diagrams with block chassis, rotatable barrels, gold bridge links, and glowing green supply halos.
- **Mobile-First CLI & Android Game Sync**:
  Outputs formatted strictly under 70 columns. Directly writes `.msch` files to Mindustry's Scoped Storage directory with root fallback.

---

## Quick Start

### Installation

Clone and install directly or run without installation:

```bash
git clone https://github.com/00000star/mindustry-schematic-maker.git
cd mindustry-schematic-maker

# Install system-wide or in virtualenv
pip install .

# Or run directly as standalone script
chmod +x msch
./msch --help
```

---

## CLI Command Reference

### 1. Procedural Schematic Generation (`msch make`)

Compile a schematic from a natural language prompt, validate it, preview it in ASCII, and optionally sync to game or export a PNG:

```bash
# Generate a 4-smelter silicon facility
msch make "4 silicon smelter"

# Generate 7x7 nested water-cooled Hail module and sync to game
msch make "nested water cooled hail module" --sync

# Generate with visual PNG preview
msch make "12 cooled duo defense" --image duo_preview.png
```

### 2. Static Validation Checklist (`msch check`)

Run the 3-Tier validation engine against any schematic file or Base64 string:

```bash
msch check "schematics/Nested Water-Cooled Hail Module (18x).msch"
```

Output:
```text
+==================================================================+
| Mindustry Schematic Static Validator                             |
| Target: Nested Water-Cooled Hail Module (18x)                    |
| Dimensions: 7x7        | Total Tiles: 49                         |
+==================================================================+

[STATUS]: PASS (100% Valid)

Checklist Summary:
  ✓ Tier A (Geometry & Multi-Tile Footprints): PASS
  ✓ Tier B (Link Integrity & Orthogonality) : PASS
  ✓ Tier C (Supply Demands & Liquid Purity)  : PASS
```

### 3. Visual & ASCII Previews (`msch preview`)

```bash
msch preview "schematics/Nested Water-Cooled Hail Module (18x).msch"
```

### 4. Direct Game Sync (`msch sync`)

Sync existing project schematics directly to Mindustry:

```bash
msch sync "Nested Water-Cooled Hail Module (18x)"
```

### 5. Listing Schematics (`msch list`)

```bash
# List local project schematics
msch list

# List installed schematics in Mindustry game folder
msch list --game
```

---

## Showcase Gallery

### 1. Nested Water-Cooled Hail Module (18x)

A high-density 7x7 artillery battery featuring 18 water-cooled Hails with dual underfloor bridge distribution (jumping solid ammo and liquid coolant independently without contamination).

- **Dimensions**: 7x7
- **Consumers**: 18x Hail (100% graphite ammo & water coolant supplied)
- **Inlets**: `(0, 0, graphite)`, `(2, 0, water)`, `(5, 0, power)`

```text
6 | RtrtRtr
5 | RtrtRtr
4 | RtrtRtr
3 | RtrtRtr
2 | RtrtRtr
1 | RtrtRtr
0 | R>r>^p^
  +--------
    0123456
```

**Mindustry Base64 Clipboard String:**
```text
bXNjaAF42k3Pu07DMBQG4BPfIoGAV/CCBEOROpWdhQUmJOa0dqilYBfHJuXpwfZfidpDfC7f0Qn11DMSfvi0dPtq52SNfh+SjaunEKYSPA9u0i/B5Mnqu/Xj8Z4ujZ130R2SC57eNseN9nBLczu4fXVjiMmNbjfUXr24tNcmD5PO3tg4TiFEvY3OfFht3Jyi2+ba+KBIxZDLMLpBuQz13/YnRLqa3Fd2ZnWqX//XTXaJLg5hKTv4YCyJugIRrQmnK5f68uAtZOW2gJ9nOxIl/D2dTpBEkzrPorGU2sg6qEWcWkUgkqgpJOuzpRgAA2AADIABMAAOwAE4AAfgABwAq9fNJX6gAgEgUBEAAkAASAAJIAEkgASQABJAASgABaAAFIACKJ8/lq9eew==
```

---

### 2. Compact Cooled Duo Defense (12x)

An ultra-compact 5x9 frontline wall with 12 water-boosted Duos, integrated mender, titanium wall buffer, and power network.

- **Dimensions**: 5x9
- **Consumers**: 12x Duo (100% copper ammo & water coolant supplied)

```text
8 | #####
7 | RtrtR
6 | RtrtR
5 | RtrtR
4 | RtrtR
3 | RtrtR
2 | RtrtR
1 | R>^.>
0 | ^p^+.
  +------
    01234
```

**Mindustry Base64 Clipboard String:**
```text
bXNjaAF42j2O207EIBCGh3La1Wx8hV66MTXRV3CvvfS+lulK0sJKwerT69DZCIR//m8OABr2DajQzwjtS5wv/ZBJ44SuPZXYnnDEsGB7//T8fYRbh8uQ/CX7GOD1DZMfPRUO1z5HDWNMmejQ15ra1uaSEubl2K4+f1BtyD6UWJZunOLazn3wY5zc4x52lPvCn5jg5hJXTF2IDsESdcVnMDMGhwlMiiWT3r0n787Y/XcdJv9ZvOuueUnfgUP2mV4oc7f20wQAD7AtIUBUbWiTkyCrUzUG0HQJS/EGtxoCmtLC/l7XVku9hkco2g0PkAwlQ8lQMVQMFUPNUDPUDA1Dw9AwtAwtQ1uBqL+yNH8TQcHmJDvFTrHT7DQ7w86ws+xIdvTQrh7B0rBIFlXlDySoWo4=
```

---

## Python API Usage

You can use `mindustry-schematic-maker` programmatically in Python applications:

```python
from core.compact import build_nested_artillery_module
from core.codec import encode_schematic, decode_schematic
from core.validator import validate_schematic
from core.sim import trace_supply
from core.visual_renderer import render_schematic_png

# 1. Build schematic programmatically
schem = build_nested_artillery_module("hail")

# 2. Statically validate
validation = validate_schematic(schem, inlets=schem.get("inlets"))
assert validation.is_valid

# 3. Simulate resource supply
report = trace_supply(schem, inlets=schem.get("inlets"))
assert len(report.missing_demands(include_optional=True)) == 0
assert len(report.leaks()) == 0

# 4. Export binary and Base64 string
raw_bytes, b64_str = encode_schematic(schem)
print("Base64:", b64_str)

# 5. Render visual PNG
png_bytes = render_schematic_png(schem)
with open("hail_module.png", "wb") as f:
    f.write(png_bytes)
```

---

## Running Unit Tests

Execute the test suite across all modules:

```bash
python3 -m unittest discover -v -s tests -p 'test_*.py'
```

Output:
```text
Ran 22 tests in 1.428s

OK
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on code guidelines, adding new block physics rules, and submitting pull requests.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
