# Visueller Builder – Skizze

Tool zum Erzeugen und Bearbeiten von **layout.json** ohne Hand-Editierung. Ausgabe: valides Layout-JSON; optional Aufruf des Skeleton-Generators.

---

## 1. Ziel und Umfang

- **Eingabe:** Keine (Neustart) oder bestehende **layout.json** (öffnen/laden).
- **Bearbeitung:** Struktur per **Baum** und/oder **Canvas**; Eigenschaften pro Knoten in einem **Property-Panel**.
- **Ausgabe:** **layout.json** speichern (Download oder Dateipfad); optional **Skeleton generieren** (callback_skeleton.py, model_schema.py) in ein Zielverzeichnis.
- **Kein Code-Editor:** Der Builder erzeugt nur das Layout; User-Logik bleibt in callback_skeleton.py (manuell oder später erweitert).

---

## 2. Benutzeroberfläche (Skizze)

Drei Bereiche nebeneinander (oder 2 + Tab):

```
+------------------+------------------------------------------+------------------+
|  PALETTE         |  CANVAS / BAUM                           |  PROPERTIES      |
|                  |                                          |                  |
|  Container       |  [Dashboard]                             |  Ausgewählt:     |
|  + rows_columns  |    ├─ top (Steuerung)                    |  type: container |
|  + expansion     |    │   ├─ run [checkbox]                 |  id: top         |
|  + tabs          |    │   ├─ test_generator [checkbox]      |  label: Steuerung|
|  + group         |    │   └─ gain [slider]                  |  layout_type:    |
|                  |    ├─ info (Info & Links) [expansion]   |    rows_columns  |
|  Widgets         |    │   ├─ info_text [label]               |  children: 3    |
|  checkbox        |    │   └─ doc_link [link]                |                  |
|  slider          |    └─ tabs_demo [tabs]                   |  [+ Add child]   |
|  button          |        ├─ tab_settings (Einstellungen)   |  [Delete node]   |
|  input           |        └─ tab_about (Über)                |                  |
|  number_input    |                                          |                  |
|  select          |  [Baum-Ansicht]  [Vorschau-Ansicht]     |                  |
|  label           |                                          |                  |
|  …               |  [Save JSON] [Generate Skeleton]         |                  |
+------------------+------------------------------------------+------------------+
```

- **Palette (links):** Liste der Knotentypen, die eingefügt werden können. Unterschieden: **Container** (rows_columns, expansion, tabs, group, tab) und **Widgets** (checkbox, slider, button, input, …). Drag auf den Baum oder „Add child“ beim ausgewählten Knoten.
- **Baum (Mitte):** Hierarchie des Layouts (Dashboard → Container → … → Widget). Klick = Auswahl für Properties; Drag & Drop = Umordnung; Kontextmenü = Löschen, „Add child“, „Add sibling“. Optional zweiter Modus: **Vorschau** (read-only Render der aktuellen layout.json mit build_ui_from_layout, z. B. in einem iframe oder separatem Bereich).
- **Properties (rechts):** Bearbeitbare Felder für den **ausgewählten** Knoten (id, label, layout_type, style; bei Widget: widget_type, props). Änderungen schreiben direkt ins interne Layout-Modell.

---

## 3. Datenmodell und Aktionen

- **Intern:** Ein JavaScript/Python-Objekt, das der **layout.json**-Struktur entspricht (version, dashboard, children mit type, id, …).
- **Aktionen:**
  - **Knoten einfügen:** Aus Palette oder „Add child“ / „Add sibling“; neuer Knoten mit Defaults (z. B. type=container, id=container_1, layout_type=rows_columns, children=[]). Bei Tab: nur unter Container mit layout_type=tabs.
  - **Knoten löschen:** Auswahl → Delete (inkl. aller Kinder).
  - **Umordnen:** Im Baum per Drag & Drop; Reihenfolge der `children`-Array wird aktualisiert.
  - **Eigenschaften bearbeiten:** Properties-Panel → Änderungen in Echtzeit ins Modell (id, label, props.value, …).
- **Validierung:** IDs eindeutig innerhalb des gleichen Parents; bei Tabs nur Tab-Kinder erlauben. Optionale Warnung bei doppelten IDs oder ungültigen layout_type-Kombinationen.

---

## 4. Ausgabe

- **Save JSON:** Serialisierung des Modells nach **layout.json** (Download als Datei oder Speichern auf Server/Dateisystem, wenn das Tool im gleichen Kontext läuft).
- **Generate Skeleton:** Aufruf von `app_builder.skeleton` mit der aktuellen layout.json und Zielverzeichnis (z. B. labs/development_app). Überschreibt callback_skeleton.py und model_schema.py. Kann als Button „Skeleton generieren“ mit konfigurierbarem Ausgabepfad umgesetzt werden (Backend-Aufruf oder CLI aus dem Tool heraus).

---

## 5. Technische Optionen

| Option | Beschreibung | Vor-/Nachteile |
|--------|--------------|-----------------|
| **A) NiceGUI-App** | Builder selbst als NiceGUI-App (lab_suite); Baum mit ui.tree oder Listen, Properties mit dynamischen Inputs, JSON-Export per Datei-Dialog oder Pfad. | Ein Stack (Python/NiceGUI), gleiche Umgebung wie Ziel-Apps; Drag & Drop im Baum evtl. aufwendiger. |
| **B) Standalone SPA** | Frontend (z. B. Vue/React) mit eigenem Backend; Canvas/Baum frei gestaltbar, Export als JSON-Download; Skeleton-Generator als Backend-Call. | Maximale Flexibilität für UX; zweiter Stack, Deployment getrennt. |
| **C) Erweiterung development_app** | „Builder-Modus“ in der development_app: Toggle umschaltet zwischen „Layout anzeigen“ und „Layout bearbeiten“ (Baum + Properties); Speichern überschreibt layout.json. | Schnell integriert; development_app wird schwerer, Konzept „reine Laufzeit-App“ vermischt sich. |

**Empfehlung für MVP:** **Option A (NiceGUI-App)** im Ordner `lab_suite/app_builder/builder_ui/` oder `lab_suite/labs/layout_builder/`: eine eigene kleine App, die nur das Layout-Modell lädt/speichert, Baum + Properties anzeigt und am Ende layout.json exportiert sowie optional den Skeleton-Generator aufruft. Kein Canvas-Drag im ersten Schritt; Baum + Properties reichen für die meisten Layouts.

---

## 6. MVP (Minimal Viable Product)

1. **Layout laden/speichern:** Bestehende layout.json laden (Datei-Upload oder Pfad); Modell im Speicher; Export als layout.json (Download oder Speichern).
2. **Baum-Ansicht:** Hierarchie anzeigen (Dashboard → Kinder → …); Auswahl durch Klick; Knotentyp und id pro Zeile anzeigen.
3. **Palette:** Buttons/Liste „Container (rows_columns)“, „Container (expansion)“, „Container (tabs)“, „Group“, „Tab“; sowie Widget-Typen (checkbox, slider, button, input, …). „Hinzufügen“ fügt als Kind des ausgewählten Knotens ein (Default-IDs: z. B. container_1, tab_1, widget_1).
4. **Property-Panel:** Für ausgewählten Knoten: id, label, layout_type (falls Container), widget_type + wichtige props (falls Widget) editierbar. Schreibweise ins Modell.
5. **Löschen:** Ausgewählten Knoten (inkl. Kinder) entfernen.
6. **Umordnen:** Im Baum Reihenfolge ändern (z. B. Buttons „Hoch/Runter“ oder einfaches Drag & Drop, falls die UI-Bibliothek es hergibt).
7. **Skeleton generieren (optional):** Button „Skeleton generieren“; Pfad zum Zielverzeichnis (z. B. labs/development_app); Aufruf `python -m app_builder.skeleton <exportierte layout.json> --out <pfad> --model`; Meldung „callback_skeleton.py und model_schema.py aktualisiert“.

**Später:** Vorschau-Ansicht (Live-Render mit build_ui_from_layout in einem Frame); Canvas-Drag für xy-Container; Validierung mit Hinweisen (doppelte IDs, fehlende Pflichtfelder).

---

## 7. Ablage und Referenzen

- **Layout-Schema:** `app_builder/layout_format.md`, `layout_schema.py` (Pfad-IDs, Knotentypen, widget_type, props).
- **Skeleton-Generator:** `app_builder/skeleton.py` (CLI: layout.json → callback_skeleton.py, model_schema.py).
- **Renderer:** `app_builder/renderer.py` (build_ui_from_layout) für spätere Vorschau.
- **Ziel-App:** `labs/development_app/` (layout.json, app.py, callback_skeleton.py, model_schema.py).

Diese Skizze kann als Grundlage für ein konkretes Implementierungs-Ticket oder einen Prototyp (z. B. NiceGUI mit ui.tree + dynamischem Property-Panel) dienen.

---

## MVP umgesetzt

Ein lauffähiger MVP liegt unter **`labs/layout_builder/`**:

- **Start:** `python -m labs.layout_builder` (aus lab_suite, Port 8082).
- **Funktionen:** Layout laden (Upload oder „Aus development_app laden“), Baum mit Auswahl, Palette (Container + Widgets hinzufügen), Property-Panel (id, label, layout_type, widget_type, props; Hoch/Runter, Löschen), layout.json herunterladen, Skeleton generieren (Zielordner eingeben).
- **Dateien:** `app.py` (UI), `layout_model.py` (Modell).
- Siehe `labs/layout_builder/README.md`.
