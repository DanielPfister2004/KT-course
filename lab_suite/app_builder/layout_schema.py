"""
Layout-Schema für den App-Builder: Pfad-IDs, State-Defaults, Callback-Namen.

- Lade/parse layout.json
- Pfad-IDs aus Hierarchie ableiten
- Default-State pro Widget-Typ für model.state
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def path_id_to_snake(path_id: str) -> str:
    """Path-ID (e.g. top.gain_block.gain) -> snake_case for Python (top_gain_block_gain)."""
    return path_id.replace(".", "_")


def user_id_to_snake(user_id: str) -> str:
    """user_id (z. B. 'Power', 'Dampfdruck-Vorgabe') → snake_case für Python-Funktionsnamen."""
    s = str(user_id).strip()
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", s).strip("_")
    return s.lower() if s else ""


# Default-Werte für model.state pro widget_type (Wert-Widgets)
# Plot-Widgets (plotly_spectrum, plotly_graph): kein State-Eintrag für Figure;
# die App aktualisiert die Figur per Widget-Referenz; Pfad-ID dient zur Referenz.
WIDGET_STATE_DEFAULTS: dict[str, Any] = {
    "checkbox": False,
    "toggle_button": False,
    "slider": 0.0,
    "number_input": 0,
    "input": "",             # Text-Eingabe (ui.input)
    "select": None,
    "gain_control_vue": 1.0,
    "vu_meter": 0.0,
    "led": "off",
    "label": None,
    "plotly_spectrum": None,  # Kein Persist; App schreibt Figur
    "plotly_graph": None,
    "plotly_scatter": None,   # X-Y/Scatter – semantischer Hinweis, wie plotly_graph
    "plotly_histogram": None,
    "plotly_3d": None,        # 3D (Scatter3d, Surface, Mesh3d)
    "table": None,            # Zeilendaten oft von App; State optional (z. B. [])
    "image": None,            # Rastergrafik; reine Anzeige (src in props oder von App)
    "link": None,             # Hyperlink; reine Navigation (url, text in props)
    "video": None,            # Video/YouTube Embed oder Verlinkung
    "youtube": None,          # wie video, semantisch für YouTube
    "image_icon_demo": None,  # Vue-Widget: Bild + Icon; reine Anzeige
    "markdown": "",  # Anzeige: optional programmatischer Inhalt; editable: Studenten-Antwort
}


def _collect_widgets(
    node: dict[str, Any],
    parent_path: str,
) -> list[tuple[str, str, dict]]:
    """
    Rekursiv alle Widgets sammeln. Returns list of (path_id, widget_type, props).
    """
    out: list[tuple[str, str, dict]] = []
    node_id = node.get("id", "")
    node_type = node.get("type", "widget")
    path = f"{parent_path}.{node_id}" if parent_path else node_id

    if node_type == "widget":
        wt = node.get("widget_type", "")
        if not isinstance(wt, str):
            wt = (wt.get("label") or wt.get("value") or "") if isinstance(wt, dict) else str(wt)
        props = node.get("props", {})
        out.append((path, wt, props))
        return out

    if node_type in ("container", "group", "tab"):
        for ch in node.get("children", []):
            out.extend(_collect_widgets(ch, path))
    return out


def _collect_widgets_from_dashboard(layout: dict) -> list[tuple[str, str, dict]]:
    """Wie _collect_widgets, aber Pfad-IDs ohne 'dashboard.' (nur Kinder des Dashboard-Root)."""
    dashboard = layout.get("dashboard", {})
    out: list[tuple[str, str, dict]] = []
    for child in dashboard.get("children", []):
        out.extend(_collect_widgets(child, ""))
    return out


def collect_semantic_binding(layout: dict) -> dict[str, str]:
    """
    Erzeugt aus dem Layout das Binding user_id → path_id für alle Widgets mit gesetzter props.user_id.
    Bei doppelten user_ids gewinnt der zuletzt traversierte (last wins).
    """
    binding: dict[str, str] = {}
    for path_id, _widget_type, props in _collect_widgets_from_dashboard(layout):
        uid = (props.get("user_id") or "")
        if isinstance(uid, dict):
            uid = (uid.get("value") or uid.get("label") or "").strip()
        else:
            uid = str(uid).strip()
        if uid:
            binding[uid] = path_id
    return binding


def _coerce_numeric_state(value: Any, default: float) -> Any:
    """Coerce value to float so sliders/numbers never receive strings (avoids Quasar toFixed error)."""
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def collect_state_entries(layout: dict) -> dict[str, Any]:
    """
    Aus dem geparsten Layout (dict) alle State-Einträge ableiten.
    Returns dict: path_id -> default value (für model.state).
    Numeric widgets (slider, number_input, gain_control_vue, vu_meter) werden immer als float gespeichert.
    """
    entries: dict[str, Any] = {}
    for path_id, widget_type, props in _collect_widgets_from_dashboard(layout):
        if not isinstance(widget_type, str):
            widget_type = str(widget_type) if widget_type is not None else ""
        default = WIDGET_STATE_DEFAULTS.get(widget_type)
        if default is None and widget_type in ("number_input", "slider"):
            default = props.get("value", 0)
        elif default is None and widget_type == "checkbox":
            default = props.get("value", False)
        elif default is None and widget_type == "gain_control_vue":
            default = props.get("value", 1.0)
        elif default is None and widget_type == "led":
            default = props.get("state", "off")
        elif widget_type in ("label", "button", "image", "link", "video", "youtube", "image_icon_demo"):
            continue  # reine Anzeige/Navigation, kein State
        if default is not None or widget_type not in ("label", "button", "image", "link", "video", "youtube", "image_icon_demo"):
            raw = props.get("value", props.get("state", default))
            if widget_type in ("slider", "number_input", "gain_control_vue", "vu_meter"):
                raw = _coerce_numeric_state(raw, 0.0 if widget_type == "number_input" else 1.0 if widget_type in ("slider", "gain_control_vue") else 0.0)
            entries[path_id] = raw
    return entries


def collect_all_widget_path_ids(layout: dict) -> list[str]:
    """Alle path_ids von Widgets im Layout (für Property-Editor-Dropdown, damit alle Widget-Typen erscheinen)."""
    return [path_id for path_id, _, _ in _collect_widgets_from_dashboard(layout)]


def _normalize_user_id(uid: Any) -> str:
    """user_id aus props (kann str oder dict sein) → bereinigter String."""
    if uid is None:
        return ""
    if isinstance(uid, dict):
        uid = (uid.get("value") or uid.get("label") or "").strip()
    return str(uid).strip()


def collect_callback_names(layout: dict) -> list[tuple[str, str, str, str, str]]:
    """
    Liste aller Callbacks: (path_id, callback_kind, python_name, widget_type, merge_key).
    callback_kind: "change" | "click" | "relayout"
    merge_key: "user_id=<id>" wenn Widget user_id hat und diese eindeutig ist, sonst "path_id:<path_id>".
    Bei user_id wird der Python-Name on_<user_id_snake>_change/click verwendet → Callbacks bleiben bei Umplatzierung erhalten.
    """
    widgets = _collect_widgets_from_dashboard(layout)
    # Nur Widget-Typen mit Callbacks
    callback_widgets: list[tuple[str, str, dict]] = []
    for path_id, widget_type, props in widgets:
        if not isinstance(widget_type, str):
            widget_type = str(widget_type) if widget_type is not None else ""
        if widget_type == "button":
            callback_widgets.append((path_id, "click", widget_type, props))
        elif widget_type in ("checkbox", "toggle_button", "slider", "number_input", "input", "select", "gain_control_vue"):
            callback_widgets.append((path_id, "change", widget_type, props))
        elif widget_type in ("plotly_spectrum", "plotly_graph", "plotly_scatter", "plotly_histogram", "plotly_3d"):
            callback_widgets.append((path_id, "relayout", widget_type, props))
        elif widget_type == "markdown" and props.get("editable"):
            callback_widgets.append((path_id, "change", widget_type, props))
    # Eindeutigkeit user_id: nur wenn genau ein Widget diese user_id hat, nutzen wir sie für Namen + Merge
    user_id_counts: Counter[str] = Counter()
    for _path_id, _kind, _wt, props in callback_widgets:
        uid = _normalize_user_id(props.get("user_id"))
        if uid:
            user_id_counts[uid] += 1
    callbacks: list[tuple[str, str, str, str, str]] = []
    for path_id, kind, widget_type, props in callback_widgets:
        uid = _normalize_user_id(props.get("user_id"))
        use_user_id = bool(uid) and user_id_counts.get(uid, 0) == 1
        if use_user_id:
            snake = user_id_to_snake(uid) or path_id_to_snake(path_id)
            merge_key = f"user_id={uid}"
        else:
            snake = path_id_to_snake(path_id)
            merge_key = f"path_id:{path_id}"
        if kind == "click":
            callbacks.append((path_id, kind, f"on_{snake}_click", widget_type, merge_key))
        elif kind == "relayout":
            callbacks.append((path_id, kind, f"on_{snake}_relayout", widget_type, merge_key))
        else:
            callbacks.append((path_id, kind, f"on_{snake}_change", widget_type, merge_key))
    return callbacks


def get_widget_node_by_path_id(layout: dict, path_id: str) -> dict | None:
    """
    Findet den Widget-Knoten im Layout anhand der path_id (z. B. "row_1.widget_2").
    Gibt das Knoten-Dict (type=widget, id, widget_type, props) zurück oder None.
    """
    if not path_id or not path_id.strip():
        return None
    segments = [s.strip() for s in path_id.split(".") if s.strip()]
    if not segments:
        return None
    dashboard = layout.get("dashboard", {})
    node: dict | None = dashboard
    for seg in segments:
        if node is None:
            return None
        children = node.get("children", [])
        found = None
        for ch in children:
            if ch.get("id") == seg:
                found = ch
                break
        node = found
    if node is not None and node.get("type") == "widget":
        return node
    return None


def load_layout(path: str | Path) -> dict:
    """Layout aus JSON-Datei laden."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)
