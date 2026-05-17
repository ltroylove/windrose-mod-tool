import shutil
from dataclasses import dataclass, field
from pathlib import Path

PAK_EXTS = {".pak", ".ucas", ".utoc"}
DISABLED = ".disabled"
GENERATED_MARKER = ".blackflag_generated"
MANIFEST_EXT = ".blackflag"


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
        return sum(1 for f in self.files if f.suffix in PAK_EXTS)


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
            if (entry / GENERATED_MARKER).exists():
                continue  # generated pak — shown in list_generated() instead
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

        result = []
        covered: set[str] = set()

        # Manifest-based mods (generated): one .blackflag file groups all category paks
        for manifest in sorted(self.mods_dir.glob(f"*{MANIFEST_EXT}")):
            mod_name = manifest.stem
            files: list[Path] = [manifest]
            covered.add(manifest.name)
            for filename in manifest.read_text(encoding="utf-8").splitlines():
                filename = filename.strip()
                if not filename:
                    continue
                for candidate in (self.mods_dir / filename,
                                  self.mods_dir / (filename + DISABLED)):
                    if candidate.exists():
                        files.append(candidate)
                        covered.add(candidate.name)
            pak_files = [f for f in files if f.suffix in (".pak",) or
                         f.name.endswith(".pak" + DISABLED)]
            # Stale manifest — every pak it referenced has been deleted. Skip it
            # rather than show a ghost mod with zero files as "enabled" (vacuous
            # truth would otherwise mark it enabled).
            if not pak_files:
                continue
            enabled = not any(f.name.endswith(DISABLED) for f in pak_files)
            result.append(InstalledMod(mod_name, sorted(files), enabled))

        # Individual mods (downloaded): group by pak stem as before
        groups: dict[str, list[Path]] = {}
        for f in self.mods_dir.iterdir():
            if f.name in covered or not f.is_file():
                continue
            base = f.name[: -len(DISABLED)] if f.name.endswith(DISABLED) else f.name
            if Path(base).suffix not in PAK_EXTS:
                continue
            stem = Path(base).stem
            groups.setdefault(stem, []).append(f)

        for stem, files in sorted(groups.items()):
            enabled = not any(f.name.endswith(DISABLED) for f in files)
            result.append(InstalledMod(stem, sorted(files), enabled))

        return sorted(result, key=lambda m: m.name)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def list_generated(self) -> list[Path]:
        """Return the primary .pak for each generated tuning mod.

        Generated dirs are identified by a GENERATED_MARKER file written at
        generation time.  Loose .pak files at the library root are also
        included for backward compat.  _Segments companions are excluded.
        """
        if not self.library_path.exists():
            return []
        result = []
        for entry in sorted(self.library_path.iterdir()):
            if entry.is_dir() and (entry / GENERATED_MARKER).exists():
                # The "primary" pak is whichever of Other / MineralOther / TreeOther
                # the user actually produced this run — they may have toggled the
                # Stack/Backpack/Building/Consumables sections off and only generated
                # loot paks. Fall back to the legacy {dir_name}.pak layout last.
                base = entry.name[:-2] if entry.name.endswith("_P") else entry.name
                for candidate_name in (f"{base}Other_P.pak",
                                       f"{base}MineralOther_P.pak",
                                       f"{base}TreeOther_P.pak",
                                       f"{entry.name}.pak"):
                    candidate = entry / candidate_name
                    if candidate.exists():
                        result.append(candidate)
                        break
            elif entry.is_file() and entry.suffix == ".pak" and "_Segments" not in entry.stem:
                result.append(entry)
        return result

    def installed_stems(self) -> set[str]:
        """Return the stems of every pak currently in ~mods (for conflict detection)."""
        return {m.name for m in self.list_installed()}

    def deploy(self, pak_file: Path, target_mods_dir: Path | None = None) -> Path:
        """Copy a .pak and companion files into ~mods. Returns dest path.

        For generated mods (directory contains GENERATED_MARKER) all .pak/.ucas/.utoc
        files in the directory are deployed together.  For downloaded mods only the
        selected pak and its direct I/O Store companions are copied.
        """
        dest_dir = target_mods_dir if target_mods_dir is not None else self.mods_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        if (pak_file.parent / GENERATED_MARKER).exists():
            # Generated mod — deploy every pak/ucas/utoc and write a manifest
            deployed: list[str] = []
            for f in sorted(pak_file.parent.iterdir()):
                if f.suffix in (".pak", ".ucas", ".utoc"):
                    shutil.copy2(f, dest_dir / f.name)
                    deployed.append(f.name)
            manifest = dest_dir / f"{pak_file.parent.name}{MANIFEST_EXT}"
            manifest.write_text("\n".join(deployed), encoding="utf-8")
        else:
            # Downloaded mod — deploy the selected pak + direct I/O Store companions
            shutil.copy2(pak_file, dest_dir / pak_file.name)
            for ext in (".ucas", ".utoc"):
                companion = pak_file.with_suffix(ext)
                if companion.exists():
                    shutil.copy2(companion, dest_dir / companion.name)

        return dest_dir / pak_file.name

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
            # A disabled pak is named "Foo.pak.disabled" — Path(...).suffix is
            # ".disabled", which is why we strip the suffix from the name first
            # and then check that what's underneath is a .pak.
            if f.name.endswith(DISABLED):
                base = f.name[: -len(DISABLED)]
                if Path(base).suffix == ".pak":
                    target = f.parent / base
                    f.rename(target)
                    new_files.append(target)
                    continue
            new_files.append(f)
        mod.files = new_files
        mod.enabled = True

    def disable(self, mod: InstalledMod) -> None:
        new_files = []
        for f in mod.files:
            if f.suffix == ".pak" and not f.name.endswith(DISABLED):
                target = f.parent / (f.name + DISABLED)
                f.rename(target)
                new_files.append(target)
            else:
                new_files.append(f)
        mod.files = new_files
        mod.enabled = False
