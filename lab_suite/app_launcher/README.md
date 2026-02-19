# KT-Lab App-Launcher

Übersicht aller Labs und Skripte in `lab_suite/labs/`, hierarchisch nach Kapitel. Ein Klick startet NiceGUI-Apps oder einzelne Python-Skripte.

## Start

Aus dem Ordner **lab_suite**:

```bash
python -m app_launcher
```

Browser öffnet sich typisch unter `http://localhost:8082`.

## Erkennung

Pro **Aufgabenordner** (z. B. 01_01_Signale_basics) gilt eindeutig: Es liegt **entweder** eine NiceGUI-App **oder** ein bzw. mehrere einfache Python-Skripte – nie beides.

- **NiceGUI-App:** Ordner enthält `__main__.py` → ein Eintrag, Start mit `python -m labs.<Ordnername>`.
- **Skripte:** Ordner ohne `__main__.py`, dafür `.py`-Dateien auf oberster Ebene → je Skript ein Eintrag, Start mit `python labs/<Ordner>/<Skript>.py`.

Die Hierarchie folgt dem Ordnernamen (z. B. `01_01_...` → Kapitel 01). Wenn im Ordner `submissions/task.md` existiert, wird „Aufgabe anzeigen“ **einmal pro Aufgabenordner** (nicht pro Skript) in einer Expansion angezeigt.

## Submissions (Abgaben)

**Konvention:** Pro Lab ein Ordner **`submissions/`** im jeweiligen Lab-Verzeichnis. Pro Aufgabenstellung (Lab) gibt es im Launcher eine Zeile **Abgabe (E-Mail-Fallback)** mit:

- **ZIP erstellen** – packt den Inhalt von `submissions/` in `abgabe_<Lab>_<datum>.zip` im gleichen Ordner.
- **Ordner öffnen** – öffnet den Dateimanager (Explorer/Finder) im `submissions/`-Ordner; Studierende können das ZIP auswählen und in die E-Mail ziehen.
- **E-Mail öffnen** – öffnet den Standard-Mail-Client mit Zieladresse und Betreff `[kt-assignment] ID=<Lab-Name>`.

**Zieladresse (repo-weit):** In **`lab_suite/submit_manifest.txt`** wird die Instructor-Adresse hinterlegt (eine Zeile, Format `submit_to_email=adresse@example.com`). Der Launcher liest diese Datei; ohne Eintrag ist „E-Mail öffnen“ deaktiviert.
