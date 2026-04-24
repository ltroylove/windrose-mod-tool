import json
import threading
import customtkinter as ctk
from pathlib import Path
from tkinter import messagebox
from core import settings as cfg
from core import pak_generator

ACCENT = "#0d9488"

# ── Presets ───────────────────────────────────────────────────────────────────

PRESETS = {
    "Vanilla": dict(
        stack_basic=50, stack_wood_products=30, stack_ore=50, stack_ingots=30,
        stack_textiles=30, stack_animal=30, stack_food=20, stack_alchemy=20,
        stack_ammo=200, stack_consumables=10,
        loot_softwood=1.0, loot_hardwood=1.0, loot_plague_wood=1.0,
        loot_copper=1.0, loot_iron=1.0, loot_sulfur=1.0,
        loot_stone=1.0, loot_ancient_debris=1.0, loot_herbs=1.0, loot_animals=1.0,
        spawn_copper_h=6.0,        spawn_copper_qty=1.0,
        spawn_iron_h=6.0,          spawn_iron_qty=1.0,
        spawn_sulfur_h=6.0,        spawn_sulfur_qty=1.0,
        spawn_stone_h=4.0,         spawn_stone_qty=1.0,
        spawn_ancient_debris_h=8.0,spawn_ancient_debris_qty=1.0,
        spawn_softwood_h=4.0,      spawn_softwood_qty=1.0,
        spawn_hardwood_h=6.0,      spawn_hardwood_qty=1.0,
        spawn_herbs_h=2.0,         spawn_herbs_qty=1.0,
    ),
    "Relaxed": dict(
        stack_basic=500, stack_wood_products=200, stack_ore=500, stack_ingots=200,
        stack_textiles=200, stack_animal=200, stack_food=100, stack_alchemy=100,
        stack_ammo=1000, stack_consumables=50,
        loot_softwood=2.0, loot_hardwood=2.0, loot_plague_wood=2.0,
        loot_copper=2.0, loot_iron=2.0, loot_sulfur=2.0,
        loot_stone=2.0, loot_ancient_debris=2.0, loot_herbs=2.0, loot_animals=2.0,
        spawn_copper_h=3.0,        spawn_copper_qty=2.0,
        spawn_iron_h=3.0,          spawn_iron_qty=2.0,
        spawn_sulfur_h=3.0,        spawn_sulfur_qty=2.0,
        spawn_stone_h=2.0,         spawn_stone_qty=2.0,
        spawn_ancient_debris_h=4.0,spawn_ancient_debris_qty=2.0,
        spawn_softwood_h=2.0,      spawn_softwood_qty=2.0,
        spawn_hardwood_h=3.0,      spawn_hardwood_qty=2.0,
        spawn_herbs_h=1.0,         spawn_herbs_qty=2.0,
    ),
    "Abundant": dict(
        stack_basic=999, stack_wood_products=999, stack_ore=999, stack_ingots=999,
        stack_textiles=999, stack_animal=999, stack_food=500, stack_alchemy=500,
        stack_ammo=9999, stack_consumables=200,
        loot_softwood=5.0, loot_hardwood=5.0, loot_plague_wood=5.0,
        loot_copper=5.0, loot_iron=5.0, loot_sulfur=5.0,
        loot_stone=5.0, loot_ancient_debris=5.0, loot_herbs=5.0, loot_animals=5.0,
        spawn_copper_h=1.0,        spawn_copper_qty=5.0,
        spawn_iron_h=1.0,          spawn_iron_qty=5.0,
        spawn_sulfur_h=1.0,        spawn_sulfur_qty=5.0,
        spawn_stone_h=1.0,         spawn_stone_qty=5.0,
        spawn_ancient_debris_h=2.0,spawn_ancient_debris_qty=5.0,
        spawn_softwood_h=1.0,      spawn_softwood_qty=5.0,
        spawn_hardwood_h=1.0,      spawn_hardwood_qty=5.0,
        spawn_herbs_h=0.5,         spawn_herbs_qty=5.0,
    ),
}

# ── Stack size rows: (key, label, example items) ──────────────────────────────

STACKS = [
    ("stack_basic",        "Basic Materials",       "Wood, Stone, Clay, Plant Fiber"),
    ("stack_wood_products","Wood Products",          "Hardwood, Plague Wood, Planks, Timber, Charcoal, Bark"),
    ("stack_ore",          "Raw Ores",              "Copper Ore, Iron Ore, Gold Ore, Silver Ore, Sulfur"),
    ("stack_ingots",       "Ingots & Refined",      "Copper Ingot, Iron Ingot, Gold Ingot, Mire Metal Ingot"),
    ("stack_textiles",     "Textiles & Fibers",     "Flax Fiber, Coarse Fabric, Linen Fabric, Tarred Fabric"),
    ("stack_animal",       "Animal Materials",      "Bones, Rough Hide, Tanned Leather, Animal Fat, Feather"),
    ("stack_food",         "Food & Crops",          "Banana, Corn, Beans, Meat, Crab Meat, Cocoplum"),
    ("stack_alchemy",      "Alchemical Materials",  "Alchemical Base, Ash, Tar, Gunpowder, Tannin, Healing Herbs"),
    ("stack_ammo",         "Ammunition",            "Cannonballs, Stone Bullets, Arrows, Spears"),
    ("stack_consumables",  "Consumables & Potions", "Elixirs, Bandages, Cooked Meals"),
]

# ── Loot drop rows: (key, label, dropped from) ────────────────────────────────

LOOT = [
    ("loot_softwood",      "Softwood Trees",          "Wood, Tree Bark, Resin"),
    ("loot_hardwood",      "Hardwood Trees",           "Hardwood, Tree Bark"),
    ("loot_plague_wood",   "Plague Wood / Tar Trees",  "Plague Wood, Tar, Tree Bark"),
    ("loot_copper",        "Copper Nodes",             "Copper Ore  (Coastal Jungle caves)"),
    ("loot_iron",          "Iron Nodes",               "Iron Ore, Foothills Iron Ore  (Foothills & Volcanic)"),
    ("loot_sulfur",        "Sulfur Deposits",          "Sulfur  (Foothills & Volcanic rocks)"),
    ("loot_stone",         "Stone Nodes",              "Stone  (surface rocks, all biomes)"),
    ("loot_ancient_debris","Ancient Debris",           "Ancient Scraps → Mire Metal Ingot  (Cursed Swamp ruins)"),
    ("loot_herbs",         "Herb & Plant Patches",     "Healing Herbs, Flax Fiber, Aloe, Bromeliad"),
    ("loot_animals",       "Animal Drops",             "Meat, Rough Hide, Bones, Animal Fat, Feather"),
]

# ── Spawner rows: (key_prefix, label) ─────────────────────────────────────────

SPAWNERS = [
    ("spawn_copper",        "Copper Nodes"),
    ("spawn_iron",          "Iron Nodes"),
    ("spawn_sulfur",        "Sulfur Deposits"),
    ("spawn_stone",         "Stone Nodes"),
    ("spawn_ancient_debris","Ancient Debris  (Swamp)"),
    ("spawn_softwood",      "Softwood Trees"),
    ("spawn_hardwood",      "Hardwood Trees"),
    ("spawn_herbs",         "Herb Patches"),
]


class CreateTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._vars: dict[str, ctk.Variable] = {}
        self._entry_vars: dict[str, ctk.StringVar] = {}
        self._build()

    # ─────────────────────────────────────────────────────────────────
    # Layout
    # ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(top, text="Game Tuning", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")

        pf = ctk.CTkFrame(top, fg_color="transparent")
        pf.grid(row=0, column=2, sticky="e")
        ctk.CTkLabel(pf, text="Presets:", text_color="#6b7280").pack(side="left", padx=(0, 6))
        for name in PRESETS:
            ctk.CTkButton(pf, text=name, width=82, height=30,
                          fg_color="#1e293b", hover_color="#334155",
                          font=ctk.CTkFont(size=12),
                          command=lambda n=name: self._apply_preset(n)).pack(side="left", padx=3)

        # body
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        self._build_stacks(body, 0)
        self._build_loot(body, 1)
        self._build_spawning(body, 2)

        # footer
        footer = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
        footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        footer.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(footer, text="Pak Name:", text_color="#94a3b8").grid(row=0, column=0, padx=(14, 8), pady=10)
        self._name_var = ctk.StringVar(value="MyGameTuning")
        ctk.CTkEntry(footer, textvariable=self._name_var, width=200, height=32).grid(row=0, column=1, sticky="w", pady=10)
        ctk.CTkButton(footer, text="Save Profile", width=110, height=32,
                      fg_color="#1e3a5f", hover_color="#1e4a7f",
                      command=self._save_profile).grid(row=0, column=2, padx=8, pady=10)
        self._gen_btn = ctk.CTkButton(footer, text="⚙  Generate Pak", width=140, height=32,
                                       fg_color=ACCENT, hover_color="#0f766e",
                                       command=self._generate)
        self._gen_btn.grid(row=0, column=3, padx=(0, 14), pady=10)

    # ─────────────────────────────────────────────────────────────────
    # Section builders
    # ─────────────────────────────────────────────────────────────────

    def _build_stacks(self, parent, idx):
        card = self._card(parent, idx, "Stack Sizes",
                          "Maximum items per inventory slot, by item category.")
        card.grid_columnconfigure(2, weight=1)

        # column headers
        for col, (txt, w) in enumerate([("CATEGORY", 170), ("EXAMPLES", 0), ("", 0), ("MAX ITEMS", 80)]):
            ctk.CTkLabel(card, text=txt, width=w, anchor="w",
                         text_color="#475569", font=ctk.CTkFont(size=10)).grid(
                row=3, column=col, padx=(14 if col == 0 else 4, 4), pady=(0, 4), sticky="w")

        for row_i, (key, label, examples) in enumerate(STACKS):
            default = PRESETS["Relaxed"][key]
            var = ctk.IntVar(value=default)
            evar = ctk.StringVar(value=str(default))
            self._vars[key] = var
            self._entry_vars[key] = evar

            r = row_i + 4
            ctk.CTkLabel(card, text=label, width=170, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).grid(row=r, column=0, padx=14, pady=5, sticky="w")
            ctk.CTkLabel(card, text=examples, anchor="w", text_color="#475569",
                         font=ctk.CTkFont(size=11)).grid(row=r, column=1, columnspan=2, padx=4, pady=5, sticky="w")

            slider = ctk.CTkSlider(card, from_=1, to=99999, variable=var, width=260,
                                   button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                                   command=lambda v, k=key: self._slide_int(k, v))
            slider.grid(row=r, column=2, padx=8, pady=5, sticky="ew")

            entry = ctk.CTkEntry(card, textvariable=evar, width=72, height=28, justify="right")
            entry.grid(row=r, column=3, padx=(0, 4), pady=5)
            evar.trace_add("write", lambda *_, k=key, ev=evar: self._entry_int(k, ev, 1, 99999))

            ctk.CTkLabel(card, text="items", text_color="#475569",
                         font=ctk.CTkFont(size=11), width=40, anchor="w").grid(row=r, column=4, padx=(0, 14), pady=5)

        ctk.CTkFrame(card, height=8, fg_color="transparent").grid(row=len(STACKS) + 4, column=0)

    def _build_loot(self, parent, idx):
        card = self._card(parent, idx, "Loot Drop Multipliers",
                          "Multiply how many items drop when harvesting each source type.")
        card.grid_columnconfigure(2, weight=1)

        for col, txt in enumerate(["SOURCE", "DROPS", "", "MULTIPLIER"]):
            ctk.CTkLabel(card, text=txt, anchor="w",
                         text_color="#475569", font=ctk.CTkFont(size=10)).grid(
                row=3, column=col, padx=(14 if col == 0 else 4, 4), pady=(0, 4), sticky="w")

        for row_i, (key, label, drops) in enumerate(LOOT):
            default = PRESETS["Relaxed"][key]
            var = ctk.DoubleVar(value=default)
            evar = ctk.StringVar(value=f"{default:.2f}")
            self._vars[key] = var
            self._entry_vars[key] = evar

            r = row_i + 4
            ctk.CTkLabel(card, text=label, width=170, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).grid(row=r, column=0, padx=14, pady=5, sticky="w")
            ctk.CTkLabel(card, text=drops, anchor="w", text_color="#475569",
                         font=ctk.CTkFont(size=11)).grid(row=r, column=1, columnspan=2, padx=4, pady=5, sticky="w")

            slider = ctk.CTkSlider(card, from_=0.1, to=100.0, variable=var, width=260,
                                   button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                                   command=lambda v, k=key: self._slide_float(k, v))
            slider.grid(row=r, column=2, padx=8, pady=5, sticky="ew")

            entry = ctk.CTkEntry(card, textvariable=evar, width=72, height=28, justify="right")
            entry.grid(row=r, column=3, padx=(0, 4), pady=5)
            evar.trace_add("write", lambda *_, k=key, ev=evar: self._entry_float(k, ev, 0.1, 100.0))

            ctk.CTkLabel(card, text="×", text_color="#475569",
                         font=ctk.CTkFont(size=12), width=24, anchor="w").grid(row=r, column=4, padx=(0, 14), pady=5)

        ctk.CTkFrame(card, height=8, fg_color="transparent").grid(row=len(LOOT) + 4, column=0)

    def _build_spawning(self, parent, idx):
        card = self._card(parent, idx, "Resource Spawning",
                          "How quickly each resource type respawns and in what quantity.")

        # sub-header columns
        ctk.CTkLabel(card, text="RESOURCE", width=160, anchor="w",
                     text_color="#475569", font=ctk.CTkFont(size=10)).grid(row=3, column=0, padx=14, pady=(0, 4))
        ctk.CTkLabel(card, text="RESPAWN TIME", anchor="w",
                     text_color="#475569", font=ctk.CTkFont(size=10)).grid(row=3, column=1, columnspan=3, padx=4, pady=(0, 4), sticky="w")
        ctk.CTkLabel(card, text="QUANTITY MULTIPLIER", anchor="w",
                     text_color="#475569", font=ctk.CTkFont(size=10)).grid(row=3, column=4, columnspan=3, padx=4, pady=(0, 4), sticky="w")

        for row_i, (prefix, label) in enumerate(SPAWNERS):
            h_key   = f"{prefix}_h"
            qty_key = f"{prefix}_qty"
            h_def   = PRESETS["Relaxed"][h_key]
            qty_def = PRESETS["Relaxed"][qty_key]

            h_var   = ctk.DoubleVar(value=h_def)
            h_evar  = ctk.StringVar(value=f"{h_def:.2f}")
            qty_var  = ctk.DoubleVar(value=qty_def)
            qty_evar = ctk.StringVar(value=f"{qty_def:.2f}")

            self._vars[h_key]    = h_var
            self._entry_vars[h_key] = h_evar
            self._vars[qty_key]  = qty_var
            self._entry_vars[qty_key] = qty_evar

            r = row_i + 4
            ctk.CTkLabel(card, text=label, width=160, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).grid(row=r, column=0, padx=14, pady=6, sticky="w")

            # respawn slider + entry
            h_slider = ctk.CTkSlider(card, from_=0.25, to=48.0, variable=h_var, width=200,
                                     button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                                     command=lambda v, k=h_key: self._slide_float(k, v))
            h_slider.grid(row=r, column=1, padx=(4, 6), pady=6)
            h_entry = ctk.CTkEntry(card, textvariable=h_evar, width=60, height=28, justify="right")
            h_entry.grid(row=r, column=2, padx=(0, 2), pady=6)
            h_evar.trace_add("write", lambda *_, k=h_key, ev=h_evar: self._entry_float(k, ev, 0.25, 48.0))
            ctk.CTkLabel(card, text="hrs", text_color="#475569",
                         font=ctk.CTkFont(size=11), width=30).grid(row=r, column=3, padx=(0, 16), pady=6)

            # quantity slider + entry
            qty_slider = ctk.CTkSlider(card, from_=0.1, to=20.0, variable=qty_var, width=200,
                                       button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                                       command=lambda v, k=qty_key: self._slide_float(k, v))
            qty_slider.grid(row=r, column=4, padx=(4, 6), pady=6)
            qty_entry = ctk.CTkEntry(card, textvariable=qty_evar, width=60, height=28, justify="right")
            qty_entry.grid(row=r, column=5, padx=(0, 2), pady=6)
            qty_evar.trace_add("write", lambda *_, k=qty_key, ev=qty_evar: self._entry_float(k, ev, 0.1, 20.0))
            ctk.CTkLabel(card, text="×", text_color="#475569",
                         font=ctk.CTkFont(size=12), width=24).grid(row=r, column=6, padx=(0, 14), pady=6)

        ctk.CTkFrame(card, height=8, fg_color="transparent").grid(row=len(SPAWNERS) + 4, column=0)

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────

    def _card(self, parent, idx, title, desc) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color="#1e293b")
        card.grid(row=idx, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, columnspan=8, sticky="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=11), text_color="#6b7280").grid(
            row=1, column=0, columnspan=8, sticky="w", padx=14, pady=(0, 6))
        ctk.CTkFrame(card, height=1, fg_color="#334155").grid(
            row=2, column=0, columnspan=8, sticky="ew", padx=14, pady=(0, 4))
        return card

    def _slide_int(self, key, value):
        v = int(round(value))
        self._vars[key].set(v)
        self._entry_vars[key].set(str(v))

    def _slide_float(self, key, value):
        v = round(float(value), 2)
        self._vars[key].set(v)
        self._entry_vars[key].set(f"{v:.2f}")

    def _entry_int(self, key, evar, lo, hi):
        try:
            v = max(lo, min(hi, int(evar.get())))
            self._vars[key].set(v)
        except ValueError:
            pass

    def _entry_float(self, key, evar, lo, hi):
        try:
            v = max(lo, min(hi, float(evar.get())))
            self._vars[key].set(v)
        except ValueError:
            pass

    def _apply_preset(self, name: str):
        preset = PRESETS[name]
        for key, val in preset.items():
            if key not in self._vars:
                continue
            self._vars[key].set(val)
            if key in self._entry_vars:
                if isinstance(self._vars[key], ctk.IntVar):
                    self._entry_vars[key].set(str(int(val)))
                else:
                    self._entry_vars[key].set(f"{float(val):.2f}")

    def _collect(self) -> dict:
        return {k: v.get() for k, v in self._vars.items()}

    def _save_profile(self):
        s = cfg.load()
        out_dir = Path(s.get("my_mods_path", "MyMods"))
        out_dir.mkdir(parents=True, exist_ok=True)
        name = (self._name_var.get().strip() or "MyGameTuning").replace(" ", "_")
        path = out_dir / f"{name}.profile.json"
        data = {"name": name, "values": self._collect()}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        messagebox.showinfo("Profile Saved", f"Saved to:\n{path}")

    def _generate(self):
        missing = pak_generator.check_sources()
        if missing:
            messagebox.showerror(
                "Missing Data",
                "Extracted mod data is missing:\n\n"
                + "\n".join(f"• {m}" for m in missing)
                + "\n\nRun the extraction step from the project README.",
            )
            return

        s = cfg.load()
        game_path = s.get("game_path", "")
        if not game_path:
            messagebox.showerror("No Game Path", "Set your game path in Settings first.")
            return

        from core.paths import GamePaths
        gp = GamePaths(Path(game_path))
        if not gp.is_valid():
            messagebox.showerror("Invalid Game Path", "Game path is not valid. Check Settings.")
            return

        pak_name = (self._name_var.get().strip() or "MyGameTuning").replace(" ", "_")
        if not pak_name.endswith("_P"):
            pak_name += "_P"

        output_dir = gp.client_mods
        output_dir.mkdir(parents=True, exist_ok=True)

        # Disable button during generation
        self._gen_btn.configure(state="disabled", text="Generating…")
        self.update_idletasks()

        def _run():
            try:
                counts = pak_generator.generate(self._collect(), pak_name, output_dir)
                self.after(0, lambda: self._on_generate_done(counts))
            except Exception as exc:
                self.after(0, lambda: self._on_generate_error(str(exc)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_generate_done(self, counts: dict):
        self._gen_btn.configure(state="normal", text="⚙  Generate Pak")
        messagebox.showinfo(
            "Pak Generated",
            f"Mod pak created successfully!\n\n"
            f"  Stack entries : {counts['stacks']}\n"
            f"  Loot entries  : {counts['loot']}\n"
            f"  Spawner entries: {counts['spawners']}\n\n"
            f"File: {counts['path'].name}\n"
            f"Location: {counts['path'].parent}",
        )

    def _on_generate_error(self, msg: str):
        self._gen_btn.configure(state="normal", text="⚙  Generate Pak")
        messagebox.showerror("Generation Failed", msg)
