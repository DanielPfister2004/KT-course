

## Final-Labor (LABOR-9): `1-Final-LAB.ipynb`

## TASK 1:

**Pfad im Repository:** `lab_suite/labs/08_01_LABOR-9/1-Final-LAB.ipynb`

Aufbau eines **RF-Frontends** (433-MHz-ISM-Empfang, zwei Verstärker, Kanalbandfilter, Mischer) mit Verschiebung auf **Zwischenfrequenz**; Messungen mit **FPC1500** als Spektrum-Analyzer und Speicherung der Traces in einer **gemeinsamen Replay-JSON**. Die **konkreten Schritte und SCPI-Hinweise** stehen in den Markdown-Zellen direkt über den jeweiligen Code-Zellen.

### Vorbereitung und Dokumentation

- [ ] **Überblick:** Ziel der Übung und vorgegebene Komponenten im Notebook gelesen; Messreihenfolge beachten (**sieben Messungen** in unmittelbarer Abfolge, Messpunkt/SA-Einstellungen zwischen den Messungen ändern).
- [ ] **FPC1500:** Kurzinfo im Notebook beachten (Mode Spectrum Analyzer, Span/Center, RBW/VBW, Reference Level); Netz **`192.168.1.10`**, SCPI-Port **`5555`**.
- [ ] **Plots im Notebook:** Hinweise zu `ipympl` / `ipywidgets`, Figure-IDs und ggf. `plt.ioff()` beachten (Abschnitt „Darstellung (Plots)“), damit Spektren und Bedienelemente korrekt dargestellt werden.
- [ ] **Foto Messaufbau:** Unter „**HIER einfügen: Foto vom Messaufbau**“ ein eigenes Bild per Markdown einbinden (vgl. Beispielsyntax im Notebook).
- [ ] **Blockschaltbild / Signalplan:** Unter „**HIER einfügen: Foto vom Blockschaltbild**“ einbinden; dazu laut Notebook: **gesamte Schaltung** als Blockbild; **Signalplan** mit **Pegel (dBm)** und **Frequenz** des Nutzsignals an allen Knoten; alle **Verstärkungen und Dämpfungen in dB** (Mischer: **Conversion Gain**, Filter: **Insertion Loss**).

### Messungen (jeweils Messaufbau, SA einstellen, Trace stabil, dann die zugehörige Code-Zelle ausführen)

- [ ] **Verbindung testen:** Zelle mit `*IDN?` ausführen; bei Live-Betrieb Antwort des FPC1500 prüfen.
- [ ] **Messung 1 — Spektrum am Antennen-Eingang:** Antenne direkt an SA; Spectrum Analyzer; Span/Center so, dass das empfangene Signal sichtbar ist; **Span/BW** sinnvoll wählen für möglichst exakte Leistungsmessung; Marker „Set To Peak“ auf Spektrallinie, **Frequenz und Leistung** notieren; Trace stabil → **Code-Zelle ausführen** (Speicher unter `spectrum_ant` laut Notebook).
- [ ] **Messung 2 — Spektrum nach erster Verstärkerstufe:** Messpunkt gemäß Aufbau auf **Knoten nach der ersten Verstärkerstufe** legen; Span/Center anpassen; Trace stabil → Zelle ausführen (Replay-Key im Code: `spectrum_amp1`).
- [ ] **Messung 3 — Spektrum nach zweiter Verstärkerstufe:** Analog Messpunkt nach **zweiter Verstärkerstufe**; Span/Center; Trace stabil → Zelle ausführen (`spectrum_amp2`).
- [ ] **Messung 4 — Spektrum nach Filter, am RF-Eingang des Mischers:** Span so wählen, dass **LO-Leck**, **IF-Mischprodukt** und ggf. **RF-Träger** beobachtbar sind; Trace stabil → Zelle ausführen (`spectrum_mixer_rf`).
- [ ] **Messung 5 — Spektrum am IF-Ausgang des Mischers:** Messung am im Labor vorgegebenen **IF-Ausgang** des Mischers; Span wie in der Zelle beschrieben (LO-Leck, IF-Mischprodukt, ggf. RF-Träger); Trace stabil → Zelle ausführen (`spectrum_mixer_if`).
- [ ] **Messung 6 — IF-Ausgang, Spiegelfrequenz:** Messkonfiguration für **Spiegelfrequenz**-Auswertung gemäß Zelle; Trace stabil → Zelle ausführen (`spectrum_mixer_if-image`).
- [ ] **Messung 7 — IF-Ausgang, Full Span:** **Full Span** am SA; Trace stabil → Zelle ausführen (`spectrum_mixer_if-fullspan`).

### Auswertung (nach allen sieben Messungen)

Nutze die **gespeicherten Spektren** bzw. die Plots im Notebook.

- [ ] **1. Pegel des empfangenen Signals an der Antenne:** **dBm** (z. B. Marker/Peak im gespeicherten Trace bzw. Maximum im relevanten Frequenzbereich).
- [ ] **2. Verstärkungsfaktor der ersten Verstärkerstufe** (aus geeigneten Trace-Vergleichen / Pegeldifferenzen).
- [ ] **3. Verstärkungsfaktor der zweiten Verstärkerstufe.**
- [ ] **4. Einfügungsdämpfung des Filters.**
- [ ] **5. Mixer Conversion Loss:** wie stark erscheint das **IF-Signal als Mischprodukt am RF-Ausgang** — **RF-Pegel** mit **IF-Mischprodukt** im Spektrum vergleichen.
- [ ] **Auswertung im Code:** die Zelle „Auswertung“ nicht bei `pass` belassen — **Peaks/Werte aus der Replay-Datei** einlesen und Pegel/Differenzen **rechnerisch** dokumentieren (Kommentar/Vorlage im Notebook).
- [ ] **Hinweis im Notebook:** erst nach **allen sieben Messungen** sind die Daten für die Punkte 1–5 vollständig.

### Optional

- [ ] **Screenshot vom Gerät:** Hardcopy auf dem FPC, Datei per `MMEM:DATA?` lesen und anzeigen (wie in den anderen SA-Notebooks beschrieben).

---

## Hinweise

- Technische Details (Replay-Keys, exakte Messpunkt-Bezeichnung am Aufbau) stehen in **`1-Final-LAB.ipynb`** — bei Abweichung zwischen Überschrift und Fließtext in einzelnen Messzellen gelten **tatsächlicher Messaufbau** und **Code-Kommentare** (gespeicherte Schlüsselnamen).
- Kurze Laborformulierungen setzen Kontext aus Vorlesung/Übung voraus.
- In der Abgabe kurz vermerken, welche Artefakte wo liegen (Replay-JSON, Screenshots, befüllte Auswertezellen, Links zu Fotos/Blockschaltbildern).

## Final-Labor (LABOR-9): `2-Final-LAB.ipynb`

## TASK 2:

- Verwende ein geeignetes Notebook aus einer früheren Laborübung, um die Parameter S11 und S21 des 433MHz SAW Filters zu bestimmen. - Das Notebook soll im submission-folder dieser Übung abgelegt werden.

