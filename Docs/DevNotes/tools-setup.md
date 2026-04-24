# Tools Setup Guide

How to get and configure the external tools the project depends on.

---

## repak (required)

**What:** UE5 pak tool for listing, extracting, and creating .pak files.  
**Version:** v0.2.3  
**Location:** `tools/repak/repak.exe` (committed to git — no download needed)

If you need to update repak:
1. Download from https://github.com/trumank/repak/releases
2. Extract `repak.exe` to `tools/repak/`

### Verify it works

```bash
tools/repak/repak.exe --version
```

---

## FModel (optional — for exploring encrypted game paks)

**What:** GUI browser for UE5 assets including encrypted I/O Store paks.  
**Version:** Dec 2025 build or later  
**Location:** `tools/FModel/FModel.exe` ← gitignored (44 MB, download separately)

FModel is only needed when you want to browse the game's encrypted asset tree (e.g., to find new item types or verify asset paths). Day-to-day development doesn't require it.

### Download

1. Go to https://fmodel.app (or check GitHub releases: https://github.com/4sval/FModel/releases)
2. Download the latest FModel zip
3. Extract to `tools/FModel/`

### Configure for Windrose

1. Launch FModel
2. Add game: Detection → Manual → select `D:\Games\Steam\steamapps\common\Windrose`
3. Set AES key: Directory → AES → paste the key:
   ```
   0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE
   ```
4. Mappings: Download the `.usmap` file from Nexus Mods mod #60 when available (not yet released as of April 2026)
5. Without a mappings file, FModel can still browse assets but custom types (R5BLInventoryItem, etc.) won't show property names

### What you can do with FModel

- Browse the full asset tree of the encrypted game paks
- Export item icons (textures) and mesh references
- View the raw JSON of any game asset once mappings are available
- Discover new asset types not yet covered by our tool

---

## Reference mod extractions (required for pak generation)

These directories must exist for `pak_generator.generate()` to work. They are committed to git, so a fresh clone should have them automatically.

| Directory | Source | What it contains |
|---|---|---|
| `tools/extracted/` | MoreStacks 100x | 380 inventory item JSONs (all items) |
| `tools/extracted_mineral/` | MoreMineralResources 6h 2x | 32 mineral loot tables + 26 spawner JSONs |
| `tools/extracted_tree/` | MoreTreeResources 2x | 85 tree/herb loot table JSONs |

### Re-extracting if needed

If you need to update these from new mod versions:

```bash
# From the project root
tools/repak/repak.exe unpack "Mods/MoreStacks 100x/MoreStacks_100x_P.pak" --output tools/extracted
tools/repak/repak.exe unpack "Mods/MoreMineralResources 6h 2x/MoreMineralResourcesOther_6h_2x_P.pak" --output tools/extracted_mineral
tools/repak/repak.exe unpack "Mods/MoreTreeResources 2x/MoreTreeResourcesOther_2x_P.pak" --output tools/extracted_tree
```

Note: The `*Other_*_P.pak` suffix is the traditional pak (JSON data). The matching `.ucas`/`.utoc` files are the I/O Store binary shards — ignore those.

---

## Python environment

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.10+ (uses `match/case` and `X | Y` type unions in some places).

### requirements.txt

```
customtkinter==5.2.2
py7zr==1.1.0
```

`py7zr` is available for future archive extraction; not currently used in the main app flow.
