# Initial Task Description

## Labor-Programmierumgebung Kommunikationstechnologie

**Kontext:** Fachhochschule, Kurs Elektronik und Computer Engineering. Zielgruppe: Studierende.

---

### Ausgangslage

- Bisherige **PyQt5-GUIs** für den Laborunterricht skalieren unter Windows 11 nicht mehr zuverlässig.
- Ziel: dauerhafter **Ersatz durch browserbasierte Lösungen**; **NiceGUI** wurde als Technologie gewählt.

---

### Technik-Stack

- **Sprache & Tooling:** Python, Git, VS Code  
- **Hardware & Echtzeit:** RTL-SDR (Software Defined Radio), sounddevices (Akustikübungen), Python-Signalverarbeitung in Echtzeit  
- **GUI:** Browser-basiert, **NiceGUI** für die Labor-Apps

---

### Inhaltliche Ausrichtung

- **Interaktive Lern-Apps** (keine reinen Skripte), z. B.:
  - **TDOA-Demo** (Schallquellen-Ortung mit 2 Mikrofonen)
  - **FFT-Scope** (Oszilloskop/Spektrum)
  - **RTL-SDR-Spektrum**
- Optional: **Orchestrator** (Vue/Tauri) als lokales Lab-Frontend und **Launcher-Service** (Python oder Node) zum Starten/Stoppen der NiceGUI-Apps.

---

### Projektstruktur (abgeleitet aus dieser Aufgabenstellung)

```
lab_suite/
├─ orchestrator/          # Vue/Tauri App (optional)
├─ launcher/              # kleiner lokaler Service (Python oder Node)
├─ labs/                  # NiceGUI Apps
│  ├─ tdoa/
│  ├─ fft_scope/
│  └─ rtlsdr_spectrum/
├─ shared/                # gemeinsame DSP/Utils
├─ docs/
└─ requirements.txt
```

---

### Kurzfassung

Labor-Programmierumgebung für Studierende der **Kommunikationstechnologie** (FH, ECE-Kurs): Python (Git, VS Code, RTL-SDR, sounddevices, Echtzeit-Signalverarbeitung); Ersatz von PyQt5 durch **browserbasierte GUIs** mit **NiceGUI**; interaktive Lern-Apps (TDOA, FFT-Scope, RTL-SDR-Spektrum); optional Orchestrator + Launcher. Der Verzeichnisbaum unter `lab_suite/` wurde entsprechend angelegt.
