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

Strategy:
  For each source JSON, determine its category, scale the relevant values so that
  vanilla × user_multiplier ≡ new_value, then pack everything with repak.

  stack sizes     : user sets absolute max-per-slot (IntVar)
  loot tables     : user sets a multiplier; vanilla = mod_value / ref_mult
  animals         : user sets a multiplier; vanilla extracted directly, ref_mult = 1.0
  backpack slots  : user sets a multiplier; vanilla = mod_value / BACKPACK_REF_MULT
  fast travel     : user sets absolute max bell count
  lantern         : user sets duration in minutes; both item MaxValue and recipe modifier updated
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# When packaged with PyInstaller the source files live inside a temp _MEI* dir
# (sys._MEIPASS).  At runtime the tools/ bundle is extracted there, so we
# resolve against _MEIPASS when frozen and against the repo root otherwise.
TOOLS_DIR  = (Path(sys._MEIPASS) / "tools") if getattr(sys, "frozen", False) else Path(__file__).parent.parent / "tools"
REPAK      = TOOLS_DIR / "repak" / "repak.exe"

SRC_STACKS      = TOOLS_DIR / "extracted"            # MoreStacks 100x
SRC_MINERAL     = TOOLS_DIR / "extracted_mineral"    # MoreMineralResources 2x
SRC_TREE        = TOOLS_DIR / "extracted_tree"       # MoreTreeResources 2x
SRC_BACKPACK    = TOOLS_DIR / "extracted_backpack"   # MoreBackpackSlots 3x
SRC_FASTTRAVEL  = TOOLS_DIR / "extracted_fasttravel" # FastTravelPlus 50
SRC_LANTERN     = TOOLS_DIR / "extracted_lantern"    # BetterLanternLonger 2x
SRC_VANILLA     = TOOLS_DIR / "extracted_vanilla"    # Direct from game paks (copper + animals)
SRC_ALLLOOT     = TOOLS_DIR / "extracted_allloot"    # 10x All Loot mod (food plants, crops, fishing, scrap)

STACK_REF_MULT    = 100.0   # MoreStacks mod multiplier
LOOT_REF_MULT     = 2.0     # loot mods multiplier (mineral + tree)
ALLLOOT_REF_MULT  = 10.0    # All Loot mod multiplier (food plants, crops, fishing, scrap)
BACKPACK_REF_MULT = 3.0     # MoreBackpackSlots mod multiplier

LANTERN_VANILLA_SECONDS = 900   # confirmed from MoreStacks extraction (MaxValue untouched)
LANTERN_VANILLA_MINUTES = 15
FASTTRAVEL_VANILLA_BELLS = 10

# Vanilla stack-size per category (keep in sync with PRESETS["Vanilla"] in create_tab.py).
# If a user value matches its vanilla, that category is skipped — no file written, so the
# game uses its own vanilla value. Avoids unexpected side effects from generating no-op mods.
VANILLA_STACK_VALUES: dict[str, int] = {
    "stack_basic": 50, "stack_wood_products": 30, "stack_ore": 50, "stack_ingots": 30,
    "stack_textiles": 30, "stack_animal": 30, "stack_food": 20, "stack_alchemy": 20,
    "stack_ammo": 200, "stack_consumables": 10,
}

# Lantern item is handled entirely by _process_lantern(); skip it in _process_stack()
_STACK_SKIP_STEMS = {"DA_CID_Misc_Lantern_L1_T01"}

# Loot category sets used to route JSON tables to the right pak group.
# Tree-chop yield (softwood/hardwood/plague_wood) and dig-volume yield (copper/iron)
# are controlled by binary assets, not these JSON loot tables — so those categories
# are intentionally absent and their incoming loot tables are left vanilla.
_TREE_LOOT_CATS    = {"loot_herbs"}
_MINERAL_LOOT_CATS = {
    "loot_sulfur", "loot_stone", "loot_clay",
    "loot_soil", "loot_obsidian", "loot_salt",
}


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
    # Note: softwood/hardwood/plague_wood (tree chop) and copper/iron (dig volume)
    # are intentionally absent — their yield is controlled by binary DA_Segment /
    # DA_DigVolume assets, not JSON loot tables. Loot tables matching those
    # patterns get no category, are skipped, and remain vanilla.
    ("loot_sulfur",         ["Mineral_Sulfur"]),
    ("loot_stone",          ["HollowStone", "MiddleRock", "Mineral_Tuf", "LavaTree"]),
    ("loot_clay",           ["Mineral_Clay", "GreyClay", "MedicinalClay"]),
    ("loot_soil",           ["Mineral_Soil", "CorruptedSoil"]),
    ("loot_obsidian",       ["Mineral_Obsidian"]),
    ("loot_salt",           ["Mineral_Salt"]),
    ("loot_herbs",          ["_Fiber_", "DefaultFiber", "LimeTree_Seeds",
                              "Bush_AloeFresh", "Bush_Flax", "Bush_Rosella", "Bush_Bromelia"]),
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
    user_val = int(values.get(cat, 50))
    if user_val == VANILLA_STACK_VALUES.get(cat):
        return  # vanilla — leave the game's value alone
    gpp["MaxCountInSlot"] = user_val

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
    if user_mult == 1.0:
        return  # vanilla — don't write (avoids scale=1/ref_mult shrinking drops)
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
    if user_mult == 1.0:
        return  # vanilla — leave the game's tables alone

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


def _process_backpack(
    src: Path, base: Path, staging: Path,
    user_mult: float, counts: dict,
) -> None:
    if user_mult == 1.0:
        return  # vanilla — leave the game's backpack slots alone

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

    max_bells = int(values.get("fasttravel_bells", FASTTRAVEL_VANILLA_BELLS))
    if max_bells == FASTTRAVEL_VANILLA_BELLS:
        return  # vanilla — leave the game's bell limit alone
    for entry in data.get("AmountLimits", []):
        if isinstance(entry.get("MaxAmount"), (int, float)):
            entry["MaxAmount"] = max_bells

    out = staging / "R5/Content/Gameplay/BuildingLimits/DA_BuildLimits_FastTravel.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent="\t"), encoding="utf-8")
    counts["build_limits"] = 1


def _process_lantern(staging: Path, values: dict, counts: dict) -> None:
    duration_min = float(values.get("lantern_duration_min", LANTERN_VANILLA_MINUTES))
    if duration_min == LANTERN_VANILLA_MINUTES:
        return  # vanilla — leave the game's lantern duration alone
    duration_sec = round(duration_min * 60)

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
    ]:
        if not path.exists():
            missing.append(f"{label} ({path})")
    return missing


def generate(values: dict, pak_name: str, output_dir: Path) -> dict:
    """
    Generate game-tuning paks mirroring the community mod structure:

      {base}TreeOther_P.pak       – herb / plant patch loot table JSONs
      {base}MineralOther_P.pak    – mineral loot table JSONs (sulfur, stone, clay, soil, obsidian, salt)
      {base}Other_P.pak           – stack sizes, backpack, lantern, fast travel, animals, food/crops/fishing/scrap

    pak_name   – filename stem, e.g. "MyGameTuning_P"
    output_dir – directory to write all generated files

    Returns a summary dict with counts per category and "path" set to the Other pak.
    """
    if not REPAK.exists():
        raise FileNotFoundError(f"repak.exe not found at {REPAK}")

    missing = check_sources()
    if missing:
        raise FileNotFoundError(
            "Missing extracted mod data:\n" + "\n".join(f"  • {m}" for m in missing)
        )

    # Clean output dir of stale pak/ucas/utoc files before generating fresh ones
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.iterdir():
        if stale.suffix in (".pak", ".ucas", ".utoc"):
            stale.unlink()

    # Derive base name without trailing _P suffix
    base = pak_name[:-2] if pak_name.endswith("_P") else pak_name

    TREE_OTHER_NAME    = f"{base}TreeOther_P"
    MINERAL_OTHER_NAME = f"{base}MineralOther_P"
    OTHER_NAME         = f"{base}Other_P"

    counts: dict = {
        "stacks": 0, "loot": 0,
        "backpack": 0, "build_limits": 0,
        "lantern_item": 0, "lantern_recipe": 0,
    }

    enabled = values.get("_enabled", {})
    stack_on      = enabled.get("Stack Sizes",     True)
    loot_on       = enabled.get("Loot Drops",      True)
    backpack_on   = enabled.get("Backpack Slots",  True)
    buildings_on  = enabled.get("Building Limits", True)
    consumables_on = enabled.get("Consumables",    True)

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)

        root_tree    = staging / TREE_OTHER_NAME    # tree + herb loot JSONs
        root_mineral = staging / MINERAL_OTHER_NAME # mineral loot + spawner JSONs
        root_other   = staging / OTHER_NAME         # stacks, backpack, lantern, etc.

        # 1 ── Stack sizes → other
        if stack_on:
            item_base = SRC_STACKS / "R5/Plugins/R5BusinessRules/Content/InventoryItems"
            if item_base.exists():
                for p in item_base.rglob("*.json"):
                    _process_stack(p, item_base, root_other, values, counts)

        # 2 ── Mineral loot tables → mineral
        if loot_on:
            mineral_loot = SRC_MINERAL / "R5/Plugins/R5BusinessRules/Content/LootTables"
            if mineral_loot.exists():
                for p in mineral_loot.rglob("*.json"):
                    _process_loot(p, mineral_loot, root_mineral, values, LOOT_REF_MULT, counts)

        # 3 ── Tree / herb loot tables → tree
        if loot_on:
            tree_loot = SRC_TREE / "R5/Plugins/R5BusinessRules/Content/LootTables"
            if tree_loot.exists():
                for p in tree_loot.rglob("*.json"):
                    _process_loot(p, tree_loot, root_tree, values, LOOT_REF_MULT, counts)

        # 4 ── Backpack slots → other
        if backpack_on:
            backpack_base = SRC_BACKPACK / "R5/Content/Gameplay/ItemsLogic/Backpack"
            if backpack_base.exists():
                user_mult = float(values.get("backpack_slots", 1.0))
                for p in backpack_base.rglob("*.json"):
                    _process_backpack(p, backpack_base, root_other, user_mult, counts)

        # 6 ── Fast travel bell limit → other
        if buildings_on:
            ft_src = SRC_FASTTRAVEL / "R5/Content/Gameplay/BuildingLimits/DA_BuildLimits_FastTravel.json"
            if ft_src.exists():
                _process_build_limits(ft_src, root_other, values, counts)

        # 7 ── Lantern burn duration → other
        if consumables_on:
            _process_lantern(root_other, values, counts)

        # 8 ── Vanilla-only mineral loot (copper + lava tree) → mineral
        vanilla_loot_base = SRC_VANILLA / "R5/Plugins/R5BusinessRules/Content/LootTables"
        vanilla_foliage = vanilla_loot_base / "Foliage"
        if loot_on and vanilla_foliage.exists():
            for p in vanilla_foliage.glob("DA_LT_Mineral_Copper*.json"):
                _process_loot(p, vanilla_loot_base, root_mineral, values, 1.0, counts)
            for p in vanilla_foliage.glob("DA_LT_Mineral_LavaTree*.json"):
                _process_loot(p, vanilla_loot_base, root_mineral, values, 1.0, counts)

        # 9 ── Animal drop tables → other
        if loot_on:
            vanilla_mob_rss = vanilla_loot_base / "Mobs" / "Rss"
            if vanilla_mob_rss.exists():
                for p in vanilla_mob_rss.glob("*.json"):
                    _process_animal_loot(p, vanilla_loot_base, root_other, values, counts)

        # 10 ── All Loot mod sources: softwood/herbs → tree; food/crops/fishing/scrap → other
        if loot_on:
            allloot_loot_base = SRC_ALLLOOT / "R5/Plugins/R5BusinessRules/Content/LootTables"
            if allloot_loot_base.exists():
                for p in allloot_loot_base.rglob("*.json"):
                    cat = _loot_category(p.stem)
                    if cat in _TREE_LOOT_CATS:
                        _process_loot(p, allloot_loot_base, root_tree, values, ALLLOOT_REF_MULT, counts)
                    elif cat in {"loot_food_plants", "loot_crops", "loot_fishing", "loot_scrap"}:
                        _process_loot(p, allloot_loot_base, root_other, values, ALLLOOT_REF_MULT, counts)

        # 11 ── Vanilla foliage tables not covered by reference mod → route by category
        if loot_on:
            ref_tree_stems = {
                p.stem
                for p in (SRC_TREE / "R5/Plugins/R5BusinessRules/Content/LootTables/Foliage").glob("*.json")
            } if (SRC_TREE / "R5/Plugins/R5BusinessRules/Content/LootTables/Foliage").exists() else set()
            if vanilla_foliage.exists():
                for p in vanilla_foliage.glob("DA_LT_Foliage_*.json"):
                    if p.stem not in ref_tree_stems:
                        cat = _loot_category(p.stem)
                        if cat in _TREE_LOOT_CATS:
                            _process_loot(p, vanilla_loot_base, root_tree, values, 1.0, counts)
                        elif cat in _MINERAL_LOOT_CATS:
                            _process_loot(p, vanilla_loot_base, root_mineral, values, 1.0, counts)

        total = sum(v for k, v in counts.items() if k not in ("path",))
        if total == 0:
            raise RuntimeError(
                "All values match vanilla — nothing to generate. "
                "Adjust at least one slider away from its vanilla setting."
            )

        # Pack each non-empty JSON group
        if root_tree.exists():
            _pack(TREE_OTHER_NAME, staging, output_dir)
        if root_mineral.exists():
            _pack(MINERAL_OTHER_NAME, staging, output_dir)
        other_pak = _pack(OTHER_NAME, staging, output_dir)

    counts["path"] = other_pak
    return counts
