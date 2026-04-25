"""
Extract vanilla game JSON assets directly from game paks using repak.
Run this whenever the game updates to refresh the vanilla baseline.

Usage:
    python tools/extract_vanilla.py

Outputs to: tools/extracted_vanilla/
"""

import subprocess
import sys
from pathlib import Path

REPAK = Path("tools/repak/repak.exe")
AES_KEY = "0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE"
OUT_DIR = Path("tools/extracted_vanilla")

# All pakchunks to check — add new ones here if the game adds more
PAK_CANDIDATES = [
    "pakchunk0-Windows.pak",
    "pakchunk0_s1-Windows.pak",
    "pakchunk0_s2-Windows.pak",
    "pakchunk0_s3-Windows.pak",
    "pakchunk0_s4-Windows.pak",
]

# Asset path prefixes to extract
WANTED_PREFIXES = [
    # Resource node spawner configs (respawn timers + quantity variants)
    "R5/Content/Gameplay/Actor/SpawnPoints/A2_Spawners/ResourcesSpawners/",
    # Mineral loot tables (copper, iron, stone, sulfur, ancient debris, etc.)
    "R5/Plugins/R5BusinessRules/Content/LootTables/Foliage/DA_LT_Mineral",
    # All foliage loot tables (trees, stumps, bushes, etc.) — vanilla baseline
    "R5/Plugins/R5BusinessRules/Content/LootTables/Foliage/DA_LT_Foliage",
    # Animal / mob drop loot tables
    "R5/Plugins/R5BusinessRules/Content/LootTables/Mobs/",
]


def get_game_paks_dir() -> Path:
    """Read game path from data/settings.json."""
    import json
    settings = Path("data/settings.json")
    if not settings.exists():
        sys.exit("No data/settings.json — open the app and set your game path in Settings first.")
    data = json.loads(settings.read_text())
    game_path = data.get("game_path", "")
    if not game_path:
        sys.exit("game_path is empty in settings.json — set your game path in Settings first.")
    paks_dir = Path(game_path) / "R5/Content/Paks"
    if not paks_dir.exists():
        sys.exit(f"Game paks directory not found: {paks_dir}")
    return paks_dir


def list_pak(pak_path: Path) -> list[str]:
    result = subprocess.run(
        [str(REPAK), "-a", AES_KEY, "list", str(pak_path)],
        capture_output=True, text=True
    )
    return result.stdout.splitlines()


def get_file(pak_path: Path, asset_path: str) -> bytes:
    result = subprocess.run(
        [str(REPAK), "-a", AES_KEY, "get", str(pak_path), asset_path],
        capture_output=True
    )
    return result.stdout


def wanted(path: str) -> bool:
    return any(path.startswith(p) for p in WANTED_PREFIXES) and path.endswith(".json")


def main():
    paks_dir = get_game_paks_dir()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    extracted = 0
    skipped = 0

    for pak_name in PAK_CANDIDATES:
        pak_path = paks_dir / pak_name
        if not pak_path.exists():
            continue

        print(f"Scanning {pak_name}...")
        all_files = list_pak(pak_path)
        targets = [f for f in all_files if wanted(f)]
        print(f"  {len(targets)} assets to extract")

        for asset_path in targets:
            out_file = OUT_DIR / asset_path
            if out_file.exists():
                skipped += 1
                continue

            data = get_file(pak_path, asset_path)
            if not data:
                print(f"  [WARN] empty: {asset_path}")
                continue

            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(data)
            extracted += 1
            if extracted % 50 == 0:
                print(f"  ...{extracted} extracted so far")

    print(f"\nDone. {extracted} extracted, {skipped} already existed.")
    print(f"Output: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
