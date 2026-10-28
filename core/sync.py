"""
Schematic Sync and Storage Manager.
Handles saving schematics to the local project folder and syncing directly
to the Mindustry game data directory with root fallback.
"""

import os
import re
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

try:
    from .codec import encode_schematic
except ImportError:
    try:
        from core.codec import encode_schematic
    except ImportError:
        from codec import encode_schematic

PROJECT_DIR = "/storage/emulated/0/Antigravity/projects/mindustry-schematic-maker"
PROJECT_SCHEMATICS_DIR = os.path.join(PROJECT_DIR, "schematics")
GAME_SCHEMATICS_DIR = "/storage/emulated/0/Android/data/io.anuke.mindustry/files/schematics"


def sanitize_filename(name: str) -> str:
    """Sanitize name to make safe for filesystem storage."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return clean if clean else "unnamed_schematic"


def save_to_project(schematic: Dict[str, Any], filename: Optional[str] = None) -> str:
    """Save schematic into project schematics folder."""
    os.makedirs(PROJECT_SCHEMATICS_DIR, exist_ok=True)

    if not filename:
        name = schematic.get("name", "schematic")
        filename = f"{sanitize_filename(name)}.msch"

    if not filename.endswith(".msch"):
        filename += ".msch"

    dest_path = os.path.join(PROJECT_SCHEMATICS_DIR, filename)
    raw_bytes, _ = encode_schematic(schematic)

    try:
        with open(dest_path, "wb") as f:
            f.write(raw_bytes)
    except PermissionError:
        # Fallback using su
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name
        cmd = 'su -c \'cp "' + tmp_path + '" "' + dest_path + '" && chmod 664 "' + dest_path + '" && rm -f "' + tmp_path + '"\''
        subprocess.run(cmd, shell=True, check=True)

    return dest_path


def sync_to_game(schematic: Dict[str, Any], filename: Optional[str] = None) -> Tuple[bool, str]:
    """
    Directly sync schematic to the Mindustry game schematics directory.
    Uses root execution fallback for Android Scoped Storage (/Android/data).
    """
    if not filename:
        name = schematic.get("name", "schematic")
        filename = f"{sanitize_filename(name)}.msch"

    if not filename.endswith(".msch"):
        filename += ".msch"

    dest_path = os.path.join(GAME_SCHEMATICS_DIR, filename)
    raw_bytes, _ = encode_schematic(schematic)

    # 1. Attempt direct unprivileged write
    try:
        if os.path.exists(GAME_SCHEMATICS_DIR):
            with open(dest_path, "wb") as f:
                f.write(raw_bytes)
            return True, dest_path
    except Exception:
        pass

    # 2. Privileged root fallback for Android Scoped Storage
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name

        # Ensure target directory exists and copy with game ownership
        copy_cmd = (
            f"su -c 'mkdir -p \"{GAME_SCHEMATICS_DIR}\" && "
            f"cp \"{tmp_path}\" \"{dest_path}\" && "
            f"chmod 660 \"{dest_path}\" && "
            f"rm -f \"{tmp_path}\"'"
        )
        res = subprocess.run(
            copy_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if res.returncode == 0:
            return True, dest_path
        else:
            return False, f"Root sync failed: {res.stderr.decode('utf-8', errors='replace')}"
    except Exception as e:
        return False, f"Sync exception: {e}"


def list_project_schematics() -> List[str]:
    """List all schematic files in the project schematics directory."""
    if not os.path.exists(PROJECT_SCHEMATICS_DIR):
        return []
    return [f for f in os.listdir(PROJECT_SCHEMATICS_DIR) if f.endswith(".msch")]


def list_game_schematics() -> List[str]:
    """
    List all schematic files installed in Mindustry.
    Supports root listing fallback for Android Scoped Storage.
    """
    # Try normal os.listdir
    try:
        if os.path.exists(GAME_SCHEMATICS_DIR):
            return [f for f in os.listdir(GAME_SCHEMATICS_DIR) if f.endswith(".msch")]
    except Exception:
        pass

    # Root fallback
    try:
        cmd = f"su -c 'ls \"{GAME_SCHEMATICS_DIR}\"'"
        res = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if res.returncode == 0:
            files = [line.strip() for line in res.stdout.splitlines() if line.strip().endswith(".msch")]
            return files
    except Exception:
        pass

    return []
