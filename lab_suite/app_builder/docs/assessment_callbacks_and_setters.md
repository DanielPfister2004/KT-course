# Assessment: Callbacks vs. Setter – Zugriff auf Input/Output-Widgets

Kurzbewertung, wie der User aktuell auf **Input** (Callbacks) und **Output** (LED, VU-Meter, Plotly) zugreift und welche Lücken bestehen.

---

## 1. Input: Callbacks (bereits vorhanden)

| Aspekt | Stand |
|--------|--------|
| **Mechanismus** | Pro Widget mit Wertänderung/Klick wird ein Callback registriert (`get_callback_registry()`: path_id → Callable). |
| **Auslösung** | Renderer ruft bei Änderung `state[path_id] = value` und `callbacks.get(path_id)(value)` (bzw. bei Klick `fn()` ohne Argument). |
| **User-Zugriff** | User implementiert in `user_callbacks.py` die Funktionen; erhält **nur** den neuen Wert `value` (bzw. bei Relayout `relayout_data`). path_id nur in Docstring, nicht als Parameter. |
| **Widget-Typen** | button → click; checkbox, slider, number_input, input, select, gain_control_vue → change; plotly_* → relayout (wenn im Renderer umgesetzt). |

---

## 2. Output: Anzeige-Widgets (LED, VU-Meter) – Lücke

### Was die Widget-Klassen können

- **VuMeter** (`widgets/vu_meter.py`): `set_value(value: float)` – aktualisiert Anzeige.
- **Led** (`widgets/led.py`): `set_state(state: str | int)` – aktualisiert Zustand (off/on/warning/error).

### Was der Renderer macht

- Beim Aufbau: `VuMeter(value=state.get(path_id, ...), ...)` bzw. `Led(state=state.get(path_id, ...), ...)`.
- Es wird **keine Referenz** auf die Widget-Instanz gespeichert oder an die App zurückgegeben.

### Konsequenz für den User

- **Kein direkter Zugriff** auf die Widget-Instanz. Der User kann **nicht** `widget_registry["row_1.vu_meter"].set_value(0.5)` o.ä. aufrufen, weil es keine Widget-Registry gibt.
- **State schreiben reicht nicht:** Wenn der User nur `state["row_1.vu_meter"] = 0.5` setzt, wird die Anzeige **nicht** aktualisiert – die Vue-Komponenten sind einmal mit dem initialen Wert erzeugt und lesen den State nicht reaktiv.

### Dokumentation vs. Realität

- In `USER_CODE_ARCHITECTURE.md` steht sinngemäß: „Streaming schreibt `state['row_1.vu_meter'] = level` → GUI zeigt Level.“ Das entspricht der **gewünschten** Architektur, ist mit dem aktuellen Renderer aber **nicht** umgesetzt (kein reaktives Binding von State → VuMeter/Led).

### Mögliche Lösungsrichtungen (für spätere Features)

1. **Widget-Registry:** `build_ui_from_layout` füllt optional ein Dict `path_id → Widget-Instanz` (nur für Output-Widgets wie led, vu_meter). User ruft z. B. `registry["row_1.vu_meter"].set_value(level)` auf.
2. **State-getriebene Updates:** Bei `on_state_change` (oder Timer) für bestimmte path_ids die zugehörigen Output-Widgets aus einer Registry holen und `set_value`/`set_state(state[path_id])` aufrufen – dann würde „State schreiben + on_state_change“ indirekt die Anzeige treiben.
3. **Reaktives Binding:** Vue-Komponenten so erweitern, dass sie einen „state key“ erwarten und sich bei Änderungen dieses Keys aktualisieren (aufwändiger, eher Framework-Änderung).

---

## 3. Output: Plotly (plotly_graph etc.) – Lücke im generischen Renderer

### Was die Widget-Klasse kann

- **PlotlyGraph** (`widgets/plotly_graph.py`):  
  - `update_figure(data, layout=None, config=None)`  
  - `update_from_figure(fig)` (z. B. `go.Figure().to_plotly_json()`).

### Was der Renderer macht

- **Aktuell:** Im **generischen** Renderer (`app_builder/renderer.py`) gibt es **keinen** Zweig für `plotly_spectrum`, `plotly_graph`, `plotly_scatter`, `plotly_histogram`, `plotly_3d`. Diese Widget-Typen landen in der Fallback-Zweig „Unbekannter Typ“ und werden als Platzhalter `[plotly_graph]` o. ä. dargestellt.
- **Konsequenz:** In der **Development-App** (layout-getrieben mit `build_ui_from_layout`) kann der User derzeit **gar nicht** plotten – es wird kein Plotly-Widget erzeugt.

### Wie es im use_case_template gelöst ist

- Die UI wird dort **manuell** gebaut (nicht über `build_ui_from_layout`). Es wird eine Referenz auf die Plot-Instanz gehalten und in einer Update-Schleife bzw. in Callbacks `plot.update_figure(_fig_with_config())` aufgerufen. Das ist der **erwartete** Nutzungsmodus (App schreibt Figur), aber außerhalb des generischen Layout-Renderers.

### Mögliche Lösungsrichtungen (für spätere Features)

1. **Plotly im Renderer:** Für `plotly_graph` (und ggf. plotly_spectrum, …) im Renderer `PlotlyGraph(...)` erzeugen und **optional** in eine **Widget-Registry** eintragen (path_id → PlotlyGraph). User könnte dann z. B. `registry["dashboard.plot1"].update_figure(data, layout)` oder `update_from_figure(fig)` aufrufen.
2. **State als Übergabe:** Weniger sinnvoll, da Figuren groß sind und typischerweise nicht vollständig im State gehalten werden; eher Registry + direkte Aufrufe.

---

## 4. Übersichtstabelle

| Ziel | Vorhandener Mechanismus | Lücke / Hinweis |
|-----|-------------------------|------------------|
| **Input melden** | Callbacks (path_id → fn); User erhält `value` (oder bei click/relayout 0/1 Argument). | path_id und Props nicht als Parameter; nur in Docstring/Layout-Lookup. |
| **LED setzen** | Led hat `set_state(...)`. | Keine Referenz/Registry; State schreiben aktualisiert die Anzeige **nicht**. |
| **VU-Meter setzen** | VuMeter hat `set_value(...)`. | Wie LED: keine Referenz/Registry; reines State-Schreiben reicht nicht. |
| **Plotly zeichnen** | PlotlyGraph hat `update_figure` / `update_from_figure`. | Plotly-Widgets im **generischen** Renderer **nicht** implementiert; in layout-getriebener App derzeit kein Plot möglich. use_case_template nutzt manuell gebaute UI + Referenz. |

---

## 5. Fazit

- **Callbacks für Input:** Vorhanden und nutzbar; User schreibt Logik in `user_callbacks.py` und erhält den neuen Wert.
- **Setter für Output (LED, VU-Meter):** API der Widgets (`set_value`/`set_state`) ist da, aber der **layout-getriebene** Stack stellt dem User **keine** Möglichkeit bereit, diese Setter aufzurufen (keine Registry, kein reaktives State-Binding).
- **Plotly:** Widget-Klasse und API sind da; im **generischen** Renderer fehlt die Erzeugung und damit jede Möglichkeit, in der Development-App zu plotten. Erst durch Einbau von Plotly im Renderer **plus** optionaler Widget-Registry könnte der User plotten wie im use_case_template (dann über Registry statt fester Variable `plot`).

**Reihenfolge der Umsetzung:** Der **erste Schritt** ist die **Widget-Registry** (path_id → Instanz für Output-Widgets, optional auch Input). **Umgesetzt:** `build_ui_from_layout(..., widget_registry=dict)` befüllt das Dict für **led** und **vu_meter**; Development-App nutzt `ui.context.client.widget_registry`. Darauf aufbauend: Plotly im Renderer + Eintrag in der Registry, dann Template und Stub-Beispielcode.

---

## 6. Strategie-Bewertung: Getter/Setter + Callbacks als dünne Schicht

**Vorgeschlagene Strategie:**

- User nutzt **primär getter() und setter()** für GUI-Parameter (Lesen/Schreiben).
- **Callbacks** = dünne Zwischenschicht: neue Werte aus Widgets lesen → in app-globalen State schreiben.
- Die **eigentliche App** (Kern, DSP, Streaming) holt Werte über **getter()**.
- **Plot-/Display-Updates** als Setter-Funktionen abstrahiert; der Zugriff kann im **user_callbacks**-Code stehen, weil dieser den Datenaustausch mit der GUI regelt.

### Bewertung: **kanonisch und sinnvoll**

| Aspekt | Einschätzung |
|--------|--------------|
| **Callbacks dünn** | Passt zur Architektur (USER_CODE_ARCHITECTURE.md): Callbacks schreiben State, rufen ggf. Kern-Logik auf, blockieren nicht. |
| **State als zentrale Kopplung** | Konsistent: Ein app-globaler State (Dict), Callbacks schreiben rein, Kern/Streaming lesen/schreiben – eine einzige Quelle. |
| **Getter in der App** | Sauber: Kern kennt keine path_ids; stabilere API (z. B. `get_gain()` statt `state["row_1.widget_5"]`). Nützlich bei Typisierung, Validierung, abgeleiteten Werten. |
| **Plot/Display-Setter in user_callbacks-Nähe** | Sinnvoll: Alle GUI-I/O an einer Stelle (Callbacks + ggf. Timer/Refresh). App liefert Daten; „GUI-Schicht“ (Callbacks oder ein kleines Modul mit Zugriff auf Registry) ruft `update_plot(path_id, fig)` / `set_led(path_id, "on")` auf. |

Diese Strategie ist **kanonisch** für eine klare Trennung: GUI-Schicht (Callbacks + Setter für Anzeigen) ↔ State ↔ Kern-Logik (nutzt Getter).

### Einfachere Alternative (ohne Getter/Setter-Layer)

Für kleine Apps oder schnelle Prototypen reicht oft:

- **Ein gemeinsamer State-Dict.** Callbacks: `state[path_id] = value`, evtl. Kern aufrufen. Kern/Streaming: lesen/schreiben direkt `state["row_1.gain"]`, `state["row_1.vu_meter"] = level`. Kein Getter/Setter – alle nutzen dieselbe Referenz.
- **Vorteil:** Weniger Code, keine Wrapper. path_id bleibt in Callbacks/Kern sichtbar (oder z. B. als Konstanten pro App).
- **Nachteil:** Keine stabile „fachliche“ API (z. B. `get_gain()`), path_ids können sich mit Layout-Änderungen verschieben.

**Wann Getter/Setter lohnen:**

- Stabile, fachliche API (Namen unabhängig von path_id).
- Typisierung / Validierung / Defaults an einer Stelle.
- Kern soll keine path_ids kennen (bessere Testbarkeit, weniger Layout-Abhängigkeit).

### Kurzfassung

- **Strategie „Getter/Setter + dünne Callbacks + Plot/Display-Setter in GUI-Schicht“:** Ja, **kanonisch** und gut für strukturierte, erweiterbare Apps.
- **Einfachere Variante:** Nur State-Dict teilen, Callbacks schreiben rein, App liest/schreibt State direkt – ohne Getter/Setter-Layer. Ausreichend für viele kleine Apps; Getter/Setter hinzufügen, sobald stabile API oder Entkopplung vom Layout gewünscht sind.

**Übungskonzept (Template + Oszilloskop/Spektrum/XY, Marker, Stubs mit Beispielcode):** Siehe **app_builder/docs/uebungskonzept_signal_analyse.md** – bestätigt, dass mit durchgängiger Widget-Registry das Konzept realisierbar ist, inkl. semantischer Template-IDs und kommentierter Callback-Stubs.

---

## 7. Timer: Single vs. Multiple, Definition in der App

**Zweck:** User-Logik periodisch ausführen (Plots aktualisieren, Messwerte lesen, Animation) – **unabhängig** von Callbacks (Klick, Slider).

| Aspekt | Entwicklung-App (Stand) |
|--------|-------------------------|
| **Wo definiert** | In **app.py** direkt nach `build_ui_from_layout`: ein `ui.timer(interval, callback)` wird gestartet. |
| **Rate** | Einstellbar über Umgebungsvariable **`TIMER_INTERVAL_SEC`** (Default `0.1` → 10 Hz). |
| **Single vs. Multiple** | **Ein** Timer ruft das aktive Assignment auf: `get_assignment()` → `mod.timer_tick()` (falls vorhanden). Für **mehrere** Raten: entweder weitere `ui.timer(interval, fn)` in app.py, die z. B. `mod.update_fast()` / `mod.update_slow()` aufrufen, oder in `timer_tick()` einen Zähler und nur jedes N-te Mal langsame Logik. |
| **Passung Architektur** | Callbacks = reaktiv (User-Event); Timer = periodisch (zeitgetriggert). Beide laufen im GUI-Kontext, nutzen dieselbe gui_binding (get/set/update_plot) und dasselbe aktive Assignment. Saubere Trennung: „Was passiert bei Event?“ vs. „Was passiert alle X Sekunden?“ |
