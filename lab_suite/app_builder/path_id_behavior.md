# Path-IDs: Ableitung, Stabilität, Skeleton, GUI-Binding

## Wie entstehen Path-IDs?

- **Path-IDs** werden aus der **Hierarchie der Knoten-IDs** gebildet, nicht aus der Position (Index).
- Formel: `path_id = parent_path + "." + node["id"]` (Root: nur `node["id"]`).
- Beispiele: `row_0`, `row_0.widget_1`, `row_1.container_1.widget_2`.

Relevanter Code:
- `layout_schema._collect_widgets()` / `renderer._path()`: bauen den Pfad aus `node.get("id", "")` pro Ebene.
- `get_widget_node_by_path_id()`: findet ein Widget, indem es das Layout anhand der Pfad-Segmente (ids) durchläuft.

## Ändern sich Path-IDs beim Hinzufügen von Widgets?

- **Neues Widget in eine Zelle legen:**  
  Das neue Widget bekommt eine **neue, eindeutige ID** (`next_widget_id` → z. B. `widget_5`).  
  Bestehende Widget-IDs (z. B. `widget_1` … `widget_4`) bleiben unverändert.  
  → **Bestehende Path-IDs ändern sich nicht.**

- **Neue Zeile/Spalte am Root einfügen (Insert row/column):**  
  Beim Export (`grid_to_layout`) erhalten Zeilen-Container **positionsbasierte IDs**: `row_0`, `row_1`, …  
  Nach dem Einfügen einer Zeile werden diese IDs neu vergeben (jede Zeile = neuer Index).  
  → **Alle Path-IDs, die ein `row_X` enthalten, können sich ändern** (z. B. `row_0.widget_1` → `row_1.widget_1`).

- **Container/Widgets in Kind-Containern (z. B. in `rows_columns`/Grid-Child):**  
  IDs kommen von `next_widget_id` / `next_container_id` (eindeutige Nummer).  
  Sie bleiben stabil, solange der Knoten nicht gelöscht wird.  
  Nur wenn sich die **Root-Zeilen-Struktur** ändert, ändert sich der **Prefix** (z. B. `row_0` → `row_1`), der komplette Path also z. B. `row_0.container_1.widget_1` → `row_1.container_1.widget_1`.

Kurz: Path-IDs sind **id-basiert**; instabil sind sie dort, wo IDs **positionsbasiert** vergeben werden (aktuell: Root-Zeilen-Container in `grid_to_layout`).

## GENERATE SKELETON (Grid-Editor)

- Verwendet das **aktuelle Layout** aus dem Grid: `get_current_layout()` → `grid_to_layout(state["cells"], state["rows"], state["cols"])`.
- Der Skeleton-Generator nutzt `collect_callback_names(layout)`, das intern `_collect_widgets_from_dashboard(layout)` aufruft.
- `_collect_widgets` traversiert **rekursiv** alle Kinder (Container, group, tab); jede Ebene hängt die eigene `node["id"]` an den Pfad.
- **Folge:** Alle Widgets mit Callbacks werden berücksichtigt – **inkl. Child-Widgets** in verschachtelten Containern (z. B. `row_0.container_1.widget_2`).
- Die generierten Stubs und das Callback-Mapping verwenden genau die **aktuellen path_ids** dieses Layouts.
- **Merge (user_callbacks.py):** Es wird nach **path_id** gematcht (`# widget: <path_id>`). Wenn sich path_ids geändert haben (z. B. nach Zeilen einfügen), gibt es für die alten path_ids kein Match mehr → neue Stubs, **bisheriger User-Code zu einer path_id kann „verloren“ wirken** (wird nicht mehr dem neuen path_id zugeordnet).

## GUI-Binding (user_id)

- **SEMANTIC_BINDING:** `user_id` (Props) → `path_id`; wird bei App-Start aus dem Layout gebaut (`collect_semantic_binding` / `update_binding_from_layout`).
- Der User arbeitet mit **logischen Namen** (`get("gain")`, `set("power", value)`); die App schaut nur `user_id` → aktuelle `path_id` im Layout.
- Wenn sich die **path_id** eines Widgets ändert (z. B. `row_0.widget_1` → `row_1.widget_1`), aber das Widget dieselbe **user_id** behält, wird beim nächsten Laden das Binding neu aufgebaut und zeigt auf die neue path_id.
- **Folge:** **GUI-Binding über user_id ist robust** gegenüber Strukturänderungen (Zeilen einfügen/löschen). **Path_id-basierte Nutzung** (Dropdown „Widget (path_id)“, Callback-Namen im Skeleton) kann sich bei Root-Strukturänderungen ändern.

## Empfehlung

- Für **stabile Zuordnung von Logik zu Widgets:** `user_id` (Props) setzen und über `gui_binding.get/set(key)` arbeiten; dann bleibt das Verhalten auch bei geänderten path_ids konsistent.
- Wenn **path_id-basierte Callbacks** genutzt werden: Nach **Zeilen/Spalten einfügen oder löschen** am Root ggf. erneut „Generate skeleton“ ausführen und prüfen, ob bestehende Callback-Funktionen noch den richtigen Widgets zugeordnet sind (Merge erfolgt nach path_id; geänderte path_ids erzeugen neue Stubs).
