# Use Cases und Software-Architektur (lab_suite)

Ziel: Für verschiedene Anwendungsfälle eine **passende Software-Architektur (Design-Pattern)** festlegen, sodass die Codestruktur auch bei wachsendem Ökosystem (Sound Input/Output, interne Signalquellen, Analyseverfahren in dsp.py) **einfach und klar** bleibt.

---

## Ausgangslage und Leitfrage

- **Bestehendes Ökosystem:** Audio-Input/Output (audio_io), interne Quellen (z. B. Test-Generator), Analyse (dsp.py), GUI (app.py mit NiceGUI), Konfiguration (config.py).
- **Leitfrage:** Ist es sauber, wenn in **app.py** neben NiceGUI-Funktionen auch **User-Logik** steckt – vor allem in **update_ui()** (z. B. Ring lesen → FFT → Plot aktualisieren)?

**Kurzantwort:** Für **einfache Demos** (z. B. Live-Spektrum) ist etwas Logik in `update_ui()` vertretbar. Sobald **Messabläufe**, **mehrere Use-Cases** und **synchronisierte Playback/Record-Pipeline** dazukommen, wird eine **trennscharfe Schicht für Mess-/Analyse-Logik** empfohlen; **app.py** bleibt dann im Wesentlichen **View + dünner Controller** (Events rufen Services auf, keine Fachlogik in update_ui).

---

## Use-Case 1: Messung der komplexen Übertragungsfunktion (Lautsprecher → Mikrofon)

### Beschreibung

- **Ziel:** Die **komplexe Übertragungsfunktion** \( H(f) = Y(f) / X(f) \) zwischen Lautsprecher-Output und Mikrofon-Input messtechnisch ermitteln (z. B. für Raumakustik, Lautsprecher- oder Systemantwort).
- **Ablauf (konzeptionell):**
  1. **Stimulus** \( x(t) \) erzeugen (intern, z. B. Sweep, Chirp, MLS, Sinus-Burst) – analog zum bestehenden Test-Generator, aber messorientiert.
  2. **Ausgabe** \( x(t) \) auf den **Lautsprecher** (Output-Device) spielen.
  3. **Aufnahme** \( y(t) \) vom **Mikrofon** (Input-Device) – **synchron** zur Ausgabe (gleicher Zeitbezug, bekannte Latenz oder Trigger).
  4. **Auswertung:** Aus \( x(t) \), \( y(t) \) die **komplexe Übertragungsfunktion** \( H(f) \) schätzen (z. B. Kreuzspektrum / Autospektrum, oder FFT von y und x, dann \( H = Y/X \)); optional Kohärenz, Impulsantwort via IFFT.
- **Bausteine:** Interne Signalquelle (Stimulus), audio_io (Output + Input, ggf. synchrone Puffer), dsp.py (Übertragungsfunktion, Fensterung, Mittelung).

### Anforderungen an die Architektur

- **Synchronisation:** Playback und Aufnahme müssen zeitlich zugeordnet sein (gleicher Zeitstempel oder feste Latenz/Trigger).
- **Trennung:** Stimulus-Generierung, Abspielen, Aufnehmen und die **Berechnung von H(f)** sind **Fachlogik** und sollen **nicht** in app.py (und nicht in update_ui()) stehen.
- **Wiederverwendung:** Dieselben Bausteine (audio_io, dsp, Stimulus-Generator) sollen für weitere Use-Cases (z. B. nur Spektrum, nur Aufnahme, Kalibrierung) nutzbar bleiben.

### Vorgeschlagenes Design-Pattern: **View + Controller + Measurement-Service**

| Schicht | Verantwortung | Enthalten in |
|--------|----------------|--------------|
| **View** | GUI aufbauen (build_ui), Widgets, Layout, **Anzeige** von State und Ergebnissen | app.py (NiceGUI) |
| **Controller** | User-Events in Aktionen übersetzen: „Messung starten“, „Parameter übernehmen“; ruft **nur** Services auf, keine Mess-/DSP-Logik | app.py (Event-Handler) oder kleines controller.py |
| **Measurement-Service** | **Ablauf** der Messung: Stimulus wählen/erzeugen, Playback starten, Aufnahme puffern, Stopp, Auswertung (H(f) in dsp aufrufen), Ergebnis in **Mess-State** schreiben | Neues Modul z. B. `measurement.py` oder `transfer_function.py` |
| **State** | **Model** (Parameter, Geräte, UI-Preferences) + **Mess-Ergebnis** (z. B. `result_H_freq`, `result_H_mag`, `result_H_phase`, Status „laufend/fertig/Fehler“) | Model (bestehend) + z. B. `measurement_state` (vom Service befüllt) |
| **Audio** | Ein-/Ausgabe, Puffer, Geräte – unverändert wiederverwendet | audio_io.py |
| **DSP** | Reine Analyse: Spektrum, **Übertragungsfunktion** H(f), Kohärenz, Impulsantwort – nur Funktionen, keine GUI | dsp.py (erweitert) |
| **Signalquelle** | Stimulus für Messung (Sweep, Chirp, …) – analog Test-Generator, aber messspezifisch | Erweiterung test_generator.py oder neues stimulus.py |

### Konkret für Use-Case 1

- **app.py:**
  - **build_ui:** Enthält nur Aufbau der GUI und **Anzeige** (z. B. Dropdown „Stimulus“, Button „Messung starten“, Plot für |H(f)| und Phase).
  - **Event-Handler:** z. B. „Messung starten“ → `measurement.start_transfer_function_measurement(model)` (oder ähnlich). Keine Berechnung von H(f) in app.py.
  - **update_ui():** Liest **nur** aus einem **Mess-State** (z. B. `measurement_state.last_H_freq`, `last_H_mag`, `last_H_phase`, `status`) und aktualisiert Plots/Labels. **Keine** Ring-Puffer-Logik, keine FFT, keine H(f)-Berechnung in update_ui – das übernimmt der Measurement-Service (ggf. in einem Timer-Tick oder nach Abschluss der Messung).
- **measurement.py (bzw. transfer_function.py):**
  - Steuert den Ablauf: Stimulus erzeugen → an audio_io zum Playback geben; gleichzeitig Aufnahme starten; nach Ende Stimulus/ Aufnahme Stopp; Puffer auslesen; **dsp.transfer_function_estimate(x, y, ...)** aufrufen; Ergebnis in `measurement_state` schreiben.
  - Nutzt **audio_io** (start_playback, start_input, Ringpuffer/Record-Puffer) und **dsp** (neue Funktion z. B. `estimate_transfer_function`).
- **dsp.py:**
  - Erweiterung um z. B. `estimate_transfer_function(x, y, sample_rate, window)` → Rückgabe freq, H_mag, H_phase (oder komplexes H). Keine GUI-Referenzen.

### Ist es sauber, User-Logik in update_ui() zu haben?

- **Aktuell (FFT Scope):** In update_ui() steht: Ring lesen → Block L/R/L+R bilden → FFT → dB → Plot. Das ist **bereits Fachlogik** (DSP-Pipeline), nur in kleinen Dosen und für einen einzigen Modus.
- **Bewertung:**
  - **Einfache, einzelne Demo:** Vertretbar, wenn es bei „einmal pro Tick: Puffer lesen, eine Analyse, ein Plot“ bleibt.
  - **Mehrere Use-Cases (Live-Spektrum + Übertragungsfunktion + …):** update_ui() würde sonst mit vielen if/else oder Modus-Flaggen wuchern. **Sauberer:** update_ui() macht **nur** „State/Ergebnis lesen → Widgets/Plots aktualisieren“. **Wer** den State befüllt, liegt in einer **Service-Schicht** (z. B. measurement.py), die je nach Modus die passende Analyse anstößt und Ergebnisse in einen gemeinsamen **Result-State** schreibt.

### Empfehlung für das Ökosystem

- **Einheitliches Muster:**  
  - **app.py** = View + dünner Controller (Events → Aufruf von Services).  
  - **update_ui()** = nur **Anzeige**: liest aus **Model** + **Mess-/Analyse-Result-State**, schreibt in Widgets/Plots.  
  - **Fachlogik** (Messablauf, Stimulus, H(f)-Berechnung, Mittelung, …) in **eigenen Modulen** (measurement.py, dsp.py, stimulus/test_generator).

- So bleibt die Codestruktur auch bei weiteren Use-Cases (z. B. Kalibrierung, nur Aufnahme, Rauschanalyse) einfach: Neue Use-Cases = neuer oder erweiterter **Service** + ggf. neue Einträge im Result-State; app.py bleibt schlank und nur anbindend.

---

## Use-Case 2: TOA- und TDOA-Ranging (Laufzeit / Laufzeitdifferenz, Positionsbestimmung)

### Beschreibung

**Ziel:** Über **Laufzeiten (TOA)** bzw. **Laufzeitdifferenzen (TDOA)** akustisch die **Position** von Lautsprechern oder Mikrofon relativ zueinander bestimmen – typische Laborübung für Ortung und Kommunikationstechnik.

**Fall 1 – Lautsprecherposition aus Mikrofonperspektive:**  
- **1 oder 2 Lautsprecher** (L, R) geben ein **periodisches** akustisches Signal aus (z. B. **Chirp**, **AWGN** oder **PRBS**).  
- **2 Mikrofonkanäle** (L, R) messen die ankommenden Signale.  
- Auswertung: **zyklische Kreuzkorrelation** (cyclic correlation) zwischen gesendetem Referenzsignal und den empfangenen Kanälen → Laufzeiten von Lautsprecher zu Mikrofon L bzw. R bzw. **Laufzeitdifferenz (TDOA)** zwischen beiden Mikrofonen.  
- Daraus: **Lautsprecherposition** relativ zu den Mikrofonen (Richtung/Abstand über TDOA/TOA).

**Fall 2 – Mikrofonposition aus Lautsprecherperspektive:**  
- **2 verschiedene Signale** (z. B. **AWGN**, **PRBS**) werden mit **beiden Lautsprechern** (L, R) gleichzeitig oder nacheinander ausgesendet.  
- **1 Mikrofon** empfängt das Überlagerte bzw. die beiden Anteile.  
- Auswertung: **Korrelationsfunktionen** zwischen Referenzsignalen und Empfangssignal → Laufzeiten zu L- und R-Lautsprecher, daraus **Mikrofonposition** relativ zu den Lautsprechern.

### Anforderungen an die Architektur

- **Gemeinsame Signale:** Chirp, AWGN, PRBS müssen **reproduzierbar** und **synchron** zu Playback/Record sein (Referenz für Korrelation).  
- **Stereo In/Out:** 2 Kanäle Input (Mikrofone), 2 Kanäle Output (Lautsprecher) – bereits im Ökosystem (audio_io).  
- **DSP:** **Zyklische Kreuzkorrelation**, Laufzeit-Peak-Erkennung, optional Umrechnung TDOA/TOA → Position (Geometrie) – reine Funktionen, keine GUI.  
- **Stimulus:** Erweiterung der Signalquellen um Chirp, PRBS (evtl. in stimulus.py / test_generator.py).

### Zuordnung zu den Schichten

| Baustein | Schicht / Modul |
|----------|------------------|
| Erzeugung Chirp / PRBS / AWGN (Referenz) | stimulus.py oder test_generator.py |
| Playback L/R, Aufnahme L/R oder Mono | audio_io.py |
| Zyklische Korrelation, TOA/TDOA-Peak, Position | **dsp.py** (neue Funktionen) |
| Ablauf: Senden → Aufnehmen → Korrelation → Ergebnis | measurement.py oder **dsp.py** (wenn Ablauf simpel) |
| Anzeige Laufzeiten, TDOA, Position, Korrelationsplot | app.py (View), update_ui liest Result-State |

---

## Use-Case 3: Modulationsverfahren

### Beschreibung

**Ziel:** **Modulationsverfahren** (z. B. AM, FM, BPSK, QPSK) mit echtem Audiosignal demonstrieren: Träger erzeugen → modulieren → über Lautsprecher ausgeben → mit Mikrofon empfangen → demodulieren und anzeigen.

- **Träger:** Reell (z. B. \( \cos(\omega t) \)) oder **komplex** (Trägerpaar \( \cos(\omega t) \), \( \sin(\omega t) \) für I/Q).  
- **Modulation:** Verschiedene Verfahren (Amplituden-, Frequenz-, Phasenmodulation, digitale Modulationsarten) auf den Träger anwenden; Ausgangssignal bandbegrenzt (z. B. im Hörbereich).  
- **Kanal:** Lautsprecher → Raum/Luft → Mikrofon (realer Kanal, ggf. mit Übertragungsfunktion aus Use-Case 1).  
- **Empfang:** Aufnahme mit Mikrofon, **Demodulation** (kohärent/nichtkohärent je nach Verfahren), Anzeige von Symbolen/Bits oder moduliertem vs. demoduliertem Signal.

### Anforderungen an die Architektur

- **Träger- und Modulationslogik:** Erzeugung von Träger (reell/komplex), Modulator (AM, FM, BPSK, …), Bandbegrenzung – **reine Funktionen**, keine GUI.  
- **Demodulation:** Aus Empfangssignal Symbolfolge oder Nutzsignal zurückgewinnen – **reine Funktionen** in dsp.py (oder einem Modulations-Modul).  
- **Audio:** Playback (moduliertes Signal), Aufnahme (empfangen) – audio_io, wie in Use-Case 1/2.  
- **Optional:** Nutzung von H(f) aus Use-Case 1 zur Kanalentzerrung vor Demodulation.

### Zuordnung zu den Schichten

| Baustein | Schicht / Modul |
|----------|------------------|
| Träger erzeugen (cos, sin, I/Q) | stimulus.py oder **dsp.py** (modulation.py) |
| Modulatoren (AM, FM, BPSK, QPSK, …) | **dsp.py** (oder user_code / modulation.py) |
| Demodulatoren | **dsp.py** (oder user_code) |
| Playback / Record | audio_io.py |
| Ablauf: Modulieren → Abspielen → Aufnehmen → Demodulieren | measurement.py oder **dsp.py** (ein Modul „User-Code“) |
| Anzeige (Träger, moduliert, empfangen, demoduliert, Konstellation) | app.py (View), update_ui liest Result-State |

---

## Optimale Software-Architektur aus allen Use-Cases

Aus dem **bestehenden Demo-Use-Case** (FFT Scope: Live-Spektrum, Test-Generator, L/R/L+R) und den **drei beschriebenen Use-Cases** (Übertragungsfunktion, TOA/TDOA-Ranging, Modulationsverfahren) wird eine **einheitliche Architektur** abgeleitet, mit der alle typischen Laborübungen für **Kommunikationstechnik** im **gleichen Ökosystem** laufen und Studierende ihren **User-Code möglichst in einem einzigen Modul** (vorzugsweise **dsp.py** bzw. ein davon abgeleitetes „User-Code“-Modul) implementieren können.

### Überblick Use-Cases und gemeinsame Bausteine

| Use-Case | Kurz | Signalquelle | Audio | Analyse / User-Logik |
|----------|------|--------------|-------|----------------------|
| **Demo (FFT Scope)** | Live-Spektrum, L/R/L+R | Test-Gen (Sinus+AWGN) | In/Out stereo, Ring, Playback | FFT, dB, Peak (dsp.py) |
| **UC1** | Übertragungsfunktion H(f) | Stimulus (Sweep, Chirp, …) | Playback + Record synchron | H(f)=Y/X, Kohärenz, IR (dsp.py) |
| **UC2** | TOA/TDOA, Position | Chirp, AWGN, PRBS (L/R) | Stereo Out + Stereo/Mono In | Zykl. Korrelation, TOA/TDOA, Position (dsp.py) |
| **UC3** | Modulationsverfahren | Träger + Modulator | Playback + Record | Demodulation, ggf. H(f) (dsp.py) |

Gemeinsam sind: **audio_io** (Input/Output, Puffer, Geräte), **Signalquellen** (Test-Gen, Stimulus, Träger/Modulator), **Konfiguration** (config.py), **GUI** (app.py). Der fachliche Kern – Analyse, Schätzung, Modulations-/Korrelationslogik – soll **an einem Ort** liegen.

### Empfohlene Schichten (einheitlich für alle Use-Cases)

1. **View + dünner Controller (app.py)**  
   - Nur: GUI bauen, Events auf **Service-/User-Code-Aufrufe** mappen, **update_ui()** liest ausschließlich aus **Model** und **Result-State** und aktualisiert Widgets/Plots.  
   - **Keine** FFT, Korrelation, H(f), Modulation/Demodulation in app.py.

2. **Audio & Signale (audio_io, stimulus / test_generator)**  
   - Unverändert wiederverwendet: Stereo In/Out, Ringpuffer, Playback-Queues, Start/Stop Input/Output/Test-Gen.  
   - Erweiterung um weitere Stimuli (Chirp, PRBS, Träger) in **stimulus.py** oder **test_generator.py**, ohne GUI.

3. **User-Code / Analyse in einem Modul (vorzugsweise dsp.py)**  
   - **Alle** analyse- und messspezifischen Funktionen an **einer** Stelle, damit Studierende **ihren eigenen User-Code** (neue Verfahren, neue Schätzungen) **in einem einzigen Modul** ergänzen können:  
     - FFT, Spektrum, dB (bereits vorhanden)  
     - Übertragungsfunktion H(f), Kohärenz, Impulsantwort (UC1)  
     - Zyklische Kreuzkorrelation, TOA/TDOA, Positionsschätzung (UC2)  
     - Modulatoren/Demodulatoren, Träger (UC3)  
   - **Keine** GUI-Imports, **keine** audio_io-Aufrufe in dsp.py – nur reine Funktionen: Eingang = Arrays/Parameter, Ausgang = Ergebnis-Arrays/Strukturen.  
   - Optional: Wenn dsp.py zu groß wird, Aufteilung in **dsp.py** (Basis: FFT, Fenster, H(f), Korrelation) und **user_code.py** (Studierenden-Code, ruft ggf. dsp auf); aus Sicht der Architektur zählt beides als **„ein Modul User-Code“**.

4. **Mess-/Ablauf-Steuerung (measurement.py oder integriert)**  
   - **Ablauf** „Stimulus wählen → Playback starten → Aufnahme starten → Puffer füllen → Stopp → Auswertung aufrufen → Result-State füllen“ lebt in einem **Service** (z. B. measurement.py), der **audio_io** und **dsp** (bzw. user_code) aufruft.  
   - Für **sehr einfache** Demos (nur Live-Spektrum wie heute) kann dieser Ablauf weiterhin schlank in app.py oder einem kleinen „live_analysis“-Callback bleiben; sobald mehrere Modi (UC1, UC2, UC3) angeboten werden, zentral in measurement.py (oder einem Modul pro Use-Case, das seinerseits nur dsp/audio_io nutzt).

5. **State (Model + Result-State)**  
   - **Model:** Parameter (Geräte, FFT-Größe, Kanal L/R/L+R, Stimulus-Typ, Modulationsart, …), von GUI geschrieben, von Services gelesen.  
   - **Result-State:** Von Measurement-Service / User-Code befüllt: z. B. `last_spectrum`, `last_H_freq`, `last_TOA_TDOA`, `last_demodulated`, Status „idle/running/done“.  
   - **update_ui()** liest **nur** Model + Result-State und zeichnet.

### Wo implementieren Studierende ihren User-Code?

- **Primär: dsp.py** (oder ein davon abgeleitetes **user_code.py**, das dsp importiert).  
- Dort: **neue Funktionen** für weitere Analyseverfahren, weitere Modulationsarten, eigene Schätzungen (z. B. andere Korrelationsvarianten, eigene Positionsberechnung).  
- **Nicht** in app.py (nur View/Controller), **nicht** in audio_io (nur I/O).  
- So bleiben alle Laborübungen (Übertragungsfunktion, TOA/TDOA, Modulation, Live-Spektrum) im **identischen Ökosystem** nutzbar, und die Codestruktur bleibt einfach und klar – mit **einem** zentralen Modul für fachlichen User-Code (dsp.py bzw. user_code.py).

### Template-Projekt: use_case_template

Das Projekt **labs/use_case_template** enthält die gleiche Funktionalität wie die FFT-Scope-Demo und dient als **Basis zum Ableiten neuer Use-Cases**:

- **Neue Use-Cases ableiten:** Ordner kopieren (z. B. nach `labs/transfer_function/`), Paketnamen anpassen, an den markierten **Einfügestellen** (siehe unten) UC-spezifischen Code ergänzen.
- **Ökosystem verfeinern:** Änderungen an audio_io, Config oder Architektur zuerst im Template erproben. Bewährte **Tweaks** in die produktiven Apps (z. B. **fft_scope**) nachziehen.
- **Einfügestellen** sind im Code mit `[Einfügestelle …]` kommentiert; Details im Abschnitt „Einfügestellen für Use-Case-spezifische Erweiterungen“ und in **labs/use_case_template/README.md**.

### Einfügestellen für Use-Case-spezifische Erweiterungen (GUI, State)

Damit Studierende **Control-Widgets** als Parameter für Analysen nachträglich einfügen und **Ergebnisse** an die GUI ausgeben können, ohne die Architektur zu verletzen, sind die folgenden Stellen in den Modulen des Ökosystems als **offizielle Einfügestellen** gekennzeichnet. Das ist **kompatibel** mit dem beschriebenen Design-Pattern: View und State haben klare Schnittstellen; Erweiterungen erfolgen nur an diesen Stellen.

#### app.py (View + Controller)

| Stelle | Zweck | Was einfügen |
|--------|--------|----------------|
| **build_ui() – Bereich „Steuerung/Parameter“** | Use-Case-spezifische **Eingabe-Widgets** (Slider, Select, Input, Checkbox) | Neue Widgets für Analyse-Parameter (z. B. Korrelationsfenster, Modulationsart, Sweep-Dauer). Im **on_change** nur: Wert in **Model** schreiben, ggf. `config.save_widget_settings_from_model(model)`; optional Service aufrufen (z. B. „Messung neu starten“). **Keine** Analyse- oder DSP-Logik. |
| **build_ui() – Bereich „Ergebnis/Anzeige“** | Use-Case-spezifische **Ausgabe-Widgets** (Label, Plot, Tabelle) | Neue Plots/Labels für Ergebnisse (z. B. Korrelationskurve, Konstellation, TOA/TDOA-Anzeige). Widget-Referenzen in einer Liste oder einem Dict halten, damit **update_ui()** sie befüllen kann. |
| **update_ui() – Lesebereich** | Werte für die Anzeige beziehen | **Nur lesen** aus **Model** (Parameter) und **Result-State** (Ergebnisse). Keine Berechnungen, keine audio_io-/dsp-Aufrufe. |
| **update_ui() – Schreibbereich** | Gelesene Werte in Widgets schreiben | Zuweisungen wie `plot.data[0].y = result_state.last_curve`, `label.text = result_state.status`. Pro Use-Case ein eigener Block oder eine Hilfsfunktion (z. B. `_update_spectrum_ui()`, `_update_transfer_function_ui()`) ist zulässig – Inhalt bleibt „State → Widget“. |
| **Event-Handler (on_click, on_change)** | Aktion auslösen | Nur: Model aktualisieren, **measurement.*** oder **dsp.*** aufrufen (wenn Aufruf von außen gewünscht), Config speichern. **Keine** Analyse im Handler. |

**Konkret im Code (FFT Scope als Vorlage):** Neue Parameter-Widgets in derselben `ui.row()`- bzw. Steuerungs-Sektion wie FFT size, Window, Kanal; neue Ergebnis-Plots/Labels unterhalb oder in einer eigenen Sektion „Ergebnis [Use-Case X]“. In **update_ui()** nach dem Block „if running:“ einen weiteren Block „if model.mode == 'transfer_function': …“ bzw. die neuen Result-State-Felder lesen und in die neuen Widgets schreiben.

#### Model (State – Parameter)

| Stelle | Zweck | Was einfügen |
|--------|--------|----------------|
| **Model-Dataclass (app.py oder eigenes model.py)** | Alle von der GUI gesetzten **Parameter** für Analysen und Messung | Neue Attribute, z. B. `sweep_duration: float = 1.0`, `correlation_window: int = 4096`, `modulation_type: str = "AM"`. **Keine** Ergebnis-Daten (die gehören in Result-State). |
| **config._SETTINGS_KEYS** (config.py) | Persistenz der Parameter | Neue Parameter-Namen hier aufnehmen, damit sie in settings.json gespeichert/geladen werden (falls gewünscht). |

#### Result-State (State – Ergebnisse)

| Stelle | Zweck | Was einfügen |
|--------|--------|----------------|
| **Gemeinsamer Result-State** (z. B. Dict oder Dataclass, von measurement.py / dsp-Callbacks befüllt) | Alle **Ausgabe-Daten** für die GUI (Ergebnisse der Analyse, Status) | Neue Felder, z. B. `last_correlation_tau`, `last_TOA_L`, `last_TOA_R`, `last_demodulated_symbols`, `last_constellation_I`, `last_constellation_Q`, `status: str`. **Befüllt von:** measurement.py oder dem Modul, das dsp aufruft. **Gelesen von:** ausschließlich update_ui() in app.py. |

**Empfehlung:** Result-State als **einen** zentralen Container definieren (z. B. `measurement_state` oder `result_state`), in dem alle Use-Cases ihre Ergebnis-Felder ablegen. So bleibt die Regel „update_ui() liest nur diesen einen State“ einfach einzuhalten.

#### dsp.py / user_code.py (Analyse)

| Stelle | Zweck | Was einfügen |
|--------|--------|----------------|
| **Neue Funktionen** | Analyse- und Verfahrenslogik | Funktionen mit Signatur **Eingang: Arrays + Skalare (Parameter)** und **Ausgang: Arrays/Structs (Ergebnis)**. Parameter können später aus dem **Model** vom Aufrufer (measurement.py oder app-Callback) übergeben werden – dsp.py kennt das Model nicht, erhält nur die konkreten Werte. |
| **Keine Einfügestelle** | – | **Keine** GUI-Widgets, **keine** Imports von app oder ui, **keine** Schreibzugriffe auf Result-State direkt aus dsp (Result-State wird vom **Aufrufer** befüllt, der die Rückgabe von dsp in den State schreibt). |

#### measurement.py (Ablauf-Steuerung)

| Stelle | Zweck | Was einfügen |
|--------|--------|----------------|
| **Nach Aufruf von dsp.*** | Ergebnisse in den Result-State schreiben | Rückgabe von dsp (z. B. `freq, H_mag, H_phase`) in **result_state** schreiben (z. B. `result_state.last_H_freq = freq`). So bleibt „eine Stelle, an der Ergebnisse für die GUI landen“. |
| **Vor Aufruf von dsp.*** | Parameter aus Model holen | Werte aus **model** lesen (z. B. `window = model.window`, `n_fft = model.fft_size`) und an dsp-Funktionen übergeben. Hier ist die Brücke „GUI-Parameter (Model) → Analyse (dsp)“. |

---

**Kompatibilität mit dem Design-Pattern:** Ja. Das Pattern verlangt: (1) **View** darf nur anzeigen und Benutzereingaben in Model/Service-Aufrufe übersetzen; (2) **State** (Model + Result-State) ist die einzige Datenverbindung zwischen View und Logik. Die genannten **Einfügestellen** sind genau die erlaubten Erweiterungspunkte: neue Widgets und Lese-/Schreibzugriffe nur an diesen Stellen halten die Trennung ein. Neue Parameter → nur Model + ggf. Config; neue Ergebnisse → nur Result-State + update_ui()-Lese-/Schreibblock. So bleiben die Rollen von app.py, Model, Result-State, dsp und measurement.py klar definiert.

---

## Audio-Datenfluss (audio_io): Faktencheck und Zielarchitektur

### Faktencheck: Wird das Signal vor der Ausgabe durch User-Logik (z. B. Filter) geführt?

**Antwort: Nein.** In der **bisherigen** Architektur:

| Quelle | Wo landet das Signal? | Ausgabe (Lautsprecher) |
|--------|------------------------|------------------------|
| **Mikrofon** | Rings (für Spektrum) **und** Playback-Queues | Output-Callback liest aus Playback-Queues → **rohes Mic**, keine Verarbeitung dazwischen. |
| **Test-Generator (Lautsprecher an)** | Rings (für Spektrum) **und** direkt `outdata` im Callback | Test-Signal wird **direkt** in den Output-Callback geschrieben → **an der User-Logik vorbei**, kein Filter o. Ä. möglich. |
| **Test-Generator (Lautsprecher aus)** | Rings **und** Playback-Queues | Output liest aus Queues → **rohes Test-Signal**, keine Verarbeitung. |

**Fazit:** Weder Mic noch Test-Generator laufen durch eine zentrale Verarbeitungsstelle vor der Ausgabe. Beim Test-Generator mit „Lautsprecher an“ wird das Signal sogar **vollständig an den Rings/Queues vorbei** direkt an die Soundkarte ausgegeben. **Filterung oder andere User-Verarbeitung vor Ausgabe ist mit dem bisherigen Datenfluss nicht möglich.**

### Zielarchitektur: Eine Quelle → Rings → eine Ausgabe (mit optionaler Verarbeitung)

Damit **alle** Quellen (Mic, Test-Generator, **WAV-Replay**) gleich behandelt werden und vor der Ausgabe bearbeitet werden können (Filter, Verstärkung, …):

1. **Alle Quellen** schreiben in die **Rings** (für Spektrum/User-Logik). **Mic und WAV** schreiben zusätzlich in **Playback-FIFOs** (`_playback_queue_left/right`).
2. **Ausgabe** läuft im **Soundkarten-Takt**. **Test-Generator (output-driven):** Chunk im Callback erzeugen → Rings → Ausgabe aus Rings (`read_latest`) – ein Takt, daher kontinuierlich. **Mic/WAV:** Producer laufen in eigenem Takt; sie füllen die **FIFO**, der Output-Callback liest aus der FIFO (gleicht Taktdifferenz aus, kein Abhacken).
3. **WAV-Replay:** Thread schreibt in Rings **und** in die Playback-FIFOs (wie Mic).

So sind Spektrum und Ausgabe dieselben Daten; Mic und WAV laufen taktsynchron über die FIFO; Test-Generator bleibt im Callback und liefert kontinuierliches Signal.

**Output-Processor nutzen (z. B. Filter):** In `audio_io` ist `set_output_processor(fn)` verfügbar. Signatur: `(left, right) -> (left_out, right_out)` (float32-Arrays, gleiche Länge). Wird im Output-Callback nach `read_latest` und vor dem Schreiben in `outdata` aufgerufen. Beispiel: `audio_io.set_output_processor(lambda L, R: (my_filter(L), my_filter(R)))`.

### Test-Pattern (WAV) und Referenz-Rings für UC1/2/3

- **Replay abgehackt:** WAV über FIFO/Thread läuft in anderem Takt als die Ausgabe → Drift. **Workaround:** WAV einlesen, puffern und **als Test-Pattern** im Output-Callback abspielen (wie der Test-Generator) → ein Takt, kontinuierlich.
- **Test-Pattern:** `load_test_pattern_from_wav(path, ...)` lädt eine WAV in einen Puffer; der Output-Callback liest chunkweise daraus. **Mic wird nicht gestoppt** → Sent (Lautsprecher) und Received (Mikrofon) laufen gleichzeitig.
- **Referenz-Rings („gesendetes Signal“):** Der Output-Callback schreibt alles, was er ausgibt, in `_reference_ring_left/right`. So hat die User-Logik Zugriff auf das **gesendete** Signal (Test-Gen oder Test-Pattern). **Nichts geht an der User-Logik vorbei.**
- **UC1 (Transfer-Funktion):** Bekanntes Signal (Test-Pattern oder Test-Gen) wird ausgegeben; Referenz-Rings = x(t). Mic = y(t). Korrelation / H(f) in dsp aus Referenz + `get_ring_left()` (Received).
- **UC2 (TOA/TDOA):** Gesendetes Signal in Referenz-Rings, Empfangen in Rings (Mic). Korrelation für Laufzeit/Laufzeitdifferenz.
- **UC3 (Modulation):** Senden und Empfangen; Demodulation aus Mic; Vergleich mit gesendeten Daten aus Referenz-Rings.

**API:** `get_reference_ring_left()`, `get_reference_ring_right()` = gesendetes Signal; `get_ring_left()`, `get_ring_right()` = empfangenes Signal (Mic), wenn Run mit Mic aktiv.

---

## Zusammenfassung

| Aspekt | Empfehlung |
|--------|------------|
| User-Logik in update_ui() | Nur vertretbar für sehr einfache, einzelne Demos. Für UC1–UC3 und mehrere Modi: **raus** aus update_ui. |
| update_ui() | Soll nur **State/Ergebnis lesen** und **Anzeige aktualisieren**. Keine DSP-, keine Messablauf-Logik. |
| Mess-/Analyse-Ablauf | In **eigener Schicht** (measurement.py), nutzt audio_io + dsp; bei einfachem Demo weiterhin schlank in einem Callback möglich. |
| app.py | View + dünner Controller: build_ui, Event-Handler rufen Services auf; keine Fachlogik. |
| dsp.py (bzw. user_code.py) | **Zentrales Modul für User-Code:** Reine Analyse- und Verfahrenslogik (FFT, H(f), Korrelation, TOA/TDOA, Modulation/Demodulation); keine GUI, keine audio_io. Studierende erweitern **hier** ihren Code. |
| Ökosystem | audio_io, Stimulus-Generatoren, dsp/user_code, config gemeinsam für Demo + UC1 + UC2 + UC3; neue Laborübungen = neue Funktionen in dsp/user_code + ggf. measurement.py. |
| **Einfügestellen** | Use-Case-spezifische Widgets und State: siehe Abschnitt **„Einfügestellen für Use-Case-spezifische Erweiterungen“** – dort sind die zulässigen Stellen in app.py, Model, Result-State, dsp, measurement.py definiert; kompatibel mit dem Design-Pattern. |

Dieses Konzept bildet die Basis für eine **Use-Case-getriebene, klare Software-Architektur** im lab_suite-Sound-Umfeld und ermöglicht alle typischen Laborübungen zur Kommunikationstechnik im **identischen Ökosystem** mit **einem** Modul (dsp.py / user_code.py) für den fachlichen User-Code.
