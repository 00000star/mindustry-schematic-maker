# Contributing to Mindustry Schematic Maker (`msch`)

Thank you for your interest in contributing to **Mindustry Schematic Maker**!

This project is a 100% pure Python standard-library suite for building, simulating, validating, and rendering Mindustry v7 Serpulo schematics with zero external dependencies.

---

## Core Invariants

1. **Zero External Dependencies**:
   All contributions must use only the Python standard library (`zlib`, `struct`, `base64`, `json`, `argparse`, `math`, `collections`, etc.). Never introduce external third-party packages into runtime dependencies.
2. **Mobile Screen Constraint**:
   All CLI output, ASCII grids, and terminal formatting must strictly not exceed **70 columns** in width to ensure perfect legibility on mobile Termux displays.
3. **100% Test Coverage for New Additions**:
   Any new procedural templates, block physics rules, or codec features must include automated unit tests under `tests/`.

---

## Repository Structure

- `core/blocks.py`: Mindustry v7 block catalog, dimensions, categories, and IDs.
- `core/rules.py`: Serpulo block physics, link mechanics, consumer demands, and transport properties.
- `core/codec.py`: Mindustry v7 binary format codec (`msch\x01`) with TypeIO serialization.
- `core/validator.py`: 3-Tier static verification system:
  * **Tier A**: Bounding geometry & multi-tile footprint collision.
  * **Tier B**: Link integrity, bridge vector constraints, and orientation.
  * **Tier C**: Consumer supply, liquid purity, and power network connectivity.
- `core/sim.py`: BFS flood-fill resource supply simulator, single-liquid purity verifier, and leak detector.
- `core/compact.py`: Algorithmic continuous-flow fortifications and ratio-balanced factory layouts.
- `core/generator.py`: Natural language prompt compiler and procedural template builders.
- `core/renderer.py`: Clean ASCII 2D grid visualizer and Bill of Materials generator.
- `core/visual_renderer.py`: Pure-Python RGBA to PNG graphic engine with validated bridge links and glowing supply indicators.
- `core/sync.py`: Android Scoped Storage game sync with root permission fallback.
- `msch` & `msch.py`: Mobile CLI executable.
- `tests/`: Exhaustive unit tests.

---

## Adding Block Physics Rules

When adding support for new Mindustry Serpulo blocks:
1. Register block dimensions in `core/blocks.py`.
2. Define physics parameters in `core/rules.py` within `get_block_physics(name)`:
   - `solid_inputs`, `liquid_inputs`, `ammo_options`
   - `is_consumer`, `requires_power`, `produces_power`
   - `max_bridge_range`, `rotatable`
3. Add corresponding test cases in `tests/test_sim.py` or `tests/test_validator.py`.

---

## Adding Procedural Templates

When implementing new procedural templates:
1. Define the generator function in `core/compact.py` or `core/generator.py`.
2. Connect prompt matching keywords in `compile_from_prompt()`.
3. Include declared inlets using `builder.inlet(x, y, resource)`.
4. Statically validate the layout before returning with `validate_schematic()`.
5. Write an end-to-end test in `tests/test_compact.py` verifying:
   - Exact dimensions and block counts.
   - 0 validation errors.
   - 0 missing supply demands.
   - 0 fluid/item leaks.

---

## Running Tests

Run the full automated unit test suite locally:

```bash
python3 -m unittest discover -v -s tests -p 'test_*.py'
```

Verify that all tests pass without errors or warnings.

---

## Pull Request Guidelines

1. Fork the repository and create your branch from `master`.
2. Ensure commit messages follow Conventional Commits (e.g., `feat: ...`, `fix: ...`, `test: ...`, `docs: ...`).
3. Confirm that all tests pass across Python 3.8 through 3.13.
4. Submit a Pull Request describing your changes and verification evidence.
