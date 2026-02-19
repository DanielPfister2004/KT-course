"""
GUI-Binding: Getter/Setter für fachliche Größen (semantische Keys).

Hier findet die Kopplung zwischen User-Logik und GUI statt. Statt path_ids
(row_1.widget_5) nutzt der Rest der App logische Namen (z. B. "power", "gain").

- SEMANTIC_BINDING: Wird automatisch aus dem Layout befüllt, wenn Widgets die Prop "user_id" haben.
  Optional kannst du Einträge hier manuell ergänzen (merge=True bei update_binding_from_layout).
- user_id im Layout: Im Property-Editor (Grid-Editor/Development-App) pro Widget "User-ID" setzen (z. B. power, gain).
  Dann wird das Binding automatisch erzeugt – kein manuelles Dict nötig.
- get(key): Liest den aktuellen Wert aus dem State.
- set(key, value): Schreibt in State und aktualisiert Output-Widgets (LED, VU-Meter) über die Registry.

Analogie Qt: Wie QObject.property(name) / setProperty(name, value); user_id = logischer Name.
"""
from __future__ import annotations

from typing import Any


# Logischer Name (fachliche Größe) → path_id. Wird bei App-Start aus Layout (props.user_id) befüllt;
# du kannst zusätzlich Einträge hier setzen (bleiben erhalten, wenn update_binding_from_layout(merge=True)).
SEMANTIC_BINDING: dict[str, str] = {}


def update_binding_from_layout(layout: dict, merge: bool = False) -> None:
    """
    Befüllt SEMANTIC_BINDING aus dem Layout: für jedes Widget mit props.user_id (nicht leer)
    wird user_id → path_id eingetragen. Bei merge=True bleiben bestehende Einträge erhalten;
    bei merge=False (Default) wird das Dict zuerst geleert (Layout ist dann die einzige Quelle).
    """
    from app_builder import collect_semantic_binding
    collected = collect_semantic_binding(layout)
    if not merge:
        SEMANTIC_BINDING.clear()
    SEMANTIC_BINDING.update(collected)


def _client_state_and_registry() -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    """State, Widget-Registry und State-Input-Registry aus dem aktuellen Client-Kontext (NiceGUI)."""
    try:
        from nicegui import ui
        client = ui.context.client
        if client is None:
            return None, None, None
        state = getattr(client, "state", None)
        registry = getattr(client, "widget_registry", None)
        state_input_registry = getattr(client, "state_input_registry", None)
        return state, registry, state_input_registry
    except Exception:
        return None, None, None


def get(key: str, default: Any = None) -> Any:
    """
    Liest den Wert der fachlichen Größe key (über SEMANTIC_BINDING → path_id → state).
    Nur in GUI-Kontext aufrufen (z. B. in Callbacks, Timer); sonst default.
    """
    path_id = SEMANTIC_BINDING.get(key)
    if not path_id:
        return default
    state, _, _ = _client_state_and_registry()
    if state is None:
        return default
    return state.get(path_id, default)


def set(key: str, value: Any) -> None:
    """
    Setzt die fachliche Größe key: schreibt in State und aktualisiert die Anzeige.
    - Widget-Registry: LED (set_state), VU-Meter (set_value), Markdown (set_content).
    - State-Input-Registry: editierbare Markdown-Textarea (.value) wird gesetzt.
    Nur in GUI-Kontext aufrufen (Callbacks, Timer).
    """
    path_id = SEMANTIC_BINDING.get(key)
    if not path_id:
        return
    state, registry, state_input_registry = _client_state_and_registry()
    str_value = str(value) if value is not None else ""
    if state is not None:
        state[path_id] = value
    if registry is not None and path_id in registry:
        w = registry[path_id]
        if hasattr(w, "set_state"):
            w.set_state(value)
        elif hasattr(w, "set_value"):
            try:
                w.set_value(float(value))
            except (TypeError, ValueError):
                pass
        elif hasattr(w, "set_content"):
            w.set_content(str_value)
    if state_input_registry is not None and path_id in state_input_registry:
        inp = state_input_registry[path_id]
        if hasattr(inp, "value"):
            inp.value = str_value
            if hasattr(inp, "update"):
                inp.update()


def clear_markdown(key: str) -> None:
    """
    Löscht den Inhalt der Markdown-Box (user_id = key).
    Gleichbedeutend mit set(key, ""). Nur in GUI-Kontext aufrufen.
    """
    set(key, "")


def update_plot(
    key: str,
    data: Any,
    layout: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    *,
    fallback_to_any: bool = True,
    restyle_only: bool = False,
) -> None:
    """
    Aktualisiert ein Plotly-Widget über die User-ID (key).
    key muss im Layout als user_id des Plot-Widgets gesetzt sein (SEMANTIC_BINDING).
    data: Liste von Traces (dict mit x, y, mode, …); x/y dürfen Listen oder NumPy-Arrays sein.
    restyle_only: Bei True nur x/y per restyle (weniger Daten, oft flüssiger bei Animation).
    fallback_to_any: Wenn key nicht gebunden ist, erstes Plotly-Widget in der Registry nutzen (Default True).
    Nur in GUI-Kontext aufrufen (Callbacks, Timer).
    """
    import os as _os
    _debug = _os.environ.get("DEBUG_GUI_BINDING", "").strip().lower() in ("1", "true", "yes")
    path_id = SEMANTIC_BINDING.get(key)
    _, registry, _ = _client_state_and_registry()
    if registry is None:
        if _debug:
            print("[update_plot] widget_registry ist None (kein GUI-Kontext?)")
        return
    if not path_id or path_id not in registry:
        if path_id and path_id not in registry and _debug:
            plotly_paths = [pid for pid, w in registry.items() if hasattr(w, "update_figure")]
            print(f"[update_plot] path_id={path_id!r} nicht in widget_registry. Plotly-Widgets: {plotly_paths}")
        if not path_id and _debug:
            print(f"[update_plot] key={key!r} nicht in SEMANTIC_BINDING. Verfügbar: {list(SEMANTIC_BINDING.keys())}")
        if fallback_to_any:
            for pid, w in registry.items():
                if hasattr(w, "update_figure"):
                    w.update_figure(data, layout=layout, config=config, restyle_only=restyle_only)
                    if _debug and not path_id:
                        print(f"[update_plot] Fallback: erstes Plotly-Widget {pid!r} aktualisiert (setze user_id={key!r} für feste Zuordnung)")
                    return
        return
    w = registry[path_id]
    if hasattr(w, "update_figure"):
        w.update_figure(data, layout=layout, config=config, restyle_only=restyle_only)
    elif _debug:
        print(f"[update_plot] Widget {path_id!r} hat keine update_figure-Methode")
