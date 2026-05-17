import json
import sys
from pathlib import Path

try:
    import keyring as _keyring
    _KEYRING_AVAILABLE = True
    _KEYRING_UNAVAILABLE_REASON = ""
except Exception as _kr_exc:
    _KEYRING_AVAILABLE = False
    _KEYRING_UNAVAILABLE_REASON = f"{type(_kr_exc).__name__}: {_kr_exc}"
    print(
        f"[BlackFlag] WARNING: keyring unavailable ({_KEYRING_UNAVAILABLE_REASON}). "
        "FTP passwords will not be saved between runs — install the 'keyring' "
        "package or fix your credential store. See requirements.txt.",
        file=sys.stderr,
    )


def keyring_available() -> bool:
    """Public accessor so the UI can surface a one-time warning when the
    credential store isn't usable on this machine."""
    return _KEYRING_AVAILABLE


def keyring_unavailable_reason() -> str:
    """Empty string when keyring is available."""
    return _KEYRING_UNAVAILABLE_REASON

# When frozen by PyInstaller, __file__ lives inside a temp _MEI* folder that
# is deleted on exit.  User data (settings) must live next to the .exe instead.
if getattr(sys, "frozen", False):
    _DATA_DIR    = Path(sys.executable).parent / "data"
    _PROJECT_ROOT = Path(sys.executable).parent
else:
    _DATA_DIR    = Path(__file__).parent.parent / "data"
    _PROJECT_ROOT = Path(__file__).parent.parent

_SETTINGS_PATH  = _DATA_DIR / "settings.json"
_KEYRING_SERVICE = "BlackFlagModManager"
_KEYRING_ACCOUNT = "ftp_password"

DEFAULTS: dict = {
    "game_path": "",
    "library_path": str(_PROJECT_ROOT / "Mods"),
    "ftp_host": "",
    "ftp_port": "21",
    "ftp_user": "",
    "ftp_server_json_path": "R5/ServerDescription.json",
    "ftp_mods_path": "R5/Content/Paks/~mods",
}


def load() -> dict:
    if _SETTINGS_PATH.exists():
        try:
            stored = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
            # Strip any legacy plain-text password that may have been persisted before
            stored.pop("ftp_password", None)
            return {**DEFAULTS, **stored}
        except Exception:
            pass
    return dict(DEFAULTS)


def save(data: dict) -> None:
    _DATA_DIR.mkdir(exist_ok=True)
    safe = {k: v for k, v in data.items() if k != "ftp_password"}
    _SETTINGS_PATH.write_text(json.dumps(safe, indent=2), encoding="utf-8")


def get_ftp_password() -> str:
    if _KEYRING_AVAILABLE:
        try:
            return _keyring.get_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT) or ""
        except Exception:
            pass
    return ""


def set_ftp_password(password: str) -> None:
    if _KEYRING_AVAILABLE:
        try:
            _keyring.set_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT, password)
        except Exception:
            pass
