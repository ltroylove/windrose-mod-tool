import json
from datetime import datetime
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"
_LOG_PATH = _DATA_DIR / "activity.json"


def log_action(action: str, detail: str) -> None:
    _DATA_DIR.mkdir(exist_ok=True)
    entries: list = []
    if _LOG_PATH.exists():
        try:
            entries = json.loads(_LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries.append({
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "action": action,
        "detail": detail,
    })
    _LOG_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def load_recent(n: int = 50) -> list[dict]:
    if not _LOG_PATH.exists():
        return []
    try:
        entries = json.loads(_LOG_PATH.read_text(encoding="utf-8"))
        return list(reversed(entries[-n:]))
    except Exception:
        return []
