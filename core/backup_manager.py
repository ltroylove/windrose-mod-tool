import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core import activity_log

_DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class BackupEntry:
    ts: str
    path: Path
    tag: str
    file_count: int


class BackupManager:
    def __init__(self, backup_dir: Path | None = None):
        self.backup_dir = backup_dir or (_DATA_DIR / "backups")

    def backup_mods(self, mods_dir: Path, tag: str) -> BackupEntry:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        ts_raw = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self.backup_dir / f"mods_{ts_raw}.zip"
        file_count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("_backup_meta.txt", f"tag={tag}\nts={ts_raw}\n")
            if mods_dir.exists():
                for f in mods_dir.iterdir():
                    if f.is_file():
                        zf.write(f, f.name)
                        file_count += 1
        ts_str = _parse_ts(ts_raw)
        activity_log.log_action("backup_created", tag)
        return BackupEntry(ts=ts_str, path=zip_path, tag=tag, file_count=file_count)

    def list_backups(self) -> list[BackupEntry]:
        if not self.backup_dir.exists():
            return []
        entries = []
        for zp in self.backup_dir.glob("mods_*.zip"):
            try:
                parts = zp.stem.split("_")  # ["mods", "YYYYMMDD", "HHMMSS"]
                ts_raw = f"{parts[1]}_{parts[2]}" if len(parts) >= 3 else ""
                tag = ""
                file_count = 0
                with zipfile.ZipFile(zp) as z:
                    names = z.namelist()
                    if "_backup_meta.txt" in names:
                        meta = z.read("_backup_meta.txt").decode()
                        for line in meta.splitlines():
                            if line.startswith("tag="):
                                tag = line[4:]
                    file_count = sum(1 for n in names if n != "_backup_meta.txt")
                entries.append(BackupEntry(
                    ts=_parse_ts(ts_raw), path=zp, tag=tag, file_count=file_count,
                ))
            except Exception:
                continue
        return sorted(entries, key=lambda e: e.ts, reverse=True)

    def restore(self, entry: BackupEntry, mods_dir: Path) -> None:
        if mods_dir.exists():
            shutil.rmtree(mods_dir)
        mods_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(entry.path) as zf:
            for name in zf.namelist():
                if name != "_backup_meta.txt":
                    zf.extract(name, mods_dir)
        activity_log.log_action("restore_performed", entry.tag)

    def prune(self, keep: int = 10) -> None:
        for old in self.list_backups()[keep:]:
            try:
                old.path.unlink()
            except Exception:
                pass


def _parse_ts(ts_raw: str) -> str:
    """Convert 'YYYYMMDD_HHMMSS' to ISO format 'YYYY-MM-DDTHH:MM:SS'."""
    try:
        d, t = ts_raw.split("_")
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}T{t[:2]}:{t[2:4]}:{t[4:6]}"
    except Exception:
        return ts_raw
