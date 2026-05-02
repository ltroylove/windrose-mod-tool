import os
import customtkinter as ctk
from pathlib import Path
from tkinter import messagebox

from core import activity_log, settings as cfg
from core.backup_manager import BackupManager
from core.ftp_manager import FTPManager
from ui.theme import ACCENT, CARD_BG, MUTED

COL_NAME  = 280
COL_TYPE  = 90
COL_FILES = 160


class LibraryTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # ── toolbar ──────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        toolbar.grid_columnconfigure(1, weight=1)

        # title + path subtitle stacked on the left
        left = ctk.CTkFrame(toolbar, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            left, text="Mod Library",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")
        self._lib_path_label = ctk.CTkLabel(
            left, text="",
            font=ctk.CTkFont(size=10), text_color="#475569", anchor="w",
        )
        self._lib_path_label.pack(anchor="w")

        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.grid(row=0, column=2, sticky="e")
        ctk.CTkButton(btn_frame, text="Open Mod Library", width=130, height=30,
                      fg_color="#1e293b", hover_color="#334155",
                      command=self._open_library).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Check Remote", width=110, height=30,
                      fg_color="#1e293b", hover_color="#334155",
                      command=self._check_remote).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Refresh", width=80, height=30,
                      fg_color="#1e293b", hover_color="#334155",
                      command=self.refresh).pack(side="left", padx=4)

        # ── column header ─────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=6, height=32)
        hdr.grid(row=1, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(2, weight=1)

        COL_DEPLOYED = 80
        COL_DEPLOY   = 300
        for col, (txt, w, anchor) in enumerate([
            ("NAME",      COL_NAME,     "w"),
            ("TYPE",      COL_TYPE,     "w"),
            ("CONTENTS",  COL_FILES,    "w"),
            ("DEPLOYED",  COL_DEPLOYED, "w"),
            ("DEPLOY",    COL_DEPLOY,   "e"),
        ]):
            ctk.CTkLabel(
                hdr, text=txt, width=w, anchor=anchor,
                text_color=MUTED, font=ctk.CTkFont(size=11),
            ).grid(row=0, column=col,
                   padx=(12 if col == 0 else 4, 12 if col == 3 else 4),
                   pady=6, sticky="ew" if col == 2 else "")

        # ── scrollable rows ───────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=2, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.refresh()

    # ─────────────────────────────────────────────────────────────────
    # Refresh
    # ─────────────────────────────────────────────────────────────────

    def _deployed_stems(self, directory: Path) -> set[str]:
        if not directory or not directory.exists():
            return set()
        return {p.stem.removesuffix(".disabled") for p in directory.iterdir() if p.is_file()}

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        s = cfg.load()
        lib_path = Path(s.get("library_path", "Mods"))
        self._lib_path_label.configure(text=f"Downloads: {lib_path.resolve()}")

        # Build deployed-stem sets for local targets
        gp = self.app.game_paths
        self._client_stems: set[str] = self._deployed_stems(gp.client_mods if gp else None)
        self._server_stems: set[str] = self._deployed_stems(gp.server_mods if gp else None)
        if not hasattr(self, "_remote_stems"):
            self._remote_stems: set[str] = set()

        if not self.app.mod_manager:
            self._empty("Configure your game path in Settings to get started.")
            return

        generated = self.app.mod_manager.list_generated()
        downloaded = self.app.mod_manager.list_available()

        if not generated and not downloaded:
            self._empty(
                "Nothing here yet.\n\n"
                "• Use  Game Tuning  to generate a custom pak\n"
                "• Download mods from Nexus Mods and extract them into your Downloads folder"
            )
            return

        row = 0
        if generated:
            row = self._section_header("Generated Tuning Paks", row)
            for pak in generated:
                self._generated_row(pak, row)
                row += 1

        if downloaded:
            row = self._section_header("Downloaded from Nexus", row)
            for pkg in downloaded:
                self._downloaded_row(pkg, row)
                row += 1

    def _section_header(self, label: str, row: int) -> int:
        ctk.CTkLabel(
            self.scroll, text=label,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#64748b", anchor="w",
        ).grid(row=row, column=0, columnspan=4, sticky="w", padx=4, pady=(12, 2))
        return row + 1

    def _empty(self, msg: str):
        ctk.CTkLabel(
            self.scroll, text=msg,
            text_color="#475569", justify="center",
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, columnspan=4, pady=50)

    # ─────────────────────────────────────────────────────────────────
    # Row renderers
    # ─────────────────────────────────────────────────────────────────

    def _generated_row(self, pak: Path, row: int):
        bg = "#1a1a2e" if row % 2 == 0 else "transparent"
        fr = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4, height=44)
        fr.grid(row=row, column=0, sticky="ew", pady=1)
        fr.grid_propagate(False)
        fr.grid_columnconfigure(2, weight=1)
        fr.grid_columnconfigure(3, minsize=80)

        ctk.CTkLabel(fr, text=pak.stem, width=COL_NAME, anchor="w",
                     font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        badge = ctk.CTkFrame(fr, fg_color="#1e3a5f", corner_radius=4, width=COL_TYPE - 10)
        badge.grid(row=0, column=1, padx=4, pady=10, sticky="w")
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text="Generated", text_color="#93c5fd",
                     font=ctk.CTkFont(size=11)).pack(padx=6, pady=2)

        size_kb = pak.stat().st_size // 1024
        ctk.CTkLabel(fr, text=f"{pak.name}  ({size_kb} KB)", anchor="w",
                     text_color="#6b7280", font=ctk.CTkFont(size=12),
        ).grid(row=0, column=2, padx=4, pady=10, sticky="w")

        self._deployed_badges(fr, self._pak_stems(pak))
        self._deploy_buttons(fr, on_client=lambda p=pak: self._deploy_pak(p, server=False),
                             on_server=lambda p=pak: self._deploy_pak(p, server=True),
                             on_remote=lambda p=pak: self._deploy_pak_remote(p))

    def _downloaded_row(self, pkg, row: int):
        bg = "#1a1a2e" if row % 2 == 0 else "transparent"
        fr = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4, height=44)
        fr.grid(row=row, column=0, sticky="ew", pady=1)
        fr.grid_propagate(False)
        fr.grid_columnconfigure(2, weight=1)
        fr.grid_columnconfigure(3, minsize=80)

        ctk.CTkLabel(fr, text=pkg.name, width=COL_NAME, anchor="w",
                     font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        badge = ctk.CTkFrame(fr, fg_color="#1a2e1a", corner_radius=4, width=COL_TYPE - 10)
        badge.grid(row=0, column=1, padx=4, pady=10, sticky="w")
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text="Downloaded", text_color="#86efac",
                     font=ctk.CTkFont(size=11)).pack(padx=6, pady=2)

        ctk.CTkLabel(fr, text=pkg.file_summary, anchor="w",
                     text_color="#6b7280", font=ctk.CTkFont(size=12),
        ).grid(row=0, column=2, padx=4, pady=10, sticky="w")

        self._deployed_badges(fr, self._pak_stems(pkg))
        self._deploy_buttons(fr, on_client=lambda p=pkg: self._deploy_package(p, server=False),
                             on_server=lambda p=pkg: self._deploy_package(p, server=True),
                             on_remote=lambda p=pkg: self._deploy_package_remote(p))

    def _pak_stems(self, mod) -> set[str]:
        if isinstance(mod, Path):
            return {mod.stem}
        return {f.stem for f in mod.pak_files}

    def _deployed_badges(self, parent, pak_stems: set[str]):
        bf = ctk.CTkFrame(parent, fg_color="transparent")
        bf.grid(row=0, column=3, padx=(4, 0), pady=6, sticky="w")
        for letter, stems_set, active_color in [
            ("C", self._client_stems, "#0d9488"),
            ("S", self._server_stems, "#2563eb"),
            ("R", self._remote_stems, "#d97706"),
        ]:
            deployed = bool(pak_stems & stems_set)
            ctk.CTkLabel(
                bf, text=letter, width=20, height=20,
                corner_radius=4,
                fg_color=active_color if deployed else "#1e293b",
                text_color="white" if deployed else "#374151",
                font=ctk.CTkFont(size=10, weight="bold"),
            ).pack(side="left", padx=2)

    def _deploy_buttons(self, parent, on_client, on_server, on_remote):
        bf = ctk.CTkFrame(parent, fg_color="transparent")
        bf.grid(row=0, column=4, padx=8, pady=6, sticky="e")

        ctk.CTkButton(bf, text="▶ Client", width=90, height=28,
                      fg_color=ACCENT, hover_color="#0f766e",
                      font=ctk.CTkFont(size=12),
                      command=on_client,
        ).pack(side="left", padx=3)

        has_server = (self.app.game_paths is not None
                      and self.app.game_paths.server_root.exists())
        ctk.CTkButton(bf, text="▶ Server", width=90, height=28,
                      fg_color="#1e293b",
                      hover_color="#334155" if has_server else "#1e293b",
                      text_color="white" if has_server else "#374151",
                      state="normal" if has_server else "disabled",
                      font=ctk.CTkFont(size=12),
                      command=on_server,
        ).pack(side="left", padx=3)

        s = cfg.load()
        has_ftp = bool(s.get("ftp_host", ""))
        ctk.CTkButton(bf, text="▶ Remote", width=90, height=28,
                      fg_color="#1e293b",
                      hover_color="#334155" if has_ftp else "#1e293b",
                      text_color="white" if has_ftp else "#374151",
                      state="normal" if has_ftp else "disabled",
                      font=ctk.CTkFont(size=12),
                      command=on_remote,
        ).pack(side="left", padx=3)

    # ─────────────────────────────────────────────────────────────────
    # Deploy actions
    # ─────────────────────────────────────────────────────────────────

    def _target_dir(self, server: bool) -> Path | None:
        if server:
            if not self.app.game_paths or not self.app.game_paths.server_root.exists():
                messagebox.showerror("Server Not Found",
                                     "Dedicated server directory not found.")
                return None
            return self.app.game_paths.server_mods
        return self.app.game_paths.client_mods if self.app.game_paths else None

    def _conflict_ok(self, pak_stem: str, target_dir: Path) -> bool:
        """Return True if safe to proceed (no conflict, or user confirmed overwrite)."""
        if not target_dir.exists():
            return True
        existing = {Path(p.stem).stem  # strip .disabled suffix if present
                    for p in target_dir.iterdir() if p.is_file()}
        if pak_stem in existing:
            return messagebox.askyesno(
                "Already Deployed",
                f"'{pak_stem}' is already in ~mods.\n\nOverwrite it?",
            )
        return True

    def _deploy_pak(self, pak_file: Path, server: bool):
        """Deploy a single generated .pak file."""
        target_dir = self._target_dir(server)
        if target_dir is None:
            return
        if target_dir.exists() and not self._conflict_ok(pak_file.stem, target_dir):
            return
        try:
            dest = self.app.mod_manager.deploy(pak_file, target_dir)
            label = "server" if server else "client"
            messagebox.showinfo("Deployed",
                                f"'{pak_file.name}' deployed to {label}.\n\n{dest}")
            if hasattr(self.app, "_refresh_status"):
                self.app._refresh_status()
        except Exception as e:
            messagebox.showerror("Deploy Failed", str(e))

    def _deploy_package(self, pkg, server: bool):
        """Deploy a downloaded mod package (may have multiple pak files)."""
        target_dir = self._target_dir(server)
        if target_dir is None:
            return
        conflicts = []
        if target_dir.exists():
            installed = {Path(p.stem).stem for p in target_dir.iterdir() if p.is_file()}
            conflicts = [f.stem for f in pkg.pak_files if f.stem in installed]
        if conflicts:
            names = ", ".join(conflicts)
            if not messagebox.askyesno(
                "Already Deployed",
                f"These paks are already in ~mods:\n{names}\n\nOverwrite?",
            ):
                return
            if not server and self.app.game_paths:
                bm = BackupManager()
                bm.backup_mods(self.app.game_paths.client_mods, f"before install {pkg.name}")
                bm.prune()
        try:
            installed = self.app.mod_manager.install(pkg) if not server else self._install_server(pkg, target_dir)
            label = "server" if server else "client"
            messagebox.showinfo("Deployed",
                                f"'{pkg.name}' deployed to {label}.\n{len(installed)} file(s) copied.")
            activity_log.log_action("mod_installed", pkg.name)
            if hasattr(self.app, "_refresh_status"):
                self.app._refresh_status()
        except Exception as e:
            messagebox.showerror("Deploy Failed", str(e))

    def _install_server(self, pkg, server_mods_dir: Path) -> list[Path]:
        import shutil
        server_mods_dir.mkdir(parents=True, exist_ok=True)
        installed = []
        for src in pkg.pak_files:
            dst = server_mods_dir / src.name
            shutil.copy2(src, dst)
            installed.append(dst)
        return installed

    # ─────────────────────────────────────────────────────────────────
    # Remote (FTP) deploy
    # ─────────────────────────────────────────────────────────────────

    def _make_ftp(self) -> FTPManager | None:
        s = cfg.load()
        host = s.get("ftp_host", "")
        if not host:
            messagebox.showwarning("FTP Not Configured", "Enter your FTP details in Settings first.")
            return None
        return FTPManager(
            host=host,
            port=int(s.get("ftp_port", 21)),
            user=s.get("ftp_user", ""),
            password=cfg.get_ftp_password(),
            server_json_path=s.get("ftp_server_json_path", "R5/ServerDescription.json"),
        )

    def _check_remote(self):
        ftp = self._make_ftp()
        if not ftp:
            return
        try:
            entries = ftp.list_remote_mods(self._remote_mods_dir())
            self._remote_stems = {Path(e).stem for e in entries}
            self.refresh()
        except Exception as e:
            messagebox.showerror("Remote Check Failed", str(e))

    def _remote_mods_dir(self) -> str:
        return cfg.load().get("ftp_mods_path", "R5/Content/Paks/~mods")

    def _deploy_pak_remote(self, pak_file: Path):
        ftp = self._make_ftp()
        if not ftp:
            return
        try:
            ftp.upload_pak(pak_file, self._remote_mods_dir())
            self._remote_stems.add(pak_file.stem)
            messagebox.showinfo("Deployed", f"'{pak_file.name}' uploaded to remote server.")
            activity_log.log_action("mod_installed", pak_file.stem + " (remote)")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Remote Deploy Failed", str(e))

    def _deploy_package_remote(self, pkg):
        ftp = self._make_ftp()
        if not ftp:
            return
        remote_dir = self._remote_mods_dir()
        try:
            count = 0
            for pak_file in pkg.pak_files:
                ftp.upload_pak(pak_file, remote_dir)
                self._remote_stems.add(pak_file.stem)
                count += 1
            messagebox.showinfo("Deployed", f"'{pkg.name}' — {count} file(s) uploaded to remote server.")
            activity_log.log_action("mod_installed", pkg.name + " (remote)")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Remote Deploy Failed", str(e))

    # ─────────────────────────────────────────────────────────────────
    # Folder shortcuts
    # ─────────────────────────────────────────────────────────────────

    def _open_library(self):
        if self.app.mod_manager:
            path = self.app.mod_manager.library_path
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(path)
