import shutil
from dataclasses import dataclass, field
from pathlib import Path

PAK_EXTS = {".pak", ".ucas", ".utoc"}
DISABLED = ".disabled"


@dataclass
class ModPackage:
    """A mod available in the library (not yet installed)."""
    name: str
    source_dir: Path
    pak_files: list[Path] = field(default_factory=list)

    def __post_init__(self):
        if not self.pak_files:
            self.pak_files = sorted(
                f for f in self.source_dir.rglob("*")
                if f.suffix in PAK_EXTS and f.is_file()
            )

    @property
    def file_summary(self) -> str:
        exts = sorted({f.suffix for f in self.pak_files})
        return f"{len(self.pak_files)} file(s): {', '.join(exts)}"


@dataclass
class InstalledMod:
    """A mod currently in the ~mods folder."""
    name: str           # stem of the .pak file (no extension, no .disabled)
    files: list[Path]
    enabled: bool

    @property
    def file_count(self) -> int:
        return len(self.files)


class ModManager:
    def __init__(self, mods_dir: Path, library_path: Path):
        self.mods_dir = mods_dir
        self.library_path = library_path

    # ------------------------------------------------------------------
    # Library
    # ------------------------------------------------------------------

    def list_available(self) -> list[ModPackage]:
        if not self.library_path.exists():
            return []
        packages = []
        for entry in sorted(self.library_path.iterdir()):
            if not entry.is_dir():
                continue
            pak_files = [
                f for f in entry.rglob("*")
                if f.suffix in PAK_EXTS and f.is_file()
            ]
            if pak_files:
                packages.append(ModPackage(entry.name, entry, pak_files))
        return packages

    # ------------------------------------------------------------------
    # Installed mods
    # ------------------------------------------------------------------

    def list_installed(self) -> list[InstalledMod]:
        if not self.mods_dir.exists():
            return []

        groups: dict[str, list[Path]] = {}
        for f in self.mods_dir.iterdir():
            if not f.is_file():
                continue
            base = f.name[: -len(DISABLED)] if f.name.endswith(DISABLED) else f.name
            if Path(base).suffix not in PAK_EXTS:
                continue
            stem = Path(base).stem
            groups.setdefault(stem, []).append(f)

        result = []
        for stem, files in sorted(groups.items()):
            enabled = not any(f.name.endswith(DISABLED) for f in files)
            result.append(InstalledMod(stem, sorted(files), enabled))
        return result

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def list_generated(self) -> list[Path]:
        """Return loose .pak files in the library root (generated tuning paks)."""
        if not self.library_path.exists():
            return []
        return sorted(p for p in self.library_path.iterdir() if p.suffix == ".pak" and p.is_file())

    def installed_stems(self) -> set[str]:
        """Return the stems of every pak currently in ~mods (for conflict detection)."""
        return {m.name for m in self.list_installed()}

    def deploy(self, pak_file: Path, target_mods_dir: Path | None = None) -> Path:
        """Copy a single .pak file into ~mods (or a given mods dir). Returns dest path."""
        dest_dir = target_mods_dir if target_mods_dir is not None else self.mods_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dst = dest_dir / pak_file.name
        shutil.copy2(pak_file, dst)
        return dst

    def install(self, package: ModPackage) -> list[Path]:
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        installed = []
        for src in package.pak_files:
            dst = self.mods_dir / src.name
            shutil.copy2(src, dst)
            installed.append(dst)
        return installed

    def uninstall(self, mod: InstalledMod) -> None:
        for f in mod.files:
            if f.exists():
                f.unlink()

    def enable(self, mod: InstalledMod) -> None:
        new_files = []
        for f in mod.files:
            if f.name.endswith(DISABLED):
                target = f.parent / f.name[: -len(DISABLED)]
                f.rename(target)
                new_files.append(target)
            else:
                new_files.append(f)
        mod.files = new_files
        mod.enabled = True

    def disable(self, mod: InstalledMod) -> None:
        new_files = []
        for f in mod.files:
            if not f.name.endswith(DISABLED):
                target = f.parent / (f.name + DISABLED)
                f.rename(target)
                new_files.append(target)
            else:
                new_files.append(f)
        mod.files = new_files
        mod.enabled = False
