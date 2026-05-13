"""Pfad-Helfer: LAB-Ordner zu sys.path hinzufuegen (fuer Notebook-Kernels)."""

from __future__ import annotations

import sys
from pathlib import Path


def lab_root_from_here() -> Path:
    """Ordner .../09_01_LABOR-8-solution (Parent von ``lib``)."""
    return Path(__file__).resolve().parent.parent


def prepend_lab_root(root: Path | None = None) -> Path:
    """Fügt den LAB-Root zu sys.path hinzu (idempotent)."""
    root = root or lab_root_from_here()
    s = str(root.resolve())
    if s not in sys.path:
        sys.path.insert(0, s)
    return root.resolve()


def prepend_cwd_if_has_lib(cwd: Path | None = None) -> Path | None:
    """Wenn ``cwd/lib`` existiert, cwd nach vorne auf sys.path."""
    cwd = (cwd or Path.cwd()).resolve()
    if (cwd / "lib").is_dir():
        s = str(cwd)
        if s not in sys.path:
            sys.path.insert(0, s)
        return cwd
    return None
