# NiceGUI-Regeln (lab_suite)

Regeln und Fixes für funktionierende NiceGUI-Apps. Bei neuen Apps diese von vornherein beachten, um typische Fehler zu vermeiden.

---

## 1. Main-Guard und ui.run()

**Regel:** Den Einstieg für `main()` (und damit `ui.run()`) mit dem erweiterten Guard schreiben:

```python
if __name__ in {"__main__", "__mp_main__"}:
    main()
```

- Nur `if __name__ == "__main__":` reicht nicht: Bei Multiprocessing/Reload kann der Subprocess mit `__name__ == "__mp_main__"` laufen. NiceGUI erwartet dann trotzdem, dass `ui.run()` aufgerufen wird.
- **Hinweis Reload:** Wenn die App mit `python -m labs.xyz` gestartet wird und der Reload-Modus aktiv ist, führt der Reload-Subprocess oft nicht unser `__main__.py` aus – dann kommt: *"You must call ui.run() to start the server"*. Abhilfe: `reload=False` in `ui.run()` setzen (oder Nutzer mit `--no-reload` starten lassen).

**Betroffen:** `app.py`, `__main__.py` (überall, wo `main()` aufgerufen wird).

---

## 2. Werte aus dem Event holen (Slider, Select, Input, …)

**Regel:** Bei **ValueChangeEventArguments** (z. B. `on_change` von Slider, Select, Input) den Wert aus **`e.value`** oder **`e.sender.value`** lesen – **nicht** aus **`e.args`**.

- `e.args` existiert bei diesen Events nicht → `AttributeError: 'ValueChangeEventArguments' object has no attribute 'args'`.

**Empfohlen:** Eine kleine Hilfsfunktion nutzen, die beide Quellen und Fallback abdeckt:

```python
def _event_value(e, default=0.0):  # Typ je nach Widget (float, int, str, ...)
    """Wert aus NiceGUI ValueChangeEvent (e.value oder e.sender.value)."""
    v = getattr(e, "value", None)
    if v is not None:
        return v  # ggf. float(v) / int(v) je nach Kontext
    s = getattr(e, "sender", None)
    if s is not None:
        v = getattr(s, "value", default)
        return v if v is not None else default
    return default
```

Dann in den Handlern z. B.:

```python
def on_slider1(e):
    slider_value["v"] = _event_value(e, 0.0)
    update_result()
```

**Betroffen:** Alle `on_change`-Handler für Slider, Select, Input usw.

**Select (Dropdown):** Den Handler im **Konstruktor** mit `on_change=...` übergeben, nicht per `.on("change", ...)` nachträglich binden – sonst feuert das Event unter Umständen nicht (z. B. Sound-Device-Auswahl zeigt keinen Effekt, keine Debug-Meldung).

```python
ui.select(options, value=model.x, label="...", on_change=on_x_change)
```

---

## 3. Struktur: build_ui und Event-Handler (Best Practice)

**Regel:** Eine zentrale Funktion (z. B. `build_ui()` oder `build_root()`) baut die gesamte GUI auf und definiert dabei die Event-Handler. Das ist bei NiceGUI Standard und in Ordnung.

- **Widgets + Handler in einer Funktion:** Du hast Zugriff auf dieselben Variablen (State, Label-Referenzen) ohne komplizierte Weitergabe. Neue GUI-Elemente und ihre Handler werden zuerst hier ergänzt.
- **Wenn die Funktion zu lang wird:** Teilbereiche in Hilfsfunktionen auslagern (z. B. `_build_controls()`, `_build_plot()`), die aus `build_ui()` aufgerufen werden. Die Handler können weiter in diesen Hilfsfunktionen stehen (Closure über gemeinsamen State).
- **State gebündelt:** Für viele Werte ein **Model** (Dataclass) oder ein Dict verwenden, das in den Handlern gelesen/geschrieben wird – so bleibt klar, wo welcher Wert liegt (siehe fft_scope).
- **Keine Fachlogik in der GUI:** Rechenlogik, Validierung, Datenzugriff in eigenen Modulen (z. B. `math.py`, `config.py`). In der GUI nur: Werte aus Events lesen, Modul aufrufen, Ergebnis in Widgets schreiben.

| Thema | Empfehlung |
|-------|------------|
| Eine Funktion baut die GUI auf | Ja, typisch. Name z. B. `build_ui()` / `build_root()`. |
| Event-Handler in derselben Funktion | Ja, normal. Ermöglicht einfachen Zugriff auf lokale Variablen/State. |
| Neue Elemente / neue Handler | Zuerst in diese Build-Funktion (oder ihre Auslagerungen). |
| Wenn es zu groß wird | In kleinere Funktionen aufteilen; State z. B. über Model. |
| Fachlogik | Nicht in der GUI – in eigenen Modulen (z. B. `math.py`). |

---

## 4. Design-Patterns: User-Code, Main-Loop, Multithreading

### User-Code nur mit Funktionen/Klassen (keine eigene Main-Loop)

**Pattern:** Der Treiber (NiceGUI mit Timer, Buttons) ruft den User-Code auf. Das Modul (z. B. `math.py`, `dsp.py`) hat **keine eigene Endlosschleife**, nur **Funktionen** und ggf. **Klassen**. Reaktiv auf Aufrufe.

- **Vorteil:** Einfach, testbar, keine Konkurrenz um „wer hat die Hauptschleife“.
- **Offizielle Begriffe:** **Event-driven**, **callback-basiert** – die „Loop“ liegt beim Framework (NiceGUI + Timer), der User-Code wird nur aufgerufen.

### Eigene „Main Loop“ im User-Code

**Ja, möglich.** Eine Endlosschleife im User-Code sollte **nicht** im GUI-Thread laufen (sonst blockiert die UI).

| Variante | Wo läuft die Loop? | Kommunikation mit GUI |
|----------|--------------------|-------------------------|
| **Timer als Loop** | GUI-Thread (z. B. `ui.timer(0.1, update_ui)`) | Das *ist* die periodische Schleife – callback-basiert (z. B. fft_scope). |
| **Eigene Endlosschleife** | In einem **eigenen Thread** | Loop schreibt in **Queue** oder geteilten Puffer; GUI liest per **Timer** und aktualisiert Widgets. |
| **Beispiel** | `audio_io._test_generator_loop` (Thread) | Schreibt in `RingBuffer`; GUI liest im Timer mit `get_ring().read_latest()`. |

Offizieller Begriff dafür: **Producer-Consumer** (ein Thread produziert Daten, der GUI-Timer konsumiert).

### Multithreading

- **Regel:** Blockierende oder lange Arbeit in einen **Worker-Thread** auslagern; GUI bleibt im Hauptthread.
- **Kommunikation:** Thread → GUI z. B. **Queue** oder **RingBuffer**; GUI liest in einem **Timer** und aktualisiert die Widgets. GUI → Thread z. B. Queue für Befehle (Start/Stop) oder geteilte Variablen mit Lock.
- **NiceGUI:** Widget-Updates nur aus dem Kontext, in dem die UI lebt. Der Worker schreibt nur in Datenstrukturen; der Timer-Callback in der GUI liest und setzt `label.text`, `plot.update()` usw.

### Kurz: Bezeichnungen

| Begriff | Bedeutung |
|---------|-----------|
| **Event-driven / reaktiv** | Keine zentrale Main-Loop im User-Code; Ablauf durch Events/Callbacks (Klicks, Timer). |
| **Callback-basiert** | Statt „ich frage ab“ → „wenn X passiert, rufe diese Funktion auf“. |
| **Main Loop / Event Loop** | Eine zentrale Schleife (oft im Framework); bei NiceGUI hat das Framework die Loop, du hängst Timer/Events dran. |
| **Producer-Consumer** | Ein Thread/Funktion produziert Daten (z. B. Audio), ein anderer (z. B. GUI-Timer) konsumiert; Kommunikation über Queue/Puffer. |
| **MVC / Trennung Model–View** | GUI (View) + User-Code/Rechenlogik (Model) getrennt; Events/Handler als schlanker Controller. |

---

## Weitere Einträge (zukünftige Fixes)

Neue NiceGUI-bezogene Fehler und deren Fixes hier als weitere nummerierte Abschnitte ergänzen (kurz: Fehlerbild, Ursache, Regel/Lösung).
