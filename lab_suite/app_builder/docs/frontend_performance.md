# Frontend-Performance messen (Browser)

Die Server-Performance (Tick-Laufzeit, CPU, Headroom) wird in `user_template.get_perf_stats()` bzw. über `DEBUG_PERF=1` gemessen. Die **Auslastung im Browser** (Rendering, FPS) ist davon getrennt und kann wie folgt erfasst werden.

## Idee

- Im Frontend einen kleinen FPS-Zähler laufen lassen (z. B. über `requestAnimationFrame`).
- Den letzten FPS-Wert in einer globalen Variable ablegen (`window.__browserFps`).
- Vom Server aus per `ui.run_javascript(...)` diesen Wert abfragen (NiceGUI führt das im Client aus und kann den Rückgabewert an den Server liefern).

## Beispiel: FPS im Browser erfassen

Einmalig beim Aufbau der Seite ein Script injizieren (z. B. in `app.py` nach `build_ui_from_layout`, nur wenn gewünscht):

```python
# Optional: Frontend-FPS-Zähler (z. B. wenn ENABLE_PERF_STATS oder DEBUG_FRONTEND_FPS=1)
if os.environ.get("DEBUG_FRONTEND_FPS", "").strip() in ("1", "true", "yes"):
    ui.add_head_html('''
    <script>
    (function(){
        var frames = 0, lastFps = 0, lastTime = performance.now();
        function tick() {
            frames++;
            var now = performance.now();
            if (now - lastTime >= 1000) { lastFps = frames; frames = 0; lastTime = now; }
            requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
        window.__browserFps = function() { return lastFps; };
    })();
    </script>
    ''')
```

Abruf vom Server (z. B. aus einem Button-Callback oder einem periodischen Timer, der async ist):

```python
# Async nötig, weil run_javascript mit Rückgabe als Coroutine
async def read_client_fps():
    result = await ui.run_javascript("return window.__browserFps ? window.__browserFps() : null;")
    return result  # FPS (Zahl) oder null
```

Hinweis: Ein synchroner `timer_tick()` kann nicht einfach `await ui.run_javascript(...)` aufrufen. Optionen: (1) Client-FPS nur on-demand per Button anzeigen, (2) einen separaten asynchronen Task laufen lassen, der periodisch die FPS abfragt und in einer Variable speichert, die `get_perf_stats()` oder die Konsole auslesen kann.

## Plot-Dauer im Browser (PlotlyGraph)

Das PlotlyGraph-Widget misst nach jeder Aktualisierung (newPlot, react, restyle+relayout) die Dauer bis zum Abschluss und schreibt sie in **`window.__lastPlotDurationMs`** (Millisekunden). Abruf vom Server z. B.:

```python
# Async, z. B. aus Button-Callback
result = await ui.run_javascript("return typeof window.__lastPlotDurationMs !== 'undefined' ? window.__lastPlotDurationMs : null;")
# result = letzte Render-Dauer (ms) oder null
```

So siehst du, wie lange der Browser für einen Plot-Update braucht (inkl. WebGL/Canvas).

---

## Kurzfassung

- **Frontend-Auslastung messen:** Ja, z. B. über FPS-Zähler im Browser und Abruf per `ui.run_javascript`.
- **Plot-Dauer im Browser:** Nach jedem Update setzt das PlotlyGraph-Widget `window.__lastPlotDurationMs` (ms). Abfrage per `ui.run_javascript("return window.__lastPlotDurationMs;")`.
- **Aufwand:** Gering (Script injizieren + gelegentlicher Abruf). Automatische Integration in die bestehende Perf-Statistik erfordert einen async Task oder on-demand Abfrage.

Siehe auch: `get_perf_stats()` in `assignments/user_template.py` (Server-Seite), `DEBUG_PERF` / `ENABLE_PERF_STATS`.
