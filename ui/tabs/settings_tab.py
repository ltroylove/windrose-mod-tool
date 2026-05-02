import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from core import settings as cfg
from core.paths import GamePaths, find_game_path
from core.ftp_manager import FTPManager
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

        # ── FTP card ─────────────────────────────────────────────────
        ftp_card = ctk.CTkFrame(self, corner_radius=8, fg_color="#1e293b")
        ftp_card.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        ftp_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            ftp_card, text="Dedicated Server FTP",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#94a3b8",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(14, 8))

        ctk.CTkFrame(ftp_card, height=1, fg_color="#334155").grid(row=1, column=0, columnspan=3, sticky="ew", padx=16)

        ftp_fields = [
            ("ftp_host",            "FTP Host"),
            ("ftp_port",            "FTP Port"),
            ("ftp_user",            "Username"),
            ("ftp_password",        "Password"),
            ("ftp_server_json_path","Server JSON Path"),
            ("ftp_mods_path",       "Mods Folder Path"),
        ]
        for i, (key, label) in enumerate(ftp_fields):
            ctk.CTkLabel(ftp_card, text=label, anchor="e", width=130, text_color="#94a3b8").grid(
                row=i + 2, column=0, sticky="e", padx=(16, 10), pady=8
            )
            show = "*" if key == "ftp_password" else ""
            default = cfg.get_ftp_password() if key == "ftp_password" else s.get(key, "")
            var = ctk.StringVar(value=default)
            self._vars[key] = var
            ctk.CTkEntry(ftp_card, textvariable=var, height=32, show=show).grid(
                row=i + 2, column=1, sticky="ew", padx=(0, 8), pady=8
            )

        self._ftp_status = ctk.CTkLabel(ftp_card, text="", font=ctk.CTkFont(size=11), text_color="#6b7280")
        self._ftp_status.grid(row=len(ftp_fields) + 2, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 4))

        ctk.CTkButton(
            ftp_card, text="Test Connection", width=140, height=32,
            fg_color="#1e293b", hover_color="#334155",
            command=self._test_ftp,
        ).grid(row=len(ftp_fields) + 3, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 12))

        # ── actions ──────────────────────────────────────────────────
        act = ctk.CTkFrame(self, fg_color="transparent")
        act.grid(row=3, column=0, sticky="w", pady=(0, 12))

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
        self._status.grid(row=4, column=0, sticky="w")

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

    def _test_ftp(self):
        self._ftp_status.configure(text="Connecting…", text_color="#94a3b8")
        self.update()
        try:
            ftp = FTPManager(
                host=self._vars["ftp_host"].get(),
                port=int(self._vars["ftp_port"].get() or 21),
                user=self._vars["ftp_user"].get(),
                password=self._vars["ftp_password"].get(),
                server_json_path=self._vars["ftp_server_json_path"].get(),
            )
            ok, msg = ftp.test_connection()
            self._ftp_status.configure(
                text=f"{'✓' if ok else '✗'} {msg}",
                text_color="#6ee7b7" if ok else "#f87171",
            )
        except Exception as e:
            self._ftp_status.configure(text=f"✗ {e}", text_color="#f87171")

    def _save(self):
        s = cfg.load()
        for key, var in self._vars.items():
            s[key] = var.get()

        # Validate port before saving
        raw_port = s.get("ftp_port", "21").strip()
        try:
            port_int = int(raw_port)
            if not (1 <= port_int <= 65535):
                raise ValueError
            s["ftp_port"] = str(port_int)
        except ValueError:
            s["ftp_port"] = "21"

        game_str = s.get("game_path", "")
        if game_str:
            gp = GamePaths(Path(game_str))
            if not gp.is_valid():
                self._status.configure(text="⚠ Game path doesn't look right — check it and try again.", text_color="#fbbf24")
                return

        # Persist password to OS credential store, not to settings.json
        cfg.set_ftp_password(s.pop("ftp_password", ""))
        cfg.save(s)
        messagebox.showinfo("Settings Saved", "Settings saved. The app will now reload.")
        self.app.reload()
