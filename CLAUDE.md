# BlackFlag Mod Manager — Claude Code Guide

## What this project is
A desktop GUI application (customtkinter) for managing and creating mods for the game **Windrose** (UE 5.6.1, Early Access April 2026, Steam). Two goals:
1. **Mod manager** — install/enable/disable .pak mods for client and dedicated server
2. **Game Tuning creator** — generate custom JSON-only .pak mods that adjust stack sizes, loot drop multipliers (sulfur, stone, clay, soil, obsidian, salt, herbs, food plants, crops, fishing, scrap, animals), backpack slots, fast-travel bell limit, and lantern duration. Features needing binary asset modification (tree/wood/copper/iron/ancient-debris yield) are intentionally out of scope — users install dedicated community mods for those.

## Tech stack
- Python 3.x, customtkinter 5.2.2, py7zr 1.1.0
- `requirements.txt` pins exact stable versions
- Entry point: `main.py` → `ui/app_window.py`

## Project layout
```
core/           Python business logic (no UI imports)
  paths.py          Game path auto-detection via Steam registry
  settings.py       Persist/load data/settings.json
  mod_manager.py    Install/enable/disable .pak mods
  config_manager.py Read/write ServerDescription.json + WorldDescription.json
  pak_generator.py  Generate custom tuning .pak from user settings (KEY FILE)
ui/
  app_window.py     Main window, sidebar nav, 5-tab layout
  tabs/
    installed_tab.py  Manage installed mods
    library_tab.py    Browse mod library, install to client/server
    create_tab.py     Game Tuning page — sliders → pak generation
    config_tab.py     Server/World config JSON editor
    settings_tab.py   Paths configuration
tools/
  repak/repak.exe      Traditional pak tool — list/pack/unpack non-I/O-Store .pak files (JSON mods)
  retoc/retoc.exe      I/O Store tool (inspection only — not used by generator)
  UAssetGUI/           GUI viewer for .uasset/.uexp — inspect UE binary asset field names/values
  extracted/           MoreStacks 100x reference data (380 inventory item JSONs)
  extracted_mineral/   MoreMineralResources 6h 2x reference data (mineral loot + swamp spawner JSONs)
  extracted_tree/      MoreTreeResources 2x reference data (tree/herb loot table JSONs)
data/             Runtime data (gitignored: settings.json)
Docs/
  DevNotes/       Technical guides for developers
  Planning/       Design docs for planned features
```

## Windrose mod system essentials
- Mods are `.pak` files dropped into `R5/Content/Paks/~mods/`
- **The UE pak loader scans every subdirectory under `Content/Paks/`** regardless of folder name — `~mods_disabled/` still gets mounted. To disable a pak, move it OUT of the `Paks/` tree (or rename its extension)
- Game paks use **I/O Store format** (.pak + .ucas + .utoc) and are AES-encrypted
- **Mod paks use traditional (non-I/O Store) .pak format** — unencrypted, repak can read/write them
- AES key: `0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE`
- Mount point for all paks: `../../../`
- Pak version: V8B (FNameBasedCompression), no compression needed for JSON-only mods

## Generated mod structure
The generator produces **three JSON paks** per mod:
- `{base}TreeOther_P.pak` — herb / plant patch loot table JSONs
- `{base}MineralOther_P.pak` — mineral loot table JSONs (sulfur, stone, clay, soil, obsidian, salt)
- `{base}Other_P.pak` — stack sizes, backpack, lantern, fast travel, animal drops, food plants, crops, fishing, scrap

**Why JSON-only?** Binary I/O Store paks (the `.ucas`/`.utoc` containers used to change DA_Segment tree-chop yield and DA_DigVolume mineral-dig yield) require UnrealReZen + the Oodle DLL. Oodle can't be redistributed (Epic/RAD license), and the in-game crash signature from our generated I/O Store paks was difficult to diagnose. Decision (2026-05-17): drop binary mod generation, lean into being a mod manager + JSON tuning generator. Binary mods stay in the modder's domain (Nexus uploads).

**Why no spawners or ancient-debris loot?** Spawner JSONs only exist for swamp ancient-debris nodes in the reference mod (tree/herb/stone/ore spawners can't be modded via JSON at all). And ancient-debris loot scaling — while technically possible via JSON — was dropped alongside the binary cuts since users wanting more mire-metal will just install MoreMineralResources directly. Keeps the UI focused on tuning features that don't already have a single-purpose community mod.

## How pak_generator.py works
The pak generator uses pre-extracted reference mod JSONs as templates, derives vanilla game values by dividing by the reference mod's known multiplier, applies the user's settings, then packs with repak.

**Source data and multipliers:**
| Directory | Source mod | Multiplier | Contains |
|---|---|---|---|
| `tools/extracted/` | MoreStacks 100x | 100× | 380 inventory item JSONs |
| `tools/extracted_mineral/` | MoreMineralResources 6h 2x | 2× loot | mineral loot tables + swamp spawners |
| `tools/extracted_tree/` | MoreTreeResources 2x | 2× loot | tree/herb loot table JSONs |
| `tools/extracted_backpack/` | MoreBackpackSlots 3x | 3× | backpack slot JSONs |
| `tools/extracted_fasttravel/` | FastTravelPlus 50 | absolute | fast-travel building limits |
| `tools/extracted_lantern/` | BetterLanternLonger 2x | 2× | lantern refuel recipe |
| `tools/extracted_vanilla/` | Direct from game paks | 1× (direct) | copper loot + animal drop tables |
| `tools/extracted_allloot/` | 10x All Loot mod | 10× | food plants, crops, fishing, scrap |

**Asset types modified (all JSON):**
1. `R5BLInventoryItem` — `InventoryItemGppData.MaxCountInSlot` set directly from user's category value
2. `R5BLLootParams` — `LootData[].Min` and `LootData[].Max` scaled: `new = round(ref_value * user_mult / ref_mult)`
3. `R5BLSlotCountModifierParams` — backpack `CountSlots` scaled
4. `R5BuildingLimits` — fast-travel `MaxAmount` set directly

## UI conventions
- Color scheme: dark navy (`#0f172a` sidebar), teal accent (`#0d9488`), muted slate text
- All tabs inherit `ctk.CTkFrame` with `fg_color="transparent"`
- Navigation via sidebar; frames shown/hidden with `grid()` / `grid_remove()`
- `app.reload()` destroys and rebuilds all UI (called after settings save)

## Game data JSON formats
See `Docs/DevNotes/pak-creation-guide.md` for complete field reference.

## Things that bit us before
- `repak pack <dir> <output_dir>` fails on Windows with "Access denied" — omit the output dir argument; repak writes next to the input dir, then move the file
- `python3 -c "..."` with pipes in bash on Windows causes goto-error IndentationError — use PowerShell tool or write a temp script file
- repak exits with code 255 even on success for some commands — check for output file, not exit code
- UE scans every subfolder of `Content/Paks/` regardless of name — `~mods_disabled/` still gets mounted. Move paks outside the Paks tree to actually disable them.
