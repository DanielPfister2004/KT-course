"""
Layout-Renderer: Baut NiceGUI-UI rekursiv aus Layout-JSON.

- Unterstützt: Container (rows_columns, column, grid, expansion, scroll, card, splitter, tabs), Gruppe, Tab, alle spezifizierten Widgets (inkl. markdown mit LaTeX, Scroll, optional editable). Grid-Kinder optional col_span/row_span.
- Pfad-IDs werden durch die Hierarchie durchgereicht; State und Callbacks werden per path_id gebunden.
- NiceGUI wird erst bei Aufruf von build_ui_from_layout importiert (Skeleton-Generator bleibt ohne NG-Abhängigkeit).
"""
from __future__ import annotations

import html as _html
import json
from typing import Any, Callable


def _ui():
    from nicegui import ui
    return ui


def build_ui_from_layout(
    layout: dict,
    state: dict[str, Any],
    callbacks: dict[str, Any],
    *,
    title: str | None = "Development-App (App-Builder PoC)",
    on_state_change: Callable[[], None] | None = None,
    get_edit_mode: Callable[[], bool] | None = None,
    on_edit_select_path: Callable[[str], None] | None = None,
    widget_registry: dict[str, Any] | None = None,
    state_input_registry: dict[str, Any] | None = None,
    sticky_header_rows: int = 0,
    on_after_sticky_content: Callable[[], None] | None = None,
    get_show_markdown_source: Callable[[], bool] | None = None,
    register_markdown_view: Callable[[Any, Any], None] | None = None,
) -> None:
    """
    Baut die NiceGUI-UI aus dem Layout-Dict.
    Verbindet Widgets mit state und callbacks (Pfad-IDs).
    on_state_change: optional, wird nach jeder State-Änderung aufgerufen (z. B. für reaktive State-Anzeige).
    get_edit_mode: optional, Callable das bei Klick ausgewertet wird; wenn True, wird on_edit_select_path(path_id) statt des echten Callbacks aufgerufen.
    on_edit_select_path: optional, wird mit path_id aufgerufen wenn Nutzer im Edit-Modus auf ein Widget klickt (z. B. Auswahl/Header setzen).
    widget_registry: optional, Dict path_id → Widget-Instanz; wird für Output-Widgets (led, vu_meter, ggf. plotly) befüllt, damit der User Setter (set_value, set_state, update_figure) aufrufen kann.
    state_input_registry: optional, Dict path_id → Widget mit .value (z. B. Textarea); vor Persistenz können aktuelle Werte daraus in state gelesen werden.
    sticky_header_rows: wenn > 0, werden die ersten N Zeilen (dashboard.children) in einem sticky Wrapper gerendert, danach on_after_sticky_content aufgerufen, dann der Rest in einer scroll_area.
    on_after_sticky_content: optional, wird nach dem Rendern der sticky Zeilen (und vor Schließen des Wrappers) aufgerufen, z. B. für globale Schalter.
    get_show_markdown_source: optional; bei editierbarem Markdown wird dieser Modus (True = Quelltext) für Anzeige genutzt; lokale Quelltext/Vorschau-Buttons können ausgeblendet werden.
    register_markdown_view: optional, (source_container, preview_container[, update_preview_from_state[, always_show_source]]) pro editierbarem Markdown; beim Toggle auf Vorschau kann die App update_preview_from_state() aufrufen. always_show_source=True (z. B. bei render_markdown=False) erzwingt Quelltext-Anzeige unabhängig vom globalen „Markdown Quelltext“-Toggle (z. B. für Plain-Text-Eingabe mit Live-Output wie Huffman).
    """
    ui = _ui()
    ui.add_head_html(
        '<style>.toggle-btn-inactive-strike{position:relative;}.toggle-btn-inactive-strike::after{content:"";position:absolute;left:0;top:0;right:0;bottom:0;border-left:2px solid rgba(128,128,128,0.8);transform-origin:center;transform:rotate(-35deg) scaleX(1.2);pointer-events:none;}</style>'
    )
    appearance = layout.get("appearance") or {}
    dashboard = layout.get("dashboard", {})
    children = dashboard.get("children", [])

    edit_kw = {
        "get_edit_mode": get_edit_mode,
        "on_edit_select_path": on_edit_select_path,
        "appearance": appearance,
        "widget_registry": widget_registry,
        "state_input_registry": state_input_registry,
        "get_show_markdown_source": get_show_markdown_source,
        "register_markdown_view": register_markdown_view,
    }

    n_sticky = max(0, int(sticky_header_rows)) if sticky_header_rows else 0
    sticky_children = children[:n_sticky] if n_sticky else []
    rest_children = children[n_sticky:] if n_sticky else children

    def _render(children_to_render: list, parent_path: str = "") -> None:
        try:
            _render_children(
                children_to_render, parent_path, state, callbacks, ui, on_state_change,
                **edit_kw,
            )
        except Exception as e:
            ui.notify(f"Layout-Fehler: {e}", type="negative")
            ui.label(f"Layout-Fehler (Inhalt nach Sticky-Header): {e}").classes("text-negative text-weight-medium p-4")
            import traceback
            ui.element("pre").classes("p-4 text-caption overflow-auto").inner_html = _html.escape(traceback.format_exc())

    page_style = _page_wrapper_style(appearance)
    if page_style:
        with ui.element("div").style(page_style):
            if title:
                ui.label(title).classes("text-h4")
            if n_sticky > 0 and sticky_children:
                _sticky_style = (
                    "position: sticky; top: 0; z-index: 50; "
                    "background: var(--q-body-bg, #fff); "
                    "box-shadow: 0 1px 3px rgba(0,0,0,.08); padding-bottom: 8px;"
                )
                with ui.element("div").classes("w-full").style(_sticky_style):
                    _render(sticky_children)
                    if on_after_sticky_content:
                        on_after_sticky_content()
                _scroll_style = _scroll_content_style(appearance)
                if _scroll_style:
                    # Innerer Wrapper mit min-height: min-content verhindert, dass Flex-Inhalt (z. B. Zeilen mit Markdown-Widgets) auf 0 zusammenschrumpft
                    with ui.element("div").classes("w-full").style(_scroll_style):
                        with ui.element("div").classes("w-full").style("min-height: min-content; display: block;"):
                            _render(rest_children)
                else:
                    with ui.element("div").classes("w-full"):
                        _render(rest_children)
            else:
                _render(children)
    else:
        if title:
            ui.label(title).classes("text-h4")
        if n_sticky > 0 and sticky_children:
            _sticky_style = (
                "position: sticky; top: 0; z-index: 50; "
                "background: var(--q-body-bg, #fff); "
                "box-shadow: 0 1px 3px rgba(0,0,0,.08); padding-bottom: 8px;"
            )
            with ui.element("div").classes("w-full").style(_sticky_style):
                _render(sticky_children)
                if on_after_sticky_content:
                    on_after_sticky_content()
            _scroll_style = _scroll_content_style(appearance)
            if _scroll_style:
                with ui.element("div").classes("w-full").style(_scroll_style):
                    with ui.element("div").classes("w-full").style("min-height: min-content; display: block;"):
                        _render(rest_children)
            else:
                with ui.element("div").classes("w-full"):
                    _render(rest_children)
        else:
            _render(children)


def _path(parent_path: str, node_id: str) -> str:
    return f"{parent_path}.{node_id}" if parent_path else node_id


def _to_css_value(val: Any) -> str | None:
    """Erzeugt einen CSS-tauglichen String aus appearance/node-Werten (auch wenn als Dict gespeichert)."""
    if val is None:
        return None
    if isinstance(val, dict):
        out = val.get("value") or val.get("label") or val.get("content")
        if out is None:
            return None
        s = str(out).strip()
        return s if s else None
    s = str(val).strip()
    return s if s else None


def _page_wrapper_style(appearance: dict) -> str:
    """CSS style for page wrapper from layout.appearance (page_padding, page_background)."""
    parts = []
    padding = _to_css_value(appearance.get("page_padding"))
    if padding:
        parts.append(f"padding: {padding}")
    bg = _to_css_value(appearance.get("page_background"))
    if bg:
        parts.append(f"background-color: {bg}")
    return "; ".join(parts) if parts else ""


def _scroll_content_style(appearance: dict) -> str | None:
    """
    CSS max-height für den Scroll-Bereich unter dem Sticky-Header.
    appearance.scroll_content_mode: "fixed" | "flex"
    - fixed: Rückgabe "max-height: <scroll_area_max_height>", Default "calc(100vh - 180px)"
    - flex: Rückgabe None (kein max-height, gesamte Seite scrollt)
    """
    raw_mode = appearance.get("scroll_content_mode") or "fixed"
    if isinstance(raw_mode, dict):
        mode = str(raw_mode.get("value") or raw_mode.get("label") or "fixed").strip().lower()
    else:
        mode = str(raw_mode).strip().lower()
    if mode == "flex":
        return None
    raw_max_h = appearance.get("scroll_area_max_height") or "calc(100vh - 180px)"
    max_h = _to_css_value(raw_max_h) if raw_max_h else None
    if not max_h:
        max_h = "calc(100vh - 180px)"
    # overflow: auto damit der Bereich bei Überlauf scrollt; Box-Größe explizit für zuverlässige Höhe
    return f"max-height: {max_h}; overflow: auto; box-sizing: border-box;"


def _merge_container_style(node_style: dict, appearance: dict) -> dict:
    """Merge appearance defaults with node style; node wins. Drops empty values. Werte immer CSS-tauglich (auch bei Dict-Speicherung)."""
    defaults = {}
    bg = _to_css_value(appearance.get("container_background"))
    if bg:
        defaults["background-color"] = bg
    pad = _to_css_value(appearance.get("container_padding"))
    if pad:
        defaults["padding"] = pad
    radius = _to_css_value(appearance.get("container_border_radius"))
    if radius:
        defaults["border-radius"] = radius
    gap = _to_css_value(appearance.get("container_gap"))
    if gap:
        defaults["gap"] = gap
    # Volle Breite, damit Container-Hintergrund (z. B. in Development-App) sichtbar ist
    if defaults:
        defaults["width"] = "100%"
        defaults["box-sizing"] = "border-box"
    merged = dict(defaults)
    for k, v in (node_style or {}).items():
        cv = _to_css_value(v)
        if cv is not None:
            merged[k] = cv
    return {k: v for k, v in merged.items() if v is not None and str(v).strip()}


def _to_float(value: Any, default: float = 0.0) -> float:
    """Coerce state/props value to float so Quasar slider/number never get strings (avoids toFixed error)."""
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _render_children(
    children: list[dict],
    parent_path: str,
    state: dict[str, Any],
    callbacks: dict[str, Any],
    ui: Any,
    on_state_change: Callable[[], None] | None = None,
    *,
    get_edit_mode: Callable[[], bool] | None = None,
    on_edit_select_path: Callable[[str], None] | None = None,
    appearance: dict | None = None,
    widget_registry: dict[str, Any] | None = None,
    state_input_registry: dict[str, Any] | None = None,
    get_show_markdown_source: Callable[[], bool] | None = None,
    register_markdown_view: Callable[[Any, Any], None] | None = None,
) -> None:
    appearance = appearance or {}
    for node in children:
        _render_node(
            node, parent_path, state, callbacks, ui, on_state_change,
            get_edit_mode=get_edit_mode, on_edit_select_path=on_edit_select_path,
            appearance=appearance, widget_registry=widget_registry,
            state_input_registry=state_input_registry,
            get_show_markdown_source=get_show_markdown_source,
            register_markdown_view=register_markdown_view,
        )


def _grid_span_class(prefix: str, span: Any, default: int = 1) -> str:
    """Tailwind class for grid span: col-span-N / row-span-N (N 1..12 or full), else col-[span_N]."""
    if span is None:
        span = default
    try:
        n = int(span)
    except (TypeError, ValueError):
        return f"{prefix}-span-full"
    if n <= 0:
        return f"{prefix}-span-full"
    if 1 <= n <= 12:
        return f"{prefix}-span-{n}"
    return f"{prefix}-[span_{n}]"


def _render_grid_children(
    children: list[dict],
    parent_path: str,
    state: dict[str, Any],
    callbacks: dict[str, Any],
    ui: Any,
    on_state_change: Callable[[], None] | None = None,
    *,
    get_edit_mode: Callable[[], bool] | None = None,
    on_edit_select_path: Callable[[str], None] | None = None,
    appearance: dict | None = None,
    widget_registry: dict[str, Any] | None = None,
    state_input_registry: dict[str, Any] | None = None,
    get_show_markdown_source: Callable[[], bool] | None = None,
    register_markdown_view: Callable[[Any, Any], None] | None = None,
) -> None:
    appearance = appearance or {}
    for node in children:
        col_span = node.get("col_span", 1)
        row_span = node.get("row_span", 1)
        span_classes = f"{_grid_span_class('col', col_span)} {_grid_span_class('row', row_span)}"
        with ui.element("div").classes(span_classes):
            _render_node(
                node, parent_path, state, callbacks, ui, on_state_change,
                get_edit_mode=get_edit_mode, on_edit_select_path=on_edit_select_path, appearance=appearance,
                widget_registry=widget_registry, state_input_registry=state_input_registry,
                get_show_markdown_source=get_show_markdown_source, register_markdown_view=register_markdown_view,
            )


def _render_splitter(
    children: list[dict],
    value: int | float,
    props_vertical: str | None,
    parent_path: str,
    state: dict[str, Any],
    callbacks: dict[str, Any],
    ui: Any,
    on_state_change: Callable[[], None] | None = None,
    *,
    get_edit_mode: Callable[[], bool] | None = None,
    on_edit_select_path: Callable[[str], None] | None = None,
    appearance: dict | None = None,
    widget_registry: dict[str, Any] | None = None,
    state_input_registry: dict[str, Any] | None = None,
    get_show_markdown_source: Callable[[], bool] | None = None,
    register_markdown_view: Callable[[Any, Any], None] | None = None,
) -> None:
    edit_kw = {"get_edit_mode": get_edit_mode, "on_edit_select_path": on_edit_select_path, "appearance": appearance or {}, "widget_registry": widget_registry, "state_input_registry": state_input_registry, "get_show_markdown_source": get_show_markdown_source, "register_markdown_view": register_markdown_view}
    before_nodes = children[0:1] if children else []
    after_nodes = children[1:2] if len(children) >= 2 else []
    splitter = ui.splitter(value=float(value)).classes("w-full")
    if props_vertical:
        splitter.props(props_vertical)
    with splitter.before:
        for node in before_nodes:
            _render_node(node, parent_path, state, callbacks, ui, on_state_change, **edit_kw)
    with splitter.after:
        for node in after_nodes:
            _render_node(node, parent_path, state, callbacks, ui, on_state_change, **edit_kw)


def _render_tabs_container(
    node: dict,
    path: str,
    state: dict[str, Any],
    callbacks: dict[str, Any],
    ui: Any,
    on_state_change: Callable[[], None] | None = None,
    *,
    get_edit_mode: Callable[[], bool] | None = None,
    on_edit_select_path: Callable[[str], None] | None = None,
    appearance: dict | None = None,
    widget_registry: dict[str, Any] | None = None,
    state_input_registry: dict[str, Any] | None = None,
    get_show_markdown_source: Callable[[], bool] | None = None,
    register_markdown_view: Callable[[Any, Any], None] | None = None,
) -> None:
    appearance = appearance or {}
    children = node.get("children", [])
    tab_nodes = [c for c in children if c.get("type") == "tab"]
    if not tab_nodes:
        return
    with ui.tabs() as tabs:
        for tn in tab_nodes:
            tid = tn.get("id", "")
            tlabel = tn.get("label", tid)
            # NiceGUI: tab(name) und tab_panel(name) müssen übereinstimmen; tlabel = lesbarer Reiter-Text.
            ui.tab(tlabel)
    first_label = tab_nodes[0].get("label", tab_nodes[0].get("id", ""))
    with ui.tab_panels(tabs, value=first_label).classes("w-full"):
        for tn in tab_nodes:
            tid = tn.get("id", "")
            tlabel = tn.get("label", tid)
            with ui.tab_panel(tlabel):
                _render_children(
                    tn.get("children", []), _path(path, tid), state, callbacks, ui, on_state_change,
                    get_edit_mode=get_edit_mode, on_edit_select_path=on_edit_select_path, appearance=appearance,
                    widget_registry=widget_registry, state_input_registry=state_input_registry,
                    get_show_markdown_source=get_show_markdown_source, register_markdown_view=register_markdown_view,
                )


def _render_node(
    node: dict,
    parent_path: str,
    state: dict[str, Any],
    callbacks: dict[str, Any],
    ui: Any,
    on_state_change: Callable[[], None] | None = None,
    *,
    get_edit_mode: Callable[[], bool] | None = None,
    on_edit_select_path: Callable[[str], None] | None = None,
    appearance: dict | None = None,
    widget_registry: dict[str, Any] | None = None,
    state_input_registry: dict[str, Any] | None = None,
    get_show_markdown_source: Callable[[], bool] | None = None,
    register_markdown_view: Callable[[Any, Any], None] | None = None,
) -> None:
    node_id = node.get("id", "")
    path = _path(parent_path, node_id)
    node_type = node.get("type", "widget")

    if node_type == "placeholder":
        return

    if node_type == "widget":
        _render_widget(
            node, path, state, callbacks, ui, on_state_change,
            get_edit_mode=get_edit_mode, on_edit_select_path=on_edit_select_path,
            widget_registry=widget_registry, state_input_registry=state_input_registry,
            get_show_markdown_source=get_show_markdown_source, register_markdown_view=register_markdown_view,
        )
        return

    if node_type == "group":
        label = node.get("label")
        with ui.column().classes("gap-1"):
            if label:
                ui.label(label).classes("text-weight-medium")
            _render_children(
                node.get("children", []), path, state, callbacks, ui, on_state_change,
                get_edit_mode=get_edit_mode, on_edit_select_path=on_edit_select_path,
                widget_registry=widget_registry, state_input_registry=state_input_registry,
                get_show_markdown_source=get_show_markdown_source, register_markdown_view=register_markdown_view,
            )
        return

    if node_type == "container":
        layout_type = node.get("layout_type", "rows_columns")
        style = _merge_container_style(node.get("style") or {}, appearance or {})
        edit_kw = {"get_edit_mode": get_edit_mode, "on_edit_select_path": on_edit_select_path, "appearance": appearance or {}, "widget_registry": widget_registry, "state_input_registry": state_input_registry, "get_show_markdown_source": get_show_markdown_source, "register_markdown_view": register_markdown_view}

        if layout_type == "rows_columns":
            columns = node.get("columns")
            if columns is not None:
                # Mehrspaltiges Layout wie Grid: rows×columns
                rows = node.get("rows")
                grid_kw = {"columns": columns}
                if rows is not None:
                    grid_kw["rows"] = rows
                grid_classes = "w-full gap-4"
                if style:
                    style_str = "; ".join(f"{k}: {v}" for k, v in style.items())
                    with ui.element("div").style(style_str):
                        with ui.grid(**grid_kw).classes(grid_classes):
                            _render_grid_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
                else:
                    with ui.grid(**grid_kw).classes(grid_classes):
                        _render_grid_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
            else:
                raw_align = node.get("align_items") or "center"
                if not isinstance(raw_align, str):
                    raw_align = getattr(raw_align, "value", None) or getattr(raw_align, "key", None) or "center"
                align = str(raw_align).strip().lower()
                if align not in ("start", "center", "end", "stretch"):
                    align = "center"
                items_class = {"start": "items-start", "center": "items-center", "end": "items-end", "stretch": "items-stretch"}[align]
                row_classes = f"gap-4 {items_class} flex-wrap w-full"
                if style:
                    style_str = "; ".join(f"{k}: {v}" for k, v in style.items())
                    with ui.element("div").style(style_str):
                        with ui.row().classes(row_classes):
                            _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
                else:
                    with ui.row().classes(row_classes):
                        _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
        elif layout_type == "column":
            col_classes = "gap-2 w-full"
            if style:
                style_str = "; ".join(f"{k}: {v}" for k, v in style.items())
                with ui.element("div").style(style_str):
                    with ui.column().classes(col_classes):
                        _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
            else:
                with ui.column().classes(col_classes):
                    _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
        elif layout_type == "expansion":
            label = node.get("label", node_id)
            if style:
                style_str = "; ".join(f"{k}: {v}" for k, v in style.items())
                with ui.element("div").style(style_str):
                    with ui.expansion(label, value=False).classes("w-full"):
                        _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
            else:
                with ui.expansion(label, value=False).classes("w-full"):
                    _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
        elif layout_type == "grid":
            columns = node.get("columns", 2)
            rows = node.get("rows")
            grid_kw = {"columns": columns}
            if rows is not None:
                grid_kw["rows"] = rows
            grid_classes = "w-full gap-4"
            if style:
                style_str = "; ".join(f"{k}: {v}" for k, v in style.items())
                with ui.element("div").style(style_str):
                    with ui.grid(**grid_kw).classes(grid_classes):
                        _render_grid_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
            else:
                with ui.grid(**grid_kw).classes(grid_classes):
                    _render_grid_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
        elif layout_type == "scroll":
            scroll_classes = "w-full gap-2"
            if style:
                style_str = "; ".join(f"{k}: {v}" for k, v in style.items())
                with ui.element("div").style(style_str):
                    with ui.scroll_area().classes(scroll_classes):
                        _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
            else:
                with ui.scroll_area().classes(scroll_classes):
                    _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
        elif layout_type == "card":
            card_classes = "w-full gap-2"
            if style:
                style_str = "; ".join(f"{k}: {v}" for k, v in style.items())
                with ui.element("div").style(style_str):
                    with ui.card().classes(card_classes):
                        _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
            else:
                with ui.card().classes(card_classes):
                    _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
        elif layout_type == "splitter":
            children = node.get("children", [])
            value = node.get("value", 30)
            orientation = node.get("orientation", "horizontal")
            splitter_props = "vertical" if orientation == "vertical" else None
            if style:
                style_str = "; ".join(f"{k}: {v}" for k, v in style.items())
                with ui.element("div").style(style_str):
                    _render_splitter(children, value, splitter_props, path, state, callbacks, ui, on_state_change, **edit_kw)
            else:
                _render_splitter(children, value, splitter_props, path, state, callbacks, ui, on_state_change, **edit_kw)
        elif layout_type == "tabs":
            _render_tabs_container(node, path, state, callbacks, ui, on_state_change, **edit_kw)
        elif layout_type == "xy":
            style_str = "position: relative; " + "; ".join(f"{k}: {v}" for k, v in style.items()) if style else "position: relative;"
            with ui.element("div").style(style_str):
                _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
        else:
            with ui.row().classes("gap-4 flex-wrap"):
                _render_children(node.get("children", []), path, state, callbacks, ui, on_state_change, **edit_kw)
        return

    if node_type == "tab":
        pass


def _render_widget(
    node: dict,
    path_id: str,
    state: dict[str, Any],
    callbacks: dict[str, Any],
    ui: Any,
    on_state_change: Callable[[], None] | None = None,
    *,
    get_edit_mode: Callable[[], bool] | None = None,
    on_edit_select_path: Callable[[str], None] | None = None,
    widget_registry: dict[str, Any] | None = None,
    state_input_registry: dict[str, Any] | None = None,
    get_show_markdown_source: Callable[[], bool] | None = None,
    register_markdown_view: Callable[[Any, Any], None] | None = None,
) -> None:
    widget_type = node.get("widget_type", "")
    props = node.get("props", {})

    def _on_change(cb_key: str, value: Any) -> None:
        state[path_id] = value
        if on_state_change:
            on_state_change()
        fn = callbacks.get(cb_key)
        if fn:
            fn(value)

    def _on_click(cb_key: str) -> None:
        fn = callbacks.get(cb_key)
        if fn:
            fn()

    def _event_value(e: Any, widget: Any, fallback: Any) -> Any:
        """Wert aus Event: e.args wenn sinnvoll (bool/number/str), sonst widget.value (NiceGUI liefert teils Event-Objekt)."""
        args = getattr(e, "args", None)
        if isinstance(args, bool):
            return args
        if isinstance(args, (int, float)) and not isinstance(args, bool):
            return args
        if isinstance(args, str):
            return args
        if hasattr(e, "sender") and hasattr(e.sender, "value"):
            return e.sender.value
        if hasattr(widget, "value"):
            return widget.value
        return fallback

    # Wrapper: data-path-id immer (für JS); title nur per JS im Edit-Modus (Hover path_id).
    # Gemeinsame Farb-Props (text_color, bg_color) für alle Widgets – Hex/Picker, konsistent anwendbar.
    def _coerce_color_prop(val: Any) -> str:
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, dict) and val.get("hex"):
            return str(val["hex"]).strip()
        return str(val).strip() if val else ""

    def _coerce_flex(val: Any) -> bool:
        """Flex-Prop kann als bool oder [bool, event] aus dem Editor gespeichert sein."""
        if val is True:
            return True
        if isinstance(val, (list, tuple)) and len(val) > 0:
            return bool(val[0])
        return bool(val)

    wrapper_style_parts = []
    tc = _coerce_color_prop(props.get("text_color"))
    if tc:
        wrapper_style_parts.append(f"color: {tc}")
    bc = _coerce_color_prop(props.get("bg_color"))
    if bc:
        wrapper_style_parts.append(f"background-color: {bc}")
    is_flex = _coerce_flex(props.get("flex"))
    # Bei Flex keine feste Breite setzen, damit das Widget (z. B. Banner) sich an die Seitenbreite anpasst
    if not is_flex:
        w = (props.get("width") or "").strip() if isinstance(props.get("width"), str) else ""
        if w:
            wrapper_style_parts.append(f"width: {w}")
        minw = (props.get("min_width") or "").strip() if isinstance(props.get("min_width"), str) else ""
        if minw:
            wrapper_style_parts.append(f"min-width: {minw}")
        maxw = (props.get("max_width") or "").strip() if isinstance(props.get("max_width"), str) else ""
        if maxw:
            wrapper_style_parts.append(f"max-width: {maxw}")
    if is_flex:
        wrapper_style_parts.append("flex: 1 1 0; min-width: 0; width: 100%;")
    # Optionaler Rahmen (Prop „framed“): umrandet das Widget; UX: sparsam nutzen zur Gruppierung/Hervorhebung
    if _coerce_flex(props.get("framed")):
        wrapper_style_parts.append("border: 1px solid rgba(0,0,0,0.12); border-radius: 6px; padding: 8px; box-sizing: border-box;")

    with ui.element("div") as wrapper:
        wrapper.props["data-path-id"] = path_id
        uid = props.get("user_id")
        if isinstance(uid, dict):
            uid = (uid.get("value") or uid.get("label") or "").strip()
        else:
            uid = str(uid).strip() if uid else ""
        if uid:
            wrapper.props["data-user-id"] = uid
        if wrapper_style_parts:
            wrapper.style("; ".join(wrapper_style_parts))
        if get_edit_mode and on_edit_select_path:
            wrapper.on("click", lambda pid=path_id: (on_edit_select_path(pid) if get_edit_mode() else None))

        if widget_type == "checkbox":
            state.setdefault(path_id, props.get("value", False))
            val = state.get(path_id, props.get("value", False))
            el = ui.checkbox(props.get("label", node.get("id", "")), value=val)

            def _checkbox_change(e: Any, pid: str = path_id, w: Any = None) -> None:
                w = w or el
                if get_edit_mode and on_edit_select_path and get_edit_mode():
                    on_edit_select_path(pid)
                    w.value = state.get(pid, val)  # Toggle rückgängig: Anzeige = State
                    w.update()
                    return
                _on_change(pid, _event_value(e, w, not state.get(pid, False)))

            el.on("update:model-value", lambda e, pid=path_id, w=el: _checkbox_change(e, pid, w))

        elif widget_type == "slider":
            state.setdefault(path_id, props.get("value", 1))
            raw = state.get(path_id, props.get("value", 1))
            val = _to_float(raw, 1.0)
            pmin = _to_float(props.get("min", 0), 0.0)
            pmax = _to_float(props.get("max", 10), 10.0)
            pstep = _to_float(props.get("step", 0.01), 0.01)
            label_pos = props.get("label_position") or "below"
            if isinstance(label_pos, dict):
                label_pos = label_pos.get("value", label_pos.get("label", "below"))
            label_pos = str(label_pos).strip().lower() or "below"
            if label_pos not in ("below", "above", "inline"):
                label_pos = "below"
            lbl_text = props.get("label", node.get("id", ""))
            has_width = bool(props.get("width") or props.get("flex"))
            inner_style = "min-width: 0; width: 100%;" if has_width else "min-width: 0; max-width: 12rem;"
            with ui.element("div").classes("shrink-0").style(inner_style):
                if label_pos == "above":
                    ui.label(lbl_text).classes("shrink-0 text-caption")
                if label_pos == "inline":
                    label_width = (props.get("label_width") or "").strip()
                    control_width = (props.get("control_width") or "").strip()
                    if isinstance(label_width, dict):
                        label_width = label_width.get("value", label_width.get("label", "")) or ""
                    if isinstance(control_width, dict):
                        control_width = control_width.get("value", control_width.get("label", "")) or ""
                    with ui.row().classes("items-center gap-2 w-full flex-nowrap min-w-0"):
                        lbl_el = ui.label(lbl_text).classes("shrink-0 text-caption")
                        if label_width:
                            lbl_el.style(f"width: {label_width};")
                        control_style = "min-width: 0; flex: 1 1 0;"
                        if control_width:
                            control_style = f"min-width: 0; width: {control_width}; flex: 0 0 auto;"
                        with ui.element("div").classes("min-w-24").style(control_style):
                            el = ui.slider(
                                min=pmin,
                                max=pmax,
                                value=val,
                                step=pstep,
                            ).classes("w-full")
                            el.on(
                                "update:model-value",
                                lambda e, pid=path_id, w=el: _on_change(pid, _to_float(_event_value(e, w, val), 1.0)),
                            )
                else:
                    el = ui.slider(
                        min=pmin,
                        max=pmax,
                        value=val,
                        step=pstep,
                    ).classes("min-w-24 w-full")
                    el.on(
                        "update:model-value",
                        lambda e, pid=path_id, w=el: _on_change(pid, _to_float(_event_value(e, w, val), 1.0)),
                    )
                    if label_pos == "below":
                        ui.label(lbl_text).classes("shrink-0 text-caption")

        elif widget_type == "button":
            if get_edit_mode and on_edit_select_path:
                def _button_click(pid: str = path_id) -> None:
                    if get_edit_mode():
                        on_edit_select_path(pid)
                    else:
                        _on_click(pid)
                ui.button(props.get("label", node.get("id", "")), on_click=lambda: _button_click(path_id))
            else:
                ui.button(props.get("label", node.get("id", "")), on_click=lambda: _on_click(path_id))

        elif widget_type == "toggle_button":
            state.setdefault(path_id, props.get("value", False))
            val = state.get(path_id, props.get("value", False))
            icon = (props.get("icon") or "toggle_on").strip() or "toggle_on"
            label = (props.get("label") or "").strip()
            label_inactive = (props.get("label_inactive") or "").strip()
            strikethrough = props.get("strikethrough_inactive", True)
            display_label = label if val else (label_inactive if label_inactive else label)
            color_prop = "color=grey" if not val else "color=primary"
            btn = ui.button(display_label).props(f"icon={icon} flat no-caps {color_prop}").classes("shrink-0")
            if strikethrough and not val:
                btn.classes("toggle-btn-inactive-strike")

            def _toggle_click(pid: str = path_id) -> None:
                if get_edit_mode and on_edit_select_path and get_edit_mode():
                    on_edit_select_path(pid)
                    return
                new_val = not state.get(pid, False)
                state[path_id] = new_val
                if on_state_change:
                    on_state_change()
                lbl = label if new_val else (label_inactive if label_inactive else label)
                color_prop = "color=grey" if not new_val else "color=primary"
                btn.props(f"icon={icon} flat no-caps {color_prop}")
                if hasattr(btn, "text"):
                    btn.text = lbl
                # Strikethrough-Klasse per JS setzen/entfernen (NiceGUI .classes() kann nur hinzufügen)
                pid_js = json.dumps(path_id)
                if new_val:
                    ui.run_javascript(
                        f"var w=document.querySelector('[data-path-id='+{pid_js}+']');"
                        "if(w){var b=w.querySelector('button');if(b)b.classList.remove('toggle-btn-inactive-strike');}"
                    )
                elif strikethrough:
                    ui.run_javascript(
                        f"var w=document.querySelector('[data-path-id='+{pid_js}+']');"
                        "if(w){var b=w.querySelector('button');if(b)b.classList.add('toggle-btn-inactive-strike');}"
                    )
                btn.update()
                fn = callbacks.get(path_id)
                if fn:
                    fn(new_val)

            btn.on("click", lambda: _toggle_click(path_id))

        elif widget_type == "number_input":
            state.setdefault(path_id, props.get("value", 0))
            raw = state.get(path_id, props.get("value", 0))
            val = _to_float(raw, 0.0)
            with ui.element("div").classes("shrink-0").style("min-width: 0; max-width: 10rem;"):
                el = ui.number(value=val).props(f'label="{props.get("label", node.get("id", ""))}"')
                el.on(
                    "update:model-value",
                    lambda e, pid=path_id, w=el: _on_change(pid, _to_float(_event_value(e, w, val), 0.0)),
                )

        elif widget_type == "input":
            state.setdefault(path_id, props.get("value", ""))
            val = state.get(path_id, props.get("value", ""))
            with ui.element("div").classes("shrink-0").style("min-width: 0; max-width: 12rem;"):
                el = ui.input(props.get("label", node.get("id", "")), value=val)
                el.on(
                    "update:model-value",
                    lambda e, pid=path_id, w=el: _on_change(pid, _event_value(e, w, val)),
                )

        elif widget_type == "select":
            state.setdefault(path_id, props.get("value"))
            val = state.get(path_id, props.get("value"))
            opts = props.get("options", [])
            with ui.element("div").classes("shrink-0").style("min-width: 0; max-width: 12rem;"):
                el = ui.select(opts, value=val, label=props.get("label", node.get("id", "")))
                el.on(
                    "update:model-value",
                    lambda e, pid=path_id, w=el: _on_change(pid, _event_value(e, w, val)),
                )

        elif widget_type == "label":
            text = props.get("text") or node.get("id", "Label")
            raw_heading = props.get("heading")
            if isinstance(raw_heading, str):
                heading = raw_heading.strip().lower()
            elif isinstance(raw_heading, int) and 1 <= raw_heading <= 6:
                heading = ("h1", "h2", "h3", "h4", "h5", "h6")[raw_heading - 1]
            else:
                heading = ""
            font = props.get("font") if isinstance(props.get("font"), str) else ""
            classes = []
            if heading in ("h1", "h2", "h3", "h4", "h5", "h6"):
                classes.append(f"text-{heading}")
            lbl = ui.label(text)
            if classes:
                lbl.classes(" ".join(classes))
            if font and font.strip():
                lbl.style(f"font-family: {font.strip()}")

        elif widget_type == "image":
            src = props.get("src", "")
            alt = props.get("alt", "")
            width = props.get("width", "")
            height = props.get("height", "auto")
            if src:
                parts = []
                if width:
                    parts.append(f"width: {width}")
                if height:
                    parts.append(f"height: {height}")
                img = ui.image(src)
                if alt:
                    img.props(f'alt="{alt}"')
                if parts:
                    img.style("; ".join(parts))

        elif widget_type == "link":
            url = (props.get("url") or "#").strip()
            if url and url != "#" and not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            text = props.get("text", url)
            target = props.get("target", "_blank")
            if get_edit_mode and on_edit_select_path:
                def _link_click(pid: str = path_id, link_url: str = url, link_target: str = target) -> None:
                    if get_edit_mode():
                        on_edit_select_path(pid)
                    else:
                        ui.run_javascript(f"window.open({link_url!r}, {link_target!r})")
                link_btn = ui.button(text).props("flat no-caps").classes("text-primary")
                link_btn.style("text-transform: none;")
                link_btn.on("click", lambda: _link_click(path_id, url, target))
            else:
                ui.link(text, url).props(f"target={target}")

        elif widget_type in ("video", "youtube"):
            url = props.get("url", "")
            embed = props.get("embed", True)
            if embed and url:
                # YouTube: convert watch URL to embed URL if needed
                if "youtube.com/watch" in url:
                    vid = ""
                    if "v=" in url:
                        vid = url.split("v=")[-1].split("&")[0]
                    if vid:
                        url = f"https://www.youtube.com/embed/{vid}"
                width = props.get("width", "560px")
                height = props.get("height", "315px")
                ui.html(f'<iframe width="{width}" height="{height}" src="{url}" frameborder="0" allowfullscreen></iframe>')
            elif url:
                ui.link(props.get("text", "Video öffnen"), url).props("target=_blank")

        elif widget_type == "table":
            state.setdefault(path_id, props.get("rows", []))
            columns = props.get("columns", [])
            rows = state.get(path_id, props.get("rows", [])) or []
            if columns:
                col_defs = [
                    {"name": c.get("field", c.get("name", "")), "label": c.get("name", c.get("field", "")), "field": c.get("field", c.get("name", ""))}
                    for c in columns
                ]
                ui.table(columns=col_defs, rows=rows).classes("w-full")

        elif widget_type == "banner_vue":
            try:
                from widgets import Banner
                Banner(
                    text1=props.get("text1", ""),
                    text2=props.get("text2", ""),
                    text3=props.get("text3", ""),
                    height=props.get("height", "80px"),
                    font_family=props.get("font_family", ""),
                    font_size1=props.get("font_size1", ""),
                    font_size2=props.get("font_size2", ""),
                    font_size3=props.get("font_size3", ""),
                    text_color=props.get("text_color", ""),
                    gradient_start=props.get("gradient_start", "#0d47a1"),
                    gradient_end=props.get("gradient_end", "#1565c0"),
                ).classes("w-full")
            except ImportError:
                ui.label("[Banner – widgets nicht verfügbar]").classes("text-grey")

        elif widget_type == "gain_control_vue":
            state.setdefault(path_id, props.get("value", 1.0))
            raw = state.get(path_id, props.get("value", 1.0))
            val = _to_float(raw, 1.0)
            try:
                from widgets import GainControlVue
                def _gain_change(e: Any, pid: str = path_id) -> None:
                    raw = getattr(e, "args", None)
                    if raw is None:
                        return
                    v = raw[0] if isinstance(raw, (list, tuple)) and raw else raw
                    if isinstance(v, dict):
                        v = v.get("value", v.get("args", 1.0))
                    num = _to_float(v, 1.0)
                    _on_change(pid, num)
                GainControlVue(
                    label=props.get("label", node.get("id", "Gain")),
                    min_=_to_float(props.get("min", 0), 0.0),
                    max_=_to_float(props.get("max", 10), 10.0),
                    value=val,
                    on_change=_gain_change,
                )
            except ImportError:
                ui.label("[GainControlVue – widgets nicht verfügbar]").classes("text-grey")

        elif widget_type == "vu_meter":
            state.setdefault(path_id, props.get("value", 0.0))
            raw = state.get(path_id, props.get("value", 0.0))
            val = _to_float(raw, 0.0)
            try:
                from widgets import VuMeter
                el = VuMeter(
                    value=val,
                    min_=_to_float(props.get("min", 0), 0.0),
                    max_=_to_float(props.get("max", 1.0), 1.0),
                    show_value=props.get("show_value", True),
                    width=props.get("width", "120px"),
                    height=props.get("height", "80px"),
                )
                if widget_registry is not None:
                    widget_registry[path_id] = el
            except ImportError:
                ui.label("[VuMeter – widgets nicht verfügbar]").classes("text-grey")

        elif widget_type == "led":
            state.setdefault(path_id, props.get("state", "off"))
            val = state.get(path_id, props.get("state", "off"))
            try:
                from widgets import Led
                el = Led(
                    state=val,
                    label=props.get("label", node.get("id", "")),
                    size=props.get("size", 16),
                )
                if widget_registry is not None:
                    widget_registry[path_id] = el
            except ImportError:
                ui.label("[Led – widgets nicht verfügbar]").classes("text-grey")

        elif widget_type == "image_icon_demo":
            try:
                from widgets import ImageIconDemo
                ImageIconDemo(
                    image_src=props.get("image_src", ""),
                    image_alt=props.get("image_alt", "Image"),
                    show_icon=props.get("show_icon", True),
                    label=props.get("label", ""),
                )
            except ImportError:
                ui.label("[ImageIconDemo – widgets nicht verfügbar]").classes("text-grey")

        elif widget_type == "markdown":
            def _markdown_content_from_val(val: Any) -> str:
                """Content für Markdown-Rendering: immer String (Props/State können Dict aus Editor sein)."""
                if val is None:
                    return ""
                if isinstance(val, dict):
                    raw = val.get("value") or val.get("label") or val.get("content") or ""
                    return str(raw).strip()
                return str(val).strip()

            def _coerce_bool(val, default: bool) -> bool:
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], bool):
                    return val[0]
                return bool(val) if val is not None else default

            is_editable = _coerce_bool(props.get("editable"), False)
            render_markdown = _coerce_bool(props.get("render_markdown"), True)
            raw_font = props.get("font", "default")
            if isinstance(raw_font, list) and len(raw_font) > 0:
                raw_font = raw_font[0]
            font = str(raw_font).strip().lower() if raw_font else "default"
            if font not in ("default", "monospace"):
                font = "default"
            font_style = "font-family: monospace;" if font == "monospace" else ""
            raw_extras = props.get("extras", "latex")
            if isinstance(raw_extras, str):
                extras_list = ["fenced-code-blocks", "tables", "latex"] if raw_extras else ["fenced-code-blocks", "tables"]
            else:
                extras_list = list(raw_extras) if raw_extras else ["fenced-code-blocks", "tables"]
            if "latex" not in extras_list and (raw_extras == "latex" or (isinstance(raw_extras, str) and "latex" in raw_extras.lower())):
                extras_list.append("latex")
            # Ohne latex2mathml stürzt markdown2 mit extras=['latex'] ab → LaTeX nur wenn Paket vorhanden
            try:
                import latex2mathml.converter  # noqa: F401
            except ImportError:
                extras_list = [e for e in extras_list if e != "latex"]
            raw_height = props.get("height")
            if isinstance(raw_height, dict):
                height = str(raw_height.get("value") or raw_height.get("label") or "300px") or "300px"
            else:
                height = (raw_height or "300px")
            height = str(height).strip() or "300px"
            height_mode = props.get("height_mode")
            if isinstance(height_mode, dict):
                height_mode = str(height_mode.get("value") or height_mode.get("label") or "fixed") or "fixed"
            else:
                height_mode = (height_mode or "fixed")
            height_mode = str(height_mode).strip().lower() if height_mode else "fixed"
            if height_mode not in ("fixed", "auto"):
                height_mode = "fixed"
            if height_mode == "fixed":
                # min-height + flex: 1 damit der Bereich die gesamte Zeilenhöhe nutzt; max-height nur als Untergrenze durch min-height
                scroll_container = ui.scroll_area().classes("w-full").style(f"min-height: {height}; flex: 1;")
            else:
                scroll_container = ui.element("div").classes("w-full")
            with scroll_container:
                if is_editable:
                    instruction = _markdown_content_from_val(props.get("content", ""))
                    if instruction:
                        if render_markdown:
                            instr_el = ui.element("div").classes("w-full").style(font_style) if font_style else None
                            if instr_el is not None:
                                with instr_el:
                                    ui.markdown(instruction, extras=extras_list)
                            else:
                                ui.markdown(instruction, extras=extras_list)
                        else:
                            pre_el = ui.element("pre").classes("w-full").style(f"white-space: pre-wrap; margin: 0; {font_style}")
                            pre_el.inner_html = _html.escape(instruction)
                    state.setdefault(path_id, "")  # damit path_id im State-Dict erscheint (auch bei neuen Widgets aus Grid-Editor)
                    student_value = _markdown_content_from_val(state.get(path_id, ""))
                    placeholder = (props.get("placeholder") or "Ihre Antwort oder Anmerkung …").strip()
                    preview_md_ref: list[Any] = [None]
                    view_mode_ref: list[str] = ["source"]

                    def _markdown_edit_change(e: Any, pid: str = path_id) -> None:
                        val = getattr(e, "args", None)
                        if val is None and hasattr(e, "sender"):
                            val = getattr(e.sender, "value", "")
                        state[pid] = val if val is not None else ""
                        if on_state_change:
                            on_state_change()
                        if preview_md_ref[0] is not None:
                            txt = state[pid] or ("*Vorschau …*" if render_markdown else "")
                            if hasattr(preview_md_ref[0], "content"):
                                preview_md_ref[0].content = txt
                            else:
                                preview_md_ref[0].set_content(txt)
                        fn = callbacks.get(pid)
                        if fn:
                            fn(state[pid])

                    def _set_view(mode: str) -> None:
                        view_mode_ref[0] = mode
                        if source_container and hasattr(source_container, "set_visibility"):
                            source_container.set_visibility(mode == "source")
                        if preview_container and hasattr(preview_container, "set_visibility"):
                            preview_container.set_visibility(mode == "preview")

                    use_global_markdown_view = get_show_markdown_source is not None
                    if not use_global_markdown_view:
                        with ui.row().classes("gap-2 mt-2"):
                            ui.button("Quelltext", on_click=lambda: _set_view("source")).props("flat dense no-caps")
                            ui.button("Vorschau", on_click=lambda: _set_view("preview")).props("flat dense no-caps")
                    # source_container: bei fixed flex: 1 damit Textarea die Zeilenhöhe ausfüllt
                    source_style = (font_style or "").strip()
                    if height_mode == "fixed":
                        source_style = f"{source_style}; flex: 1; min-height: 0; display: flex; flex-direction: column;" if source_style else "flex: 1; min-height: 0; display: flex; flex-direction: column;"
                    source_container = ui.element("div").classes("w-full").style(source_style) if source_style else ui.element("div").classes("w-full")
                    with source_container:
                        # Höhe wirkt nur auf das innere <textarea>: Quasar QInput braucht input-style; resize: none entfernt die verschiebbare Begrenzungslinie
                        input_style_attr = f"min-height: {height}; height: 100%; resize: none;"
                        ta_style_outer = f"min-height: {height};" if height_mode == "fixed" else f"min-height: {height}; max-height: none;"
                        ta = ui.textarea(value=student_value).props(
                            f'placeholder="{placeholder}" input-style="{input_style_attr}"'
                        ).classes("w-full").style(ta_style_outer)
                        ta.on("update:model-value", lambda e, pid=path_id: _markdown_edit_change(e, pid))
                        if state_input_registry is not None:
                            state_input_registry[path_id] = ta
                    # Bei render_markdown=False Vorschau-Container min-height, damit Zeile nicht auf 0 kollabiert (App: "Markdown Quelltext" aus)
                    preview_style = (font_style or "").strip()
                    if not render_markdown:
                        preview_style = f"{preview_style}; min-height: 6em;" if preview_style else "min-height: 6em;"
                    preview_container = ui.element("div").classes("w-full")
                    if preview_style:
                        preview_container.style(preview_style)
                    with preview_container:
                        if render_markdown:
                            preview_md_ref[0] = ui.markdown(student_value or "*Vorschau …*", extras=extras_list)
                        else:
                            pre_el = ui.element("pre").classes("w-full").style(f"white-space: pre-wrap; margin: 0; overflow-x: auto; min-height: 4em; {font_style}")
                            pre_el.inner_html = _html.escape(student_value or "")

                            class _PlainTextPreviewWrapper:
                                def __init__(self, el: Any) -> None:
                                    self._el = el

                                def set_content(self, text: str) -> None:
                                    self._el.inner_html = _html.escape(str(text) if text else "")

                            preview_md_ref[0] = _PlainTextPreviewWrapper(pre_el)
                    if use_global_markdown_view and get_show_markdown_source:
                        show_source = get_show_markdown_source()
                        # Wenn Property "Markdown rendern" aus: immer Textarea (Quelltext) anzeigen, damit User Plain-Text eintippen kann (z. B. für Live-Huffman-Codierung + Codetabelle)
                        if not render_markdown:
                            show_source = True
                        source_container.set_visibility(show_source)
                        preview_container.set_visibility(not show_source)
                        if hasattr(source_container, "style"):
                            source_container.style(f"display: {'none' if not show_source else 'block'};")
                        if hasattr(preview_container, "style"):
                            preview_container.style(f"display: {'block' if not show_source else 'none'};")
                        view_mode_ref[0] = "source" if show_source else "preview"
                    else:
                        preview_container.set_visibility(False)
                    def _update_preview_from_state() -> None:
                        if preview_md_ref[0] is not None:
                            raw = state.get(path_id, "") or ""
                            txt = raw if not render_markdown else (raw or "*Vorschau …*")
                            if hasattr(preview_md_ref[0], "content"):
                                preview_md_ref[0].content = txt
                            else:
                                preview_md_ref[0].set_content(txt)
                    if register_markdown_view is not None:
                        # always_show_source=True wenn Plain-Text (render_markdown=False), damit Quelltext-Textarea auch bei globalem Toggle „Markdown Quelltext“ aus sichtbar bleibt
                        register_markdown_view(source_container, preview_container, _update_preview_from_state, not render_markdown)
                else:
                    raw_content = state.get(path_id, props.get("content", ""))
                    content = _markdown_content_from_val(raw_content) if raw_content else _markdown_content_from_val(props.get("content", ""))
                    if render_markdown:
                        container = ui.element("div").classes("w-full").style(font_style) if font_style else None
                        if container is not None:
                            with container:
                                md = ui.markdown(content or "*Kein Inhalt.*", extras=extras_list)
                        else:
                            md = ui.markdown(content or "*Kein Inhalt.*", extras=extras_list)
                        if widget_registry is not None:
                            widget_registry[path_id] = md
                    else:
                        # Plain-Text: kein Markdown-Rendering, HTML escapen
                        plain = content or ""
                        pre_el = ui.element("pre").classes("w-full").style(f"white-space: pre-wrap; margin: 0; overflow-x: auto; {font_style}")
                        pre_el.inner_html = _html.escape(plain)

                        class _PlainTextWrapper:
                            def __init__(self, el: Any) -> None:
                                self._el = el

                            def set_content(self, text: str) -> None:
                                self._el.inner_html = _html.escape(str(text) if text else "")

                        wrapper = _PlainTextWrapper(pre_el)
                        if widget_registry is not None:
                            widget_registry[path_id] = wrapper

        elif widget_type in ("plotly_graph", "plotly_scatter", "plotly_histogram", "plotly_3d"):
            try:
                from widgets import PlotlyGraph

                def _prop_str(p: Any, default: str = "") -> str:
                    v = props.get(p, default)
                    if isinstance(v, dict):
                        return str(v.get("value") or v.get("label") or default).strip()
                    return str(v).strip() if v is not None else default

                def _prop_num(p: Any, default: float) -> float:
                    v = props.get(p, default)
                    if isinstance(v, dict):
                        v = v.get("value") or v.get("label")
                    if v is None:
                        return default
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return default

                def _prop_bool(p: Any, default: bool) -> bool:
                    v = props.get(p, default)
                    if isinstance(v, dict):
                        v = v.get("value") if "value" in v else v.get("label")
                    if v is None:
                        return default
                    return bool(v)

                height = _prop_str("height", "400px") or "400px"
                plotly_script_url = _prop_str("plotly_script_url", "/widgets-static/plotly.min.js")
                title = _prop_str("title", "")
                xaxis_title = _prop_str("xaxis_title", "")
                yaxis_title = _prop_str("yaxis_title", "")
                xaxis_type = _prop_str("xaxis_type", "linear") or "linear"
                yaxis_type = _prop_str("yaxis_type", "linear") or "linear"
                xaxis_autorange = _prop_bool("xaxis_autorange", True)
                yaxis_autorange = _prop_bool("yaxis_autorange", True)
                xaxis_range_raw = _prop_str("xaxis_range", "")
                yaxis_range_raw = _prop_str("yaxis_range", "")
                trace_count = max(1, min(20, int(_prop_num("trace_count", 1))))
                mode = _prop_str("mode", "lines") or "lines"
                marker_size = _prop_num("marker_size", 6)
                marker_symbol = _prop_str("marker_symbol", "circle") or "circle"
                marker_color = _prop_str("marker_color", "")
                line_dash = _prop_str("line_dash", "solid") or "solid"
                line_width = _prop_num("line_width", 1.5)
                responsive = _prop_bool("responsive", True)

                layout: dict[str, Any] = {
                    "margin": {"t": 40, "r": 20, "b": 50, "l": 60},
                    "xaxis": {"type": xaxis_type, "autorange": xaxis_autorange, "title": {"text": xaxis_title or None}},
                    "yaxis": {"type": yaxis_type, "autorange": yaxis_autorange, "title": {"text": yaxis_title or None}},
                }
                if title:
                    layout["title"] = {"text": title}
                if xaxis_range_raw:
                    parts = [s.strip() for s in xaxis_range_raw.replace("[", "").replace("]", "").split(",") if s.strip()]
                    if len(parts) >= 2:
                        try:
                            layout["xaxis"]["range"] = [float(parts[0]), float(parts[1])]
                            layout["xaxis"]["autorange"] = False
                        except ValueError:
                            pass
                if yaxis_range_raw:
                    parts = [s.strip() for s in yaxis_range_raw.replace("[", "").replace("]", "").split(",") if s.strip()]
                    if len(parts) >= 2:
                        try:
                            layout["yaxis"]["range"] = [float(parts[0]), float(parts[1])]
                            layout["yaxis"]["autorange"] = False
                        except ValueError:
                            pass

                data: list[dict[str, Any]] = []
                for i in range(trace_count):
                    trace: dict[str, Any] = {"x": [], "y": [], "mode": mode, "name": f"Trace {i + 1}"}
                    if "marker" in mode or mode == "markers":
                        trace["marker"] = {"size": marker_size, "symbol": marker_symbol}
                        if marker_color:
                            trace["marker"]["color"] = marker_color
                    if "lines" in mode or mode == "lines":
                        trace["line"] = {"dash": line_dash, "width": line_width}
                        if marker_color and "marker" not in trace:
                            trace["line"]["color"] = marker_color
                    data.append(trace)

                config: dict[str, Any] = {"responsive": responsive}
                el = PlotlyGraph(
                    data=data,
                    layout=layout,
                    config=config,
                    height=height,
                    plotly_script_url=plotly_script_url,
                )
                el.classes("w-full")
                if widget_registry is not None:
                    widget_registry[path_id] = el
            except ImportError:
                ui.label("[PlotlyGraph – widgets nicht verfügbar]").classes("text-grey")

        else:
            # Unbekannter Typ: Platzhalter
            ui.label(f"[{widget_type}]").classes("text-grey")
