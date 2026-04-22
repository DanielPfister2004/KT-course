## 5. Laborübung


### Ziel der Übung
- Aufbau und Verständnis einer FM-Sendekette und verschiedener FM-Empfängerstrukturen.
- Praktische Umsetzung zentraler Formeln (Modulation, Downconversion, Demodulation).
- Überprüfung der Ergebnisse über Spektren, Zeitverläufe und mehrsekündige Audioausgabe.

### Aufgaben nach Notebook
- `1-FM-Grundlagen.ipynb`  
  Enthält **TODO-markierte Programmieraufgaben** zur Implementierung grundlegender FM-Formeln und Signalverarbeitungsschritte.

- `2-FM-IQ-modulator.ipynb`  
  Enthält **TODO-markierte Programmieraufgaben** zur Implementierung des FM-IQ-Modulators.  
  Ergebnis ist ein **FM-moduliertes Trägersignal**, das in eine Datei exportiert wird.

- `3-FM-demod.ipynb`  
  Referenz-Notebook für einen FM-Empfänger (Demodulation direkt aus IQ-Signal).  
  Das in Notebook 2 erzeugte Signalfile wird eingelesen und analysiert.

- `4-FM-IQ-demod.ipynb`  
  Referenz-Notebook für eine zweite FM-Empfängerstruktur (IQ-Rekonstruktion aus Realteil + Demodulation).  
  Ebenfalls Einlesen und Analyse des in Notebook 2 exportierten Signalfiles.

- `5-FM-SDR-demod.ipynb`  
  Enthält **TODO-markierte Programmieraufgaben** für die Live-SDR-Verarbeitung:  
  - Einlesen und Aufzeichnen von SDR-Signalen in der Laborübung  
  - Ergänzen der Algorithmen für **komplexen Downconverter** und **FM-Demodulator**  
  - Auswahl sinnvoller **Filterbandbreiten**

### Zusatzaufgabe (Notebook 5)
- Empfange und demoduliere mit dem SDR einen **FM-Radiokanal im UKW-Bereich 88-108 MHz**.
- Mache das empfangene Radiosignal für mehrere Sekunden hörbar.

### Gemeinsame Anforderung für alle Notebooks
- Jedes Notebook soll am Ende eine **mehrsekündige Audioausgabe** erzeugen, um das Ergebnis akustisch zu überprüfen.
- Ziel ist insbesondere, ein FM-Signal (inkl. UKW-Radio in Notebook 5) hörbar und plausibel nachzuweisen.

### Hinweis zum Python-Demo
- `6-SDR-FM-Receiver.py` ist ein **Demonstrationsprogramm** (Matplotlib + Audio) für Live-FM-Empfang.
- In dieser Datei ist **keine gesonderte Programmieraufgabe** zu bearbeiten.

