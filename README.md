# Windrose Mod Tool

A desktop GUI application for managing and creating mods for **Windrose** (Early Access, Steam).

## Features

- **Mod Manager** — install, enable, and disable `.pak` mods for the client and dedicated server
- **Game Tuning Creator** — generate custom `.pak` mods that adjust stack sizes, loot drop multipliers, and resource spawner timing
- **Mod Library** — unified library for downloaded and generated mods
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

The Game Tuning Creator uses pre-extracted JSON files from reference mods as templates, derives vanilla values by dividing by the reference mod's known multiplier, applies your chosen multipliers, then repacks with [repak](https://github.com/trumank/repak).

Supported tuning categories: stack sizes, loot (wood, fiber, stone, ore, minerals, crops, food plants, herbs, scrap, fishing), and resource spawner respawn timing.

## License

This project is licensed under the **GNU General Public License v3.0** — see [LICENSE](LICENSE) for details.

Any distributed modifications must also be released under GPL v3.
