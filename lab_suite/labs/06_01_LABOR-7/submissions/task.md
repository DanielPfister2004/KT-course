# Laborübung 7: FPC1500 NA/SA Messungen und Mixer-Analyse

Diese Aufgabe umfasst die Notebooks `1` bis `6` im Ordner `06_01_LABOR-7`.
Führe Messungen und Auswertungen gemäß den Hinweisen in den Notebooks durch.
An den gekennzeichneten Stellen sind eigene Analysen/Interpretationen als Python-Code
und als kurze fachliche Bewertung zu ergänzen.

### 1) Kalibration für S21-Messungen

Notebook: `1-fpc1500-NA-S21.ipynb`

- Führe die S21-Kalibration durch.
- Verbinde dazu den Generator-Ausgang mit dem RF-Eingang über ein `0.5 m RG58` Koaxkabel.
- Diese Kalibration ist Grundlage für die nachfolgenden NA-Messungen.

### 2) S21-Analyse eines RF-Filters (vorgegebene Messdaten)

Notebook: `2-fpc1500-NA-S21.ipynb`

- Dieses Notebook enthält gespeicherte Messwerte (Vorlage), keine eigene Live-Messung erforderlich.
- Führe die geforderten Auswertungen im markierten Python-Bereich durch.
- Interpretiere die Filtereigenschaften auf Basis der vorgegebenen S21-Daten
  (z. B. Durchlassbereich, Dämpfung, charakteristische Frequenzbereiche).

### 3) S21-Messung eines weiteren RF-Filters (eigene Messung)

Notebook: `3-fpc1500-NA-S21.ipynb`

- Führe eigene S21-Messungen des angegebenen RF-Filters durch.
- Ergänze anschliessend dieselbe Art von Analyse und Interpretation wie in Notebook 2.
- Dokumentiere die wesentlichen Ergebnisse nachvollziehbar.

### 4) S21 eines 30 dB Abschwächers im Full-Span

Notebook: `4-fpc1500-NA-S21.ipynb`

- Ermittle die S21-Parameter eines `30 dB` Abschwächers über Full-Span (bis `3 GHz`).
- Vorher die Full-Span-Kalibration mit Notebook 1 durchführen.
- Die gemessenen Abschwächerdaten werden als `attenuator.json` gespeichert.
- Diese Datei wird im nächsten Notebook weiterverwendet.

### 5) S21 eines RF-Verstärkers mit Korrektur über attenuator.json

Notebook: `5-fpc1500-NA-S21.ipynb`

- Ermittle die S21-Parameter eines RF-Verstärkers (`+5 V` Versorgung beachten).
- Damit der Verstärker nicht in Sättigung gerät, wird der `30 dB` Abschwächer vorgeschaltet.
- Mit `attenuator.json` rechnet das Notebook den Abschwächeranteil heraus und bestimmt
  die Verstärkercharakteristik.
- Führe an den markierten Stellen zusätzliche Analysen und Interpretationen durch.

### 6) Spectrum-Analyzer Messungen und Mixer-Analyse

Notebook: `6-fpc1500-SA-mixer.ipynb`

- Analysiere einen Frequency-Mixer mit drei Messungen:
  1. LO-Signal messen
  2. IF-Signal messen
  3. RF-Ausgangsspektrum messen
- Vorgaben:
  - LO wird durch einen Oszillator bereitgestellt.
  - IF wird mit einem Signalgenerator eingespeist, mit deutlich geringerem Pegel
    und typischerweise `5-10 MHz`.
- Werte anschliessend die Mixer-Parameter aus:
  - LO-Isolation
  - Conversion Loss
- Interpretiere das RF-Ausgangsspektrum fachlich.
- Nutze den Datenblatt-Link des Mixers, ermittle dort relevante Soll-/Referenzwerte
  und vergleiche sie mit den Messresultaten.

### Hinweis zu Referenzdaten (Recordings)

Für alle Notebooks sind Referenzmessungen als `recordings` hinterlegt.
Diese können genutzt werden, um den Ablauf im Labor robuster zu machen
(z. B. bei Verbindungs- oder Messproblemen).
## Checkliste zur Abgabe (zum Abhaken)

#### Notebook 1: Kalibration (`1-fpc1500-NA-S21.ipynb`)

- [ ] 0.5 m RG58 korrekt zwischen Generator-Ausgang und RF-Eingang angeschlossen.
- [ ] S21-Kalibration erfolgreich ausgeführt.
- [ ] Kalibrierung als Basis für die Folge-Notebooks verwendet.

#### Notebook 2: Filteranalyse mit Vorgabedaten (`2-fpc1500-NA-S21.ipynb`)

- [ ] Vorgegebene Messdaten geladen/ausgewertet (keine Live-Messung).
- [ ] Python-Analyse im markierten Bereich implementiert.
- [ ] Fachliche Interpretation dokumentiert (z. B. Durchlassbereich, Dämpfung).

#### Notebook 3: Filtermessung + Analyse (`3-fpc1500-NA-S21.ipynb`)

- [ ] Eigene S21-Messung durchgeführt.
- [ ] Analysecode wie in Notebook 2 ergänzt.
- [ ] Ergebnisse und Interpretation nachvollziehbar dokumentiert.

#### Notebook 4: Abschwächer Full-Span (`4-fpc1500-NA-S21.ipynb`)

- [ ] Full-Span-Kalibration (Notebook 1) vorher ausgeführt.
- [ ] S21-Verlauf des 30 dB Abschwächers bis 3 GHz gemessen.
- [ ] `attenuator.json` erfolgreich erzeugt.

#### Notebook 5: Verstärker mit Korrektur (`5-fpc1500-NA-S21.ipynb`)

- [ ] Verstärker mit +5 V korrekt versorgt.
- [ ] 30 dB Abschwächer vorgeschaltet (Sättigung vermieden).
- [ ] `attenuator.json` eingelesen und Korrektur angewendet.
- [ ] S21 des Verstärkers berechnet und analysiert.
- [ ] Markierte Analyse-/Interpretationsaufgaben ergänzt.

#### Notebook 6: Mixer-Analyse (`6-fpc1500-SA-mixer.ipynb`)

- [ ] Messung 1 (LO), Messung 2 (IF) und Messung 3 (RF-Ausgang) durchgeführt.
- [ ] LO-Isolation aus den Messdaten bestimmt.
- [ ] Conversion Loss aus den Messdaten bestimmt.
- [ ] RF-Ausgangsspektrum fachlich interpretiert.
- [ ] Datenblattwerte recherchiert und mit Messung verglichen.

#### Referenzdaten und Dokumentation

- [ ] Bei Bedarf `recordings` für Replay/Robustheit genutzt.
- [ ] Alle geforderten Code-Ergänzungen gespeichert.
- [ ] Ergebnisse in den Notebooks klar kommentiert.