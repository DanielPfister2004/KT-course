"""
E-Mail-Fallback: Manifest lesen, submissions-Ordner öffnen, ZIP erstellen.
"""
from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# Repo-weites Manifest: lab_suite/submit_manifest.txt, key=value
SUBMIT_MANIFEST_NAME = "submit_manifest.txt"


def _find_manifest(lab_suite_root: Path) -> Path:
    """Pfad zum Submit-Manifest (lab_suite/submit_manifest.txt)."""
    return lab_suite_root / SUBMIT_MANIFEST_NAME


def read_submit_to_email(lab_suite_root: Path) -> str:
    """
    Liest submit_to_email aus lab_suite/submit_manifest.txt.
    Format: Zeilen mit # sind Kommentare; submit_to_email=adresse@example.com
    Leer = keine Adresse konfiguriert.
    """
    path = _find_manifest(lab_suite_root)
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.split("#", 1)[0].strip()
        if not raw:
            continue
        if "=" in raw:
            key, value = raw.split("=", 1)
            if key.strip().lower() == "submit_to_email":
                return value.strip().strip('"\'')
    return ""


def open_submissions_folder(lab_suite_root: Path, folder_name: str) -> tuple[bool, str]:
    """
    Öffnet den Dateimanager im Ordner lab_suite/labs/<folder_name>/submissions/.
    Erstellt den Ordner, falls er nicht existiert.
    Rückgabe: (Erfolg, Meldung)
    """
    submissions_dir = lab_suite_root / "labs" / folder_name / "submissions"
    try:
        submissions_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, str(e)
    path_str = str(submissions_dir.resolve())
    try:
        if sys.platform == "win32":
            os.startfile(path_str)
        elif sys.platform == "darwin":
            subprocess.run(["open", path_str], check=False)
        else:
            subprocess.run(["xdg-open", path_str], check=False)
    except Exception as e:
        return False, str(e)
    return True, path_str


def create_submissions_zip(lab_suite_root: Path, folder_name: str) -> tuple[bool, str]:
    """
    Erstellt ein ZIP-Archiv mit dem Inhalt von labs/<folder_name>/submissions/
    und speichert es im gleichen Ordner als abgabe_<folder_name>_<datum>.zip.
    Vorhandene abgabe_*.zip werden nicht in das neue ZIP aufgenommen.
    Rückgabe: (Erfolg, Pfad oder Fehlermeldung)
    """
    submissions_dir = lab_suite_root / "labs" / folder_name / "submissions"
    submissions_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    safe_name = folder_name.replace(" ", "_")
    zip_name = f"abgabe_{safe_name}_{date_str}.zip"
    zip_path = submissions_dir / zip_name
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in submissions_dir.rglob("*"):
                if f.is_file() and f.suffix == ".zip" and f.name.startswith("abgabe_"):
                    continue
                rel = f.relative_to(submissions_dir)
                zf.write(f, rel)
        return True, str(zip_path)
    except Exception as e:
        return False, str(e)


def build_mailto_url(email: str, folder_name: str) -> str:
    """mailto-URL mit Betreff [kt-assignment] ID=<folder_name>."""
    if not email:
        return ""
    subject = f"[kt-assignment] ID={folder_name}"
    return f"mailto:{email}?subject={quote(subject)}"
