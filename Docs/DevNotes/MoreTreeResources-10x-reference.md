# MoreTreeResources 10x — Complete File Reference

Extracted from `C:\Projects\windrose\Mods\MoreTreeResources 10x\`. This document
describes every file precisely enough to recreate the mod from scratch.

---

## File Inventory

| File | Size | Format |
|---|---|---|
| `MoreTreeResources_10x_P.pak` | 347 bytes | I/O Store stub (empty, required by engine) |
| `MoreTreeResources_10x_P.ucas` | 309,732 bytes | I/O Store binary data (DA_Segment_* assets) |
| `MoreTreeResources_10x_P.utoc` | 5,350 bytes | I/O Store table of contents |
| `MoreTreeResourcesOther_10x_P.pak` | 73,515 bytes | Traditional pak (JSON loot tables) |

The naming convention `MoreTreeResourcesOther_10x_P` puts "Other" before the multiplier
tag. This differs from our generator's `{base}TreeOther_P` pattern.

---

## Critical Finding: Where the 10x Actually Comes From

**The 10x multiplier comes entirely from the JSON loot tables in `MoreTreeResourcesOther_10x_P.pak`.**

The DA_Segment binary files in the I/O Store pack contain **vanilla values (1.65)** —
identical to the unmodified game. The mod includes them unchanged. This means:

- DA_Segment files control something unrelated to item drop counts (likely animation/chopping
  stage parameters, not the wood you receive in your inventory)
- All wood/herb/hardwood/fiber yield increases are from the loot table JSONs
- The I/O Store pak may be included to claim those asset slots and prevent other mods from
  overriding them, or simply because the author included all tree-related assets

**Implication for our generator:** Our `_process_segment_uexp()` modification is unnecessary
for changing how much wood a player receives. Loot table JSON changes are what matter.

---

## JSON Pak: `MoreTreeResourcesOther_10x_P.pak`

### Pak format
- Tool: repak `V8B` (FNameBasedCompression), no compression
- Mount point: `../../../`
- All paths inside: `R5/Plugins/R5BusinessRules/Content/LootTables/Foliage/...`

### File count: 85 JSON files

All files are type `R5BLLootParams` with `LootTableType: List` (or `Weight` for
corrupted-stump redirectors). Extra fields present on all records:
- `LootTableId: {"TagName": "None"}` (may be absent on simpler entries)
- `AssetBundleData: {"Bundles": []}` (may be absent on simpler entries)

### Complete file listing and values

All paths are relative to the pak mount: `R5/Plugins/R5BusinessRules/Content/LootTables/Foliage/`

#### Ashlands BurntTree (plague_wood category, 32 files)

These all drop Coal and/or Wood at 10x. Vanilla values can be back-computed by dividing
the values shown here by 10.

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Ashlands_BurntTree_01_01.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_02.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_04.json` | Coal W=1: Min=40 Max=50 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_05.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_06.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_07.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_08.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_09.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_10.json` | Coal W=1: Min=10 Max=20; Wood W=1: Min=10 Max=20 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_11.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_01_12.json` | Coal W=1: Min=10 Max=20; Wood W=1: Min=20 Max=30 |
| `DA_LT_Foliage_Ashlands_BurntTree_02_01.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_02_02.json` | Coal W=1: Min=10 Max=10; SticksWood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_02_05.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_02_06.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_02_08.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_02_09.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_02_11.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_02_12.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_03_02.json` | Coal W=1: Min=10 Max=20; Wood W=1: Min=10 Max=20 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_01.json` | Wood W=1: Min=30 Max=30; Wood W=1: Min=20 Max=30; Wood W=1: Min=20 Max=30 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_02.json` | Wood W=1: Min=30 Max=50; Wood W=1: Min=30 Max=50; Wood W=1: Min=30 Max=50 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_03.json` | Wood W=1: Min=30 Max=30; Wood W=1: Min=20 Max=30; Wood W=1: Min=20 Max=30 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_07.json` | Wood W=1: Min=30 Max=30; Wood W=1: Min=20 Max=30; Wood W=1: Min=20 Max=30 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_08.json` | Wood W=1: Min=30 Max=50; Wood W=1: Min=30 Max=50; Wood W=1: Min=30 Max=50 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_09.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_10.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_11.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_12.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_13.json` | Coal W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_14.json` | Wood W=1: Min=30 Max=50; Wood W=1: Min=30 Max=50; Wood W=1: Min=30 Max=50 |
| `DA_LT_Foliage_Ashlands_BurntTree_04_15.json` | Wood W=1: Min=30 Max=30; Wood W=1: Min=20 Max=30; Wood W=1: Min=20 Max=30 |

Note: BurntTree_01_* and _02_* are small nodes; _04_* are large dead trees.
_03_02 appears to be a medium variant. No _03_01 or other _03_* files are present.

#### Ashlands BurntTree Big (large fallen logs, 5 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Ashlands_BurntTree_Big_01.json` | Coal W=1: Min=40 Max=50; Wood W=1: Min=30 Max=50; Wood W=1: Min=30 Max=50 |
| `DA_LT_Foliage_Ashlands_BurntTree_Big_02.json` | Coal W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40 |
| `DA_LT_Foliage_Ashlands_BurntTree_Big_03.json` | Coal W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40 |
| `DA_LT_Foliage_Ashlands_BurntTree_Big_04.json` | Coal W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40 |
| `DA_LT_Foliage_Ashlands_BurntTree_Big_05.json` | Coal W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40 |

#### Ashlands BurntTree Palm / PalmSabal_Burnt (8 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Ashlands_BurntTree_Palm_01.json` | Wood W=0: Min=30 Max=50; Wood W=1: Min=30 Max=50 |
| `DA_LT_Foliage_Ashlands_BurntTree_Palm_02.json` | Wood W=0: Min=20 Max=40; Wood W=1: Min=20 Max=40; Wood W=1: Min=20 Max=40 |
| `DA_LT_Foliage_Ashlands_BurntTree_Palm_03.json` | Wood W=0: Min=20 Max=40; Wood W=1: Min=20 Max=40; Wood W=1: Min=20 Max=40 |
| `DA_LT_Foliage_Ashlands_BurntTree_Palm_05.json` | Wood W=0: Min=30 Max=40; Wood W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40 |
| `DA_LT_Foliage_Ashlands_BurntTree_Palm_06.json` | Wood W=0: Min=30 Max=40; Wood W=1: Min=30 Max=40; Wood W=1: Min=30 Max=40 |
| `DA_LT_Foliage_Ashlands_BurntTree_Palm_07.json` | Wood W=0: Min=20 Max=30; Wood W=1: Min=10 Max=20; Wood W=1: Min=10 Max=20 |
| `DA_LT_Foliage_Ashlands_BurntTree_PalmSabal_Burnt_600cm.json` | Wood W=0: Min=30 Max=50; Wood W=1: Min=30 Max=50 |
| `DA_LT_Foliage_Ashlands_BurntTree_PalmSabal_Burnt_1000cm.json` | Wood W=0: Min=30 Max=50; Wood W=1: Min=30 Max=50 |
| `DA_LT_Foliage_Ashlands_BurntTree_PalmSabal_Burnt_1300cm.json` | Wood W=0: Min=30 Max=50; Wood W=1: Min=30 Max=50; Wood W=1: Min=30 Max=50 |

Note: `Palm_04` is absent (presumably vanilla value not modified or file skipped by mod author).

#### Ashlands Frailejon (herbs/shrubs, 3 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Ashlands_Frailejon_150cm.json` | Wood W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_Frailejon_330cm.json` | Wood W=1: Min=10 Max=10; Wood W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Ashlands_Frailejon_400cm.json` | Wood W=1: Min=20 Max=30; Wood W=1: Min=20 Max=30 |

#### Ashlands Logs (fallen logs on ground, 3 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Ashlands_Log_01.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=20 |
| `DA_LT_Foliage_Ashlands_Log_02.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=20 |
| `DA_LT_Foliage_Ashlands_Log_03.json` | Coal W=1: Min=10 Max=10; Wood W=1: Min=10 Max=20 |

#### Default / Generic trees (5 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_DefaultFiber.json` | FiberPlant W=0: Min=10 Max=10 |
| `DA_LT_Foliage_DefaultStick.json` | Wood W=0: Min=10 Max=10 |
| `DA_LT_Foliage_DefaultWood.json` | Wood W=0: Min=10 Max=10 |
| `DA_LT_Foliage_DiviStump.json` | Hardwood W=0: Min=20 Max=30; Bark W=0: Min=10 Max=10 |
| `DA_LT_Foliage_MahoganyStump.json` | Mahogany W=0: Min=20 Max=30; Mahogany W=0: Min=20 Max=30; Mahogany W=1: Min=30 Max=40 |

**DefaultFiber** lacks `LootTableId` and `AssetBundleData` fields.
**DefaultWood** and **DefaultFiber** also lack those fields.
**DiviStump** and **MahoganyStump** lack those fields too.

Vanilla back-compute (÷10): DefaultWood/DefaultStick → 1 each. DiviStump → Hardwood 2-3, Bark 0-1.

#### Fiber plants (5 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Fiber_Big_T01.json` | Fiber W=0: Min=10 Max=10; Fiber W=0: Min=10 Max=10; Fiber W=0: Min=10 Max=20 |
| `DA_LT_Foliage_Fiber_Mancinella_Big.json` | Fiber W=0: Min=30 Max=40; sub-table W=0: Min=10 Max=10 (→ DA_LT_Foliage_Mancinella_Seeds) |
| `DA_LT_Foliage_Fiber_Mancinella_Medium.json` | Fiber W=0: Min=20 Max=30 |
| `DA_LT_Foliage_Fiber_Medium_T01.json` | Fiber W=0: Min=10 Max=10; Fiber W=0: Min=10 Max=20 |
| `DA_LT_Foliage_Fiber_Small_T01.json` | Fiber W=0: Min=10 Max=10 |

Note: Mancinella entries include `ItemAttributeModifiers: []` field.

#### Jungle Logs (3 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Jungle_Log_01.json` | Wood W=0: Min=20 Max=30; Fiber W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Jungle_Log_02.json` | Wood W=0: Min=30 Max=40; Fiber W=1: Min=10 Max=10 |
| `DA_LT_Foliage_Jungle_Log_03.json` | Wood W=0: Min=20 Max=30; Fiber W=1: Min=10 Max=10 |

Vanilla (÷10): Log_01/03 → 2-3 wood; Log_02 → 3-4 wood. Fiber = 1.

#### Lime Tree (food, 1 file)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_LimeTree.json` | Lime W=1: Min=20 Max=30; sub-table W=0: Min=10 Max=10 (→ Sub_tables/DA_LT_Foliage_LimeTree_Seeds) |

Has `ItemAttributeModifiers: []` field on entries.

#### Stumps (2 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Stump_01.json` | Wood W=0: Min=30 Max=40; Wood W=0: Min=10 Max=20 |
| `DA_LT_Foliage_Stump_02.json` | Wood W=0: Min=20 Max=30; Wood W=0: Min=10 Max=20 |

Vanilla (÷10): Stump_01 → 3-4 + 1-2 wood; Stump_02 → 2-3 + 1-2 wood.

#### Corrupted Stumps (6 files, redirectors)

These use `LootTableType: Weight` and redirect to sub-tables.

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Stump_Corrupted_01.json` | → StatueCorrupted_01 W=70: Min=10 Max=10; → StatueCorrupted_02 W=30: Min=10 Max=10 |
| `DA_LT_Foliage_Stump_Corrupted_02.json` | → StatueCorrupted_01 W=70: Min=10 Max=10; → StatueCorrupted_02 W=30: Min=10 Max=10 |
| `DA_LT_Foliage_Stump_Corrupted_03.json` | → StatueCorrupted_01 W=70: Min=10 Max=10; → StatueCorrupted_02 W=30: Min=10 Max=10 |
| `DA_LT_Foliage_Stump_Corrupted_04.json` | → StatueCorrupted_01 W=70: Min=10 Max=10; → StatueCorrupted_02 W=15: Min=10 Max=10 |
| `DA_LT_Foliage_Stump_Corrupted_05.json` | → StatueCorrupted_01 W=70: Min=10 Max=10; → StatueCorrupted_02 W=30: Min=10 Max=10 |
| `DA_LT_Foliage_Stump_Corrupted_06.json` | → StatueCorrupted_01 W=60: Min=10 Max=10; → StatueCorrupted_02 W=40: Min=10 Max=10 |

Corrupted_04 has `LootTableId: {"TagName": "None"}` and `AssetBundleData` fields; the others do not.
Corrupted_06 also has those fields.

LootItem field: `'None'` (string) for entries 01-03/05; `'None'` for 04/06 too.

#### Swamp trees (3 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Swamp_BigTaxodium_01.json` | Wood W=0: Min=30 Max=40; Resin W=1: Min=20 Max=30 |
| `DA_LT_Foliage_Swamp_BigTaxodium_02.json` | Wood W=0: Min=20 Max=30 |
| `DA_LT_Foliage_Swamp_SmallTaxodium_01.json` | Wood W=0: Min=30 Max=40 |

Resin item: `DA_DID_Resource_Resin_T03`.

#### Swamp StatueCorrupted sub-tables (3 files)

| File | LootData entries |
|---|---|
| `DA_LT_Foliage_Swamp_StatueCorrupted_01.json` | Wood W=0: Min=20 Max=30 |
| `DA_LT_Foliage_Swamp_StatueCorrupted_02.json` | Wood W=0: Min=20 Max=30; EnchantedWood W=0: Min=10 Max=30 |
| `DA_LT_Foliage_Swamp_StatueCorrupted_Final.json` | → StatueCorrupted_01 W=70: Min=10 Max=10; → StatueCorrupted_02 W=30: Min=10 Max=10 |

`StatueCorrupted_Final` uses `LootItem: ''` (empty string, not `'None'`).
`LootTableType: Weight`.

#### Hardwood Divi log (axe-mined logs, 4 files)

These are under `DA_LT_Mineral_*` but are loot_hardwood. Named with `Mineral_` prefix because
Divi logs are chopped from the ground like minerals.

| File | LootData entries |
|---|---|
| `DA_LT_Mineral_DiviLog_01.json` | Hardwood W=0: Min=10 Max=20; Bark W=1: Min=10 Max=10; Wood W=1: Min=10 Max=20 |
| `DA_LT_Mineral_DiviLogs_01.json` | Hardwood W=0: Min=80 Max=120; Bark W=1: Min=40 Max=80; Wood W=1: Min=40 Max=120 |
| `DA_LT_Mineral_DiviLogs_02.json` | Hardwood W=0: Min=40 Max=80; Bark W=1: Min=30 Max=60; Wood W=1: Min=40 Max=80 |
| `DA_LT_Mineral_DiviLogs_03.json` | Hardwood W=0: Min=120 Max=140; Bark W=1: Min=60 Max=100; Wood W=1: Min=120 Max=140 |

These have `ItemAttributeModifiers: []` on each entry.

#### Sub-table (1 file, in `Sub_tables/` subfolder)

| File | LootData entries |
|---|---|
| `Sub_tables/DA_LT_Foliage_LimeTree_Seeds.json` | None W=50: Min=10 Max=10; LimeTreeSeeds W=50: Min=10 Max=10 |

`LootTableType: Weight`. Has `ItemAttributeModifiers: []` on entries.
LimeTreeSeeds item: `DA_DID_Resource_LimeTreeSeeds_T02`.

---

## Item Reference Keys

Short names used in the tables above map to these full asset paths:

| Short name | Full path |
|---|---|
| Wood | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_Wood_T01.DA_DID_Resource_Wood_T01` |
| SticksWood | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_SticksWood_T01.DA_DID_Resource_SticksWood_T01` |
| Hardwood | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_Hardwood_T02.DA_DID_Resource_Hardwood_T02` |
| Mahogany | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_Mahogany_T04.DA_DID_Resource_Mahogany_T04` |
| EnchantedWood | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_EnchantedWood_T03.DA_DID_Resource_EnchantedWood_T03` |
| Bark | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_Bark_T02.DA_DID_Resource_Bark_T02` |
| Resin | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_Resin_T03.DA_DID_Resource_Resin_T03` |
| Coal | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_Coal_T01.DA_DID_Resource_Coal_T01` |
| Fiber | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_FiberPlant_T01.DA_DID_Resource_FiberPlant_T01` |
| Lime | `/R5BusinessRules/InventoryItems/Consumables/Food/DA_CID_Food_Raw_Lime_T02.DA_CID_Food_Raw_Lime_T02` |
| LimeTreeSeeds | `/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_LimeTreeSeeds_T02.DA_DID_Resource_LimeTreeSeeds_T02` |

---

## I/O Store Pack: `MoreTreeResources_10x_P.pak/.ucas/.utoc`

### Format

- Tool: `retoc to-zen --version UE5_6`
- Chunk type: `ExportBundleData` (41 asset chunks + 1 `ContainerHeader`)
- **Chunk ID paths use `R5/Content/...` prefix** — NOT `Content/...`
  - Staging dir must have `R5/Content/Gameplay/Foliage/...` structure
  - This matches the game's internal chunk ID namespace for R5 plugin assets

### File count: 41 DA_Segment_* files

All stored at virtual path: `R5/Content/Gameplay/Foliage/SegmentTrees/ParamsSegmentTrees/`

### Critical: All segment values are VANILLA (1.65)

Every DA_Segment file in this mod contains **unmodified vanilla values**. Each file has
exactly 4 amount groups, each with `min=1.65, max=1.65` (anchored by a 0.75 probability
double immediately following each pair in the binary).

The mod author included these files without changing their values. **Do not modify these
to increase wood yield — use loot table JSONs instead.**

### Complete list of DA_Segment files with sizes and value offsets

All 41 files: 4 amount groups each, all min=1.65 max=1.65.

| File | Size (bytes) | Group 1 offset | Group 2 offset | Group 3 offset | Group 4 offset |
|---|---|---|---|---|---|
| DA_Segment_Coast_Jungle_Ficus_1000cm | 7,045 | 6581 | 6707 | 6833 | 6959 |
| DA_Segment_Coast_Jungle_Ficus_1200cm | 7,090 | 6597 | 6723 | 6849 | 6975 |
| DA_Segment_Coast_Jungle_Ficus_1800cm | 7,636 | 7143 | 7269 | 7395 | 7521 |
| DA_Segment_Coast_Jungle_Ficus_300cm | 7,282 | 6544 | 6670 | 6796 | 6922 |
| DA_Segment_Coast_Jungle_Ficus_500cm | 7,282 | 6544 | 6670 | 6796 | 6922 |
| DA_Segment_Coast_Jungle_Ficus_600cm | 7,282 | 6544 | 6670 | 6796 | 6922 |
| DA_Segment_Coast_Jungle_Ficus_800cm | 7,245 | 6637 | 6763 | 6889 | 7015 |
| DA_Segment_Coast_Jungle_FicusRed_500cm | 7,359 | 6621 | 6747 | 6873 | 6999 |
| DA_Segment_Coast_Jungle_PalmCoconutFruit_1000cm | 8,262 | 7511 | 7637 | 7763 | 7889 |
| DA_Segment_Coast_Jungle_PalmCoconutFruit_1400cm | 8,217 | 7495 | 7621 | 7747 | 7873 |
| DA_Segment_Coast_Jungle_PalmCoconutFruit_700cm | 8,315 | 7564 | 7690 | 7816 | 7942 |
| DA_Segment_Coast_Jungle_PalmSabal_1000cm | 7,163 | 6670 | 6796 | 6922 | 7048 |
| DA_Segment_Coast_Jungle_PalmSabal_1400cm | 7,587 | 7094 | 7220 | 7346 | 7472 |
| DA_Segment_Coast_Jungle_PalmSabal_250cm | 7,394 | 6771 | 6897 | 7023 | 7149 |
| DA_Segment_Coast_Jungle_PalmSabal_450cm | 7,394 | 6771 | 6897 | 7023 | 7149 |
| DA_Segment_Coast_Jungle_PalmSabal_700cm | 7,333 | 6710 | 6836 | 6962 | 7088 |
| DA_Segment_Highlands_Divi_1200cm | 8,234 | 7582 | 7708 | 7834 | 7960 |
| DA_Segment_Highlands_Divi_1600cm | 8,336 | 7598 | 7724 | 7850 | 7976 |
| DA_Segment_Highlands_Divi_1700cm | 8,336 | 7598 | 7724 | 7850 | 7976 |
| DA_Segment_Highlands_Divi_500cm | 7,334 | 6625 | 6751 | 6877 | 7003 |
| DA_Segment_Highlands_Divi_800cm | 7,334 | 6625 | 6751 | 6877 | 7003 |
| DA_Segment_Sand_Beach_PalmCoconutEmpty_1400cm | 7,329 | 6721 | 6847 | 6973 | 7099 |
| DA_Segment_Sand_Beach_PalmCoconutEmpty_700cm | 7,158 | 6665 | 6791 | 6917 | 7043 |
| DA_Segment_Sand_Beach_PalmCoconutEmpty_900cm | 7,036 | 6543 | 6669 | 6795 | 6921 |
| DA_Segment_Swamp_GrumpyFicus_1000cm | 7,117 | 6653 | 6779 | 6905 | 7031 |
| DA_Segment_Swamp_GrumpyFicus_1200cm | 7,162 | 6669 | 6795 | 6921 | 7047 |
| DA_Segment_Swamp_GrumpyFicus_1800cm | 7,223 | 6730 | 6856 | 6982 | 7108 |
| DA_Segment_Swamp_PalmSabal_Sick_1000cm | 7,227 | 6734 | 6860 | 6986 | 7112 |
| DA_Segment_Swamp_PalmSabal_Sick_1400cm | 7,227 | 6734 | 6860 | 6986 | 7112 |
| DA_Segment_Swamp_PalmSabal_Sick_250cm | 7,280 | 6787 | 6913 | 7039 | 7165 |
| DA_Segment_Swamp_PalmSabal_Sick_450cm | 7,280 | 6787 | 6913 | 7039 | 7165 |
| DA_Segment_Swamp_PalmSabal_Sick_700cm | 7,211 | 6718 | 6844 | 6970 | 7096 |
| DA_Segment_Swamp_TaxodiumBald_800cm | 7,695 | 7202 | 7328 | 7454 | 7580 |
| DA_Segment_Swamp_TaxodiumBald_900cm | 7,695 | 7202 | 7328 | 7454 | 7580 |
| DA_Segment_Swamp_TaxodiumBaldCorrupted_900cm | 7,504 | 6925 | 7051 | 7177 | 7303 |
| DA_Segment_Swamp_TaxodiumDead_1200cm | 7,658 | 7194 | 7320 | 7446 | 7572 |
| DA_Segment_Swamp_TaxodiumDeadCorrupted_1200cm | 7,743 | 7279 | 7405 | 7531 | 7657 |
| DA_Segment_Swamp_TaxodiumDying_1100cm | 7,727 | 7263 | 7389 | 7515 | 7641 |
| DA_Segment_Swamp_TaxodiumDyingCorrupted_740cm | 7,983 | 7404 | 7530 | 7656 | 7782 |
| DA_Segment_Swamp_TaxodiumDyingCorrupted_900cm | 7,922 | 7343 | 7469 | 7595 | 7721 |
| DA_Segment_Swamp_TaxodiumSick_1000cm | 7,719 | 7255 | 7381 | 7507 | 7633 |

Note: offsets shown are for the first field of the min/max pair in the I/O Store format
(after `retoc unpack`). These differ from the `.uexp` offsets in the traditional format.
The source files in `tools/extracted_segments/` are traditional `.uasset/.uexp` pairs
(vanilla game format) and will have different internal layouts.

---

## How to Recreate This Mod

### Prerequisites
- `repak.exe` (V8B pak tool)
- `retoc.exe` (I/O Store tool, `to-zen` subcommand, `--version UE5_6`)
- 41 vanilla DA_Segment_*.uasset/.uexp files from `tools/extracted_segments/Content/...`

### Step 1: Build the JSON pak

1. Create staging dir `MoreTreeResourcesOther_10x_P/`
2. Populate `R5/Plugins/R5BusinessRules/Content/LootTables/Foliage/` with all 85 JSON files
   listed above, using the exact values shown (this IS the 10x data; vanilla ÷ 10)
3. Run: `repak pack --version V8B MoreTreeResourcesOther_10x_P/`
4. Result: `MoreTreeResourcesOther_10x_P.pak` (~73 KB)

### Step 2: Build the I/O Store pak (segment binary files)

1. Create staging dir with path structure: `staging/R5/Content/Gameplay/Foliage/SegmentTrees/ParamsSegmentTrees/`
   — **The `R5/` prefix is mandatory**; without it chunk IDs won't match the game's registry
2. Copy all 41 `.uasset` + `.uexp` files from `tools/extracted_segments/Content/Gameplay/...`
   into that staging path (do NOT modify them — leave values at vanilla 1.65)
3. Run: `retoc to-zen --version UE5_6 <staging_dir> MoreTreeResources_10x_P.utoc`
4. Result: three files `MoreTreeResources_10x_P.pak` (347 bytes stub) + `.ucas` + `.utoc`

### Step 3: Deploy

Place all 4 files in `R5/Content/Paks/~mods/` (create folder if needed).

---

## What Our Generator Does Wrong

Comparing `MoreTreeResources 10x` against `MyGameTuning_P`:

1. **Segment chunk paths**: Our generator stages segments at `Content/Gameplay/...`
   (without `R5/` prefix) → wrong chunk IDs → game ignores our segment pak entirely.
   **Fix**: stage at `R5/Content/Gameplay/...` (one-line change in `pak_generator.py`).
   *(This fix has been applied as of this writing.)*

2. **Segment modification**: We modify the 1.65 doubles to user_mult × 1.65.
   The reference mod does NOT do this. The 1.65 values are **not** the wood yield per chop —
   they appear to be animation/physics parameters. Wood yield comes from loot tables only.
   Our modification is harmless but unnecessary and produces no effect on wood drops.

3. **File naming**: Reference uses `MoreTreeResourcesOther_10x_P` (Other before multiplier).
   Our generator uses `{base}TreeOther_P`. Both are valid pak names; the game loads by path
   not filename. No fix needed unless trying to exactly replicate the reference.

4. **Missing loot tables**: Reference has 85 files including Ashlands BurntTree (32 files),
   Ashlands Log, Ashlands Frailejon, Fiber plants, Lime Tree, DiviLog/DiviLogs (Mineral_ prefix).
   Our `SRC_TREE` (MoreTreeResources 2x) has fewer files. Check what categories the generator
   routes into `root_tree` vs what the reference covers.
