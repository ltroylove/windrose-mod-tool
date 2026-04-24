"""
Generates a custom game-tuning .pak mod from Game Tuning values.

Data sources (pre-extracted mod paks used as templates):
  tools/extracted/          MoreStacks 100x      → inventory item JSONs
  tools/extracted_mineral/  MoreMineralResources 2x → mineral loot tables + spawner JSONs
  tools/extracted_tree/     MoreTreeResources 2x → tree / herb loot table JSONs

Strategy:
  For each source JSON, determine its category, scale the relevant values so that
  vanilla × user_multiplier ≡ new_value, then pack everything with repak.

  stack sizes  : user sets absolute max-per-slot (IntVar)
  loot tables  : user sets a multiplier; vanilla = mod_value / ref_mult
  spawners     : user sets respawn hours directly + quantity multiplier
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).parent.parent / "tools"
REPAK     = TOOLS_DIR / "repak" / "repak.exe"

SRC_STACKS  = TOOLS_DIR / "extracted"           # MoreStacks 100x
SRC_MINERAL = TOOLS_DIR / "extracted_mineral"   # MoreMineralResources 2x
SRC_TREE    = TOOLS_DIR / "extracted_tree"      # MoreTreeResources 2x

STACK_REF_MULT = 100.0   # MoreStacks mod multiplier
LOOT_REF_MULT  = 2.0     # loot mods multiplier
SPAWN_QTY_REF  = 2.0     # spawner quantity reference multiplier


# ─── Stack size category rules ────────────────────────────────────────────────
# Checked in order; first match wins.  Pattern matched against full posix path.
STACK_RULES: list[tuple[str, list[str]]] = [
    ("stack_ammo",        ["/Ammo/", "Cannonball", "FirearmProjectile"]),
    ("stack_consumables", ["Potion_", "Elixir_", "Bandage", "_Recall_"]),
    ("stack_food",        ["/Food/", "SeaTrade"]),
    ("stack_alchemy",     ["/Alchemy/", "AlchemicalBase", "HealingHerbs", "Tannin",
                            "Saltpeter", "Bezoar", "Acid_T", "QuagmirePowder",
                            "UmbraEssence", "UndeadEssence", "HolyDust",
                            "VolcanicAsh", "Firefly", "Bromeliaceae", "_Aloe_",
                            "MistyOrchid", "TritonsTrumpet", "Lobstershroom"]),
    ("stack_ingots",      ["Ingot", "GoldNugget", "SilverIngot"]),
    ("stack_textiles",    ["Fabric", "FlaxFiber", "Leather", "_Rope_", "Rigging",
                            "Broadcloth", "Linen"]),
    ("stack_animal",      ["_Bones_", "_Feather_", "_Fat_T", "MeatBird", "MeatCrab",
                            "FishMeat", "_Meat_T", "_BoneMeal_", "BoarHead", "BoarTusk",
                            "GoatHorn", "CrocodileHead", "CrocodileTail", "CrocodileTears",
                            "WolfFang", "WolfHead", "EliteGoatHead", "CrabShell", "DodoEgg",
                            "DodoHead"]),
    ("stack_wood_products", ["Hardwood_T", "Mahogany", "EnchantedWood", "GhostWood",
                              "HolyWood", "WoodenBeam", "_Bark_T", "_Resin_T",
                              "TarredPlank", "PlanksWood", "SticksWood",
                              "VarnishedMahogany"]),
    ("stack_ore",         ["CopperOre", "_Iron_T", "_Sulfur_T", "Obsidian",
                            "_Stone_T", "_Coal_T", "_CopperOre_"]),
]
# Anything that doesn't match → stack_basic


def _stack_category(path_str: str) -> str:
    for cat, patterns in STACK_RULES:
        if any(p in path_str for p in patterns):
            return cat
    return "stack_basic"


# ─── Loot table category rules ────────────────────────────────────────────────
LOOT_RULES: list[tuple[str, list[str]]] = [
    ("loot_iron",           ["Mineral_Iron", "VolcaniIron"]),
    ("loot_sulfur",         ["Mineral_Sulfur"]),
    ("loot_stone",          ["HollowStone", "MiddleRock", "Mineral_Tuf"]),
    ("loot_ancient_debris", ["AncientMedalion", "AncientStatue", "BrokenStatue",
                              "RuinsDebris", "StatueCorrupted"]),
    ("loot_hardwood",       ["Mahogany", "BigTaxodium", "SmallTaxodium",
                              "DiviLog", "DiviStump"]),
    ("loot_plague_wood",    ["BurntTree", "Stump_Corrupted"]),
    ("loot_herbs",          ["_Fiber_", "DefaultFiber", "LimeTree_Seeds"]),
    ("loot_softwood",       ["DefaultWood", "DefaultStick", "Jungle_Log",
                              "Foliage_Stump_0", "Ashlands_Log", "LimeTree"]),
]


def _loot_category(stem: str) -> str | None:
    for cat, patterns in LOOT_RULES:
        if any(p in stem for p in patterns):
            return cat
    return None


# ─── Spawner category rules ───────────────────────────────────────────────────
SPAWNER_RULES: list[tuple[str, list[str]]] = [
    ("spawn_ancient_debris", ["BrokenStatue", "RootedMetall"]),
]


def _spawner_category(stem: str) -> str | None:
    for cat, patterns in SPAWNER_RULES:
        if any(p in stem for p in patterns):
            return cat
    return None


# ─── File processors ──────────────────────────────────────────────────────────

def _process_stack(
    src: Path, base: Path, staging: Path,
    values: dict, counts: dict,
) -> None:
    try:
        data = json.loads(src.read_bytes())
    except Exception:
        return

    gpp = data.get("InventoryItemGppData", {})
    if "MaxCountInSlot" not in gpp:
        return

    cat = _stack_category(src.as_posix())
    gpp["MaxCountInSlot"] = int(values.get(cat, 50))

    rel = src.relative_to(base)
    out = staging / "R5/Plugins/R5BusinessRules/Content/InventoryItems" / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent="\t"), encoding="utf-8")
    counts["stacks"] += 1


def _process_loot(
    src: Path, base: Path, staging: Path,
    values: dict, ref_mult: float, counts: dict,
) -> None:
    try:
        data = json.loads(src.read_bytes())
    except Exception:
        return

    native = str(data.get("NativeClass", "")) + str(data.get("$type", ""))
    if "R5BLLootParams" not in native:
        return

    cat = _loot_category(src.stem)
    if cat is None:
        return

    user_mult = float(values.get(cat, 1.0))
    scale = user_mult / ref_mult

    changed = False
    for entry in data.get("LootData", []):
        if isinstance(entry.get("Min"), (int, float)) and isinstance(entry.get("Max"), (int, float)):
            entry["Min"] = max(1, round(entry["Min"] * scale))
            entry["Max"] = max(1, round(entry["Max"] * scale))
            changed = True

    if not changed:
        return

    rel = src.relative_to(base)
    out = staging / "R5/Plugins/R5BusinessRules/Content/LootTables" / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent="\t"), encoding="utf-8")
    counts["loot"] += 1


def _process_spawner(
    src: Path, base: Path, staging: Path,
    values: dict, counts: dict,
) -> None:
    try:
        data = json.loads(src.read_bytes())
    except Exception:
        return

    if data.get("$type") != "R5GameplaySpawnerParams":
        return

    cat = _spawner_category(src.stem)
    if cat is None:
        return

    h_key   = f"{cat}_h"
    qty_key = f"{cat}_qty"
    hours   = float(values.get(h_key, 6.0))
    qty_m   = float(values.get(qty_key, 1.0))
    qty_scale = qty_m / SPAWN_QTY_REF

    ri = data.get("RespawnInterval")
    if isinstance(ri, dict):
        secs = int(hours * 3600)
        ri["Min"] = secs
        ri["Max"] = secs

    for variant in data.get("Variants", []):
        for col in variant.get("Collection", []):
            amt = col.get("Amount", {})
            if isinstance(amt.get("Min"), (int, float)):
                amt["Min"] = max(1, round(amt["Min"] * qty_scale))
                amt["Max"] = max(1, round(amt["Max"] * qty_scale))

    rel = src.relative_to(base)
    out = staging / "R5/Content/Gameplay/Actor/SpawnPoints" / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent="\t"), encoding="utf-8")
    counts["spawners"] += 1


# ─── repak packing ────────────────────────────────────────────────────────────

def _pack(pak_name: str, staging: Path, output_dir: Path) -> Path:
    """
    Pack <staging>/<pak_name>/ into <output_dir>/<pak_name>.pak using repak.

    repak's output-directory argument fails on Windows, so we pack next to the
    input dir (inside the temp tree) and then move the result to output_dir.
    """
    input_dir = staging / pak_name
    tmp_pak   = staging / f"{pak_name}.pak"
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [str(REPAK), "pack", "--version", "V8B", str(input_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if not tmp_pak.exists():
        raise RuntimeError(
            f"repak pack failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    final = output_dir / f"{pak_name}.pak"
    shutil.move(str(tmp_pak), str(final))
    return final


# ─── Public API ───────────────────────────────────────────────────────────────

def check_sources() -> list[str]:
    """Return a list of missing source directories (empty = all good)."""
    missing = []
    for label, path in [
        ("MoreStacks extraction",         SRC_STACKS),
        ("MoreMineralResources extraction", SRC_MINERAL),
        ("MoreTreeResources extraction",    SRC_TREE),
    ]:
        if not path.exists():
            missing.append(f"{label} ({path})")
    return missing


def generate(values: dict, pak_name: str, output_dir: Path) -> dict:
    """
    Generate a .pak file from the given tuning values.

    pak_name   – filename stem, e.g. "MyGameTuning_P"
    output_dir – directory to write the final .pak

    Returns a summary dict: {"stacks": N, "loot": N, "spawners": N, "path": Path}
    """
    if not REPAK.exists():
        raise FileNotFoundError(f"repak.exe not found at {REPAK}")

    missing = check_sources()
    if missing:
        raise FileNotFoundError(
            "Missing extracted mod data:\n" + "\n".join(f"  • {m}" for m in missing)
        )

    counts: dict = {"stacks": 0, "loot": 0, "spawners": 0}

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)
        root    = staging / pak_name   # repak will name the pak after this folder

        # 1 ── Stack sizes
        item_base = SRC_STACKS / "R5/Plugins/R5BusinessRules/Content/InventoryItems"
        if item_base.exists():
            for p in item_base.rglob("*.json"):
                _process_stack(p, item_base, root, values, counts)

        # 2 ── Mineral loot tables
        mineral_loot = SRC_MINERAL / "R5/Plugins/R5BusinessRules/Content/LootTables"
        if mineral_loot.exists():
            for p in mineral_loot.rglob("*.json"):
                _process_loot(p, mineral_loot, root, values, LOOT_REF_MULT, counts)

        # 3 ── Tree / herb loot tables
        tree_loot = SRC_TREE / "R5/Plugins/R5BusinessRules/Content/LootTables"
        if tree_loot.exists():
            for p in tree_loot.rglob("*.json"):
                _process_loot(p, tree_loot, root, values, LOOT_REF_MULT, counts)

        # 4 ── Spawners (mineral mod only; tree mod has no spawner JSONs)
        spawner_base = SRC_MINERAL / "R5/Content/Gameplay/Actor/SpawnPoints"
        if spawner_base.exists():
            for p in spawner_base.rglob("*.json"):
                _process_spawner(p, spawner_base, root, values, counts)

        total = counts["stacks"] + counts["loot"] + counts["spawners"]
        if total == 0:
            raise RuntimeError("No files were staged — check extraction directories.")

        pak_path = _pack(pak_name, staging, output_dir)

    counts["path"] = pak_path
    return counts
