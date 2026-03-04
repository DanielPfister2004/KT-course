# Reihenfolge der Python-Kapitel und Anknüpfung an die KT-Vorlesung

Diese Datei definiert die **didaktische Reihenfolge** der Python-Inhalte und (optional) die **Verknüpfung** mit Kapiteln aus der Vorlesung (Obsidian-Vault, `kt_lecture_scriptum_index.json`).

## Empfohlene Reihenfolge der Python-Kapitel

| Nr. | Ordner | Inhalt (Gerüst) | Anknüpfung KT (Vorschlag) |
|-----|--------|------------------|----------------------------|
| 00 | **00_Einfuehrung** | Was ist Python? Wann entwickelt? Warum heißt es Python? Konzept Interpreter, Idee Objektorientierung (ohne Code). | 00.Einleitung / Kurs-Organisation |
| 01 | **01_Erste_Schritte** | Installation, erstes Programm, Ausführen (Skript vs. REPL / interaktiv). | — |
| 02 | **02_Datentypen** | Erste Datentypen: Zahlen (`int`, `float`), Strings, `bool`. | — |
| 03 | **03_Variablen_und_Operatoren** | Zuweisung, Rechnen, Vergleichsoperatoren, Ausdrücke. | — |
| 04 | **04_Listen_und_Sequenzen** | `list`, Index, Slice, einfache `for`-Schleife über Listen. | — |
| 05 | **05_Arrays** | Kein C-Array in Python; NumPy-Arrays, Index/Slice, elementweise Op.; Bezug 02.Signale und Spektren. | 02.Signale und Spektren |
| 06 | **06_Plotten** | Matplotlib: Installation, Import; Liniendiagramm/Zeitfunktion, X-Y-Plot, Histogramm, Scatterplot; Bezug Signale/Spektren. | 02.Signale und Spektren |
| 07 | **07_Komplexe_Zahlen** | Komplexe Zahlen in Python; Programmieren vs. C; Zeitdiagramm (Re/Im), komplexe Ebene (XY) mit matplotlib; Bezug Signale/Spektren. | 02.Signale und Spektren |
| 08 | **08_Zufallszahlen** | Gleich-/Normalverteilung; Seed; Rauschen/Zufallsprozesse; Histogramme; Bezug stochastische Signale, 02.Signale und Spektren. | 02.Signale und Spektren |
| 09 | **09_Steuerung** | `if`/`else`/`elif`, `for`, `while`, Einrückung. | — |
| 10 | **10_Tupels** | Tupel-Konzept, unveränderlich; Unterschied zu Listen; C-Äquivalent; Anwendung (mehrere Rückgabewerte, Paare). | Vorbereitung 11_Funktionen |
| 11 | **11_Funktionen** | `def`, Parameter, Rückgabe, Aufruf; mehrere Rückgabewerte (Tupel). | — |
| 12 | **12_Module_und_Bibliotheken** | `import`, z. B. `math`; später `numpy`, `matplotlib` (Grundlagen). | 02.Signale Spektren (Arrays, Plots) |
| 13 | **13_Objektorientierung_Grundlagen** | Klassen-Idee, Attribute, Methoden (kurz). | Nach Bedarf in späteren KT-Themen |
| 14 | **14_Dateien_und_EinAusgabe** | `open`, Lesen/Schreiben von Dateien, Konsole (`input`/`print`). | Optional für Auswertungen, Logs |
| 15 | **15_Besondere_Datentypen** | `None`; `bytes`/`bytearray`; `str.encode()`/`decode()` (Zeichenketten ↔ Bytes); ggf. `set`. | Binärdaten, Codierung (01.Codierung, 08.Leitungscodierung) |
| 16 | **16_Dictionaries** | `dict`, Schlüssel-Wert-Paare; Zugriff, Iteration; typische Anwendungen (Lookup, Zähler, Konfiguration). | Symboltabellen, Codetabellen (01.Codierung, 09.Digitale Modulation) |
| 17 | **17_Spektralanalyse** | FFT mit NumPy (`np.fft`), Sinus + AWGN, Skalierung des Spektrums, Maximum im Spektrum; spektrale Auflösung, Wertebereich. | 02.Signale und Spektren |

## Erste inhaltliche Anknüpfung (Beispiel)

Ab **02_Datentypen** und **03_Variablen_und_Operatoren** kann an das KT-Kapitel **01.Informationstheorie und Codierung → 2. Informationstheorie** angeknüpft werden:

- Einfache Berechnungen: **Signalvorrat** (M^k, Anzahl Zeichen), **Entropie** (Formel mit Logarithmus), **mittlerer Binärstellenaufwand**.
- Dafür reichen: Zahlen, Variablen, einfache Arithmetik, ggf. `math.log2`. Keine Listen oder Grafik nötig.

Die genaue Zuordnung „welches Python-Kapitel ↔ welches KT-Unterkapitel“ kann pro Ordner in der jeweiligen `README.md` oder in einer zentralen Tabelle hier ergänzt werden.

## Grundkurs (00–17) – was gehört dazu?

Der **Python-Grundkurs** deckt ab: Spracheinstieg, Datentypen, Variablen/Operatoren, Listen, Arrays (NumPy), Plotten (Matplotlib), komplexe Zahlen, Zufallszahlen, Steuerung, Tupel, Funktionen, Module/pip/.venv, Objektorientierung, Dateien I/O, besondere Datentypen (None, bytes, encode/decode, set), Dictionaries, Spektralanalyse (FFT). Das reicht für **typische KT-Grundaufgaben**: Informationstheorie (Entropie, Codierung), Signale/Spektren (Arrays, Plots, Rauschen, FFT), einfache Modellierung und Auswertung.

**Nicht** im Grundkurs (Kandidaten für **Fortgeschrittenenkurs**): NumPy/SciPy vertieft (FFT, Filter, lineare Algebra), reguläre Ausdrücke (z. B. für Protokolle/Logs), Unit-Tests, Paketierung (pip installierbare Pakete), asynchrone Programmierung, spezielle KT-Bibliotheken (z. B. SDR, Simulationstoolboxen). Siehe auch `docs/KT_Python_Grundkurs_Fortgeschritten.md` und `kt_lecture_scriptum_index.json` für die Zuordnung zu den Vorlesungskapiteln.

## Fortgeschrittenenkurs – Themenvorschlag

| Thema | Begründung (KT-Bezug) |
|-------|------------------------|
| **NumPy/SciPy vertieft** | FFT (02.Signale Spektren), Filter, LTI-Systeme |
| **Reguläre Ausdrücke** | Protokolle, Logs, Text-/Datenparsing |
| **Unit-Tests / pytest** | Robuste Auswertung und Reproduzierbarkeit |
| **JSON/Config strukturiert** | Konfiguration, Schnittstellen (APIs, Logs) |
| **Paketierung (setuptools, pip)** | Eigene Module wiederverwendbar machen |
| **Optional: SDR/Simulation** | Nach Bedarf für Praktika oder Projektarbeit |

## Hinweis

- Die **Reihenfolge** ist bewusst **python-didaktisch** (von einfach zu komplex), nicht 1:1 an die Vorlesungsnummerierung (01, 02, 03 …) gebunden.
- **KT-Verknüpfung** kann 1:n sein: ein Python-Kapitel kann zu mehreren KT-Themen passen; ein KT-Kapitel kann mehrere Python-Kapitel nutzen.
