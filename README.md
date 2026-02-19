# KT-Lab – Anleitung für Studierende

Nach dem Klonen dieses Repos: Umgebung einrichten und Labs starten.

**Python im Kurs:** Ihr lernt Python mit drei Anwendungsarten – **Konsolen-Output** (print, Logs), **Matplotlib-Fenster** (klassische Skripte mit `plt.show()`) und **Browser-GUI** (Labs mit interaktiver Weboberfläche). Alle drei nutzen dieselbe Umgebung (`requirements.txt`).

## 1. Virtuelle Umgebung (empfohlen)

```bash
# Im Repo-Root (KT-course)
python -m venv .venv

# Aktivierung:
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate
```

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
