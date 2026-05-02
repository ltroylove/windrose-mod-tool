"""
Generates a custom game-tuning .pak mod from Game Tuning values.

Data sources:
  tools/extracted/            MoreStacks 100x           → inventory item JSONs
  tools/extracted_mineral/    MoreMineralResources 2x   → mineral loot tables + spawner JSONs
  tools/extracted_tree/       MoreTreeResources 2x      → tree / herb loot table JSONs
  tools/extracted_backpack/   MoreBackpackSlots 3x      → backpack slot JSONs
  tools/extracted_fasttravel/ FastTravelPlus 50         → fast travel building limits JSON
  tools/extracted_lantern/    BetterLanternLonger 2x    → lantern refuel recipe JSON
  tools/extracted_vanilla/    Direct from game paks     → copper loot + animal drop tables
  tools/extracted_segments/   Direct from game paks     → DA_Segment_*.uasset/.uexp (tree chop amounts)

Strategy:
  For each source JSON, determine its category, scale the relevant values so that
  vanilla × user_multiplier ≡ new_value, then pack everything with repak.

  stack sizes     : user sets absolute max-per-slot (IntVar)
  loot tables     : user sets a multiplier; vanilla = mod_value / ref_mult
  copper/animals  : user sets a multiplier; vanilla extracted directly, ref_mult = 1.0
  spawners        : user sets respawn hours directly + quantity multiplier
  backpack slots  : user sets a multiplier; vanilla = mod_value / BACKPACK_REF_MULT
  fast travel     : user sets absolute max bell count
  lantern         : user sets duration in minutes; both item MaxValue and recipe modifier updated
  tree segments   : user sets a multiplier; vanilla DA_Segment_*.uexp modified in-place,
                    repacked to I/O Store (.pak+.ucas+.utoc) via retoc
"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

# When packaged with PyInstaller the source files live inside a temp _MEI* dir
# (sys._MEIPASS).  At runtime the tools/ bundle is extracted there, so we
# resolve against _MEIPASS when frozen and against the repo root otherwise.
TOOLS_DIR = (Path(sys._MEIPASS) / "tools") if getattr(sys, "frozen", False) else Path(__file__).parent.parent / "tools"
REPAK     = TOOLS_DIR / "repak" / "repak.exe"
RETOC     = TOOLS_DIR / "retoc" / "retoc.exe"

SRC_STACKS      = TOOLS_DIR / "extracted"            # MoreStacks 100x
SRC_MINERAL     = TOOLS_DIR / "extracted_mineral"    # MoreMineralResources 2x
SRC_TREE        = TOOLS_DIR / "extracted_tree"       # MoreTreeResources 2x
SRC_BACKPACK    = TOOLS_DIR / "extracted_backpack"   # MoreBackpackSlots 3x
SRC_FASTTRAVEL  = TOOLS_DIR / "extracted_fasttravel" # FastTravelPlus 50
SRC_LANTERN     = TOOLS_DIR / "extracted_lantern"    # BetterLanternLonger 2x
SRC_VANILLA     = TOOLS_DIR / "extracted_vanilla"    # Direct from game paks (copper + animals)
SRC_ALLLOOT     = TOOLS_DIR / "extracted_allloot"    # 10x All Loot mod (food plants, crops, fishing, scrap)
SRC_SEGMENTS    = TOOLS_DIR / "extracted_segments"   # DA_Segment_*.uasset/.uexp (tree chop amounts)

# Vanilla amount per chop-group as extracted from the current game pak.
# All 41 DA_Segment_* files use this same value for min and max.
SEGMENT_VANILLA_AMOUNT = 1.65
# The 0.75 double that immediately follows each min/max pair in the uexp —
# used as a reliable anchor to locate the amount fields.
_SEGMENT_PROB_BYTES = struct.pack("<d", 0.75)

STACK_REF_MULT    = 100.0   # MoreStacks mod multiplier
LOOT_REF_MULT     = 2.0     # loot mods multiplier (mineral + tree)
ALLLOOT_REF_MULT  = 10.0    # All Loot mod multiplier (food plants, crops, fishing, scrap)
SPAWN_QTY_REF     = 2.0     # spawner quantity reference multiplier
BACKPACK_REF_MULT = 3.0     # MoreBackpackSlots mod multiplier

LANTERN_VANILLA_SECONDS = 900   # confirmed from MoreStacks extraction (MaxValue untouched)
# Lantern item is handled entirely by _process_lantern(); skip it in _process_stack()
_STACK_SKIP_STEMS = {"DA_CID_Misc_Lantern_L1_T01"}


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
    ("loot_copper",         ["Mineral_Copper"]),
    ("loot_iron",           ["Mineral_Iron", "VolcaniIron"]),
    ("loot_sulfur",         ["Mineral_Sulfur"]),
    ("loot_stone",          ["HollowStone", "MiddleRock", "Mineral_Tuf", "LavaTree"]),
    ("loot_clay",           ["Mineral_Clay", "GreyClay", "MedicinalClay"]),
    ("loot_soil",           ["Mineral_Soil", "CorruptedSoil"]),
    ("loot_obsidian",       ["Mineral_Obsidian"]),
    ("loot_salt",           ["Mineral_Salt"]),
    ("loot_ancient_debris", ["AncientMedalion", "AncientStatue", "BrokenStatue",
                              "RuinsDebris", "StatueCorrupted"]),
    ("loot_hardwood",       ["Mahogany", "BigTaxodium", "SmallTaxodium",
                              "DiviLog", "DiviStump"]),
    ("loot_plague_wood",    ["BurntTree", "Stump_Corrupted"]),
    ("loot_herbs",          ["_Fiber_", "DefaultFiber", "LimeTree_Seeds",
                              "Bush_AloeFresh", "Bush_Flax", "Bush_Rosella", "Bush_Bromelia"]),
    ("loot_softwood",       ["DefaultWood", "DefaultStick", "Jungle_Log",
                              "Foliage_Stump_0", "Ashlands_Log", "LimeTree",
                              "Frailejon", "Bush_Yucca"]),
    ("loot_food_plants",    ["Bush_Banana", "Bush_Corn", "Bush_Tomato", "Bush_Pepper",
                              "Bush_Icaco", "Bush_Cocoloba", "Foliage_Leek",
                              "Foliage_Pineapple", "Foliage_Potato", "Foliage_BlackBean"]),
    ("loot_crops",          ["Foliage_Crop_"]),
    ("loot_fishing",        ["FishData_", "Butchering_"]),
    ("loot_scrap",          ["ScrapsNode_", "Mineral_Shipwreck_"]),
]

# Wildlife mob names whose Rss/ leaf tables make up animal drops.
# Human enemies (BlackBeard, Brit, Skeleton, etc.) are excluded.
_ANIMAL_MOB_NAMES = {
    "Boar", "BoarF", "BoarMega",
    "Dodo", "DodoF",
    "Crab", "DrownedCrab",
    "Wolf", "AlphaWolf",
    "Crocodile", "CorruptedCrocodile",
}


def _is_animal_mob(stem: str) -> bool:
    """Return True if this Mobs/Rss/ stem belongs to a wildlife animal."""
    # stem format: DA_LT_Mob_<AnimalName>_<DropType>[_<variant>]
    parts = stem.split("_")
    return len(parts) >= 4 and parts[3] in _ANIMAL_MOB_NAMES


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
    if src.stem in _STACK_SKIP_STEMS:
        return  # handled separately by _process_lantern()

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


def _process_animal_loot(
    src: Path, base: Path, staging: Path,
    values: dict, counts: dict,
) -> None:
    """Scale a Mobs/Rss/ leaf table for a wildlife animal using vanilla values directly."""
    if not _is_animal_mob(src.stem):
        return

    try:
        data = json.loads(src.read_bytes())
    except Exception:
        return

    native = str(data.get("NativeClass", "")) + str(data.get("$type", ""))
    if "R5BLLootParams" not in native:
        return

    user_mult = float(values.get("loot_animals", 1.0))

    changed = False
    for entry in data.get("LootData", []):
        if isinstance(entry.get("Min"), (int, float)) and isinstance(entry.get("Max"), (int, float)):
            entry["Min"] = max(1, round(entry["Min"] * user_mult))
            entry["Max"] = max(1, round(entry["Max"] * user_mult))
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


def _process_backpack(
    src: Path, base: Path, staging: Path,
    user_mult: float, counts: dict,
) -> None:
    try:
        data = json.loads(src.read_bytes())
    except Exception:
        return

    if data.get("$type") != "R5BLSlotCountModifierParams":
        return

    slots_data = data.get("InventorySlotsData", {})
    ref_val = slots_data.get("CountSlots")
    if not isinstance(ref_val, (int, float)):
        return

    vanilla = ref_val / BACKPACK_REF_MULT
    slots_data["CountSlots"] = max(1, round(vanilla * user_mult))

    rel = src.relative_to(base)
    out = staging / "R5/Content/Gameplay/ItemsLogic/Backpack" / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent="\t"), encoding="utf-8")
    counts["backpack"] += 1


def _process_build_limits(
    src: Path, staging: Path,
    values: dict, counts: dict,
) -> None:
    try:
        data = json.loads(src.read_bytes())
    except Exception:
        return

    if data.get("$type") != "R5BuildingLimits":
        return

    max_bells = int(values.get("fasttravel_bells", 10))
    for entry in data.get("AmountLimits", []):
        if isinstance(entry.get("MaxAmount"), (int, float)):
            entry["MaxAmount"] = max_bells

    out = staging / "R5/Content/Gameplay/BuildingLimits/DA_BuildLimits_FastTravel.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent="\t"), encoding="utf-8")
    counts["build_limits"] = 1


def _process_lantern(staging: Path, values: dict, counts: dict) -> None:
    duration_sec = round(float(values.get("lantern_duration_min", 15.0)) * 60)

    # Item definition — sourced from MoreStacks extraction (vanilla MaxValue=900 confirmed)
    item_src = SRC_STACKS / "R5/Plugins/R5BusinessRules/Content/InventoryItems/Consumables/Misc/DA_CID_Misc_Lantern_L1_T01.json"
    if item_src.exists():
        try:
            data = json.loads(item_src.read_bytes())
            for attr in data.get("InventoryItemGppData", {}).get("Attributes", []):
                if attr.get("Tag", {}).get("TagName") == "Inventory.Item.Attribute.Counter":
                    attr["MaxValue"] = duration_sec
            out = staging / "R5/Plugins/R5BusinessRules/Content/InventoryItems/Consumables/Misc/DA_CID_Misc_Lantern_L1_T01.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(data, indent="\t"), encoding="utf-8")
            counts["lantern_item"] = 1
        except Exception:
            pass

    # Refuel recipe — sourced from lantern mod extraction
    recipe_src = SRC_LANTERN / "R5/Plugins/R5BusinessRules/Content/Recipes/Economy/Items/Consumables/Misc/DA_RD_CID_Misc_Lantern_L4_T01_fromL1.json"
    if recipe_src.exists():
        try:
            data = json.loads(recipe_src.read_bytes())
            data["ResultAttributeModifier"]["AttributeModifierData"]["AttributesModifier"] = duration_sec
            out = staging / "R5/Plugins/R5BusinessRules/Content/Recipes/Economy/Items/Consumables/Misc/DA_RD_CID_Misc_Lantern_L4_T01_fromL1.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(data, indent="\t"), encoding="utf-8")
            counts["lantern_recipe"] = 1
        except Exception:
            pass


# ─── Tree segment binary modifier ────────────────────────────────────────────

def _process_segment_uexp(src: Path, dest: Path, user_mult: float) -> int:
    """
    Copy src .uexp to dest with all spawn-group Amount min/max values scaled by
    user_mult.  Returns number of groups modified (0 = nothing changed, file not written).
    """
    data = bytearray(src.read_bytes())
    new_val = SEGMENT_VANILLA_AMOUNT * user_mult
    modified = 0
    pos = 0
    while True:
        idx = data.find(_SEGMENT_PROB_BYTES, pos)
        if idx < 0:
            break
        if idx >= 16:
            mn = struct.unpack_from("<d", data, idx - 16)[0]
            mx = struct.unpack_from("<d", data, idx - 8)[0]
            if 0 < mn <= 1000 and 0 < mx <= 1000:
                struct.pack_into("<d", data, idx - 16, new_val)
                struct.pack_into("<d", data, idx - 8,  new_val)
                modified += 1
        pos = idx + 1

    if modified:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return modified


def _pack_iostore(staging_legacy: Path, output_base: Path) -> tuple[Path, Path, Path]:
    """
    Convert a legacy (.uasset/.uexp) staging tree to an I/O Store container
    (.pak + .ucas + .utoc) using retoc.  output_base is the full path stem
    (e.g. /some/dir/MyMod_Segments_P).  Returns (pak, ucas, utoc) paths.
    """
    utoc_out = output_base.with_suffix(".utoc")
    cmd = [
        str(RETOC), "to-zen",
        "--version", "UE5_6",
        str(staging_legacy),
        str(utoc_out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    pak  = output_base.with_suffix(".pak")
    ucas = output_base.with_suffix(".ucas")
    utoc = output_base.with_suffix(".utoc")

    if not ucas.exists():
        raise RuntimeError(
            f"retoc to-zen failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return pak, ucas, utoc


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
        ("MoreStacks extraction",          SRC_STACKS),
        ("MoreMineralResources extraction", SRC_MINERAL),
        ("MoreTreeResources extraction",    SRC_TREE),
        ("Backpack slots extraction",       SRC_BACKPACK),
        ("Fast travel limits extraction",   SRC_FASTTRAVEL),
        ("Lantern recipe extraction",       SRC_LANTERN),
        ("Vanilla game extraction",        SRC_VANILLA),
        ("All Loot mod extraction",        SRC_ALLLOOT),
        ("Tree segment extraction",        SRC_SEGMENTS),
    ]:
        if not path.exists():
            missing.append(f"{label} ({path})")
    return missing


def generate(values: dict, pak_name: str, output_dir: Path) -> dict:
    """
    Generate a .pak file from the given tuning values.

    pak_name   – filename stem, e.g. "MyGameTuning_P"
    output_dir – directory to write the final .pak

    Returns a summary dict: {"stacks": N, "loot": N, "spawners": N, "segments": N, "path": Path}
    """
    if not REPAK.exists():
        raise FileNotFoundError(f"repak.exe not found at {REPAK}")
    if not RETOC.exists():
        raise FileNotFoundError(f"retoc.exe not found at {RETOC}")

    missing = check_sources()
    if missing:
        raise FileNotFoundError(
            "Missing extracted mod data:\n" + "\n".join(f"  • {m}" for m in missing)
        )

    counts: dict = {
        "stacks": 0, "loot": 0, "spawners": 0,
        "backpack": 0, "build_limits": 0,
        "lantern_item": 0, "lantern_recipe": 0,
        "segments": 0,
    }

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

        # 5 ── Backpack slots
        backpack_base = SRC_BACKPACK / "R5/Content/Gameplay/ItemsLogic/Backpack"
        if backpack_base.exists():
            user_mult = float(values.get("backpack_slots", 1.0))
            for p in backpack_base.rglob("*.json"):
                _process_backpack(p, backpack_base, root, user_mult, counts)

        # 6 ── Fast travel bell limit
        ft_src = SRC_FASTTRAVEL / "R5/Content/Gameplay/BuildingLimits/DA_BuildLimits_FastTravel.json"
        if ft_src.exists():
            _process_build_limits(ft_src, root, values, counts)

        # 7 ── Lantern burn duration
        _process_lantern(root, values, counts)

        # 8 ── Vanilla-only mineral loot (copper + lava tree — not in any reference mod)
        vanilla_loot_base = SRC_VANILLA / "R5/Plugins/R5BusinessRules/Content/LootTables"
        vanilla_foliage = vanilla_loot_base / "Foliage"
        if vanilla_foliage.exists():
            for p in vanilla_foliage.glob("DA_LT_Mineral_Copper*.json"):
                _process_loot(p, vanilla_loot_base, root, values, 1.0, counts)
            for p in vanilla_foliage.glob("DA_LT_Mineral_LavaTree*.json"):
                _process_loot(p, vanilla_loot_base, root, values, 1.0, counts)

        # 9 ── Animal drop tables (vanilla source, ref_mult=1.0)
        vanilla_mob_rss = vanilla_loot_base / "Mobs" / "Rss"
        if vanilla_mob_rss.exists():
            for p in vanilla_mob_rss.glob("*.json"):
                _process_animal_loot(p, vanilla_loot_base, root, values, counts)

        # 10 ── Food plants, crops, fishing, scrap (all-loot mod, ref_mult=10.0)
        allloot_loot_base = SRC_ALLLOOT / "R5/Plugins/R5BusinessRules/Content/LootTables"
        if allloot_loot_base.exists():
            for p in allloot_loot_base.rglob("*.json"):
                if _loot_category(p.stem) in {
                    "loot_food_plants", "loot_crops", "loot_fishing", "loot_scrap",
                    "loot_herbs", "loot_softwood",
                }:
                    _process_loot(p, allloot_loot_base, root, values, ALLLOOT_REF_MULT, counts)

        # 11 ── Vanilla foliage tables not covered by reference mod (ref_mult=1.0)
        # Catches any tree/shrub loot tables the MoreTreeResources mod packaged in
        # I/O Store format (unreadable by repak) — e.g. coastal palms, yucca, etc.
        ref_tree_stems = {
            p.stem
            for p in (SRC_TREE / "R5/Plugins/R5BusinessRules/Content/LootTables/Foliage").glob("*.json")
        } if (SRC_TREE / "R5/Plugins/R5BusinessRules/Content/LootTables/Foliage").exists() else set()
        if vanilla_foliage.exists():
            for p in vanilla_foliage.glob("DA_LT_Foliage_*.json"):
                if p.stem not in ref_tree_stems and _loot_category(p.stem) is not None:
                    _process_loot(p, vanilla_loot_base, root, values, 1.0, counts)

        # 12 ── Tree segment binary params (I/O Store .ucas/.utoc output)
        # Controls how much wood each tree segment drops when chopped.
        # Uses vanilla .uasset/.uexp as source; modifies Amount min/max in .uexp;
        # converts back to Zen format via retoc.
        seg_mult = float(values.get("loot_softwood", 1.0))
        if SRC_SEGMENTS.exists() and seg_mult != 1.0:
            seg_src_base = SRC_SEGMENTS / "Content/Gameplay/Foliage/SegmentTrees/ParamsSegmentTrees"
            seg_staging  = staging / "segments_legacy"
            for uasset in seg_src_base.glob("*.uasset"):
                uexp = uasset.with_suffix(".uexp")
                if not uexp.exists():
                    continue
                rel = uasset.relative_to(SRC_SEGMENTS)
                dest_uexp   = seg_staging / rel.parent / uexp.name
                dest_uasset = seg_staging / rel.parent / uasset.name
                dest_uasset.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(uasset, dest_uasset)
                n = _process_segment_uexp(uexp, dest_uexp, seg_mult)
                counts["segments"] += n

            if counts["segments"] > 0:
                seg_pak_base = staging / f"{pak_name}_Segments"
                _pack_iostore(seg_staging, seg_pak_base)

        total = sum(v for k, v in counts.items() if k not in ("path",))
        if total == 0:
            raise RuntimeError("No files were staged — check extraction directories.")

        pak_path = _pack(pak_name, staging, output_dir)

        # Move I/O Store segment files to output_dir alongside the main pak
        if counts["segments"] > 0:
            for ext in (".pak", ".ucas", ".utoc"):
                src_file = staging / f"{pak_name}_Segments{ext}"
                if src_file.exists():
                    shutil.move(str(src_file), str(output_dir / src_file.name))

    counts["path"] = pak_path
    return counts
