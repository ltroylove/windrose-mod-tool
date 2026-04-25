import customtkinter as ctk
from tkinter import messagebox

from core import activity_log
from core.backup_manager import BackupManager
from ui.theme import ACCENT

COL_STAT  = 100
COL_FILES = 70
COL_ACT   = 170


class InstalledTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._sort_col = "name"
        self._sort_rev = False
        self._hdr_btns: dict[str, ctk.CTkButton] = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── toolbar ──────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        toolbar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            toolbar, text="Installed Mods",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.grid(row=0, column=2, sticky="e")
        ctk.CTkButton(btn_frame, text="Enable All",  width=90, height=30, command=self._enable_all).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Disable All", width=90, height=30, command=self._disable_all).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Refresh",     width=80, height=30, command=self.refresh).pack(side="left", padx=4)

        # ── unified scroll frame — header (row 0) + data share one grid
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)           # name expands
        self.scroll.grid_columnconfigure(1, minsize=COL_STAT)
        self.scroll.grid_columnconfigure(2, minsize=COL_FILES)
        self.scroll.grid_columnconfigure(3, minsize=COL_ACT)

        self._build_header()
        self.refresh()

    # ── header ────────────────────────────────────────────────────────

    def _build_header(self):
        kw = dict(
            fg_color="#1e293b", hover_color="#334155",
            text_color="#475569", font=ctk.CTkFont(size=11),
            anchor="w", corner_radius=0, height=32, border_width=0,
        )
        for col_idx, (key, label) in enumerate(
            [("name", "MOD NAME"), ("status", "STATUS"), ("file_count", "FILES")],
        ):
            btn = ctk.CTkButton(
                self.scroll, text=self._hdr_text(key, label),
                command=lambda k=key, l=label: self._sort_by(k, l),
                **kw,
            )
            btn.grid(row=0, column=col_idx, sticky="nsew")
            if col_idx == 0:
                btn._text_label.configure(padx=12)
            self._hdr_btns[key] = btn

        ctk.CTkLabel(
            self.scroll, text="ACTIONS", fg_color="#1e293b", height=32,
            text_color="#475569", font=ctk.CTkFont(size=11), anchor="center",
        ).grid(row=0, column=3, sticky="nsew")

    def _hdr_text(self, key: str, label: str) -> str:
        if self._sort_col != key:
            return label
        return label + (" ▼" if self._sort_rev else " ▲")

    def _sort_by(self, key: str, label: str):
        if self._sort_col == key:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = key
            self._sort_rev = False
        for k, lbl in [("name", "MOD NAME"), ("status", "STATUS"), ("file_count", "FILES")]:
            if k in self._hdr_btns:
                self._hdr_btns[k].configure(text=self._hdr_text(k, lbl))
        self._redraw()

    # ── data ──────────────────────────────────────────────────────────

    def refresh(self):
        self._redraw()
        if hasattr(self.app, "_refresh_status"):
            self.app._refresh_status()

    def _redraw(self):
        # destroy all grid children except row 0 (header)
        for w in self.scroll.winfo_children():
            info = w.grid_info()
            if info and int(info.get("row", 0)) > 0:
                w.destroy()

        if not self.app.mod_manager:
            self._empty("Configure your game path in Settings to get started.")
            return

        mods = self.app.mod_manager.list_installed()
        if not mods:
            self._empty("No mods installed yet.\n\nGo to  Library  to install mods from your collection.")
            return

        key_fn = {
            "name":       lambda m: m.name.lower(),
            "status":     lambda m: (0 if m.enabled else 1),
            "file_count": lambda m: m.file_count,
        }.get(self._sort_col, lambda m: m.name.lower())
        mods = sorted(mods, key=key_fn, reverse=self._sort_rev)

        for i, mod in enumerate(mods):
            self._row(mod, grid_row=i + 1)

    def _empty(self, msg: str):
        ctk.CTkLabel(
            self.scroll, text=msg,
            text_color="#475569", justify="center",
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, columnspan=4, pady=50)

    def _row(self, mod, grid_row: int):
        bg = "#1a1f2e" if grid_row % 2 == 0 else "transparent"

        # name
        name_lbl = ctk.CTkLabel(
            self.scroll, text=mod.name, height=40,
            anchor="w", fg_color=bg, font=ctk.CTkFont(size=13),
        )
        name_lbl._label.configure(padx=12)
        name_lbl.grid(row=grid_row, column=0, sticky="nsew", pady=1)

        # status badge
        badge_color = "#064e3b" if mod.enabled else "#1f2937"
        badge_text  = "Enabled"  if mod.enabled else "Disabled"
        badge_fg    = "#6ee7b7"  if mod.enabled else "#6b7280"
        stat_cell = ctk.CTkFrame(self.scroll, fg_color=bg, height=40)
        stat_cell.grid(row=grid_row, column=1, sticky="nsew", pady=1)
        stat_cell.grid_propagate(False)
        badge = ctk.CTkFrame(stat_cell, fg_color=badge_color, corner_radius=4)
        badge.place(relx=0.0, rely=0.5, anchor="w", x=6)
        ctk.CTkLabel(
            badge, text=badge_text, text_color=badge_fg,
            font=ctk.CTkFont(size=11),
        ).pack(padx=8, pady=3)

        # file count
        ctk.CTkLabel(
            self.scroll, text=str(mod.file_count), height=40,
            anchor="w", fg_color=bg, text_color="#6b7280",
            font=ctk.CTkFont(size=12),
        ).grid(row=grid_row, column=2, sticky="nsew", pady=1)

        # action buttons
        act_cell = ctk.CTkFrame(self.scroll, fg_color=bg, height=40)
        act_cell.grid(row=grid_row, column=3, sticky="nsew", pady=1)
        act_cell.grid_propagate(False)

        toggle_txt = "Disable" if mod.enabled else "Enable"
        toggle_fg  = "#1e293b" if mod.enabled else ACCENT
        ctk.CTkButton(
            act_cell, text=toggle_txt, width=72, height=28,
            fg_color=toggle_fg, hover_color="#0f766e" if not mod.enabled else "#374151",
            font=ctk.CTkFont(size=12),
            command=lambda m=mod: self._toggle(m),
        ).place(relx=0.05, rely=0.5, anchor="w")
        ctk.CTkButton(
            act_cell, text="Remove", width=72, height=28,
            fg_color="#450a0a", hover_color="#7f1d1d",
            font=ctk.CTkFont(size=12),
            command=lambda m=mod: self._remove(m),
        ).place(relx=0.52, rely=0.5, anchor="w")

    # ── actions ───────────────────────────────────────────────────────

    def _toggle(self, mod):
        if mod.enabled:
            self.app.mod_manager.disable(mod)
            activity_log.log_action("mod_disabled", mod.name)
        else:
            self.app.mod_manager.enable(mod)
            activity_log.log_action("mod_enabled", mod.name)
        self.refresh()

    def _remove(self, mod):
        if messagebox.askyesno("Remove Mod", f"Remove '{mod.name}' from ~mods?\nFiles will be deleted."):
            if self.app.game_paths:
                bm = BackupManager()
                bm.backup_mods(self.app.game_paths.client_mods, f"before remove {mod.name}")
                bm.prune()
            self.app.mod_manager.uninstall(mod)
            activity_log.log_action("mod_removed", mod.name)
            self.refresh()

    def _enable_all(self):
        if not self.app.mod_manager:
            return
        for mod in self.app.mod_manager.list_installed():
            if not mod.enabled:
                self.app.mod_manager.enable(mod)
        self.refresh()

    def _disable_all(self):
        if not self.app.mod_manager:
            return
        for mod in self.app.mod_manager.list_installed():
            if mod.enabled:
                self.app.mod_manager.disable(mod)
        self.refresh()
