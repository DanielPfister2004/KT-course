# Übungskonzept: Template-GUI + Signalgenerator + Oszilloskop/Spektrum/XY-Plot

Kunde/User (Student) soll mit **wenig Zeitaufwand** auf die **fachliche Arbeit** fokussieren: vorgegebene GUI, klare Zuordnung Widget ↔ physikalische Variable, Übungsinhalt in Python (moduliertes Signal erzeugen, darstellen, analysieren). Später: eigene Widgets/Callbacks/Variablen ergänzen.

**Frage:** Kann dieses Konzept realisiert werden, wenn eine **durchgängige Widget-Registry** eingeführt wird?

**Antwort:** **Ja.** Mit Widget-Registry, Plotly im Renderer und einem festen Template-Layout ist das Übungskonzept realisierbar. Die nachfolgenden Abschnitte skizzieren die Zuordnung und die Erweiterungen (Stubs mit Beispielcode).

---

## 1. Anforderungen aus dem Übungskonzept

| Anforderung | Bedeutung |
|-------------|-----------|
| **Wenig Zeitaufwand** | Fertige GUI (Template), keine Layout-Arbeit; Student konzentriert sich auf Signalverarbeitung. |
| **Klare Zuordnung** | Welches Widget = welche physikalische Variable (Level, Frequenz, Bandbreite, …). |
| **Eingaben** | Signalgenerator: Level, Frequenz; Filter: Bandbreite; ggf. weitere (Modulationstyp, Trägerfrequenz, …). |
| **Übungsinhalt** | In Python: moduliertes Signal erzeugen, dann darstellen und analysieren. |
| **Ausgaben** | Oszilloskop (Zeit), Spektralanalysator (Frequenz), XY-Plot (Zeigerdiagramm); Marker, deren Werte von der GUI ausgelesen werden. |
| **Später** | Studenten fügen eigene Widgets hinzu, verknüpfen Callbacks, ergänzen eigene Variablen. |
| **Stubs** | In Callback-Stubs optional **kommentierter Beispielcode** (z. B. wie man den Widget-Wert liest/schreibt). |

---

## 2. Realisierbarkeit mit durchgängiger Widget-Registry

### 2.1 Was die Registry liefert

- **Eingabe-Widgets (slider, number_input, checkbox, …):** Werte laufen bereits über **State**; Callbacks schreiben `state[path_id] = value`. Zum **Lesen** braucht der Student entweder direkten State-Zugriff oder Getter (z. B. `get_frequency()` → `state["sig_gen.frequency"]`). Registry für Input ist optional (z. B. um programmatisch Werte zu setzen).
- **Ausgabe-Widgets (LED, VU-Meter):** Registry `path_id → Instanz` erlaubt `registry["panel.vu_meter"].set_value(level)`.
- **Plot-Widgets (Oszilloskop, Spektrum, XY-Plot):** Registry `path_id → PlotlyGraph` erlaubt `registry["panel.oscilloscope"].update_figure(data, layout)` bzw. `update_from_figure(fig)`.

Mit einer **einheitlichen** Registry (alle Output- und Plot-Widgets, optional auch Input) hat der Student einen **einzigen Zugangsweg**: `registry[path_id]` für Setter/Plots; State (oder Getter) für Lesen der Eingaben.

### 2.2 Template-Layout mit fester Semantik

- **Template** = vordefiniertes `layout.json` mit **festen, semantischen IDs** (nicht nur `widget_1`, `widget_2`), z. B.:
  - `sig_gen.level`, `sig_gen.frequency` (Signalgenerator)
  - `filter.bandwidth` (Filterbandbreite)
  - `display.oscilloscope`, `display.spectrum`, `display.xy_plot` (Plots)
  - `markers.freq_1`, `markers.freq_2` oder `markers.level_1` (Marker als number_input/slider, Werte aus GUI auslesbar)
- Dann können **Getter** stabil benannt werden: `get_signal_level()`, `get_signal_frequency()`, `get_bandwidth()`, `get_marker_freq_1()`, … und im Übungstext steht klar: „Die Frequenz des Signalgenerators ist das Widget `sig_gen.frequency` / die Funktion `get_signal_frequency()`.“

### 2.3 Ablauf aus Studentensicht (mit Registry)

1. **Template starten** → GUI erscheint (Oszilloskop, Spektrum, XY-Plot, Slider für Level/Frequenz/Bandbreite, ggf. Marker-Eingaben).
2. **Parameter setzen** → Callbacks (dünn) schreiben in State; Student liest in seiner Logik per State oder Getter: Level, Frequenz, Bandbreite.
3. **Moduliertes Signal in Python erzeugen** → Student schreibt Code (z. B. in `app_logic.py` oder in einem „Übungs“-Modul), nutzt Getter/State, erzeugt Zeitserie.
4. **Resultat darstellen** → Student ruft z. B. `registry["display.oscilloscope"].update_figure(time_trace)` oder `update_from_figure(fig)`; analog für Spektrum (FFT) und XY (Zeigerdiagramm).
5. **Marker** → Entweder als **Widgets** (number_input/slider) mit festen path_ids: Student liest `state["markers.freq_1"]` / `get_marker_freq_1()`; oder Marker kommen aus Plot-Interaktion (relayout/click), dann müssten Werte in State geschrieben werden, damit „von GUI ausgelesen“ einheitlich bleibt. Für Übung reicht: Marker = Eingabefelder, die der Student in seiner Auswertung liest.
6. **Später:** Eigene Widgets im Layout hinzufügen (Grid-Editor), Skeleton neu generieren → neue Callback-Stubs; Student verknüpft Callbacks, ergänzt State/Getter für neue Variable.

### 2.4 Fazit Realisierbarkeit

| Baustein | Mit Widget-Registry | Anmerkung |
|----------|---------------------|-----------|
| Level, Frequenz, Bandbreite setzen | ✅ State + Callbacks (vorhanden); Getter optional | Klare Zuordnung über Template-IDs. |
| Moduliertes Signal in Python erzeugen | ✅ Kern liest State/Getter | Kein GUI-Code nötig. |
| Oszilloskop / Spektrum / XY-Plot | ✅ Registry → `update_figure` / `update_from_figure` | Plotly im Renderer + Registry nötig. |
| Marker-Werte „von GUI auslesen“ | ✅ State oder Getter für Marker-Widgets | Marker als normale Input-Widgets mit fester path_id. |
| Später: eigene Widgets, Callbacks, Variablen | ✅ Layout anpassen, Skeleton neu generieren | Callback-Stubs mit Beispielcode (s. u.). |

**Das Übungskonzept ist mit durchgängiger Widget-Registry realisierbar.**

---

## 3. Callback-Stubs mit kommentiertem Beispielcode

Damit Studenten sofort sehen, „wie man den Wert dieses Widgets nutzt“, können die generierten Stubs **kommentierten Default-Code** enthalten, z. B.:

```python
# widget: sig_gen.frequency (path_id: sig_gen.frequency)
def on_sig_gen_frequency_change(value: Any) -> None:
    """Path-ID: sig_gen.frequency. Callback args: value: float"""
    # Beispiel: Wert in State schreiben (wird von App-Logik gelesen)
    # state["sig_gen.frequency"] = value
    # Optional: Kern-Logik anstoßen
    # app_logic.update_signal_params()
    pass
```

Für ein **Plot-Widget** (wenn Registry verfügbar ist) könnte ein Stub so aussehen (in einer Übungs-App, die Registry an die Callbacks übergibt oder global bereitstellt):

```python
# Beispiel: Oszilloskop-Plot aktualisieren (z. B. aus Timer/Update-Schleife)
# plot = registry["display.oscilloscope"]
# plot.update_figure(data=[{"x": t, "y": y}], layout={"title": "Zeitsignal"})
# oder: plot.update_from_figure(fig)  # fig = go.Figure()
```

Der Skeleton-Generator könnte pro Widget-Typ (slider, number_input, button, plotly_*) eine **optionale Vorlage** (kommentierte Zeilen) einfügen, die der Student entkommentiert oder als Referenz nutzt. So bleibt der Fokus auf der fachlichen Arbeit; die „Verbindung“ Widget ↔ Variable ist im Stub sichtbar.

---

## 4. Kurz: Abhängigkeiten für die Umsetzung

**Erster Schritt: Widget-Registry.** Alle weiteren Schritte (Plotly im Renderer, Template, Stubs mit Beispielcode) bauen darauf auf.

- **Widget-Registry** (durchgängig): `build_ui_from_layout` füllt optional ein Dict `path_id → Instanz` für Output- und Plot-Widgets (und ggf. Input). **← zuerst umsetzen.**
- **Plotly im Renderer:** Zweige für `plotly_graph` (und ggf. `plotly_spectrum`, …), Erzeugung + Eintrag in Registry.
- **Template layout.json:** Feste, semantische IDs (z. B. `sig_gen.*`, `filter.*`, `display.*`, `markers.*`) und vordefinierte Plots (Oszilloskop, Spektrum, XY).
- **Getter-Layer (optional):** Modul mit `get_signal_frequency()`, `get_bandwidth()`, `get_marker_freq_1()` etc., die auf State bzw. feste path_ids zugreifen – dann ist die fachliche Variable im Code klar benannt.
- **Skeleton:** Option „Stub mit kommentiertem Beispielcode“ pro Widget-Typ (State schreiben, ggf. Registry/Plot-Update).

Mit diesen Schritten ist das beschriebene Übungskonzept (Template-GUI, physikalische Variablen, moduliertes Signal, Oszilloskop/Spektrum/XY, Marker aus GUI, später Erweiterung durch Studenten) realisierbar.
