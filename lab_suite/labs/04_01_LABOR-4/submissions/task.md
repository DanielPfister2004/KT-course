## 1. Laborübung - Kurzübersicht

Die konkreten Arbeitsaufträge sind zusätzlich in den jeweiligen Notebook-Kommentaren markiert.

**Ziel der Übung**  
Verständnis von Amplitudenmodulation (AM), Trägerunterdrückung, Demodulation (Hüllkurve und IQ/Magnitude) sowie SDR-basierter Signalerfassung und -auswertung.

### Überblick über die Notebooks

**`1-AM-Grundlagen.ipynb` (konkrete Implementierungsaufgabe)**  
Einführung in klassische AM: Signalaufbau im Zeitbereich, Spektrum, Modulationsgrad und Peak-Auswertung.  
Arbeitsauftrag laut Kommentar im Code: **AM-Modulator für den Standardfall mit fixem DC-Offset (`DC = 1`) implementieren** (Normierung `u_m_hat`, Hüllkurve `envelope`, modulierter Träger `s_am`).

**`2-AM-suppressed-carrier.ipynb` (konkrete Implementierungsaufgabe)**  
AM mit reduzierbarem/unterdrückbarem Träger über variablen DC-Offset, plus Spektralanalyse mit Peak-Detektion und Träger-Entscheidung.  
Arbeitsauftrag laut Kommentar im Code: **AM-Modulator mit variablem DC-Offset (`DC`) implementieren** (inkl. Fall `DC = 0` zur Trägerunterdrückung; Berechnung von `u_m_hat`, `envelope`, `s_am`).

**`3-AM-envelope-demod.ipynb` (as is / Ausführen und verstehen)**  
Demodulation per Gleichrichtung + Tiefpass (Sliding-Averager), Darstellung im Zeitbereich und Audioausgabe. Ziel: Hüllkurvendemodulation nachvollziehen und interpretieren.

**`4-QAM-demod.ipynb` (as is / Ausführen und vergleichen)**  
IQ-basierte Demodulation mit lokalem Oszillator, I-/Q-Kanälen und Magnitude-Signal. Vergleich zur Hüllkurvendemodulation und Beobachtung der Frequenzverschiebung in den Spektren.

**`5-AM-SDR-demod-envelope.ipynb` (konkrete Implementierungsaufgabe)**  
SDR-Capture/Replay und anschließende Envelope-Demodulation.  
Arbeitsauftrag laut Kommentar im Code: **Envelope-Demodulation (Gleichrichtung + Sliding-Averager) selbst implementieren** und Ausgangssignal `x_demod` berechnen.

**`6-AM-SDR-demod-iq.ipynb` (konkrete Implementierungsaufgabe)**  
SDR-Capture/Replay, IF-/LO-Schätzung aus dem Spektrum und IQ-Demodulation.  
Arbeitsauftrag laut Kommentar im Code: **IQ-Demodulation selbst implementieren** (Mischung mit lokalem Oszillator, Bildung von I/Q und Magnitude-Demodulation, Berechnung von `u_demod`).

### Erwartete Tätigkeiten der Studierenden

- Notebooks in der vorgesehenen Reihenfolge bearbeiten (`1` bis `6`).
- In `1-AM-Grundlagen.ipynb` den AM-Modulator mit fixem DC-Offset implementieren.
- In `2-AM-suppressed-carrier.ipynb` den AM-Modulator mit variablem DC-Offset (inkl. Trägerreduktion/-unterdrückung) implementieren.
- In den beiden SDR-Notebooks (`5` und `6`) die markierten Code-Abschnitte vervollständigen.
- Ergebnisse über Plots und Audioausgabe prüfen (Plausibilität von Träger, Seitenbändern, Demodulationssignal).
- Unterschiede zwischen Hüllkurven- und IQ-Demodulation kurz dokumentieren.