"""
User-Template: Kern- und Fachlogik für die Übung.

Hier lösen Sie die eigentliche Fach-Aufgabe. Die GUI liefert Parameter über get()
und zeigt Ergebnisse über set(); die Zuordnung Widget ↔ fachliche Größe erfolgt
über die User-ID im Layout (SEMANTIC_BINDING wird daraus automatisch befüllt).

Stand get() / set() / update_plot():
- get(key) und set(key, value) sind vollständig implementiert.
- get(key): Liest den Wert aus dem State (key = User-ID aus dem Layout).
- set(key, value): Schreibt in State und aktualisiert Output-Widgets (LED: set_state,
  VU-Meter: set_value), sofern die path_id in der Widget-Registry steht.
- update_plot(key, data, layout=None): Aktualisiert ein Plotly-Widget (user_id = key).
- Voraussetzung: Aufruf im GUI-Kontext (z. B. aus user_callbacks.py oder aus einem
  ui.timer), damit ui.context.client.state und widget_registry verfügbar sind.
- Wenn SEMANTIC_BINDING korrekt befüllt ist (user_id pro Widget gesetzt), reicht
  get("power"), set("led_status", "on"), update_plot("sine_plot", data) etc.

Timer: Die App startet einen Timer (einstellbare Rate, z. B. 10 Hz) und ruft
timer_tick() in diesem Modul auf, falls vorhanden. So können Plots/Logik periodisch
laufen, unabhängig von Button-Callbacks.

Performance: ENABLE_PERF_STATS=True oder DEBUG_PERF=1 aktiviert Laufzeit-Messung
(perf_counter) und optional Prozess-CPU (psutil). Budget = Timer-Intervall;
Headroom = verbleibende Zeit für DSP pro Tick.
"""
from __future__ import annotations

import math
import os
import random
import time

# Zugriff auf die GUI über fachliche Größen (User-IDs aus dem Layout)
from .._core import gui_binding

# Demo: Phasenverschiebung für animierten Sinus (wird in timer_tick erhöht)
_sine_phase = 0.0
_sine_layout_sent = False  # Layout nur einmal senden, danach restyle_only für flüssigere Animation
# Einmaliger Debug-Ausdruck (auf True setzen zum Prüfen von Binding/Registry)
_DEBUG_PLOT_FIRST_RUN = False

# Performance: Laufzeiten (ms) und optional Prozess-CPU; Auswertung alle REPORT_EVERY_TICKS
ENABLE_PERF_STATS = os.environ.get("DEBUG_PERF", "").strip() in ("1", "true", "yes")
ENABLE_PERF_STATS = True
PERF_HISTORY_SIZE = 100
REPORT_EVERY_TICKS = 50
_perf_tick_durations_ms: list[float] = []
_perf_tick_count = 0
_perf_process: object | None = None
try:
    import psutil
    _perf_process = psutil.Process()
    print("psutil found")

except ImportError:
    print("psutil not found")
    _perf_process = None

# Scattergl (WebGL): flüssigere Animation, bessere Performance bei vielen Punkten (PLOT_SCATTERGL=1)
USE_SCATTERGL = True #os.environ.get("PLOT_SCATTERGL", "").strip().lower() in ("1", "true", "yes")


def run_domain_logic() -> None:
    """
    Beispiel: Parameter aus der GUI lesen, Fachlogik ausführen, Ergebnis in die GUI schreiben.
    Rufen Sie diese Funktion z. B. aus einem Callback in user_callbacks.py oder aus einem
    ui.timer auf, damit get/set im GUI-Kontext laufen.
    """
    power_on = gui_binding.get("Power-switch", False)
    gain = gui_binding.get("gain")
    pressure_set = gui_binding.get("Dampfdruck-set")
    #print("power_on: ", power_on, "gain: ", gain, "pressure_set: ", pressure_set)
    if power_on:
        gui_binding.set("led_status", "on")
        gui_binding.set("vu_level", min(10.0, gain))
    else:
        gui_binding.set("led_status", "off")
        gui_binding.set("vu_level", 0.0)


def get_perf_stats(timer_interval_sec: float = 0.1) -> dict:
    """
    Liefert die letzten Performance-Kennzahlen (Laufzeit pro Tick, Headroom für DSP).
    timer_interval_sec: Timer-Intervall (z. B. aus TIMER_INTERVAL_SEC, Default 0.1).
    Returns: dict mit last_ms, avg_ms, budget_ms, headroom_ms, headroom_pct, cpu_pct (falls psutil).
    """
    budget_ms = timer_interval_sec * 1000.0
    if not _perf_tick_durations_ms:
        return {
            "last_ms": 0.0,
            "avg_ms": 0.0,
            "budget_ms": budget_ms,
            "headroom_ms": budget_ms,
            "headroom_pct": 100.0,
            "cpu_pct": None,
        }
    last_ms = _perf_tick_durations_ms[-1]
    avg_ms = sum(_perf_tick_durations_ms) / len(_perf_tick_durations_ms)
    headroom_ms = max(0.0, budget_ms - avg_ms)
    headroom_pct = (headroom_ms / budget_ms * 100.0) if budget_ms > 0 else 100.0
    cpu_pct = None
    if _perf_process is not None:
        try:
            cpu_pct = _perf_process.cpu_percent(interval=None)
        except Exception:
            pass
    return {
        "last_ms": last_ms,
        "avg_ms": avg_ms,
        "budget_ms": budget_ms,
        "headroom_ms": headroom_ms,
        "headroom_pct": headroom_pct,
        "cpu_pct": cpu_pct,
    }


def debug_plot_binding() -> None:
    """
    Einmal aufrufen (z. B. aus timer_tick oder einem Button), um zu prüfen,
    ob „sine_plot“ gebunden ist und welche Plotly-Widgets in der Registry stehen.
    Ausgabe in der Konsole (Server/Terminal).
    """
    try:
        from nicegui import ui
        reg = getattr(ui.context.client, "widget_registry", None) or {}
        plotly_ids = [pid for pid, w in reg.items() if hasattr(w, "update_figure")]
        bound = gui_binding.SEMANTIC_BINDING.get("sine_plot")
        print("[debug_plot_binding] SEMANTIC_BINDING['sine_plot'] =", bound)
        print("[debug_plot_binding] Plotly-Widgets in Registry:", plotly_ids)
        if not bound and plotly_ids:
            print("[debug_plot_binding] Tipp: User-ID 'sine_plot' am Plot-Widget setzen oder Fallback nutzt", plotly_ids[0])
    except Exception as e:
        print("[debug_plot_binding] Fehler:", e)


# Einmaliges Layout für Sinus-Demo (fixe Achsen, wird bei restyle_only für relayout mitgeschickt)
_SINE_LAYOUT = {
    "title": {"text": "Sinus-Demo (timer-getriggert)"},
    "xaxis": {"title": {"text": "x"}, "range": [0, 4 * math.pi], "autorange": False},
    "yaxis": {"title": {"text": "y"}, "range": [-1.5, 1.5], "autorange": False},
}


def _update_sine_demo() -> None:
    """
    Demo: Einfache Sinusfunktion im Plot anzeigen.
    Erster Aufruf: volles Layout (Titel, Achsen); danach restyle_only (nur x/y) für flüssigere Animation.
    Layout wird immer mitgegeben, damit der Client die Achsen per relayout fix halten kann.
    """
    global _sine_layout_sent
    n = 2000
    x = [4 * math.pi * i / (n - 1) for i in range(n)]
    # Sinus + AWGN, damit man Updates (z. B. mit scattergl) besser erkennt
    noise_sigma = 0.12
    y = [math.sin(xi + _sine_phase) + random.gauss(0, noise_sigma) for xi in x]
    trace = {"x": x, "y": y, "mode": "lines", "name": "sin(x)+noise"}
    if USE_SCATTERGL:
        trace["type"] = "scattergl"
    data = [trace]
    if not _sine_layout_sent:
        gui_binding.update_plot("sine_plot", data, _SINE_LAYOUT, restyle_only=False)
        _sine_layout_sent = True
    else:
        gui_binding.update_plot("sine_plot", data, _SINE_LAYOUT, restyle_only=True)


def timer_tick(timer_interval_sec: float | None = None) -> None:
    """
    Wird periodisch vom App-Timer aufgerufen (einstellbare Rate, z. B. 10 Hz).
    Hier: Domain-Logik ausführen und Sinus-Demo-Plot aktualisieren (animierte Phase).
    timer_interval_sec: Für Performance-Budget; wenn None, wird TIMER_INTERVAL_SEC aus der Umgebung gelesen (Default 0.1).
    """
    global _sine_phase, _DEBUG_PLOT_FIRST_RUN, _perf_tick_durations_ms, _perf_tick_count
    interval = timer_interval_sec
    if interval is None:
        interval = float(os.environ.get("TIMER_INTERVAL_SEC", "0.1"))
    if _DEBUG_PLOT_FIRST_RUN:
        _DEBUG_PLOT_FIRST_RUN = False
        debug_plot_binding()
    t0 = time.perf_counter()
    run_domain_logic()
    _sine_phase += 0.00  # leichte Animation
    _update_sine_demo()
    if ENABLE_PERF_STATS:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        _perf_tick_durations_ms.append(elapsed_ms)
        if len(_perf_tick_durations_ms) > PERF_HISTORY_SIZE:
            _perf_tick_durations_ms.pop(0)
        _perf_tick_count += 1
        if _perf_tick_count % REPORT_EVERY_TICKS == 0:
            s = get_perf_stats(interval)
            msg = (
                f"Tick: last={s['last_ms']:.2f} ms, avg={s['avg_ms']:.2f} ms, "
                f"budget={s['budget_ms']:.0f} ms, headroom={s['headroom_pct']:.0f}%"
            )
            if s.get("cpu_pct") is not None:
                msg += f", CPU={s['cpu_pct']:.1f}%"
            print(f"[perf] {msg}")
            # Optional: in GUI anzeigen, wenn ein Label mit user_id "perf_status" existiert
            try:
                gui_binding.set("perf_status", msg)
            except Exception:
                pass


def solve_task() -> None:
    """
    Einstieg für die eigentliche Fach-Aufgabe.
    Wird typisch aus user_callbacks.py oder einem Timer aufgerufen.
    """
    run_domain_logic()
    _update_sine_demo()
