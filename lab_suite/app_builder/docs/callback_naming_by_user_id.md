# Callback-Namen nach user_id statt path_id

## Bewertung der Idee

**Ziel:** Callbacks im Code nach **user_id** (z. B. `on_power_change`) benennen statt nach **path_id** (z. B. `on_row_0_widget_1_change`). Bei Umplatzierung von Widgets (z. B. Zeile einfügen) bleibt die user_id gleich → der gleiche Callback wird wiedergefunden, User-Code geht nicht verloren.

### Ist die Annahme korrekt?

**Ja.** Wenn ein Widget `user_id="power"` hat und von `row_0` nach `row_1` verschoben wird, ändert sich:
- **path_id:** `row_0.widget_1` → `row_1.widget_1`
- **user_id:** bleibt `"power"`

Das Merge im Skeleton matcht heute nach **path_id**. Nach der Änderung matcht es nach **user_id** (falls gesetzt), sonst nach path_id. Beim erneuten Generieren wird der Block mit `# widget: user_id=power` wiedererkannt, der User-Code bleibt erhalten.

### Ist es ohne große Architekturänderung umsetzbar?

**Ja.** Die bestehende Architektur bleibt erhalten:

| Komponente | Änderung |
|------------|----------|
| **Renderer** | Keine. Ruft weiter `callbacks.get(path_id)` auf – die Registry bleibt **path_id → Callable**. |
| **callback_registry** | Unverändert: `dict[str, Callable]` mit path_id als Key. Zur Laufzeit kommt vom Renderer immer path_id; die zugehörige Funktion kann `on_power_change` heißen. |
| **Binding** | path_id ↔ user_id: Das Layout liefert beides. Beim Aufbau der Registry: für jedes Widget mit path_id wird die passende Funktion (benannt nach user_id oder path_id) eingetragen: `registry[path_id] = on_power_change`. Kein zusätzliches Binding nötig – die Zuordnung path_id → Funktion steht einmalig beim Generieren/Laden fest. |
| **layout_schema** | `collect_callback_names` erweitern: pro Widget optional user_id aus props; wenn user_id gesetzt und eindeutig → py_name = `on_{user_id_snake}_change` und Merge-Key = user_id; sonst wie bisher path_id. |
| **Skeleton** | Merge-Key: in user_callbacks.py Blöcke mit `# widget: user_id=power` oder `# widget: path_id: row_0.widget_1` schreiben; Parser liest beides; beim Merge nach diesem Key matchen (nicht nur path_id). |

### Vorteile für Studierende

1. **Stabile Namen:** `on_power_change` statt `on_row_0_widget_1_change` – lesbar und unabhängig von Zeilen/Spalten.
2. **Kein Verlust bei Umplatzierung:** Widget mit user_id verschieben → gleicher Block wird beim nächsten „Generate skeleton“ wiedererkannt, Code bleibt erhalten.
3. **Semantik:** user_id entspricht der fachlichen Rolle (z. B. „power“, „gain“); Callback-Namen passen dazu.
4. **Rückwärtskompatibel:** Widgets ohne user_id verhalten sich wie bisher (path_id für Name und Merge).

### Randfälle

- **Doppelte user_id:** Zwei Widgets mit derselben user_id → nur eines kann den Namen `on_power_change` tragen. Lösung: Bei Duplikaten für alle betroffenen Widgets auf path_id-Benennung (und path_id-Merge-Key) ausweichen; ggf. Warnung im Generator.
- **user_id-Format:** Für Python-Funktionsnamen nur erlaubte Zeichen (z. B. user_id zu snake_case normalisieren: Leerzeichen/Sonderzeichen → `_`).

### Fazit

**Umsetzung empfohlen.** Kleine, lokale Änderungen in layout_schema (Callback-Liste inkl. Merge-Key, py_name aus user_id wenn eindeutig) und Skeleton (Merge-Key im Kommentar, Parser, Merge nach Key). Renderer und Registry-API bleiben unverändert; die Idee ist mit der bestehenden Architektur vereinbar und erleichtert Studierenden den Umgang mit stabilen Callbacks.
