import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"
_SETTINGS_PATH = _DATA_DIR / "settings.json"

_PROJECT_ROOT = Path(__file__).parent.parent

DEFAULTS: dict = {
    "game_path": "",
    "library_path": str(_PROJECT_ROOT / "Mods"),
    "ftp_host": "",
    "ftp_port": "21",
    "ftp_user": "",
    "ftp_password": "",
    "ftp_server_json_path": "R5/ServerDescription.json",
    "ftp_mods_path": "R5/Content/Paks/~mods",
}


def load() -> dict:
    if _SETTINGS_PATH.exists():
        try:
            stored = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
            return {**DEFAULTS, **stored}
        except Exception:
            pass
    return dict(DEFAULTS)


def save(data: dict) -> None:
    _DATA_DIR.mkdir(exist_ok=True)
    _SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
