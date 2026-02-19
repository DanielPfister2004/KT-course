"""
Scannt lab_suite/labs/ und erkennt NiceGUI-Apps vs. Skript-Ordner.
Gruppierung nach Kapitel (Präfix aus Ordnernamen, z. B. 01_, 03_).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


# Unterordner, deren .py-Dateien nicht als eigenständige Skripte gelten
SCRIPT_EXCLUDE_DIRS = frozenset({"_core", "assignments", "templates"})


@dataclass
class LabEntry:
    """Ein Eintrag im Launcher: entweder eine App oder ein Skript."""
    kind: str  # "app" | "script"
    chapter: str  # z. B. "01", "03"
    folder_name: str  # Ordnername, z. B. 01_01_Signale_basics
    label: str  # Anzeigename
    # Für App: Modulname (labs.01_05_chapter1); für Skript: relativer Pfad (labs/01_01_Signale_basics/matplotlib-demo.py)
    run_target: str
    has_submissions_folder: bool


@dataclass
class ChapterGroup:
    """Kapitel mit zugehörigen Labs/Skripten."""
    chapter: str
    title: str  # z. B. "Kapitel 01"
    entries: list[LabEntry]


def _chapter_from_folder(folder_name: str) -> str:
    """Kapitel-Präfix aus Ordnernamen (z. B. 01_01_Signale_basics -> 01)."""
    if "_" in folder_name:
        return folder_name.split("_")[0]
    return folder_name[:2] if len(folder_name) >= 2 else folder_name


def _top_level_scripts(lab_dir: Path) -> list[str]:
    """Nur .py-Dateien direkt im Ordner (nicht in _core, assignments, …)."""
    scripts = []
    for f in lab_dir.iterdir():
        if not f.is_file() or f.suffix != ".py":
            continue
        if f.name.startswith("__"):
            continue
        scripts.append(f.name)
    return sorted(scripts)


def scan_labs(labs_root: Path) -> list[ChapterGroup]:
    """
    Scannt labs_root (lab_suite/labs) und liefert gruppierte Einträge.

    Regel pro Aufgabenordner (z. B. 01_01_Signale_basics): Es liegt entweder
    - eine NiceGUI-App (__main__.py vorhanden) ODER
    - ein bzw. mehrere einfache Python-Skripte (oberste Ebene, keine __main__.py).
    Nie beides – der Scan erkennt zuerst __main__.py (dann App), sonst Skripte.
    """
    if not labs_root.is_dir():
        return []

    groups: dict[str, list[LabEntry]] = {}
    for item in sorted(labs_root.iterdir()):
        if not item.is_dir() or item.name.startswith("."):
            continue
        # Python-Modulname: Ordnername (Unterstriche erlaubt)
        folder_name = item.name
        chapter = _chapter_from_folder(folder_name)
        submissions_dir = item / "submissions"
        has_submissions = submissions_dir.is_dir()

        if (item / "__main__.py").exists():
            # NiceGUI-App
            mod = f"labs.{folder_name}"
            entry = LabEntry(
                kind="app",
                chapter=chapter,
                folder_name=folder_name,
                label=folder_name,
                run_target=mod,
                has_submissions_folder=has_submissions,
            )
            groups.setdefault(chapter, []).append(entry)
        else:
            scripts = _top_level_scripts(item)
            if not scripts:
                continue
            for script_name in scripts:
                rel_path = f"labs/{folder_name}/{script_name}"
                entry = LabEntry(
                    kind="script",
                    chapter=chapter,
                    folder_name=folder_name,
                    label=f"{folder_name} / {script_name}",
                    run_target=rel_path,
                    has_submissions_folder=has_submissions,
                )
                groups.setdefault(chapter, []).append(entry)

    result = []
    for ch in sorted(groups.keys()):
        result.append(ChapterGroup(
            chapter=ch,
            title=f"Kapitel {ch}",
            entries=groups[ch],
        ))
    return result
