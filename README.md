# Mindustry Schematic Maker (`msch`)

Pure Python standard-library binary encoder, decoder, procedural generator, ASCII preview renderer, and direct game sync tool for **Mindustry v7** schematics (`.msch`).

Optimized specifically for mobile Termux displays with strict `<= 70` column formatting.

## Features
- **Zero Dependencies**: 100% Python standard library (`zlib`, `struct`, `base64`, `json`, `argparse`).
- **Binary Codec**: Fully compatible with Mindustry v7 `msch\x01` format, including TypeIO serialization (Point2, Point2[], Content mapping, MLOG bytecode byte arrays, etc.).
- **Mobile ASCII Renderer**: Clean 2D grid representation with multi-tile footprint resolution, directional conveyor glyphs (`>`, `<`, `^`, `v`), axis indices, and Bill of Materials (BOM) breakdown.
- **Procedural Generation & Natural Language Compiler**:
  - `4 silicon smelter`
  - `8 graphite press`
  - `metaglass kiln`
  - `cryofluid plant`
  - `thorium reactor safe` (auto-wires anti-meltdown microprocessor logic)
  - `defense line salvo 4`
  - `solar array`
- **Direct Mindustry Game Sync**: Seamlessly writes `.msch` files directly to `/storage/emulated/0/Android/data/io.anuke.mindustry/files/schematics` with automatic root fallback for Android Scoped Storage.

## CLI Usage

```bash
# Generate from natural language prompt
msch make "4 silicon smelter"

# Generate and sync directly to Mindustry game
msch make "thorium reactor with logic" --sync

# Render ASCII preview of an existing schematic or base64 string
msch preview "schematics/Silicon Factory (4x).msch"

# Decode schematic to structured JSON
msch decode "schematics/Silicon Factory (4x).msch"

# List project or installed game schematics
msch list
msch list --game

# Sync an existing schematic to the game folder
msch sync "Silicon Factory (4x)"
```

## Running Unit Tests

```bash
python3 -m unittest tests/test_roundtrip.py
```
