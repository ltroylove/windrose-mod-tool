import os
from datetime import datetime
import customtkinter as ctk

from core import activity_log
from core.backup_manager import BackupManager
from ui.theme import ACCENT, CARD_BG, MUTED, MUTED_LIGHT

_ACTION_COLORS = {
    "mod_installed":    "#6ee7b7",
    "mod_removed":      "#f87171",
    "mod_enabled":      "#6ee7b7",
    "mod_disabled":     "#6b7280",
    "tuning_generated": "#60a5fa",
    "backup_created":   "#fbbf24",
    "restore_performed":"#c084fc",
}


def _rel_time(ts_str: str) -> str:
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
        s = int((datetime.now() - dt).total_seconds())
        if s < 60:    return "just now"
        if s < 3600:  return f"{s // 60}m ago"
        if s < 86400: return f"{s // 3600}h ago"
        return f"{s // 86400}d ago"
    except Exception:
        return ts_str


class HomeTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=0, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._body = body
        self._render()

    def refresh(self):
        for w in self._body.winfo_children():
            w.destroy()
        self._render()

    # ── full render ───────────────────────────────────────────────────

    def _render(self):
        body = self._body
        row = 0

        # ── page title ───────────────────────────────────────────────
        ctk.CTkLabel(
            body, text="Home",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(0, 14))
        row += 1

        # ── game status card ─────────────────────────────────────────
        row = self._game_card(body, row)

        # ── stat cards ───────────────────────────────────────────────
        row = self._stat_cards(body, row)

        # ── quick actions ────────────────────────────────────────────
        row = self._quick_actions(body, row)

        # ── recent activity ──────────────────────────────────────────
        row = self._recent_activity(body, row)

        # ── feature cards ────────────────────────────────────────────
        row = self._feature_card(
            body, row,
            icon="⚙",
            title="Game Tuning",
            desc=(
                "Adjust stack sizes per item category, loot drop multipliers per "
                "resource type, and spawner respawn timing. Generates a ready-to-load "
                ".pak mod — no manual file editing required."
            ),
            btn_text="Open Game Tuning",
            btn_cmd=lambda: self.app._nav_to("Game Tuning"),
            enabled=True,
        )
        row = self._feature_card(
            body, row,
            icon="▣",
            title="Mod Manager",
            desc=(
                "Install, enable, and disable .pak mods for your local client. "
                "Browse your mod library and push mods to a dedicated server."
            ),
            btn_text="Open Mods",
            btn_cmd=lambda: self.app._nav_to("Mods"),
            enabled=bool(self.app.mod_manager),
        )
        row = self._feature_card(
            body, row,
            icon="⊞",
            title="Server Config",
            desc=(
                "Edit ServerDescription.json and WorldDescription.json for your "
                "dedicated server — player count, PVP mode, day length, and more."
            ),
            btn_text="Open Server",
            btn_cmd=lambda: self.app._nav_to("Server"),
            enabled=bool(self.app.config_manager),
        )

    # ── game status card ─────────────────────────────────────────────

    def _game_card(self, parent, row: int) -> int:
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 14))
        card.grid_columnconfigure(1, weight=1)

        if self.app.game_paths and self.app.game_paths.is_valid():
            dot_color  = ACCENT
            status_txt = "Game detected"
            status_fg  = "#6ee7b7"
            path_txt   = str(self.app.game_paths.game_root)
        else:
            dot_color  = "#ef4444"
            status_txt = "Game not found — set the path in Settings"
            status_fg  = "#fbbf24"
            path_txt   = "No game path configured"

        # colored dot
        ctk.CTkFrame(
            card, width=10, height=10, corner_radius=5, fg_color=dot_color,
        ).grid(row=0, column=0, padx=(16, 10), pady=18, sticky="w")

        # status + path
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w", pady=14)
        ctk.CTkLabel(
            info, text=status_txt,
            font=ctk.CTkFont(size=13, weight="bold"), text_color=status_fg,
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=path_txt,
            font=ctk.CTkFont(size=11), text_color=MUTED,
        ).pack(anchor="w")

        # settings button
        ctk.CTkButton(
            card, text="Settings", width=90, height=30,
            fg_color="#0f172a", hover_color="#334155",
            font=ctk.CTkFont(size=12),
            command=lambda: self.app._nav_to("Settings"),
        ).grid(row=0, column=2, padx=14, pady=14)

        return row + 1

    # ── stat cards ────────────────────────────────────────────────────

    def _stat_cards(self, parent, row: int) -> int:
        if not self.app.mod_manager:
            return row

        installed = self.app.mod_manager.list_installed()
        enabled   = sum(1 for m in installed if m.enabled)
        library   = len(self.app.mod_manager.list_available())

        bm = BackupManager()
        backups = bm.list_backups()
        last_backup = _rel_time(backups[0].ts) if backups else "Never"

        stats = [
            (str(len(installed)), "Installed"),
            (str(enabled),        "Enabled"),
            (str(library),        "In Library"),
            (last_backup,         "Last Backup"),
        ]

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 14))
        for col, (value, label) in enumerate(stats):
            frame.grid_columnconfigure(col, weight=1)
            card = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=8)
            card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0))
            ctk.CTkLabel(
                card, text=value,
                font=ctk.CTkFont(size=28 if len(value) <= 4 else 16, weight="bold"),
                text_color="white",
            ).pack(pady=(16, 2))
            ctk.CTkLabel(
                card, text=label,
                font=ctk.CTkFont(size=11), text_color=MUTED_LIGHT,
            ).pack(pady=(0, 16))

        return row + 1

    # ── quick actions ─────────────────────────────────────────────────

    def _quick_actions(self, parent, row: int) -> int:
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 14))

        ctk.CTkLabel(
            card, text="Quick Actions",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8",
        ).pack(anchor="w", padx=16, pady=(12, 8))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(anchor="w", padx=12, pady=(0, 12))

        can_launch = bool(self.app.game_paths and self.app.game_paths.client_exe)
        ctk.CTkButton(
            btn_row, text="▶ Launch Windrose", width=150, height=32,
            fg_color=ACCENT if can_launch else "#1e293b",
            hover_color="#0f766e" if can_launch else "#334155",
            state="normal" if can_launch else "disabled",
            font=ctk.CTkFont(size=12),
            command=self.app._launch_game,
        ).pack(side="left", padx=(0, 6))

        can_client = bool(self.app.game_paths)
        ctk.CTkButton(
            btn_row, text="📁 Client Mods", width=120, height=32,
            fg_color="#1e293b", hover_color="#334155",
            state="normal" if can_client else "disabled",
            font=ctk.CTkFont(size=12),
            command=self._open_client_mods,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="📁 Mod Library", width=110, height=32,
            fg_color="#1e293b", hover_color="#334155",
            font=ctk.CTkFont(size=12),
            command=self._open_my_mods,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="💾 Back Up Now", width=120, height=32,
            fg_color="#1e293b", hover_color="#334155",
            state="normal" if can_client else "disabled",
            font=ctk.CTkFont(size=12),
            command=self._backup_now,
        ).pack(side="left")

        return row + 1

    def _open_client_mods(self):
        if self.app.game_paths:
            path = self.app.game_paths.client_mods
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(path)

    def _open_my_mods(self):
        from core import settings as cfg
        from pathlib import Path
        s = cfg.load()
        path = Path(s.get("library_path", "Mods"))
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def _backup_now(self):
        if self.app.game_paths:
            bm = BackupManager()
            bm.backup_mods(self.app.game_paths.client_mods, "manual backup")
            bm.prune()
            self.refresh()

    # ── recent activity ───────────────────────────────────────────────

    def _recent_activity(self, parent, row: int) -> int:
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 14))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(
            hdr, text="Recent Activity",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8",
        ).pack(side="left")

        entries = activity_log.load_recent(5)
        if not entries:
            ctk.CTkLabel(
                card, text="No activity yet",
                font=ctk.CTkFont(size=12), text_color=MUTED,
            ).pack(pady=(0, 16))
        else:
            for entry in entries:
                action = entry.get("action", "")
                detail = entry.get("detail", "")
                ts     = entry.get("ts", "")
                color  = _ACTION_COLORS.get(action, MUTED_LIGHT)
                label  = action.replace("_", " ").title()

                row_frame = ctk.CTkFrame(card, fg_color="transparent")
                row_frame.pack(fill="x", padx=16, pady=2)
                ctk.CTkLabel(
                    row_frame, text=label, width=130,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=color, anchor="w",
                ).pack(side="left")
                ctk.CTkLabel(
                    row_frame, text=detail,
                    font=ctk.CTkFont(size=11), text_color="white", anchor="w",
                ).pack(side="left", expand=True, fill="x")
                ctk.CTkLabel(
                    row_frame, text=_rel_time(ts), width=70,
                    font=ctk.CTkFont(size=10), text_color=MUTED, anchor="e",
                ).pack(side="right")

            ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

        return row + 1

    # ── feature card ──────────────────────────────────────────────────

    def _feature_card(
        self, parent, row: int,
        icon: str, title: str, desc: str,
        btn_text: str, btn_cmd, enabled: bool,
    ) -> int:
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        card.grid_columnconfigure(1, weight=1)

        # icon badge
        badge = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=6, width=44, height=44)
        badge.grid(row=0, column=0, padx=(16, 14), pady=16, sticky="nw")
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text=icon, font=ctk.CTkFont(size=20)).place(relx=0.5, rely=0.5, anchor="center")

        # text block
        txt = ctk.CTkFrame(card, fg_color="transparent")
        txt.grid(row=0, column=1, sticky="ew", pady=14)
        ctk.CTkLabel(
            txt, text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            txt, text=desc,
            font=ctk.CTkFont(size=11), text_color=MUTED_LIGHT,
            anchor="w", justify="left", wraplength=520,
        ).pack(anchor="w", pady=(3, 0))

        # action button
        ctk.CTkButton(
            card, text=f"{btn_text}  →", width=150, height=32,
            fg_color=ACCENT if enabled else "#1e293b",
            hover_color="#0f766e" if enabled else "#334155",
            text_color="white" if enabled else MUTED,
            font=ctk.CTkFont(size=12),
            state="normal" if enabled else "disabled",
            command=btn_cmd,
        ).grid(row=0, column=2, padx=16, pady=16)

        return row + 1
