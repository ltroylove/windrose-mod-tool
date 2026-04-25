import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"
_LOG_PATH = _DATA_DIR / "activity.json"


def log_action(action: str, detail: str) -> None:
    _DATA_DIR.mkdir(exist_ok=True)
    entries: list = []
    if _LOG_PATH.exists():
        try:
            entries = json.loads(_LOG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            corrupt = _LOG_PATH.with_name(f"activity.corrupt.{ts}.json")
            _LOG_PATH.rename(corrupt)
            entries = [{"ts": _now(), "action": "log_recovered", "detail": str(corrupt.name)}]
    entries.append({"ts": _now(), "action": action, "detail": detail})
    _atomic_write(_LOG_PATH, json.dumps(entries, indent=2))


def load_recent(n: int = 50) -> list[dict]:
    if not _LOG_PATH.exists():
        return []
    try:
        entries = json.loads(_LOG_PATH.read_text(encoding="utf-8"))
        return list(reversed(entries[-n:]))
    except (json.JSONDecodeError, OSError):
        return []


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
