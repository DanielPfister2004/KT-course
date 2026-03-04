"""
Submission-Copy: Kopiert Dateien aus dem Task-Ordner (oder assignments/) nach submissions/,
falls dort noch nicht vorhanden. EDIT/STARTEN arbeiten dann mit der Kopie (keine Merge-Konflikte).
"""
from __future__ import annotations

import shutil
from pathlib import Path

# lab_suite = Parent von app_launcher
_MODULE_DIR = Path(__file__).resolve().parent
LABS_DIR = _MODULE_DIR.parent / "labs"


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
    return result
