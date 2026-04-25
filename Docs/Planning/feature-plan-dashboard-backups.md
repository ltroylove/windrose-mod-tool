# Windrose Mod Tool — Feature Expansion Plan
## Dashboard, Backups, Activity Log, Launch Game, Open Folder Shortcuts

---

## Context

After comparing our tool against the competing "Windrose Mod Manager v0.6.1" (Nexus mod #29), we identified several high-value features it has that we don't: automatic backups before destructive operations, an activity/history log, a Dashboard with quick actions, and a persistent "Launch Game" button. We also noticed the Settings tab lacks "Open in Explorer" shortcuts next to each path, which that app does well. Our key differentiator remains the Game Tuning creator (they have nothing like it). This plan adds the missing quality-of-life features in a way that fits our style.

**Triggered by:** User comparison session 2026-04-25.  
**Goal:** Ship all 6 features in a single implementation pass.

---

## Current State (What Exists)

| File | Relevant State |
|---|---|
| `ui/tabs/home_tab.py` | Has game-status card, 3 stat tiles (Installed/Enabled/Library), 3 feature-nav cards. No quick actions, no activity, no launch button. |
| `ui/tabs/settings_tab.py` | Three path fields (game_path, library_path, my_mods_path) each with Browse button. No Open/Validate. Auto-detect exists as a button action. |
| `ui/app_window.py` | Status bar shows counts only. No Launch button anywhere. Build order: header → sidebar → statusbar → content → nav. |
| `core/paths.py` | `GamePaths` has: client_paks, client_mods, server_root, server_paks, server_mods, server_description, find_world_configs(), is_valid(). No exe path property. |
| `core/mod_manager.py` | install/uninstall/enable/disable — no logging or backup hooks. |
| `core/settings.py` | load()/save(), DEFAULTS: game_path="", library_path=Mods/, my_mods_path=MyMods/ |
| `data/` | Only `settings.json`. No backups/, no activity.json. |

---

## Features to Implement

### 1. `core/activity_log.py` — New file
Simple append-only JSON log. Needed by backup manager and UI features.

```python
# Entry schema
{"ts": "2026-04-25T10:30:00", "action": "mod_installed", "detail": "MyMod"}

# Actions:
# mod_installed, mod_removed, mod_enabled, mod_disabled
# tuning_generated, backup_created, restore_performed
```

**Functions:**
- `log_action(action: str, detail: str) -> None` — appends entry to `data/activity.json`, creates file if absent
- `load_recent(n: int = 50) -> list[dict]` — returns last N entries in reverse-chronological order

**Storage:** `data/activity.json` — JSON array, appended to (read-all, append, write-all pattern to avoid line-by-line parsing complexity).

---

### 2. `core/backup_manager.py` — New file

```python
@dataclass
class BackupEntry:
    ts: str           # "2026-04-25T10:30:00"
    path: Path        # data/backups/mods_20260425_103000.zip
    tag: str          # human description ("before remove MyMod")
    file_count: int
```

**Class `BackupManager`:**
- `__init__(self, backup_dir: Path)` — `backup_dir = DATA_DIR / "backups"`
- `backup_mods(mods_dir: Path, tag: str) -> BackupEntry` — zips all files in mods_dir → timestamped file in backup_dir, calls `activity_log.log_action("backup_created", tag)`, returns BackupEntry
- `list_backups() -> list[BackupEntry]` — scans backup_dir for `*.zip`, parses metadata from filename, returns sorted newest-first
- `restore(entry: BackupEntry, mods_dir: Path) -> None` — clears mods_dir, extracts zip, logs restore
- `prune(keep: int = 10) -> None` — deletes oldest backups beyond `keep` limit

**Filename format:** `mods_YYYYMMDD_HHMMSS.zip` (tag stored inside zip as `_backup_meta.txt`)

**When called:**
- `InstalledTab._remove()` — backup before uninstall (only if mods_dir has files)
- `LibraryTab._deploy_package()` — backup before overwrite install

---

### 3. `core/paths.py` — Add `client_exe` property

```python
@property
def client_exe(self) -> Path | None:
    """Return the Windrose client executable path, or None if not found."""
    candidates = [
        self.game_root / "R5.exe",
        self.game_root / "Windrose.exe",
        self.game_root / "R5" / "Binaries" / "Win64" / "R5-Win64-Shipping.exe",
    ]
    return next((p for p in candidates if p.exists()), None)
```

---

### 4. `ui/app_window.py` — Auto-detect first run + Launch button

**Auto-detect on first run** in `_init_services()`:
```python
if not game_str:
    found = find_game_path()
    if found:
        s["game_path"] = str(found)
        cfg.save(s)
        game_str = str(found)
```

**Launch button** in `_build_statusbar()` (right-aligned):
```python
ctk.CTkButton(bar, text="▶  Launch Windrose", width=150, height=22,
    fg_color=ACCENT, hover_color=ACCENT_HOVER, font=ctk.CTkFont(size=10),
    command=self._launch_game,
).pack(side="right", padx=8, pady=2)

def _launch_game(self):
    import subprocess
    exe = self.game_paths.client_exe if self.game_paths else None
    if exe:
        subprocess.Popen([str(exe)], cwd=str(exe.parent))
```

Only shown when `game_paths` is valid and `client_exe` is found.

---

### 5. `ui/tabs/settings_tab.py` — Open + Validate

**"Open" button** (column 3) next to each Browse (column 2):
```python
ctk.CTkButton(card, text="Open", width=60, height=32,
    fg_color="#1e293b", hover_color="#334155",
    command=lambda k=key: self._open_folder(k)
).grid(row=i+2, column=3, padx=(0, 16), pady=8)

def _open_folder(self, key: str):
    path = self._vars[key].get()
    if path and Path(path).exists():
        os.startfile(path)
```

**"Validate" button** next to Save Settings in the actions row:
```python
def _validate(self):
    labels = {"game_path": "Game Folder", "library_path": "Downloads", "my_mods_path": "Tuning Paks"}
    parts = []
    for key, lbl in labels.items():
        p = self._vars[key].get()
        ok = bool(p) and Path(p).exists()
        parts.append(f"{'✓' if ok else '✗'} {lbl}")
    self._status.configure(text="   ".join(parts), text_color="#6ee7b7")
```

---

### 6. `ui/tabs/home_tab.py` — Dashboard enhancements

Enhance `_render()` to insert between stat tiles and feature cards:

**a) Quick Actions row** — 4 buttons:
- `▶ Launch Windrose` — `app._launch_game()`
- `📁 Client Mods` — `os.startfile(app.game_paths.client_mods)`
- `📁 MyMods` — `os.startfile(Path(cfg.load()["my_mods_path"]))`
- `💾 Back Up Now` — creates backup, refreshes activity

**b) Recent Activity card**:
- Calls `activity_log.load_recent(5)`
- Each entry: coloured action label + detail + relative timestamp
- "No activity yet" when empty

**c) 4th stat tile** — "Last Backup":
- Reads `BackupManager(...).list_backups()`
- Shows "Never" or relative time (e.g. "2h ago")

---

### 7. Integrate activity logging in existing tabs

**`ui/tabs/installed_tab.py`:**
- `_remove()`: backup mods dir, then `activity_log.log_action("mod_removed", mod.name)`
- `_toggle()`: `activity_log.log_action("mod_enabled"/"mod_disabled", mod.name)`

**`ui/tabs/library_tab.py`:**
- `_deploy_package()` before overwrite: `BackupManager(...).backup_mods(...)`
- After install: `activity_log.log_action("mod_installed", pkg.name)`

**`ui/tabs/create_tab.py`:**
- After successful generate: `activity_log.log_action("tuning_generated", pak_name)`

---

## File Change Summary

| File | Change Type | Notes |
|---|---|---|
| `core/activity_log.py` | **NEW** | Append-only JSON log |
| `core/backup_manager.py` | **NEW** | Zip backups of ~mods, restore support |
| `core/paths.py` | Edit | Add `client_exe` property |
| `ui/app_window.py` | Edit | Auto-detect first run, `_launch_game()`, statusbar button |
| `ui/tabs/home_tab.py` | Edit | Quick Actions, Recent Activity card, 4th stat tile |
| `ui/tabs/settings_tab.py` | Edit | Open buttons (col 3), Validate button |
| `ui/tabs/installed_tab.py` | Edit | backup + activity log in _remove(), _toggle() |
| `ui/tabs/create_tab.py` | Edit | activity log on successful generation |
| `ui/tabs/library_tab.py` | Edit | backup before overwrite, activity on install |

---

## Implementation Order

1. `core/activity_log.py` — foundation, no dependencies
2. `core/backup_manager.py` — depends on activity_log
3. `core/paths.py` — add client_exe (standalone)
4. `ui/app_window.py` — auto-detect first run, _launch_game(), statusbar button
5. `ui/tabs/settings_tab.py` — Open buttons, Validate button
6. `ui/tabs/installed_tab.py` — backup + activity in remove/toggle
7. `ui/tabs/library_tab.py` — backup before overwrite, activity on install
8. `ui/tabs/create_tab.py` — activity log on generate
9. `ui/tabs/home_tab.py` — Dashboard: Quick Actions, Recent Activity, 4th stat tile

---

## Verification

1. **First run auto-detect:** Delete `data/settings.json`, restart app → game path auto-filled if Steam found
2. **Launch button:** Click "▶ Launch Windrose" in status bar → Windrose opens
3. **Open folder:** Settings → Open next to Game Folder → Explorer opens at game path
4. **Validate:** Settings → Validate → shows ✓/✗ for each path
5. **Backup on remove:** Install a test mod → Remove it → check `data/backups/` for zip → verify contents
6. **Activity log:** Perform install/remove/generate → check `data/activity.json` entries
7. **Dashboard Quick Actions:** Home tab → click Back Up Now → backup created, activity updates
8. **Dashboard Recent Activity:** Shows last 5 actions with timestamps
