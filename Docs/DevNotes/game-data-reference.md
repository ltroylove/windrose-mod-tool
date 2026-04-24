# Windrose Game Data Reference

Key paths, formats, and values needed when working with Windrose game data.

---

## Game installation

Default Steam path: `D:\Games\Steam\steamapps\common\Windrose`  
The app auto-detects this via the Windows registry key:  
`HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 3277370`

### Key directories

| Path (relative to game root) | Contents |
|---|---|
| `R5/Content/Paks/` | Game pak files |
| `R5/Content/Paks/~mods/` | Mod pak drop folder (create manually) |
| `R5/Builds/WindowsServer/` | Dedicated server files |
| `R5/Builds/WindowsServer/R5/Content/Paks/~mods/` | Server mod folder |

---

## Server configuration files

### ServerDescription.json

**Path:** `R5/Builds/WindowsServer/R5/ServerDescription.json`

Controls server lobby settings. Key fields:

```json
{
  "Parameters": [
    { "TagName": "ServerConfig.MaxPlayers",       "Value": "6" },
    { "TagName": "ServerConfig.ServerName",        "Value": "My Server" },
    { "TagName": "ServerConfig.ServerPassword",    "Value": "" },
    { "TagName": "ServerConfig.IsPublic",          "Value": "true" },
    { "TagName": "ServerConfig.PVP",               "Value": "false" }
  ]
}
```

### WorldDescription.json

**Path:** `R5/Builds/WindowsServer/R5/Maps/<WorldName>/WorldDescription.json`

One file per game world/island. Controls world rules. Key fields:

```json
{
  "Parameters": [
    { "TagName": "WorldConfig.DayDuration",        "Value": "1800" },
    { "TagName": "WorldConfig.NightDuration",      "Value": "600" },
    { "TagName": "WorldConfig.HarvestMultiplier",  "Value": "1.0" },
    { "TagName": "WorldConfig.XPMultiplier",       "Value": "1.0" }
  ]
}
```

---

## Game pak encryption

The main game paks are encrypted with AES-256:

```
Key: 0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE
```

Use this key with FModel or aes-capable repak commands to browse encrypted content. Mod paks are NOT encrypted.

---

## Asset naming conventions

Windrose uses consistent prefixes for Data Assets:

| Prefix | Meaning | Example |
|---|---|---|
| `DA_` | Data Asset | `DA_DID_Resource_Wood_T01` |
| `DA_DID_` | Default Item Data | `DA_DID_Resource_Wood_T01` |
| `DA_AID_` | Ammo Item Data | `DA_AID_Ammo_Cannonball_T01` |
| `DA_CID_` | Consumable Item Data | `DA_CID_Alchemy_Potion_Healing_T01` |
| `DA_LT_` | Loot Table | `DA_LT_Mineral_Iron_01` |
| `DA_ResSpawner_` | Resource Spawner | `DA_ResSpawner_SW_BrokenStatue_A` |

### Biome codes in spawner names

| Code | Biome |
|---|---|
| `SW_` | Swamp (Cursed Swamp) |
| `CJ_` | Coastal Jungle |
| `FH_` | Foothills |
| `VL_` | Volcanic |
| `AL_` or `Ashlands_` | Ashlands |

### Tier naming

Items follow `_T01` through `_T04` tier suffixes (see `item-database.md`).

---

## Known moddable asset paths

All paths are pak-internal (relative to mount point `../../../`).

### Inventory items
```
R5/Plugins/R5BusinessRules/Content/InventoryItems/
  Ammo/          ← ammunition
  Consumables/
    Alchemy/     ← potions, elixirs, bandages
    Food/        ← cooked food
    SeaTrade/    ← trade goods
  DefaultItems/
    Misc/        ← keys, quest items, loot bags
    NPC/         ← NPC-specific items
    Resource/    ← all raw materials, metals, crafting materials
```

### Loot tables
```
R5/Plugins/R5BusinessRules/Content/LootTables/
  Foliage/       ← tree and mineral node loot tables
    Sub_tables/  ← nested loot tables referenced by parent tables
  Enemies/       ← enemy drop tables (not yet modded)
  Chests/        ← chest loot tables (not yet modded)
```

### Resource spawners
```
R5/Content/Gameplay/Actor/SpawnPoints/
  A2_Spawners/
    ResourcesSpawners/   ← node respawn configs (swamp biome covered)
```

---

## UE class → JSON type mapping

| UE Class | JSON `$type` | What it controls |
|---|---|---|
| `R5BLInventoryItem` | `R5BLInventoryItem` | Item properties, stack sizes |
| `R5BLLootParams` | `R5BLLootParams` | Drop quantities from a node |
| `R5GameplaySpawnerParams` | `R5GameplaySpawnerParams` | Node respawn timing and counts |

The `NativeClass` field in each JSON also identifies the class:  
```
/Script/CoreUObject.Class'/Script/R5BusinessRules.R5BLInventoryItem'
```
