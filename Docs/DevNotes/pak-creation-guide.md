# Windrose Pak Creation Guide

Everything a developer needs to know to create, unpack, and inspect Windrose mod paks.

---

## How Windrose loads mods

The game scans `<GameRoot>/R5/Content/Paks/~mods/` at startup and loads every `.pak` file it finds. Files are loaded in alphabetical order; later files override earlier ones for the same asset path. The `~` prefix on the folder name ensures it sorts after game content.

**The `~mods/` folder is not created by the game** — you must create it manually if it doesn't exist.

### Pak naming and priority

Windrose follows the standard UE5 convention: a `_P` suffix marks a file as a "patch" pak, which loads with higher priority than base paks. Always name your mods with `_P`:

```
MyMod_P.pak          ← loads after base game content (correct)
MyMod.pak            ← lower priority, may not override correctly
```

Alphabetical sort controls tie-breaking among same-priority paks, so `z_MyMod_P.pak` loads after `a_MyMod_P.pak`.

---

## Two pak formats in Windrose

| Format | Used by | Readable by repak? |
|---|---|---|
| Traditional .pak | Mod paks, some game chunks | Yes |
| I/O Store (.pak + .ucas + .utoc) | Main game chunks | Not directly |

**Mod paks always use traditional format.** If you see a mod with only a `.pak` file, it's traditional. If it ships `.pak + .ucas + .utoc`, the `.ucas`/`.utoc` are I/O Store shards (binary UE5 assets); the separate `*Other_P.pak` or `*_P.pak` file that exists alongside them is the traditional JSON pak.

The encrypted game paks (`pakchunk0-Windows.pak` etc.) use I/O Store and require the AES key to read:
```
0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE
```

---

## repak — the pak tool

`tools/repak/repak.exe` is v0.2.3. Core commands:

```bash
# List contents of a pak
repak list <file.pak>

# Extract all files
repak unpack <file.pak> --output <output_dir>

# Create a pak from a directory (directory name becomes pak name)
repak pack --version V8B <input_dir>
# → writes <input_dir>.pak next to <input_dir>

# Show pak metadata
repak info <file.pak>
```

**Windows quirk:** `repak pack <input> <output_dir>` fails with "Access denied". Always omit the output directory argument — repak creates the pak next to the input folder, then move it where you need it.

### Pak settings for Windrose mods

```
Version:     V8B  (FNameBasedCompression)
Mount point: ../../../
Compression: none  (JSON files don't benefit from it)
Encryption:  none
```

---

## Asset path structure

Inside a mod pak, files follow the game's virtual asset paths. The mount point `../../../` maps the root of the pak to the game's content root, so:

```
pak internal path:   R5/Plugins/R5BusinessRules/Content/InventoryItems/...
real game path:      <GameRoot>/R5/Plugins/R5BusinessRules/Content/InventoryItems/...
```

---

## JSON asset types we modify

All mod JSON files contain a `$type` or `NativeClass` field identifying the UE class.

### R5BLInventoryItem — inventory item definitions

**Path pattern:** `R5/Plugins/R5BusinessRules/Content/InventoryItems/<Category>/<Name>.json`

**Key fields:**
```json
{
  "$type": "R5BLInventoryItem",
  "InventoryItemGppData": {
    "MaxCountInSlot": 50,       ← stack size we modify
    "Weight": 0.5,
    "ItemTag": { "TagName": "ItemData.Resource.CopperOre.T01" },
    "ItemType": { "TagName": "Inventory.ItemType.Resource" },
    "Rarity": "Common",
    "ItemClass": "Default"
  },
  "InventoryItemUIData": {
    "Category": "Resource",     ← UI category ("Resource", "Ammo", "Medicine", etc.)
    "ItemName": { "TableId": "InventoryItems", "Key": "..." }
  }
}
```

**To change stack size:** set `InventoryItemGppData.MaxCountInSlot` to your desired value.

### R5BLLootParams — what drops when you harvest a node

**Path pattern:** `R5/Plugins/R5BusinessRules/Content/LootTables/Foliage/<Name>.json`

```json
{
  "$type": "R5BLLootParams",
  "LootTableType": "List",
  "LootData": [
    {
      "LootItem": "/R5BusinessRules/InventoryItems/DefaultItems/Resource/DA_DID_Resource_Iron_T02.DA_DID_Resource_Iron_T02",
      "Min": 8,     ← minimum drop quantity  (we multiply these)
      "Max": 10,    ← maximum drop quantity
      "Weight": 0
    }
  ]
}
```

**To change loot:** multiply `Min` and `Max` by your desired multiplier. Always keep `Min <= Max` and `>= 1`.

### R5GameplaySpawnerParams — resource node respawning

**Path pattern:** `R5/Content/Gameplay/Actor/SpawnPoints/.../<Name>.json`

```json
{
  "$type": "R5GameplaySpawnerParams",
  "RespawnInterval": {
    "Min": 21600,   ← seconds (21600 = 6 hours)
    "Max": 21600
  },
  "Variants": [
    {
      "Collection": [
        {
          "Amount": { "Min": 1, "Max": 1 }  ← how many actors spawn
        }
      ]
    }
  ]
}
```

**To change respawn:** set `RespawnInterval.Min` and `RespawnInterval.Max` to your desired seconds (`hours × 3600`).  
**To change quantity:** multiply `Amount.Min` and `Amount.Max`.

---

## Creating a pak from scratch

1. Create a staging directory named exactly what you want the pak to be called (e.g., `MyMod_P`)
2. Inside it, recreate the full asset path starting from `R5/`:
   ```
   MyMod_P/
     R5/
       Plugins/R5BusinessRules/Content/InventoryItems/...
   ```
3. Place your modified JSON files in the correct locations
4. Run: `repak pack --version V8B MyMod_P`
5. Move the resulting `MyMod_P.pak` to the game's `~mods/` folder

---

## How our pak_generator.py works

See `CLAUDE.md` for the full algorithm. In short:

1. Reads reference JSON files from `tools/extracted*/` (pre-extracted from community mods)
2. Derives vanilla values: `vanilla = ref_value / ref_multiplier`
3. Applies user settings: `new_value = round(vanilla * user_multiplier)` for loot, or sets directly for stack sizes and respawn times
4. Writes modified files to a temp staging dir
5. Calls repak, moves the pak to `~mods/`
