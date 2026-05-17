# v0.1.2 — Crash fix, server management, and tighter scope

**Headline:** generated Game Tuning mods now load cleanly. Earlier builds could trigger an in-game crash after deployment; that path has been replaced with a focused JSON-only generator.

## What's new

- **Generated mods no longer crash the game.** The crash-prone path has been removed entirely. Anything Game Tuning produces in v0.1.2 will load cleanly.
- **Manage Remote** — new Library tab dialog that lists every mod currently on your dedicated server (via FTP) and lets you bulk-delete the ones you no longer want. Runs on a worker thread with a per-file progress counter, so the UI doesn't freeze on slow servers.
- **Vanilla means vanilla.** Each Game Tuning slider that's left at its vanilla value writes nothing for that category — your generated pak only contains the values you actually changed, and the game uses its own values for the rest. (Previously, a 1.0× multiplier could still produce a no-op pak that subtly shifted some loot tables; that's fixed.)
- **Better Library badges.** Disabled paks now correctly show the Client / Server "deployed" indicators, and loose `.pak` files at the library root show their own name instead of the parent folder.
- **FTP polish.** Test Connection runs on a worker thread; the Settings tab shows a clear warning if the OS credential store isn't available so you'll know why a password isn't persisting.
- **Smaller fixes:** re-enabling a disabled mod actually re-enables it; switching between Relaxed and Abundant presets resets every slider (no stale values); the post-generation success dialog only names paks it actually wrote; ghost mods with deleted files no longer linger as "enabled."

## Tightened scope

The Game Tuning Creator now focuses on the categories that work cleanly with JSON-only mods: stack sizes, loot drops (fiber, stone, sulfur, clay, soil, obsidian, salt, herbs, food plants, crops, fishing, scrap piles, animal drops), backpack slot count, fast-travel bell limit, and lantern burn duration.

For features that need direct binary asset edits — base wood-per-chop, base ore-per-dig, resource respawn timing — install the dedicated community mods (e.g. MoreTreeResources, MoreMineralResources) alongside this manager. Both work together; the manager will install them to client and server for you.

## File

`BlackFlagModManager.exe` — standalone Windows executable. Place it anywhere and run.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
