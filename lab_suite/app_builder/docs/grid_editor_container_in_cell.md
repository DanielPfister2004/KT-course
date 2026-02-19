# Grid-Editor: Container in einer Zelle (Skizze)

**Ziel:** Eine Zelle im Grid kann nicht nur ein **Widget** sein, sondern auch ein **Container** (z. B. Expansion, Card, Column, Scroll). Der Container hat `children` (Widgets oder weitere Container), die im Editor konfigurierbar sind.

---

## 1. Erweiterung des Zellenmodells

### Aktuell (Stufe 1)
- **Zelle** = `None` | **Widget-Spec** (`type: "widget"`, `widget_type`, `props`, …).
- `grid_to_layout`: Pro Zeile ein Container `rows_columns`, `children` = nur Widgets.
- `layout_to_grid`: Liest nur Layouts, in denen jede Zeile nur Widgets enthält; bei verschachteltem Container → `None` (nicht grid-kompatibel).

### Erweitert (Stufe 2)
- **Zelle** = `None` | **Widget-Spec** | **Container-Spec**.
- **Container-Spec:** `type: "container"`, `layout_type` (z. B. `"expansion"`, `"card"`, `"column"`, `"scroll"`), `id`, ggf. `label` (Expansion), `children: [ … ]`.
- `children` eines Containers in einer Zelle: Liste von **Widgets** (und optional weiterer Container, siehe Abschnitt 4).

**Datenmodell (grid_model):**
- `Cell = None | dict` bleibt; das Dict kann sein:
  - `type == "widget"` → wie bisher (Widget-Spec).
  - `type == "container"` → Container-Spec mit `layout_type`, `id`, `label` (falls nötig), `children`.
- Hilfsfunktionen: `def is_widget(cell): ...`, `def is_container(cell): ...`, `def get_container_children(container_cell): ...`.

---

## 2. Serialisierung: grid_to_layout

- Beim Durchlauf der Zeilen/Zellen:
  - **Leer (None):** überspringen (wie bisher).
  - **Widget:** `children.append(copy.deepcopy(cell))` (wie bisher).
  - **Container:** `children.append(copy.deepcopy(cell))` – das gesamte Container-Dict (inkl. `children`) wird übernommen.
- Ergebnis: `dashboard.children` = Liste von Zeilen-Containern (`rows_columns`); jede Zeile hat `children` = Mix aus **Widgets** und **Containern**. Das ist mit der bestehenden layout.json-Architektur und dem Renderer kompatibel, da der Renderer in `_render_node` sowohl `type == "widget"` als auch `type == "container"` (mit `layout_type`) verarbeitet. Beim Rendern einer Zeile werden die Kinder rekursiv gerendert – Widgets als Widgets, Container (Expansion, Card, …) mit ihren eigenen Kindern.

---

## 3. Deserialisierung: layout_to_grid

- Bisher: Nur Layouts, in denen jede Zeile nur Widgets enthält.
- Erweitert: Beim Lesen einer Zeile (`rows_columns.children`):
  - Wenn `node.type == "widget"` → wie bisher, ein Widget in die Zelle.
  - Wenn `node.type == "container"` und `layout_type` in der erlaubten Liste (z. B. `expansion`, `card`, `column`, `scroll`) → Container-Knoten in die Zelle übernehmen (inkl. `children`).
  - Wenn `node.type == "container"` mit anderem `layout_type` (z. B. `rows_columns`, `tabs`) → optional unterstützen oder als „nicht grid-kompatibel“ ablehnen (wie bisher bei beliebigen Containern).
- So bleibt **Load** deterministisch: Layouts, die vom erweiterten Grid exportiert wurden, lassen sich wieder laden; Layouts mit nicht unterstützten Strukturen weiterhin `None`.

---

## 4. UI im Grid-Editor (app.py)

- **Palette:** Zusätzlich zu den Widgets eine Gruppe **„Container“** mit Einträgen wie **Expansion**, **Card**, **Column**, **Scroll** (und optional Splitter, Tabs).
- **Zelle befüllen:** Bei Klick auf „Expansion“ (o. Ä.) wird in die aktive Zelle ein **Container-Spec** eingetragen (z. B. aus `CONTAINER_DEFAULTS["expansion"]`), `id` generieren, `children: []`.
- **Anzeige der Zelle:** Wenn die Zelle ein Container ist, z. B. Kurzlabel: `[Expansion]` oder `[Expansion: 1 Kind]` (Anzahl Kinder).
- **Auswahl + Property-Panel:** Wenn die aktive Zelle ein **Container** ist:
  - Eigene Props des Containers bearbeiten: `label` (Expansion), `layout_type` (read-only), ggf. `style`.
  - **Kinder verwalten:** Liste der `children` – für jedes Kind Anzeige (Widget-Typ oder Container-Typ), Buttons „Bearbeiten“, „Entfernen“, „Hinzufügen (Widget/Unter-Container)“.
- **Kinder hinzufügen:** Für den ausgewählten Container ein weiteres Kind einfügen: Auswahl „Widget“ (z. B. Markdown, Button, …) oder „Container“ (z. B. nur Column/Scroll, um Verschachtelung begrenzt zu halten). Neues Kind wird an `container["children"].append(...)` angehängt.
- **Verschachtelungstiefe:** Empfehlung: In einer Zelle nur **ein** Container; dessen `children` nur **Widgets** (keine weiteren Container). So bleibt die UI überschaubar und das Modell einfach. Optional später: Container in Container (z. B. Expansion → Column → Widgets) mit fester Maximaltiefe.

---

## 5. Nutzung für andere Container-Typen

Das Feature „Zelle = Widget oder Container“ ist **generisch** und kann für alle im Layout-Modell vorhandenen Container-Typen genutzt werden:

| layout_type   | NiceGUI-Element | Sinnvoll in Zelle? | Anmerkung |
|---------------|-----------------|--------------------|-----------|
| **expansion**  | `ui.expansion`  | Ja                 | Aufgabenstellung, aufklappbare Hilfe. |
| **card**      | `ui.card`       | Ja                 | Gruppierte Blöcke (z. B. Karte mit Slider + Button). |
| **column**    | `ui.column`     | Ja                 | Vertikaler Stapel in einer Zelle. |
| **scroll**    | `ui.scroll_area`| Ja                 | Längerer Inhalt (z. B. Markdown) mit Scroll. |
| **rows_columns** | `ui.row`      | Eher nein          | Redundant (Zeile ist schon eine Row). |
| **grid**      | `ui.grid`       | Optional           | Nested Grid; erhöht Komplexität. |
| **splitter**  | `ui.splitter`   | Ja, mit Einschränkung | Genau 2 Kinder nötig; UI muss 2 Slots anbieten. |
| **tabs**      | `ui.tabs`       | Ja                 | Kinder = Tab-Knoten (mit je `children`); etwas mehr UI-Logik. |

**Empfehlung für die erste Umsetzung:** Nur **expansion**, **card**, **column**, **scroll** als wählbare „Container in Zelle“. Splitter/Tabs optional in einer zweiten Phase.

---

## 6. Native Container-Typen (NiceGUI / Browser)

### In unserem Layout-Modell (CONTAINER_DEFAULTS / layout_format)
- **rows_columns** → NiceGUI `ui.row` (flex, flex-wrap)
- **column** → NiceGUI `ui.column`
- **grid** → NiceGUI `ui.grid`
- **expansion** → NiceGUI `ui.expansion` (Quasar QExpansionItem)
- **scroll** → NiceGUI `ui.scroll_area` (Quasar scroll-area)
- **card** → NiceGUI `ui.card` (Quasar QCard)
- **splitter** → NiceGUI `ui.splitter` (Quasar QSplitter)
- **tabs** → NiceGUI `ui.tabs` / `ui.tab_panels` (Quasar QTabs)
- **group** → kein eigenes NiceGUI-Container-Element; logische Gruppe mit Label, Renderer baut z. B. column + Label
- **tab** → Teil von tabs (Tab + Tab-Panel)

### Weitere NiceGUI-/Quasar-Elemente (nicht zwingend im Layout)
- **ui.element("div")** – generisches Block-Element (Browser `div`)
- **ui.html()** – beliebiges HTML (für spezielle Fälle)
- Quasar: **QDialog**, **QDrawer**, **QMenu**, **QToolbar**, **QBar** – eher Overlays/Navigation als „Layout-Container“ im Grid

### Browser-nativ (ohne NiceGUI-Wrapper)
- **div**, **section**, **article**, **aside**, **main**, **header**, **footer** – alle als Block-Container nutzbar; unser Layout nutzt sie indirekt über NiceGUI/Quasar.

**Fazit:** Die für den Grid-Editor relevanten Container sind die bereits im Layout-Modell abgebildeten: **expansion**, **card**, **column**, **scroll**, **grid**, **splitter**, **tabs**. Das Feature „Container in Zelle“ kann für alle diese Typen einheitlich genutzt werden; die Einschränkung (z. B. nur expansion/card/column/scroll zuerst) ist eine Reduktion der UI-Komplexität, nicht der Architektur.

---

## 7. Kompatibilität mit layout.json

- **Export:** Das aus dem Grid erzeugte Layout ist ein gültiges layout.json: `dashboard.layout_type == "column"`, `dashboard.children` = Liste von Containern mit `layout_type: "rows_columns"`, jede Zeile hat `children` = Array aus **Widgets** und **Containern**. Jeder Container hat dieselbe Struktur wie in layout_format beschrieben (`type`, `layout_type`, `id`, `label` ggf., `children`).
- **Import:** Der Renderer ändert sich nicht; er traversiert bereits rekursiv und rendert jeden Knoten nach `type` (widget vs. container) und `layout_type`. Layouts mit „Container in Zeile“ werden also korrekt gerendert.
- **Roundtrip:** Grid → layout.json → Save → Load → layout_to_grid → Grid-State: Wenn nur unterstützte Container in Zellen vorkommen und `layout_to_grid` wie in Abschnitt 3 erweitert wird, ist der Roundtrip gewährleistet.

---

## 8. Implementierungsreihenfolge (Vorschlag)

1. **grid_model:** `Cell`-Typ erweitern (Widget | Container); Hilfsfunktionen; `grid_to_layout` um Container-Zellen erweitern; `layout_to_grid` um erlaubte Container in Zeilen erweitern (whitelist: expansion, card, column, scroll).
2. **grid_editor app.py:** Palette um „Container“-Gruppe ergänzen (Expansion, Card, Column, Scroll); Platzieren eines Containers in Zelle; Anzeige der Zelle als `[Expansion]` o. Ä.; Property-Panel für Container (label, children-Liste); Kinder hinzufügen/entfernen (nur Widgets als Kinder in Phase 1).
3. **Optional:** Container-Kinder auch als Container erlauben (z. B. Expansion → Column → Widgets), mit fester Maximaltiefe; Splitter/Tabs in der Palette.

Damit ist das Feature für Expansion und alle anderen genannten Container-Typen nutzbar und mit der layout.json-Architektur kompatibel.

---

## Workflow: Anordnung von Widgets innerhalb einer Expansion

### Ziel: z. B. 2 Zeilen × 3 Spalten in einer Expansion

**Option A – Ein Grid-Container (empfohlen):**
1. Zelle mit **Expansion** platzieren, Label setzen (z. B. „Aufgaben & Steuerung“).
2. Bei der Expansion auf **„Add child“ → Container → Grid** klicken → die Expansion hat jetzt ein Kind „grid“.
3. **„Edit“** beim Kind „grid“ klicken (Drill-Down) → das Property-Panel bearbeitet nun den Grid-Container.
4. Optional: Spaltenzahl des Grids anpassen (z. B. 3), siehe Container-Props falls angeboten.
5. **„Add child (widget)“** sechsmal ausführen → die 6 Widgets füllen das Grid **zeilenweise** (erste Zeile: 1–3, zweite Zeile: 4–6). Reihenfolge = Anordnung.

**Option B – Zwei Zeilen (rows_columns):**
1. Expansion platzieren.
2. **Add child → Container → rows_columns** (erste Zeile).
3. **Edit** bei diesem „rows_columns“ → jetzt Kinder dieser Zeile bearbeiten. Drei Widgets hinzufügen → erste Zeile mit 3 Spalten.
4. **Back** → zurück zur Expansion.
5. **Add child → Container → rows_columns** (zweite Zeile).
6. **Edit** bei der zweiten rows_columns → drei Widgets hinzufügen → zweite Zeile mit 3 Spalten.

### Anordnungsmöglichkeiten (Reihenfolge der Children)

| Container-Typ   | Bedeutung der Kinder-Reihenfolge |
|-----------------|-----------------------------------|
| **column**      | Untereinander (1 Spalte). |
| **rows_columns**| Nebeneinander, mit Umbruch (Zeile, flex-wrap). |
| **grid**        | Raster: Kinder füllen Zeile für Zeile, Spaltenzahl aus Container-Prop `columns`. |
| **expansion**   | Beim Aufklappen: Kinder untereinander (oder gemäß eigenem Layout). |
| **card, scroll**| Kinder typisch untereinander. |

Es wird **kein zweiter Grid-Editor** für Kind-Container benötigt: Stattdessen **Drill-Down** – im Property-Panel bei einem Kind-Container auf **„Edit“** wechseln, dann werden dessen Kinder gelistet und „Add child“ fügt dort hinzu. **„Back“** zurück zur übergeordneten Ebene.
