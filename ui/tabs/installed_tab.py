import customtkinter as ctk
from tkinter import messagebox

ACCENT   = "#0d9488"
COL_NAME = 320
COL_STAT = 90
COL_FILES = 70


class InstalledTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
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

        # ── column headers ────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=6, height=32)
        hdr.grid(row=1, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(hdr, text="",            width=10,       anchor="w", text_color="#475569", font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=(10, 0), pady=6)
        ctk.CTkLabel(hdr, text="MOD NAME",    width=COL_NAME, anchor="w", text_color="#475569", font=ctk.CTkFont(size=11)).grid(row=0, column=1, padx=(12, 0), pady=6)
        ctk.CTkLabel(hdr, text="STATUS",      width=COL_STAT, anchor="w", text_color="#475569", font=ctk.CTkFont(size=11)).grid(row=0, column=2, pady=6)
        ctk.CTkLabel(hdr, text="FILES",       width=COL_FILES,anchor="w", text_color="#475569", font=ctk.CTkFont(size=11)).grid(row=0, column=3, pady=6)
        ctk.CTkLabel(hdr, text="ACTIONS",                     anchor="e", text_color="#475569", font=ctk.CTkFont(size=11)).grid(row=0, column=4, padx=(0, 12), pady=6, sticky="e")

        # ── scrollable rows ───────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=2, column=0, sticky="nsew", pady=(4, 0))
        self.scroll.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.refresh()

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not self.app.mod_manager:
            self._empty("Configure your game path in Settings to get started.")
            return

        mods = self.app.mod_manager.list_installed()
        if not mods:
            self._empty(
                "No mods installed yet.\n\nGo to  Library  to install mods from your collection.",
            )
            return

        for i, mod in enumerate(mods):
            self._row(mod, i)

        if hasattr(self.app, "_refresh_status"):
            self.app._refresh_status()

    def _empty(self, msg: str):
        ctk.CTkLabel(
            self.scroll, text=msg,
            text_color="#475569", justify="center",
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, columnspan=5, pady=50)

    def _row(self, mod, idx: int):
        bg = "#1a1a2e" if idx % 2 == 0 else "transparent"
        row = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4, height=40)
        row.grid(row=idx, column=0, sticky="ew", pady=1)
        row.grid_propagate(False)
        row.grid_columnconfigure(2, weight=1)

        # status dot
        dot_color = ACCENT if mod.enabled else "#374151"
        ctk.CTkFrame(row, width=8, height=8, corner_radius=4, fg_color=dot_color).grid(
            row=0, column=0, padx=(12, 0), pady=16
        )

        # name
        ctk.CTkLabel(
            row, text=mod.name, width=COL_NAME,
            anchor="w", font=ctk.CTkFont(size=13),
        ).grid(row=0, column=1, padx=(10, 0), pady=8, sticky="w")

        # status badge
        badge_color = "#064e3b" if mod.enabled else "#1f2937"
        badge_text  = "Enabled"  if mod.enabled else "Disabled"
        badge_fg    = "#6ee7b7"  if mod.enabled else "#6b7280"
        badge = ctk.CTkFrame(row, fg_color=badge_color, corner_radius=4, width=COL_STAT - 10)
        badge.grid(row=0, column=2, padx=4, pady=10, sticky="w")
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text=badge_text, text_color=badge_fg, font=ctk.CTkFont(size=11)).pack(padx=8, pady=2)

        # file count
        ctk.CTkLabel(
            row, text=str(mod.file_count), width=COL_FILES,
            anchor="w", text_color="#6b7280", font=ctk.CTkFont(size=12),
        ).grid(row=0, column=3, pady=8)

        # action buttons
        btn_frame = ctk.CTkFrame(row, fg_color="transparent")
        btn_frame.grid(row=0, column=4, padx=8, pady=6, sticky="e")

        toggle_txt = "Disable" if mod.enabled else "Enable"
        toggle_fg  = "#1e293b" if mod.enabled else ACCENT
        ctk.CTkButton(
            btn_frame, text=toggle_txt, width=72, height=28,
            fg_color=toggle_fg, hover_color="#0f766e" if not mod.enabled else "#374151",
            font=ctk.CTkFont(size=12),
            command=lambda m=mod: self._toggle(m),
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_frame, text="Remove", width=72, height=28,
            fg_color="#450a0a", hover_color="#7f1d1d",
            font=ctk.CTkFont(size=12),
            command=lambda m=mod: self._remove(m),
        ).pack(side="left", padx=3)

    def _toggle(self, mod):
        if mod.enabled:
            self.app.mod_manager.disable(mod)
        else:
            self.app.mod_manager.enable(mod)
        self.refresh()

    def _remove(self, mod):
        if messagebox.askyesno("Remove Mod", f"Remove '{mod.name}' from ~mods?\nFiles will be deleted."):
            self.app.mod_manager.uninstall(mod)
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
