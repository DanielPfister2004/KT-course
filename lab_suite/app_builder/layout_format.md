# JSON-Layout-Format (App-Builder)

Schnittstelle zwischen Builder (später Drag & Drop) und Laufzeit: Beschreibung des Dashboards in einer einzigen JSON-Datei.

## Grundprinzip

- **Hierarchie:** Dashboard → Container → … → Container (beliebig oft schachtelbar) → Gruppe (optional) → Widget.
- **Container in Container:** Mehrere Ebenen sind ausdrücklich erlaubt (z. B. `top` → `link_budget` → `tx` → Widget). Jeder Container hat `id`, `layout_type` und `children`; in `children` stehen wieder Container, Gruppen oder Widgets.
- **Pfad-ID:** Eindeutiger Bezeichner pro Widget = verkettete IDs mit Punkt: `container_id.group_id.widget_id` (bei Schachtelung: `outer.inner.group_id.widget_id`). Gruppen optional; Widgets direkt im Dashboard: `dashboard.widget_id`.
- **Layout pro Ebene:** Entweder **rows_columns** (NiceGUI Rows/Columns) oder **xy** (absolute Positionierung in px/%).

---

## Feature-Übersicht für Laborübungen

Welche Mittel stehen für das Design von Laborübungen (Dashboard, Oszilloskop, Messplatz, etc.) zur Verfügung?

### Container & Anordnung

| Feature | layout_type / Mittel | Kurzbeschreibung |
|--------|----------------------|-------------------|
| **Zeile** | `rows_columns` | Kinder nebeneinander, Umbruch bei Platzmangel (z. B. Toolbar). |
| **Spalte** | `column` | Kinder untereinander (z. B. linkes Panel). |
| **Raster** | `grid` | Kinder in Zeilen/Spalten; `columns` (und optional `rows`), optional pro Kind `col_span` / `row_span`. |
| **Aufklappbar** | `expansion` | Bereich mit Titel, Inhalt ein-/ausklappbar. |
| **Scroll** | `scroll` | Scrollbarer Bereich (z. B. lange Control-Liste); `style.max-height` für sichtbaren Scroll. |
| **Karte** | `card` | Karten-Container (Rahmen, Schatten). |
| **Splitter** | `splitter` | Zwei Bereiche mit verschiebbarer Trennlinie; `orientation` (horizontal/vertical), `value` (0–100 %). |
| **Tabs** | `tabs` | Tab-Leiste; Kinder = Tab-Knoten mit je `label` und `children`. |
| **Absolut** | `xy` | Container mit `position: relative`; Kinder mit `position.left/top` (px/%). |

### Gruppierung & Struktur

- **Gruppe** (`type: "group"`): logische Gruppe mit optionalem `label`, nur Widgets als Kinder.
- **Verschachteln:** Container in Container beliebig tief (z. B. Zeile → links Card mit Grid, rechts Plot).

### Styling (Container)

- **`style`** an jedem Container: `background-color`, `padding`, `border-radius`, `width`, `height`, `max-height`, etc. (CSS-ähnlich).

### App-Oberfläche (appearance)

Optionales Objekt **`appearance`** auf Layout-Root (neben `version` und `dashboard`): Vorgaben für Seiten- und Container-Optik. Der Renderer wendet sie wie folgt an:

- **Seite:** Wird die gesamte UI in einen Wrapper mit `page_padding` und `page_background` gepackt (falls gesetzt).
- **Container:** Jeder Container (row, column, grid, …) erhält **Vorgabewerte** für Hintergrund, Padding, Abstand (gap) und Ecken (border-radius). Einzelne Container können diese per eigenem `style` überschreiben.

| Schlüssel | Beispiel | Wirkung |
|-----------|----------|---------|
| `page_padding` | `"16px"` | Padding um die gesamte App |
| `page_background` | `"#fafafa"` | Hintergrundfarbe der Seite |
| `container_background` | `"#f0f0f0"` | Vorgabe: Hintergrund aller Container (z. B. Zeilen) |
| `container_padding` | `"12px"` | Vorgabe: Padding in Containern |
| `container_gap` | `"0.5rem"` | Vorgabe: Abstand zwischen Kindern (CSS gap) |
| `container_border_radius` | `"8px"` | Vorgabe: abgerundete Ecken |

In der **Development-App** gibt es im Edit-Modus den Tab **„App-Oberfläche“**, um diese Werte zu setzen; sie werden in `layout.json` unter `appearance` gespeichert und vom Renderer ausgewertet. So erzielt man ohne pro-Container-Pflege ein einheitliches, professionelles Erscheinungsbild (dezent hinterlegte Zeilen/Container, einheitliche Abstände).

### Styling (Widgets – gemeinsame Props)

- **Breite/Flex:** `width`, `min_width`, `max_width`, `flex` (z. B. Plot mit `flex: true` füllt Restplatz).
- **Farben:** `text_color`, `bg_color` (Hex oder Picker).

### Widget-Typen (Auswahl)

- **Eingabe:** `checkbox`, `toggle_button` (Icon + optional Text, aktiv/inaktiv mit Ausgrauen/Durchstreichen), `slider`, `button`, `input`, `number_input`, `select`.
- **Anzeige:** `label`, `led`, `vu_meter`, `image`, `link`, `table`.
- **Plots:** `plotly_spectrum`, `plotly_graph`, `plotly_scatter`, `plotly_histogram`, `plotly_3d`.
- **Custom:** `gain_control_vue`, `image_icon_demo`, etc.

### Typisches Muster (z. B. Oszilloskop)

- **Außen:** `rows_columns` oder `splitter` (links Controls, rechts Display).
- **Links:** `scroll` + `card` + `grid` mit vielen Controls (feste Breite, gleiches Erscheinungsbild).
- **Rechts:** ein Plot-Widget mit `flex: true` und ggf. fester Mindesthöhe.

---

## Schema (Überblick)

```json
{
  "version": 1,
  "dashboard": { "id": "dashboard", "layout_type": "rows_columns", "children": [...] },
  "appearance": {
    "page_padding": "16px",
    "page_background": "#fafafa",
    "container_background": "#f0f0f0",
    "container_padding": "12px",
    "container_gap": "0.5rem",
    "container_border_radius": "8px"
  }
}
```

`appearance` ist optional; alle Schlüssel darin sind optional.

---

## Knotentypen

### 1. Dashboard (Root)

| Feld          | Typ     | Pflicht | Beschreibung |
|---------------|---------|--------|--------------|
| `version`     | number  | ja     | Layout-Format-Version (1) |
| `dashboard`   | object  | ja     | Root-Container |
| `appearance`  | object  | nein   | Vorgaben für Seiten- und Container-Optik (siehe „App-Oberfläche“) |

### 2. Dashboard-Objekt

| Feld          | Typ     | Pflicht | Beschreibung |
|---------------|---------|--------|--------------|
| `id`          | string  | ja     | Immer `"dashboard"` oder App-Name |
| `layout_type` | string  | ja     | `"rows_columns"` \| `"xy"` |
| `children`    | array   | ja     | Liste von Container oder Widget |

### 3. Container

| Feld          | Typ     | Pflicht | Beschreibung |
|---------------|---------|--------|--------------|
| `type`        | string  | ja     | `"container"` |
| `id`          | string  | ja     | Eindeutige ID (Buchstaben, Ziffern, `_`) |
| `label`       | string  | nein   | Anzeige (z. B. Expansion-Titel) |
| `layout_type` | string  | ja     | `"rows_columns"` \| `"column"` \| `"grid"` \| `"xy"` \| **`"expansion"`** \| **`"scroll"`** \| **`"card"`** \| **`"splitter"`** \| **`"tabs"`** |
| `children`    | array   | ja     | **Container, Gruppe, Tab oder Widget** (siehe unten). Bei `expansion`: Inhalt; bei `tabs`: nur **Tab**-Knoten; bei **splitter**: genau **2** Kinder (erstes = links/oben, zweites = rechts/unten). |
| `columns`     | number \| string | nein  | Nur bei **`layout_type: "grid"`**: Anzahl Spalten (z. B. `2`, `3`) oder CSS `grid-template-columns` (z. B. `"auto 1fr 2fr"`). Default: `2`. |
| `rows`        | number \| string | nein  | Nur bei **`layout_type: "grid"`**: optional Anzahl Zeilen oder CSS `grid-template-rows`. |
| `orientation` | string  | nein   | Nur bei **`layout_type: "splitter"`**: `"horizontal"` (links/rechts) oder `"vertical"` (oben/unten). Default: `"horizontal"`. |
| `value`       | number  | nein   | Nur bei **`layout_type: "splitter"`**: Anteil des ersten Bereichs in Prozent (0–100). Default: `30`. |
| `col_span` / `row_span` | number | nein | Nur wenn dieser Container **direktes Kind eines Grid-Containers** ist: Zelle spannt über N Spalten/Zeilen (Default 1). |
| `align_items` | string  | nein   | Nur bei **`layout_type: "rows_columns"`**: vertikale Ausrichtung der Kinder. `"start"` = oben, `"center"` = mitte (Standard), `"end"` = unten, `"stretch"` = strecken. |
| `style`       | object  | nein   | CSS-ähnlich: z. B. `{"width": "700px", "height": "200px"}` für xy; **für alle layout_type:** `{"background-color": "#f0f0f0", "padding": "12px", "border-radius": "8px"}` für einheitlichen Hintergrund und Abstand. Bei **scroll** z. B. `{"max-height": "300px"}` für sichtbaren Scroll. |

- **`layout_type: "rows_columns"`** → Eine Zeile (NiceGUI `ui.row`), Kinder nebeneinander, bei Platzmangel Umbruch (flex-wrap). **`align_items`** steuert die vertikale Ausrichtung (z. B. `"start"` für oben bündig).
- **`layout_type: "column"`** → Eine Spalte (NiceGUI `ui.column`), Kinder untereinander.
- **`layout_type: "grid"`** → Raster (NiceGUI `ui.grid`): Kinder werden in **Zeilen und Spalten** platziert (nicht nur zeilenweise). `columns` (und optional `rows`) steuern das Layout; Kinder füllen das Grid der Reihe nach (links→rechts, dann nächste Zeile). **Grid-Spans:** Jedes **Kind** eines Grid-Containers kann optional `col_span` und/oder `row_span` (Zahlen, Default 1) haben – z. B. `"col_span": 2` spannt über 2 Spalten.
- **`layout_type: "expansion"`** → Aufklappbarer Bereich (NiceGUI `ui.expansion`). `label` = Titel der Expansion, `children` = Inhalt beim Aufklappen.
- **`layout_type: "scroll"`** → Scrollbarer Bereich (NiceGUI `ui.scroll_area`). Für lange Listen oder Control-Panels; mit `style` z. B. `{"max-height": "300px"}` die sichtbare Höhe begrenzen.
- **`layout_type: "card"`** → Karten-Container (NiceGUI `ui.card`). Eigenes Karten-Layout (Rahmen, Schatten); `style` optional für zusätzliche Anpassung.
- **`layout_type: "splitter"`** → Verschiebbare Trennlinie (NiceGUI `ui.splitter`). **Genau 2 Kinder:** erstes = links bzw. oben, zweites = rechts bzw. unten. `orientation`: `"horizontal"` oder `"vertical"`; `value`: Anteil des ersten Bereichs in Prozent (0–100).
- **`layout_type: "tabs"`** → Tab-Leiste. `children` = Liste von **Tab**-Knoten (siehe 3b); jeder Tab hat einen eigenen Titel und Inhalt.

**Flex-Container mit einheitlicher Hintergrundfarbe:** Bei `rows_columns`, `column`, `grid`, `expansion`, `scroll`, `card` und `splitter` wird `style` auf einen Wrapper angewendet. Beispiel für eine Zeile mit grauem Hintergrund und Abstand:

```json
{ "type": "container", "id": "toolbar", "layout_type": "rows_columns", "style": { "background-color": "#e8e8e8", "padding": "12px", "border-radius": "8px" }, "children": [...] }
```

### 3a. Professionell wirkende Layouts (native Mittel)

- **Container-Hintergrund:** `style` mit `background-color`, `padding`, `border-radius` für klare Blöcke (siehe oben).
- **Abstände:** `gap-*`-Klassen im Renderer oder zusätzliche Container mit Padding; konsistente Werte (z. B. 12px, 16px).
- **Breite/Flex der Widgets:** Gemeinsame Props `width`, `min_width`, `max_width`, `flex` (siehe Widget-Props) – z. B. zwei Slider mit `flex: true` teilen die Zeile; Buttons mit fester `width` wirken aufgeräumt.
- **Farben:** Gemeinsame Props `text_color`, `bg_color` (Hex oder Picker) für Akzente; zurückhaltende Hintergründe (#f5f5f5, #eee) für Container, kräftige nur für CTAs.
- **Struktur:** Wenige Ebenen (Dashboard → wenige rows_columns/column → Widgets), klare Gruppierung mit Expansion oder Tabs für komplexere Bereiche.
- **Kein Extra-Framework nötig:** Alles über layout.json (`style` an Containern, gemeinsame Widget-Props) und ggf. wenig eigenes CSS (z. B. `ui.add_head_html` für globale Schrift/Abstand).

### 3b. Tab (nur als Kind eines Containers mit `layout_type: "tabs"`)

| Feld       | Typ   | Pflicht | Beschreibung |
|------------|-------|--------|--------------|
| `type`     | string| ja     | `"tab"` |
| `id`       | string| ja     | Eindeutige ID innerhalb des Tabs-Containers |
| `label`    | string| ja     | Tab-Reiter-Beschriftung |
| `children` | array | ja     | Container, Gruppe oder Widgets (Inhalt dieses Tabs) |

### 4. Gruppe

| Feld          | Typ     | Pflicht | Beschreibung |
|---------------|---------|--------|--------------|
| `type`        | string  | ja     | `"group"` |
| `id`          | string  | ja     | Eindeutige ID innerhalb des Containers |
| `label`       | string  | nein   | Optional Anzeige |
| `children`    | array   | ja     | Nur Widgets |

### 5. Widget

| Feld         | Typ     | Pflicht | Beschreibung |
|--------------|---------|--------|--------------|
| `type`       | string  | ja     | `"widget"` |
| `id`         | string  | ja     | Eindeutige ID innerhalb Parent |
| `widget_type`| string  | ja     | Siehe Widget-Typen unten |
| `props`      | object  | ja     | Typ-spezifische Properties (value, min, max, label, …) |
| `position`   | object  | nein   | Nur bei Parent mit `layout_type: "xy"`: `{"left": "10px", "top": "20px", "z_index": 2}` |
| `col_span`   | number  | nein   | Nur als **direktes Kind eines Grid-Containers**: Zelle spannt über N Spalten (Default 1). |
| `row_span`   | number  | nein   | Nur als **direktes Kind eines Grid-Containers**: Zelle spannt über N Zeilen (Default 1). |

**Pfad-ID des Widgets:** `parent_id.widget_id` (rekursiv über alle Ebenen). Bei geschachtelten Containern z. B. `top.link_budget.tx.power` (Dashboard → top → link_budget → tx → Widget power).

---

## Widget-Typen und `props` (Beispiele)

| widget_type      | Typ/Beschreibung | Beispiel-Props |
|------------------|-------------------|----------------|
| `checkbox`       | bool              | `{"label": "Run", "value": false}` |
| **`toggle_button`** | bool (aktiv/inaktiv) | `{"icon": "play_arrow", "label": "Run", "label_inactive": "", "value": false, "strikethrough_inactive": true}` – Icon (Material-Icon-Name), optional Text aktiv/inaktiv; inaktiv = ausgegraut + optional diagonale Durchstreichung. |
| `slider`         | float/int         | `{"label": "Gain", "min": 0, "max": 10, "value": 1, "step": 0.01, "label_position": "below|above|inline"}` – optional `label_width`/`control_width` (z. B. `80px`, `120px`) für Inline-Layout. |
| `button`         | click             | `{"label": "Reset"}` |
| `number_input`   | number            | `{"label": "Freq (Hz)", "value": 440}` |
| **`input`**      | **Text**          | `{"label": "Tx Power [dBm]", "value": "10"}` – einzeilige Texteingabe (ui.input). |
| **`select`**     | **Dropdown**      | `{"label": "Input", "options": [], "value": null}` – Dropdown-Auswahl; Optionen oft von der App gesetzt. |
| `gain_control_vue`| float (Gain)     | `{"label": "Gain", "min": 0, "max": 10, "value": 1}` – Vue-Widget (lab_suite/widgets); Slider + Anzeige + Reset. |
| `vu_meter`       | Anzeige float     | `{"value": 0, "min": 0, "max": 1, "show_value": true, "width": "120px", "height": "80px"}` – Vue-Widget; Anzeige, App schreibt Wert. |
| `led`            | state             | `{"state": "off", "label": "Status", "size": 18}` – Vue-Widget; Zustand off/on/warning/error. |
| `image_icon_demo`| Anzeige           | `{"image_src": "", "image_alt": "Image", "show_icon": true, "label": ""}` – Vue-Widget; Bild + optional Inline-Icon. |
| `label`          | nur Text          | `{"text": "Titel"}` |
| **`plotly_spectrum`** | Plot (Plotly)   | `{"height": "400px", "title": "Spektrum"}` – Anzeige; Figur wird von der App gesetzt (update_figure). |
| **`plotly_graph`**    | generischer Plot | `{"height": "400px"}` – beliebige Plotly-Figur; data/layout von der App. |
| **`plotly_scatter`**  | X-Y / Scatter   | `{"height": "400px", "title": "X-Y"}` – semantischer Hinweis; technisch wie plotly_graph, App liefert z. B. go.Scatter(mode='markers'). |
| **`plotly_histogram`**| Histogram       | `{"height": "400px", "title": "Histogram"}` – semantischer Hinweis; App liefert z. B. go.Histogram. |
| **`plotly_3d`**       | 3D-Plot         | `{"height": "500px"}` – Plotly unterstützt 3D (go.Scatter3d, go.Surface, go.Mesh3d); App liefert Figur mit 3D-Traces. |
| **`table`**           | Tabelle         | `{"columns": [{"name": "Spalte A", "field": "a"}], "rows": []}` – Spaltendefinition im Layout; Zeilendaten typisch von der App/State. |
| **`image`**           | Rastergrafik    | `{"src": "/static/photo.png", "alt": "Beschreibung", "width": "200px", "height": "auto"}` – Bild-URL (relativ/absolut), Alt-Text, optionale Größe. |
| **`link`**            | Hyperlink       | `{"url": "https://example.com", "text": "Link-Text", "target": "_blank"}` – Klickbarer Link; `text` = Anzeige, optional `target` (_blank, _self). |
| **`video`** / **`youtube`** | Video (Einbettung/Verlinkung) | `{"url": "https://www.youtube.com/watch?v=...", "embed": true}` – Bei `embed: true` Einbettung (iframe); bei `embed: false` nur Verlinkung (wie `link`). Optional `width`, `height` für Embed. |

**Dropdown:** Bereits abgebildet als Widget-Typ **`select`** (options, value); Optionen können im Layout oder von der App zur Laufzeit gesetzt werden.

**Tabellen:** Widget-Typ **`table`** – Spalten in `props.columns`, Zeilendaten oft aus State oder App (z. B. `model.state[path_id]` = Liste von Zeilen). Optional Callback bei Zeilenauswahl.

**Plot-Widgets (Plotly):** Werden in der Architektur mit abgebildet. Plotly unterstützt auch **3D-Plots** (Scatter3d, Surface, Mesh3d, Cone); die App übergibt wie bei 2D eine Figur mit den gewünschten Traces – technisch über `plotly_graph`, optional semantisch `plotly_3d`. **X-Y (Scatter), Histogram, Liniendiagramme, Balken** etc. werden alle unterstützt: Die App übergibt eine Plotly-Figur mit den gewünschten Traces (z. B. `go.Scatter` für X-Y/Scatter, `go.Histogram` für Histogramme, `go.Bar`). `plotly_graph` ist der generische Typ; `plotly_scatter` und `plotly_histogram` sind optionale semantische Hinweise im Layout (gleiche Laufzeit-Behandlung, nur andere widget_type-Kennung). Sie sind überwiegend **Ausgabe**: Die App schreibt die Figur (z. B. aus DSP/Ergebnissen) in das Widget; optional können Events wie `relayout` oder `click` einen Callback auslösen (`on_<path_id>_relayout`). Im Modell-State wird typischerweise **kein** vollständiger Figure-Inhalt persistiert, sondern nur die App-Daten, aus denen die Figur gebaut wird – das Plot-Widget erhält die Pfad-ID zur Referenz (z. B. für `build_ui` / Update-Schleife).

**Mehrere Traces / Multi-Channel:** Ein Plot-Widget entspricht **einer** Plot-Fläche (einer Pfad-ID). Der **Inhalt** der Figur wird vollständig von der App bestimmt. Die App kann dabei beliebig viele **Traces** und ggf. **Subplots** nutzen, z. B.:
- **Spektrum + Max-Hold:** Zwei (oder mehr) Traces in derselben Figur – z. B. aktuelle Magnitude + persistente Peak-Werte (Max-Hold), beide von der User-Logik berechnet und in `fig.data` eingetragen.
- **Oszilloskop, mehrere Kanäle:** Mehrere Traces für Kanal 1, 2, 3, … (Time-Domain); die App liefert pro Kanal eine Spur und füllt `fig.data` entsprechend.
- **Mehrere Subplots:** Falls gewünscht, kann die App eine Figur mit mehreren Achsen (z. B. Plotly `make_subplots`) bauen und an dasselbe Widget übergeben.

Das Layout legt nur fest, **wo** und mit welcher Pfad-ID die Plot-Fläche sitzt; **was** gezeichnet wird (Anzahl Traces, Max-Hold-Logik, Kanalzuordnung), liegt in der User-Logik.

---

## Bild, Hyperlink, YouTube/Video

**Bilder (Rastergrafik):** Widget-Typ **`image`** – `props.src` (URL, z. B. `/static/…` nach `add_static_files`), `props.alt`, optional `props.width`/`props.height`. Kein State nötig (reine Anzeige); wenn die App die URL wechseln soll, kann sie das Widget per Referenz aktualisieren oder `src` aus State befüllen.

**Bild mit Beschriftung in einer Box:** Container mit optionalem `style` (Rahmen, Padding) als „Box“, darin z. B. zuerst Widget **`image`**, darunter Widget **`label`** mit `props.text` als Beschriftung – Reihenfolge in `children` entscheidet (oben/unten). Beispiel:

```json
{
  "type": "container",
  "id": "photo_box",
  "layout_type": "rows_columns",
  "style": {"border": "1px solid #ccc", "border-radius": "8px", "padding": "8px"},
  "children": [
    { "type": "widget", "id": "photo", "widget_type": "image", "props": {"src": "/static/diagram.png", "alt": "Schema", "width": "300px"} },
    { "type": "widget", "id": "caption", "widget_type": "label", "props": {"text": "Abb. 1: Blockschema"} }
  ]
}
```

**Hyperlinks als eigenes Widget:** Ja. Widget-Typ **`link`** – `props.url`, `props.text` (angezeigter Text), optional `props.target` (`_blank` für neuen Tab). Eigenständiges Widget mit Pfad-ID; kein State nötig (reine Navigation). Für dynamische URLs kann die App das Link-Widget per Referenz setzen oder die URL aus State lesen.

**YouTube / Video:** Widget-Typ **`video`** oder **`youtube`** – `props.url` (z. B. YouTube-Watch-URL), `props.embed` (boolean): bei `true` Einbettung als iframe (typisch für YouTube), bei `false` nur klickbarer Link (wie `link`). Optionale `props.width`, `props.height` für die Embed-Box. YouTube-URLs können in Embed-URL umgesetzt werden (z. B. `https://www.youtube.com/embed/<id>`).

Für jeden Typ mit **Wert** wird ein Eintrag im Modell-State angelegt (Key = Pfad-ID). Für `button` nur ein Callback (on_click). Für Plot-Widgets optional State/Callbacks wie oben.

---

## Aufklappbare Bereiche (Expansion), Tabs, Tabellen, Dropdown

| Element        | Abbildung in der Struktur |
|----------------|----------------------------|
| **Aufklappbarer Bereich** | Container mit `layout_type: "expansion"`; `label` = Titel, `children` = Inhalt (wird beim Aufklappen angezeigt). |
| **Tabs**       | Container mit `layout_type: "tabs"`; `children` = Liste von **Tab**-Knoten (siehe Abschnitt „3b. Tab“). |
| **Einzelner Tab** | Knoten `type: "tab"` mit `id`, `label` (Reiter-Text), `children` (Inhalt des Tabs). Widgets in Tabs erhalten Pfad-IDs wie `container_id.tab_id.widget_id`. |
| **Dropdown**   | Widget `widget_type: "select"` mit `props.options`, `props.value` (bereits in der Widget-Tabelle). |
| **Tabelle**    | Widget `widget_type: "table"` mit `props.columns` (Spaltendefinition); Zeilendaten typisch von App/State. |

---

## Marker-/Spektrum-Parameter (SNR, Band-Leistung, etc.)

**Marker-Einstellungen** (z. B. Frequenz-Marker 1/2 für Spektrum, Start/Stop, Center/Span) sind **normale Widgets** (`number_input`, `slider`) mit eigenen Pfad-IDs. Sie stehen der User-Logik vollständig zur Verfügung:

- **Lesen:** In Callbacks oder in der Update-Schleife z. B. `f1 = model.state["spectrum_markers.freq_1"]`, `f2 = model.state["spectrum_markers.freq_2"]` für SNR, Band-Leistung, Marker-Anzeige im Plot.
- **Schreiben:** Die App kann Werte setzen (z. B. nach Laden); die GUI zeigt sie an, wenn das Widget an `model.state` gebunden ist.
- **Persistenz:** Die Werte liegen im gemeinsamen State und werden mit `save_state`/`load_state` gespeichert (Session).

**Empfohlene Pfad-ID-Konvention** für Marker, damit die User-Logik einheitlich zugreifen kann:

| Zweck              | Beispiel-Pfad-IDs |
|--------------------|-------------------|
| Frequenz-Marker 1/2| `spectrum_markers.freq_1`, `spectrum_markers.freq_2` |
| Start/Stop         | `spectrum_markers.start`, `spectrum_markers.stop`   |
| Center/Span        | `spectrum_markers.center`, `spectrum_markers.span`  |

Im Layout einen Container (z. B. `spectrum_markers`) mit diesen Widgets anlegen; die User-Logik liest dann z. B. in der Update-Schleife die Marker und berechnet Band-Leistung/SNR oder aktualisiert die Plot-Shapes.

---

## Callback-Namenskonvention

- **Änderung eines Werts:** `on_<path_id_snake>_change(value)`  
  Beispiel: Pfad-ID `top.run` → `on_top_run_change(value: bool)`.
- **Button-Klick:** `on_<path_id_snake>_click()`  
  Beispiel: `top.reset_gain` → `on_top_reset_gain_click()`.
- **Plotly Relayout (Zoom/Pan):** optional `on_<path_id_snake>_relayout(relayout_data)`.
- Pfad-ID mit Punkt wird zu Snake-Case für Python: `top.gain_block.gain` → `on_top_gain_block_gain_change`.

### Was dem User in den Callbacks zur Verfügung steht

| Verfügbar | Beschreibung |
|-----------|--------------|
| **`value`** (nur bei `*_change`) | Der neue Wert: bei `checkbox` → `bool`, bei `slider`/`number_input`/`gain_control_vue` → `float`, bei `input`/`select` → `str` bzw. gewählter Optionen-Wert. |
| **Bei `*_click`** | Keine Argumente. |
| **Bei `*_relayout`** | Ein Argument: `relayout_data` (Plotly-Relayout-Daten, z. B. Zoom/Pan). |
| **path_id** | Nur in der Docstring-Zeile des generierten Callbacks (z. B. `"""Path-ID: row_1.widget_2. ..."""`), nicht als Parameter. Zur Identifikation des Widgets. |

**Nicht an den Callback übergeben** (aber in der App vorhanden):

| Nicht übergeben | Wo verfügbar |
|------------------|--------------|
| Widget-Props (z. B. `label`, `min`, `max`, `options`) | Im Layout unter `layout["dashboard"]` → Knoten mit `props`; per `get_widget_node_by_path_id(layout, path_id)` (app_builder) erreichbar. |
| State (alle Werte) | In der Development-App: State-Dict wird an `build_ui_from_layout` übergeben; Zugriff z. B. über die gleiche Referenz, die die App beim Aufbau hält (z. B. `model.state` / geladener State). Im Skeleton-Kommentar: „Access state via model.state['path_id']“. |
| `widget_type` | Im Layout-Knoten: `node["widget_type"]` (über `get_widget_node_by_path_id`). |
| **Widget-Registry** (Output-Widgets) | Optional: `build_ui_from_layout(..., widget_registry=dict)` befüllt das Dict mit `path_id → Instanz` für **led**, **vu_meter** (später plotly). In der Development-App: `ui.context.client.widget_registry` nach dem Aufbau; z. B. `ui.context.client.widget_registry["row_2.widget_13"].set_state("on")` oder `.set_value(0.5)` für VU-Meter. |
| **user_id** (Prop pro Widget) | Optionale Prop **User-ID** (gemeinsam für alle Widgets): Wenn gesetzt (z. B. `power`, `gain`), wird daraus **automatisch** SEMANTIC_BINDING (gui_binding) erzeugt – Studenten setzen nur im Property-Editor die User-ID, dann `gui_binding.get("power")` / `gui_binding.set("led_status", "on")` ohne manuelles Dict. Im Edit-Modus zeigt Hover path_id und user_id. |

---

## Beispiel (minimal)

```json
{
  "version": 1,
  "dashboard": {
    "id": "dashboard",
    "layout_type": "rows_columns",
    "children": [
      {
        "type": "container",
        "id": "top",
        "label": "Steuerung",
        "layout_type": "rows_columns",
        "children": [
          {
            "type": "widget",
            "id": "run",
            "widget_type": "checkbox",
            "props": {"label": "Run", "value": false}
          },
          {
            "type": "widget",
            "id": "test_generator",
            "widget_type": "checkbox",
            "props": {"label": "Test-Generator", "value": false}
          },
          {
            "type": "widget",
            "id": "gain",
            "widget_type": "slider",
            "props": {"label": "Gain", "min": 0, "max": 10, "value": 1}
          }
        ]
      }
    ]
  }
}
```

Daraus entstehen: State-Keys `top.run`, `top.test_generator`, `top.gain` und Callbacks `on_top_run_change`, `on_top_test_generator_change`, `on_top_gain_change`.

---

## Erweiterbarkeit: Display-Widgets und externe Shapes

**Ja.** Die Architektur ist bewusst erweiterbar:

- **Neue Display-Widgets** (Balken, Batterie-Ladestand, beliebige Anzeigen) können jederzeit ergänzt werden, sofern die Darstellung per **HTML/CSS** oder als **Vue-/NiceGUI-Komponente** verfügbar ist: Neuen `widget_type` (z. B. `bargraph`, `battery`) in der Widget-Tabelle und im Laufzeit-Renderer (build_ui / Widget-Registry) anlegen, gleiche Schnittstelle (Pfad-ID, State, optional Callbacks). Props bleiben typ-spezifisch (z. B. `value`, `max`, `color`).
- **Shapes aus externen Tools:** SVG/Assets, die mit externen Tools (Design-Programme, SVG-Editoren, Icon-Libs) erstellt wurden, lassen sich nutzen, indem man entweder (a) ein **neues Widget** definiert, das diese Assets per URL oder eingebettetem Markup rendert, oder (b) einen generischen Typ wie `custom_svg`/`image` mit `props.src` oder `props.markup` vorsieht. Die Laufzeit rendert dann HTML/CSS bzw. die zugehörige Vue-Komponente.
- **Einheitliche Schnittstelle:** Jedes zusätzliche Widget braucht eine klare Zuordnung Pfad-ID ↔ State (falls wertgesteuert) und optional Callbacks; dann passen Persistenz, Callback-Skeleton und Modell wie bei den bestehenden Typen.

Kurz: Alle Display-Widgets und Shapes sind leicht erweiterbar, sofern die Darstellung (HTML/CSS oder Komponente) bereitsteht; externe Tools können jederzeit genutzt werden, indem neue `widget_type`-Einträge und die zugehörige Render-Logik ergänzt werden.

---

## Animation und Sichtbarkeit (programmatische Steuerung)

**Ja.** Beides ist generell möglich, ohne dass das Layout-Format dafür extra Felder braucht:

- **Animation:** Die Laufzeit/User-App hält Referenzen auf die erzeugten Widgets (z. B. über eine Widget-Registry mit Pfad-ID). In Timer- oder Event-Callbacks kann die App beliebige Eigenschaften **programmatisch** ändern: z. B. `widget.style("left: 100px; top: 50px;")` und `widget.update()` für Bewegung; wiederholte Updates ergeben Animation (wie im use_case_template mit der Punkt-Animation). CSS-Animationen (keyframes) können bei eigenen Vue/HTML-Widgets genutzt werden; bei NiceGUI-Elementen steuert die App die Änderungen per `.style()`/`.update()`.

- **Sichtbarkeit und z-index:** Ebenfalls per programmatischer Steuerung: `widget.style("z-index: 5;")`, `widget.style("opacity: 0;")` oder `widget.style("display: none;")` und `widget.update()`. So lassen sich Überlagerung (z-index) und Ein-/Ausblenden (opacity, visibility, display) von der User-Logik aus steuern. Im Layout kann bei `layout_type: "xy"` pro Widget optional `position.z_index` vorgegeben werden; dynamische Änderung bleibt in der App.

Die Spezifikation beschreibt nur die **Struktur** (Layout, Pfad-IDs, State, Callbacks). Animation und dynamische Sichtbarkeit/z-index sind **Implementierungsdetails** der Laufzeit und der User-Logik (Referenzen auf Widgets, Timer/Events, `.style()`/`.update()`).

---

## Workflow: app.py, layout.json, Callbacks, Modell

**Assessment zu Callbacks vs. Settern:** Welche Mechanismen für **Input** (Callbacks) und **Output** (LED, VU-Meter, Plotly setzen/plotten) bestehen und wo Lücken sind, ist in **app_builder/docs/assessment_callbacks_and_setters.md** beschrieben.

- **app.py** wird **unverändert** als Einstieg genutzt: lädt `layout.json`, lädt State aus `model_schema`, holt die Callback-Registry aus `callback_skeleton`, baut die NiceGUI mit `build_ui_from_layout(layout, state, callbacks)` und hängt Save-on-Disconnect an. Keine Geschäftslogik in app.py.
- **User-Logik:** Entweder in **callback_skeleton.py** (wird beim erneuten Generieren überschrieben) oder besser in **user_callbacks.py**: Skeleton mit Option **„User-Modul (user_callbacks)“** generieren – dann importiert callback_skeleton nur aus user_callbacks; user_callbacks.py wird **nicht** überschrieben, deine Edits bleiben erhalten.
- **layout.json** ist die einzige Beschreibung der Oberfläche (Container, Tabs, Widgets, Pfad-IDs). Wird das Layout geändert oder erweitert, generiert der App-Builder **model_schema.py** und **callback_skeleton.py** neu (`python -m app_builder.skeleton layout.json --out <app_dir> --model`); danach ergänzt der User nur die neuen Callbacks in callback_skeleton.py.
- **Nächster Schritt:** Erstellung von **layout.json** mit einem **visuellen Builder-Tool** (Drag & Drop), das das JSON und optional den Skeleton-Aufruf ausgibt, statt die Datei von Hand zu schreiben.

---

## Nächste Schritte (nach dem Grundgerüst)

Mit Layout-Schema, Skeleton-Generator, Renderer und development_app-PoC steht das **Grundgerüst**. Umgesetzt sind u. a.:

- **Generischer Layout-Renderer** (app_builder/renderer.py): Container (rows_columns, column, grid, expansion, scroll, card, splitter, tabs), Gruppen, alle spezifizierten Widgets inkl. input, gain_control_vue, vu_meter, led, image_icon_demo; Grid-Kinder mit col_span/row_span; State und Callbacks pro Pfad-ID; reaktive State-Anzeige. **Widget-Registry:** optionaler Parameter `widget_registry` (Dict), wird mit path_id → Instanz für led, vu_meter befüllt (später plotly); User kann Setter (`set_state`, `set_value`, `update_figure`) aufrufen.
- **Code-Export (Deployment-Option):** Aus layout.json kann **statischer Python-Code** erzeugt werden (app_builder/code_export.py), der dieselbe UI mit reinen NiceGUI-Aufrufen baut – **ohne** Renderer und ohne layout.json in der ausgelieferten App. Nutzung: `python -m app_builder.code_export layout.json -o deployed_ui.py`; in der Ziel-App: `from deployed_ui import build_ui` dann `build_ui(ui, state, callbacks, title="...")`. State- und Callback-Schnittstelle bleibt gleich.
- **Test-Layout** in development_app mit Expansion, Tabs und Widget-Demo.

**Als nächster Schritt empfohlen:**

- **Visueller Builder:** Tool (z. B. Drag & Drop), mit dem **layout.json** erstellt/bearbeitet wird und das optional den Skeleton-Generator aufruft. Ausgabe: layout.json (+ ggf. aktualisierte callback_skeleton.py / model_schema.py). **Skizze:** siehe `app_builder/visual_builder_sketch.md`.

**Optional danach:**  
- use_case_template schrittweise mit diesem Layout nachbauen.  
- Widget-Registry (Referenzen pro path_id) für programmatische Updates (VU-Meter, LED, Plot-Figuren).
