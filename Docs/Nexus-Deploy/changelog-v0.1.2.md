# v0.1.2 — Game Tuning scope cut & UX polish

**Why this update:** The previous build's Game Tuning generator tried to mod binary tree-chop and mineral-dig yields by repacking the game's encrypted I/O Store containers. That path caused deterministic in-game crashes that were hard to diagnose, and shipping it required redistributing the Oodle DLL (which Epic's license doesn't allow). The fix is a deliberate scope cut: the tool is now a focused mod manager + JSON tuning generator, and the binary stuff is left to the dedicated community mods.

## What's new

- **No more crashes from generated mods.** Removed every code path that produced binary I/O Store paks (`.ucas`/`.utoc`). Generated mods are now JSON-only and load cleanly.
- **Honest "vanilla" handling.** If a slider sits at its vanilla value, no file is written for that category — your generated pak only changes what you actually changed, and the game uses its own values for the rest. (This also closes a silent bug where leaving a multiplier at 1.0 was sneakily halving loot drops.)
- **Trimmed Game Tuning UI.** Removed the misleading "Vanilla" preset (vanilla varies per item inside a category — picking it actually changed a lot of things). Removed the Spawners section entirely (only swamp ancient-debris was wireable in JSON, and MoreMineralResources covers that better). Removed the tree-chop / copper / iron loot sliders (those need binary asset edits — install MoreTreeResources or MoreMineralResources for those).
- **Fast Travel vanilla corrected to 10 bells** (was guessed at 5).
- **Library tab fixes.** Disabled paks now correctly show the C/S "deployed" badges. Loose legacy paks in the library root show their own name instead of the library folder name. Generated mods consisting only of loot paks (no Other_P) are no longer hidden from the Library.
- **Manage Remote.** New dialog for listing and bulk-deleting mods from a dedicated server via FTP. Runs on a worker thread with a per-file progress counter on the Delete button.
- **FTP & keyring polish.** FTP passwords are stored in the OS credential store (Windows Credential Manager) instead of `settings.json`. Test Connection now runs on a worker thread so the UI doesn't freeze on slow servers. The Settings tab warns when the credential store isn't available so the failure mode is discoverable.
- Lots of smaller fixes: `enable()` actually re-enables disabled paks now, `_apply_preset` no longer leaves stale slider values when switching between presets, success-dialog stops naming pak files that weren't written, frozen `--windowed` builds no longer crash on import when `sys.stderr` is `None`, and more.

## Known limitations

- The tool does **not** mod base wood-per-chop, base ore-per-dig, or resource respawn timing. Those require binary asset edits and are intentionally out of scope. Install **MoreTreeResources**, **MoreMineralResources**, etc. for those features.
- FTP is currently plain (unencrypted) FTP. FTPS support is on the roadmap — until then, treat the FTP password as visible on the wire.

## File

`BlackFlagModManager.exe` — standalone, no installer, no extra dependencies. Just place it anywhere on your PC and run it.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
