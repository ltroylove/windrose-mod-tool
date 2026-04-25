# Vanilla Asset Extraction

How we extract vanilla game JSON assets directly from the encrypted game paks using `repak`.
Run this whenever the game patches to refresh the baseline values.

---

## Quick re-extraction (after a game update)

```bash
python tools/extract_vanilla.py
```

The script reads `data/settings.json` for the game path, scans all pakchunks with
the AES key, and writes matching assets to `tools/extracted_vanilla/`.  
Existing files are skipped — delete the folder first if you want a full refresh:

```bash
rm -rf tools/extracted_vanilla/
python tools/extract_vanilla.py
```

---

## What the script extracts

| Asset prefix | Count (v0.1) | Purpose |
|---|---|---|
| `R5/Content/Gameplay/Actor/SpawnPoints/A2_Spawners/ResourcesSpawners/` | 58 | Spawner configs — respawn timers + quantity variants |
| `R5/Plugins/R5BusinessRules/Content/LootTables/Foliage/DA_LT_Mineral*` | 38 | Mineral node loot tables (copper, iron, stone, sulfur, ancient debris, …) |
| `R5/Plugins/R5BusinessRules/Content/LootTables/Mobs/` | 358 | Mob/animal drop tables (boar, dodo, crab, wolf, …) |

All assets live in `pakchunk0-Windows.pak`. The `_s1` through `_s4` shards contain no
matching assets as of v0.1.

---

## Technical details

### Why repak works here

The game paks use **I/O Store format** (`.pak` + `.ucas` + `.utoc`).  
Normally this requires FModel (CUE4Parse) to read. However, the `.pak` portion of
Windrose's I/O Store paks **also embeds the JSON data assets in legacy pak format**
alongside the I/O Store index. `repak` can read and extract these directly using the
AES key — no FModel needed.

### AES key

```
0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE
```

### Manual extraction (single file)

```bash
tools/repak/repak.exe -a 0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE \
  get "D:\games\steam\steamapps\common\Windrose\R5\Content\Paks\pakchunk0-Windows.pak" \
  "R5/Plugins/R5BusinessRules/Content/LootTables/Foliage/DA_LT_Mineral_Copper_01.json"
```

### Manual listing (find new asset paths)

```bash
tools/repak/repak.exe -a 0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE \
  list "D:\games\steam\steamapps\common\Windrose\R5\Content\Paks\pakchunk0-Windows.pak" \
  | grep "LootTables"
```

---

## Vanilla values reference

### Copper node loot (`DA_LT_Mineral_Copper_01.json`)

```json
{ "Min": 1, "Max": 2 }
```

Drops 1–2 Copper Ore per node hit. One file covers all copper node variants.

### Animal drops (Mobs/Rss/ sub-tables)

Animal loot uses a two-level structure:
- **`Mobs/DA_LT_Mob_Boar_Final.json`** — master table, references sub-tables via `LootTable`
- **`Mobs/Rss/DA_LT_Mob_Boar_Leather.json`** etc. — leaf tables with actual `Min`/`Max`

All vanilla leaf tables have `Min: 1, Max: 1`. Scaling requires modifying the leaf
tables (in `Mobs/Rss/`), not the master Final tables.

Animals with drop tables:
- Boar — Leather, Meat, Fat, Tusk, BoarHead
- BoarMega — same categories
- Dodo / DodoF — Meat, Feather, Egg
- Crab / DrownedCrab — CrabMeat, CrabClaw
- Wolf / AlphaWolf — Leather, Meat, Fang

### Spawner respawn intervals

`RespawnInterval.Min` and `.Max` are in **seconds**.

| Spawner file | Node type | Vanilla interval |
|---|---|---|
| `DA_ResSpawner_CJ_Clay_Single.json` | Clay | 4 h (14400 s) |
| `DA_ResSpawner_SW_BigBrokenStatue_*.json` | Ancient Debris (Big) | see file |
| `DA_ResSpawner_SW_BrokenStatue_*.json` | Ancient Debris | see file |
| `DA_ResSpawner_SW_RootedMetall_*.json` | Ancient Metal | see file |

> **Note:** Iron, copper, stone, and tree spawners were not found in extracted data —
> these node types may use per-biome level streaming or inline spawner configs rather
> than standalone `R5GameplaySpawnerParams` assets. The spawner slider will save the
> user's value but no pak output will be generated for those types until the asset
> paths are confirmed.

---

## Adding new asset types to the extractor

Edit `WANTED_PREFIXES` in `tools/extract_vanilla.py`:

```python
WANTED_PREFIXES = [
    "R5/Content/Gameplay/Actor/SpawnPoints/A2_Spawners/ResourcesSpawners/",
    "R5/Plugins/R5BusinessRules/Content/LootTables/Foliage/DA_LT_Mineral",
    "R5/Plugins/R5BusinessRules/Content/LootTables/Mobs/",
    # Add new prefixes here
]
```

Then re-run the script. Already-extracted files are skipped automatically.
