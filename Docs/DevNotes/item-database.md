# Windrose Item Database

Reference for all item categories our tool can modify. Derived from extracting the MoreStacks 100x mod pak (`tools/extracted/`).

---

## How items are categorized

Our tool maps items to one of 10 stack-size categories. The mapping uses keyword matching against the item's file path. The matching rules are in `core/pak_generator.py` → `STACK_RULES`.

Category priority (first match wins):
1. `stack_ammo`
2. `stack_consumables`
3. `stack_food`
4. `stack_alchemy`
5. `stack_ingots`
6. `stack_textiles`
7. `stack_animal`
8. `stack_wood_products`
9. `stack_ore`
10. `stack_basic` (default)

---

## Stack size categories

### stack_basic — Basic Materials (default 50)
Items that don't match any other category. Raw gathering resources.

| Item file | In-game name | Notes |
|---|---|---|
| DA_DID_Resource_Wood_T01 | Softwood | T01 = tier 1 |
| DA_DID_Resource_Clay_T01 | Clay | |
| DA_DID_Resource_Stone_T01 | Stone | |
| DA_DID_Resource_SticksWood_T01 | Sticks | |
| DA_DID_Resource_Coal_T01 | Coal / Charcoal | From burnt trees |
| DA_DID_Resource_Soil_T02 | Soil | |
| DA_DID_Resource_FiberPlant_T01 | Plant Fiber | |

### stack_wood_products — Wood Products (default 200)
Processed and specialty woods.

| Item file | In-game name | Notes |
|---|---|---|
| DA_DID_Resource_Hardwood_T02 | Hardwood | T02 = tier 2 |
| DA_DID_Resource_Mahogany_T04 | Mahogany | T04 = tier 4, rare |
| DA_DID_Resource_VarnishedMahogany_T04 | Varnished Mahogany | |
| DA_DID_Resource_PlanksWood_T01 | Wood Planks | Crafted |
| DA_DID_Resource_WoodenBeam_T02 | Wooden Beam | Crafted |
| DA_DID_Resource_Bark_T02 | Tree Bark | |
| DA_DID_Resource_Resin_T03 | Resin | |
| DA_DID_Resource_TarredPlanks_T03 | Tarred Planks | |
| DA_DID_Resource_EnchantedWood_T03 | Enchanted Wood | |
| DA_DID_Resource_GhostWood_T04 | Ghost Wood | |
| DA_DID_Resource_HolyWood_T04 | Holy Wood | |

### stack_ore — Raw Ores & Minerals (default 500)
Unprocessed minerals harvested from nodes.

| Item file | In-game name | Notes |
|---|---|---|
| DA_DID_Resource_CopperOre_T01 | Copper Ore | Coastal Jungle caves |
| DA_DID_Resource_Iron_T02 | Iron Ore | Foothills biome |
| DA_DID_Resource_Iron_T03 | Volcanic Iron Ore | Volcanic biome |
| DA_DID_Resource_Sulfur_T01 | Sulfur | Foothills & Volcanic rocks |
| DA_DID_Resource_Stone_T01 | Stone | Surface rocks, all biomes |
| DA_DID_Resource_Coal_T01 | Coal | Ashlands burnt trees |
| DA_DID_Resource_Obsidian_T03 | Obsidian | |

### stack_ingots — Ingots & Refined Metals (default 200)
Smelted/processed metals.

| Item file | In-game name | Notes |
|---|---|---|
| DA_DID_Metal_CopperIngot_T01 | Copper Ingot | Smelted from Copper Ore |
| DA_DID_Metal_Ingot_Iron_T02 | Iron Ingot | Smelted from Iron Ore |
| DA_DID_Metal_Ingot_Ancient_T03 | Mire Metal Ingot | From Ancient Scraps |
| DA_DID_Resource_GoldIngot_T03 | Gold Ingot | |
| DA_DID_Resource_GoldNugget_T03 | Gold Nugget | |
| DA_DID_Resource_SilverIngot_T02 | Silver Ingot | |
| DA_DID_Resource_TumbagoIngot_T03 | Tumbago Ingot | |
| DA_DID_Resource_EnchantedIngot_T03 | Enchanted Ingot | |
| DA_DID_Resource_GhostIngot_T04 | Ghost Ingot | |
| DA_DID_Resource_HolyIngot_T04 | Holy Ingot | |

### stack_textiles — Textiles & Fabrics (default 200)

| Item file | In-game name | Notes |
|---|---|---|
| DA_DID_Resource_Fabric_T01 | Coarse Fabric | |
| DA_DID_Resource_LinenFabric_T02 | Linen Fabric | |
| DA_DID_Resource_TarredFabric_T03 | Tarred Fabric | |
| DA_DID_Resource_Broadcloth_T04 | Broadcloth | |
| DA_DID_Resource_FlaxFiber_T02 | Flax Fiber | |
| DA_DID_Resource_Leather_T01 | Rough Leather | |
| DA_DID_Resource_TanLeather_T02 | Tanned Leather | |
| DA_DID_Resource_CrocodileLeather_T03 | Crocodile Leather | |
| DA_DID_Resource_ElasticLeather_T04 | Elastic Leather | |
| DA_DID_Resource_EnchantedFabric_T03 | Enchanted Fabric | |
| DA_DID_Resource_Rope_T01 | Rope | |
| DA_DID_Resource_Rigging_T04 | Rigging | |

### stack_animal — Animal Materials (default 200)

| Item file | In-game name | Notes |
|---|---|---|
| DA_DID_Resource_Bones_T03 | Bones | |
| DA_DID_Resource_Feather_T01 | Feather | |
| DA_DID_Resource_Fat_T01 | Animal Fat | |
| DA_DID_Resource_Meat_T01 | Meat | |
| DA_DID_Resource_MeatBird_T01 | Bird Meat | |
| DA_DID_Resource_MeatCrab_T01 | Crab Meat | |
| DA_DID_Resource_FishMeat_T02 | Fish Meat | |
| DA_DID_Resource_BoneMeal_T04 | Bone Meal | |
| DA_DID_Resource_WolfFang_T02 | Wolf Fang | |
| DA_DID_Resource_GoatHorn_T02 | Goat Horn | |
| DA_DID_Resource_CrocodileTail_T03 | Crocodile Tail | |
| DA_DID_Resource_CrabShell_T01 | Crab Shell | |
| DA_DID_Resource_DodoEgg_01 | Dodo Egg | |

### stack_food — Food & Crops (default 100)
Raw ingredients, seeds, and prepared food items.

| Item file | In-game name | Notes |
|---|---|---|
| DA_CID_Food_* | Cooked dishes | Many varieties |
| DA_DID_Resource_*Seeds* | Seeds | Farming |
| DA_DID_Resource_Bean_T03 | Black Beans | |
| DA_DID_Resource_Potato_T01 | Potato | |
| DA_DID_Resource_Onion_T03 | Onion | |
| DA_DID_Resource_Peanut_T02 | Peanut | |
| DA_DID_Resource_CaneSugar_T03 | Sugar Cane | |
| DA_DID_Resource_Coffee_T03 | Coffee | |

### stack_alchemy — Alchemical Materials (default 100)
Ingredients for potions, elixirs, and crafting.

| Item file | In-game name | Notes |
|---|---|---|
| DA_DID_Resource_AlchemicalBase_T01 | Alchemical Base | |
| DA_DID_Resource_HealingHerbs_T01 | Healing Herbs | |
| DA_DID_Resource_Tannin_T02 | Tannin | |
| DA_DID_Resource_Saltpeter_T02 | Saltpeter | Gunpowder ingredient |
| DA_DID_Resource_Bezoar_T02 | Bezoar | |
| DA_DID_Resource_Ash_T01 | Ash | |
| DA_DID_Resource_Aloe_T02 | Aloe | |
| DA_DID_Resource_Bromeliaceae_T02 | Bromeliad | |
| DA_DID_Resource_MistyOrchid_T01 | Misty Orchid | |
| DA_DID_Resource_TritonsTrumpet_T01 | Triton's Trumpet | |
| DA_DID_Resource_Lobstershroom_T01 | Lobstershroom | |
| DA_DID_Resource_Firefly_T03 | Firefly | |
| DA_DID_Resource_UndeadEssence_T01 | Undead Essence | |
| DA_DID_Resource_UmbraEssence_T03 | Umbra Essence | |
| DA_DID_Resource_QuagmirePowder_T03 | Quagmire Powder | |

### stack_ammo — Ammunition (default 1000)
All projectiles and propellant.

| Item file | In-game name | Notes |
|---|---|---|
| DA_AID_Ammo_Cannonball_RegularCannonball_T01 | Iron Cannonball | |
| DA_AID_Ammo_Cannonball_RegularCannonball_T02 | Steel Cannonball | |
| DA_AID_Ammo_Cannonball_RegularCannonball_T03 | Advanced Cannonball | |
| DA_AID_Ammo_FirearmProjectile_StoneBullet_T01 | Stone Bullet | |
| DA_AID_Ammo_FirearmProjectile_RoughMetal_T02 | Rough Metal Bullet | |
| DA_AID_Ammo_FirearmProjectile_FineMetal_T02 | Fine Metal Bullet | |
| DA_AID_Ammo_FirearmProjectile_AncientMetal_T03 | Ancient Metal Bullet | |
| DA_AID_Ammo_Gunpowder_Homemade_T02 | Homemade Gunpowder | |
| DA_AID_Ammo_ScallopPearl_T01 | Scallop Pearl | |

### stack_consumables — Consumables & Potions (default 50)
Single-use items with active effects.

| Item file | In-game name | Notes |
|---|---|---|
| DA_CID_Alchemy_Potion_Healing_T01 | Healing Potion | |
| DA_CID_Alchemy_Potion_EnhancedHealing_T01 | Enhanced Healing | |
| DA_CID_Alchemy_Potion_GreatHealing_T01 | Greater Healing | |
| DA_CID_Alchemy_Bandages_T01 | Bandages | |
| DA_CID_Alchemy_Elixir_* | Elixirs (various) | Damage, Resist, etc. |
| DA_CID_Alchemy_Potion_Recall_T01 | Recall Potion | |

---

## Item tier system

Items follow a tier naming convention:

| Tier | Tag | Quality | Typical biome |
|---|---|---|---|
| T01 | tier 1 | Basic | Starter / Coastal |
| T02 | tier 2 | Improved | Foothills / Jungle |
| T03 | tier 3 | Advanced | Volcanic / Swamp |
| T04 | tier 4 | Rare/Enchanted | Late game |

---

## Loot table categories

These correspond to the loot multiplier sliders in the Game Tuning tab. The reference mods used are MoreMineralResources (2×) and MoreTreeResources (2×).

| Category key | Loot table pattern | Vanilla drop range (approx.) |
|---|---|---|
| loot_iron | Mineral_Iron_*, VolcaniIron_* | 8–10 iron per node |
| loot_sulfur | Mineral_Sulfur | 4–6 sulfur per node |
| loot_stone | HollowStone_*, MiddleRock, Mineral_Tuf_* | 4–8 stone per rock |
| loot_ancient_debris | AncientStatue_*, BrokenStatue_*, AncientMedalion_*, RuinsDebris | 2–8 ancient scraps |
| loot_hardwood | Swamp_*Taxodium_*, MahoganyStump, DiviLog* | 2–4 hardwood per tree |
| loot_plague_wood | Ashlands_BurntTree_*, Stump_Corrupted_* | 1–2 coal per node |
| loot_herbs | DefaultFiber, Fiber_* | 1–2 fiber per patch |
| loot_softwood | DefaultWood, DefaultStick, Jungle_Log_*, Stump_01/02 | 1–2 wood per tree |

**Not currently moddable via this mechanism:**
- Copper node loot (not in MoreMineralResources scope)
- Animal drops (no reference mod extracted)

---

## Resource spawner categories

Spawner JSON files control where and how resource nodes respawn. Only the Swamp biome ancient debris spawners have extractable JSONs from existing mods.

| Category key | Spawner pattern | Note |
|---|---|---|
| spawn_ancient_debris | SW_BrokenStatue_*, SW_RootedMetall_* | 24 spawner files |

Other spawner types (copper, iron, sulfur, stone, trees, herbs) appear to use a different spawning mechanism not exposed through the same JSON assets.
