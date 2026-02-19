"""
Editor-Integration: Zeilensuche für # widget: path_id in user_callbacks.py.
Für Editor-Modus (Widget anklicken → Stelle im Code anzeigen).
"""
from __future__ import annotations

from pathlib import Path


def find_widget_marker_line(content: str, path_id: str) -> int | None:
    """
    Sucht die Zeilennummer (1-basiert) der Zeile mit „# widget: <path_id>“.
    Gibt None zurück, wenn nicht gefunden.
    """
    marker = f"# widget: {path_id}"
    for i, line in enumerate(content.splitlines(), start=1):
        if marker in line or line.strip() == marker:
            return i
    return None


def get_editor_context(file_path: Path | str, path_id: str) -> tuple[str, int]:
    """
    Liest die Datei und findet die Zeile für den gegebenen path_id.
    Returns (content, line_number). line_number ist 1-basiert; wenn nicht gefunden, 1.
    """
    path = Path(file_path)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    line = find_widget_marker_line(content, path_id)
    return content, (line if line is not None else 1)
