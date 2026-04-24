from pathlib import Path
import winreg


def find_steam_path() -> Path | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            p = Path(path)
            if p.exists():
                return p
    except Exception:
        pass
    for candidate in [
        Path("C:/Program Files (x86)/Steam"),
        Path("C:/Program Files/Steam"),
        Path("D:/Steam"),
        Path("D:/Games/Steam"),
        Path("E:/Steam"),
    ]:
        if candidate.exists():
            return candidate
    return None


def find_game_path() -> Path | None:
    steam = find_steam_path()
    if steam:
        game = steam / "steamapps/common/Windrose"
        if game.exists():
            return game
    return None


class GamePaths:
    def __init__(self, game_root: Path):
        self.game_root = Path(game_root)

    @property
    def client_paks(self) -> Path:
        return self.game_root / "R5/Content/Paks"

    @property
    def client_mods(self) -> Path:
        return self.client_paks / "~mods"

    @property
    def server_root(self) -> Path:
        return self.game_root / "R5/Builds/WindowsServer"

    @property
    def server_paks(self) -> Path:
        return self.server_root / "R5/Content/Paks"

    @property
    def server_mods(self) -> Path:
        return self.server_paks / "~mods"

    @property
    def server_description(self) -> Path:
        return self.game_root / "R5/ServerDescription.json"

    def find_world_configs(self) -> list[Path]:
        saved = self.game_root / "R5/Saved/SaveProfiles/Default/RocksDB"
        if not saved.exists():
            return []
        return list(saved.rglob("WorldDescription.json"))

    def is_valid(self) -> bool:
        return self.game_root.exists() and (self.game_root / "R5").exists()
