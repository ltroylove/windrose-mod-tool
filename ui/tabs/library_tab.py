import os
import customtkinter as ctk
from tkinter import messagebox

ACCENT    = "#0d9488"
COL_NAME  = 300
COL_FILES = 200


class LibraryTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── toolbar ──────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            toolbar, text="Mod Library",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.grid(row=0, column=2, sticky="e")
        ctk.CTkButton(btn_frame, text="Open Folder", width=100, height=30, command=self._open_folder).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Refresh",     width=80,  height=30, command=self.refresh).pack(side="left", padx=4)

        # ── path hint ────────────────────────────────────────────────
        path_txt = str(self.app.mod_manager.library_path) if self.app.mod_manager else "—"
        ctk.CTkLabel(
            self, text=path_txt,
            font=ctk.CTkFont(size=11), text_color="#475569", anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 6))

        # ── column headers ────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=6, height=32)
        hdr.grid(row=2, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="MOD NAME",  width=COL_NAME,  anchor="w", text_color="#475569", font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=12, pady=6)
        ctk.CTkLabel(hdr, text="CONTENTS",  width=COL_FILES, anchor="w", text_color="#475569", font=ctk.CTkFont(size=11)).grid(row=0, column=1, pady=6)
        ctk.CTkLabel(hdr, text="INSTALL",                    anchor="e", text_color="#475569", font=ctk.CTkFont(size=11)).grid(row=0, column=2, padx=12, pady=6, sticky="e")

        # ── rows ──────────────────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=3, column=0, sticky="nsew", pady=(4, 0))
        self.scroll.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.refresh()

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not self.app.mod_manager:
            self._empty("Configure your game path in Settings to get started.")
            return

        packages = self.app.mod_manager.list_available()
        if not packages:
            self._empty(
                "No mods in your library yet.\n\n"
                "Download mods from Nexus Mods and extract them into the Mods folder,\n"
                "then click Refresh."
            )
            return

        for i, pkg in enumerate(packages):
            self._row(pkg, i)

    def _empty(self, msg: str):
        ctk.CTkLabel(
            self.scroll, text=msg,
            text_color="#475569", justify="center",
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, columnspan=3, pady=50)

    def _row(self, pkg, idx: int):
        bg = "#1a1a2e" if idx % 2 == 0 else "transparent"
        row = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4, height=44)
        row.grid(row=idx, column=0, sticky="ew", pady=1)
        row.grid_propagate(False)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row, text=pkg.name, width=COL_NAME,
            anchor="w", font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        ctk.CTkLabel(
            row, text=pkg.file_summary, width=COL_FILES,
            anchor="w", text_color="#6b7280", font=ctk.CTkFont(size=12),
        ).grid(row=0, column=1, pady=10, sticky="w")

        btn_frame = ctk.CTkFrame(row, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=8, pady=6, sticky="e")

        ctk.CTkButton(
            btn_frame, text="▶ Client", width=90, height=28,
            fg_color=ACCENT, hover_color="#0f766e",
            font=ctk.CTkFont(size=12),
            command=lambda p=pkg: self._install(p, server=False),
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_frame, text="▶ Server", width=90, height=28,
            fg_color="#1e293b", hover_color="#334155",
            font=ctk.CTkFont(size=12),
            command=lambda p=pkg: self._install(p, server=True),
        ).pack(side="left", padx=3)

    def _install(self, pkg, server: bool):
        if not self.app.mod_manager:
            return
        if server:
            if not self.app.game_paths or not self.app.game_paths.server_root.exists():
                messagebox.showerror("Server Not Found", "Dedicated server not found at the expected path.")
                return
            from core.mod_manager import ModManager
            mgr = ModManager(self.app.game_paths.server_mods, self.app.mod_manager.library_path)
        else:
            mgr = self.app.mod_manager

        try:
            installed = mgr.install(pkg)
            target = "server" if server else "client"
            messagebox.showinfo(
                "Installed",
                f"'{pkg.name}' installed to {target}.\n{len(installed)} file(s) copied.",
            )
            if hasattr(self.app, "_refresh_status"):
                self.app._refresh_status()
        except Exception as e:
            messagebox.showerror("Install Failed", str(e))

    def _open_folder(self):
        if self.app.mod_manager:
            path = self.app.mod_manager.library_path
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(path)
