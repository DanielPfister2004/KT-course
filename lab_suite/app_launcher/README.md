# KT-Lab App-Launcher

Übersicht aller Labs und Skripte in `lab_suite/labs/`, hierarchisch nach Kapitel. Ein Klick startet NiceGUI-Apps oder einzelne Python-Skripte.

## Start

Aus dem Ordner **lab_suite**:

```bash
python -m app_launcher
```

Browser öffnet sich typisch unter `http://localhost:8082`.

**Port 8082 schon belegt (verwaiste Launcher-Instanz)?** Port freimachen und danach Launcher neu starten:
```bash
# Vom Repo-Root (KT-workspace):
python lab_suite/scripts/free_port_8082.py
# oder unter Windows:
.\free_port_8082.ps1
```

**Git (Expansion am Anfang):** Oben erscheint eine Expansion **„Git (Status, Log, Remote, Pull)“**. Buttons: **Git Status** (Ausgabe von `git status`), **Git Log (-10)** (`git log --oneline -10`), **Git Remote** (`git remote -v`), **Pull (upstream)** (`git pull upstream <Branch>`). Der jeweils ausgeführte Befehl und die Konsolenausgabe werden darunter in einem scrollbaren Bereich angezeigt. So sehen Studierende genau, welches Kommando ausgeführt wurde.

**Git Push pro Aufgabe:** In jeder Aufgabenkarte mit submissions-Ordner gibt es einen Button **„Git Push“**. Ein Klick führt aus: `git add lab_suite/labs/<Ordner>/submissions`, `git commit -m "committing ..."`, `git push origin`. Ein Dialog zeigt die ausgeführten Befehle und die Ausgabe (Feedback für Studierende). Voraussetzung: Das Projekt liegt in einem Git-Repo (z. B. Studenten-Fork).

## Erkennung

Es wird **für jeden Unterordner** unter `labs/` mindestens eine **Task-Card** erzeugt. Drei Fälle:

- **NiceGUI-App:** Ordner enthält `__main__.py` → ein Eintrag mit **Web-Icon**, Start mit `python -m labs.<Ordnername>`.
- **NiceGUI-Apps:** **EDIT** öffnet – falls vorhanden – **`assignments/user_template.py`** im Editor (hier ergänzen Studierende den eigenen Code). **Doc** (Icon Buch) zeigt `doc.md` im Browser. **Starten** startet die App.
- **Python-Skripte:** **EDIT** öffnet das Skript im Editor, **Doc** zeigt `doc.md` im Browser, **Starten** führt das Skript aus.
- **Nur Dokumentenabgabe:** Weder App noch Skripte → ein Eintrag mit **Dokument-Icon**; gleiche Nutzung von `submissions/` (Abgabe, Ordner, Drop-Zone), aber **kein „Starten“-Button** (keine Programmieraufgabe).

Die Hierarchie folgt dem Ordnernamen (z. B. `01_01_...` → Kapitel 01). Wenn `submissions/task.md` existiert, wird „Aufgabe anzeigen“ **einmal pro Aufgabenordner** in einer Expansion angezeigt.

**Fragebogen (questions.* → answers.*):** Legst du in einem Lab unter `submissions/` eine Fragenvorlage ab (`questions.md`, `questions.docx` oder `questions.txt`), erscheint **„Fragebogen – Öffnen / Bearbeiten“**. Die Priorität ist: `.md` → `.docx` → `.txt` (erste gefundene Datei zählt). Ein Klick kopiert bei Bedarf `questions.<ext>` nach `answers.<ext>` und öffnet die Antwortdatei im Standard-Programm. **Bilder in .md:** Mit `![Beschreibung](screenshot.png)` lassen sich Screenshots einbinden.

**Konsolenausgabe einfügen:** Schreibt ein Skript seine Ausgabe parallel in `submissions/console_log.txt`, erscheint neben dem Fragebogen-Button ein **Merge-Symbol**. Ein Klick hängt den Inhalt von `console_log.txt` an `answers.md` bzw. `answers.txt` an (unter „Konsolenausgabe“). So können Studierende den Skript-Output in den Antwortbogen übernehmen und kommentieren. Reihenfolge: Fragebogen öffnen (answers anlegen) → Skript ausführen → Merge klicken → Antworten kommentieren.

## Submissions (Abgaben)

**Konvention:** Pro Lab ein Ordner **`submissions/`** im jeweiligen Lab-Verzeichnis. In jeder **Aufgabenkarte** (links neben „Starten“) gibt es bei Labs mit submissions-Ordner:
- **Ordner geöffnet (Icon):** Zeigt den Inhalt von submissions/ in einem Dialog (Dateiliste).
- **Ordner (Icon):** Öffnet den Ordner **submissions/** im **Windows-Explorer** (bzw. Dateimanager). So können Studierende Dateien ablegen, Stub-Dokumente bearbeiten oder entfernen und Abgaben vorbereiten. Dieselbe Aktion gibt es unter „E-mail Fallback Abgaben“ als Button „Ordner öffnen“.

Pro Aufgabenstellung (Lab) gibt es zusätzlich im Launcher eine Zeile **Abgabe (E-Mail-Fallback)** mit:

- **ZIP erstellen** – packt den Inhalt von `submissions/` in `abgabe_<Lab>_<datum>.zip` im gleichen Ordner.
- **Ordner öffnen** – öffnet den Dateimanager (Explorer/Finder) im `submissions/`-Ordner; Studierende können das ZIP auswählen und in die E-Mail ziehen.
- **E-Mail öffnen** – öffnet den Standard-Mail-Client mit Zieladresse und Betreff `[kt-assignment] ID=<Lab-Name>`.

**Zieladresse (repo-weit):** In **`lab_suite/submit_manifest.txt`** wird die Instructor-Adresse hinterlegt (eine Zeile, Format `submit_to_email=adresse@example.com`). Der Launcher liest diese Datei; ohne Eintrag ist „E-Mail öffnen“ deaktiviert.

**Abgabedatum pro Aufgabe:** Optional kann pro Lab eine Datei **`submissions/deadline.txt`** angelegt werden. Inhalt: **eine Zeile**, Datum im Format **`YYYY-MM-DD`** (z. B. `2025-04-15`). Der Launcher zeigt dann in der Aufgabenkarte links neben „Starten“ den Text **„Abgabe bis: DD.MM.YYYY“** an.

**Instructor-Modus (nur für Dozenten):** Wenn im Ordner **lab_suite** eine Datei **`.instructor_key`** existiert und nicht leer ist, erscheint pro Aufgabenkarte (mit submissions/) ein **Kalender-Icon**. Ein Klick öffnet einen Dialog mit Date-Picker: Abgabedatum wählen → „Übernehmen“ speichert in `deadline.txt` und lädt die Seite neu; „Löschen“ entfernt das Abgabedatum. Die Datei `.instructor_key` darf **nicht** ins Studenten-Repo exportiert werden (steht in `.gitignore` und im Export-Skript in der Ignore-Liste). Dozent: einmalig z. B. `echo kt-instructor > lab_suite/.instructor_key` anlegen.
