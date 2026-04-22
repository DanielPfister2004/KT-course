# KT-Lab – Anleitung für Studierende

Nach dem Klonen dieses Repos: Umgebung einrichten und Labs starten.

**Python im Kurs:** Ihr lernt Python mit drei Anwendungsarten – **Konsolen-Output** (print, Logs), **Matplotlib-Fenster** (klassische Skripte mit `plt.show()`) und **Browser-GUI** (Labs mit interaktiver Weboberfläche). Alle drei nutzen dieselbe Umgebung (`requirements.txt`). Für die Labs wird **Python 3.10** empfohlen.

---

## 0. Python 3.10 herunterladen und installieren

Falls auf deinem PC noch kein Python 3.10 installiert ist:

### Windows

1. **Offizielle Seite:** Gehe zu [python.org/downloads](https://www.python.org/downloads/).
2. **Ältere Version wählen:** Für Python 3.10 scrolle nach unten zu „Looking for a specific release?“ und wähle **Python 3.10.x** (z. B. 3.10.11), oder öffne direkt [python.org/downloads/release/python-31011](https://www.python.org/downloads/release/python-31011/).
3. **Installer laden:** Lade den **Windows installer (64-bit)** herunter (z. B. `python-3.10.11-amd64.exe`).
4. **Installation:** Starte den Installer.
   - Wichtig: Setze einen Haken bei **„Add Python 3.10 to PATH“**, damit du `python` bzw. `py` in der Konsole nutzen kannst.
   - „Install Now“ wählen oder „Customize“ für einen eigenen Installationsordner.
5. **Prüfen:** Neue Konsole (PowerShell oder CMD) öffnen und eingeben:
   ```bash
   py -3.10 --version
   ```
   Es sollte z. B. `Python 3.10.11` angezeigt werden.

### macOS / Linux

- **macOS:** Von [python.org](https://www.python.org/downloads/) den Installer für macOS laden, oder mit Homebrew: `brew install python@3.10`. Danach oft als `python3.10` aufrufbar.
- **Linux:** Über den Paketmanager, z. B. `sudo apt install python3.10 python3.10-venv` (Ubuntu/Debian) oder `sudo dnf install python3.10` (Fedora). Der Aufruf ist meist `python3.10`.

---

## 1. Virtuelle Umgebung mit Python 3.10 anlegen (empfohlen)

Im Repo-Root (z. B. `KT-workspace` oder `KT-course`) eine venv mit **Python 3.10** erstellen:

```bash
# Windows (py-Launcher – stellt Python 3.10 bereit):
py -3.10 -m venv .venv

# Windows (falls "python" bereits Python 3.10 ist):
python -m venv .venv

# Linux/macOS:
python3.10 -m venv .venv
```

**Aktivierung:**

```bash
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate
```

Nach der Aktivierung zeigt die Eingabezeile z. B. `(.venv)` an – dann nutzt `pip` und `python` automatisch diese Umgebung.

## 2. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

Falls keine `requirements.txt` im Root liegt: Sie kann vom Dozenten bereitgestellt werden oder liegt in `lab_suite/`. Dann z. B.:

```bash
pip install -r lab_suite/requirements.txt
```

## 3. Labs starten

**Option A – App-Launcher (Übersicht):**

```bash
cd lab_suite
python -m app_launcher
```

Im Browser siehst du alle verfügbaren Labs und Skripte nach Kapiteln; mit „Starten“ startest du die gewünschte App oder das Skript.

**Option B – Einzelnes Lab direkt:**

```bash
cd lab_suite
python -m labs.01_05_chapter1
```

Browser typisch unter `http://localhost:8080`. Andere Labs: Modulname anpassen (z. B. `labs.01_02_Informationstheorie`).

## 4. Klassische Skripte (Konsole, Matplotlib-Fenster)

Skripte, die nur in der Konsole ausgeben oder ein **Matplotlib-Fenster** öffnen (`import matplotlib.pyplot as plt` … `plt.show()`), wie gewohnt ausführen:

```bash
python pfad/zum/skript.py
```

Dabei wird ein Grafikfenster geöffnet; die Konsole bleibt für Ausgaben verfügbar. Dafür ist kein Umstieg auf Plotly/Browser nötig.

---

**Plotly (Graphen in den Labs):** Die App nutzt eine lokale Kopie von Plotly.js (`/static/plotly.min.js`), sodass keine Internetverbindung nötig ist.

Bei Fragen: Hinweise des Dozenten oder der Kursunterlagen beachten.
