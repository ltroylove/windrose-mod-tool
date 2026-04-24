import json
import threading
import customtkinter as ctk
from pathlib import Path
from tkinter import messagebox
from core import settings as cfg
from core import pak_generator

from ui.theme import ACCENT, CARD_BG, NAV_BG, MUTED

NAV_W = 168

# Keys with no backing mod data — sliders are shown but disabled with a notice
_UNSUPPORTED = {
    "loot_copper", "loot_animals",
    "spawn_copper", "spawn_iron", "spawn_sulfur", "spawn_stone",
    "spawn_softwood", "spawn_hardwood", "spawn_herbs",
}

# ── Presets ───────────────────────────────────────────────────────────────────

PRESETS = {
    "Vanilla": dict(
        stack_basic=50, stack_wood_products=30, stack_ore=50, stack_ingots=30,
        stack_textiles=30, stack_animal=30, stack_food=20, stack_alchemy=20,
        stack_ammo=200, stack_consumables=10,
        loot_softwood=1.0, loot_hardwood=1.0, loot_plague_wood=1.0,
        loot_copper=1.0, loot_iron=1.0, loot_sulfur=1.0,
        loot_stone=1.0, loot_ancient_debris=1.0, loot_herbs=1.0, loot_animals=1.0,
        spawn_copper_h=6.0,         spawn_copper_qty=1.0,
        spawn_iron_h=6.0,           spawn_iron_qty=1.0,
        spawn_sulfur_h=6.0,         spawn_sulfur_qty=1.0,
        spawn_stone_h=4.0,          spawn_stone_qty=1.0,
        spawn_ancient_debris_h=8.0, spawn_ancient_debris_qty=1.0,
        spawn_softwood_h=4.0,       spawn_softwood_qty=1.0,
        spawn_hardwood_h=6.0,       spawn_hardwood_qty=1.0,
        spawn_herbs_h=2.0,          spawn_herbs_qty=1.0,
        backpack_slots=1.0,
        fasttravel_bells=5,
        lantern_duration_min=15.0,
    ),
    "Relaxed": dict(
        stack_basic=500, stack_wood_products=200, stack_ore=500, stack_ingots=200,
        stack_textiles=200, stack_animal=200, stack_food=100, stack_alchemy=100,
        stack_ammo=1000, stack_consumables=50,
        loot_softwood=2.0, loot_hardwood=2.0, loot_plague_wood=2.0,
        loot_copper=2.0, loot_iron=2.0, loot_sulfur=2.0,
        loot_stone=2.0, loot_ancient_debris=2.0, loot_herbs=2.0, loot_animals=2.0,
        spawn_copper_h=3.0,         spawn_copper_qty=2.0,
        spawn_iron_h=3.0,           spawn_iron_qty=2.0,
        spawn_sulfur_h=3.0,         spawn_sulfur_qty=2.0,
        spawn_stone_h=2.0,          spawn_stone_qty=2.0,
        spawn_ancient_debris_h=4.0, spawn_ancient_debris_qty=2.0,
        spawn_softwood_h=2.0,       spawn_softwood_qty=2.0,
        spawn_hardwood_h=3.0,       spawn_hardwood_qty=2.0,
        spawn_herbs_h=1.0,          spawn_herbs_qty=2.0,
        backpack_slots=2.0,
        fasttravel_bells=20,
        lantern_duration_min=30.0,
    ),
    "Abundant": dict(
        stack_basic=999, stack_wood_products=999, stack_ore=999, stack_ingots=999,
        stack_textiles=999, stack_animal=999, stack_food=500, stack_alchemy=500,
        stack_ammo=9999, stack_consumables=200,
        loot_softwood=5.0, loot_hardwood=5.0, loot_plague_wood=5.0,
        loot_copper=5.0, loot_iron=5.0, loot_sulfur=5.0,
        loot_stone=5.0, loot_ancient_debris=5.0, loot_herbs=5.0, loot_animals=5.0,
        spawn_copper_h=1.0,         spawn_copper_qty=5.0,
        spawn_iron_h=1.0,           spawn_iron_qty=5.0,
        spawn_sulfur_h=1.0,         spawn_sulfur_qty=5.0,
        spawn_stone_h=1.0,          spawn_stone_qty=5.0,
        spawn_ancient_debris_h=2.0, spawn_ancient_debris_qty=5.0,
        spawn_softwood_h=1.0,       spawn_softwood_qty=5.0,
        spawn_hardwood_h=1.0,       spawn_hardwood_qty=5.0,
        spawn_herbs_h=0.5,          spawn_herbs_qty=5.0,
        backpack_slots=5.0,
        fasttravel_bells=50,
        lantern_duration_min=60.0,
    ),
}

# ── Category data ─────────────────────────────────────────────────────────────

STACKS = [
    ("stack_basic",        "Basic Materials",       "Wood, Stone, Clay, Plant Fiber"),
    ("stack_wood_products","Wood Products",          "Hardwood, Plague Wood, Planks, Timber, Charcoal, Bark"),
    ("stack_ore",          "Raw Ores",              "Copper Ore, Iron Ore, Sulfur, Stone, Coal, Obsidian"),
    ("stack_ingots",       "Ingots & Refined",      "Copper Ingot, Iron Ingot, Gold Ingot, Mire Metal Ingot"),
    ("stack_textiles",     "Textiles & Fibers",     "Flax Fiber, Coarse Fabric, Linen Fabric, Tarred Fabric"),
    ("stack_animal",       "Animal Materials",      "Bones, Rough Hide, Tanned Leather, Animal Fat, Feather"),
    ("stack_food",         "Food & Crops",          "Banana, Corn, Beans, Meat, Crab Meat, Cocoplum"),
    ("stack_alchemy",      "Alchemical Materials",  "Alchemical Base, Ash, Tar, Tannin, Healing Herbs"),
    ("stack_ammo",         "Ammunition",            "Cannonballs, Stone Bullets, Firearm Projectiles"),
    ("stack_consumables",  "Consumables & Potions", "Elixirs, Bandages, Healing Potions, Recall"),
]

LOOT = [
    ("loot_softwood",      "Softwood Trees",         "Wood, Tree Bark, Resin"),
    ("loot_hardwood",      "Hardwood Trees",          "Hardwood, Tree Bark"),
    ("loot_plague_wood",   "Plague Wood / Tar Trees", "Plague Wood, Tar, Tree Bark"),
    ("loot_copper",        "Copper Nodes",            "Copper Ore  (Coastal Jungle caves)"),
    ("loot_iron",          "Iron Nodes",              "Iron Ore, Volcanic Iron Ore  (Foothills & Volcanic)"),
    ("loot_sulfur",        "Sulfur Deposits",         "Sulfur  (Foothills & Volcanic rocks)"),
    ("loot_stone",         "Stone Nodes",             "Stone  (surface rocks, all biomes)"),
    ("loot_ancient_debris","Ancient Debris",          "Ancient Scraps → Mire Metal Ingot  (Cursed Swamp ruins)"),
    ("loot_herbs",         "Herb & Plant Patches",    "Healing Herbs, Flax Fiber, Aloe, Bromeliad"),
    ("loot_animals",       "Animal Drops",            "Meat, Rough Hide, Bones, Animal Fat, Feather"),
]

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

# ── Section registry — add new sections here ──────────────────────────────────
# Each entry: (nav_label, subtitle, builder_method_name)
SECTIONS = [
    ("Stack Sizes",    "Max items per inventory slot, by category.",          "_build_stacks"),
    ("Loot Drops",     "Multiply drop quantities per resource type.",          "_build_loot"),
    ("Spawners",       "Respawn timing and quantity per node type.",           "_build_spawners"),
    ("Backpack Slots", "Number of inventory slots per backpack tier.",         "_build_backpack"),
    ("Building Limits","Maximum number of placeable buildings per type.",      "_build_building_limits"),
    ("Consumables",    "Duration and charges for consumable items.",           "_build_consumables"),
]


class CreateTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._vars:       dict[str, ctk.Variable]  = {}
        self._entry_vars: dict[str, ctk.StringVar] = {}
        self._active_section = SECTIONS[0][0]
        self._nav_btns: dict[str, ctk.CTkButton]  = {}
        self._build()

    # ─────────────────────────────────────────────────────────────────
    # Top-level layout
    # ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── top bar (title + presets) ─────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text="Game Tuning",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        pf = ctk.CTkFrame(top, fg_color="transparent")
        pf.grid(row=0, column=2, sticky="e")
        ctk.CTkLabel(pf, text="Presets:", text_color="#6b7280").pack(side="left", padx=(0, 6))
        for name in PRESETS:
            ctk.CTkButton(
                pf, text=name, width=80, height=28,
                fg_color=CARD_BG, hover_color="#334155",
                font=ctk.CTkFont(size=12),
                command=lambda n=name: self._apply_preset(n),
            ).pack(side="left", padx=3)

        # ── left section nav ──────────────────────────────────────────
        nav = ctk.CTkFrame(self, width=NAV_W, fg_color=NAV_BG, corner_radius=8)
        nav.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        nav.grid_propagate(False)
        nav.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            nav, text="SECTIONS",
            font=ctk.CTkFont(size=10), text_color="#334155",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        for i, (label, _, _) in enumerate(SECTIONS):
            btn = ctk.CTkButton(
                nav, text=label, anchor="w", height=36,
                corner_radius=6, border_width=0,
                fg_color="transparent", hover_color="#1e293b",
                text_color="#64748b", font=ctk.CTkFont(size=13),
                command=lambda l=label: self._show_section(l),
            )
            btn.grid(row=i + 1, column=0, sticky="ew", padx=8, pady=2)
            self._nav_btns[label] = btn

        nav.grid_rowconfigure(len(SECTIONS) + 1, weight=1)

        # ── right content panel ───────────────────────────────────────
        self._content_host = ctk.CTkFrame(self, fg_color="transparent")
        self._content_host.grid(row=1, column=1, sticky="nsew")
        self._content_host.grid_columnconfigure(0, weight=1)
        self._content_host.grid_rowconfigure(0, weight=1)

        # pre-build all section frames (hidden until selected)
        self._section_frames: dict[str, ctk.CTkScrollableFrame] = {}
        for label, subtitle, builder in SECTIONS:
            sf = ctk.CTkScrollableFrame(self._content_host, fg_color="transparent")
            sf.grid(row=0, column=0, sticky="nsew")
            sf.grid_columnconfigure(0, weight=1)
            sf.grid_remove()
            self._section_frames[label] = sf
            getattr(self, builder)(sf, subtitle)

        # ── footer ────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        footer.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            footer, text="Pak Name:", text_color="#94a3b8",
        ).grid(row=0, column=0, padx=(14, 8), pady=10)
        self._name_var = ctk.StringVar(value="MyGameTuning")
        ctk.CTkEntry(footer, textvariable=self._name_var, width=200, height=32).grid(
            row=0, column=1, sticky="w", pady=10,
        )
        ctk.CTkButton(
            footer, text="Save Profile", width=110, height=32,
            fg_color="#1e3a5f", hover_color="#1e4a7f",
            command=self._save_profile,
        ).grid(row=0, column=2, padx=8, pady=10)
        self._gen_btn = ctk.CTkButton(
            footer, text="⚙  Generate Pak", width=140, height=32,
            fg_color=ACCENT, hover_color="#0f766e",
            command=self._generate,
        )
        self._gen_btn.grid(row=0, column=3, padx=(0, 14), pady=10)

        self._show_section(SECTIONS[0][0])

    # ─────────────────────────────────────────────────────────────────
    # Section navigation
    # ─────────────────────────────────────────────────────────────────

    def _show_section(self, label: str):
        self._active_section = label
        for name, btn in self._nav_btns.items():
            if name == label:
                btn.configure(fg_color=ACCENT, hover_color="#0f766e", text_color="white")
            else:
                btn.configure(fg_color="transparent", hover_color="#1e293b", text_color="#64748b")
        for name, frame in self._section_frames.items():
            if name == label:
                frame.grid()
            else:
                frame.grid_remove()

    # ─────────────────────────────────────────────────────────────────
    # Section builders
    # ─────────────────────────────────────────────────────────────────

    def _build_stacks(self, parent: ctk.CTkScrollableFrame, subtitle: str):
        self._section_header(parent, subtitle)
        parent.grid_columnconfigure(1, weight=1)

        # column headers
        for col, (txt, anchor) in enumerate([("CATEGORY", "w"), ("", "w"), ("MAX / SLOT", "e"), ("", "w")]):
            ctk.CTkLabel(
                parent, text=txt, anchor=anchor,
                text_color=MUTED, font=ctk.CTkFont(size=10),
            ).grid(row=2, column=col, padx=(14 if col == 0 else 4, 4), pady=(0, 4), sticky="ew")

        for r, (key, label, examples) in enumerate(STACKS):
            default = PRESETS["Relaxed"][key]
            var  = ctk.IntVar(value=default)
            evar = ctk.StringVar(value=str(default))
            self._vars[key]       = var
            self._entry_vars[key] = evar

            row = r + 3
            # name + examples stacked in col 0
            lf = ctk.CTkFrame(parent, fg_color="transparent")
            lf.grid(row=row, column=0, padx=14, pady=4, sticky="w")
            ctk.CTkLabel(lf, text=label, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(lf, text=examples, anchor="w",
                         text_color="#64748b", font=ctk.CTkFont(size=11),
                         wraplength=200).pack(anchor="w")

            ctk.CTkSlider(
                parent, from_=1, to=99999, variable=var,
                button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                command=lambda v, k=key: self._slide_int(k, v),
            ).grid(row=row, column=1, padx=(8, 8), pady=4, sticky="ew")

            entry = ctk.CTkEntry(parent, textvariable=evar, width=72, height=28, justify="right")
            entry.grid(row=row, column=2, padx=(0, 4), pady=4)
            evar.trace_add("write", lambda *_, k=key, ev=evar: self._entry_int(k, ev, 1, 99999))

            ctk.CTkLabel(
                parent, text="items", text_color=MUTED,
                font=ctk.CTkFont(size=11), width=40, anchor="w",
            ).grid(row=row, column=3, padx=(0, 14), pady=4)

    def _build_loot(self, parent: ctk.CTkScrollableFrame, subtitle: str):
        self._section_header(parent, subtitle)
        parent.grid_columnconfigure(1, weight=1)

        for col, (txt, anchor) in enumerate([("SOURCE", "w"), ("", "w"), ("MULTIPLIER", "e"), ("", "w")]):
            ctk.CTkLabel(
                parent, text=txt, anchor=anchor,
                text_color=MUTED, font=ctk.CTkFont(size=10),
            ).grid(row=2, column=col, padx=(14 if col == 0 else 4, 4), pady=(0, 4), sticky="ew")

        for r, (key, label, drops) in enumerate(LOOT):
            default = PRESETS["Relaxed"][key]
            var  = ctk.DoubleVar(value=default)
            evar = ctk.StringVar(value=f"{default:.2f}")
            self._vars[key]       = var
            self._entry_vars[key] = evar

            row = r + 3
            unsupported = key in _UNSUPPORTED
            name_color  = "#374151" if unsupported else None

            lf = ctk.CTkFrame(parent, fg_color="transparent")
            lf.grid(row=row, column=0, padx=14, pady=4, sticky="w")
            ctk.CTkLabel(lf, text=label, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=name_color or "white").pack(anchor="w")
            ctk.CTkLabel(lf, text=drops, anchor="w",
                         text_color="#374151" if unsupported else "#64748b",
                         font=ctk.CTkFont(size=11), wraplength=200).pack(anchor="w")

            if unsupported:
                ctk.CTkLabel(
                    parent, text="No mod data available yet",
                    text_color="#374151", font=ctk.CTkFont(size=11), anchor="w",
                ).grid(row=row, column=1, columnspan=3, padx=8, pady=4, sticky="w")
            else:
                ctk.CTkSlider(
                    parent, from_=0.1, to=100.0, variable=var,
                    button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                    command=lambda v, k=key: self._slide_float(k, v),
                ).grid(row=row, column=1, padx=(8, 8), pady=4, sticky="ew")

                entry = ctk.CTkEntry(parent, textvariable=evar, width=72, height=28, justify="right")
                entry.grid(row=row, column=2, padx=(0, 4), pady=4)
                evar.trace_add("write", lambda *_, k=key, ev=evar: self._entry_float(k, ev, 0.1, 100.0))

                ctk.CTkLabel(
                    parent, text="×", text_color=MUTED,
                    font=ctk.CTkFont(size=12), width=24, anchor="w",
                ).grid(row=row, column=3, padx=(0, 14), pady=4)

    def _build_spawners(self, parent: ctk.CTkScrollableFrame, subtitle: str):
        self._section_header(parent, subtitle)

        # column headers
        ctk.CTkLabel(parent, text="RESOURCE", width=160, anchor="w",
                     text_color=MUTED, font=ctk.CTkFont(size=10),
        ).grid(row=2, column=0, padx=14, pady=(0, 4))
        ctk.CTkLabel(parent, text="RESPAWN TIME", anchor="w",
                     text_color=MUTED, font=ctk.CTkFont(size=10),
        ).grid(row=2, column=1, columnspan=3, padx=4, pady=(0, 4), sticky="w")
        ctk.CTkLabel(parent, text="QUANTITY MULTIPLIER", anchor="w",
                     text_color=MUTED, font=ctk.CTkFont(size=10),
        ).grid(row=2, column=4, columnspan=3, padx=4, pady=(0, 4), sticky="w")

        for r, (prefix, label) in enumerate(SPAWNERS):
            h_key   = f"{prefix}_h"
            qty_key = f"{prefix}_qty"
            h_def   = PRESETS["Relaxed"][h_key]
            qty_def = PRESETS["Relaxed"][qty_key]

            h_var    = ctk.DoubleVar(value=h_def)
            h_evar   = ctk.StringVar(value=f"{h_def:.2f}")
            qty_var  = ctk.DoubleVar(value=qty_def)
            qty_evar = ctk.StringVar(value=f"{qty_def:.2f}")

            self._vars[h_key]         = h_var
            self._entry_vars[h_key]   = h_evar
            self._vars[qty_key]       = qty_var
            self._entry_vars[qty_key] = qty_evar

            unsupported  = prefix in _UNSUPPORTED
            name_color   = "#374151" if unsupported else "white"

            row = r + 3
            ctk.CTkLabel(
                parent, text=label, width=160, anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"), text_color=name_color,
            ).grid(row=row, column=0, padx=14, pady=6, sticky="w")

            if unsupported:
                ctk.CTkLabel(
                    parent, text="No mod data available yet",
                    text_color="#374151", font=ctk.CTkFont(size=11), anchor="w",
                ).grid(row=row, column=1, columnspan=6, padx=4, pady=6, sticky="w")
                continue

            ctk.CTkSlider(
                parent, from_=0.25, to=48.0, variable=h_var, width=180,
                button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                command=lambda v, k=h_key: self._slide_float(k, v),
            ).grid(row=row, column=1, padx=(4, 6), pady=6)
            h_entry = ctk.CTkEntry(parent, textvariable=h_evar, width=60, height=28, justify="right")
            h_entry.grid(row=row, column=2, padx=(0, 2), pady=6)
            h_evar.trace_add("write", lambda *_, k=h_key, ev=h_evar: self._entry_float(k, ev, 0.25, 48.0))
            ctk.CTkLabel(
                parent, text="hrs", text_color=MUTED,
                font=ctk.CTkFont(size=11), width=30,
            ).grid(row=row, column=3, padx=(0, 16), pady=6)

            ctk.CTkSlider(
                parent, from_=0.1, to=20.0, variable=qty_var, width=180,
                button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                command=lambda v, k=qty_key: self._slide_float(k, v),
            ).grid(row=row, column=4, padx=(4, 6), pady=6)
            qty_entry = ctk.CTkEntry(parent, textvariable=qty_evar, width=60, height=28, justify="right")
            qty_entry.grid(row=row, column=5, padx=(0, 2), pady=6)
            qty_evar.trace_add("write", lambda *_, k=qty_key, ev=qty_evar: self._entry_float(k, ev, 0.1, 20.0))
            ctk.CTkLabel(
                parent, text="×", text_color=MUTED,
                font=ctk.CTkFont(size=12), width=24,
            ).grid(row=row, column=6, padx=(0, 14), pady=6)

    def _build_backpack(self, parent: ctk.CTkScrollableFrame, subtitle: str):
        self._section_header(parent, subtitle)
        parent.grid_columnconfigure(1, weight=1)

        for col, (txt, anchor) in enumerate([("TIER", "w"), ("", "w"), ("MULTIPLIER", "e"), ("", "w")]):
            ctk.CTkLabel(
                parent, text=txt, anchor=anchor,
                text_color=MUTED, font=ctk.CTkFont(size=10),
            ).grid(row=2, column=col, padx=(14 if col == 0 else 4, 4), pady=(0, 4), sticky="ew")

        rows = [
            ("backpack_slots", "Backpack Slot Multiplier",
             "Scales all tiers proportionally. Vanilla: 4 / 8 / 12 / 16 / 20 slots per tier."),
        ]
        for r, (key, label, desc) in enumerate(rows):
            default = PRESETS["Relaxed"][key]
            var  = ctk.DoubleVar(value=default)
            evar = ctk.StringVar(value=f"{default:.1f}")
            self._vars[key]       = var
            self._entry_vars[key] = evar

            row = r + 3
            lf = ctk.CTkFrame(parent, fg_color="transparent")
            lf.grid(row=row, column=0, padx=14, pady=4, sticky="w")
            ctk.CTkLabel(lf, text=label, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(lf, text=desc, anchor="w",
                         text_color="#64748b", font=ctk.CTkFont(size=11),
                         wraplength=200).pack(anchor="w")

            def _slide_backpack(v, k=key, ev=evar):
                val = round(float(v), 1)
                self._vars[k].set(val)
                ev.set(f"{val:.1f}")

            ctk.CTkSlider(
                parent, from_=1.0, to=10.0, variable=var,
                button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                command=_slide_backpack,
            ).grid(row=row, column=1, padx=(8, 8), pady=4, sticky="ew")

            entry = ctk.CTkEntry(parent, textvariable=evar, width=72, height=28, justify="right")
            entry.grid(row=row, column=2, padx=(0, 4), pady=4)
            evar.trace_add("write", lambda *_, k=key, ev=evar: self._entry_float(k, ev, 1.0, 10.0))

            ctk.CTkLabel(
                parent, text="×", text_color=MUTED,
                font=ctk.CTkFont(size=12), width=24, anchor="w",
            ).grid(row=row, column=3, padx=(0, 14), pady=4)

    def _build_building_limits(self, parent: ctk.CTkScrollableFrame, subtitle: str):
        self._section_header(parent, subtitle)
        parent.grid_columnconfigure(1, weight=1)

        for col, (txt, anchor) in enumerate([("BUILDING", "w"), ("", "w"), ("MAX COUNT", "e"), ("", "w")]):
            ctk.CTkLabel(
                parent, text=txt, anchor=anchor,
                text_color=MUTED, font=ctk.CTkFont(size=10),
            ).grid(row=2, column=col, padx=(14 if col == 0 else 4, 4), pady=(0, 4), sticky="ew")

        rows = [
            ("fasttravel_bells", "Fast Travel Bells",
             "Max Fast Travel Bells placeable per world. Vanilla ≈ 5 (assumed)."),
        ]
        for r, (key, label, desc) in enumerate(rows):
            default = PRESETS["Relaxed"][key]
            var  = ctk.IntVar(value=default)
            evar = ctk.StringVar(value=str(default))
            self._vars[key]       = var
            self._entry_vars[key] = evar

            row = r + 3
            lf = ctk.CTkFrame(parent, fg_color="transparent")
            lf.grid(row=row, column=0, padx=14, pady=4, sticky="w")
            ctk.CTkLabel(lf, text=label, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(lf, text=desc, anchor="w",
                         text_color="#64748b", font=ctk.CTkFont(size=11),
                         wraplength=200).pack(anchor="w")

            ctk.CTkSlider(
                parent, from_=1, to=100, variable=var,
                button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                command=lambda v, k=key: self._slide_int(k, v),
            ).grid(row=row, column=1, padx=(8, 8), pady=4, sticky="ew")

            entry = ctk.CTkEntry(parent, textvariable=evar, width=72, height=28, justify="right")
            entry.grid(row=row, column=2, padx=(0, 4), pady=4)
            evar.trace_add("write", lambda *_, k=key, ev=evar: self._entry_int(k, ev, 1, 100))

            ctk.CTkLabel(
                parent, text="bells", text_color=MUTED,
                font=ctk.CTkFont(size=11), width=40, anchor="w",
            ).grid(row=row, column=3, padx=(0, 14), pady=4)

    def _build_consumables(self, parent: ctk.CTkScrollableFrame, subtitle: str):
        self._section_header(parent, subtitle)
        parent.grid_columnconfigure(1, weight=1)

        for col, (txt, anchor) in enumerate([("ITEM", "w"), ("", "w"), ("DURATION", "e"), ("", "w")]):
            ctk.CTkLabel(
                parent, text=txt, anchor=anchor,
                text_color=MUTED, font=ctk.CTkFont(size=10),
            ).grid(row=2, column=col, padx=(14 if col == 0 else 4, 4), pady=(0, 4), sticky="ew")

        rows = [
            ("lantern_duration_min", "Lantern Burn Duration",
             "How long a lantern burns before needing refuel. Vanilla = 15 min."),
        ]
        for r, (key, label, desc) in enumerate(rows):
            default = PRESETS["Relaxed"][key]
            var  = ctk.DoubleVar(value=default)
            evar = ctk.StringVar(value=f"{default:.0f}")
            self._vars[key]       = var
            self._entry_vars[key] = evar

            row = r + 3
            lf = ctk.CTkFrame(parent, fg_color="transparent")
            lf.grid(row=row, column=0, padx=14, pady=4, sticky="w")
            ctk.CTkLabel(lf, text=label, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(lf, text=desc, anchor="w",
                         text_color="#64748b", font=ctk.CTkFont(size=11),
                         wraplength=200).pack(anchor="w")

            def _slide_lantern(v, k=key, ev=evar):
                val = round(float(v))
                self._vars[k].set(val)
                ev.set(str(val))

            ctk.CTkSlider(
                parent, from_=15.0, to=120.0, variable=var,
                button_color=ACCENT, button_hover_color="#0f766e", progress_color=ACCENT,
                command=_slide_lantern,
            ).grid(row=row, column=1, padx=(8, 8), pady=4, sticky="ew")

            entry = ctk.CTkEntry(parent, textvariable=evar, width=72, height=28, justify="right")
            entry.grid(row=row, column=2, padx=(0, 4), pady=4)
            evar.trace_add("write", lambda *_, k=key, ev=evar: self._entry_float(k, ev, 15.0, 120.0))

            ctk.CTkLabel(
                parent, text="min", text_color=MUTED,
                font=ctk.CTkFont(size=11), width=40, anchor="w",
            ).grid(row=row, column=3, padx=(0, 14), pady=4)

    # ─────────────────────────────────────────────────────────────────
    # Shared helpers
    # ─────────────────────────────────────────────────────────────────

    def _section_header(self, parent: ctk.CTkScrollableFrame, subtitle: str):
        ctk.CTkLabel(
            parent, text=subtitle,
            font=ctk.CTkFont(size=11), text_color="#64748b", anchor="w",
        ).grid(row=0, column=0, columnspan=8, sticky="w", padx=2, pady=(0, 2))
        ctk.CTkFrame(parent, height=1, fg_color="#1e293b").grid(
            row=1, column=0, columnspan=8, sticky="ew", pady=(0, 8),
        )

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

    # ─────────────────────────────────────────────────────────────────
    # Save / Generate
    # ─────────────────────────────────────────────────────────────────

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
                + "\n\nRe-extract using the commands in Docs/DevNotes/tools-setup.md.",
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
            f"  Stack entries    : {counts['stacks']}\n"
            f"  Loot entries     : {counts['loot']}\n"
            f"  Spawner entries  : {counts['spawners']}\n"
            f"  Backpack entries : {counts['backpack']}\n"
            f"  Building limits  : {counts['build_limits']}\n"
            f"  Lantern entries  : {counts['lantern_item'] + counts['lantern_recipe']}\n\n"
            f"File: {counts['path'].name}\n"
            f"Location: {counts['path'].parent}",
        )

    def _on_generate_error(self, msg: str):
        self._gen_btn.configure(state="normal", text="⚙  Generate Pak")
        messagebox.showerror("Generation Failed", msg)
