import customtkinter as ctk
from tkinter import messagebox
from core.config_manager import ConfigManager, ServerConfig, WorldConfig


class ConfigTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._server_vars: dict = {}
        self._world_vars: dict = {}
        self._current_world: WorldConfig | None = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_server_panel()
        self._build_world_panel()

    # ------------------------------------------------------------------
    # Server config
    # ------------------------------------------------------------------

    def _build_server_panel(self):
        panel = ctk.CTkFrame(self, corner_radius=8)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(panel, text="Server Settings", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 6)
        )

        form = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        form.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        form.grid_columnconfigure(1, weight=1)

        if not self.app.config_manager:
            ctk.CTkLabel(form, text="Game path not configured.", text_color="gray").grid(pady=20)
            return

        cfg = self.app.config_manager.load_server()
        self._server_vars = {}

        fields = [
            ("server_name",          "Server Name",       "str",  cfg.server_name),
            ("invite_code",          "Invite Code",       "str",  cfg.invite_code),
            ("max_player_count",     "Max Players",       "int",  str(cfg.max_player_count)),
            ("password",             "Password",          "str",  cfg.password),
            ("is_password_protected","Password Required", "bool", cfg.is_password_protected),
            ("user_selected_region", "Region",            "combo",cfg.user_selected_region),
            ("use_direct_connection","Direct Connect",    "bool", cfg.use_direct_connection),
            ("direct_connection_port","Direct Port",      "int",  str(cfg.direct_connection_port)),
            ("p2p_proxy_address",    "P2P Proxy IP",      "str",  cfg.p2p_proxy_address),
        ]

        for row_i, (key, label, ftype, default) in enumerate(fields):
            ctk.CTkLabel(form, text=label, anchor="e", width=140).grid(row=row_i, column=0, sticky="e", padx=(4, 8), pady=3)
            if ftype == "bool":
                var = ctk.BooleanVar(value=bool(default))
                ctk.CTkSwitch(form, variable=var, text="").grid(row=row_i, column=1, sticky="w")
                self._server_vars[key] = (var, "bool")
            elif ftype == "combo":
                var = ctk.StringVar(value=default)
                ctk.CTkOptionMenu(form, variable=var, values=["", "EU", "SEA", "CIS"]).grid(row=row_i, column=1, sticky="w")
                self._server_vars[key] = (var, "str")
            else:
                var = ctk.StringVar(value=str(default))
                ctk.CTkEntry(form, textvariable=var).grid(row=row_i, column=1, sticky="ew", padx=(0, 8))
                self._server_vars[key] = (var, ftype)

        # read-only info
        row_i += 1
        ctk.CTkLabel(form, text="Server ID", anchor="e", width=140, text_color="gray").grid(row=row_i, column=0, sticky="e", padx=(4, 8), pady=3)
        ctk.CTkLabel(form, text=cfg.persistent_server_id or "—", text_color="gray", anchor="w").grid(row=row_i, column=1, sticky="w")

        ctk.CTkButton(panel, text="Save Server Config", command=self._save_server).grid(
            row=2, column=0, padx=12, pady=(0, 12), sticky="ew"
        )

    def _save_server(self):
        if not self.app.config_manager:
            return
        existing = self.app.config_manager.load_server()
        try:
            for key, (var, ftype) in self._server_vars.items():
                raw = var.get()
                if ftype == "int":
                    setattr(existing, key, int(raw))
                elif ftype == "bool":
                    setattr(existing, key, bool(raw))
                else:
                    setattr(existing, key, raw)
            self.app.config_manager.save_server(existing)
            messagebox.showinfo("Saved", "Server config saved.\nRestart the server for changes to take effect.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))

    # ------------------------------------------------------------------
    # World config
    # ------------------------------------------------------------------

    def _build_world_panel(self):
        panel = ctk.CTkFrame(self, corner_radius=8)
        panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(panel, text="World Settings", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )

        if not self.app.game_paths:
            ctk.CTkLabel(panel, text="Game path not configured.", text_color="gray").grid(pady=20)
            return

        worlds = self.app.game_paths.find_world_configs()

        # World selector
        selector_frame = ctk.CTkFrame(panel, fg_color="transparent")
        selector_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
        ctk.CTkLabel(selector_frame, text="World:").pack(side="left")
        self._world_options = {w.parent.parent.name: w for w in worlds}
        world_names = list(self._world_options.keys()) or ["No worlds found"]
        self._world_var = ctk.StringVar(value=world_names[0])
        ctk.CTkOptionMenu(
            selector_frame, variable=self._world_var, values=world_names,
            command=self._load_world
        ).pack(side="left", padx=8)

        self._world_form = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self._world_form.grid(row=2, column=0, sticky="nsew", padx=8)
        self._world_form.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(panel, text="Save World Config", command=self._save_world).grid(
            row=3, column=0, padx=12, pady=(6, 12), sticky="ew"
        )

        if worlds:
            self._load_world(world_names[0])

    def _load_world(self, world_key: str):
        for w in self._world_form.winfo_children():
            w.destroy()
        self._world_vars = {}

        path = self._world_options.get(world_key)
        if not path or not self.app.config_manager:
            return

        try:
            wc = self.app.config_manager.load_world(path)
        except Exception as e:
            ctk.CTkLabel(self._world_form, text=f"Could not load: {e}", text_color="orange").grid(pady=10)
            return

        self._current_world = wc

        fields = [
            ("world_name",               "World Name",         "str",   wc.world_name),
            ("world_preset_type",        "Preset",             "combo", wc.world_preset_type),
            ("combat_difficulty",        "Combat Difficulty",  "combo", wc.combat_difficulty),
            ("mob_health",               "Mob Health ×",       "float", str(wc.mob_health)),
            ("mob_damage",               "Mob Damage ×",       "float", str(wc.mob_damage)),
            ("ship_health",              "Ship Health ×",      "float", str(wc.ship_health)),
            ("ship_damage",              "Ship Damage ×",      "float", str(wc.ship_damage)),
            ("boarding_difficulty",      "Boarding Diff ×",    "float", str(wc.boarding_difficulty)),
            ("coop_stats_correction",    "Coop Stats Adj",     "float", str(wc.coop_stats_correction)),
            ("coop_ship_stats_correction","Coop Ship Adj",     "float", str(wc.coop_ship_stats_correction)),
            ("shared_quests",            "Shared Quests",      "bool",  wc.shared_quests),
            ("easy_explore",             "Immersive Explore",  "bool",  wc.easy_explore),
        ]

        combo_opts = {
            "world_preset_type":  ["Easy", "Medium", "Hard", "Custom"],
            "combat_difficulty":  ["Easy", "Normal", "Hard"],
        }

        for row_i, (key, label, ftype, default) in enumerate(fields):
            ctk.CTkLabel(self._world_form, text=label, anchor="e", width=150).grid(
                row=row_i, column=0, sticky="e", padx=(4, 8), pady=3
            )
            if ftype == "bool":
                var = ctk.BooleanVar(value=bool(default))
                ctk.CTkSwitch(self._world_form, variable=var, text="").grid(row=row_i, column=1, sticky="w")
                self._world_vars[key] = (var, "bool")
            elif ftype == "combo":
                var = ctk.StringVar(value=str(default))
                ctk.CTkOptionMenu(self._world_form, variable=var, values=combo_opts.get(key, [])).grid(row=row_i, column=1, sticky="w")
                self._world_vars[key] = (var, "str")
            else:
                var = ctk.StringVar(value=str(default))
                ctk.CTkEntry(self._world_form, textvariable=var).grid(row=row_i, column=1, sticky="ew", padx=(0, 8))
                self._world_vars[key] = (var, ftype)

    def _save_world(self):
        if not self._current_world or not self.app.config_manager:
            return
        wc = self._current_world
        try:
            for key, (var, ftype) in self._world_vars.items():
                raw = var.get()
                if ftype == "float":
                    setattr(wc, key, float(raw))
                elif ftype == "bool":
                    setattr(wc, key, bool(raw))
                else:
                    setattr(wc, key, raw)
            self.app.config_manager.save_world(wc)
            messagebox.showinfo("Saved", "World config saved.\nRestart the server for changes to take effect.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))
