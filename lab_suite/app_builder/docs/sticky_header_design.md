# Sticky-Header: Integration in Grid-Editor und Architektur

## 0. Banner volle Breite + Sticky-Bereich für globale Schalter

**Frage:** Banner wie gehabt über die gesamte Seitenbreite (flex), darunter ein ebenfalls sticky Bereich mit den globalen Schaltern – ist das möglich? Wie ist die Platzierung der Schalter mit der Architektur möglich?

**Antwort:**

**Ja, beides ist möglich.** Die Struktur sieht dann so aus:

```
┌─────────────────────────────────────────────────────────┐
│  STICKY-BLOCK (position: sticky; ein gemeinsamer Wrapper) │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Zeile 0: Banner (volle Breite, flex wie bisher)     │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Zeile „Schalter“: Edit-Modus, Markdown-Quelltext …  │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Scrollbarer Inhalt: Zeile 2, 3, … aus dem Layout         │
└─────────────────────────────────────────────────────────┘
```

- **Banner volle Breite:** Unverändert. Zeile 0 (`row_0`) hat wie heute ein Kind (z. B. Banner-Widget) mit `flex: true`; der Renderer setzt bereits `flex: 1 1 0; min-width: 0; width: 100%` (s. `renderer.py`). Der Banner bleibt also über die gesamte Breite gezogen.
- **Sticky:** Ein **einziger** Sticky-Wrapper umfasst beide Bereiche: (1) den Inhalt von Zeile 0 (Banner), (2) eine zweite Zeile für die globalen Schalter. Beim Scrollen bleibt der komplette Block oben (Banner + Schalter-Leiste).

**Platzierung der globalen Schalter – zwei Varianten:**

| Variante | Beschreibung | Platzierung im Grid | Aufwand |
|----------|--------------|---------------------|---------|
| **A – Struktur (empfohlen)** | Der Sticky-Block enthält fest: zuerst Zeile 0 (Banner), dann eine **von der App gerenderte** Zeile (nur Schalter). Diese Schalter-Zeile gehört **nicht** zum Layout/Grid. | Keine – die Schalter-Zeile ist immer direkt unter dem Banner, fest im Code. | Gering: Renderer baut „sticky Wrapper → row_0 → Schalter-Zeile (App)“, Rest wie bisher. |
| **B – Layout-Zeile** | Zeile 1 im Layout ist die „Schalter-Zeile“ (`sticky: true`), kann leer sein oder einen Platzhalter haben. Die App injiziert die Schalter in den **Inhalt** dieser Zeile. | Im Grid = Zeile 1; Position der Zeile (über/unter Banner) ist durch die Reihenfolge im Layout festgelegt. | Mittel: Zwei Zeilen mit `sticky: true`, App muss Zeile 1 finden und dort injizieren. |

**Empfehlung Variante A:** Ein Sticky-Wrapper, darin (1) Inhalt von `row_0` (Banner, volle Breite), (2) eine feste zweite Zeile, die die App mit Edit-Modus, Markdown-Quelltext usw. füllt. Keine zusätzliche Layout-Zeile nötig; die Schalter sind immer an derselben Stelle (unter dem Banner). Grid-Editor und `layout_to_grid` bleiben unverändert; nur die **App** (development_app) baut nach dem Rendern von Zeile 0 die Schalter-Zeile in den gleichen Sticky-Wrapper ein.

---

## 1. Berücksichtigung im Grid-Editor

**Aktuell:** `layout_to_grid` erwartet `dashboard.children` = nur Container mit `layout_type: "rows_columns"`. Jeder solche Container = eine Zeile im Grid.

**Empfehlung:** Den Sticky-Bereich **nicht** als eigenen Containertyp einführen, sondern als **Eigenschaft** einer bestehenden Zeile (z. B. der ersten):

- **Option A – Container-Property:** Erste Zeile (z. B. `row_0`) bekommt eine Property `sticky: true` (am Container-Knoten oder unter `props`/`style`). Der Grid-Editor bearbeitet weiterhin Zeilen als `rows_columns`-Container; es kommt nur eine neue Property dazu.
- **Option B – Appearance:** `layout.appearance.sticky_header_row: 0` o. ä. Die erste Zeile wird beim Rendern als sticky gerendert, das Layout-Modell der Zeile bleibt unverändert.

In beiden Fällen bleibt das Layout **grid-kompatibel**: `layout_to_grid` und `grid_to_layout` müssen nur optional `sticky` lesen/schreiben (Option A am Container, Option B in `appearance`). Kein neuer Containertyp nötig.

---

## 2. Instanzierbares Widget?

**Nein.** Der Sticky-Bereich ist ein **Container** (eine Zeile mit `sticky: true`), keine neues Widget. Im Grid-Editor ist es die gleiche Zeile wie heute (z. B. Zeile 0 mit Banner); sie wird nur beim Rendern mit `position: sticky` gerendert. Es ist also derselbe Container, mit einer zusätzlichen Eigenschaft.

---

## 3. Properties wie bei Container

**Ja.** Container haben bereits `style`, `layout_type`, ggf. `props` im Layout-Modell. Eine boolesche Property `sticky` passt gut:

- **Layout-Modell (layout_model):** Bei `rows_columns` (oder allen Container-Typen) optional `sticky: false` als Default.
- **Grid-Editor:** Im Property-Panel für einen **Zeilen-Container** (wenn man die Zeile als Ganzes auswählt) eine Checkbox „Sticky (oben fixieren)“ → schreibt `sticky: true` in den Container-Knoten.
- **grid_to_layout / layout_to_grid:** Beim Konvertieren die Property `sticky` mitnehmen (am jeweiligen Zeilen-Container bzw. in `appearance`).

Damit können wir den Sticky-Bereich genauso mit Properties steuern wie andere Container.

---

## 4. EDIT-MODE-Checkbox im Sticky-Bereich

Zwei Wege:

**Variante 1 – App injiziert Checkbox (geringer Aufwand):**  
Der Sticky-Bereich ist eine normale Zeile mit Inhalt aus dem Layout (z. B. Banner). Die **App** rendert den Sticky-Bereich in zwei Schritten:

1. Sticky-Wrapper mit Inhalt aus dem Layout (Banner etc.) bauen.
2. Danach die globale EDIT-MODE-Checkbox (und ggf. „Markdown Quelltext“) in denselben Wrapper einfügen (z. B. rechts mit `ui.row()` + `ui.space()`).

Dafür muss der Renderer den Sticky-Bereich als **eigenen Block** ausgeben (z. B. erst alle „sticky“-Zeilen in einem Wrapper, dann der restliche Inhalt). Die Checkbox bleibt in der App (z. B. `edit_mode_ref`), wird nur **visuell** in den Sticky-Bereich gesetzt. Kein neues Widget, keine neuen Layout-Knoten.

**Variante 2 – Platzhalter-Widget „global_controls_slot“:**  
Ein neues Widget-Typ `global_controls_slot` wird im Layout in der Sticky-Zeile platziert. Der Renderer erzeugt ein leeres Element und registriert es (z. B. in `widget_registry`). Die App füllt es nach `build_ui_from_layout` mit der EDIT-MODE-Checkbox. Dann kann der Grid-Editor die Position der „globalen“ Leiste im Layout festlegen. Dafür braucht es ein neues Widget in layout_model + Renderer + ggf. Grid-Editor-Palette.

**Empfehlung:** Variante 1 – Sticky-Zeile als eigener Render-Block, App hängt die Checkbox daran. Kein neues Widget, sauber in bestehender Architektur.

---

## 5. Globale Variable für Markdown Quelltext / gerendert

**Ja, passt gut.** Eine globale Variable (z. B. im Client oder in der App) kann den Modus „Quelltext vs. gerendert“ für **alle** Markdown-Widgets steuern:

- **App:** z. B. `show_markdown_source_ref: list[bool] = [True]` und ein Toggle im Sticky-Bereich, der diesen Wert umschaltet.
- **Renderer:** Neuer optionaler Parameter z. B. `get_show_markdown_source: Callable[[], bool] | None`. Bei editierbarem Markdown: wenn gesetzt, wird der angezeigte Modus (Quelltext vs. Vorschau) aus diesem Callable gelesen; die bestehenden Buttons „Quelltext“/„Vorschau“ können ausgeblendet oder durch den globalen Toggle ersetzt werden.
- **Wirkung:** Ein Schalter im Sticky-Header steuert für alle Markdown-Widgets, ob Quelltext oder gerenderter Inhalt gezeigt wird. Eine einzige Referenz, überall genutzt.

---

## Erweiterbarkeit: weitere globale Schalter

**Frage:** Ist es möglich, später weitere globale Schalter hinzuzufügen?

**Ja.** Die Schalter-Zeile wird vollständig von der **App** gerendert (nicht aus dem Layout). Neue Schalter lassen sich jederzeit ergänzen, ohne Layout oder Grid-Editor anzupassen.

**Vorgehen:**

1. **In der App (z. B. development_app/app.py):** In der Stelle, an der die Schalter-Zeile im Sticky-Block gebaut wird, ein weiteres Widget einfügen (z. B. `ui.checkbox(...)`, `ui.toggle(...)` oder `ui.select(...)`).
2. **State/Callback:** Eine neue Ref (z. B. `some_option_ref: list[bool] = [False]`) und ggf. einen Handler anbinden; bei Bedarf den Wert an den Renderer weiterreichen (z. B. als `get_some_option: Callable[[], bool]`), damit andere Widgets (z. B. Markdown, Listen) darauf reagieren können.
3. **Layout/Grid:** Keine Änderung nötig – weder `layout.json` noch Grid-Editor noch Renderer-Layout-Struktur müssen angepasst werden.

**Beispiele für spätere Schalter:** „Alle Expansionen zuklappen“, „Kompakte Ansicht“, „Hilfe-Tooltips an/aus“, themenspezifische Filter usw. Alle leben in derselben Schalter-Zeile (oder in einer weiteren Zeile innerhalb des Sticky-Blocks), zentral in der App gepflegt.

---

## Inhaltshöhe (Scroll-Bereich): fix vs. flexibel

**Problem:** Mit Sticky-Header wird der Bereich unter dem Header in einer `scroll_area` mit fester **max-height** (z. B. `calc(100vh - 180px)`) gerendert. Die Höhe war bisher fix und nicht einstellbar; bei kleinen Viewports oder viel Inhalt wirkt der sichtbare Ausschnitt zu niedrig.

**Lösung:** Zwei Modi über `layout.appearance`, editierbar im Edit-Modus unter **App-Oberfläche** (neben Farben/Padding):

| Option | `scroll_content_mode` | Verhalten | Wann sinnvoll |
|--------|------------------------|-----------|----------------|
| **Fixe Höhe** | `"fixed"` (Default) | Der Bereich unter dem Sticky-Header ist eine `scroll_area` mit **max-height** aus `scroll_area_max_height` (z. B. `calc(100vh - 180px)` oder `80vh`). Nur dieser Bereich scrollt. | Wenn der Sticky-Header immer sichtbar bleiben und der Inhalt in einem „Fenster“ scrollen soll; Höhe anpassbar. |
| **Flexibel** | `"flex"` | Kein max-height; der Inhalt unter dem Sticky-Header fließt in die volle Länge, die **gesamte Seite** scrollt im Browser (wie vor Einführung des Sticky-Headers). | Wenn viel Inhalt da ist und man keine feste „Box“ will; Sticky bleibt oben, Rest der Seite scrollt natürlich. |

**Technisch:**

- **Renderer:** Liest `appearance.scroll_content_mode` und `appearance.scroll_area_max_height`. Bei `fixed`: `scroll_area` mit `style=max-height: <wert>`. Bei `flex`: einfacher `div` (kein max-height), Inhalt wächst, Browser scrollt.
- **Appearance (App-Oberfläche):** Im Tab „App-Oberfläche“: Dropdown „Inhaltshöhe“ (Fixe Höhe / Flexibel) und Eingabe „Scrollbereich max. Höhe“ (nur bei Fixe Höhe), z. B. `calc(100vh - 180px)` oder `80vh`. Werte landen in `layout.json` unter `appearance`.
- **Architektur:** Wie `page_padding`, `page_background` etc.: reine Appearance-Optionen, keine Änderung am Grid oder an Widgets. Default: `scroll_content_mode: "fixed"`, `scroll_area_max_height: "calc(100vh - 180px)"`.

---

## 6. Sauberer Einbau mit geringem Aufwand

| Aspekt | Aufwand | Einordnung |
|--------|---------|------------|
| Sticky = Property einer Zeile (z. B. `sticky: true`) | Gering | Grid bleibt kompatibel, nur Property lesen/schreiben + im Renderer erste Zeile (oder durch `appearance` markierte Zeile) in sticky-`div` wrappen. |
| Properties für Container | Gering | `sticky` im Layout-Modell + optional im Grid-Editor Property-Panel für Zeilen-Container. |
| EDIT-MODE im Sticky | Gering (Variante 1) | Renderer: sticky-Zeile(n) zuerst in einem Block rendern; App hängt danach die bestehende Edit-Mode-Checkbox an diesen Block. Kein neues Widget. |
| Global „Markdown Quelltext“ | Gering | Eine Ref + Toggle in der App, optionaler Parameter `get_show_markdown_source` im Renderer, Markdown-Widget nutzt ihn. |

**Fazit:**  
Sticky als **Container-Property** (eine Zeile mit `sticky: true`), gleiche Properties wie bei anderen Containern, EDIT-MODE durch **App-Injektion** in den Sticky-Block, globale Variable für Markdown-Quelltext mit **einem** Callable-Parameter im Renderer – das passt sauber in die bestehende Architektur und ist mit geringem Aufwand umsetzbar.

---

## Konkrete Schritte (Minimalvariante, mit Banner + Schalter-Zeile)

1. **Layout / Renderer:** `sticky` für Container unterstützen (z. B. nur für die erste Zeile `row_0` oder über `appearance.sticky_header_row`). Beim Rendern: **ein** Sticky-Wrapper (`position: sticky; top: 0; z-index: 50`), darin zuerst der Inhalt von Zeile 0 (Banner, volle Breite wie bisher), dann **kein** weiteres Layout-Element – der Wrapper bleibt offen für App-Inhalt.
2. **App (development_app):** Nach dem Rendern von Zeile 0 (Banner) in den Sticky-Wrapper eine zweite Zeile einfügen (z. B. `ui.row()` mit Edit-Mode-Checkbox, „Markdown Quelltext“-Toggle usw.), dann den Sticky-Wrapper schließen. Anschließend den restlichen Layout-Inhalt (Zeile 1, 2, …) rendern: bei **fixer** Inhaltshöhe (`appearance.scroll_content_mode: "fixed"`) in einer `scroll_area` mit max-height aus `appearance.scroll_area_max_height`, bei **flexibler** Höhe (`scroll_content_mode: "flex"`) in einem einfachen Container, sodass die ganze Seite scrollt.
3. **Renderer:** Optional `get_show_markdown_source` übergeben; editierbare Markdown-Widgets lesen daraus den Anzeige-Modus und blenden ggf. die lokalen Buttons aus.
4. **Grid-Editor:** Optional: im Property-Panel für Zeilen-Container (z. B. nur Zeile 0) eine Checkbox „Sticky“ anbieten und `sticky` in `layout.json` schreiben bzw. bei Import übernehmen.

**Platzierung der globalen Schalter:** Über die **Struktur** – sie stehen immer in der zweiten Zeile des Sticky-Blocks, direkt unter dem Banner, von der App eingefügt. Kein eigenes Layout-Row, keine Grid-Zelle nötig.
