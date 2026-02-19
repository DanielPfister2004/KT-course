"""
NiceGUI-Oberfläche des App-Launchers: hierarchische Liste, Start-Buttons, E-Mail-Fallback Submit.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from nicegui import ui

from .widgets import Banner
from .scan import ChapterGroup, LabEntry, scan_labs
from . import submit

# lab_suite = Parent von app_launcher
LAB_SUITE_ROOT = Path(__file__).resolve().parent.parent
LABS_DIR = LAB_SUITE_ROOT / "labs"


def _launch_app(entry: LabEntry) -> None:
    """Startet NiceGUI-App als Subprocess (python -m labs.xxx)."""
    cmd = [sys.executable, "-m", entry.run_target]
    try:
        subprocess.Popen(
            cmd,
            cwd=str(LAB_SUITE_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        ui.notify(f"App wird gestartet: {entry.run_target}", type="positive")
    except Exception as e:
        ui.notify(f"Starten fehlgeschlagen: {e}", type="negative")


def _launch_script(entry: LabEntry) -> None:
    """Startet Skript als Subprocess (python labs/.../file.py)."""
    cmd = [sys.executable, entry.run_target]
    try:
        subprocess.Popen(
            cmd,
            cwd=str(LAB_SUITE_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        ui.notify(f"Skript wird gestartet: {entry.run_target}", type="positive")
    except Exception as e:
        ui.notify(f"Starten fehlgeschlagen: {e}", type="negative")


def _launch(entry: LabEntry) -> None:
    if entry.kind == "app":
        _launch_app(entry)
    else:
        _launch_script(entry)


def _on_zip_create(folder_name: str) -> None:
    """ZIP aus submissions/ erstellen und ggf. Ordner öffnen."""
    ok, msg = submit.create_submissions_zip(LAB_SUITE_ROOT, folder_name)
    if ok:
        ui.notify(f"ZIP erstellt: {msg}", type="positive")
        submit.open_submissions_folder(LAB_SUITE_ROOT, folder_name)
    else:
        ui.notify(f"ZIP fehlgeschlagen: {msg}", type="negative")


def _on_open_folder(folder_name: str) -> None:
    """Dateimanager im submissions-Ordner öffnen."""
    ok, msg = submit.open_submissions_folder(LAB_SUITE_ROOT, folder_name)
    if ok:
        ui.notify("Ordner geöffnet.", type="positive")
    else:
        ui.notify(f"Ordner öffnen fehlgeschlagen: {msg}", type="negative")


def _make_drop_handler(folder_name: str):
    """Erstellt einen on_upload-Handler, der Dateien in labs/<folder_name>/submissions/ speichert."""

    async def handler(e):
        dest_dir = LABS_DIR / folder_name / "submissions"
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            ui.notify(f"Ordner nicht erstellbar: {err}", type="negative")
            return
        name = Path(e.file.name).name.strip() or "uploaded_file"
        if ".." in name or name.startswith("/"):
            ui.notify("Ungültiger Dateiname.", type="negative")
            return
        path = dest_dir / name
        try:
            await e.file.save(str(path))
            ui.notify(f"Gespeichert: {name} → submissions/", type="positive")
        except Exception as err:
            ui.notify(f"Speichern fehlgeschlagen: {err}", type="negative")

    return handler


def _read_task_md(folder_name: str) -> str:
    """Liest labs/<folder_name>/submissions/task.md; leere Zeichenkette falls nicht vorhanden."""
    path = LABS_DIR / folder_name / "submissions" / "task.md"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _task_markdown_extras() -> list[str]:
    """Extras für ui.markdown (LaTeX nur wenn latex2mathml verfügbar)."""
    extras = ["fenced-code-blocks", "tables"]
    try:
        import latex2mathml.converter  # noqa: F401
        extras.append("latex")
    except ImportError:
        pass
    return extras


def _group_entries_by_folder(entries: list[LabEntry]) -> list[tuple[str, list[LabEntry]]]:
    """Gruppiert Einträge nach folder_name, Reihenfolge wie in entries (erstes Vorkommen)."""
    order: list[str] = []
    groups: dict[str, list[LabEntry]] = {}
    for e in entries:
        if e.folder_name not in groups:
            order.append(e.folder_name)
            groups[e.folder_name] = []
        groups[e.folder_name].append(e)
    return [(fn, groups[fn]) for fn in order]


def build_ui() -> None:
    """Baut die Launcher-UI: Kapitel-Gruppen, Einträge mit Start-Button, Submit-Zeile pro Lab."""
    chapters = scan_labs(LABS_DIR)
    if not chapters:
        ui.label("Keine Labs gefunden. Bitte lab_suite/labs/ prüfen.").classes("text-weight-medium")
        return

    submit_email = submit.read_submit_to_email(LAB_SUITE_ROOT)

    ui.label("Verfügbare Labs und Skripte").classes("text-h5 q-mb-md")
    ui.label("Klicke auf „Starten“, um eine App (Browser) oder ein Skript (Konsole/Matplotlib) zu starten.").classes(
        "text-body2 text-grey-7 q-mb-lg"
    )

    for group in chapters:
        with ui.expansion(group.title, value=True).classes("w-full launcher-chapter-expansion"):
            with ui.column().classes("w-full bg-grey-2 rounded-borders q-pa-md"):
                for folder_name, folder_entries in _group_entries_by_folder(group.entries):
                    # Leicht schattierter Container pro Aufgabenblock (Einträge + Aufgabe)
                    with ui.card().classes("w-full q-mb-md bg-white rounded-borders").style("box-shadow: 0 1px 3px rgba(0,0,0,0.08)"):
                        for entry in folder_entries:
                            with ui.row().classes("items-center q-gutter-sm full-width q-mb-xs"):
                                if entry.kind == "app":
                                    ui.icon("web", size="sm").classes("text-primary")
                                else:
                                    ui.icon("code", size="sm").classes("text-secondary")
                                ui.label(entry.label).classes("flex-grow")
                                if entry.has_submissions_folder:
                                    ui.badge("submissions/", color="green").classes("text-caption")
                                ui.button("Starten", on_click=lambda e=entry: _launch(e)).props("flat dense color=primary")
                        # Drop-Zone für submissions/ (nur wenn Lab submissions-Ordner hat; grünes Badge signalisiert das)
                        if any(e.has_submissions_folder for e in folder_entries):
                            ui.upload(
                                on_upload=_make_drop_handler(folder_name),
                                label="Dateien hier ablegen → submissions/",
                                auto_upload=True,
                                multiple=True,
                            ).classes("w-full q-mt-xs").props("flat bordered")
                        # Aufgabe nach dem letzten Eintrag des Blocks
                        task_content = _read_task_md(folder_name)
                        if task_content.strip():
                            with ui.expansion("Aufgabe anzeigen", value=False).classes("w-full q-ml-sm q-mt-xs q-mb-sm"):
                                extras = _task_markdown_extras()
                                ui.markdown(task_content, extras=extras).classes("q-pa-sm bg-white rounded-borders")

                # Pro Lab (eindeutige folder_name) eine Submit-Zeile: ZIP, Ordner öffnen, E-Mail – unter Expansion (default zu)
                unique_folders = sorted({e.folder_name for e in group.entries})
                if unique_folders:
                    with ui.expansion("E-mail Fallback Abgaben", value=False).classes("w-full q-mt-sm"):
                        ui.label("Abgabe (E-Mail-Fallback)").classes("text-caption text-grey-7 q-mb-xs")
                        for folder_name in unique_folders:
                            with ui.row().classes("items-center q-gutter-sm full-width q-mb-xs"):
                                ui.label(folder_name).classes("text-body2 flex-grow")
                                ui.button("ZIP erstellen", on_click=lambda fn=folder_name: _on_zip_create(fn)).props(
                                    "flat dense color=secondary"
                                )
                                ui.button("Ordner öffnen", on_click=lambda fn=folder_name: _on_open_folder(fn)).props(
                                    "flat dense color=secondary"
                                )
                                mailto_url = submit.build_mailto_url(submit_email, folder_name)
                                if mailto_url:
                                    ui.link("E-Mail öffnen", mailto_url).props("flat dense color=secondary").classes(
                                        "text-secondary"
                                    )
                                else:
                                    ui.label("(submit_to_email in submit_manifest.txt fehlt)").classes("text-caption text-grey")

    ui.separator().classes("q-my-lg")
    with ui.card().classes("w-full bg-blue-1"):
        ui.label("Abgaben (Submissions)").classes("text-subtitle1 text-weight-medium")
        ui.label(
            "Pro Lab: Ordner submissions/. ZIP erstellen → Ordner öffnen → ZIP in die geöffnete E-Mail ziehen und senden. "
            "Zieladresse: lab_suite/submit_manifest.txt (submit_to_email=…)."
        ).classes("text-body2")
        ui.label("Pfad: lab_suite/labs/<Lab-Name>/submissions/").classes("text-caption text-grey-7")


def run(port: int = 8082, title: str = "KT-Lab Launcher") -> None:
    """Startet die NiceGUI-App (Launcher)."""

    @ui.page("/")
    def index():
        # Größere Schrift für Kapitel-Expansion-Überschriften; Schatten-Hintergrund wird per Klasse gesetzt
        ui.add_head_html(
            """
            <style>
            /* Nur die äußere Kapitel-Expansion: Header-Label groß */
            .launcher-chapter-expansion .q-expansion-item__container > .q-item .q-item__label { font-size: 1.35rem; font-weight: 600; }
            .launcher-chapter-expansion .q-expansion-item__container > .q-item { min-height: 48px; }
            /* Innere Expansionen (Aufgabe anzeigen, E-mail Fallback): blau, geringere Signifikanz */
            .launcher-chapter-expansion .q-expansion-item__content .q-expansion-item .q-item__label { font-size: 1rem; font-weight: normal; color: #1565c0; }
            </style>
            """
        )
        with ui.column().classes("q-pa-lg w-full"):
            Banner(
                text1=title,
                text2="Labs starten · Aufgaben einsehen",
                text3="Abgaben senden",
                height="80px",
            ).classes("w-full")
            build_ui()

    ui.run(port=port, title=title, reload=False)
