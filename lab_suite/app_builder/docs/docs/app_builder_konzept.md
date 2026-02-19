# App-Builder-Konzept: Prüfung und Klärung

## 1. Bewertung des 6-Stufen-Ansatzes

| Stufe | Bewertung | Kurz |
|-------|-----------|------|
| **1) Primitive Vue-Components** | Sinnvoll | Slider, Button, Checkbox etc. als Vue-Komponenten mit einheitlichem Props/Events-Interface; direkt vom Browser gezeichnet. |
| **2) Erweiterung Standard-Lib** | Sinnvoll | Toggle-Button (Text/Farbe änderbar), Composite-Pattern; baut auf 1 auf. |
| **3) Custom-Widgets (SVG)** | Sinnvoll | VU-Meter, LED, beliebige SVG-Shapes; gleiches Interface wie Primitives (value, on_change, etc.). |
| **4) Container mit absoluter Positionierung** | Sinnvoll | Gruppe von Widgets in einem Container, XY-Positionierung; ermöglicht „Panel“- oder „Rack“-artige Anordnungen. |
| **5) Haupt-Dashboard** | Sinnvoll | Entweder XY-Canvas oder Rows/Columns (NiceGUI); einheitlicher Ort für alle Container/Gruppen. |
| **6) Builder: Canvas + Drag & Drop** | Sinnvoll | Visuelles Anordnen; Export: gemeinsames Modell (Dataclass) + JSON-Persistenz; Skeleton-Callbacks für User-Logik. |

**Fazit:** Der Ansatz ist schlüssig und umsetzbar. Die offenen Punkte betreffen vor allem **Namensgebung**, **Modell-Struktur** und **Trennung GUI vs. User-App**.

---

## 2. Namensgebung (Namespace) bei hierarchischer Anordnung

### 2.1 Hierarchie-Ebenen

- **Dashboard** (Root)
- **Container** (z. B. „Link-Budget-Panel“, „Gain-Block“) – kann selbst einen Namen haben.
- **Gruppe** (optional, z. B. „Marker-Slider“, „Tx-Parameter“) – Unterbereich innerhalb eines Containers.
- **Widget** (Slider, Button, LED, …) – Blattknoten.

Jede Ebene braucht eine **eindeutige ID** im Kontext des Parents, damit Zustand und Callbacks klar zugeordnet werden können.

### 2.2 Vorschlag: Punktierte Pfad-IDs

- **Format:** `container_id.group_id.widget_id` (Gruppe optional).
- **Beispiele:**
  - `gain_block.slider`  → Slider im Container „gain_block“
  - `link_budget.tx.power`  → Widget „power“ in Gruppe „tx“ im Container „link_budget“
  - `dashboard.vu_meter`  → VU-Meter direkt auf dem Dashboard (ohne Container)

**Regeln:**

- IDs nur: Buchstaben, Ziffern, Unterstrich; keine Leerzeichen.
- Eindeutigkeit: innerhalb eines Containers (bzw. einer Gruppe) darf es keine doppelten `widget_id` geben.
- Container-Namen und optionale Gruppen-Namen werden im Builder vergeben und fließen ins Modell ein.

### 2.3 Namenskonflikte vermeiden

- Im Builder: Prüfung auf doppelte IDs beim Erzeugen/Umbenennen.
- Optional: automatische Suffixe (`slider_1`, `slider_2`), wenn der User keinen Namen vergibt.
- Das **gemeinsame Modell** verwendet genau diese Pfad-IDs als Attributnamen oder als Keys in einem Dict (siehe unten).

---

## 3. Gemeinsames Modell (Dataclass) – sinnvolle Namen und Struktur

### 3.1 Zwei Optionen für das Modell

**Option A: Flaches Modell mit Punkt-Namen (einfach, gut erweiterbar)**

```python
@dataclass
class AppModel:
    # Jedes Widget/Container-State-Feld hat einen Namen = Pfad-ID
    gain_block_slider: float = 0.0
    gain_block_vu_value: float = 0.0
    link_budget_tx_power: float = 10.0
    dashboard_run: bool = False
    # ...
```

- **Vorteil:** Einfach, direkter Zugriff `model.gain_block_slider`; bei GUI-Änderung nur neue Felder hinzufügen/umbenennen.
- **Nachteil:** Punkt in ID muss durch Unterstrich ersetzt werden (Python-Attribut), oder man nutzt ein Dict (z. B. `model.state["link_budget.tx.power"]`).

**Option B: Hierarchisches Modell (spiegelt GUI-Struktur)**

```python
@dataclass
class GainBlockState:
    slider: float = 0.0
    vu_value: float = 0.0

@dataclass
class LinkBudgetState:
    tx_power: float = 10.0
    rx_display: float = 0.0

@dataclass
class AppModel:
    gain_block: GainBlockState = field(default_factory=GainBlockState)
    link_budget: LinkBudgetState = field(default_factory=LinkBudgetState)
    run: bool = False
```

- **Vorteil:** Klare Struktur, Typisierung pro Container; Refactoring pro Gruppe möglich.
- **Nachteil:** Bei jeder neuen Container/Gruppe im Builder muss die Dataclass-Struktur angepasst werden (kann aber aus JSON-Schema/Builder-Export generiert werden).

### 3.2 Empfehlung für leichte Modifikation der GUI

- **Kern:** Ein **einziges Dict** (oder eine flache Dataclass) mit **string-Keys = Pfad-IDs** (z. B. `"gain_block.slider"`, `"link_budget.tx.power"`). Das ist das „persistente State-Dictionary“.
- **Optional:** Darüber eine **generierte oder handgepflegte Dataclass**, die dieses Dict liest/schreibt, damit die User-App mit `model.gain_block_slider` arbeiten kann; die Dataclass wird aus dem Builder-Layout (JSON) abgeleitet.
- **Sinnvolle Namenskonvention für die finalen Modell-Felder:**
  - Ersetze Punkte durch `_` für Python-Attribute: `gain_block_slider`, `link_budget_tx_power`.
  - Oder: Zugriff nur über `model.state["gain_block.slider"]` – dann keine Umbenennung nötig, GUI-Änderungen betreffen nur die Keys.

**Konkret:** Wenn die GUI oft geändert wird, ist ein **reines Dict mit Pfad-IDs als Keys** am robustesten; die User-Logik arbeitet mit diesen Keys. Wenn die GUI stabiler ist, kann eine **generierte Dataclass** mit lesbaren Attributnamen (z. B. `gain_block_slider`) aus demselben Dict erzeugt werden – das Modell bleibt dann „ein Dict + optional TypedDict/Dataclass-View“.

---

## 4. Trennung: GUI (NiceGUI) vs. User-App

### 4.1 Saubere Trennung – ja, möglich

- **GUI-Schicht (Builder-Output):**
  - Beschreibung des Layouts: welche Widgets, wo (XY oder Rows/Columns), welche Container/Gruppen, welche Pfad-IDs.
  - Erzeugung der NiceGUI-Elemente (Rows, Columns, Container mit absolut positionierten Widgets).
  - **Keine** Geschäftslogik; nur Bindung: bei Widget-Event → Callback aufrufen und State im gemeinsamen Modell aktualisieren.

- **User-App / Logik-Schicht:**
  - Ein gemeinsames **State-Objekt** (Dict oder Dataclass) mit allen relevanten Werten.
  - **Callbacks**, die vom Builder als Skeleton erzeugt werden (z. B. `on_gain_block_slider_change(value)`, `on_run_change(value)`). Der User füllt nur diese Callbacks mit seiner Logik (DSP, Geräte-Ansteuerung, Berechnungen).
  - Optional: Timer, Hintergrund-Threads, die nur auf das State-Objekt und ggf. auf die Callbacks zugreifen – wie in der use_case_template.

### 4.2 Konkrete Aufteilung (nach Vorbild use_case_template)

- **generated_ui.py (oder vom Builder erzeugt):**
  - `build_ui(model: AppModel) -> None`: baut nur die Oberfläche aus dem Layout-JSON/Registry; registriert für jedes Widget einen kleinen Adapter, der `model.state["pfad.id"] = value` setzt und dann `user_callbacks.on_xxx(value)` aufruft.
  - Kein `audio_io`, kein `config` (außer wenn explizit als „Services“ injiziert).

- **model.py (oder vom Builder + User erweitert):**
  - `AppModel`: Dataclass oder TypedDict mit allen State-Feldern (Keys = Pfad-IDs oder davon abgeleitete Attributnamen).
  - Optional: `load/save` für JSON-Persistenz (Sessions).

- **user_app.py / main.py (User-Code):**
  - Instanziert `AppModel`, lädt gespeicherten State.
  - Definiert die **Callbacks** (z. B. `def on_gain_block_slider_change(value): ...`, `def on_run_change(value): ...`).
  - Ruft `build_ui(model, callbacks=...)` auf und startet ggf. Timer/Services; die GUI ruft nur zurück in diese Callbacks.

So bleibt die GUI „dumm“ (nur Darstellung + State schreiben + Callback feuern), die User-App enthält die gesamte Logik.

### 4.3 Grenzfälle

- **Widgets, die von der Logik gesteuert werden** (z. B. VU-Meter-Anzeige, LED-Status): Die User-App setzt `model.state["gain_block.vu_value"] = x` und ruft `widget.update()` oder die Vue-Komponente bekommt den Wert per Prop-Updates. Dafür muss die GUI-Schicht eine schlanke **Referenz** auf die Widget-Instanzen bereitstellen (z. B. Dict `widget_registry["gain_block.vu"] -> VuMeter`) oder die Updates laufen über das gemeinsame Modell und ein zentrales `update_ui()` (wie im Template).
- **Services (Audio, Config, RTL-SDR):** Werden von der User-App instanziiert und den Callbacks über Closure oder ein Context-Objekt übergeben – nicht Teil der generierten GUI.

---

## 5. Kurzantworten auf die gestellten Fragen

| Frage | Kurzantwort |
|-------|--------------|
| **Namensgebung (Namespace) unter Berücksichtigung hierarchischer Anordnung?** | Punktierte Pfad-IDs: `container_id.group_id.widget_id`. Container und Gruppen haben eigene Namen; Eindeutigkeit pro Parent. |
| **Sinnvolle finale Namen für das gemeinsame Modell?** | Ein Dict mit Keys = Pfad-IDs (z. B. `"gain_block.slider"`) ist am flexibelsten bei GUI-Änderungen. Optional generierte Dataclass mit Unterstrich-Attributen (z. B. `gain_block_slider`) für bequemen Zugriff. |
| **Kann GUI und Bauen der GUI sauber von der User-App getrennt werden?** | Ja: GUI-Schicht baut nur UI, schreibt State, ruft User-Callbacks. User-App hält Modell und Callbacks mit gesamter Logik; keine Geschäftslogik in der generierten GUI. |

---

## 6. Ablage im lab_suite-Ordnerbaum

- **App-Builder (Kern):** `lab_suite/app_builder/`  
  - Layout-Schema (`layout_schema.py`), JSON-Format-Spezifikation (`layout_format.md`), Skeleton-Generator (`skeleton.py`).  
  - Später: visueller Builder (Drag & Drop), der Layouts exportiert und Skeleton-Code erzeugt.

- **Development-App (PoC):** `lab_suite/labs/development_app/`  
  - Parallele App zu use_case_template; nutzt den App-Builder, um die Use-Case-Template-App schrittweise nachzubilden (gleiche Controls, verbesserte GUI).  
  - Enthält: `layout.json`, `callback_skeleton.py`, `model_schema.py`, `app.py`.

- **Use-Case-Template:** `lab_suite/labs/use_case_template/`  
  - Referenz-App, deren Steuerung und Logik in der development_app über Layout + Callbacks nachgebildet werden.

## 7. Nächste Schritte (optional)

- Builder: Layout-Format (JSON-Schema) für Dashboard, Container, Gruppen, Widgets inkl. Pfad-IDs und Positionen definieren.
- Code-Generator: Aus Layout-JSON → `build_ui(...)`, Skeleton-Callbacks, Modell-Dict/Dataclass und JSON load/save erzeugen.
- Standard-Widget-Library (Stufe 1–3) in `lab_suite/widgets` weiter ausbauen; jedes Widget einheitliches Interface (value, min, max, on_change, …) und dokumentierte Props/Events für den Builder.
- Development-App: Layout schrittweise um alle use_case_template-Controls erweitern und `build_ui_from_layout` im App-Builder oder in der App generisch machen.
