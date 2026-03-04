# Jupyter Notebook – Bedienungsanleitung

Kurze Anleitung, wie du Jupyter Notebooks bedienst: Notebook öffnen, Zellen bearbeiten, Tastenkürzel, Code vs. Markdown, Dateien einlesen, Links und Bilder einbetten, Plotten.

---

## 1. Notebook starten und öffnen

- **Jupyter im Browser starten:** Zuerst im **Terminal** (z. B. PowerShell oder cmd) in den gewünschten Ordner wechseln (z. B. `cd lab_suite\python_grundkurs`) und dann eingeben:
  ```bash
  jupyter notebook
  ```
  Danach öffnet sich Jupyter im Standardbrowser; von dort aus kannst du Notebooks öffnen oder neu anlegen. Das Terminal Fenster dabei **nicht schließen** – es hält den Jupyter-Server am Laufen. Zum Beenden: im Terminal **Strg+C**.
- **Neues Notebook:** In Jupyter (Browser): Klick auf **New → Python 3** (oder den gewählten Kernel). In VS Code/Cursor: **Datei → Neu** oder `Strg+N`, dann „Jupyter Notebook“ wählen bzw. eine neue `.ipynb`-Datei anlegen.
- **Bestehendes Notebook öffnen:** Doppelklick auf eine `.ipynb`-Datei oder in Jupyter über das Dateibrowser-Fenster die Datei auswählen.
- **Kernel starten:** Beim ersten Öffnen startet der Kernel meist automatisch. Sonst: Menü **Kernel → Restart** (oder in der Toolbar das „Play“-Symbol).

---

## 2. Kommandomodus und Bearbeitungsmodus

Jupyter unterscheidet zwei Modi, in denen Tastendrücke unterschiedlich wirken:

- **Bearbeitungsmodus (Edit Mode):** Du bearbeitest den **Inhalt** einer Zelle – der Cursor blinkt in der Zelle, du tippst Text oder Code. Alles, was du eintippst, landet **in der Zelle**. In den Bearbeitungsmodus kommst du mit **Enter** (nach Klick in die Zelle oder Auswahl der Zelle).
- **Kommandomodus (Command Mode):** Die Zelle ist **ausgewählt**, aber der Cursor ist nicht zum Tippen in der Zelle. Jetzt steuern Tastendrücke **Aktionen** (Zelle einfügen, löschen, Typ wechseln usw.). In den Kommandomodus wechselst du mit **Esc**.

**Wichtig – Kleinbuchstaben:** Die Zellen-Shortcuts reagieren auf **Kleinbuchstaben** (**a**, **b**, **d**, **m**, **y**). Du musst also die Taste **ohne Shift** drücken! **Esc**, danach **y** = Code-Zelle, **m** = Markdown-Zelle, **d** zweimal = Zelle löschen, **a** = Zelle darüber, **b** = Zelle darunter. Wenn du **Shift+m** drückst, entsteht ein großes „M“ – dann wird oft „Zellen zusammenführen“ ausgelöst statt „Markdown“. **Zuerst Esc**, dann den gewünschten Buchstaben **als Kleinbuchstaben** (ohne Shift).

In Jupyter (Browser) erkennst du den Modus oft an der **Umrandung**: Im Kommandomodus ist die Zelle mit einem kräftigen Rahmen markiert; im Bearbeitungsmodus siehst du einen blinkenden Cursor in der Zelle.

**Wenn Esc und die Buchstaben-Shortcuts bei dir nicht reagieren:**

1. **Fokus prüfen:** Der Browser muss die Tastatureingaben an das **Notebook** schicken. Klicke einmal **mitten in den Notebook-Bereich** (auf eine Zelle oder in den Rand neben den Zellen), sodass kein anderes Element (Adresszeile, anderes Tab, Suchfeld) den Fokus hat. Danach **Esc** drücken – die Zelle sollte einen deutlichen Rahmen bekommen (Kommandomodus). Erst dann z. B. **b** für neue Zelle darunter oder **d**, **d** zum Löschen (Kleinbuchstaben).
2. **Jupyter Classic vs. JupyterLab:** Du startest mit `jupyter notebook` die **klassische** Oberfläche (Tabs, Menü „Cell“, „Insert“). Wenn du stattdessen **JupyterLab** nutzt (`jupyter lab`), sieht die Oberfläche anders aus; dort sind das **Dropdown (Code/Markdown)** und die **Plus-Buttons** (+ Code / + Markdown) die normale Art, Zelltyp zu wechseln und Zellen einzufügen. Die Einzelbuchstaben-Shortcuts können in JupyterLab abweichen – probiere nach Klick ins Notizbuch **Esc**, dann **b** oder **d**, **d** (jeweils Kleinbuchstaben).
3. **Immer möglich: Menü und Toolbar.** Egal welcher Modus: Über **Menü „Insert“** (neue Zelle oben/unten), **Menü „Cell“** (Zelltyp, Löschen, Ausführen) und die **Toolbar** (Buttons für Run, + Zelle, Zelltyp-Dropdown) erreichst du alles auch ohne Shortcuts. Wenn die Tastenkürzel nicht wollen, einfach Menü oder Dropdown nutzen.

**Nur a/b funktionieren, aber d d / m / y nicht:** Jupyter reagiert auf **Kleinbuchstaben** – du musst die Taste **ohne Shift** drücken, die **d**, **m** oder **y** erzeugt. Auf deutscher Tastatur liegt **y** auf einer anderen Taste (oft links neben dem T). Zum Löschen: nacheinander zweimal **d** (Kleinbuchstabe). Für Code: **y**, für Markdown: **m** (beides Kleinbuchstabe, ohne Shift). Wenn es trotzdem nicht geht: **Menü „Cell“ → „Delete Cells“** bzw. **„Cell“ → „Cell Type“ → „Code“** / **„Markdown“** (oder Dropdown in der Toolbar).

**Mit „m“ kommt Zusammenführen statt Markdown:** Wenn du aus Versehen **Shift+m** drückst, entsteht ein großes M und es können Zellen zusammengeführt werden. Für Markdown wirklich nur **m** (Kleinbuchstabe, ohne Shift) nach **Esc** drücken. In **JupyterLab** kann die Belegung abweichen – dann Zelltyp per **Dropdown** oder **Menü „Cell“ → „Cell Type“** wechseln.

---

## 3. Zellen: Einfügen, Löschen, Verschieben

| Aktion | Vorgehen |
|--------|----------|
| **Neue Zelle darunter** | Nach Auswahl einer Zelle: **b** (Kleinbuchstabe, im Kommandomodus). Oder Menü **Insert → Insert Cell Below** / **+ Code** (VS Code). |
| **Neue Zelle darüber** | **a** (Kleinbuchstabe, im Kommandomodus). Oder **Insert → Insert Cell Above**. |
| **Zelle löschen** | Zelle auswählen, **Esc**, dann **d**, **d** (zweimal den Kleinbuchstaben **d** – ohne Shift, sonst passiert etwas anderes). In VS Code: Kontextmenü → „Delete Cell“. |
| **Zelle verschieben** | Zelle auswählen, dann **Pfeil hoch/runter** in der Toolbar (Jupyter) oder Zelle per Drag & Drop verschieben. |
| **Zelle teilen** | Cursor an die gewünschte Stelle setzen → **Strg+Shift+-** (Jupyter). |
| **Zellen zusammenführen** | Zellen auswählen → **Shift+m** (Großbuchstabe M erzeugen). Wenn du nur **m** (Kleinbuchstabe) drückst, wechselt in Jupyter Classic der Zelltyp zu Markdown. |

---

## 4. Zelltyp: Code vs. Markdown

| | **Code-Zelle** | **Markdown-Zelle** |
|---|----------------|-------------------|
| **Zweck** | Python-Code wird **ausgeführt** (Kernel). | Text, Formeln, Listen – wird nur **dargestellt**, nicht ausgeführt. |
| **Umschalten** | Im Kommandomodus (Esc): **y** (Kleinbuchstabe – Taste für „y“ ohne Shift). In VS Code/JupyterLab: oft Dropdown „Code“. | Im Kommandomodus (Esc): **m** (Kleinbuchstabe – Taste für „m“ ohne Shift; **Shift+m** = großes M = Zellen zusammenführen!). In JupyterLab oft nur per Dropdown oder Menü „Cell“ → „Cell Type“. |
| **Ausführung** | **Shift+Enter** oder Klick auf ▶ führt die Zelle aus. | **Shift+Enter** rendert den Markdown-Text (kein Python-Lauf). |
| **Syntax** | Gültiges Python. | Markdown + LaTeX: Überschriften mit `#`, **fett** mit `**`, Formeln mit `$...$` (inline) bzw. `$$...$$` (abgesetzt). |

**Tipp:** Für Überschriften und Erklärungen immer Markdown verwenden; für ausführbaren Code die Code-Zelle.

**Markdown-Zelle bearbeiten:** Nach dem Ausführen (Shift+Enter) siehst du den **gerenderten** Text (Überschriften, Fettdruck usw.). Um den **Quelltext** (z. B. `## Überschrift`, `**fett**`) wieder zu bearbeiten: **Doppelklick** auf die Markdown-Zelle – oder Zelle auswählen und **Enter** drücken. Dann erscheint der Rohtext zum Editieren. Mit **Shift+Enter** oder **Esc** verlässt du die Bearbeitung; Shift+Enter rendert die Zelle erneut.

---

## 5. Tastenkürzel (Shortcuts)

### Allgemein (Jupyter Classic / JupyterLab)

| Shortcut | Aktion |
|----------|--------|
| **Enter** | Zelle bearbeiten (Edit-Modus). |
| **Esc** | Kommandomodus (Cursor aus Zelle, Shortcuts aktiv). |
| **Shift+Enter** | Zelle ausführen und zur nächsten wechseln. |
| **Strg+Enter** | Zelle ausführen, Cursor bleibt in der Zelle. |
| **Alt+Enter** | Zelle ausführen und darunter neue Zelle einfügen. |

### Zellen

**Hinweis:** Diese Shortcuts gelten nur im **Kommandomodus** (zuerst **Esc**). Es sind **Kleinbuchstaben** – **a**, **b**, **d**, **m**, **y** (ohne Shift). Mit Shift würdest du z. B. **M** erzeugen und damit „Zellen zusammenführen“ auslösen statt „Markdown“.

| Shortcut | Aktion |
|----------|--------|
| **a** | Zelle **a**bove (darüber) einfügen. |
| **b** | Zelle **b**elow (darunter) einfügen. |
| **d**, **d** | Zelle löschen (**d**elete) – zweimal **d** (Kleinbuchstabe). |
| **y** | Zelltyp: **C**ode (y = Code-Mnemonic). |
| **m** | Zelltyp: **M**arkdown – nur **m** (Kleinbuchstabe); **Shift+m** = großes M = Zellen zusammenführen. In JupyterLab ggf. nur per Dropdown/Menü. |
| **Shift+m** | Großbuchstabe M → Zellen zusammenführen (merge). |
| **Strg+Shift+-** | Zelle an Cursorposition teilen. |

### Bearbeiten (im Edit-Modus, also **Enter** in der Zelle)

| Shortcut | Aktion |
|----------|--------|
| **Strg+Z** | Rückgängig. |
| **Strg+Shift+Z** / **Strg+Y** | Wiederherstellen. |
| **Strg+/** | Zeile(n) aus-/eincommenten. |
| **Strg+D** | Zeile duplizieren (manche Umgebungen). |

### Kernel

| Shortcut | Aktion |
|----------|--------|
| **0, 0** (zweimal Null) | Kernel neu starten. |
| **I, I** (zweimal I) | Kernel-Execution unterbrechen. |

### Sonstiges

| Shortcut | Aktion |
|----------|--------|
| **Strg+S** | Notebook speichern. |
| **H** | Liste aller Shortcuts anzeigen (Jupyter). |

*Hinweis:* In **VS Code** und **Cursor** können Shortcuts abweichen; dort findest du sie unter **Datei → Einstellungen → Tastenkürzel** (nach „notebook“ oder „jupyter“ suchen).

---

## 6. Dateien einlesen

Du kannst aus einer Code-Zelle heraus Dateien lesen (z. B. CSV, Text, Bilder).

**Beispiel: Textdatei**
```python
with open("pfad/zur/datei.txt", "r", encoding="utf-8") as f:
    inhalt = f.read()
print(inhalt)
```

**Beispiel: CSV mit pandas**
```python
import pandas as pd
df = pd.read_csv("daten.csv", sep=";")
df.head()
```

**Beispiel: Bild mit Matplotlib/PIL**
```python
import matplotlib.pyplot as plt
from PIL import Image
img = Image.open("bild.png")
plt.imshow(img)
plt.axis("off")
plt.show()
```

**Wichtig:** Der Pfad ist relativ zum **Arbeitsverzeichnis** (meist der Ordner, in dem das Notebook liegt, oder das beim Start von Jupyter angegebene Verzeichnis). Bei anderen Ordnern relativen Pfad angeben, z. B. `../andere_ordner/datei.csv`.

---

## 7. Links einbetten

In **Markdown-Zellen** kannst du Links so einbetten:

- **Einfacher Link:** `[Anzeigetext](https://example.com)`
- **Link zu einer anderen Datei im Projekt:** `[Beschreibung](pfad/zur/datei.ipynb)` oder `[Kapitel 02](02_Datentypen/02_Datentypen.ipynb)`
- **Link in neuem Tab:** In reinem Markdown geht das je nach Viewer; in HTML:  
  `<a href="https://example.com" target="_blank">Link</a>`

**Beispiel in einer Markdown-Zelle:**
```markdown
Siehe [Python-Dokumentation](https://docs.python.org/3/) und das [nächste Kapitel](03_Variablen/03_Variablen.ipynb).
```

---

## 8. Bilder einbinden

### In einer Markdown-Zelle

- **Lokale Datei** (Pfad relativ zum Notebook bzw. Arbeitsverzeichnis):
  ```markdown
  ![Beschreibung des Bildes](bild.png)
  ![Skizze](ordner/grafik.png)
  ```
- **Bild aus dem Internet:**
  ```markdown
  ![Beispiel](https://example.com/image.png)
  ```
- **Größe mit HTML steuern:**
  ```html
  <img src="bild.png" width="400" alt="Beschreibung">
  ```

### In einer Code-Zelle

Mit **IPython.display** (z. B. wenn der Dateiname variabel ist oder du mehrere Bilder nacheinander anzeigen willst):

```python
from IPython.display import Image, display

display(Image(filename="bild.png"))
display(Image(filename="bild.png", width=400))   # Breite in Pixel
display(Image(url="https://example.com/image.png"))
```

Mit **Matplotlib** (z. B. neben anderen Plots):

```python
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

img = mpimg.imread("bild.png")
plt.imshow(img)
plt.axis("off")
plt.show()
```

**Hinweis:** Liegt das Bild im **gleichen Ordner** wie das Notebook, reicht der Dateiname, z. B. `![Skizze](skizze.png)`.

---

## 9. Plotten (Matplotlib)

In einer **Code-Zelle**:

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 2*np.pi, 100)
y = np.sin(x)
plt.figure(figsize=(8, 4))
plt.plot(x, y, color="C0", label="sin(x)")
plt.xlabel("x")
plt.ylabel("y")
plt.title("Sinus")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

- **`plt.figure(figsize=(breite, höhe))`** – Größe der Figur (optional).
- **`plt.plot`, `plt.scatter`, `plt.hist`** – Kurven, Punkte, Histogramme.
- **`plt.xlabel`, `plt.ylabel`, `plt.title`** – Achsen und Titel.
- **`plt.legend()`** – Legende, wenn du `label=...` in den Plot-Befehlen gesetzt hast.
- **`plt.grid(True)`** – Gitter.
- **`plt.tight_layout()`** – verhindert abgeschnittene Beschriftungen.
- **`plt.show()`** – Ausgabe der Figur im Notebook.

**Mehrere Plots untereinander (Subplots):**
```python
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
ax1.plot(x, np.sin(x))
ax1.set_ylabel("sin(x)")
ax2.plot(x, np.cos(x))
ax2.set_xlabel("x")
ax2.set_ylabel("cos(x)")
plt.tight_layout()
plt.show()
```

Die Plots erscheinen direkt unter der Zelle; bei erneutem Ausführen der Zelle wird die Ausgabe aktualisiert.

---

## 10. Weitere nützliche Edit-Funktionen

- **Alle Zellen ausführen:** Menü **Cell → Run All** (oder **Kernel → Restart & Run All** für einen sauberen Lauf von oben).
- **Ausgabe löschen:** **Cell → Current Outputs → Clear** (oder nur bei einer Zelle).
- **Kernel neu starten:** **Kernel → Restart** – Variablen im Speicher sind danach weg; bei „Restart & Run All“ wird das komplette Notebook neu ausgeführt.
- **Zellen ein-/ausklappen:** In manchen Oberflächen (z. B. JupyterLab) über das kleine Dreieck links an der Zelle.
- **Suche:** **Strg+F** durchsucht in vielen Editoren das aktuelle Notebook.

---

## 11. Kurz: Typischer Arbeitsablauf

1. Notebook öffnen (oder neu anlegen).
2. Oben: Überschrift in einer **Markdown-Zelle** (`# Überschrift`).
3. Darunter: **Code-Zelle** mit Python-Code.
4. **Shift+Enter** zum Ausführen; Ausgabe erscheint unter der Zelle.
5. Weitere Erklärungen in **Markdown**, weitere Berechnungen/Plots in **Code-Zellen**.
6. **Strg+S** zum Speichern.

Bei Fragen zu Inhalten des Kurses: siehe **README.md** und die jeweiligen Kapitel-Notebooks.
