from pathlib import Path
import customtkinter as ctk
from core import settings as cfg
from core.paths import GamePaths, find_game_path
from core.mod_manager import ModManager
from core.config_manager import ConfigManager
from ui.tabs.installed_tab import InstalledTab
from ui.tabs.library_tab import LibraryTab
from ui.tabs.create_tab import CreateTab
from ui.tabs.config_tab import ConfigTab
from ui.tabs.settings_tab import SettingsTab

ACCENT       = "#0d9488"
ACCENT_HOVER = "#0f766e"
SIDEBAR_BG   = "#0f172a"
SIDEBAR_W    = 190

NAV = [
    ("Installed",    "▣"),   # ▣
    ("Library",      "≡"),   # ≡
    ("Create",       "✚"),   # ✚
    ("Server Config","⊞"),   # ⊞
    ("Settings",     "⚙"),   # ⚙
]

TAB_CLASSES = {
    "Installed":    InstalledTab,
    "Library":      LibraryTab,
    "Create":       CreateTab,
    "Server Config":ConfigTab,
    "Settings":     SettingsTab,
}


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windrose Mod Tool")
        self.geometry("1080x700")
        self.minsize(920, 580)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._frames: dict[str, ctk.CTkFrame] = {}
        self._active = "Installed"

        self._init_services()
        self._build()

    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------

    def _init_services(self):
        s = cfg.load()
        game_str = s.get("game_path", "")
        if game_str:
            game = Path(game_str)
        else:
            game = find_game_path()
            if game:
                s["game_path"] = str(game)
                cfg.save(s)

        self.game_paths     = GamePaths(game) if game and game.exists() else None
        self.mod_manager    = None
        self.config_manager = None

        if self.game_paths and self.game_paths.is_valid():
            library = Path(s.get("library_path", "Mods"))
            self.mod_manager    = ModManager(self.game_paths.client_mods, library)
            self.config_manager = ConfigManager(self.game_paths.server_description)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_sidebar()
        self._build_content()
        self._build_statusbar()
        self._nav_to("Installed")

    def _build_header(self):
        hdr = ctk.CTkFrame(self, height=46, corner_radius=0, fg_color=SIDEBAR_BG)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.grid_propagate(False)

        ctk.CTkLabel(
            hdr, text="⚓  WINDROSE MOD TOOL",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ACCENT,
        ).pack(side="left", padx=18, pady=12)

        if self.game_paths and self.game_paths.is_valid():
            game_name = self.game_paths.game_root.name
            status_txt   = f"✓  {game_name}"
            status_color = "#6ee7b7"
        else:
            status_txt   = "⚠  Game not found — go to Settings"
            status_color = "#fbbf24"

        ctk.CTkLabel(
            hdr, text=status_txt,
            font=ctk.CTkFont(size=11), text_color=status_color,
        ).pack(side="right", padx=18)

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=SIDEBAR_W, corner_radius=0, fg_color=SIDEBAR_BG)
        sb.grid(row=1, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)

        # thin separator under header
        ctk.CTkFrame(sb, height=1, fg_color="#1e293b").grid(row=0, column=0, sticky="ew")

        for i, (name, icon) in enumerate(NAV):
            btn = ctk.CTkButton(
                sb,
                text=f"  {icon}   {name}",
                anchor="w",
                height=42,
                corner_radius=6,
                border_width=0,
                fg_color="transparent",
                hover_color="#1e293b",
                text_color="#64748b",
                font=ctk.CTkFont(size=13),
                command=lambda n=name: self._nav_to(n),
            )
            btn.grid(row=i + 1, column=0, sticky="ew", padx=8, pady=2)
            self._nav_buttons[name] = btn

        # version watermark at bottom
        ctk.CTkLabel(
            sb, text="v0.1.0",
            font=ctk.CTkFont(size=10), text_color="#1e293b",
        ).grid(row=99, column=0, sticky="s", pady=10)
        sb.grid_rowconfigure(99, weight=1)

    def _build_content(self):
        host = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        host.grid(row=1, column=1, sticky="nsew")
        host.grid_columnconfigure(0, weight=1)
        host.grid_rowconfigure(0, weight=1)

        for name, Cls in TAB_CLASSES.items():
            frame = Cls(host, self)
            frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)
            frame.grid_remove()
            self._frames[name] = frame

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=26, corner_radius=0, fg_color=SIDEBAR_BG)
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        self._status_lbl = ctk.CTkLabel(
            bar, text="",
            font=ctk.CTkFont(size=10), text_color="#334155",
        )
        self._status_lbl.pack(side="left", padx=14)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _nav_to(self, name: str):
        for n, btn in self._nav_buttons.items():
            if n == name:
                btn.configure(fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white")
            else:
                btn.configure(fg_color="transparent", hover_color="#1e293b", text_color="#64748b")

        for n, frame in self._frames.items():
            if n == name:
                frame.grid()
                if hasattr(frame, "refresh"):
                    frame.refresh()
            else:
                frame.grid_remove()

        self._active = name
        self._refresh_status()

    def _refresh_status(self):
        if not self.mod_manager:
            self._status_lbl.configure(text="Game not configured")
            return
        installed = self.mod_manager.list_installed()
        enabled   = sum(1 for m in installed if m.enabled)
        available = len(self.mod_manager.list_available())
        self._status_lbl.configure(
            text=f"Installed: {len(installed)}   Enabled: {enabled}   Library: {available}"
        )

    # ------------------------------------------------------------------
    # Called by SettingsTab after a save
    # ------------------------------------------------------------------

    def reload(self):
        self._init_services()
        for w in self.winfo_children():
            w.destroy()
        self._nav_buttons = {}
        self._frames = {}
        self._build()
