"""
Assignment-Registry: Wahlweise eine Fachaufgabe (Assignment) in die App einhängen.

Assignments liegen im Ordner assignments/ (user_template.py, assignment_01.py, …).
Aktives Assignment: GUI-Auswahl (speichert in assignments/active.json) oder Fallback ASSIGNMENT.
Aus user_callbacks.py oder Timer: get_assignment() → Modul mit run_domain_logic() / solve_task().
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import ModuleType

# Fallback, wenn keine GUI-Auswahl und keine active.json
ASSIGNMENT: str = "user_template"

# App-Root = development_app/ (Parent von _core)
APP_ROOT = Path(__file__).resolve().parent.parent
_ASSIGNMENTS_DIR = APP_ROOT / "assignments"
_ACTIVE_FILE = _ASSIGNMENTS_DIR / "active.json"

# Modulnamen, die keine Assignments sind (nur Callbacks/Infrastruktur)
_NON_ASSIGNMENT_MODULES = frozenset({"user_callbacks", "__init__"})


def _parent_package() -> str:
    """Paket der App (development_app), nicht _core, für Import .assignments.<name>."""
    pkg = __package__ or ""
    if "._core" in pkg:
        return pkg.rsplit("._core", 1)[0]
    return pkg


def _get_active_name(override: str | None) -> str | None:
    """Aktives Assignment: override (z. B. aus State) > active.json > ASSIGNMENT."""
    if override and override.strip():
        return override.strip()
    if _ACTIVE_FILE.exists():
        try:
            data = json.loads(_ACTIVE_FILE.read_text(encoding="utf-8"))
            name = (data.get("assignment") or "").strip()
            if name:
                return name
        except Exception:
            pass
    return ASSIGNMENT.strip() or None


def get_assignment(active_override: str | None = None) -> ModuleType | None:
    """Lädt das aktive Assignment-Modul aus assignments/ (user_template, assignment_01, …)."""
    name = _get_active_name(active_override)
    if not name:
        return None
    parent = _parent_package()
    if not parent:
        return None
    try:
        return importlib.import_module(f".assignments.{name}", package=parent)
    except Exception:
        return None


def list_assignments() -> list[str]:
    """Listet Assignment-Modulnamen aus assignments/*.py (ohne __init__, user_callbacks)."""
    names = []
    if not _ASSIGNMENTS_DIR.exists():
        return names
    for p in _ASSIGNMENTS_DIR.glob("*.py"):
        stem = p.stem
        if stem not in _NON_ASSIGNMENT_MODULES:
            names.append(stem)
    return sorted(names)


def get_active_assignment_name(override: str | None = None) -> str:
    """Name des aktiven Assignments (für GUI-Anzeige/Dropdown)."""
    return _get_active_name(override) or ASSIGNMENT or "user_template"


def set_active_assignment(name: str) -> None:
    """Setzt das aktive Assignment (persistent in assignments/active.json)."""
    _ASSIGNMENTS_DIR.mkdir(parents=True, exist_ok=True)
    _ACTIVE_FILE.write_text(json.dumps({"assignment": name.strip()}, indent=2), encoding="utf-8")
