# Windrose Mod Tool — Claude Code Guide

## What this project is
A desktop GUI application (customtkinter) for managing and creating mods for the game **Windrose** (UE 5.6.1, Early Access April 2026, Steam). Two goals:
1. **Mod manager** — install/enable/disable .pak mods for client and dedicated server
2. **Game Tuning creator** — generate custom .pak mods that adjust stack sizes, loot drop multipliers, and resource spawner timing

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
  repak/repak.exe   UE pak tool (v0.2.3) — list/unpack/pack .pak files
  extracted/        MoreStacks 100x reference data (380 inventory item JSONs)
  extracted_mineral/ MoreMineralResources 2x reference data (loot + spawner JSONs)
  extracted_tree/   MoreTreeResources 2x reference data (loot table JSONs)
data/             Runtime data (gitignored: settings.json)
Docs/
  DevNotes/       Technical guides for developers
  Planning/       Design docs for planned features
```

## Windrose mod system essentials
- Mods are `.pak` files dropped into `R5/Content/Paks/~mods/` (must create the folder)
- Game paks use **I/O Store format** (.pak + .ucas + .utoc) and are AES-encrypted
- **Mod paks use traditional (non-I/O Store) .pak format** — unencrypted, repak can read/write them
- AES key: `0x5F430BF9FEF2B0B91B7C79C313BDAF291BA076A1DAB5045974186333AA16CFAE`
- Mount point for all paks: `../../../`
- Pak version: V8B (FNameBasedCompression), no compression needed for JSON-only mods

## How pak_generator.py works
The pak generator uses pre-extracted reference mod JSONs as templates, derives vanilla game values by dividing by the reference mod's known multiplier, applies the user's settings, then packs with repak.

**Source data and multipliers:**
| Directory | Source mod | Multiplier | Contains |
|---|---|---|---|
| `tools/extracted/` | MoreStacks 100x | 100× | 380 inventory item JSONs |
| `tools/extracted_mineral/` | MoreMineralResources 6h 2x | 2× loot | mineral loot tables + swamp spawners |
| `tools/extracted_tree/` | MoreTreeResources 2x | 2× loot | tree/herb loot table JSONs |

**Three asset types modified:**
1. `R5BLInventoryItem` — `InventoryItemGppData.MaxCountInSlot` set directly from user's category value
2. `R5BLLootParams` — `LootData[].Min` and `LootData[].Max` scaled: `new = round(ref_value * user_mult / ref_mult)`
3. `R5GameplaySpawnerParams` — `RespawnInterval.{Min,Max}` set to `hours × 3600`; `Variants[].Collection[].Amount.{Min,Max}` scaled by quantity multiplier

**Limitations (no reference mods for these):**
- Copper node loot is not in the mineral mod's scope
- Spawner JSONs only exist for Swamp biome ancient debris nodes; tree/herb/stone/ore spawners aren't moddable via this mechanism

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
