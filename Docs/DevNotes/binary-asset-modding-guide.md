# Binary Asset Modding Guide — DA_Segment & DA_DigVolume

> **⚠ Historical reference — not the current generator behavior.**
> BlackFlag Mod Manager no longer generates binary I/O Store paks. The
> generator emits JSON-only paks (`*Other_P.pak`); `UnrealReZen`, retoc-based
> I/O Store packing, and the `tools/extracted_segments/` + `tools/extracted_digvol/`
> sources have all been removed (see PR #5, May 2026). The references below to
> `_process_segment_uexp`, `_pack_iostore`, and combined Tree/Mineral pak triples
> describe the *previous* design and are preserved here only as a reference for
> anyone investigating binary modding outside this tool. The community mods on
> Nexus (MoreTreeResources, MoreMineralResources) handle these binary-asset
> changes directly.

Both MoreTreeResources and MoreMineralResources follow the same two-file mod structure:

| File | Format | Contents |
|---|---|---|
| `ModName_P.pak + .ucas + .utoc` | I/O Store (binary) | Modified binary `.uasset` files |
| `ModNameOther_P.pak` | Traditional pak (JSON) | Modified JSON data assets |

Our generated mod must mirror this exactly. This document covers both binary asset types.

---

## 1. DA_Segment_* — Tree Chop Yield

### What these are
41 binary assets controlling how much wood you get per chop segment (one per tree mesh size).

**Game path:** `R5/Content/Gameplay/Foliage/SegmentTrees/ParamsSegmentTrees/`  
**Source for extraction:** `tools/extracted_segments/` (pre-extracted from game pak)  
**File format:** Legacy `.uasset` + `.uexp` pair

### Binary format (.uexp)
Each file has 2–4 spawn groups. Each group is a triplet of 8-byte doubles:

```
[min: f64 little-endian]   ← vanilla = 1.65
[max: f64 little-endian]   ← vanilla = 1.65
[prob: f64 = 0.75]         ← probability anchor (do not modify)
```

Offsets are NOT fixed — they vary by file size. Use the `0.75` probability anchor to locate each group.

**Vanilla amount:** `SEGMENT_VANILLA_AMOUNT = 1.65`

### How to find yield values
```python
PROB_BYTES = struct.pack("<d", 0.75)
pos = 0
while True:
    idx = data.find(PROB_BYTES, pos)
    if idx < 0: break
    if idx >= 16:
        min_val = struct.unpack_from("<d", data, idx - 16)[0]
        max_val = struct.unpack_from("<d", data, idx - 8)[0]
        if 0 < min_val <= 1000 and 0 < max_val <= 1000:
            # These are the yield values — replace both with new_amount
    pos = idx + 1
```

### How to modify
```python
new_amount = SEGMENT_VANILLA_AMOUNT * user_multiplier
# Replace min and max at each group with new_amount
struct.pack_into("<d", data, idx - 16, new_amount)
struct.pack_into("<d", data, idx - 8,  new_amount)
```

### Extraction from game paks
Pre-extracted vanilla files already live in `tools/extracted_segments/`.  
To re-extract if game updates:

```powershell
# Combine MoreTreeResources mod + game global into one directory
# Then run:
tools\retoc\retoc.exe to-legacy --version UE5_6 --filter DA_Segment_ tools\_ref_combined_tree tools\extracted_segments
```

The `_ref_combined_tree` directory must contain:
- `MoreTreeResources_*_P.pak/.ucas/.utoc` (the tree mod)
- `global.ucas` + `global.utoc` (from game Paks folder — provides script objects)

### Packing to I/O Store
```powershell
# staging_dir contains: Content/Gameplay/Foliage/SegmentTrees/ParamsSegmentTrees/*.uasset + *.uexp
tools\retoc\retoc.exe to-zen --version UE5_6 staging_dir output_stem.utoc
# Produces: output_stem.pak + output_stem.ucas + output_stem.utoc
```

Deploy all three files (`.pak` + `.ucas` + `.utoc`) into `~mods/`.

---

## 2. DA_DigVolume_* — Mineral Dig Yield

### What these are
35 binary assets controlling how much ore you get per hit on a mineral node.

**Game path:** `R5/Content/TMP/TunnelProt/{Copper,Iron,Rock,Sulfur}/`  
**Source for extraction:** game `pakchunk0_s4-Windows.utoc` (AES-encrypted)  
**File format:** Legacy `.uasset` + `.uexp` pair

### File inventory (35 files total)

| Folder | Files |
|---|---|
| `Copper/Poor/` | 100cmA/C/D, 200cmE, 250cmA/B/C/D, 300cmE, 500cmA/B/C/D (13 files) |
| `Copper/Rich/` | 100cmA, 250cmA, 500cmA, 500cmB (4 files) |
| `Iron/Poor/` | 100cmA/C/D, 200cmE, 250cmA/B/D, 300cmE, 500cmD (9 files) |
| `Iron/Rich/` | 100cm, 250cm, 500cmA, 500cmB (4 files) |
| `Rock/` | 100cm, 250cm, 500cm (3 files) — no yield values found |
| `Sulfur/` | 100cm1 (1 file) — no yield values found |
| `(root)` | DA_DigVolume_PoorType (1 file) |

### Binary format (.uexp) — current game version

Yield values are stored as **4-byte floats (little-endian)** in triplets.  
Each triplet: 3 identical float values spaced **8 bytes apart**.  
Triplets represent {min, max, default} or similar distribution parameters.

#### PoorCopper (13 files, 427–461 bytes)
All Poor Copper files are structurally identical.

| Offset | Vanilla value | Type |
|---|---|---|
| 52 | 242.44 | Structural constant — DO NOT MODIFY |
| 108 | 2.0 | Yield triplet start |
| 116 | 2.0 | Yield triplet mid |
| 124 | 2.0 | Yield triplet end |
| 232 | 1.0 | Probability — DO NOT MODIFY |
| 280 | 2.0 | Secondary yield (present in some files) |

**Modify:** floats at offsets 108, 116, 124 (and 280 if present).

#### RichCopper (4 files, 404–440 bytes)
Rich nodes yield multiple material types — each material has its own yield triplet.

| Offsets | Vanilla value | Notes |
|---|---|---|
| 48 | 223.42 | Structural constant — DO NOT MODIFY |
| 88 | 1.0 | Probability — DO NOT MODIFY |
| 92 | 1.1 | Weight — DO NOT MODIFY |
| 96 | 370.0 | Structural constant — DO NOT MODIFY |
| 104, 112, 120 | 3.10 | Yield group 1 |
| 128, 136, 144 | 2.56 | Yield group 2 |
| 152, 160, 168 | 2.72 | Yield group 3 |
| 176, 184, 192 | 3.10 / 3.26 | Yield group 4 |
| 200, 208, 216 | 2.85 | Yield group 5 |
| 220 | 125.0 | Structural constant — DO NOT MODIFY |
| 412, 420, 428 | 3.39 | Yield group 6 (present in 250/500cm files) |
| 432 | 1.0 | Probability — DO NOT MODIFY |

**Modify:** all yield triplets (groups 1–6).

#### PoorIron (9 files, all 393 bytes)
All Poor Iron files are structurally identical.

| Offsets | Vanilla value | Notes |
|---|---|---|
| 92 | 1.0 | DO NOT MODIFY |
| 96 | 1.0 | DO NOT MODIFY |
| 100 | 450.0 | Structural constant — DO NOT MODIFY |
| 108, 116, 124 | 3.25 | Yield group 1 |
| 132, 140, 148 | 3.10 / 3.26 | Yield group 2 |
| 156, 164, 172 | 2.85 | Yield group 3 |
| 176 | 125.0 | Structural constant — DO NOT MODIFY |
| 336 | 0.30 | Probability — DO NOT MODIFY |

**Modify:** yield groups 1–3 (offsets 108–172).

#### RichIron (4 files, all 471 bytes)
Rich Iron nodes have a single variable yield per file (scales with node size).

| Offset | Vanilla value | Notes |
|---|---|---|
| 272 | 1.0 | DO NOT MODIFY |
| 288 | 3.0 / 6.0 / 28.0 / 35.0 | Total yield — MODIFY this value |

Each file has a different vanilla yield. Modify offset 288 only.  
Vanilla values by file: `100cm=3.0`, `250cm=6.0`, `500cmA=28.0`, `500cmB=35.0`.

#### Rock (3 files, all 307 bytes) — NO YIELD MODIFICATION
No yield values in the 0.5–500 range. Rock yield is controlled by loot tables only.

#### Sulfur (1 file, 307 bytes) — NO YIELD MODIFICATION
Same as Rock — no yield values to modify in this file.

### Modification strategy
For Copper and Iron yield triplets, scale all three values by user multiplier:
```python
new_value = vanilla_value * user_multiplier
struct.pack_into("<f", data, offset, new_value)  # 4-byte float
```

For RichIron offset 288:
```python
new_value = vanilla_value * user_multiplier
struct.pack_into("<f", data, 288, new_value)
```

**Do not modify** values at the structural constant offsets (242.44, 370.0, 450.0, 125.0) or probability offsets (1.0, 1.1, 0.30).

### Extraction from game paks
Vanilla DA_DigVolume files live in `pakchunk0_s4-Windows.utoc` (AES-encrypted).

```powershell
$AES = "0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE"
$GAME_PAKS = "D:\games\steam\steamapps\common\Windrose\R5\Content\Paks"

# Build combined dir: s4 pak + global (provides script objects)
# Copy to tools\_ref_combined_digvol: global.ucas, global.utoc,
#   pakchunk0_s4-Windows.pak/.ucas/.utoc

tools\retoc\retoc.exe -a $AES to-legacy --version UE5_6 --no-script-objects `
    --filter DA_DigVolume tools\_ref_combined_digvol tools\extracted_digvol
```

Pre-extracted vanilla files should be stored in `tools/extracted_digvol/`.

### Packing to I/O Store
Identical to DA_Segment — pack staging dir (with .uasset + .uexp files) using retoc to-zen:

```powershell
# staging_dir contains: R5/Content/TMP/TunnelProt/**/*.uasset + *.uexp
tools\retoc\retoc.exe to-zen --version UE5_6 staging_dir output_stem.utoc
# Produces: output_stem.pak + output_stem.ucas + output_stem.utoc
```

---

## 3. Generated Mod File Structure

Our generated mod mirrors the community mod pattern exactly:

### Tree/Wood group (4 files)
| File | Contents |
|---|---|
| `MyGameTuningTree_P.pak` | I/O Store container |
| `MyGameTuningTree_P.ucas` | I/O Store data |
| `MyGameTuningTree_P.utoc` | I/O Store TOC |
| `MyGameTuningTreeOther_P.pak` | Tree + herb loot table JSONs |

Tree I/O Store contains: 41 modified `DA_Segment_*` files  
Tree Other pak contains: all `LootTables/Foliage/` JSONs for wood, herbs, hardwood, plague wood

### Mineral group (4 files)
| File | Contents |
|---|---|
| `MyGameTuningMineral_P.pak` | I/O Store container |
| `MyGameTuningMineral_P.ucas` | I/O Store data |
| `MyGameTuningMineral_P.utoc` | I/O Store TOC |
| `MyGameTuningMineralOther_P.pak` | Mineral loot + spawner JSONs |

Mineral I/O Store contains: up to 32 modified `DA_DigVolume_*` files (Copper + Iron — Rock/Sulfur skipped)  
Mineral Other pak contains: all `LootTables/Foliage/DA_LT_Mineral_*` JSONs + `ResourcesSpawners/` JSONs

### Everything else (1 file)
| File | Contents |
|---|---|
| `MyGameTuningOther_P.pak` | Stack sizes, backpack slots, lantern, fast travel, animals, food, fishing, scrap |

---

## 4. Extraction Tools Reference

| Tool | Location | Use case |
|---|---|---|
| `repak` | `tools/repak/repak.exe` | List/pack/unpack **traditional** `.pak` files (JSON mods, downloaded mods) |
| `retoc` | `tools/retoc/retoc.exe` | List/pack/unpack **I/O Store** `.utoc` containers; convert legacy↔zen |
| `retoc to-legacy` | — | Extract `.uasset`+`.uexp` from an I/O Store container |
| `retoc to-zen` | — | Pack a legacy staging dir into I/O Store (`.pak`+`.ucas`+`.utoc`) |
| `UnrealReZen` | `tools/UnrealReZen/UnrealReZen.exe` | Alternative I/O Store packer (game-dir aware, compression options) |
| `UAssetGUI` | `tools/UAssetGUI/UAssetGUI.exe` | GUI viewer for `.uasset`/`.uexp` — inspect field names and values |

### Key retoc commands
```powershell
# List I/O Store container (shows hashes, not paths — use unpack for paths)
retoc.exe list mod.utoc

# Unpack raw chunks — shows actual file paths
retoc.exe unpack mod.utoc output_dir

# Convert I/O Store → legacy (needs global + optional AES key)
retoc.exe [-a AES_KEY] to-legacy --version UE5_6 [--no-script-objects] [--filter NAME] input_dir output_dir

# Convert legacy → I/O Store (used to build our mod segments)
retoc.exe to-zen --version UE5_6 staging_legacy_dir output_stem.utoc

# Show container info
retoc.exe info mod.utoc
```

### Key repak commands
```powershell
# List contents of traditional pak
repak.exe list mod.pak

# Pack a directory into a pak (output is placed next to input dir, not in specified dir)
repak.exe pack --version V8B input_dir
# Then move the resulting .pak to desired location

# Unpack a pak
repak.exe unpack mod.pak output_dir
```

### Extracting from encrypted game paks
Game paks require the AES key. Pass it as the first argument to retoc:
```powershell
$AES = "0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE"
retoc.exe -a $AES to-legacy ...
```

For `to-legacy` to work, the input directory must contain BOTH the target pak AND the game's `global.ucas`/`global.utoc` (script objects). Without global, all assets fail to extract.

---

## 5. Version Compatibility Warning

The MoreMineralResources 6h 2x mod's `.uexp` files are ~4x larger than the current vanilla files, indicating it was built for an older game version. **Do not use the modded DA_DigVolume files as a reference** for current-format binary values. Always extract fresh vanilla files from the current game paks.

If the game patches and vanilla uexp file sizes change, re-extract using the procedure in section 2.
