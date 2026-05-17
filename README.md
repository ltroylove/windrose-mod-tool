# BlackFlag Mod Manager

A desktop GUI application for managing and creating mods for **Windrose** (Early Access, Steam).

> **Note:** This is our first modding project, so not everything may work as expected. It is still actively being developed and improved.

## Features

- **Mod Manager** — install, enable, and disable `.pak` mods for the client and dedicated server
- **Game Tuning Creator** — generate custom JSON-only `.pak` mods that adjust stack sizes, loot drop multipliers (fiber, stone, sulfur, clay, salt, herbs, crops, fishing, scrap, animal drops, and more), backpack slots, fast-travel bell limit, and lantern duration
- **Mod Library** — unified library for downloaded and generated mods, with optional FTP deployment to a dedicated server
- **Backup System** — automatic backups of your `~mods/` folder before any destructive operation
- **Activity Log** — persistent history of every install, remove, enable, disable, and generation
- **Dashboard** — quick actions, recent activity, and one-click game launch

## Requirements

- Python 3.10+
- Windows 10/11
- Windrose installed via Steam

## Setup

```bash
pip install -r requirements.txt
python main.py
```

On first launch, the tool will attempt to auto-detect your Windrose installation via the Steam registry. If not found, set the path manually in **Settings**.

## Project Structure

```
core/           Business logic (no UI imports)
ui/             customtkinter GUI
  tabs/         One file per tab
tools/          repak.exe and extracted reference data
data/           Runtime data (gitignored)
Docs/           Developer notes and planning docs
```

## How It Works

The Game Tuning Creator applies your chosen multipliers to vanilla game values and repacks them into a set of JSON `.pak` mods using [repak](https://github.com/trumank/repak). Each generated mod produces up to three paks (`*Other_P.pak`, `*MineralOther_P.pak`, `*TreeOther_P.pak`) — only the groups whose values differ from vanilla are written.

Supported tuning categories: stack sizes (per item type), loot drop multipliers (sulfur, stone, clay, soil, obsidian, salt, herbs, food plants, crops, fishing, scrap, animal drops), backpack slots, fast-travel bell limit, and lantern burn duration.

For features that require binary asset edits (base wood-per-chop, base ore-per-dig, ancient-debris spawner timing), install the dedicated community mods from Nexus — that's outside this tool's scope.

## License

This project is licensed under the **GNU General Public License v3.0** — see [LICENSE](LICENSE) for details.

Any distributed modifications must also be released under GPL v3.
