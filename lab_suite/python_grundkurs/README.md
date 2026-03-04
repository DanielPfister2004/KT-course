# Python-Grundkurs (KT)

Kapitelweise geordneter Python-Kurs für Studierende der Kommunikationstechnik, **parallel** zur Vorlesungsstruktur. Dieser Ordner liegt neben `labs/` (dort die konkreten Tasks/Abgaben) und dient der **didaktischen Reihenfolge der Python-Inhalte** sowie der späteren Verknüpfung mit den Vorlesungskapiteln aus dem Obsidian-Vault (siehe `kt_lecture_scriptum_index.json` im KT-workspace-Root).

## Anrede

In allen Notebooks und kursöffentlichen Texten gilt durchgängig **„Du“** – die Kursplattform spricht die Studierenden auf Augenhöhe an. Nur die Lehrenden nutzen in der direkten Ansprache weiterhin „Sie“.

## Zweck

- **Reihenfolge festlegen:** In welcher Reihenfolge sind Python-Themen für Anfänger sinnvoll? (Einführung → Datentypen → Variablen → … → Funktionen → Module → ggf. OOP.)
- **Anknüpfung an KT:** Sobald die Grundstruktur steht, können einzelne Python-Kapitel explizit an Vorlesungskapitel angebunden werden (z. B. „Datentypen + Variablen“ → **01.2 Informationstheorie**: Signalvorrat, Entropie, mittlerer Binärstellenaufwand).
- **Ein Ort für Material:** Pro Kapitel Platz für kurze Texte, Beispiele (`.py` oder `.ipynb`) und Verweise auf `lecture_content` (Skriptum `*__de.md`).

## Jupyter Notebook – Bedienung

Eine kurze Anleitung zum Bedienen von Jupyter Notebooks (Zellen, Shortcuts, Code vs. Markdown, Dateien einlesen, Links, Plotten) findest du in **JUPYTER_NOTEBOOK_README.md**.

## Struktur

- **STRUKTUR.md** – empfohlene Reihenfolge der Python-Kapitel und (optional) Zuordnung zu KT-Vorlesungskapiteln.
- **00_Einfuehrung**, **01_Erste_Schritte**, … – je ein Ordner pro Python-Kapitel mit kurzer Beschreibung (README) und Platz für Beispiele.

Die Nummerierung (00, 01, 02, …) folgt der **didaktischen Logik des Python-Kurses**, nicht zwingend der Nummerierung der KT-Vorlesung (01.Informationstheorie, 02.Signale, …). Die Verknüpfung KT ↔ Python wird in STRUKTUR.md geführt.

## Konzept: Ein Haupt-Notebook pro Kapitel + progressive/fachliche Vertiefung

**Empfohlenes Vorgehen:**

- **Pro Kapitel ein Haupt-Notebook** (z. B. `02_Datentypen.ipynb`): kurze, klare Einführung in die Python-Themen (Syntax, Konzepte). Das ist der **Pflichtpfad** – alle können damit durch den Kurs.
- **Fachliche Inhalte und progressive Aufgaben** können auf zwei Wegen ergänzt werden:
  1. **Option A – im gleichen Notebook:** Am Ende (oder in einem markierten Abschnitt „Optional / Vertiefung“) zusätzliche Zellen mit KT-Beispielen oder etwas anspruchsvolleren Aufgaben. Wer will, macht sie; wer nur die Basics braucht, überspringt sie.
  2. **Option B – eigenes Vertiefungs-Notebook:** Zusätzliche Datei im gleichen Kapitelordner, z. B. `02_Datentypen_KT_Beispiele.ipynb` oder `02b_Informationstheorie_Anknuepfung.ipynb`. Darin: progressive Aufgaben, Verknüpfung mit Vorlesung (z. B. Signalvorrat, Entropie), Verweis auf `lecture_content` im Index. Im Haupt-Notebook ein kurzer Link: „Fachliche Vertiefung: [02_KT_Beispiele](02_Datentypen_KT_Beispiele.ipynb)“.

**Vorteil:** Ein klarer Einstieg pro Kapitel, kein Überforderung; wer mehr will, nutzt die optionalen Teile oder das Zusatz-Notebook. Mehrere fachliche Beispiele und progressive Aufgaben können schrittweise ergänzt werden, ohne das Haupt-Notebook zu überladen.

## LaTeX / mathematische Formeln in Notebooks

Damit Formeln in **Jupyter**, **JupyterLab**, **VS Code** und **Cursor** korrekt dargestellt werden, verwenden wir in Markdown-Zellen durchgängig:

- **Inline:** `$...$` (z. B. `$E = m c^2$`)
- **Abgesetzt:** `$$...$$` (z. B. `$$\int_0^T p(t)\,\mathrm{d}t$$`)

Die ältere Schreibweise `\(...\)` / `\[...\]` wird von einigen Viewern (z. B. Cursor/VS Code) nicht gerendert; entsprechende Notebooks wurden auf `$`/`$$` umgestellt. Bei neuen Inhalten bitte von vornherein `$` und `$$` verwenden.

## Bezug zum Lecture-Index

Die Vorlesungsskripte sind in **`kt_lecture_scriptum_index.json`** (KT-workspace-Root) erfasst: Hauptkapitel, Unterkapitel, `lecture_content`-Pfade zu den `*__de.md`-Dateien. Beim Ausarbeiten der Python-Kapitel können diese Pfade genutzt werden, um z. B. „Zu diesem Python-Kapitel passendes Vorlesungskapitel: 01.Informationstheorie und Codierung → 2. Informationstheorie“ anzugeben und Verweise/Links zu setzen.
