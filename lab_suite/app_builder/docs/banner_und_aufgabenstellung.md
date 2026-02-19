# Banner + Aufgabenstellung (Markdown-Expansion) – Optionen

**Ziel:** Ganz am Anfang der Seite (1) einen fixen Banner mit konfigurierbaren Texten, (2) eine Expansion, die beim Ausklappen einen Markdown-Text aus `assignments/assignment_01_description.md` (zum aktiven Assignment passend) anzeigt.

---

## Option 1: Alles im Layout (Grid-Editor) – nur bestehende Bausteine

**Idee:** Banner = erste Zeile (Container `rows_columns`) mit einem oder mehreren **Label-Widgets** (Text konfigurierbar über props). Aufgabenstellung = **Expansion-Container** als zweites Kind mit **einem neuen Widget** „assignment_description“ darin, das den Markdown-Inhalt aus einer Datei lädt.

| Aspekt | Bewertung |
|--------|-----------|
| **Banner** | Kein neuer Typ nötig: eine Zeile mit Label(s), Text in `props.text`, ggf. Styling über `props` (bg_color, text_color). Im Grid-Editor anlegen und verschieben. |
| **Expansion** | Bereits vorhanden: Container mit `layout_type: "expansion"`, `label` z. B. „Aufgabenstellung“. |
| **Markdown-Inhalt** | **Ein neuer Widget-Typ** `assignment_description`: Props z. B. `assignment_key` (z. B. `"assignment_01"`) oder optional `markdown_file` (relativer Pfad). Renderer lädt `assignments/{assignment_key}_description.md` und rendert mit `ui.markdown(content)`. |
| **Aufwand** | Gering: layout_model um einen Eintrag, Renderer um einen `elif widget_type == "assignment_description"` (mit optionalem Parameter `assignments_dir: Path` an `build_ui_from_layout`). App übergibt `Path(__file__).parent / "assignments"`. |
| **Sauberkeit** | Sehr gut: Alles im Layout definiert, Grid-Editor kann Banner-Zeile und Expansion anpassen (Reihenfolge, Texte, welches Assignment). Keine Sonderlogik in app.py. |

**Fazit Option 1:** Minimaler Zusatz: **ein** neues Widget `assignment_description`, Banner und Expansion sind normales Layout. Sauber und mit wenig Code umsetzbar.

---

## Option 2: Layout-Root-Keys (banner + assignment_description)

**Idee:** Im Layout-JSON auf Root-Ebene optionale Keys, z. B. `banner: { "lines": ["Titel", "Untertitel"] }` und `assignment_description: "assignment_01"`. Der **Renderer** (oder die App) rendert **vor** `dashboard.children`: zuerst Banner (z. B. eine Zeile mit Labels), dann eine Expansion; den Markdown-Inhalt lädt die App aus `assignments/assignment_01_description.md` und übergibt ihn an den Renderer.

| Aspekt | Bewertung |
|--------|-----------|
| **Banner** | Renderer oder App liest `layout.banner` und baut eine feste Zeile (z. B. `ui.row()` mit `ui.label(...)` pro Eintrag). Kein neues Widget. |
| **Expansion** | Renderer oder App baut eine Expansion, Inhalt = übergebener Markdown-String (von App aus Datei gelesen). |
| **Konfiguration** | Im Layout: `banner`, `assignment_description`. Im Grid-Editor müsste man einen eigenen Bereich „Seiten-Optionen“ / „Banner“ anbieten, sonst wird das JSON von Hand gepflegt. |
| **Aufwand** | Gering: Erweiterung von `build_ui_from_layout` (oder ein Stück UI in app.py vor dem Aufruf). Optional: `build_ui_from_layout(..., banner_lines=..., assignment_markdown=...)`; App füllt diese aus `layout` + Datei. |
| **Sauberkeit** | Gut: Klare Trennung Konfiguration (Layout) vs. Inhalte (Datei). Banner/Expansion sind aber **nicht** als normale Kinder im Grid sichtbar/verschiebbar. |

**Fazit Option 2:** Schnell umsetzbar, Banner/Expansion sind jedoch „Sonderbereich“ und nicht Teil der normalen Container-/Widget-Struktur im Editor.

---

## Option 3: Nur in der App (app.py) vor dem Layout

**Idee:** Die App rendert **vor** `build_ui_from_layout` fest: eine Banner-Zeile (Text z. B. aus Konstante oder aus `layout.banner`) und eine Expansion mit Markdown aus `assignments/{aktives_assignment}_description.md`. Das Layout enthält nur das bisherige `dashboard.children`.

| Aspekt | Bewertung |
|--------|-----------|
| **Banner / Expansion** | Alles in app.py: Reihenfolge und Aufbau fest verdrahtet. Konfiguration nur über Layout-Keys oder Code. |
| **Aufwand** | Sehr gering: ein paar Zeilen in app.py (Banner, Expansion, Datei lesen, `ui.markdown`). |
| **Sauberkeit** | Weniger sauber: Keine einheitliche „alles im Layout“, Banner/Expansion nicht im Grid-Editor bearbeitbar. Dafür keine Renderer-/Modell-Änderung. |

**Fazit Option 3:** Sehr wenig Code, aber wenig flexibel und nicht im Layout-Editor abbildbar.

---

## Option 4: Banner + Expansion als „normales“ Layout, Markdown-Widget neu

**Idee:** Wie Option 1, aber das neue Widget heißt z. B. `markdown` und hat eine Prop `source: "assignment"` bzw. `assignment_key: "assignment_01"` (oder `file_path`). Der Renderer rendert für dieses Widget den Inhalt aus der zugehörigen Datei. Banner weiterhin eine normale Zeile mit Labels.

| Aspekt | Bewertung |
|--------|-----------|
| **Gleich wie Option 1** | Nur andere Namensgebung (markdown vs. assignment_description). Technisch identisch. |

---

## Empfehlung

**Option 1 (Layout mit einem neuen Widget „assignment_description“):**

1. **Banner:** Kein neuer Typ – im Layout die **erste Zeile** (Container `rows_columns`) mit **Label-Widget(s)**. Texte und ggf. Styling vollständig im Grid-Editor konfigurierbar.
2. **Expansion:** **Zweites Kind** des Dashboards = Container mit `layout_type: "expansion"`, z. B. `label: "Aufgabenstellung"`, `children: [ { type: "widget", widget_type: "assignment_description", props: { "assignment_key": "assignment_01" } } ]`.
3. **Neues Widget einmalig:** Im Renderer `widget_type == "assignment_description"` → Datei `assignments/{assignment_key}_description.md` lesen (Pfad von der App an `build_ui_from_layout` übergeben), Inhalt mit `ui.markdown(...)` anzeigen. In layout_model ein Default-Eintrag für `assignment_description` mit Prop `assignment_key`.

**Vorteile:** Minimaler Aufwand (ein Widget, ein Renderer-Branch, optionaler Parameter), alles im Layout und im Grid-Editor bearbeitbar, klare Zuordnung Assignment ↔ `assignment_XX_description.md`.

**Alternative**, wenn man bewusst **keine** neuen Widget-Typen will: **Option 2** (Root-Keys `banner` und `assignment_description` im Layout, Renderer oder App baut Banner + Expansion vor den Children). Dann ist der Banner nicht als „erste Zeile“ im Grid sichtbar, aber konfigurierbar über JSON.

---

## Erweiterung Option 1: Banner als Vue-Komponente + Markdown/KaTeX-Widget

### 1. Banner als Vue-Komponente (moderne Optik, Symbole, Verläufe, Animationen)

**Idee:** Statt einer einfachen Zeile mit Label-Widgets ein **eigenes Vue-Widget** „Banner“ (z. B. `banner_vue`), das du – wie in anderen Projekten – mit modernen Symbolen, Farbverläufen und optionalen Animationen gestaltest. Im Layout wird es wie jedes andere Widget eingebunden (z. B. erste Zeile = eine Row mit einem `banner_vue`-Widget).

| Kriterium | Bewertung |
|-----------|-----------|
| **Passung zu Option 1** | Sehr gut: Ein weiterer Widget-Typ im Layout, im Grid-Editor platzierbar und verschiebbar. Keine Sonderlogik. |
| **Wiederverwendung** | Du hast bereits ansprechende Banner als Vue-Komponenten; diese lassen sich als `banner.js` + `banner.py` (NiceGUI Element) in `lab_suite/widgets` übernehmen. Props z. B. `title`, `subtitle`, `gradient`, `animated` – je nach bestehendem Design. |
| **Konfiguration** | Über Layout-Props wie bei GainControlVue: Texte, Farben, „animated“ etc. im Property-Editor bearbeitbar. Kein Hardcoding. |
| **Aufwand** | Gering, wenn die Vue-Komponente schon existiert: (1) `.js`/`.py` in `widgets/`, (2) Eintrag in layout_model (WIDGET_DEFAULTS + Palette), (3) Renderer-Branch `elif widget_type == "banner_vue":` mit Instanziierung und Weitergabe der Props. Neue Komponente von Grund auf: mittlerer Aufwand (Vue-Template, ggf. CSS/Animationen). |
| **Risiken** | Wie bei GainControlVue: Events (falls Banner klickbar etc.) sauber mit `@change.stop` o. Ä. abfangen, wenn nötig. Ansonsten Standard-Vue-Integration. |
| **Sauberkeit** | Sehr gut: Einheitliches Muster (wie alle anderen Custom-Widgets), keine Ausnahme im Renderer. |

**Fazit Banner-Vue:** Sehr gut in Option 1 integrierbar. Bestehende Banner-Komponente einbinden ist schnell; dann wirkt die App konsistent modern und professionell.

---

### 2. Markdown + KaTeX als „normales“ Widget (erklärende Texte, Formeln)

**Idee:** Ein **allgemeines Widget** „Markdown“ (z. B. `markdown` oder `rich_text`), das einen Markdown-Text mit **LaTeX-Formeln (KaTeX)** rendert. Zwei Nutzungsarten:

- **A)** Inhalt aus Datei: Prop `source: "assignment"` + `assignment_key: "assignment_01"` → Renderer lädt `assignments/assignment_01_description.md` (wie bisher „assignment_description“).
- **B)** Inhalt aus Layout: Prop `content` (String) oder `markdown_file` (relativer Pfad) → für kurze erklärende Texte direkt in der GUI (überall platzierbar: neben Slidern, in Expansion, in Tabs).

So können **Aufgabenstellungen** und **beliebige Erklärungstexte mit Formeln** mit demselben Widget und einheitlicher Darstellung (Markdown + KaTeX) realisiert werden.

| Kriterium | Bewertung |
|-----------|-----------|
| **Passung zu Option 1** | Sehr gut: Ein Widget-Typ, zwei Modi (Datei vs. Inline/Dateipfad). Im Grid-Editor überall einfügbar – Aufgabenstellung in Expansion, Kurztexte in beliebigen Containern. |
| **KaTeX** | Du hast KaTeX-Rendering bereits in einem anderen Projekt; technisch: Markdown-String parsen, LaTeX-Blöcke (z. B. `$...$`, `$$...$$`) mit KaTeX rendern. In NiceGUI: entweder (1) `ui.mermaid`-ähnlich ein eigenes Element mit HTML-Ausgabe (Markdown → HTML, KaTeX → HTML) oder (2) vorhandene NiceGUI-/Quasar-Markdown-Komponente prüfen, ob sie KaTeX unterstützt; andernfalls kleines Vue-Widget, das markdown-it (oder ähnlich) + KaTeX einbindet. |
| **Wiederverwendung** | Ein Widget für alle „fließenden Texte mit Formeln“ – Aufgabenstellung, Hinweise, Theorieblöcke. Kein zweites Widget nur für Assignment-Description nötig. |
| **Konfiguration** | **Modus A (Assignment):** `source: "assignment"`, `assignment_key: "assignment_01"` – Renderer lädt Datei, übergibt Inhalt an Widget (oder Widget bekommt schon fertigen String von Renderer). **Modus B (Inline):** `content: "..."` oder `file: "snippets/hinweis.md"` – direkt aus Layout oder aus Datei. Im Property-Editor: bei `content` großer Textbereich oder Dateipfad. |
| **Aufwand** | **Ohne KaTeX:** Gering (NiceGUI `ui.markdown` + ggf. Dateiladen im Renderer). **Mit KaTeX:** Mittlerer Aufwand – entweder Vue-Komponente (markdown-it + KaTeX im Frontend) oder Backend: Markdown → HTML, LaTeX → HTML mit Python-Bibliothek (z. B. markdown + python-katex oder Server-seitig KaTeX), dann `ui.html()` o. Ä. Vue-Variante oft ansprechender (KaTeX ist JS-nativ). |
| **Risiken** | XSS: Nur vertrauenswürdige Inhalte (eigene .md-Dateien, keine User-Inputs ohne Sanitizing). KaTeX-Bibliothek und Markdown-Parser sauber einbinden. |
| **Sauberkeit** | Sehr gut: Ein generisches „Rich-Text mit Formeln“-Widget deckt Aufgabenstellung und Erklärungstexte ab, reduziert Sonderfälle. |

**Fazit Markdown/KaTeX-Widget:** Sinnvolle Erweiterung von Option 1. Ein „markdown“-Widget mit optionalem KaTeX und zwei Modi (assignment-Datei / Inline oder Dateipfad) ist wiederverwendbar und wirkt überall professionell. Implementierungsaufwand hängt an der KaTeX-Integration (Vue vs. Python); Konzept passt gut ins Layout-Modell.

---

### 3. Gesamtbewertung für Option 1

| Baustein | Empfehlung | Aufwand (grob) | Nutzen |
|----------|------------|----------------|--------|
| **Banner** | Als **Vue-Komponente** (`banner_vue`) – bestehende Banner aus anderen Projekten wiederverwenden, im Layout als normales Widget. | Gering (wenn Komponente da) bis mittel (neu bauen) | Moderne, einheitliche Optik; konfigurierbar im Grid-Editor. |
| **Aufgabenstellung / Erklärungstexte** | **Ein** Widget **Markdown (mit optional KaTeX)** – Modus „aus Assignment-Datei“ und Modus „Inline/Datei“ für kurze Texte überall. | Gering (nur Markdown) bis mittel (+ KaTeX, evtl. Vue) | Professionelle Darstellung, Formeln möglich, ein Widget für alle Textbereiche. |

**Reihenfolge für Implementierung:** (1) Banner-Vue einbinden oder anlegen, (2) Markdown-Widget (z. B. zuerst nur Markdown, dann KaTeX ergänzen). Beide als normale Widget-Typen in layout_model und Renderer – Option 1 bleibt erhalten und wird nur um zwei klare, wiederverwendbare Bausteine erweitert.

---

## Kurz-Checkliste: Markdown-Textbox (mit LaTeX/KaTeX)

| Frage | Antwort |
|-------|--------|
| **Ist das Konzept dokumentiert?** | **Ja.** Dieses Dokument beschreibt die Markdown-Textbox (Widget „markdown“ bzw. „assignment_description“) inkl. LaTeX/KaTeX, zwei Modi (Datei vs. Inline/Dateipfad), Konfiguration und Aufwand. |
| **Programmatisches Befüllen (z. B. .md-Datei einlesen)?** | **Ja, vorgesehen.** Modus A: Prop `assignment_key` → Renderer lädt `assignments/{key}_description.md`. Modus B: Prop `content` (String) oder `markdown_file` (relativer Pfad) → Renderer lädt Datei bzw. nutzt String. User kann also eine .md-Datei referenzieren (im Layout oder per assignment_key), der Renderer liest die Datei und befüllt die Anzeige. Optional: `build_ui_from_layout(..., assignments_dir: Path)` bzw. `markdown_base_path` für Pfadauflösung. |
| **Textbox in einer Expansion verpacken?** | **Ja, ohne Zusatzaufwand.** Expansion ist ein normaler Container (`layout_type: "expansion"`, `label`, `children`). Die Markdown-Textbox ist ein normales Widget als Kind. Beispiel: `{ "type": "container", "layout_type": "expansion", "label": "Aufgabenstellung", "children": [ { "type": "widget", "widget_type": "markdown", "props": { "markdown_file": "assignments/assignment_01_description.md" } } ] }`. Im Grid-Editor: Expansion-Container einfügen, darin das Markdown-Widget platzieren. |

**Implementierungsstand:** Das Markdown-/assignment_description-Widget ist im Konzept beschrieben, aber **noch nicht** in `layout_model` (WIDGET_DEFAULTS) oder im Renderer implementiert. Sobald ein Eintrag `markdown` bzw. `assignment_description` und der zugehörige Renderer-Branch (Datei laden, `ui.markdown(content)` oder KaTeX-Variante) existieren, sind alle drei Punkte umsetzbar.
