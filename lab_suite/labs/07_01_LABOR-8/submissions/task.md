## 8. Laborübung (LABOR-8)

Die **konkreten Formulierungen und der fachliche Kontext** stehen in den jeweiligen Markdown-Zellen der Notebooks (oft direkt über dem zugehörigen Code). Die folgende **Checkliste** fasst alle dort mit **ToDo** gekennzeichneten Aufgaben zusammen — **alphabetisch nach Notebook-Dateiname** sortiert. Zum Arbeiten und zur Abgabe: Punkte abhaken; Ergebnisse, Plots und Texte wie in der Kursvorgabe im Notebook bzw. in `submissions/` dokumentieren.

Die drei ersten Notebooks bauen **ASK und Demodulation** schrittweise auf (Grundlagen, Hüllkurven-Demod, QAM/OOK-Bezug) und enden jeweils mit **reflektierenden ToDos** (Beschreibung der Rechenschritte und Interpretation der Plots). Hier geht es vor allem um **Verständnis und Formulierung**, nicht um SDR-Hardware.

### `1-ASK-basics.ipynb`

- [ ] Beschreibe in eigenen Worten die mathematischen Funktionen der Pythoncode-Zellen.
- [ ] Welche Aussagekraft haben die gezeigten Plots, was kann man daraus ableiten?

### `2-ASK-demod-envelope.ipynb`

- [ ] Beschreibe in eigenen Worten die mathematischen Funktionen dieser Signalverarbeitungs-Kette.
- [ ] Welche Aussagekraft haben die gezeigten Plots, was kann man daraus ableiten?

### `3-QAM-demod.ipynb`

- [ ] Beschreibe in eigenen Worten die mathematischen Funktionen dieser Signalverarbeitungs-Kette.
- [ ] Welche Aussagekraft haben die gezeigten Plots, was kann man daraus ableiten?
- [ ] Wähle für nicht-kohärente OOK-ASK jenes SNR, mit dem eine BER = 1e-4 erzielt wird, und führe mit diesem Setting das Notebook aus.

### `4-ASK-SDR-demod-iq.ipynb`

Hier wird eine **SDR-Aufzeichnung** eines **ASK-modulierten** Signals mit **IQ-Demodulation** (LO, Basisbandfilter, Bitraten-/Augen-/Histogramm-Auswertung) bearbeitet. Die ToDos verlangen **konkrete Parameter** (`f_if_est_hz`, `f_lp`, Bitrate), **mess- bzw. plotbasierte Antworten** (Bitrate, Modulationsgrad, SNR vs. Filter) sowie ein **Blockschaltbild** mit kurzer Erläuterung.

- [ ] Abschätzen der Trägerfrequenz und Konfigurieren der LO-Frequenz `f_if_est_hz`, sodass das Signal in die Nähe von Null Hertz verschoben wird.
- [ ] Eingabe der Filterbandbreite `f_lp` für den Sliding Averager als Basisbandfilter; einen sinnvollen Wert ermitteln (bis max. 40 kHz).
- [ ] **Spektrum des Zero-IF-Basisbandsignals (vor dem Baseband-Filter):** Aus diesem Spektrum die Bitrate ermitteln. *(Hinweis im Notebook: die Bitrate des Testsignals ist ein **Vielfaches von 100 Hz**.)*
- [ ] Geschätzte Bitrate eingeben, damit Augendiagramm und Amplitudenhistogramm für die Bit-Abtastwerte möglich werden. *(Hinweis: nur näherungsweise aus dem Spektrum; im Notebook auf ein **exaktes Vielfaches von 100 Hz** festlegen.)*
- [ ] Blockschaltbild für die gesamte Signalverarbeitungskette (Sender ASK-Modulator, Funkstrecke, SDR, Signalverarbeitung im Notebook) mit kurzer Erklärung der **Funktionsblöcke** und der Aussage der gezeigten Plots.
- [ ] Wie groß ist die Bitrate des ASK-Signals?
- [ ] Wie groß ist der Modulationsgrad des ASK-Signals? Aus welchem gezeigten Plot kann dieser ermittelt werden?
- [ ] Einfluss der Bandbreite des Basisband-Tiefpassfilters auf das erzielte SNR für **vier** verschiedene Grenzfrequenzen bis 40 kHz ermitteln; **tabellarische Übersicht** und Kommentar der Ergebnisse.

### `5-FSK-SDR-demod.ipynb`

Dieses Notebook behandelt **FSK über SDR** (Capture/Replay), **Trägerlage**, **IQ-Downconversion**, **FM-/FSK-Demod**, **FIR-Basisbandfilterung** sowie **Augendiagramm** und **Amplitudenhistogramm** mit einstellbarem **Bit-Start-Offset**. Die ToDos ergänzen die ASK-SDR-Kette um **FSK-spezifische** Auswertungen (Filter-SNR bis 50 kHz, Abtastphase per Slider) und wiederholen die **Dokumentationspflicht** (Signalpfad, Blockdiagramm-Link, Einordnung von Auge/Histogramm und BER).

- [ ] Gegebenenfalls **Center Frequency** und **Gain** für den SDR anpassen (Abschnitt „Parameter und Imports“).
- [ ] **Trägerfrequenz:** Aus dem Spektrum des empfangenen Signals die Trägerfrequenz schätzen, damit das Signal mit dem LO möglichst in die Nähe von Null Hertz verschoben werden kann.
- [ ] **FIR-Tiefpass:** Cutoff-Frequenz im Bereich bis 50 kHz variieren und den Einfluss der Filterbandbreite auf das SNR nach der Demodulation untersuchen; **optimale** Filterbandbreite für das beste erzielbare SNR finden.
- [ ] **Analysen und Dokumentation:** (1) Blockschaltbild vom gesamten Signalpfad (Sender, Funkstrecke, SDR, alle im Notebook implementierten Stufen); pro Block kurze, prägnante Beschreibung der mathematischen Operationen (z. B. FIR-Filter, Frequenzverschiebung, FM-Demodulation, Histogramm, Augendiagramm). (2) Relevanz von Augendiagramm und Amplitudenhistogramm; Bezug zur Bitfehlerrate.
- [ ] **Blockdiagramm-Link:** Blockdiagramm der Signalverarbeitungsstufen von Sender und Funkstrecke bis zum demodulierten Datenstrom **hier einfügen** (Markdown-Syntax z. B. `![erklärender Text](media/bild.jpg)`).
- [ ] **Analyse:** Zusammenhang FIR-Tiefpass-Bandbreite und SNR nach der Demodulation für Cutoffs bis 50 kHz; Ergebnis als **Tabelle oder Plot**; optimale Filterbandbreite für maximales SNR; **optimalen Abtastzeitpunkt** anhand des Amplitudenhistogramms (Slidereinstellung `BIT_START_OFFSET_SAMPLES`).

---

## Hinweise zur Klarheit dieser Liste

- **Gut nutzbar** als Überblick, welche Notebooks welche Arbeitsanteile enthalten, und als Abgabe-Checkliste.
- **Einschränkung:** Einzelne Formulierungen sind knapp (Labor-Notebook-Stil). Begriffe wie `f_if_est_hz`, `f_lp`, SNR- oder Histogramm-Auswertung setzen das Durcharbeiten der jeweiligen Zellen voraus — das ist beabsichtigt, für Studierende ohne Vorlesungs-/Übungskontext aber nicht überall selbsterklärend.
- **Konsistenz:** In `4-ASK-SDR-demod-iq.ipynb` stehen teils kleine Tippfehler (z. B. „Vielfahces“, „Fubktionsblöcke“, doppeltes „-“ vor einem Listeneintrag); in dieser Checkliste sind die Aufgaben sinngemäß bereinigt wiedergegeben — die Originale in den `.ipynb` können bei Gelegenheit separat korrigiert werden.
- **Empfehlung:** In der Abgabe kurz vermerken, in welchem Notebook welche Ergebnisse (Plots, Tabellen, Link zum Blockdiagramm) stehen.
