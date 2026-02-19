# User-Code: Scope und Anbindung an die GUI

## 0. Architektur-Überblick: neu (layout-getrieben) vs. alt (use_case_template)

| Aspekt | **Neue Architektur** (development_app, App-Builder) | **Alte Architektur** (use_case_template/app.py) |
|--------|-----------------------------------------------------|--------------------------------------------------|
| **Layout** | layout.json (Grid/Renderer), dynamisch | In Code: `build_ui(model)` mit fester Struktur |
| **State/Model** | **Dict** `state[path_id]`, aus model_schema (STATE_DEFAULTS + load/save) | **@dataclass Model** mit festen Attributen (sample_rate, fft_size, …) |
| **Callbacks** | Getrennt: user_callbacks.py (User) + callback_skeleton.py (Registry, generiert) | Im selben app.py, direkt in build_ui / Event-Handler |
| **Generierung** | Skeleton aus Layout → callback_skeleton, model_schema, user_callbacks (Merge) | Keine; alles manuell |

Die neue Architektur trennt Layout, State-Schema und Callback-Logik in eigene Module; der User bearbeitet nur user_callbacks.py (und ggf. eigenes Kern-Modul). Das Model ist bewusst ein **Dict** (kein Dataclass), weil die Keys (path_ids) vom Layout kommen und sich mit dem Layout ändern.

---

## 1. Scope des User-Codes

| Schicht | Wo | Aufgabe |
|--------|-----|--------|
| **Reaktiv (GUI-Events)** | `user_callbacks.py` | Reagiert auf User-Input: Slider, Button, Checkbox, etc. Dünne Schicht: Wert entgegennehmen, an Kern-Logik weiterreichen, ggf. State lesen/schreiben. |
| **Kern (Algorithmik, DSP, Domain)** | Eigenes Modul, z. B. `app_logic.py` oder `dsp.py` | Dedizierte Logik ohne GUI: Berechnungen, DSP, Streaming-Steuerung. **Liest/schreibt nur den State** (den gleichen Dict, den model_schema lädt/speichert). Kein NiceGUI-Import. |
| **Real-Time / Streaming** | Eigenes Modul (z. B. `streaming.py`) oder Teil der Kern-Logik | Läuft in Thread/Async: z. B. Audio-Stream. Liest aus State (Parameter wie Gain, Mute), schreibt in State (Levels, Status) → GUI aktualisiert sich über `on_state_change`. |

**Kurz:** Ja – der **Kern des User-Codes** (DSP, Algorithmik, Streaming) greift idealerweise **nur auf den State zu** (den model_schema definiert und die App lädt/speichert). Die GUI und die Callbacks sind die einzigen Stellen, die NiceGUI kennen; der Rest ist GUI-frei und testbar.

---

## 2. Wo macht der User was am besten?

```
┌─────────────────────────────────────────────────────────────────┐
│  GUI (layout.json + build_ui_from_layout)                        │
│  → zeigt State, ruft bei Änderung Callbacks auf                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  user_callbacks.py  (reaktiv)                                    │
│  → on_xxx_change(value) / on_xxx_click()                          │
│  → dünn: State lesen/schreiben, Kern-Logik aufrufen              │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  State (Dict)   │  │  app_logic.py    │  │  streaming.py   │
│  model_schema   │  │  (Kern: DSP,     │  │  (Thread/Async: │
│  load/save      │  │   Algorithmik)   │  │   Audio-Stream)│
│                 │  │  → liest/schreibt│  │  → liest State  │
│  Einzige        │  │    State         │  │  → schreibt     │
│  Schnittstelle  │  │  → kein GUI      │  │    Level/Status │
│  GUI ↔ Logik    │  └─────────────────┘  └─────────────────┘
└─────────────────┘
```

- **user_callbacks.py:** Nur reaktiv. Parameter aus Event, bei Bedarf State lesen/schreiben, Kern-Logik aufrufen. Keine langen Berechnungen, kein Blocking.
- **Kern-Modul (app_logic / dsp / …):** Reine Funktionen oder kleine Klassen: Input = State-Dict oder konkrete Werte, Output = State aktualisieren oder Rückgabe. Kein `import nicegui`. Ideal für Tests und Wiederverwendung.
- **Streaming / Real-Time:** In eigenem Thread oder async Task. Liest z. B. `state["gain"]`, `state["mute"]`; schreibt z. B. `state["row_0.widget_5"] = level` (VU) oder ein dediziertes `state["stream_level"]`. Die GUI wird über das bestehende `on_state_change` aktualisiert (Refresh der Anzeige), sofern die App das für die relevanten Keys macht.

---

## 3. Gut strukturierte Anbindung (Beispiel)

### State als einzige Kopplung GUI ↔ Logik

- **model_schema** definiert Keys (path_ids + ggf. extra Keys für Status/Level).
- **App** lädt State einmal, übergibt ihn an `build_ui_from_layout` und an die Callbacks (sobald State dort verfügbar ist).
- **Callbacks** lesen/schreiben State und rufen Kern-Logik auf.
- **Kern/Streaming** bekommen den **gleichen** State-Dict (Referenz); alle Änderungen sind sofort für die GUI sichtbar, wenn die App nach Änderungen `on_state_change` aufruft (oder der Renderer das ohnehin tut).

### Callbacks mit State-Zugriff (empfohlene Erweiterung)

Damit der User in Callbacks andere GUI-Werte lesen/setzen kann, die Callbacks aber weiterhin einfach bleiben:

- **Option A:** Callbacks bekommen `(value, state)` übergeben; Registry wird bei App-Start mit gebundenem `state` erzeugt (Closure).
- **Option B:** Ein zentrales Modul (z. B. `app_state.py`) hält `current_state: dict` und bietet `get_state()` / `set_state(path_id, value)`; Callbacks und Kern importieren das und lesen/schreiben dort.

Dann sieht ein User-Callback z. B. so aus:

```python
# user_callbacks.py
from . import app_logic  # Kern
# state per Option A (Parameter) oder Option B (get_state())

def on_gain_change(value: Any) -> None:
    state = get_state()  # oder state wird injiziert
    state["row_0.gain"] = value
    app_logic.set_gain(value)  # Kern aktualisiert DSP
```

```python
# app_logic.py (Kern, kein GUI)
def set_gain(gain: float) -> None:
    # DSP, Filter, etc.
    ...
```

```python
# streaming.py (Thread)
def _run_stream(state: dict) -> None:
    while running:
        level = audio_device.read_level()
        state["row_1.vu_meter"] = level  # GUI zeigt Level
```

### Option C: Get/Set mit fachlichen Größen (gui_binding) – empfohlen für Entkopplung

In der **development_app** gibt es **gui_binding.py**: eine zentrale Zuordnung **logischer Name → path_id** (SEMANTIC_BINDING) und zwei Funktionen **get(key)** / **set(key, value)**. Der Rest der App (Callbacks, Kern, Streaming) arbeitet nur mit den Keys (z. B. `"power"`, `"gain"`, `"led_status"`); path_ids und Widget-Registry bleiben in der GUI-Schicht.

- **SEMANTIC_BINDING:** Du pflegst einmalig z. B. `"gain" → "row_2.widget_15"`, `"led_status" → "row_2.widget_13"`.
- **get("gain"):** Liest aus State (über path_id); nutzbar in Callbacks und in der Kern-Logik, wenn sie im GUI-Kontext aufgerufen wird.
- **set("led_status", "on"):** Schreibt State und aktualisiert Output-Widgets (LED, VU-Meter) über die Widget-Registry.

**Vergleich Qt:** In Qt trennt man oft Model (Daten) und View (Widgets); die View bindet an **Property-Namen** oder **Model-Rollen** (z. B. `model.data(index, Qt::DisplayRole)`). SEMANTIC_BINDING ist dasselbe Prinzip: eine Tabelle, die fachliche Größen eindeutig mit dem technischen Schlüssel (path_id) verknüpft. Sauber und einfach: eine Stelle zum Pflegen, überall sonst nur logische Namen.

**Beispiel Callback mit gui_binding:**

```python
# user_callbacks.py
from . import gui_binding, app_logic

def on_row_2_widget_15_change(value: Any) -> None:
    gui_binding.set("gain", value)  # State + ggf. Anzeige
    app_logic.apply_gain(gui_binding.get("gain"))
```

```python
# app_logic.py (Kern – wird aus Callback aufgerufen; kann bei Bedarf auch get nutzen)
def apply_gain(gain: float) -> None:
    ...
```

---

## 4. Kurz-Checkliste

- **Reaktiv (GUI):** Nur in `user_callbacks.py`, dünn, State + Aufruf Kern/Streaming.
- **Kern (DSP, Algo):** Eigenes Modul, greift nur auf State zu (und ggf. Dateien/ Hardware-APIs), kein NiceGUI.
- **Real-Time/Streaming:** Eigenes Modul/Thread, liest Konfiguration aus State, schreibt Ergebnisse/Status in State; GUI aktualisiert sich über vorhandenes State-Binding.
- **State:** Ein gemeinsamer Dict (model_schema), von App geladen, an GUI und an alle User-Module (Callbacks, Kern, Streaming) als gleiche Referenz übergeben oder zentral bereitgestellt.

So bleibt die GUI-Anbindung klar, der Kern bleibt testbar und GUI-frei, und Streaming kann sicher und reaktiv an die GUI angebunden werden.

---

## 4b. Modulliste (neue Architektur) – Scope pro Datei

| Modul | Ort | Scope | Generiert? |
|-------|-----|--------|------------|
| **layout.json** | App-Ordner (z. B. development_app/) | Struktur der GUI: Dashboard → Container/Widgets, path_ids, widget_type, props. | Ja (Grid-Editor / Layout-Builder), User kann anpassen. |
| **model_schema.py** | App-Ordner | STATE_DEFAULTS (dict, Keys = path_ids), load_state(path), save_state(state, path). Session-Persistenz. | Ja (Skeleton mit --model), bei Layout-Änderung neu generieren. |
| **callback_skeleton.py** | App-Ordner | STATE_DEFAULTS (für UI), Imports aus user_callbacks, get_callback_registry(). | Ja, bei jedem Skeleton neu generiert. |
| **user_callbacks.py** | App-Ordner | Nur Callback-Funktionen (on_…_change, on_…_click). Reaktiv: Wert/State lesen/schreiben, ggf. Kern-Logik aufrufen. | Merge: neue Stubs ergänzt, Bereiche mit „#begin user code“ / „#end user code“ erhalten. |
| **app.py** | App-Ordner | Dünn: Layout laden, State laden (model_schema), Registry holen (callback_skeleton), build_ui_from_layout aufrufen, Editor-Dialog (optional). | Nein, einmalig pro App. |
| **Kern-Modul** (z. B. app_logic.py, dsp.py) | App-Ordner (optional) | Domain-/DSP-Logik ohne GUI. Liest/schreibt nur den State-Dict. | Nein, User. |

**Model = Dict, kein Dataclass:** In der neuen Architektur ist das „Model“ der gemeinsame **State-Dict** (Keys = path_ids aus dem Layout). Es gibt **keine** @dataclass Model-Klasse, weil die Keys dynamisch aus dem Layout kommen. Typisierung pro Key wäre möglich (z. B. generiertes TypedDict), ist aber aktuell nicht umgesetzt. – In **use_case_template** gibt es weiterhin eine **@dataclass Model** mit festen Feldern (sample_rate, fft_size, …), weil diese App use-case-spezifisch und nicht layout-getrieben ist.

---

## 5. Editor-Modus für Studierende („nur diese Stelle bearbeiten“)

**Ziel:** Studierende mit wenig Zeit sollen **kleine Teile** User-Code implementieren, ohne die Gesamtkomplexität zu sehen. Dazu: gezielter Zugang vom Widget zur zugehörigen Stelle in `user_callbacks.py`.

### Idee

- **Editor-Modus** in der laufenden App (z. B. Toggle „Code bearbeiten“ oder nur in Lern-/Dev-Umgebung).
- **Widget anklicken** → Fokus auf dieses Widget (path_id bekannt).
- **Aktion „Code für dieses Widget öffnen“** → separates Fenster (z. B. Monaco-Editor mit Flake8, wie in eurem anderen Projekt) öffnet `user_callbacks.py` und **springt gezielt zur passenden Stelle**.
- **Verdrahtung** bleibt einfach: Studierende sehen nur die eine Callback-Funktion (und ggf. 1–2 Zeilen Kontext), ergänzen dort ihre Logik. Optional: neues Widget im Layout-Builder einfügen, Skeleton neu generieren, danach im Editor-Modus das neue Widget anklicken und wieder nur die neue Stelle bearbeiten.

### Technik: stabile Marker im Code

Damit die App „die betreffende Stelle“ findet, braucht der generierte User-Code einen **maschinenlesbaren Marker** pro Widget/Callback:

- Im Skeleton-Generator für `user_callbacks.py` wird **über jeder Callback-Funktion** eine Zeile erzeugt:
  - `# widget: <path_id>`
  - z. B. `# widget: row_0.gain`
- Beim Öffnen des Editors: Datei `user_callbacks.py` laden, nach `# widget: <path_id>` suchen (path_id = das fokussierte Widget), **diese Zeile (oder die folgende Funktion) im Editor anzeigen/scrollen**.

So muss der Studierende nicht in der ganzen Datei suchen; die App führt ihn direkt zur richtigen Funktion.

### Ablauf (geplant)

1. App läuft, Editor-Modus an (oder nur in „Lab“-Build).
2. Studierende klickt auf ein Widget (z. B. Slider „Gain“).
3. App kennt die **path_id** des Widgets (muss beim Rendern pro Widget gesetzt werden, z. B. als `data-path-id` oder über eine Rückabbildung aus dem Layout).
4. Button/Link „Code für dieses Widget bearbeiten“ (oder automatisch) → externes Fenster (Monaco o. ä.) öffnet `user_callbacks.py`, sucht `# widget: row_0.gain`, positioniert Cursor/View auf diese Zeile.
5. Studierende bearbeitet nur diese Funktion, speichert; App kann bei Bedarf neu laden oder Hot-Reload.

### Sinnhaftigkeit

- **Ja, sinnvoll** für Nutzer, die „nur“ spezifischen User-Code (Laboraufgabe) ergänzen oder ein neues Widget einbauen und dann nur die eine neue Callback-Stelle füllen wollen.
- Reduziert kognitive Last: kein Durchsuchen der ganzen Datei, keine Konfrontation mit der vollen Struktur.
- Voraussetzungen: (1) path_id pro Widget in der GUI verfügbar (Rendererschicht: bei jedem Widget path_id setzen/speichern, damit beim Klick bekannt), (2) generierte `user_callbacks.py` enthält die `# widget: path_id`-Kommentare, (3) Editor-Fenster (Monaco etc.) mit API zum Öffnen einer Datei und Setzen der Zeile (z. B. `?file=...&line=42` oder Editor-API).

Die Skeleton-Generierung wird um den `# widget: path_id`-Marker ergänzt (siehe app_builder/skeleton.py); die GUI-seitige „Editor-Modus + Klick → path_id → Editor öffnen“-Logik kann schrittweise in der App bzw. in einem gemeinsamen Lab-Launcher umgesetzt werden.

### Wiederverwendung: Monaco + Flake8 aus dem anderen Projekt

Im KT-workspace liegen unter **`reused_code/`** die relevanten Teile aus dem FastAPI-Projekt:

- **MonacoEditor.vue** – Editor-Komponente mit `setMarkers(errors)` und **revealLine(lineNumber)** zum Anspringen einer Zeile.
- **AssignmentEditor.vue** – Einbindung von Monaco + Aufruf von `POST …/validate_python`; Rückgabe `errors` wird an den Editor als Marker übergeben.
- **assignments.py** – `_run_flake8(code)` (Zeile 726) und Endpoint **validate_python** (Zeile 779); liefert `{ line, column, message, severity }` für Monaco.

Details und Datenfluss stehen in **`reused_code/README_MONACO_FLAKE8.md`**. Für den Editor-Modus in der Lab-Suite: Nach `# widget: <path_id>` in `user_callbacks.py` die Zeilennummer ermitteln und in Monaco **revealLine(line)** aufrufen; Flake8-Check kann übernommen werden (z. B. _run_flake8 in einem kleinen Backend oder in der NiceGUI-App per Subprocess).

### Umgesetzte Editor-Integration (development_app)

- **app_builder/editor_helper.py:** `find_widget_marker_line(content, path_id)` und `get_editor_context(file_path, path_id)` → (content, line) für die Zeile `# widget: path_id`.
- **development_app:** Bereich „Editor: Code für Widget“ mit Dropdown (alle path_ids aus dem Layout) und Button „user_callbacks.py öffnen“. Öffnet einen **Dialog** (maximiert) mit **ui.code** (Anzeige von user_callbacks.py) und Hinweis „Callback für path_id (Zeile N)“; Studierende bearbeiten die Datei in der IDE.
- **Optional für Monaco:** Wenn die App mit `ui.run_with(fastapi_app)` läuft, kann `GET /api/editor_context?path_id=...` mit `get_editor_context(..., path_id)` implementiert werden und liefert `{ "content": "...", "line": N }` für die Vue/Monaco-Seite.
