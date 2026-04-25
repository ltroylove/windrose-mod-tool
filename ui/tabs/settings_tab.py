import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from core import settings as cfg
from core.paths import GamePaths, find_game_path
from ui.theme import ACCENT


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._vars: dict[str, ctk.StringVar] = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Settings",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 16))

        # ── Paths card ───────────────────────────────────────────────
        card = ctk.CTkFrame(self, corner_radius=8, fg_color="#1e293b")
        card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Paths",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#94a3b8",
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(14, 8))

        ctk.CTkFrame(card, height=1, fg_color="#334155").grid(row=1, column=0, columnspan=4, sticky="ew", padx=16)

        s = cfg.load()
        fields = [
            ("game_path",    "Game Folder",     self._browse_game),
            ("library_path", "Mod Library",     self._browse("library_path")),
        ]
        for i, (key, label, cmd) in enumerate(fields):
            ctk.CTkLabel(card, text=label, anchor="e", width=130, text_color="#94a3b8").grid(
                row=i + 2, column=0, sticky="e", padx=(16, 10), pady=8
            )
            var = ctk.StringVar(value=s.get(key, ""))
            self._vars[key] = var
            ctk.CTkEntry(card, textvariable=var, height=32).grid(
                row=i + 2, column=1, sticky="ew", padx=(0, 8), pady=8
            )
            ctk.CTkButton(card, text="Browse", width=80, height=32, command=cmd).grid(
                row=i + 2, column=2, padx=(0, 8), pady=8
            )
            ctk.CTkButton(
                card, text="Open", width=60, height=32,
                fg_color="#1e293b", hover_color="#334155",
                command=lambda k=key: self._open_folder(k),
            ).grid(row=i + 2, column=3, padx=(0, 16), pady=8)

        # ── actions ──────────────────────────────────────────────────
        act = ctk.CTkFrame(self, fg_color="transparent")
        act.grid(row=2, column=0, sticky="w", pady=(0, 12))

        ctk.CTkButton(
            act, text="Auto-detect Game", width=160, height=34,
            fg_color="#1e293b", hover_color="#334155",
            command=self._auto_detect,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            act, text="Validate", width=100, height=34,
            fg_color="#1e293b", hover_color="#334155",
            command=self._validate,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            act, text="Save Settings", width=130, height=34,
            fg_color=ACCENT, hover_color="#0f766e",
            command=self._save,
        ).pack(side="left")

        self._status = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11), text_color="#6b7280",
        )
        self._status.grid(row=3, column=0, sticky="w")

    def _browse_game(self):
        path = filedialog.askdirectory(title="Select Windrose Game Folder")
        if path:
            self._vars["game_path"].set(path)

    def _browse(self, key: str):
        def _go():
            path = filedialog.askdirectory()
            if path:
                self._vars[key].set(path)
        return _go

    def _open_folder(self, key: str):
        path = self._vars[key].get()
        if path and Path(path).exists():
            os.startfile(path)
        else:
            self._status.configure(text="Path does not exist", text_color="#fbbf24")

    def _validate(self):
        labels = {"game_path": "Game Folder", "library_path": "Mod Library"}
        parts = []
        for key, lbl in labels.items():
            p = self._vars[key].get()
            ok = bool(p) and Path(p).exists()
            parts.append(f"{'✓' if ok else '✗'} {lbl}")
        self._status.configure(text="   ".join(parts), text_color="#6ee7b7")

    def _auto_detect(self):
        found = find_game_path()
        if found:
            self._vars["game_path"].set(str(found))
            self._status.configure(text=f"✓ Found: {found}", text_color="#6ee7b7")
        else:
            self._status.configure(text="Could not auto-detect. Set the path manually.", text_color="#fbbf24")

    def _save(self):
        s = cfg.load()
        for key, var in self._vars.items():
            s[key] = var.get()

        game_str = s.get("game_path", "")
        if game_str:
            gp = GamePaths(Path(game_str))
            if not gp.is_valid():
                self._status.configure(text="⚠ Game path doesn't look right — check it and try again.", text_color="#fbbf24")
                return

        cfg.save(s)
        messagebox.showinfo("Settings Saved", "Settings saved. The app will now reload.")
        self.app.reload()
