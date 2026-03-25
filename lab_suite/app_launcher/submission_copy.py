"""
Submission-Copy: Kopiert Dateien aus dem Task-Ordner (oder assignments/) nach submissions/,
falls dort noch nicht vorhanden. EDIT/STARTEN arbeiten dann mit der Kopie (keine Merge-Konflikte).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

# lab_suite = Parent von app_launcher
_MODULE_DIR = Path(__file__).resolve().parent
LABS_DIR = _MODULE_DIR.parent / "labs"
COPY_MANIFEST_NAME = "copy_manifest.json"


def ensure_submission_copy(
    folder_name: str,
    filename: str,
    source_subdir: str | None = None,
) -> Path | None:
    """
    Stellt sicher, dass eine Kopie der Datei in submissions/ existiert.
    Wenn submissions/<filename> fehlt, wird von <task_folder>/<source_subdir>/<filename>
    bzw. <task_folder>/<filename> kopiert.

    Args:
        folder_name: Lab-Ordner (z. B. 01_02_Informationstheorie).
        filename: Dateiname (z. B. entropy1.py, user_template.py).
        source_subdir: Optionaler Unterordner im Task (z. B. "assignments").
            Wenn None, liegt die Quelle direkt im Task-Ordner.

    Returns:
        Pfad zur Datei in submissions/ (absolut), oder None wenn die Quelldatei nicht existiert.
    """
    task_dir = LABS_DIR / folder_name
    submissions_dir = task_dir / "submissions"
    dest = submissions_dir / filename

    if source_subdir:
        source = task_dir / source_subdir / filename
    else:
        source = task_dir / filename

    if not source.is_file():
        return None

    submissions_dir.mkdir(parents=True, exist_ok=True)

    if not dest.exists():
        shutil.copy2(source, dest)

    return dest.resolve()


def _is_safe_relative_path(path_str: str) -> bool:
    """
    Erlaubt nur relative, lokale Pfade ohne Traversal.
    """
    p = Path(path_str)
    if p.is_absolute():
        return False
    return ".." not in p.parts


def _load_copy_manifest(task_dir: Path) -> dict | None:
    """
    Lädt optionales copy_manifest.json aus dem Task-Ordner.
    Rückgabe None bei fehlender/ungültiger Datei.
    """
    manifest_path = task_dir / COPY_MANIFEST_NAME
    if not manifest_path.is_file():
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    if int(data.get("version", 0)) != 1:
        return None
    if data.get("mode", "extend-defaults") != "extend-defaults":
        return None
    rules = data.get("rules")
    if not isinstance(rules, list):
        return None
    return data


def _copytree_if_missing(src: Path, dst: Path) -> bool:
    """
    Kopiert Ordner rekursiv, aber nur wenn Ziel noch nicht existiert.
    Return True falls Ziel nachher existiert.
    """
    if dst.exists():
        return True
    if not src.is_dir():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    return True


def _copyfile_if_missing(src: Path, dst: Path) -> bool:
    """
    Kopiert Datei, aber nur wenn Ziel noch nicht existiert.
    Return True falls Ziel nachher existiert.
    """
    if dst.exists():
        return True
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def ensure_manifest_submission_extras(folder_name: str) -> list[Path]:
    """
    Optional: zusätzliche Kopierregeln aus labs/<folder>/copy_manifest.json anwenden.
    Rückwärtskompatibel: ohne gültiges Manifest passiert nichts.

    Aktuelles Verhalten:
    - mode muss "extend-defaults" sein
    - Regeltypen: "file" und "dir"
    - if_exists muss "copy" sein
    - Es wird nur kopiert, wenn das Ziel in submissions/ noch nicht existiert.
    """
    task_dir = LABS_DIR / folder_name
    submissions_dir = task_dir / "submissions"
    manifest = _load_copy_manifest(task_dir)
    if manifest is None:
        return []

    result: list[Path] = []
    submissions_dir.mkdir(parents=True, exist_ok=True)

    for rule in manifest.get("rules", []):
        if not isinstance(rule, dict):
            continue
        if rule.get("if_exists", "copy") != "copy":
            continue

        rtype = str(rule.get("type", "")).strip()
        src_rel = str(rule.get("source", "")).strip()
        dst_rel = str(rule.get("target", "")).strip()
        if not src_rel or not dst_rel:
            continue
        if not _is_safe_relative_path(src_rel) or not _is_safe_relative_path(dst_rel):
            continue

        src = task_dir / src_rel
        dst = submissions_dir / dst_rel
        copied_or_exists = False
        if rtype == "dir":
            copied_or_exists = _copytree_if_missing(src, dst)
        elif rtype == "file":
            copied_or_exists = _copyfile_if_missing(src, dst)
        else:
            continue

        if copied_or_exists and dst.exists():
            result.append(dst.resolve())

    return result


def _top_level_script_names(task_dir: Path) -> list[str]:
    """.py- und .ipynb-Dateien direkt im Task-Ordner (wie in scan.py)."""
    names = []
    for f in task_dir.iterdir():
        if not f.is_file():
            continue
        if f.suffix not in (".py", ".ipynb"):
            continue
        if f.name.startswith("__"):
            continue
        names.append(f.name)
    return sorted(names)


def ensure_all_task_script_copies(folder_name: str) -> list[Path]:
    """
    Kopiert alle .py- und .ipynb-Dateien der obersten Ebene aus dem Task-Ordner
    nach submissions/, falls sie dort noch fehlen (z. B. bei Labs mit mehreren Skripten/Notebooks).

    Returns:
        Liste der Pfade in submissions/, die (neu oder bereits vorhanden) existieren.
    """
    task_dir = LABS_DIR / folder_name
    if not task_dir.is_dir():
        return []
    result = []
    for name in _top_level_script_names(task_dir):
        path = ensure_submission_copy(folder_name, name)
        if path is not None:
            result.append(path)
    # Optionale Zusatzdateien/-ordner aus copy_manifest.json (rückwärtskompatibel)
    result.extend(ensure_manifest_submission_extras(folder_name))
    return result


def ensure_app_submission_files(folder_name: str) -> list[Path]:
    """
    Kopiert assignments/user_template.py und user_callbacks.py nach submissions/,
    falls sie im Task-Ordner existieren und in submissions/ noch fehlen.

    Returns:
        Liste der Pfade in submissions/ (die nun existieren).
    """
    result = []
    for name in ("user_template.py", "user_callbacks.py"):
        path = ensure_submission_copy(folder_name, name, source_subdir="assignments")
        if path is not None:
            result.append(path)
    # Optionale Zusatzdateien/-ordner aus copy_manifest.json (rückwärtskompatibel)
    result.extend(ensure_manifest_submission_extras(folder_name))
    return result
