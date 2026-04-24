import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ServerConfig:
    invite_code: str = ""
    server_name: str = ""
    is_password_protected: bool = False
    password: str = ""
    max_player_count: int = 4
    user_selected_region: str = ""
    use_direct_connection: bool = False
    direct_connection_port: int = 7777
    p2p_proxy_address: str = ""
    # read-only — don't let the UI overwrite these
    persistent_server_id: str = ""
    world_island_id: str = ""
    version: int = 1
    deployment_id: str = ""


@dataclass
class WorldConfig:
    island_id: str = ""
    world_name: str = "The Archipelago"
    world_preset_type: str = "Medium"   # Easy | Medium | Hard | Custom
    # Flat copies of the nested parameters for easy UI binding
    shared_quests: bool = True
    easy_explore: bool = False
    mob_health: float = 1.0
    mob_damage: float = 1.0
    ship_health: float = 1.0
    ship_damage: float = 1.0
    boarding_difficulty: float = 1.0
    coop_stats_correction: float = 1.0
    coop_ship_stats_correction: float = 0.0
    combat_difficulty: str = "Normal"   # Easy | Normal | Hard
    source_path: Path | None = None


class ConfigManager:
    def __init__(self, server_description_path: Path):
        self.server_path = server_description_path

    # ------------------------------------------------------------------
    # Server config
    # ------------------------------------------------------------------

    def load_server(self) -> ServerConfig:
        if not self.server_path.exists():
            return ServerConfig()
        raw = json.loads(self.server_path.read_text(encoding="utf-8"))
        d = raw.get("ServerDescription_Persistent", {})
        return ServerConfig(
            invite_code=d.get("InviteCode", ""),
            server_name=d.get("ServerName", ""),
            is_password_protected=d.get("IsPasswordProtected", False),
            password=d.get("Password", ""),
            max_player_count=d.get("MaxPlayerCount", 4),
            user_selected_region=d.get("UserSelectedRegion", ""),
            use_direct_connection=d.get("UseDirectConnection", False),
            direct_connection_port=d.get("DirectConnectionServerPort", 7777),
            p2p_proxy_address=d.get("P2pProxyAddress", ""),
            persistent_server_id=d.get("PersistentServerId", ""),
            world_island_id=d.get("WorldIslandId", ""),
            version=raw.get("Version", 1),
            deployment_id=raw.get("DeploymentId", ""),
        )

    def save_server(self, cfg: ServerConfig) -> None:
        raw = {}
        if self.server_path.exists():
            raw = json.loads(self.server_path.read_text(encoding="utf-8"))
        raw["Version"] = cfg.version
        if cfg.deployment_id:
            raw["DeploymentId"] = cfg.deployment_id
        d = raw.setdefault("ServerDescription_Persistent", {})
        d["InviteCode"] = cfg.invite_code
        d["ServerName"] = cfg.server_name
        d["IsPasswordProtected"] = cfg.is_password_protected
        d["Password"] = cfg.password
        d["MaxPlayerCount"] = cfg.max_player_count
        d["UserSelectedRegion"] = cfg.user_selected_region
        d["UseDirectConnection"] = cfg.use_direct_connection
        d["DirectConnectionServerPort"] = cfg.direct_connection_port
        d["P2pProxyAddress"] = cfg.p2p_proxy_address
        # preserve read-only fields
        if cfg.persistent_server_id:
            d["PersistentServerId"] = cfg.persistent_server_id
        if cfg.world_island_id:
            d["WorldIslandId"] = cfg.world_island_id
        self.server_path.write_text(json.dumps(raw, indent="\t"), encoding="utf-8")

    # ------------------------------------------------------------------
    # World config
    # ------------------------------------------------------------------

    def load_world(self, path: Path) -> WorldConfig:
        raw = json.loads(path.read_text(encoding="utf-8"))
        d = raw.get("WorldDescription", {})
        bp = d.get("WorldSettings", {}).get("BoolParameters", {})
        fp = d.get("WorldSettings", {}).get("FloatParameters", {})
        tp = d.get("WorldSettings", {}).get("TagParameters", {})

        def b(tag: str, default: bool) -> bool:
            return bp.get(f'{{"TagName": "{tag}"}}', default)

        def f(tag: str, default: float) -> float:
            return fp.get(f'{{"TagName": "{tag}"}}', default)

        def t(tag: str, default: str) -> str:
            val = tp.get(f'{{"TagName": "{tag}"}}', {})
            name = val.get("TagName", "")
            return name.split(".")[-1] if name else default

        return WorldConfig(
            island_id=d.get("islandId", ""),
            world_name=d.get("WorldName", "The Archipelago"),
            world_preset_type=d.get("WorldPresetType", "Medium"),
            shared_quests=b("WDS.Parameter.Coop.SharedQuests", True),
            easy_explore=b("WDS.Parameter.EasyExplore", False),
            mob_health=f("WDS.Parameter.MobHealthMultiplier", 1.0),
            mob_damage=f("WDS.Parameter.MobDamageMultiplier", 1.0),
            ship_health=f("WDS.Parameter.ShipsHealthMultiplier", 1.0),
            ship_damage=f("WDS.Parameter.ShipsDamageMultiplier", 1.0),
            boarding_difficulty=f("WDS.Parameter.BoardingDifficultyMultiplier", 1.0),
            coop_stats_correction=f("WDS.Parameter.Coop.StatsCorrectionModifier", 1.0),
            coop_ship_stats_correction=f("WDS.Parameter.Coop.ShipStatsCorrectionModifier", 0.0),
            combat_difficulty=t("WDS.Parameter.CombatDifficulty", "Normal"),
            source_path=path,
        )

    def save_world(self, cfg: WorldConfig) -> None:
        if not cfg.source_path or not cfg.source_path.exists():
            return
        raw = json.loads(cfg.source_path.read_text(encoding="utf-8"))
        d = raw.setdefault("WorldDescription", {})
        d["WorldName"] = cfg.world_name
        d["WorldPresetType"] = cfg.world_preset_type

        def tag(name: str) -> str:
            return f'{{"TagName": "{name}"}}'

        ws = d.setdefault("WorldSettings", {})
        ws["BoolParameters"] = {
            tag("WDS.Parameter.Coop.SharedQuests"): cfg.shared_quests,
            tag("WDS.Parameter.EasyExplore"): cfg.easy_explore,
        }
        ws["FloatParameters"] = {
            tag("WDS.Parameter.MobHealthMultiplier"): cfg.mob_health,
            tag("WDS.Parameter.MobDamageMultiplier"): cfg.mob_damage,
            tag("WDS.Parameter.ShipsHealthMultiplier"): cfg.ship_health,
            tag("WDS.Parameter.ShipsDamageMultiplier"): cfg.ship_damage,
            tag("WDS.Parameter.BoardingDifficultyMultiplier"): cfg.boarding_difficulty,
            tag("WDS.Parameter.Coop.StatsCorrectionModifier"): cfg.coop_stats_correction,
            tag("WDS.Parameter.Coop.ShipStatsCorrectionModifier"): cfg.coop_ship_stats_correction,
        }
        ws["TagParameters"] = {
            tag("WDS.Parameter.CombatDifficulty"): {
                "TagName": f"WDS.Parameter.CombatDifficulty.{cfg.combat_difficulty}"
            }
        }
        cfg.source_path.write_text(json.dumps(raw, indent="\t"), encoding="utf-8")
