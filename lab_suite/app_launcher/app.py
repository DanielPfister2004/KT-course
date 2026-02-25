"""
NiceGUI-Oberfläche des App-Launchers: hierarchische Liste, Start-Buttons, E-Mail-Fallback Submit.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from nicegui import ui

from .widgets import Banner
from .scan import ChapterGroup, LabEntry, scan_labs
from . import submit
from . import port_check
from . import git_ops

# lab_suite = Parent von app_launcher
LAB_SUITE_ROOT = Path(__file__).resolve().parent.parent
LABS_DIR = LAB_SUITE_ROOT / "labs"
INSTRUCTOR_KEY_PATH = LAB_SUITE_ROOT / ".instructor_key"


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


def _open_script_in_editor(entry: LabEntry) -> None:
    """Öffnet das zum Eintrag gehörige Python-Skript im Standard-Editor (z. B. VS Code)."""
    if entry.kind != "script":
        return
    script_path = LAB_SUITE_ROOT / entry.run_target
    if not script_path.is_file():
        ui.notify(f"Datei nicht gefunden: {script_path}", type="negative")
        return
    ok, msg = submit.open_file_with_default_app(script_path)
    if ok:
        ui.notify(f"Editor: {script_path.name}", type="positive")
    else:
        ui.notify(msg, type="negative")


# Konvention: NiceGUI-Apps mit Übungs-Code öffnen assignments/user_template.py im Editor
def _get_app_user_template_path(folder_name: str) -> Path | None:
    """Pfad zu labs/<folder_name>/assignments/user_template.py, falls vorhanden."""
    path = LABS_DIR / folder_name / "assignments" / "user_template.py"
    return path if path.is_file() else None


def _open_app_user_template(entry: LabEntry) -> None:
    """Öffnet assignments/user_template.py der App im Standard-Editor (für Studierende zum Ergänzen)."""
    if entry.kind != "app":
        return
    template_path = _get_app_user_template_path(entry.folder_name)
    if not template_path:
        ui.notify("assignments/user_template.py nicht gefunden.", type="warning")
        return
    ok, msg = submit.open_file_with_default_app(template_path)
    if ok:
        ui.notify(f"Editor: {template_path.name}", type="positive")
    else:
        ui.notify(msg, type="negative")


def _get_doc_md_path(folder_name: str) -> Path | None:
    """Pfad zu labs/<folder_name>/doc.md, falls vorhanden; sonst None."""
    path = LABS_DIR / folder_name / "doc.md"
    return path if path.is_file() else None


def _read_doc_md(folder_name: str) -> str:
    """Liest labs/<folder_name>/doc.md; leere Zeichenkette falls nicht vorhanden."""
    doc_path = _get_doc_md_path(folder_name)
    if not doc_path:
        return ""
    try:
        return doc_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _show_doc_dialog(folder_name: str) -> None:
    """Zeigt doc.md gerendert (Markdown + LaTeX) in einem Dialog im Browser – kein externer Editor."""
    content = _read_doc_md(folder_name)
    if not content.strip():
        ui.notify("doc.md nicht gefunden oder leer.", type="warning")
        return
    extras = _task_markdown_extras()
    with ui.dialog() as d, ui.card().classes("q-pa-md min-w-[320px] max-w-[90vw] max-h-[85vh] overflow-auto"):
        ui.label("Erklärung (doc.md)").classes("text-subtitle1 text-weight-medium")
        ui.label(folder_name).classes("text-caption text-grey-7 q-mb-sm")
        ui.markdown(content, extras=extras).classes("q-pa-sm bg-white rounded-borders text-body2")
        ui.button("Schließen", on_click=d.close).props("flat color=primary").classes("q-mt-sm")
    d.open()


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


def _list_submissions(folder_name: str) -> list[tuple[str, int]]:
    """Listet labs/<folder_name>/submissions/; liefert [(Dateiname, Größe in Bytes), ...], sortiert nach Name."""
    path = LABS_DIR / folder_name / "submissions"
    if not path.is_dir():
        return []
    result: list[tuple[str, int]] = []
    try:
        for f in sorted(path.iterdir()):
            if f.is_file():
                result.append((f.name, f.stat().st_size))
    except OSError:
        pass
    return result


def _show_submissions_dialog(folder_name: str) -> None:
    """Öffnet einen Dialog mit dem Inhalt des submission-Ordners (Dateiliste + Größe)."""
    items = _list_submissions(folder_name)
    with ui.dialog() as d, ui.card().classes("q-pa-md min-w-[280px]"):
        ui.label(f"Inhalt: submissions/").classes("text-subtitle2 text-weight-medium")
        ui.label(folder_name).classes("text-caption text-grey-7 q-mb-sm")
        if not items:
            ui.label("(Ordner leer oder nicht vorhanden)").classes("text-body2 text-grey")
        else:
            with ui.column().classes("w-full gap-0"):
                for name, size in items:
                    size_str = f"{size:,} B" if size < 1024 else f"{size / 1024:.1f} KB"
                    with ui.row().classes("items-center q-gutter-sm full-width"):
                        ui.icon("insert_drive_file", size="sm").classes("text-grey-7")
                        ui.label(name).classes("flex-grow text-body2")
                        ui.label(size_str).classes("text-caption text-grey-7")
        ui.button("Schließen", on_click=d.close).props("flat color=primary").classes("q-mt-sm")
    d.open()


def _is_instructor_mode() -> bool:
    """True, wenn die Instructor-Key-Datei existiert und nicht leer ist (Key nicht an Studierende exportieren)."""
    if not INSTRUCTOR_KEY_PATH.is_file():
        return False
    try:
        return bool(INSTRUCTOR_KEY_PATH.read_text(encoding="utf-8").strip())
    except Exception:
        return False


def _read_deadline_iso(folder_name: str) -> str | None:
    """Liest deadline.txt, gibt YYYY-MM-DD zurück oder None."""
    path = LABS_DIR / folder_name / "submissions" / "deadline.txt"
    if not path.is_file():
        return None
    try:
        line = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if len(line) >= 10 and line[4] == "-" and line[7] == "-":
            return line[:10]
    except Exception:
        pass
    return None


def _write_deadline(folder_name: str, date_iso: str) -> bool:
    """Schreibt YYYY-MM-DD in submissions/deadline.txt. Erstellt submissions/ bei Bedarf."""
    dest_dir = LABS_DIR / folder_name / "submissions"
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / "deadline.txt").write_text(date_iso.strip()[:10] + "\n", encoding="utf-8")
        return True
    except OSError:
        return False


def _deadline_reminder(folder_name: str) -> tuple[str, str] | None:
    """
    Berechnet aus deadline.txt den Hinweistext und die Farbe für die Task-Card.
    Rückgabe: (Text, Quasar-Farbklasse) oder None, wenn kein gültiges Abgabedatum.
    - Noch nicht fällig: "Abgabe in X Tagen" (grün wenn > 3 Tage, bernstein/amber wenn ≤ 3 Tage).
    - Heute fällig: "Abgabe heute" (bernstein/amber).
    - Überfällig: "Abgabe seit X Tagen" (rot).
    """
    from datetime import date

    iso = _read_deadline_iso(folder_name)
    if not iso or len(iso) < 10:
        return None
    try:
        deadline = date.fromisoformat(iso[:10])
    except ValueError:
        return None
    today = date.today()
    days = (deadline - today).days
    if days > 3:
        return (f"Abgabe in {days} Tagen", "text-green")
    if days > 0:
        return (f"Abgabe in {days} Tagen", "text-amber-8")
    if days == 0:
        return ("Abgabe heute", "text-amber-8")
    return (f"Abgabe seit {-days} Tagen", "text-red")


def _read_task_done(folder_name: str) -> str | None:
    """
    Liest labs/<folder_name>/submissions/task_done.txt (eine Zeile: „Abgabe am DD.MM.YYYY“).
    Gibt das Datum „DD.MM.YYYY“ zurück oder None. State ist session-übergreifend und per Git für den Dozenten sichtbar.
    """
    path = LABS_DIR / folder_name / "submissions" / "task_done.txt"
    if not path.is_file():
        return None
    try:
        line = path.read_text(encoding="utf-8").strip().splitlines()
        if not line:
            return None
        text = line[0].strip()
        if text.startswith("Abgabe am "):
            return text.replace("Abgabe am ", "").strip()
    except Exception:
        pass
    return None


def _write_task_done(folder_name: str) -> bool:
    """Schreibt „Abgabe am DD.MM.YYYY“ in submissions/task_done.txt. Erstellt submissions/ bei Bedarf."""
    from datetime import date

    dest_dir = LABS_DIR / folder_name / "submissions"
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        today = date.today().strftime("%d.%m.%Y")
        (dest_dir / "task_done.txt").write_text(f"Abgabe am {today}\n", encoding="utf-8")
        return True
    except OSError:
        return False


def _clear_task_done(folder_name: str) -> bool:
    """Entfernt submissions/task_done.txt."""
    path = LABS_DIR / folder_name / "submissions" / "task_done.txt"
    try:
        if path.is_file():
            path.unlink()
        return True
    except OSError:
        return False


def _read_deadline(folder_name: str) -> str | None:
    """
    Liest labs/<folder_name>/submissions/deadline.txt (eine Zeile: YYYY-MM-DD).
    Gibt das Datum als Anzeigestring (DD.MM.YYYY) zurück oder None, wenn keine Datei/ungültig.
    """
    path = LABS_DIR / folder_name / "submissions" / "deadline.txt"
    if not path.is_file():
        return None
    try:
        line = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if not line:
            return None
        # ISO YYYY-MM-DD → DD.MM.YYYY
        parts = line.split("-")
        if len(parts) == 3 and len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2:
            y, m, d = parts[0], parts[1], parts[2]
            if y.isdigit() and m.isdigit() and d.isdigit():
                return f"{d}.{m}.{y}"
    except Exception:
        pass
    return None


def _show_deadline_picker_dialog(folder_name: str) -> None:
    """Öffnet Dialog mit Kalender zur Auswahl des Abgabedatums (nur im Instructor-Modus)."""
    from datetime import date as date_type

    initial = _read_deadline_iso(folder_name) or date_type.today().isoformat()
    with ui.dialog() as d, ui.card().classes("q-pa-md min-w-[300px]"):
        ui.label("Abgabedatum setzen").classes("text-subtitle2 text-weight-medium")
        ui.label(folder_name).classes("text-caption text-grey-7 q-mb-sm")
        picker = ui.date(value=initial, mask="YYYY-MM-DD").classes("w-full")
        with ui.row().classes("q-mt-md q-gutter-sm"):
            ui.button("Abbrechen", on_click=d.close).props("flat")
            ui.button("Löschen", on_click=lambda: _apply_deadline_and_close(folder_name, None, d)).props("flat color=negative")
            ui.button("Übernehmen", on_click=lambda: _apply_deadline_and_close(folder_name, picker, d)).props("flat color=primary")
    d.open()


def _apply_deadline_and_close(folder_name: str, picker, d) -> None:
    """Schreibt gewähltes Datum in deadline.txt (oder löscht Datei), schließt Dialog, lädt Seite neu."""
    if picker is not None:
        val = getattr(picker, "value", None)
        date_str = (str(val)[:10] if val else "").strip()
        if not date_str or len(date_str) < 10:
            ui.notify("Bitte ein gültiges Datum wählen.", type="warning")
            return
        if not _write_deadline(folder_name, date_str):
            ui.notify("Speichern fehlgeschlagen.", type="negative")
            return
        ui.notify(f"Abgabe bis: {date_str} gespeichert.", type="positive")
    else:
        path = LABS_DIR / folder_name / "submissions" / "deadline.txt"
        try:
            if path.is_file():
                path.unlink()
            ui.notify("Abgabedatum entfernt.", type="positive")
        except OSError:
            ui.notify("Löschen fehlgeschlagen.", type="negative")
    d.close()
    ui.run_javascript("window.location.reload()")


def _read_task_md(folder_name: str) -> str:
    """Liest labs/<folder_name>/submissions/task.md; leere Zeichenkette falls nicht vorhanden."""
    path = LABS_DIR / folder_name / "submissions" / "task.md"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# Unterstützte Fragebogen-Formate: Erweiterung und Priorität (erste gefundene gewinnt)
QUESTIONS_EXTENSIONS = (".md", ".docx", ".txt")


def _get_questions_path(folder_name: str) -> Path | None:
    """
    Sucht in labs/<folder_name>/submissions/ nach questions.<ext> (Reihenfolge: .md, .docx, .txt).
    Gibt den Pfad zur ersten gefundenen Datei zurück oder None.
    """
    submissions_dir = LABS_DIR / folder_name / "submissions"
    if not submissions_dir.is_dir():
        return None
    for ext in QUESTIONS_EXTENSIONS:
        path = submissions_dir / f"questions{ext}"
        if path.is_file():
            return path
    return None


def _has_questions_file(folder_name: str) -> bool:
    """True, wenn in submissions/ eine questions.*-Datei (md, docx, txt) existiert."""
    return _get_questions_path(folder_name) is not None


def _open_questionnaire(folder_name: str) -> None:
    """
    Öffnet den Fragebogen: Sucht questions.<ext> (md, docx, txt). Fehlt answers.<ext>,
    wird questions.<ext> dorthin kopiert; danach wird answers.<ext> im Standard-Editor geöffnet.
    """
    submissions_dir = LABS_DIR / folder_name / "submissions"
    questions_path = _get_questions_path(folder_name)
    if not questions_path or not questions_path.is_file():
        ui.notify("Keine questions.md / questions.docx / questions.txt gefunden.", type="warning")
        return
    ext = questions_path.suffix
    answers_path = submissions_dir / f"answers{ext}"
    try:
        submissions_dir.mkdir(parents=True, exist_ok=True)
        if not answers_path.is_file():
            shutil.copy2(questions_path, answers_path)
            ui.notify(f"answers{ext} aus questions{ext} erstellt und geöffnet.", type="positive")
        else:
            ui.notify(f"answers{ext} geöffnet.", type="positive")
        ok, msg = submit.open_file_with_default_app(answers_path)
        if not ok:
            ui.notify(msg, type="negative")
    except OSError as e:
        ui.notify(f"Fehler: {e}", type="negative")


# Standard-Dateiname für Konsolenausgabe (Skript schreibt parallel dorthin)
CONSOLE_LOG_NAME = "console_log.txt"


def _get_console_log_path(folder_name: str) -> Path | None:
    """Pfad zu submissions/console_log.txt, falls vorhanden."""
    path = LABS_DIR / folder_name / "submissions" / CONSOLE_LOG_NAME
    return path if path.is_file() else None


def _has_console_log(folder_name: str) -> bool:
    """True, wenn submissions/console_log.txt existiert."""
    return _get_console_log_path(folder_name) is not None


def _get_answers_path(folder_name: str) -> Path | None:
    """Erste existierende answers-Datei (answers.md, answers.txt, answers.docx) in submissions/."""
    submissions_dir = LABS_DIR / folder_name / "submissions"
    if not submissions_dir.is_dir():
        return None
    for ext in QUESTIONS_EXTENSIONS:
        p = submissions_dir / f"answers{ext}"
        if p.is_file():
            return p
    return None


def _merge_console_log_into_answers(folder_name: str) -> None:
    """
    Hängt den Inhalt von submissions/console_log.txt an answers.md bzw. answers.txt an
    (unter einer Überschrift „Konsolenausgabe“). answers.docx wird nicht unterstützt.
    """
    console_path = _get_console_log_path(folder_name)
    answers_path = _get_answers_path(folder_name)
    if not console_path:
        ui.notify("console_log.txt nicht gefunden. Skript zuerst ausführen.", type="warning")
        return
    if not answers_path:
        ui.notify("Bitte zuerst Fragebogen öffnen (answers.md/an answers.txt anlegen).", type="warning")
        return
    if answers_path.suffix == ".docx":
        ui.notify("Einfügen in answers.docx wird nicht unterstützt. Bitte answers.md oder answers.txt nutzen.", type="warning")
        return
    try:
        log_content = console_path.read_text(encoding="utf-8")
    except OSError as e:
        ui.notify(f"Fehler beim Lesen: {e}", type="negative")
        return
    try:
        existing = answers_path.read_text(encoding="utf-8")
    except OSError as e:
        ui.notify(f"Fehler beim Lesen der Antwortdatei: {e}", type="negative")
        return
    separator = "\n\n---\n\n## Konsolenausgabe\n\n"
    if answers_path.suffix == ".md":
        new_part = "```\n" + log_content.strip() + "\n```"
    else:
        new_part = log_content.strip()
    new_content = existing.rstrip() + separator + new_part + "\n"
    try:
        answers_path.write_text(new_content, encoding="utf-8")
        ui.notify("Konsolenausgabe in answers eingefügt.", type="positive")
    except OSError as e:
        ui.notify(f"Fehler beim Schreiben: {e}", type="negative")


def _task_markdown_extras() -> list[str]:
    """Extras für ui.markdown (LaTeX nur wenn latex2mathml verfügbar)."""
    extras = ["fenced-code-blocks", "tables"]
    try:
        import latex2mathml.converter  # noqa: F401
        extras.append("latex")
    except ImportError:
        pass
    return extras


EXPANSION_STATE_PATH = LAB_SUITE_ROOT / "launcher_expansion_state.json"


def _read_expansion_state() -> dict[str, bool]:
    """Liest den gespeicherten Open/Closed-State der Hauptkapitel-Expansions (session-übergreifend)."""
    if not EXPANSION_STATE_PATH.is_file():
        return {}
    try:
        import json

        data = json.loads(EXPANSION_STATE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {k: bool(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _write_expansion_state(state: dict[str, bool]) -> None:
    """Speichert den Open/Closed-State der Hauptkapitel-Expansions."""
    try:
        import json

        EXPANSION_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def _on_expansion_change(title: str, is_open: bool) -> None:
    """Aktualisiert den gespeicherten State für ein Kapitel und schreibt die Datei."""
    state = _read_expansion_state()
    state[title] = is_open
    _write_expansion_state(state)


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


# Nur 8081 prüfen – 8082 ist der Launcher selbst; Freigabe von 8082 würde den Launcher beenden
LAB_APP_PORT = 8081
PORT_CHECK_INTERVAL = 1.0  # Sekunden


def _fill_port_status_content(container: ui.column) -> None:
    """Füllt den übergebenen Container mit dem aktuellen Port-8081-Status (für Timer-Aktualisierung)."""
    container.clear()
    with container:
        pids = port_check.get_pids_on_port(LAB_APP_PORT)
        if not pids:
            with ui.row().classes("items-center q-gutter-sm"):
                ui.icon("check_circle", size="sm").classes("text-green-7")
                ui.label("Port 8081: frei").classes("text-body2 text-weight-medium text-green-8")
            ui.label("Labs können auf Port 8081 starten. Bei „Socket bereits verwendet“ diese Expansion öffnen.").classes(
                "text-caption text-grey-7 q-mt-xs"
            )
        else:
            pid = pids[0]
            name = port_check.get_process_name(pid) or "?"
            with ui.row().classes("items-center q-gutter-sm"):
                ui.icon("warning", size="sm").classes("text-amber-8")
                ui.label("Port 8081: belegt").classes("text-body2 text-weight-medium text-amber-9")
            ui.label(
                "Belegt kann bedeuten: (1) Ein Lab läuft regulär – dann nichts tun. "
                "(2) Port ist verwaist (z. B. nach Absturz oder Doppelstart) – dann unten „Port freigeben“ nutzen, "
                "damit ein neues Lab starten kann."
            ).classes("text-caption text-grey-8 q-my-xs")
            with ui.row().classes("items-center q-gutter-sm full-width q-mt-sm"):
                ui.label(f"Belegt von: {name} (PID {pid})").classes("text-caption text-grey-7 flex-grow")
                ui.button("Port freigeben", on_click=lambda pid_to_kill=pid: _on_free_port(LAB_APP_PORT, pid_to_kill)).props(
                    "flat dense color=amber-8"
                )


def _build_port_status_card() -> None:
    """Zeigt in einer (standardmäßig geschlossenen) Expansion den Status von Port 8081; Inhalt wird im Sekundentakt aktualisiert."""
    with ui.expansion("Port 8081 prüfen (nur bei Startproblemen öffnen)", value=False).classes("w-full q-mb-md"):
        port_content = ui.column().classes("w-full")
        _fill_port_status_content(port_content)
        ui.timer(PORT_CHECK_INTERVAL, lambda: _fill_port_status_content(port_content), once=False)


def _on_free_port(port: int, pid: int) -> None:
    """Beendet den Prozess auf dem Port und lädt die Seite neu."""
    if port_check.kill_process(pid):
        ui.notify(f"Port {port} freigegeben (Prozess {pid} beendet).", type="positive")
        ui.run_javascript("window.location.reload()")
    else:
        ui.notify("Port konnte nicht freigegeben werden (evtl. fehlen Rechte).", type="negative")


def _show_git_output_in_container(container: ui.column, cmd_str: str, stdout: str, stderr: str) -> None:
    """Füllt den Container mit Befehl und Ausgabe (scrollbar)."""
    container.clear()
    with container:
        ui.label("Ausgeführter Befehl:").classes("text-caption text-weight-bold")
        ui.html(
            f'<pre class="q-pa-sm bg-grey-3 rounded-borders" style="white-space:pre-wrap;max-height:120px;overflow:auto;font-size:0.85em;">{_escape_html(cmd_str)}</pre>'
        )
        ui.label("Ausgabe:").classes("text-caption text-weight-bold q-mt-sm")
        combined = (stdout + "\n" + stderr).strip() or "(leer)"
        ui.html(
            f'<pre class="q-pa-sm bg-grey-3 rounded-borders" style="white-space:pre-wrap;max-height:280px;overflow:auto;font-size:0.85em;">{_escape_html(combined)}</pre>'
        )


def _escape_html(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _build_git_expansion() -> None:
    """Expansion am Anfang: Git Status, Log, Remote, Pull – Befehl und Ausgabe sichtbar."""
    repo_root = git_ops.get_repo_root(LAB_SUITE_ROOT)
    with ui.expansion("Git (Status, Log, Remote, Pull)", value=False).classes("w-full q-mb-md"):
        if repo_root is None:
            ui.label("Kein Git-Repo erkannt (oder git nicht im PATH).").classes("text-body2 text-grey-7")
            return
        ui.label(f"Repo: {repo_root}").classes("text-caption text-grey-7 q-mb-sm")
        git_output_container = ui.column().classes("w-full")
        ui.label("Klicke einen Button – ausgeführter Befehl und Ausgabe erscheinen unten.").classes(
            "text-caption text-grey-7 q-mb-xs"
        )

        def run_and_show(args: list[str], description: str) -> None:
            ok, out, err, cmd = git_ops.run_git(args, repo_root)
            _show_git_output_in_container(git_output_container, cmd, out, err)
            if ok:
                ui.notify(f"{description}: OK", type="positive")
            else:
                ui.notify(f"{description}: Fehler", type="warning")

        with ui.row().classes("q-gutter-sm wrap"):
            ui.button("Git Status", on_click=lambda: run_and_show(["status"], "Git Status")).props(
                "flat dense color=secondary"
            )
            ui.button("Git Log (-10)", on_click=lambda: run_and_show(["log", "--oneline", "-10"], "Git Log")).props(
                "flat dense color=secondary"
            )
            ui.button("Git Remote", on_click=lambda: run_and_show(["remote", "-v"], "Git Remote")).props(
                "flat dense color=secondary"
            )
            def do_pull() -> None:
                ok_b, out, _, _ = git_ops.run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root)
                branch = out.strip() if ok_b and out.strip() else "main"
                run_and_show(["pull", "upstream", branch, "--no-edit"], "Pull upstream")

            ui.button("Pull (upstream)", on_click=do_pull).props("flat dense color=primary").tooltip(
                "git pull upstream <aktueller Branch> – Remote 'upstream' muss existieren"
            )
        ui.separator().classes("q-my-sm")
        with git_output_container:
            ui.label("(Befehl und Ausgabe nach Klick auf einen der Buttons oben)").classes(
                "text-caption text-grey-6"
            )


def _show_git_push_dialog(folder_name: str) -> None:
    """Dialog: Git add/commit/push für submissions-Ordner; zeigt ausgeführte Befehle und Ausgabe."""
    repo_root = git_ops.get_repo_root(LAB_SUITE_ROOT)
    if repo_root is None:
        ui.notify("Kein Git-Repo erkannt.", type="warning")
        return
    ok, msg, steps = git_ops.push_submissions_folder(repo_root, folder_name)
    lines: list[str] = []
    for cmd, out, err in steps:
        lines.append(f"$ {cmd}")
        if out:
            lines.append(out)
        if err:
            lines.append(err)
        lines.append("")
    text = "\n".join(lines).strip()
    with ui.dialog() as d, ui.card().classes("q-pa-md min-w-[360px] max-w-[90vw] max-h-[85vh] overflow-auto"):
        ui.label("Git Push (Abgabe)").classes("text-subtitle1 text-weight-medium")
        ui.label(folder_name).classes("text-caption text-grey-7 q-mb-sm")
        if ok:
            ui.label(msg).classes("text-body2 text-green-8")
        else:
            ui.label(msg).classes("text-body2 text-red-8")
        ui.label("Ausgeführte Befehle und Ausgabe:").classes("text-caption text-weight-bold q-mt-sm")
        ui.html(
            f'<pre class="q-pa-sm bg-grey-3 rounded-borders" style="white-space:pre-wrap;max-height:320px;overflow:auto;font-size:0.85em;">{_escape_html(text)}</pre>'
        )
        ui.button("Schließen", on_click=d.close).props("flat color=primary").classes("q-mt-sm")
    d.open()
    if ok:
        ui.notify("Push erfolgreich.", type="positive")
    else:
        ui.notify(msg, type="negative")


def build_ui() -> None:
    """Baut die Launcher-UI: Git-Expansion, Kapitel-Gruppen, Einträge mit Start-Button, Submit-Zeile pro Lab."""
    chapters = scan_labs(LABS_DIR)
    if not chapters:
        ui.label("Keine Labs gefunden. Bitte lab_suite/labs/ prüfen.").classes("text-weight-medium")
        return

    instructor_mode = _is_instructor_mode()
    submit_email = submit.read_submit_to_email(LAB_SUITE_ROOT)

    _build_git_expansion()

    ui.label("Verfügbare Labs und Skripte").classes("text-h5 q-mb-md")
    ui.label("Klicke auf „Starten“, um eine App (Browser) oder ein Skript (Konsole/Matplotlib) zu starten.").classes(
        "text-body2 text-grey-7 q-mb-lg"
    )

    expansion_state = _read_expansion_state()
    for group in chapters:
        # State pro Kapitel: gespeichert in launcher_expansion_state.json, default offen (True)
        initial_open = expansion_state.get(group.title, True)
        with ui.expansion(group.title, value=initial_open).classes("w-full launcher-chapter-expansion") as chapter_exp:
            def _chapter_expansion_handler(e, title=group.title):
                is_open = getattr(e, "value", None)
                if is_open is None and getattr(e, "args", None) and len(e.args) > 0:
                    is_open = e.args[0]
                _on_expansion_change(title, bool(is_open) if is_open is not None else True)

            chapter_exp.on_value_change(_chapter_expansion_handler)
            with ui.column().classes("w-full bg-grey-2 rounded-borders q-pa-md"):
                for folder_name, folder_entries in _group_entries_by_folder(group.entries):
                    task_done_date = _read_task_done(folder_name)
                    card_bg = "bg-green-1" if task_done_date else "bg-white"
                    # Leicht schattierter Container pro Aufgabenblock (Einträge + Aufgabe); hellgrün wenn als erledigt markiert
                    with ui.card().classes(f"w-full q-mb-md rounded-borders {card_bg}").style("box-shadow: 0 1px 3px rgba(0,0,0,0.08)"):
                        deadline_str = _read_deadline(folder_name)
                        for entry in folder_entries:
                            with ui.row().classes("items-center q-gutter-sm full-width q-mb-xs"):
                                if entry.kind == "app":
                                    ui.icon("web", size="sm").classes("text-primary")
                                elif entry.kind == "script":
                                    ui.icon("code", size="sm").classes("text-secondary")
                                else:
                                    ui.icon("description", size="sm").classes("text-grey-7").tooltip(
                                        "Dokumentenabgabe (keine Programmieraufgabe)"
                                    )
                                ui.label(entry.label).classes("flex-grow")
                                if entry.has_submissions_folder:
                                    ui.badge("submissions/", color="green").classes("text-caption")
                                    ui.button(
                                        icon="folder_open",
                                        on_click=lambda fn=folder_name: _show_submissions_dialog(fn),
                                    ).props("flat dense round color=secondary").tooltip("Inhalt von submissions/ anzeigen")
                                    ui.button(
                                        icon="folder",
                                        on_click=lambda fn=folder_name: _on_open_folder(fn),
                                    ).props("flat dense round color=secondary").tooltip(
                                        "submissions/ im Explorer öffnen (Dateien hinzufügen, Stub-Dokumente bearbeiten oder entfernen)"
                                    )
                                    if instructor_mode:
                                        ui.button(
                                            icon="edit_calendar",
                                            on_click=lambda fn=folder_name: _show_deadline_picker_dialog(fn),
                                        ).props("flat dense round color=primary").tooltip("Abgabedatum setzen (Instructor)")
                                if deadline_str:
                                    ui.label(f"Abgabe bis: {deadline_str}").classes(
                                        "text-caption text-weight-medium text-grey-8"
                                    )
                                    reminder = _deadline_reminder(folder_name)
                                    if reminder:
                                        msg, color = reminder
                                        ui.label(msg).classes(f"text-caption text-weight-medium {color}")
                                if entry.kind in ("script", "app") and _get_doc_md_path(entry.folder_name):
                                    ui.button(
                                        icon="menu_book",
                                        on_click=lambda fn=entry.folder_name: _show_doc_dialog(fn),
                                    ).props("flat dense round color=secondary").tooltip("Erklärung (doc.md) im Browser anzeigen")
                                if entry.kind == "script":
                                    ui.button(
                                        "EDIT",
                                        icon="edit",
                                        on_click=lambda e=entry: _open_script_in_editor(e),
                                    ).props("flat dense color=secondary").tooltip("Skript im Editor öffnen (z. B. VS Code)")
                                elif entry.kind == "app" and _get_app_user_template_path(entry.folder_name):
                                    ui.button(
                                        "EDIT",
                                        icon="edit",
                                        on_click=lambda e=entry: _open_app_user_template(e),
                                    ).props("flat dense color=secondary").tooltip("assignments/user_template.py im Editor öffnen (eigenen Code ergänzen)")
                                if entry.kind != "document":
                                    ui.button("Starten", on_click=lambda e=entry: _launch(e)).props("flat dense color=primary")
                        # Fragebogen-Button: nur wenn submissions/ existiert und questions.* (md/docx/txt) vorhanden (einmal pro Karte)
                        if any(e.has_submissions_folder for e in folder_entries) and _has_questions_file(folder_name):
                            with ui.row().classes("items-center q-gutter-sm full-width q-mt-xs"):
                                ui.icon("quiz", size="sm").classes("text-secondary")
                                ui.label("Fragebogen").classes("text-caption text-grey-7")
                                ui.button(
                                    "Öffnen / Bearbeiten",
                                    icon="edit_note",
                                    on_click=lambda fn=folder_name: _open_questionnaire(fn),
                                ).props("flat dense color=secondary").tooltip(
                                    "answers.<ext> aus questions.<ext> anlegen (falls neu) und öffnen (Format: md, docx, txt)"
                                )
                                if _has_console_log(folder_name):
                                    ui.button(
                                        icon="merge_type",
                                        on_click=lambda fn=folder_name: _merge_console_log_into_answers(fn),
                                    ).props("flat dense round color=secondary").tooltip(
                                        "Konsolenausgabe (console_log.txt) in answers einfügen"
                                    )
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

                        # SUBMIT-Checkbox: Aufgabe als erledigt markieren (State in submissions/task_done.txt, session-übergreifend + per Git sichtbar)
                        def _on_submit_check(folder: str, value: bool) -> None:
                            if value:
                                if not _write_task_done(folder):
                                    ui.notify("Speichern fehlgeschlagen.", type="negative")
                                    return
                                ui.notify("Als erledigt gespeichert (Abgabe am " + _read_task_done(folder) + ").", type="positive")
                            else:
                                # Uncheck: task_done.txt löschen, Karte wird nach Reload wieder weiß
                                _clear_task_done(folder)
                                ui.notify("Markierung entfernt.", type="info")
                            ui.run_javascript("window.location.reload()")

                        with ui.row().classes("items-center q-gutter-sm full-width q-mt-sm q-pt-sm border-top"):
                            # on_change muss im Konstruktor übergeben werden (NiceGUI registriert es sonst nicht).
                            # fn=folder_name bindet den Ordner pro Karte. Neuer Wert aus e.args oder e.sender.value.
                            def _submit_check_handler(e, fn=folder_name):
                                val = True
                                if getattr(e, "args", None) is not None and len(e.args) > 0:
                                    val = bool(e.args[0])
                                elif getattr(e, "sender", None) is not None and hasattr(e.sender, "value"):
                                    val = bool(e.sender.value)
                                _on_submit_check(fn, val)

                            submit_check = ui.checkbox(
                                "SUBMIT (als erledigt markieren)",
                                value=bool(task_done_date),
                                on_change=_submit_check_handler,
                            )
                            if task_done_date:
                                ui.label(f"Abgabe am {task_done_date}").classes("text-caption text-weight-medium text-green-8")
                            if any(e.has_submissions_folder for e in folder_entries):
                                ui.button(
                                    "Git Push",
                                    icon="push",
                                    on_click=lambda fn=folder_name: _show_git_push_dialog(fn),
                                ).props("flat dense color=primary").tooltip(
                                    "git add submissions/ → commit → push origin (Ausgabe im Dialog)"
                                )

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
            /* Sticky: Banner + Port-Check bleiben beim Scrollen sichtbar */
            .launcher-sticky-header { position: sticky; top: 0; z-index: 10; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
            /* Nur die äußere Kapitel-Expansion: Header-Label groß */
            .launcher-chapter-expansion .q-expansion-item__container > .q-item .q-item__label { font-size: 1.35rem; font-weight: 600; }
            .launcher-chapter-expansion .q-expansion-item__container > .q-item { min-height: 48px; }
            /* Innere Expansionen (Aufgabe anzeigen, E-mail Fallback): blau, geringere Signifikanz */
            .launcher-chapter-expansion .q-expansion-item__content .q-expansion-item .q-item__label { font-size: 1rem; font-weight: normal; color: #1565c0; }
            </style>
            """
        )
        with ui.column().classes("q-pa-lg w-full"):
            with ui.column().classes("launcher-sticky-header q-pa-lg w-full rounded-borders q-mb-md"):
                Banner(
                    text1=title,
                    text2="Labs starten · Aufgaben einsehen",
                    text3="Abgaben senden",
                    height="80px",
                ).classes("w-full")
                _build_port_status_card()
            build_ui()

    ui.run(port=port, title=title, reload=False)
