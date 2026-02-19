# Spezifikation: plotly_graph-Widget in der Widget-Palette

## 1. Ist-Zustand (Integration)

| Aspekt | Status |
|--------|--------|
| **Widget-Klasse** | `lab_suite/widgets/plotly_graph.py` + `plotly_graph.js` – vorhanden, funktionsfähig |
| **Props (aktuell)** | `data`, `layout`, `config`, `height`, `plotly_script_url`; Palette-Props siehe Abschnitt 3 |
| **Methoden** | `update_figure(data, layout?, config?)`, `update_from_figure(fig)`; NumPy in x/y/z wird zu Listen konvertiert |
| **Widget-Palette** | **Integriert** – `plotly_graph` in `WIDGET_DEFAULTS` (layout_model.py), Property-Hints für Axis/Labels/Traces/Marker |
| **Renderer** | **Integriert** – Zweig für `plotly_graph`, `plotly_scatter`, `plotly_histogram`, `plotly_3d` in `app_builder/renderer.py`; initiales Layout/Data aus Props, Eintrag in `widget_registry` |
| **Layout-Schema** | plotly-Typen in `layout_schema.py` (WIDGET_STATE_DEFAULTS, Callbacks relayout) vorhanden |

---

## 2. Ziele der Integration

- **Palette:** `plotly_graph` (und optional `plotly_scatter`, `plotly_histogram`, `plotly_3d`) in der Widget-Palette verfügbar; im Grid-Editor und in der Development-App auswählbar.
- **Konfiguration:** Achsen-Skalierung, Achsen- und Titel-Labels, Anzahl der Traces (als Vorgabe/Hinweis), Marker-Optionen über Props/Layout im Property-Panel editierbar.
- **Ausgabe:** Plot-Daten von der App an das Widget übergeben (Widget-Registry + `update_figure` / `update_from_figure`); optional Events (relayout, click) für Export oder Reaktion auf Zoom/Auswahl.

---

## 3. Konfigurationsparameter (Props / Layout)

Die folgenden Parameter sollen im Property-Panel (EDIT MODE) konfigurierbar sein und als Vorgaben für das initiale Layout bzw. für die App dienen. Die **tatsächlichen Plot-Daten** (Traces x/y, etc.) kommen zur Laufzeit von der App über die Widget-Registry.

### 3.1 Achsen-Skalierung (Axis Scaling)

| Parameter | Typ | Beschreibung | Plotly-Entsprechung |
|-----------|-----|--------------|---------------------|
| **xaxis_type** | `string` | Skalierung X-Achse | `layout.xaxis.type` |
| | Optionen: `linear`, `log`, `date`, `category` | | |
| **yaxis_type** | `string` | Skalierung Y-Achse | `layout.yaxis.type` |
| **xaxis_range** | `string` oder leer | Fixer Bereich X, z. B. `"0,10"` oder `"[0, 100]"` | `layout.xaxis.range` (Array) |
| **yaxis_range** | `string` | Fixer Bereich Y | `layout.yaxis.range` |
| **xaxis_autorange** | `boolean` | True = automatische Range | `layout.xaxis.autorange` |
| **yaxis_autorange** | `boolean` | True = automatische Range | `layout.yaxis.autorange` |

- Default: `xaxis_type`/`yaxis_type` = `linear`, `*_autorange` = true, `*_range` = leer (ignoriert bei autorange).

### 3.2 Labels

| Parameter | Typ | Beschreibung | Plotly-Entsprechung |
|-----------|-----|--------------|---------------------|
| **title** | `string` | Graph-Titel (über dem Plot) | `layout.title.text` |
| **xaxis_title** | `string` | Label X-Achse | `layout.xaxis.title.text` |
| **yaxis_title** | `string` | Label Y-Achse | `layout.yaxis.title.text` |
| **title_font_size** | `number` | Schriftgröße Titel (optional) | `layout.title.font.size` |
| **axis_title_font_size** | `number` | Schriftgröße Achsen-Labels (optional) | `layout.xaxis.title.font.size` (analog yaxis) |

### 3.3 Anzahl der Traces

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| **trace_count** | `integer` (min 1, max z. B. 20) | Vorgabe für die Anzahl der Traces (Hinweis für die App / Default-Leerfigure). Kein zwingendes Limit; die App kann mehr/weniger Traces in `update_figure(data)` übergeben. |

- Nutzung: Initiale leere Figur mit `trace_count` leeren Traces (z. B. `[{ x: [], y: [], name: 'Trace 1' }, ...]`) oder nur als Dokumentation/Default für Code-Generatoren.

### 3.4 Marker und Linien (Defaults pro Trace)

| Parameter | Typ | Beschreibung | Plotly-Entsprechung |
|-----------|-----|--------------|---------------------|
| **mode** | `string` | Darstellungsmodus | `trace.mode` |
| | Optionen: `lines`, `markers`, `lines+markers` | | |
| **marker_size** | `number` | Größe der Marker (px) | `trace.marker.size` |
| **marker_symbol** | `string` | Symbol, z. B. `circle`, `square`, `diamond`, `cross` | `trace.marker.symbol` |
| **marker_color** | `string` (Hex/color) | Farbe Marker (eine; bei mehreren Traces ggf. Palette) | `trace.marker.color` |
| **line_dash** | `string` | Linienart | `trace.line.dash` (solid, dot, dash, longdash, dashdot, longdashdot) |
| **line_width** | `number` | Linienbreite | `trace.line.width` |

- Diese Props dienen als **Vorgaben** für die initiale Figur oder für Code-Stubs; die App kann in `update_figure(data)` pro Trace abweichende Werte setzen.

### 3.5 Sonstige Props (bereits vorhanden / erweitert)

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| **height** | `string` | Höhe des Plot-Containers (z. B. `400px`, `50vh`) |
| **plotly_script_url** | `string` | Optional: URL zu plotly.js (leer = CDN); für Offline Default: `/widgets-static/plotly.min.js` (eine Kopie in widgets/static) |
| **responsive** | `boolean` | Layout responsiv (Plotly config) |

---

## 4. Ausgabe von Plot-Daten (Data Output)

### 4.1 Schreiben der Plot-Daten (App → Widget)

- **Widget-Registry:** Der Renderer erzeugt für jedes `plotly_graph`-Widget eine Instanz `PlotlyGraph(...)` und trägt sie in `widget_registry[path_id]` ein.
- **Setter:** Die App liest die Referenz z. B. über `ui.context.client.widget_registry[path_id]` und ruft auf:
  - `update_figure(data, layout=None, config=None)` – Daten (Liste Traces) und optional Layout/Config,
  - oder `update_from_figure(fig)` – `fig` eine `go.Figure()` mit `fig.to_plotly_json()`.
- **State:** Es wird **kein** vollständiger Figure-Inhalt im Session-State persistiert; die App ist alleinige Quelle der Plot-Daten.

### 4.2 Events (optional): Relayout, Click

- **relayout:** Bei Zoom/Pan/Anpassung der Achsen kann ein Callback `on_<path_id>_relayout` (oder über user_id) mit den neuen Layout-Daten aufgerufen werden (z. B. für Export der sichtbaren Range oder Synchronisation mit anderen Plots).
- **click:** Bei Klick auf einen Punkt kann ein Callback mit Punkt-Daten (Trace-Index, x, y, Punktindex) ausgelöst werden – für Tooltips, Marker oder Daten-Export.

Die genaue Event-Weiterleitung (NiceGUI/Vue → Python) ist in der Implementierung zu definieren (z. B. `plotly_relayout` / `plotly_click` in plotly_graph.js emittieren und im Renderer auf Callback mappen).

---

## 5. Datenmodell (Layout / Props)

### 5.1 Vorschlag für `WIDGET_DEFAULTS["plotly_graph"]`

```python
"plotly_graph": {
    "type": "widget",
    "id": "",
    "widget_type": "plotly_graph",
    "props": {
        "height": "400px",
        "plotly_script_url": "",
        "title": "",
        "xaxis_title": "",
        "yaxis_title": "",
        "xaxis_type": "linear",
        "yaxis_type": "linear",
        "xaxis_autorange": True,
        "yaxis_autorange": True,
        "xaxis_range": "",
        "yaxis_range": "",
        "trace_count": 1,
        "mode": "lines",
        "marker_size": 6,
        "marker_symbol": "circle",
        "marker_color": "",
        "line_dash": "solid",
        "line_width": 1.5,
        "responsive": True,
    },
},
```

### 5.2 Vorschlag für `WIDGET_PROP_HINTS["plotly_graph"]`

- `xaxis_type` / `yaxis_type`: Options-Select (`linear`, `log`, `date`, `category`).
- `mode`: Options-Select (`lines`, `markers`, `lines+markers`).
- `marker_symbol`: Options-Select (circle, square, diamond, cross, x, triangle-up, …).
- `line_dash`: Options-Select (solid, dot, dash, longdash, dashdot, longdashdot).
- `marker_color`: color (Hex oder Picker wie bei text_color/bg_color).
- Numeric: `marker_size`, `line_width`, `trace_count`, `title_font_size`, `axis_title_font_size` mit sinnvollen min/max.

---

## 6. Renderer: Abbildung Props → Plotly-Layout/Data

Im Renderer-Zweig für `plotly_graph`:

1. **Initiales Layout** aus Props bauen:
   - `layout.title.text` = props.title
   - `layout.xaxis.type` = props.xaxis_type, `layout.xaxis.title.text` = props.xaxis_title, `layout.xaxis.autorange` = props.xaxis_autorange, ggf. `layout.xaxis.range` aus props.xaxis_range parsen
   - analog für yaxis
   - optionale font sizes
2. **Initiale Data (Traces):** `trace_count` leere Traces mit Vorgaben für mode, marker (size, symbol, color), line (dash, width).
3. **Widget-Registry:** Nach Erstellung `widget_registry[path_id] = plotly_graph_instance`.
4. **Optional:** Event-Handler für relayout/click registrieren und an callbacks anbinden.

---

## 7. Implementierungs-Checkliste

- [x] **layout_model.py:** `plotly_graph` in `WIDGET_DEFAULTS` mit Props (height, title, x/yaxis_*, trace_count, mode, marker_*, line_*, responsive).
- [x] **layout_model.py:** `WIDGET_PROP_HINTS["plotly_graph"]` für Axis-Type, Mode, Marker-Symbol, Line-Dash, Farben, Zahlen.
- [x] **renderer.py:** Zweig für `plotly_graph`, `plotly_scatter`, `plotly_histogram`, `plotly_3d`: Props → initiales Layout/Data, `PlotlyGraph(...)`, `widget_registry[path_id] = el`.
- [x] **plotly_graph.py:** NumPy in data/layout zu Listen konvertieren (`_to_serializable`), damit x/y/z als numpy.ndarray übergeben werden können.
- [ ] **Events (optional):** In plotly_graph.js bei Plotly-Events (relayout/click) ein Custom-Event emittieren; im Renderer Handler registrieren und Callback aufrufen.
- [x] **Development-App / Grid-Editor:** Palette und Property-Editor nutzen WIDGET_DEFAULTS – kein weiterer Anpassungsbedarf.

---

## 8. Datentypen und DSP-Plot-Varianten

### 8.1 Unterstützte Daten (Speed, NumPy)

- **NumPy-Arrays:** In `update_figure(data, ...)` und in Traces (z. B. `dict(x=freq, y=magnitude)`) können **numpy.ndarray** für `x`, `y`, `z` übergeben werden. Das Widget konvertiert sie intern per `.tolist()` für die JSON-Übergabe an plotly.js. Das ist schnell und typisch für DSP-Pipelines.
- **Listen:** Normale Python-Listen sind unverändert nutzbar.
- **go.Figure:** Mit `update_from_figure(fig)` wird eine Plotly-`go.Figure` übernommen; Plotly konvertiert NumPy beim Aufbau der Figur ohnehin, zusätzlich wendet das Widget `_to_serializable` an.

Empfehlung für DSP: Berechnungen mit NumPy (z. B. FFT, Filterung), dann Traces mit NumPy-Arrays übergeben – keine explizite `.tolist()` nötig.

### 8.2 Entsprechung zu typischen Plot-Funktionen (matplotlib-ähnlich)

| Typ / Funktion   | Beschreibung              | Plotly / Daten |
|------------------|---------------------------|----------------|
| **Plot**         | Linie y über Index        | `go.Scatter(x=None, y=y, mode='lines')` – x optional (Index 0..N-1); NumPy `y` möglich. |
| **PlotXY**       | Linie y über x            | `go.Scatter(x=x, y=y, mode='lines')` – x, y NumPy oder Listen. |
| **PlotScatter**  | Punkte (x, y)             | `go.Scatter(x=x, y=y, mode='markers')` oder `mode='lines+markers'`. |
| **PlotHistogram**| Histogram                 | `go.Histogram(x=values)` – `values` NumPy-Array oder Liste; optional `nbinsx`, `autobinx`. |
| **PlotSpectrum** | Frequenz vs. Magnitude    | `go.Scatter(x=freq, y=magnitude, mode='lines')` – typisch nach FFT: `freq = np.fft.rfftfreq(N, 1/fs)`, `magnitude = np.abs(np.fft.rfft(signal))`. Y-Achse oft `yaxis_type='log'`. |
| **Plot 3D**      | Fläche / Punkte 3D        | `go.Surface(z=Z)` oder `go.Scatter3d(x=x, y=y, z=z)` – Z/x/y NumPy-Arrays möglich. |

Beispiel (DSP, Spektrum):

```python
import numpy as np
import plotly.graph_objects as go

# Nach FFT
freq = np.fft.rfftfreq(len(signal), 1.0 / fs)
magnitude = np.abs(np.fft.rfft(signal))

# Option A: update_figure mit Listen/NumPy (NumPy wird automatisch konvertiert)
data = [{"x": freq, "y": magnitude, "mode": "lines", "name": "Spektrum"}]
layout = {"xaxis": {"title": "f (Hz)"}, "yaxis": {"title": "|X|", "type": "log"}}
widget_registry[path_id].update_figure(data, layout)

# Option B: go.Figure
fig = go.Figure(data=[go.Scatter(x=freq, y=magnitude, mode="lines")], layout=go.Layout(...))
widget_registry[path_id].update_from_figure(fig)
```

---

## 9. Scattergl (WebGL)

Für flüssigere Animationen und große Punktmengen kann **scattergl** statt scatter genutzt werden: gleiche API, Trace-Typ `scattergl`. Plotly rendert dann per WebGL.

- **Aufwand:** Gering. In den Trace-Daten `type: "scattergl"` setzen (oder im Layout-Builder eine Option „WebGL“ / `use_webgl`).
- **Sinnvoll für:** Echtzeit-Plots, viele Punkte (>1000), 60 Hz Updates.
- **Einschränkung:** Browser begrenzen WebGL-Kontexte pro Seite (typisch 4–8); bei vielen Plotly-Figuren mit scattergl kann eine ältere Figur den Kontext verlieren.

**Beispiel (user_template):** `PLOT_SCATTERGL=1` setzen; die Sinus-Demo nutzt dann `type: "scattergl"` im Trace.

---

## 10. Referenzen

- Widget-Implementierung: `lab_suite/widgets/plotly_graph.py`, `plotly_graph.js`
- Widget-README: `lab_suite/widgets/README.md` (Abschnitt PlotlyGraph)
- Layout-Format: `lab_suite/app_builder/layout_format.md` (Plot-Widgets)
- Callbacks/Setters: `lab_suite/app_builder/docs/assessment_callbacks_and_setters.md` (Abschnitt Plotly)
- Plotly Layout: https://plotly.com/javascript/reference/layout/
- Plotly Traces: https://plotly.com/javascript/reference/#scatter
- Scattergl: https://plotly.com/javascript/reference/scattergl/
