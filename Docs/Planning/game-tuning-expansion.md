# Game Tuning Expansion — Implementation Plan

**Date:** 2026-04-24  
**Branch:** development  
**Scope:** Five new feature areas for the Game Tuning tab, discovered by inspecting community mod pak files.

---

## Executive Summary

The current Game Tuning tab supports Stack Sizes, Loot Drops, and Spawners. This plan adds five new moddable feature areas:

| # | Feature | Approach | Difficulty |
|---|---|---|---|
| 1 | Backpack Slots | JSON — 6 files, 1 new processor | Low |
| 2 | Hero Level Progression | JSON — 1 file, computed array output | Medium |
| 3 | Fast Travel Bell Limit | JSON — 1 file, 1 new processor | Low |
| 4 | Lantern Burn Duration | JSON — 2 files, partially reuses existing data | Low |
| 5 | INI Mods (Minimap + Fog) | INI file packing — new code path | Medium |

**Implementation order recommendation:** 4 → 3 → 1 → 2 → 5

---

## Feature 1 — Backpack Slots

### What It Does

Sets the number of inventory slots on each backpack tier. Vanilla gives each tier a fixed slot count (4 / 8 / 12 / 16 / 20 / 300). A single multiplier scales all tiers proportionally.

### Reference Mod

**"More slots in Bag"** — `MorebackpackslotsX3_P.pak` — 3× multiplier across all tiers.

### Asset Type

`R5BLSlotCountModifierParams` — 6 Data Assets under `R5/Content/Gameplay/ItemsLogic/Backpack/`

### JSON Schema

```json
{
    "$type": "R5BLSlotCountModifierParams",
    "InventorySlotsData": {
        "SlotParams": "/R5BusinessRules/Inventory/SlotsParams/DA_BL_Slot_Default.DA_BL_Slot_Default",
        "CountSlots": 12
    },
    "ModifiableModule": { "TagName": "Inventory.Module.Default" },
    "AssetBundleData": { "Bundles": [] },
    "NativeClass": "/Script/CoreUObject.Class'/Script/R5BusinessRules.R5BLSlotCountModifierParams'"
}
```

**Target field:** `InventorySlotsData.CountSlots`

### Vanilla and Reference Values

| File | Vanilla slots | Mod slots (3×) |
|---|---|---|
| `DA_Backpack_SlotCountModifierParams_L00_T01.json` | 4 | 12 |
| `DA_Backpack_SlotCountModifierParams__L01_T01.json` | 8 | 24 |
| `DA_Backpack_SlotCountModifierParams__L02_T01.json` | 12 | 36 |
| `DA_Backpack_SlotCountModifierParams__L03_T01.json` | 16 | 48 |
| `DA_Backpack_SlotCountModifierParams__L04_T01.json` | 20 | 60 |
| `DA_Backpack_SlotCountModifierParams__L10_T01.json` | 300 | 900 |

Note: Files L01–L10 have a double underscore before `L0X` in their filename — this is not a typo, it matches the pak content exactly.

**Reference multiplier:** `BACKPACK_REF_MULT = 3.0`  
**Derivation:** `new_value = round((mod_value / 3.0) * user_mult)`

### Extraction Steps

```bash
tools/repak/repak.exe unpack "Mods/More slots in Bag/MorebackpackslotsX3_P.pak" --output tools/extracted_backpack
```

### pak_generator.py Changes

New constant:
```python
SRC_BACKPACK      = TOOLS_DIR / "extracted_backpack"
BACKPACK_REF_MULT = 3.0
```

New function `_process_backpack(src, base, staging, user_mult, counts)`:
- Read JSON, check `$type == "R5BLSlotCountModifierParams"`
- `vanilla = CountSlots / BACKPACK_REF_MULT`
- `new_val = max(1, round(vanilla * user_mult))`
- Write to same relative path under staging

In `generate()`, iterate `SRC_BACKPACK.rglob("*.json")` and call `_process_backpack()` with `values.get("backpack_slots", 1.0)`.

### UI Changes (create_tab.py)

New section: `("Backpack Slots", "Number of inventory slots per backpack tier.", "_build_backpack")`

Single slider row:
- Key: `backpack_slots`, type `DoubleVar`, range 1.0–10.0, unit "×"
- Label: "Backpack Slot Multiplier"
- Description: "Scales all tiers proportionally. Vanilla: 4 / 8 / 12 / 16 / 20 slots."

Add `backpack_slots` to all three PRESETS: Vanilla=1.0, Relaxed=2.0, Abundant=5.0.

### Risks

- L10_T01 has 300 vanilla slots. A 10× multiplier = 3000 — verify the game handles this without issues before setting the slider max.
- The file naming inconsistency (single vs double underscore) must be preserved exactly.

---

## Feature 2 — Hero Level Progression

### What It Does

Controls the hero XP table: how many levels exist, how much XP each level costs, and how many talent/stat points are awarded per level.

### Reference Mod

**"BetterLevels 30L DE 6S 3T"** — `BetterLevels_30L_DE_6S_3T_P.pak`  
Name: **30 Levels**, **6 Stat points/level**, **3 Talent points/level**.

### Asset Type

`R5BLEntityProgressionLevelParams` — single file:  
`R5/Plugins/R5BusinessRules/Content/EntityProgression/DA_HeroLevels.json`

### JSON Schema

```json
{
    "$type": "R5BLEntityProgressionLevelParams",
    "Levels": [
        { "Exp": 0,   "TalentPointsReward": 0, "StatPointsReward": 0 },
        { "Exp": 600, "TalentPointsReward": 3, "StatPointsReward": 6 },
        ...
    ],
    "AssetBundleData": { "Bundles": [] },
    "NativeClass": "/Script/CoreUObject.Class'/Script/R5BusinessRules.R5BLEntityProgressionLevelParams'"
}
```

### Reference XP Table (actual extracted values)

| Level | Exp | Δ from prev | TalentPts | StatPts |
|---|---|---|---|---|
| 0 | 0 | — | 0 | 0 |
| 1 | 600 | 600 | 3 | 6 |
| 2–4 | +600 each | 600 | 3 | 6 |
| 5–9 | +800 each | 800 | 3 | 6 |
| 10–29 | +1000 each | 1000 | 3 | 6 |

XP pattern: levels 1–4 add 600, levels 5–9 add 800, levels 10+ add 1000.

### Vanilla Values

**Unknown.** The reference mod is a full replacement of the level table, not a multiplier mod. Two options:

- **Option A (recommended for v1):** Use the BetterLevels table as the baseline. Apply `xp_mult` relative to its values. At 1.0×, the user gets the BetterLevels XP curve.
- **Option B:** Extract vanilla `DA_HeroLevels.json` via FModel with the AES key and game mappings. Then hardcode vanilla XP values in `pak_generator.py` and apply `xp_mult` relative to those. This gives a true "vanilla feel" at 1.0×.

**Decision required before implementation:** Confirm whether FModel extraction is available.

### Extraction Steps

```bash
tools/repak/repak.exe unpack "Mods/BetterLevels 30L DE 6S 3T/BetterLevels_30L_DE_6S_3T_P.pak" --output tools/extracted_levels
```

### pak_generator.py Changes

New constant:
```python
SRC_LEVELS = TOOLS_DIR / "extracted_levels"
```

New function `_process_levels(src, staging, values, counts)`:
- Read reference JSON to get XP deltas per level
- Apply `xp_mult` to each level's Exp value
- Set `TalentPointsReward` and `StatPointsReward` from user values for every level (except level 0)
- Truncate or extend array to `levels_max` entries
- For levels beyond the reference table, extrapolate using the last known delta × xp_mult
- Level 0 entry must always be `{Exp:0, TalentPointsReward:0, StatPointsReward:0}`

### UI Changes (create_tab.py)

New section: `("Hero Levels", "XP curve, talent points, and stat points per level.", "_build_levels")`

Four slider rows:
- `levels_xp_mult` — `DoubleVar`, 0.1–5.0, unit "×". Label note: "< 1.0 = cheaper XP, > 1.0 = grindier"
- `levels_talent_pts` — `IntVar`, 0–10, unit "pts/level"
- `levels_stat_pts` — `IntVar`, 0–20, unit "pts/level"
- `levels_max` — `IntVar`, 1–100, unit "levels"

Preset values:

| Key | Vanilla | Relaxed | Abundant |
|---|---|---|---|
| `levels_xp_mult` | 1.0 | 0.5 | 0.25 |
| `levels_talent_pts` | 3 | 3 | 5 |
| `levels_stat_pts` | 6 | 6 | 10 |
| `levels_max` | 30 | 30 | 50 |

### Risks

- **xp_mult direction is counterintuitive:** higher value = harder, lower = easier. UI must make this explicit.
- Talent/stat points too high may trivialize skill trees. Cap slider at 10 / 20 respectively.
- Level 0 entry must always have all-zero values — the game relies on this as the initial state.

---

## Feature 3 — Fast Travel Bell Limit

### What It Does

Sets the maximum number of Fast Travel Bells placeable per world. Two bell types exist; both are set to the same limit.

### Reference Mod

**"FastTravelPlus 50"** — `MoreFastTravelPoints_50_P.pak` — sets `MaxAmount = 50` for both bell types.

### Asset Type

`R5BuildingLimits` — single file:  
`R5/Content/Gameplay/BuildingLimits/DA_BuildLimits_FastTravel.json`

### JSON Schema (full file, actual mod values)

```json
{
    "$type": "R5BuildingLimits",
    "AmountLimits": [
        {
            "Type": "Total",
            "Collection": ["/Game/Gameplay/Building/BuildingUtilities/DA_BI_Utilities_FastTravel_Bell.DA_BI_Utilities_FastTravel_Bell"],
            "MaxAmount": 50
        },
        {
            "Type": "Total",
            "Collection": ["/Game/Gameplay/Building/BuildingUtilities/DA_BI_Utilities_FastTravelBell_02.DA_BI_Utilities_FastTravelBell_02"],
            "MaxAmount": 50
        }
    ],
    "NativeClass": "/Script/CoreUObject.Class'/Script/R5.R5BuildingLimits'"
}
```

**Target field:** `AmountLimits[].MaxAmount` — both entries set identically.

### Vanilla Values

**Unknown — assumed 5 or 10. Confirm via FModel or in-game before setting the Vanilla preset.**

### Extraction Steps

```bash
tools/repak/repak.exe unpack "Mods/FastTravelPlus 50/MoreFastTravelPoints_50_P.pak" --output tools/extracted_fasttravel
```

### pak_generator.py Changes

New constant:
```python
SRC_FASTTRAVEL = TOOLS_DIR / "extracted_fasttravel"
```

New function `_process_build_limits(src, staging, values, counts)`:
- Read JSON, check `$type == "R5BuildingLimits"`
- Set all `AmountLimits[].MaxAmount` entries to `int(values.get("fasttravel_bells", 10))`
- Write to `staging / "R5/Content/Gameplay/BuildingLimits/DA_BuildLimits_FastTravel.json"`

In `generate()`, call with the extracted JSON file.

### UI Changes (create_tab.py)

New section: `("Building Limits", "Maximum number of placeable buildings per type.", "_build_building_limits")`

Single slider row:
- Key: `fasttravel_bells`, type `IntVar`, range 1–100, unit "bells"
- Label: "Fast Travel Bells"
- Description: "Max Fast Travel Bells placeable per world. Vanilla = 5 (assumed, verify)."

Preset values: Vanilla=5, Relaxed=20, Abundant=50.

### Risks

- Vanilla bell count unconfirmed. If actually 10, update the Vanilla preset before shipping.
- Future game updates may add more bell types as new `AmountLimits` entries — the iterator approach handles this automatically.

---

## Feature 4 — Lantern Burn Duration

### What It Does

Controls how long a lantern burns and how much burn time is restored per refuel. Vanilla = 900 seconds (15 min). Also scales the refuel recipe to match.

### Reference Mod

**"BetterLanternLonger 2x"** — `BetterLanternLonger_2x_P.pak` — 2× multiplier (900 → 1800 seconds).

### Asset Types

1. `R5BLInventoryItem` — `R5/Plugins/R5BusinessRules/Content/InventoryItems/Consumables/Misc/DA_CID_Misc_Lantern_L1_T01.json`
2. `R5BLRecipeData` — `R5/Plugins/R5BusinessRules/Content/Recipes/Economy/Items/Consumables/Misc/DA_RD_CID_Misc_Lantern_L4_T01_fromL1.json`

### Confirmed Vanilla Values

The existing `tools/extracted/` (MoreStacks 100x) already contains the lantern item with **`MaxValue: 900`** — confirmed vanilla, because MoreStacks only touches `MaxCountInSlot`, not `Attributes`.

```
Vanilla burn duration: 900 seconds (15 minutes)
Mod burn duration:    1800 seconds (30 minutes)
Reference multiplier: 2.0×
```

The refuel recipe is **not** in `tools/extracted/`. It must be sourced from the lantern mod extraction.

### JSON Schema — Item Definition (target field)

```json
"Attributes": [
    {
        "Tag": { "TagName": "Inventory.Item.Attribute.Counter" },
        "Value": 0,
        "MaxValue": 900
    }
]
```

**Target:** `Attributes[where Tag.TagName == "Inventory.Item.Attribute.Counter"].MaxValue`

### JSON Schema — Refuel Recipe (target field)

```json
"ResultAttributeModifier": {
    "AttributeModifierData": {
        "AttributeTag": { "TagName": "Inventory.Item.Attribute.Counter" },
        "AttributesModifier": 1800,
        "ModifyItemAttributePolicy": "Override"
    }
}
```

**Target:** `ResultAttributeModifier.AttributeModifierData.AttributesModifier`

### Extraction Steps

```bash
# Recipe file only; item file already exists in tools/extracted/
tools/repak/repak.exe unpack "Mods/BetterLanternLonger 2x/BetterLanternLonger_2x_P.pak" --output tools/extracted_lantern
```

### pak_generator.py Changes

New constants:
```python
SRC_LANTERN              = TOOLS_DIR / "extracted_lantern"
LANTERN_VANILLA_SECONDS  = 900
LANTERN_ITEM_STEM        = "DA_CID_Misc_Lantern_L1_T01"
```

New function `_process_lantern(staging, values, counts)`:
- `duration_sec = round(float(values.get("lantern_duration_min", 15.0)) * 60)`
- Item file: read from `SRC_STACKS` (existing extraction), find the `Counter` attribute, set `MaxValue = duration_sec`, write to staging
- Recipe file: read from `SRC_LANTERN`, set `AttributesModifier = duration_sec`, write to staging

**Important:** Add `LANTERN_ITEM_STEM` to a skip-set in `_process_stack()` so the lantern is not also written by that function with a conflicting MaxCountInSlot-only update. `_process_lantern()` handles the complete file.

```python
_STACK_SKIP_STEMS = {"DA_CID_Misc_Lantern_L1_T01"}
# In _process_stack(), early return if src.stem in _STACK_SKIP_STEMS
```

### UI Changes (create_tab.py)

New section: `("Consumables", "Duration and charges for consumable items.", "_build_consumables")`

Single slider row initially:
- Key: `lantern_duration_min`, type `DoubleVar`, range 15.0–120.0, unit "min"
- Label: "Lantern Burn Duration"
- Description: "How long a lantern burns before refuel. Vanilla = 15 min."

Preset values: Vanilla=15.0, Relaxed=30.0, Abundant=60.0.

### Risks

- `_process_stack()` and `_process_lantern()` both write the lantern item file. Without the skip-set fix, the last writer wins. Since lantern runs after stacks, it would win — but this is fragile. **Implement the skip-set fix before shipping.**
- `Value: 0` in the Attributes entry is the starting charge (lantern starts unlit). Do not modify this field.
- The refuel recipe uses `ModifyItemAttributePolicy: "Override"` — each refuel restores the full `AttributesModifier` amount regardless of current charge. This matches vanilla behavior.

---

## Feature 5 — INI-Based Mods (Minimap Range + Disable Fog)

### What It Does

Two quality-of-life settings controlled via INI files rather than JSON Data Assets:

- **5a. Minimap Range** — increases the reveal radius around the player and their ships
- **5b. Disable Fog** — removes atmospheric fog from the game world

### Reference Mods

| Sub-feature | Mod | Delivery method |
|---|---|---|
| Minimap Range | "BetterMinimapRange 2x 2x" | INI packed inside a traditional pak |
| Disable Fog | "Disable Fog" | Standalone `Engine.ini` copied to game config directory |

---

### 5a — Minimap Range

**Asset:** `R5/Config/DefaultR5MapSettings.ini` packed into `BetterMinimapRange_2x_2x_P.pak`

**Key INI field:** `MiniMapShowDistance` (appears multiple times for foot, shallow boat, and large ships)

**Reference mod values (2× assumed):**
- On foot: 500 units (vanilla assumed 250)
- Ships: 1500 units (vanilla assumed 750)

**Note:** Vanilla values are unconfirmed. Must verify via FModel or by reading the game's `DefaultR5MapSettings.ini` before shipping this feature.

**Reference multiplier:** `MINIMAP_REF_MULT = 2.0`

#### Extraction Steps

```bash
tools/repak/repak.exe unpack "Mods/BetterMinimapRange 2x 2x/BetterMinimapRange_2x_2x_P.pak" --output tools/extracted_minimap
```

#### pak_generator.py Changes

New constants:
```python
SRC_MINIMAP      = TOOLS_DIR / "extracted_minimap"
MINIMAP_REF_MULT = 2.0
```

New function `_process_minimap(staging, values, counts)`:
- Read `SRC_MINIMAP / "R5/Config/DefaultR5MapSettings.ini"` as text
- Apply `scale = user_mult / MINIMAP_REF_MULT` to all `MiniMapShowDistance=<value>` occurrences via regex
- Write modified INI to `staging / "R5/Config/DefaultR5MapSettings.ini"`
- Pack normally with repak (INI inside pak is loaded by the game)

```python
import re
def scale_distance(m):
    return f"MiniMapShowDistance={float(m.group(1)) * scale:.6f}"
text = re.sub(r"MiniMapShowDistance=(\d+\.\d+)", scale_distance, text)
```

#### UI Changes

Add to the "World Settings" section (new):
- Key: `minimap_range`, type `DoubleVar`, range 0.5–5.0, unit "×"
- Label: "Minimap Reveal Range"
- Description: "Reveal radius around character and ships. Vanilla ≈ 1× (unconfirmed)."

Preset values: Vanilla=1.0, Relaxed=2.0, Abundant=3.0.

---

### 5b — Disable Fog

**File content:**
```ini
[SystemSettings]
r.fog=0
```

**Delivery:** Standalone `Engine.ini` written to `<GameRoot>/R5/Saved/Config/Windows/Engine.ini`. This is **not** packed into a pak — UE5 does not load Engine.ini from pak files.

#### Implementation Approach

Use a separate flow, not part of pak generation:

1. Add `engine_config_path` property to `GamePaths` in `paths.py`:
   ```python
   @property
   def engine_ini(self) -> Path:
       return self.game_root / "R5" / "Saved" / "Config" / "Windows" / "Engine.ini"
   ```

2. New function `apply_engine_ini_mods(game_paths, values)` in `pak_generator.py` (or a new `ini_manager.py`):
   - Read existing `Engine.ini` if present (parse `[SystemSettings]` section)
   - If `values.get("disable_fog")`: set `r.fog=0`
   - If not: remove `r.fog` key if present (restore fog)
   - Write merged INI back to disk

3. UI: add a **checkbox** (not a slider) to the World Settings section. "Apply" is triggered by a separate button with a confirmation dialog showing the file path that will be modified.

#### UI Changes

New section: `("World Settings", "Minimap range and visual/engine settings.", "_build_world_settings")`

Two rows:
- Minimap Range (see 5a above)
- Fog checkbox row:
  - Key: `disable_fog`, type `BooleanVar`
  - Label: "Disable Atmospheric Fog"
  - Description: "Writes Engine.ini to remove fog. Applied separately — not part of pak. Game updates may reset this."
  - Button: "Apply Engine Changes" (calls `apply_engine_ini_mods()`, shows confirmation dialog with destination path)

#### Risks

- **Engine.ini path varies.** Verify `<GameRoot>/R5/Saved/Config/Windows/Engine.ini` is correct for a Steam install. Add to `GamePaths` and verify it exists before writing.
- **Existing Engine.ini must be merged, not overwritten.** Read current content, update only the `r.fog` key, preserve all other keys.
- **Game patches may reset Engine.ini.** Warn users in the UI.
- **UE5 does NOT load Engine.ini from pak files** — do not attempt to pack it.

---

## Reference Data Extraction Summary

Run all extraction commands once from the project root, then commit results to git.

```bash
# Feature 1 — Backpack Slots (3× reference)
tools/repak/repak.exe unpack "Mods/More slots in Bag/MorebackpackslotsX3_P.pak" --output tools/extracted_backpack

# Feature 2 — Hero Levels (30-level reference)
tools/repak/repak.exe unpack "Mods/BetterLevels 30L DE 6S 3T/BetterLevels_30L_DE_6S_3T_P.pak" --output tools/extracted_levels

# Feature 3 — Fast Travel Bells (50-bell reference)
tools/repak/repak.exe unpack "Mods/FastTravelPlus 50/MoreFastTravelPoints_50_P.pak" --output tools/extracted_fasttravel

# Feature 4 — Lantern recipe (item file already in tools/extracted/)
tools/repak/repak.exe unpack "Mods/BetterLanternLonger 2x/BetterLanternLonger_2x_P.pak" --output tools/extracted_lantern

# Feature 5a — Minimap Range INI
tools/repak/repak.exe unpack "Mods/BetterMinimapRange 2x 2x/BetterMinimapRange_2x_2x_P.pak" --output tools/extracted_minimap

# Feature 5b — Fog disable (no extraction needed; content is hardcoded)
```

New `check_sources()` entries to add:
```python
("Backpack slots extraction",     SRC_BACKPACK),
("Hero levels extraction",        SRC_LEVELS),
("Fast travel limits extraction", SRC_FASTTRAVEL),
("Lantern recipe extraction",     SRC_LANTERN),
("Minimap settings extraction",   SRC_MINIMAP),
```

---

## New PRESETS Keys Summary

All keys must be added to all three preset dicts (`Vanilla`, `Relaxed`, `Abundant`):

| Key | Type | Vanilla | Relaxed | Abundant | Slider range |
|---|---|---|---|---|---|
| `backpack_slots` | float | 1.0 | 2.0 | 5.0 | 1.0–10.0 |
| `levels_xp_mult` | float | 1.0 | 0.5 | 0.25 | 0.1–5.0 |
| `levels_talent_pts` | int | 3 | 3 | 5 | 0–10 |
| `levels_stat_pts` | int | 6 | 6 | 10 | 0–20 |
| `levels_max` | int | 30 | 30 | 50 | 1–100 |
| `fasttravel_bells` | int | 5 | 20 | 50 | 1–100 |
| `lantern_duration_min` | float | 15.0 | 30.0 | 60.0 | 15.0–120.0 |
| `minimap_range` | float | 1.0 | 2.0 | 3.0 | 0.5–5.0 |
| `disable_fog` | bool | False | False | False | checkbox |

`levels_xp_mult` note: values **below 1.0 make leveling easier** (less XP needed). The UI must make this direction explicit.

---

## Unresolved Items — Require Game Data Access

Before shipping Features 3, 5a, and 5b, confirm these vanilla values via FModel (AES key + mappings) or in-game observation:

1. **Fast travel bell vanilla limit** — assumed 5, may be 10. Check `DA_BuildLimits_FastTravel.json` in the encrypted game paks.
2. **Minimap show distances** — assumed 250 (foot) / 750 (ship). Check `DefaultR5MapSettings.ini` in the game install at `<GameRoot>/R5/Config/` or via FModel.
3. **Vanilla hero level count and XP curve** — entirely unknown. Check `DA_HeroLevels.json` in game paks via FModel.
4. **Engine.ini config path** — assumed `<GameRoot>/R5/Saved/Config/Windows/Engine.ini`. Verify against the actual Steam install.

---

## Key Files for Implementation

| File | Role |
|---|---|
| `core/pak_generator.py` | All new `_process_*` functions |
| `ui/tabs/create_tab.py` | New SECTIONS, PRESETS keys, builder methods |
| `core/paths.py` | Add `engine_ini` path property for Feature 5b |
| `Docs/DevNotes/game-data-reference.md` | Update with new asset types |
| `Docs/DevNotes/tools-setup.md` | Add new extraction commands |
