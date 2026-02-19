# 01_05_chapter1 (Template – Single Source of Truth)

**Dieses Verzeichnis ist das gewartete Template** für neue Layout-basierte Apps. Nicht direkt ausführen; neue Apps werden per **App-Creator** daraus in `labs/<Name>/` geklont.

## Verwendung

1. Im **Grid-Editor** (oder per App-Creator): „Neue App aus Template erstellen“, Name angeben (z. B. `01_04_Modulation`).
2. Der Creator legt `labs/<Name>/` an und kopiert den Inhalt dieses Templates; der Name wird in README und Paketbeschreibung ersetzt.
3. Im Grid-Editor die neue App als Ziel wählen, Layout gestalten, „Save layout“, ggf. „Skeleton generieren“.
4. App starten: `python -m labs.<Name>` (aus lab_suite).

## Struktur (wie development_app)

- **_core/** – app.py, callback_skeleton, model_schema, assignment_registry, gui_binding
- **assignments/** – user_callbacks.py (deine Logik), user_template.py (Assignment-Vorlage), active.json
- **layout.json** – minimales Layout (ein Button); nach dem Klonen im Grid-Editor anpassen.

## Skeleton nach Layout-Änderung

```bash
cd lab_suite
python -m app_builder.skeleton labs/<Name>/layout.json --out labs/<Name>/ --model --user-module assignments.user_callbacks
```

Bei Apps mit **_core/** zusätzlich: `--out-internal _core`

## Erweiterte Templates (später)

- **audio_app** – Standard + Audio-Stack (Mic, Lautsprecher, DSP, Ringbuffer)
- **rtl_sdr_app** – Standard + RTL-SDR-Interface

Diese werden als weitere Template-Ordner (z. B. `templates/audio_app/`) bereitgestellt; der App-Creator kann dann „Standard“ vs. „Audio“ wählen.
