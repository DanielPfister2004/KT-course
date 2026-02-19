"""
Layout-Modell für den visuellen Builder: laden, speichern, Knoten zugreifen/ändern.
Pfad = Liste von Indizes: [0, 1] = dashboard.children[0].children[1].

Ursprünglich in labs/layout_builder; hier im app_builder zentral, damit development_app
und grid_editor (und ggf. layout_builder-App) eine gemeinsame Quelle nutzen.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_layout() -> dict:
    """Leeres Layout mit nur Dashboard-Root."""
    return {
        "version": 1,
        "dashboard": {
            "id": "dashboard",
            "layout_type": "rows_columns",
            "children": [],
        },
    }


def load_layout(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_layout(layout: dict, path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2, ensure_ascii=False)


def get_node(layout: dict, path: list[int]) -> dict | None:
    """Knoten an path (Liste von children-Indizes). path=[] => dashboard."""
    if not path:
        return layout.get("dashboard")
    node = layout.get("dashboard")
    for i in path:
        if node is None or i >= len(node.get("children", [])):
            return None
        node = node["children"][i]
    return node


def get_parent_and_index(layout: dict, path: list[int]) -> tuple[dict | None, int | None]:
    """(Parent-Knoten, Index des Kindes in parent.children). Bei path=[] => (None, None)."""
    if not path:
        return None, None
    parent = get_node(layout, path[:-1])
    if parent is None:
        return None, None
    return parent, path[-1]


def get_children(node: dict) -> list[dict]:
    return node.get("children", [])


def get_all_paths_dfs(layout: dict) -> list[list[int]]:
    """Alle Knoten-Pfade in Tiefensuche-Reihenfolge (für Cursor hoch/runter)."""
    out: list[list[int]] = []

    def walk(path: list[int]) -> None:
        out.append(path)
        node = get_node(layout, path)
        if node is None:
            return
        for i in range(len(get_children(node))):
            walk(path + [i])

    walk([])
    return out


def _next_id(children: list[dict], prefix: str) -> str:
    used = {n.get("id", "") for n in children if isinstance(n.get("id"), str)}
    for i in range(1, 1000):
        cand = f"{prefix}_{i}"
        if cand not in used:
            return cand
    return f"{prefix}_new"


CONTAINER_DEFAULTS = {
    "rows_columns": {"type": "container", "id": "", "layout_type": "rows_columns", "columns": 4, "align_items": "center", "children": []},
    "column": {"type": "container", "id": "", "layout_type": "column", "children": []},
    "grid": {"type": "container", "id": "", "layout_type": "grid", "columns": 2, "children": []},
    "expansion": {"type": "container", "id": "", "label": "", "layout_type": "expansion", "children": []},
    "scroll": {"type": "container", "id": "", "layout_type": "scroll", "children": []},
    "card": {"type": "container", "id": "", "layout_type": "card", "children": []},
    "splitter": {"type": "container", "id": "", "layout_type": "splitter", "orientation": "horizontal", "value": 30, "children": []},
    "tabs": {"type": "container", "id": "", "layout_type": "tabs", "children": []},
    "group": {"type": "group", "id": "", "label": "", "children": []},
    "tab": {"type": "tab", "id": "", "label": "", "children": []},
}

WIDGET_DEFAULTS: dict[str, dict] = {
    # Markdown (oben in der Palette: Anzeige + optional editierbar für Assignments)
    "markdown": {
        "type": "widget",
        "id": "",
        "widget_type": "markdown",
        "props": {
            "content": "",
            "editable": False,
            "placeholder": "Ihre Antwort oder Anmerkung …",
            "extras": "latex",
            "height": "300px",
            "height_mode": "fixed",
            "render_markdown": True,
            "font": "default",
            "framed": False,
        },
    },
    # Standard (NiceGUI/Browser)
    "checkbox": {"type": "widget", "id": "", "widget_type": "checkbox", "props": {"label": "", "value": False}},
    "slider": {
        "type": "widget",
        "id": "",
        "widget_type": "slider",
        "props": {"label": "", "min": 0, "max": 10, "value": 1, "step": 0.01, "label_position": "below", "label_width": "", "control_width": ""},
    },
    "button": {"type": "widget", "id": "", "widget_type": "button", "props": {"label": ""}},
    "toggle_button": {
        "type": "widget",
        "id": "",
        "widget_type": "toggle_button",
        "props": {"icon": "toggle_on", "label": "", "label_inactive": "", "value": False, "strikethrough_inactive": True},
    },
    "input": {"type": "widget", "id": "", "widget_type": "input", "props": {"label": "", "value": ""}},
    "number_input": {"type": "widget", "id": "", "widget_type": "number_input", "props": {"label": "", "value": 0}},
    "select": {"type": "widget", "id": "", "widget_type": "select", "props": {"label": "", "options": [], "value": None}},
    "label": {
        "type": "widget",
        "id": "",
        "widget_type": "label",
        "props": {"text": "", "heading": "", "font": ""},
    },
    "link": {"type": "widget", "id": "", "widget_type": "link", "props": {"url": "", "text": "", "target": "_blank"}},
    "image": {"type": "widget", "id": "", "widget_type": "image", "props": {"src": "", "alt": ""}},
    # Custom (lab_suite/widgets)
    "banner_vue": {
        "type": "widget",
        "id": "",
        "widget_type": "banner_vue",
        "props": {
            "text1": "KT-Labor",
            "text2": "Übung",
            "text3": "1",
            "height": "80px",
            "font_family": "",
            "font_size1": "",
            "font_size2": "",
            "font_size3": "",
            "text_color": "",
            "gradient_start": "#0d47a1",
            "gradient_end": "#1565c0",
            "flex": False,
        },
    },
    "gain_control_vue": {"type": "widget", "id": "", "widget_type": "gain_control_vue", "props": {"label": "Gain", "min": 0, "max": 10, "value": 1.0}},
    "vu_meter": {"type": "widget", "id": "", "widget_type": "vu_meter", "props": {"min": 0, "max": 1.0, "show_value": True, "width": "120px", "height": "80px"}},
    "led": {"type": "widget", "id": "", "widget_type": "led", "props": {"label": "", "size": 16}},
    "image_icon_demo": {"type": "widget", "id": "", "widget_type": "image_icon_demo", "props": {"image_src": "", "image_alt": "Image", "show_icon": True, "label": ""}},
    # Plotly: generischer Graph (DSP: Plot, PlotXY, Spektrum, Histogram, Scatter); Daten von App per update_figure
    "plotly_graph": {
        "type": "widget",
        "id": "",
        "widget_type": "plotly_graph",
        "props": {
            "height": "400px",
            "plotly_script_url": "/widgets-static/plotly.min.js",
            "title": "",
            "xaxis_title": "",
            "yaxis_title": "",
            "xaxis_type": "linear",
            "yaxis_type": "linear",
            "xaxis_autorange": True,
            "yaxis_autorange": True,
            "xaxis_range": "",
            "yaxis_range": "",
            "trace_count": 1,
            "mode": "lines",
            "marker_size": 6,
            "marker_symbol": "circle",
            "marker_color": "",
            "line_dash": "solid",
            "line_width": 1.5,
            "responsive": True,
        },
    },
}

# Optional per-widget or per-prop hints for the property editor (label, min, max, options).
WIDGET_PROP_HINTS: dict[str, dict[str, dict[str, Any]]] = {
    "slider": {
        "label_position": {
            "label": "Label-Position",
            "type": "string",
            "options": ["below", "above", "inline"],
        },
        "label_width": {"label": "Label-Breite (inline, z.B. 80px)", "type": "string"},
        "control_width": {"label": "Control-Breite (inline, z.B. 120px)", "type": "string"},
    },
    "label": {
        "heading": {
            "label": "Überschrift (HTML-Stil)",
            "type": "string",
            "options": ["", "h1", "h2", "h3", "h4", "h5", "h6"],
        },
        "font": {
            "label": "Schrift",
            "type": "string",
            "options": ["", "sans-serif", "serif", "monospace"],
        },
    },
    "markdown": {
        "content": {"label": "Inhalt (Markdown, LaTeX mit $$...$$)", "type": "string"},
        "editable": {"label": "Editierbar (Textarea für Studenten-Antwort)", "type": "boolean"},
        "placeholder": {"label": "Placeholder Textarea (bei editierbar)", "type": "string"},
        "extras": {"label": "Markdown-Extras (z. B. latex)", "type": "string"},
        "height": {"label": "Höhe (z. B. 300px); bei fixed = max. Höhe + Scroll, bei auto = min. Höhe Textarea", "type": "string"},
        "height_mode": {
            "label": "Höhe",
            "type": "string",
            "options": ["fixed", "auto"],
        },
        "render_markdown": {"label": "Markdown rendern (aus: nur Plain-Text; Quelltext bleibt auch bei globalem „Markdown Quelltext“-Toggle sichtbar, z. B. für Live-Huffman)", "type": "boolean"},
        "font": {
            "label": "Schrift",
            "type": "string",
            "options": ["default", "monospace"],
        },
        "framed": {"label": "Rahmen (Box um das Widget; sparsam für Gruppierung nutzen)", "type": "boolean"},
    },
    "banner_vue": {
        "text1": {"label": "Text 1 (z. B. Modul/Titel)"},
        "text2": {"label": "Text 2 (z. B. Thema)"},
        "text3": {"label": "Text 3 (z. B. Übungsnummer)"},
        "height": {"label": "Höhe (z. B. 80px, 5rem)"},
        "font_family": {
            "label": "Schriftart",
            "type": "string",
            "options": ["", "sans-serif", "serif", "monospace", "Consolas", "Roboto Mono", "JetBrains Mono", "Courier New", "Source Code Pro"],
        },
        "font_size1": {"label": "Schriftgröße Text 1 (z. B. 1.2rem)"},
        "font_size2": {"label": "Schriftgröße Text 2"},
        "font_size3": {"label": "Schriftgröße Text 3"},
        "text_color": {"label": "Textfarbe (Hex, z. B. #fff)"},
        "gradient_start": {"label": "Verlauf Start (Hex)"},
        "gradient_end": {"label": "Verlauf Ende (Hex)"},
    },
    "plotly_graph": {
        "height": {"label": "Höhe (z. B. 400px, 50vh)", "type": "string"},
        "plotly_script_url": {"label": "Plotly.js URL (Default: /widgets-static/plotly.min.js für Offline; leer = CDN)", "type": "string"},
        "title": {"label": "Titel (über dem Plot)", "type": "string"},
        "xaxis_title": {"label": "X-Achse Label", "type": "string"},
        "yaxis_title": {"label": "Y-Achse Label", "type": "string"},
        "xaxis_type": {"label": "X-Achse Skalierung", "type": "string", "options": ["linear", "log", "date", "category"]},
        "yaxis_type": {"label": "Y-Achse Skalierung", "type": "string", "options": ["linear", "log", "date", "category"]},
        "xaxis_autorange": {"label": "X-Achse Auto-Range", "type": "boolean"},
        "yaxis_autorange": {"label": "Y-Achse Auto-Range", "type": "boolean"},
        "xaxis_range": {"label": "X-Achse Range (z. B. 0,10)", "type": "string"},
        "yaxis_range": {"label": "Y-Achse Range (z. B. -1,1)", "type": "string"},
        "trace_count": {"label": "Anzahl Traces (Vorgabe)", "type": "integer", "min": 1, "max": 20},
        "mode": {"label": "Darstellung", "type": "string", "options": ["lines", "markers", "lines+markers"]},
        "marker_size": {"label": "Marker-Größe", "type": "number", "min": 1, "max": 30},
        "marker_symbol": {"label": "Marker-Symbol", "type": "string", "options": ["circle", "square", "diamond", "cross", "x", "triangle-up", "triangle-down", "star", "hexagon"]},
        "marker_color": {"label": "Marker-Farbe (Hex)", "type": "color"},
        "line_dash": {"label": "Linienart", "type": "string", "options": ["solid", "dot", "dash", "longdash", "dashdot", "longdashdot"]},
        "line_width": {"label": "Linienbreite", "type": "number", "min": 0.5, "max": 10},
        "responsive": {"label": "Responsive", "type": "boolean"},
    },
}

COMMON_PROP_SPECS: list[dict[str, Any]] = [
    {"key": "user_id", "default": "", "type": "string", "label": "User-ID (fachliche Größe für get/set, z.B. power, gain)"},
    {"key": "text_color", "default": "", "type": "color", "label": "Textfarbe (Hex oder Picker)"},
    {"key": "bg_color", "default": "", "type": "color", "label": "Hintergrundfarbe (Hex oder Picker)"},
    {"key": "width", "default": "", "type": "string", "label": "Breite (z.B. 100px, 50%)"},
    {"key": "min_width", "default": "", "type": "string", "label": "Mindestbreite (z.B. 80px)"},
    {"key": "max_width", "default": "", "type": "string", "label": "Max. Breite (z.B. 200px)"},
    {"key": "flex", "default": False, "type": "boolean", "label": "Flex (teilt Platz mit Nachbarn, responsiv)"},
]


def _infer_prop_type(value: Any) -> str:
    """Infer editor input type from default value."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "json"
    return "string"


def _prop_label(key: str) -> str:
    """Human-readable label from prop key."""
    return key.replace("_", " ").strip().title() or key


def get_prop_editor_specs(widget_type: str) -> list[dict[str, Any]]:
    """
    Return a list of property specs for the property editor, derived from WIDGET_DEFAULTS.
    New widgets: add an entry to WIDGET_DEFAULTS with props → editor adapts automatically.
    Optional WIDGET_PROP_HINTS[widget_type][prop_key] can override label, type, min, max, options.
    Each spec: {"key": str, "default": Any, "type": str, "label": str, "min"?: number, "max"?: number, "options"?: list}.
    """
    if widget_type not in WIDGET_DEFAULTS:
        return []
    props = WIDGET_DEFAULTS[widget_type].get("props", {})
    hints = WIDGET_PROP_HINTS.get(widget_type, {})
    out: list[dict[str, Any]] = []
    for key, default in props.items():
        h = hints.get(key, {})
        spec: dict[str, Any] = {
            "key": key,
            "default": default,
            "type": h.get("type") or _infer_prop_type(default),
            "label": h.get("label") or _prop_label(key),
        }
        if "min" in h:
            spec["min"] = h["min"]
        if "max" in h:
            spec["max"] = h["max"]
        if "options" in h:
            spec["options"] = h["options"]
        out.append(spec)
    for common in COMMON_PROP_SPECS:
        out.append(dict(common))
    return out


def add_child(layout: dict, parent_path: list[int], kind: str) -> dict | None:
    """
    Fügt einen neuen Knoten als Kind von parent_path ein.
    kind: "rows_columns" | "column" | "grid" | "expansion" | "scroll" | "card" | "splitter" | "tabs" | "group" | "tab" | widget_type (z. B. "checkbox").
    Gibt den neuen Knoten zurück.
    """
    parent = get_node(layout, parent_path)
    if parent is None:
        return None
    children = parent.get("children", [])
    if kind in CONTAINER_DEFAULTS:
        import copy
        node = copy.deepcopy(CONTAINER_DEFAULTS[kind])
        prefix = "container" if kind in ("rows_columns", "column", "grid", "expansion", "scroll", "card", "splitter", "tabs") else kind
    elif kind in WIDGET_DEFAULTS:
        import copy
        node = copy.deepcopy(WIDGET_DEFAULTS[kind])
        prefix = "widget"
    else:
        return None
    node["id"] = _next_id(children, prefix)
    if kind == "tab":
        node["label"] = node["id"]
    children.append(node)
    parent["children"] = children
    return node


def delete_node(layout: dict, path: list[int]) -> bool:
    """Entfernt den Knoten an path (inkl. aller Kinder)."""
    parent, index = get_parent_and_index(layout, path)
    if parent is None or index is None:
        return False
    children = parent.get("children", [])
    if index >= len(children):
        return False
    children.pop(index)
    parent["children"] = children
    return True


def move_node(layout: dict, path: list[int], direction: int) -> bool:
    """Verschiebt den Knoten um direction (-1 = hoch, +1 = runter)."""
    if not path or direction == 0:
        return False
    parent, index = get_parent_and_index(layout, path)
    if parent is None or index is None:
        return False
    children = parent["children"]
    new_index = index + direction
    if new_index < 0 or new_index >= len(children):
        return False
    children[index], children[new_index] = children[new_index], children[index]
    return True


def update_node_property(layout: dict, path: list[int], key: str, value: Any) -> bool:
    """Setzt ein Feld (id, label, layout_type, widget_type) oder props.key am Knoten."""
    node = get_node(layout, path)
    if node is None:
        return False
    if key == "props":
        if isinstance(value, dict):
            node["props"] = value
        return True
    if key.startswith("props."):
        prop_key = key[6:]
        if "props" not in node:
            node["props"] = {}
        node["props"][prop_key] = value
        return True
    node[key] = value
    return True
