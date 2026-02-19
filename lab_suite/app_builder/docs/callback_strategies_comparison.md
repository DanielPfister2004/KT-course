# Callback-Strategien: Vergleich und Koexistenz

Zwei Ansätze für Input-Callbacks und wie sie für Studierende mit wenig Laborzeit geeignet sind bzw. in unserer Architektur nebeneinander genutzt werden können.

---

## 1. Zwei Strategien im Überblick

| Aspekt | **A: Pro-Widget-Callback (aktuell)** | **B: User-definierter Callback (Qt/CVI-Style)** |
|--------|--------------------------------------|-------------------------------------------------|
| **Idee** | Pro Input-Widget wird **automatisch** eine Callback-Funktion erzeugt (Stub in `user_callbacks.py`). Registry: `path_id → eine Funktion`. | Der User **weist** einem Widget (oder mehreren) explizit einen Callback zu. Mehrere Widgets können **denselben** Callback nutzen (z. B. „Parameter geändert“). |
| **Beispiel** | Slider Frequenz → `on_freq_change(value)`, Slider Amplitude → `on_amplitude_change(value)`. | Slider Frequenz und Slider Amplitude → beide rufen `on_signal_params_change(value, source_id)` auf. |
| **Typisch in** | Unser App-Builder (generierte Stubs), viele Web-Frameworks. | Qt (`connect(slider, &QSlider::valueChanged, this, &Generator::onParamChanged)`), LabWindows CVI, klassische GUI-Toolkits. |

---

## 2. Welche Strategie ist besser für Studierende mit wenig Zeit?

**Für knappe Laborzeit ist Strategie A (Pro-Widget, automatisch generiert) in der Regel die bessere Wahl.**

| Kriterium | A (Pro-Widget) | B (Shared Callback) |
|-----------|----------------|---------------------|
| **Einstieg** | „Jedes Widget hat eine Funktion; dort machst du deine Logik.“ Kein Konzept „Callback zuweisen“. | Erfordert Verständnis: Callback-Referenz, mehrere Widgets → eine Funktion, ggf. `source_id` auswerten. |
| **Generator** | Stubs werden vollautomatisch erzeugt und gemerged; Studierende füllen nur die Rumpf-Logik. | Entweder weiterhin ein Stub pro Widget (dann redundant zu A) oder ein gemeinsamer Stub für mehrere Widgets – dann muss das Layout „callback_ref“ o. ä. setzen und der Generator das abbilden. |
| **Fehlersuche** | Ein Widget → eine Funktion; Stacktrace und Breakpoint sind eindeutig. | Eine Funktion für mehrere Quellen; Studierende müssen `source_id`/path_id auswerten oder State vergleichen. |
| **Flexibilität** | Wenn zwei Slider dasselbe tun sollen, ruft man in beiden Stubs dieselbe Hilfsfunktion auf (z. B. `apply_signal_params()`). | Natürlich: ein Callback, der alle Parameter eines „Signalgenerators“ ausliest und anwendet. Weniger Duplikat-Code. |

**Fazit für die Zielgruppe:**  
- **Standard für Übungen:** **A** beibehalten – wenig Konzepte, klare 1:1-Zuordnung, Generator übernimmt die Struktur.  
- **B** als **Option** für fortgeschrittene Szenarien (z. B. viele Parameter eines Moduls bündeln) oder wenn ihr gezielt „ein Callback für mehrere Widgets“ lehren wollt.

---

## 3. Koexistenz in unserer Architektur

Beide Strategien lassen sich in der bestehenden Architektur unter einen Hut bringen.

### 3.1 Was unverändert bleibt

- **Renderer:** Ruft weiter `callbacks.get(path_id)(value)` (ggf. mit optionalem `path_id`) auf. Er muss nicht wissen, ob die Funktion „pro Widget“ oder „shared“ ist.
- **Registry-Typ:** `dict[str, Callable]` mit **path_id als Key**. Mehrere path_ids können auf **dieselbe** Callable zeigen – das ist bereits erlaubt.

### 3.2 Optionale Erweiterung für Shared Callbacks (Strategie B)

- **Layout:** Neues optionales Prop für Widgets mit Callback, z. B. **`callback_ref`** (String).  
  - Fehlt `callback_ref`: Verhalten wie heute → generierter Name pro Widget (Strategie A).  
  - Ist `callback_ref` gesetzt (z. B. `"on_signal_params_change"`): Dieser Name wird für alle Widgets mit diesem `callback_ref` verwendet; die Registry mappt **jedes** dieser path_ids auf **dieselbe** Funktion.

- **Schema/Skeleton:**  
  - `collect_callback_names`: Liest optional `callback_ref` aus den Widget-Props. Wenn gesetzt → `py_name = callback_ref`, Merge-Key z. B. `callback_ref=<name>`. Sonst wie bisher (generierter Name aus user_id/path_id).  
  - Beim Generieren der Registry: `registry[path_id] = getattr(user_callbacks, py_name)` – mehrere path_ids erhalten dieselbe `py_name` → dieselbe Callable.

- **Callback-Signatur:** Damit ein gemeinsamer Callback die **Quelle** kennt, ein optionales zweites Argument:  
  **`(value, path_id=None)`** (bei change/click).  
  - Bestehende Callbacks mit nur `(value)` bleiben gültig (Python erlaubt zusätzliche optionale Argumente).  
  - Shared Callback: `def on_signal_params_change(value, path_id=None): ...` und je nach `path_id` z. B. State/Modell aktualisieren.

- **Renderer:** Statt nur `fn(value)` z. B. `fn(value, path_id)` aufrufen (oder `fn(value, path_id=path_id)`), damit alle Callbacks optional die Quelle nutzen können.

### 3.3 Konkrete Schritte für Koexistenz

1. **Layout-Format:** Optionale Prop `callback_ref: string` in den Widget-Definitionen dokumentieren (z. B. in `layout_format.md` / Layout-Builder-Hints).
2. **`layout_schema.collect_callback_names`:** Wenn `props.get("callback_ref")` gesetzt und nicht leer → `py_name = callback_ref`, Merge-Key z. B. `callback_ref:<name>`; sonst Verhalten wie bisher.
3. **Skeleton/Generator:** Pro **eindeutigem** `py_name` nur **einen** Stub erzeugen (bei shared: ein Stub für mehrere path_ids). Registry: für jedes path_id mit diesem `callback_ref` Eintrag `path_id → on_xyz`.
4. **Renderer:** Callback-Aufruf um optionales Argument erweitern, z. B. `callbacks.get(path_id)(value, path_id)` (oder keyword `path_id=`). Alte Callbacks mit Signatur `(value)` funktionieren weiter.
5. **Doku/Stubs:** In Docstring/Stub für shared Callbacks erwähnen: „Wird von mehreren Widgets aufgerufen; `path_id` gibt die Quelle an.“

Damit gilt:

- **Ohne `callback_ref`:** Weiterhin ein automatisch generierter Callback pro Widget (Strategie A), ideal für den Standard-Einstieg.
- **Mit `callback_ref`:** Mehrere Widgets rufen dieselbe User-Funktion auf (Strategie B); geeignet für gebündelte Parameter-Logik (z. B. Signalgenerator), mit optionalem `path_id` zur Unterscheidung.

---

## 4. Kurzfassung

| Frage | Antwort |
|-------|--------|
| **Besser für Studierende mit wenig Zeit?** | **Strategie A** (ein Callback pro Widget, automatisch generiert): weniger Konzepte, klare Zuordnung, Generator erledigt die Struktur. |
| **Koexistenz möglich?** | **Ja.** Registry bleibt path_id → Callable; mehrere path_ids können dieselbe Callable referenzieren. Optionale Layout-Prop `callback_ref` + optionales Argument `path_id` im Callback reichen für Strategie B. |
| **Empfehlung** | A als Default beibehalten; B über `callback_ref` optional anbieten für fortgeschrittene/gebündelte Fälle. |
