"""
Layout-basierte App (Template standard_app).

- Layout aus layout.json
- State aus model_schema (SESSION_STATE_PATH)
- Callbacks aus callback_skeleton (User füllt Logik)
- GUI wird aus Layout gebaut (build_ui_from_layout)
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

# App-Root = Parent von _core (wird beim Klonen zum jeweiligen App-Ordner); lab_suite für widgets, app_builder
_this_dir = Path(__file__).resolve().parent
APP_ROOT = _this_dir.parent
_lab_suite_root = APP_ROOT.parent.parent
if str(_lab_suite_root) not in sys.path:
    sys.path.insert(0, str(_lab_suite_root))

from nicegui import Client, app, ui

from app_builder import (
    build_ui_from_layout,
    collect_all_widget_path_ids,
    collect_callback_names,
    get_widget_node_by_path_id,
    load_layout,
)
from app_builder.editor_helper import get_editor_context

# Projektbezogene Module (gleicher Ordner)
from .assignment_registry import (
    get_active_assignment_name,
    get_assignment,
    list_assignments,
    set_active_assignment,
)
from .callback_skeleton import get_callback_registry
from .gui_binding import update_binding_from_layout
from .model_schema import load_state, save_state, STATE_DEFAULTS

# Property-Editor (wie im Grid-Editor)
from app_builder import get_prop_editor_specs


def _parse_list_or_keep(value: Any) -> list | str:
    """Parse JSON list or comma-separated string; return as list or keep string."""
    if isinstance(value, list):
        return value
    s = str(value).strip()
    if not s:
        return []
    try:
        out = json.loads(s)
        return out if isinstance(out, list) else [out]
    except json.JSONDecodeError:
        return [x.strip() for x in s.split(",") if x.strip()]


def _to_num(value: Any, default: int | float, is_int: bool = False) -> int | float:
    """Coerce value to int or float for prop editor."""
    if value is None or value == "":
        return int(default) if is_int else float(default)
    if isinstance(value, (int, float)):
        return int(value) if is_int else float(value)
    try:
        n = float(value)
        return int(n) if is_int else n
    except (TypeError, ValueError):
        return int(default) if is_int else float(default)

# Neutraler Name (unabhängig vom App-Ordner; Klonen/Umbenennen bricht nicht).
# Nur "session_state.json" – nicht ".development_app_state.json".
# Session-State-Datei: neutraler Name (session_state.json), unabhängig vom App-Ordner.
SESSION_STATE_FILENAME = "session_state.json"
SESSION_STATE_PATH = APP_ROOT / SESSION_STATE_FILENAME
USER_CALLBACKS_PATH = APP_ROOT / "assignments" / "user_callbacks.py"
LAYOUT_PATH = APP_ROOT / "layout.json"

# Static files for Monaco editor iframe (once at import, not per connection)
_static_dir = APP_ROOT / "static"
if _static_dir.exists():
    try:
        app.add_static_files("/static", str(_static_dir))
    except Exception:
        pass  # Route may already exist

# Gemeinsame Widget-Assets (z. B. plotly.min.js) – eine Kopie für alle Apps
_widgets_static = _lab_suite_root / "widgets" / "static"
if _widgets_static.exists():
    try:
        app.add_static_files("/widgets-static", str(_widgets_static))
    except Exception:
        pass

# Gemeinsamer State für alle Clients (ein Tab = eine state-Kopie würde beim Shutdown mit altem Stand überschreiben)
_SHARED_STATE_REF: list = [None]


async def build_root() -> None:
    await ui.context.client.connected()
    # Skip building if client already disconnected (e.g. user refreshed); avoids "Client has been deleted" warning.
    try:
        instances = getattr(Client, "instances", None)
        if instances is not None and ui.context.client.id not in instances:
            return
    except Exception:
        pass

    layout = load_layout(LAYOUT_PATH)
    layout.setdefault("appearance", {})
    update_binding_from_layout(layout)  # SEMANTIC_BINDING aus props.user_id befüllen
    if _SHARED_STATE_REF[0] is None:
        _SHARED_STATE_REF[0] = load_state(APP_ROOT / SESSION_STATE_FILENAME)
    state = _SHARED_STATE_REF[0]
    callbacks = get_callback_registry()

    state_label_holder: list = []
    _persist_state_timer_ref: list = [None]  # für debounced Save bei Widget-Änderung
    # Edit-Modus: an = Code-Editor-Expansion ist offen (geöffnet per Button oder Klick auf Expansion).
    # Nur im Edit-Modus: Hover über Widget zeigt path_id (title); Auswahlbox (Rahmen); Klick auf Widget setzt Auswahl (ohne Aktion).
    # Edit-Modus aus: Expansion zu (Schließen-Button oder Expansion zuklappen) → Hover/Box aus, Klick auf Widget löst normale Aktion aus.
    edit_mode_ref: list = [False]
    edit_select_handler_ref: list = [None]  # wird später mit _handle_edit_select_path belegt
    show_markdown_source_ref: list = [False]  # global: True = Quelltext, False = Vorschau; Default unchecked
    markdown_views_ref: list = []  # Liste (source_container, preview_container) pro editierbarem Markdown; für globalen Toggle
    markdown_source_checkbox_ref: list = []  # Checkbox „Markdown Quelltext“, Wert nach Toggle daraus lesen
    edit_mode_checkbox_ref: list = []
    edit_mode_container_ref: list = []  # wird in Editor-Bereich befüllt
    debug_mode_ref: list = [False]  # DEBUG MODE: State-Dictionary-Anzeige ein/aus
    debug_mode_checkbox_ref: list = []
    state_label_container_ref: list = []  # Container um State-Label; Sichtbarkeit per DEBUG MODE

    def _refresh_state_display() -> None:
        if state_label_holder:
            el = state_label_holder[0]
            el.text = "State (Keys = Path-IDs): " + str(state)
            el.update()
        _schedule_persist_state()  # session_state.json debounced speichern

    def _on_edit_select_from_layout(path_id: str) -> None:
        """Wird vom Renderer bei Klick auf Widget im Edit-Modus aufgerufen (Callback-Handler)."""
        if edit_select_handler_ref[0]:
            edit_select_handler_ref[0](path_id)

    # State + Widget-Registry am Client: für gui_binding.get/set und direkten Zugriff (path_id → Instanz).
    ui.context.client.state = state
    widget_registry = getattr(ui.context.client, "widget_registry", None)
    if widget_registry is None:
        ui.context.client.widget_registry = {}
        widget_registry = ui.context.client.widget_registry
    widget_registry.clear()
    state_input_registry = getattr(ui.context.client, "state_input_registry", None)
    if state_input_registry is None:
        ui.context.client.state_input_registry = {}
        state_input_registry = ui.context.client.state_input_registry
    state_input_registry.clear()

    sticky_header_rows = int(layout.get("appearance", {}).get("sticky_header_rows", 1))
    if sticky_header_rows < 0:
        sticky_header_rows = 0

    def _sync_edit_mode_ui() -> None:
        """Hover (title) und Auswahlbox nur im Edit-Modus; Editor-Container Sichtbarkeit."""
        if edit_mode_container_ref:
            edit_mode_container_ref[0].set_visibility(edit_mode_ref[0])
            edit_mode_container_ref[0].update()
        if edit_mode_ref[0]:
            ui.run_javascript("""
                document.querySelectorAll("[data-path-id]").forEach(function(el) {
                    var pid = el.getAttribute("data-path-id") || "";
                    var uid = el.getAttribute("data-user-id");
                    el.setAttribute("title", uid ? pid + " | user_id: " + uid : pid);
                });
            """)
        else:
            ui.run_javascript("""
                document.querySelectorAll("[data-path-id]").forEach(function(el) { el.removeAttribute("title"); });
                document.querySelectorAll(".widget-selected").forEach(function(el) { el.classList.remove("widget-selected"); });
            """)

    def _set_markdown_global_view(show_source: bool) -> None:
        show_markdown_source_ref[0] = show_source
        if not show_source:
            # Vor Anzeige der Vorschau: aktuelle Werte aus Textareas (state_input_registry) in state übernehmen
            reg = getattr(ui.context.client, "state_input_registry", None)
            if reg:
                for path_id, w in reg.items():
                    try:
                        val = getattr(w, "value", None)
                        if val is not None:
                            state[path_id] = val
                    except Exception:
                        pass
            _refresh_state_display()
        for item in markdown_views_ref:
            src_el = item[0]
            prev_el = item[1]
            # Widget-Level-Override: bei Plain-Text (z. B. Huffman-Eingabe) immer Quelltext anzeigen, unabhängig vom globalen Toggle
            effective_show_source = show_source if (len(item) <= 3 or not item[3]) else True
            # Beim Wechsel auf Vorschau: Inhalt aus state in die Vorschau übernehmen
            if not effective_show_source and len(item) > 2 and callable(item[2]):
                try:
                    item[2]()
                except Exception:
                    pass
            try:
                # set_visibility + update; Fallback: style display (manche NiceGUI-Elemente reagieren zuverlässiger)
                if hasattr(src_el, "set_visibility"):
                    src_el.set_visibility(effective_show_source)
                    src_el.update()
                if hasattr(src_el, "style"):
                    src_el.style(f"display: {'none' if not effective_show_source else 'block'};")
                if hasattr(prev_el, "set_visibility"):
                    prev_el.set_visibility(not effective_show_source)
                    prev_el.update()
                if hasattr(prev_el, "style"):
                    prev_el.style(f"display: {'block' if not effective_show_source else 'none'};")
            except Exception:
                pass

    def _on_after_sticky_content() -> None:
        """Globale Schalter-Zeile im Sticky-Bereich (unter dem Banner)."""
        with ui.row().classes("items-center gap-4 w-full mt-2 px-2"):
            edit_cb = ui.checkbox("Edit-Modus", value=edit_mode_ref[0]).props("dense")

            def _on_edit_mode_change(e) -> None:
                if edit_mode_checkbox_ref:
                    edit_mode_ref[0] = bool(edit_mode_checkbox_ref[0].value)
                else:
                    edit_mode_ref[0] = bool(getattr(e, "args", False))
                _sync_edit_mode_ui()
                if edit_mode_ref[0] and _load_editor_for_current_selection_ref:
                    _load_editor_for_current_selection_ref[0]()

            edit_cb.on("update:model-value", _on_edit_mode_change)
            edit_mode_checkbox_ref.append(edit_cb)

            def _on_markdown_source_change(e) -> None:
                # Wert aus Checkbox lesen (Vue hat ihn bereits aktualisiert), nicht aus e.args
                if markdown_source_checkbox_ref:
                    show_source = bool(markdown_source_checkbox_ref[0].value)
                else:
                    show_source = bool(getattr(e, "args", show_markdown_source_ref[0]))
                _set_markdown_global_view(show_source)

            md_source_cb = ui.checkbox(
                "Markdown Quelltext",
                value=show_markdown_source_ref[0],
            ).props("dense")
            markdown_source_checkbox_ref.append(md_source_cb)
            md_source_cb.on("update:model-value", _on_markdown_source_change)

            def _on_debug_mode_change(e) -> None:
                if debug_mode_checkbox_ref:
                    debug_mode_ref[0] = bool(debug_mode_checkbox_ref[0].value)
                else:
                    debug_mode_ref[0] = bool(getattr(e, "args", False))
                if state_label_container_ref:
                    state_label_container_ref[0].set_visibility(debug_mode_ref[0])
                    state_label_container_ref[0].update()

            dbg_cb = ui.checkbox("DEBUG MODE", value=debug_mode_ref[0]).props("dense")
            debug_mode_checkbox_ref.append(dbg_cb)
            dbg_cb.on("update:model-value", _on_debug_mode_change)

            ui.space()
            ui.label("(Edit-Modus: Hover path_id, Rahmen, Klick wählt; Code/Properties erscheinen)").classes(
                "text-caption text-grey"
            )

    _load_editor_for_current_selection_ref: list = [lambda: None]

    build_ui_from_layout(
        layout,
        state,
        callbacks,
        on_state_change=_refresh_state_display,
        get_edit_mode=lambda: edit_mode_ref[0],
        on_edit_select_path=_on_edit_select_from_layout,
        widget_registry=widget_registry,
        state_input_registry=state_input_registry,
        sticky_header_rows=sticky_header_rows,
        on_after_sticky_content=_on_after_sticky_content if sticky_header_rows > 0 else None,
        get_show_markdown_source=lambda: show_markdown_source_ref[0],
        register_markdown_view=lambda src, prev, update=None, always_show_source=False: markdown_views_ref.append((src, prev, update, always_show_source)),
    )

    # Timer für User-Logik (Plot-Updates etc.); Rate über Umgebungsvariable TIMER_INTERVAL_SEC (z. B. 0.1 = 10 Hz)
    _timer_interval = float(__import__("os").environ.get("TIMER_INTERVAL_SEC", "0.1"))
    if _timer_interval > 0:

        def _timer_callback() -> None:
            mod = get_assignment()
            if mod is not None and hasattr(mod, "timer_tick"):
                try:
                    mod.timer_tick()
                except Exception:
                    pass

        ui.timer(_timer_interval, _timer_callback)

    # State-Dictionary-Anzeige (Code bleibt; Sichtbarkeit per DEBUG MODE Checkbox)
    with ui.element("div") as state_label_container:
        state_label = ui.label("State (Keys = Path-IDs): " + str(state)).classes("text-caption")
        state_label_holder.append(state_label)
    state_label_container_ref.append(state_label_container)
    state_label_container.set_visibility(debug_mode_ref[0])

    # ---- Editor-Modus: CodeMirror (fertiger Editor mit Zeilennummern, Syntax, Scroll) ----
    # Dropdown mit allen Widgets (nicht nur Callback-Widgets), damit z. B. toggle_button, led, vu_meter Properties bearbeitet werden können.
    callbacks_list = collect_callback_names(layout)
    path_id_options = {pid: pid for pid in collect_all_widget_path_ids(layout)}
    editor_header_label: list = []
    editor_cm_ref: list = []
    if path_id_options:
        # CSS für ausgewähltes Widget und CodeMirror (Kommentare grün)
        ui.add_head_html(
            "<style>"
            ".widget-selected { outline: 2px solid var(--q-primary); outline-offset: 2px; border-radius: 4px; }"
            " .cm-editor .cm-content .cm-comment-custom { color: #0a5f0a !important; }"
            "</style>"
        )
        path_id_select_ref: list = []
        editor_header_label: list = []
        editor_cm_ref: list = []
        props_container: list = []
        copied_props_ref: list = []  # Copy/Paste: gespeicherte props (ein Dict)

        def refresh_props_panel() -> None:
            """Property-Editor-Inhalt für das aktuell gewählte Widget füllen (wie Grid-Editor)."""
            if not props_container:
                return
            cont = props_container[0]
            cont.clear()
            path_id = path_id_select_ref[0].value if path_id_select_ref else None
            node = get_widget_node_by_path_id(layout, path_id) if path_id else None
            with cont:
                ui.label("Widget-Properties (layout.json)").classes("text-weight-medium")
                if not node:
                    ui.label("Widget im Dropdown „Widget (path_id)“ oben wählen.").classes("text-grey")
                    return
                widget_type = node.get("widget_type", "")
                ui.label(f"id: {node.get('id', '')} · widget_type: {widget_type}").classes("text-caption")
                props = node.setdefault("props", {})

                def set_prop(key: str, value: Any) -> None:
                    props[key] = value

                for spec in get_prop_editor_specs(widget_type):
                    key = spec["key"]
                    current = props.get(key, spec["default"])
                    label = spec.get("label", key)
                    prop_type = spec.get("type", "string")
                    if prop_type == "boolean":
                        ui.checkbox(label, value=bool(current)).classes("w-full").on(
                            "update:model-value", lambda e, k=key: set_prop(k, e.args)
                        )
                    elif prop_type in ("integer", "number"):
                        num_min = spec.get("min")
                        num_max = spec.get("max")
                        default = spec["default"]
                        is_int = prop_type == "integer"
                        num_val = _to_num(
                            current,
                            default if isinstance(default, (int, float)) else (0 if is_int else 0.0),
                            is_int,
                        )
                        props_str = "dense"
                        if num_min is not None:
                            props_str += f" min={num_min}"
                        if num_max is not None:
                            props_str += f" max={num_max}"
                        ui.number(label, value=num_val).classes("w-full").props(props_str).on(
                            "update:model-value",
                            lambda e, k=key, d=default, i=is_int: set_prop(
                                k,
                                _to_num(
                                    e.args,
                                    d if isinstance(d, (int, float)) else (0 if i else 0.0),
                                    i,
                                ),
                            ),
                        )
                    elif prop_type == "list":
                        raw = json.dumps(current) if isinstance(current, list) else str(current)
                        ui.input(label, value=raw).classes("w-full").props("dense").on(
                            "update:model-value",
                            lambda e, k=key: set_prop(k, _parse_list_or_keep(e.args)),
                        )
                    elif prop_type == "color":
                        color_val = (current if isinstance(current, str) else "") or ""

                        def _coerce_color(v):
                            if isinstance(v, str) and v.strip():
                                return v.strip()
                            if isinstance(v, dict) and v.get("hex"):
                                return str(v["hex"]).strip()
                            return str(v).strip() if v else ""

                        with ui.row().classes("w-full items-center gap-1"):
                            inp = ui.input(
                                label=label,
                                value=color_val,
                                placeholder="#rrggbb",
                            ).classes("flex-grow").props("dense").on(
                                "update:model-value",
                                lambda e, k=key: set_prop(k, _coerce_color(getattr(e, "args", None))),
                            )
                            def _on_color_pick(e, k=key, inp_ref=inp):
                                color = _coerce_color(getattr(e, "color", None)) or ""
                                set_prop(k, color)
                                inp_ref.value = color
                                inp_ref.update()
                            picker = ui.color_picker(on_pick=_on_color_pick)
                            def _open_picker(picker_ref=picker, inp_ref=inp):
                                picker_ref.set_color(inp_ref.value or "#000000")
                                picker_ref.open()
                            ui.button(icon="colorize", on_click=_open_picker).props("flat round dense")
                    elif spec.get("options"):
                        opts = list(spec["options"])
                        # NiceGUI select sends {value: index, label: str}; index -> opts[i]
                        if isinstance(current, dict):
                            idx = current.get("value")
                            current = opts[idx] if isinstance(idx, int) and 0 <= idx < len(opts) else (current.get("label") or (opts[0] if opts else ""))
                            set_prop(key, current)
                        elif isinstance(current, int) and 0 <= current < len(opts):
                            current = opts[current]
                            set_prop(key, current)
                        val = current if current in opts else (opts[0] if opts else "")
                        def _option_value(e, k=key):
                            v = getattr(e, "args", None)
                            if isinstance(v, dict):
                                idx = v.get("value")
                                v = opts[idx] if isinstance(idx, int) and 0 <= idx < len(opts) else (v.get("label") or (opts[0] if opts else ""))
                            elif isinstance(v, int) and 0 <= v < len(opts):
                                v = opts[v]
                            set_prop(k, v)
                        ui.select(
                            options=opts,
                            value=val,
                            label=label,
                        ).classes("w-full").props("dense").on(
                            "update:model-value", _option_value
                        )
                    else:
                        ui.input(
                            label, value=str(current) if current is not None else ""
                        ).classes("w-full").props("dense").on(
                            "update:model-value", lambda e, k=key: set_prop(k, e.args)
                        )

        def save_layout_json() -> None:
            try:
                with open(LAYOUT_PATH, "w", encoding="utf-8") as f:
                    json.dump(layout, f, indent=2, ensure_ascii=False)
                ui.notify("Layout gespeichert. Seite neu laden, um Änderungen zu sehen.", type="positive")
            except Exception as e:
                ui.notify(f"Layout speichern fehlgeschlagen: {e}", type="negative")

        def _load_editor_for_current_selection() -> bool:
            """Lädt user_callbacks.py für das aktuell gewählte Widget in den Editor. Gibt True bei Erfolg zurück."""
            path_id = path_id_select_ref[0].value if path_id_select_ref else None
            if not path_id or not USER_CALLBACKS_PATH.exists():
                return False
            try:
                content, line = get_editor_context(USER_CALLBACKS_PATH, path_id)
            except Exception:
                return False
            if editor_header_label:
                editor_header_label[0].text = f'user_callbacks.py — Callback „{path_id}" (Zeile {line})'
                editor_header_label[0].update()
            if editor_cm_ref:
                editor_cm_ref[0].value = content
                editor_cm_ref[0].update()
                # Syntax: Kommentare grün färben (CodeMirror 6 hat keine stabilen Klassen)
                _apply_codemirror_comment_highlight(editor_cm_ref[0].html_id)
            return True

        _load_editor_for_current_selection_ref[0] = _load_editor_for_current_selection

        def _apply_codemirror_comment_highlight(cm_id: str) -> None:
            """Markiert Kommentar-Zeilen im CodeMirror mit .cm-comment-custom (grün per CSS)."""
            js = f"""
                (function() {{
                    setTimeout(function() {{
                        var el = document.getElementById({cm_id!r});
                        if (!el) return;
                        var content = el.querySelector('.cm-content');
                        if (!content) return;
                        var lines = content.querySelectorAll('.cm-line');
                        for (var i = 0; i < lines.length; i++) {{
                            var line = lines[i];
                            var text = (line.textContent || '').trim();
                            if (text.indexOf('#') === 0) {{
                                var spans = line.querySelectorAll('span');
                                for (var j = 0; j < spans.length; j++) spans[j].classList.add('cm-comment-custom');
                            }}
                        }}
                    }}, 150);
                }})();
            """
            ui.run_javascript(js)

        async def open_editor() -> None:
            path_id = path_id_select_ref[0].value if path_id_select_ref else None
            if not path_id:
                ui.notify("Zuerst ein Widget im Dropdown oben wählen.", type="warning")
                return
            if not USER_CALLBACKS_PATH.exists():
                ui.notify("user_callbacks.py missing.", type="warning")
                return
            if not _load_editor_for_current_selection():
                ui.notify("Fehler beim Laden der Datei.", type="negative")
                return
            edit_mode_ref[0] = True
            if edit_mode_checkbox_ref:
                edit_mode_checkbox_ref[0].value = True
                edit_mode_checkbox_ref[0].update()
            _sync_edit_mode_ui()
            if edit_select_handler_ref[0]:
                edit_select_handler_ref[0](path_id)
            # CodeMirror: Zeile scrollen + Zeile programmatisch fokussieren
            try:
                content, line = get_editor_context(USER_CALLBACKS_PATH, path_id)
            except Exception:
                content, line = "", 1
            if editor_cm_ref:
                cm = editor_cm_ref[0]
                focus_line = max(1, min(line, len(content.splitlines()) or 1))
                cm_id = cm.html_id
                js = f"""
                    (function() {{
                        requestAnimationFrame(function() {{
                            setTimeout(function() {{
                                var el = document.getElementById({cm_id!r});
                                if (!el) return;
                                var scroller = el.querySelector('.cm-scroller');
                                if (scroller) {{
                                    var lineHeight = 20;
                                    scroller.scrollTop = Math.max(0, ({focus_line} - 1) * lineHeight - 80);
                                }}
                                var view = null;
                                try {{
                                    var root = el.querySelector('.cm-editor') || el;
                                    if (root._view) view = root._view;
                                    if (!view && el.__vueParentComponent) {{
                                        var ctx = el.__vueParentComponent.ctx;
                                        view = ctx.view || ctx.editorView || (ctx.$refs && ctx.$refs.editor && ctx.$refs.editor.view);
                                    }}
                                    if (!view && typeof getElement !== "undefined") {{
                                        var comp = getElement({cm_id!r});
                                        if (comp && (comp.view || comp.editorView)) view = comp.view || comp.editorView;
                                    }}
                                }} catch (e) {{}}
                                if (view && view.dispatch && view.state && view.state.doc) {{
                                    try {{
                                        var doc = view.state.doc;
                                        var lineObj = doc.line(Math.min({focus_line}, doc.lines));
                                        var pos = lineObj.from;
                                        view.dispatch({{ selection: {{ anchor: pos, head: pos }} }});
                                        view.focus();
                                    }} catch (e) {{}}
                                }} else {{
                                    var content = el.querySelector('.cm-content');
                                    if (content) {{
                                        var lines = content.querySelectorAll('.cm-line');
                                        if (lines.length >= {focus_line} && {focus_line} >= 1) {{
                                            var lineEl = lines[{focus_line} - 1];
                                            var rect = lineEl.getBoundingClientRect();
                                            lineEl.dispatchEvent(new MouseEvent('click', {{ bubbles: true, view: window, clientX: rect.left + 8, clientY: rect.top + rect.height / 2 }}));
                                        }}
                                    }}
                                }}
                            }}, 120);
                        }});
                    }})();
                """
                await ui.run_javascript(js)

        def save_editor() -> None:
            if not editor_cm_ref:
                return
            text = editor_cm_ref[0].value or ""
            try:
                USER_CALLBACKS_PATH.write_text(text, encoding="utf-8")
                ui.notify("Gespeichert.", type="positive")
            except Exception as e:
                ui.notify(f"Fehler beim Speichern: {e}", type="negative")

        def close_editor() -> None:
            edit_mode_ref[0] = False
            _sync_edit_mode_ui()
            if edit_mode_checkbox_ref:
                edit_mode_checkbox_ref[0].value = False
                edit_mode_checkbox_ref[0].update()
            if editor_header_label:
                editor_header_label[0].text = (
                    "user_callbacks.py — Widget wählen und oben „Open user_callbacks.py“ klicken."
                )
                editor_header_label[0].update()

        # Editor-Container: nur sichtbar wenn Edit-Modus an (Dropdown + Tabs Code | Properties)
        with ui.column().classes("w-full mt-2 gap-2") as edit_container:
            edit_mode_container_ref.append(edit_container)
            edit_container.set_visibility(False)

            # Aktives Assignment (assignments/*.py) – Auswahl für Studierende
            assignment_options = list_assignments()
            if assignment_options:
                with ui.row().classes("items-center gap-2"):
                    ui.label("Aktives Assignment:").classes("text-weight-medium")
                    assignment_sel = ui.select(
                        options={x: x for x in assignment_options},
                        value=get_active_assignment_name(),
                        label="Assignment",
                    ).classes("w-48")
                    def _on_assignment_change(e):
                        val = getattr(e, "args", None)
                        if val:
                            set_active_assignment(val)
                            ui.notify(f'Assignment "{val}" aktiv. Nächste Aktion nutzt es.', type="positive")
                    assignment_sel.on("update:model-value", _on_assignment_change)

            with ui.row().classes("items-center gap-2"):
                ui.label("Widget (path_id):").classes("text-weight-medium")
                path_sel = ui.select(
                    options=path_id_options,
                    value=next(iter(path_id_options)) if path_id_options else None,
                    label="Widget",
                ).classes("w-64")
                path_id_select_ref.append(path_sel)

            def _handle_edit_select_path(path_id: str) -> None:
                if path_id_select_ref:
                    path_id_select_ref[0].value = path_id
                    path_id_select_ref[0].update()
                if editor_header_label:
                    try:
                        _, line = get_editor_context(USER_CALLBACKS_PATH, path_id)
                        editor_header_label[0].text = f'user_callbacks.py — Callback „{path_id}" (Zeile {line})'
                    except Exception:
                        editor_header_label[0].text = f'user_callbacks.py — Callback „{path_id}"'
                    editor_header_label[0].update()
                if edit_mode_ref[0]:
                    path_id_js = json.dumps(path_id)
                    ui.run_javascript(f"""
                    (function() {{
                        var sel = {path_id_js};
                        document.querySelectorAll('[data-path-id]').forEach(function(el) {{
                            el.classList.toggle('widget-selected', el.getAttribute('data-path-id') === sel);
                        }});
                    }})();
                    """)
                refresh_props_panel()

            edit_select_handler_ref[0] = _handle_edit_select_path
            path_id_select_ref[0].on(
                "update:model-value",
                lambda e: _handle_edit_select_path(e.args) if getattr(e, "args", None) else None,
            )

            with ui.tabs().classes("w-full") as tabs:
                tab_code = ui.tab("Code", label="Code (user_callbacks.py)")
                tab_props = ui.tab("Properties", label="Properties (layout)")
                tab_appearance = ui.tab("Appearance", label="App-Oberfläche")
            with ui.tab_panels(tabs, value=tab_code).classes("w-full mt-1") as tab_panels:

                with ui.tab_panel(tab_code):
                    with ui.card().classes("w-full column gap-2 p-3").style(
                        "display: flex; flex-direction: column; min-height: 80vh;"
                    ):
                        lbl = ui.label("user_callbacks.py — Widget im Dropdown wählen; Inhalt lädt beim Aktivieren des Edit-Modus oder beim Wechsel auf diesen Tab.")
                        editor_header_label.append(lbl)
                        with ui.row().classes("gap-2 shrink-0"):
                            ui.button("Save", on_click=save_editor).props("flat color=primary")
                            ui.button("Schließen", on_click=close_editor).props("flat")
                        with ui.element("div").style("min-height: 70vh; height: 70vh; width: 100%;"):
                            cm = ui.codemirror(
                                value="",
                                language="Python",
                                theme="basicLight",
                            ).classes("w-full h-full")
                            cm.style("height: 100%;")
                            editor_cm_ref.append(cm)

                def do_copy_properties() -> None:
                    if not path_id_select_ref:
                        ui.notify("Select a widget first.", type="warning")
                        return
                    node = get_widget_node_by_path_id(layout, path_id_select_ref[0].value)
                    if not node:
                        ui.notify("Select a widget first.", type="warning")
                        return
                    copied_props_ref.clear()
                    copied_props_ref.append(copy.deepcopy(node.get("props", {})))
                    ui.notify("Properties copied.", type="positive")

                def do_paste_properties() -> None:
                    if not copied_props_ref:
                        ui.notify("Copy a widget's properties first.", type="warning")
                        return
                    if not path_id_select_ref:
                        ui.notify("Select a widget first.", type="warning")
                        return
                    node = get_widget_node_by_path_id(layout, path_id_select_ref[0].value)
                    if not node:
                        ui.notify("Select a widget first.", type="warning")
                        return
                    node.setdefault("props", {}).update(copy.deepcopy(copied_props_ref[0]))
                    refresh_props_panel()
                    ui.notify("Pasted. Save layout to persist.", type="positive")

                with ui.tab_panel(tab_props):
                    with ui.card().classes("w-full p-3"):
                        with ui.row().classes("w-full gap-2 items-center"):
                            ui.label("Properties").classes("text-weight-medium")
                            ui.button("Copy properties", on_click=do_copy_properties).props("flat dense")
                            ui.button("Paste properties", on_click=do_paste_properties).props("flat dense")
                        with ui.column().classes("w-full gap-2") as props_col:
                            props_container.append(props_col)
                        ui.label("Widget über Dropdown oben wählen (oder Klick auf Widget im Edit-Modus).").classes(
                            "text-caption text-grey"
                        )
                        ui.button("Layout speichern (layout.json)", on_click=save_layout_json).props(
                            "flat dense color=primary"
                        )
                        ui.label("Änderungen erst nach Neuladen der Seite sichtbar.").classes("text-caption text-grey")

                with ui.tab_panel(tab_appearance):
                    with ui.card().classes("w-full p-3"):
                        ui.label("App-Oberfläche (layout.json → appearance)").classes("text-weight-medium")
                        ui.label(
                            "Dezente Hintergründe und Abstände für Container (z. B. Zeilen) und Seite. "
                            "Leer = kein Vorgabewert; einzelne Container können weiterhin eigenes style setzen."
                        ).classes("text-caption text-grey")
                        app_opt = layout.setdefault("appearance", {})

                        def _appearance_value(val: Any) -> str:
                            """String für Anzeige/Speicherung; layout kann Dict aus Editor speichern."""
                            if val is None:
                                return ""
                            if isinstance(val, dict):
                                return str(val.get("value") or val.get("label") or "").strip()
                            return str(val).strip() if val else ""

                        def _appearance_input(label: str, key: str, placeholder: str = ""):
                            with ui.row().classes("items-center gap-2 w-full"):
                                ui.label(label).classes("w-48 shrink-0")
                                inp = ui.input(
                                    value=_appearance_value(app_opt.get(key)),
                                    placeholder=placeholder,
                                ).classes("flex-grow").props("dense")
                                inp.on("update:model-value", lambda e, k=key: app_opt.update({k: getattr(e, "args", "") or ""}))

                        _appearance_input("Seiten-Padding", "page_padding", "z. B. 16px")
                        _appearance_input("Seiten-Hintergrund", "page_background", "z. B. #fafafa")
                        _appearance_input("Container-Hintergrund", "container_background", "z. B. #f0f0f0")
                        _appearance_input("Container-Padding", "container_padding", "z. B. 12px")
                        _appearance_input("Container-Abstand (gap)", "container_gap", "z. B. 0.5rem")
                        _appearance_input("Container-Ecken (radius)", "container_border_radius", "z. B. 8px")

                        ui.label("Inhaltshöhe (Bereich unter Sticky-Header):").classes("text-weight-medium mt-3")

                        def _normalize_scroll_content_mode(val: Any) -> str:
                            """Immer 'fixed' oder 'flex' (layout.json kann Dict aus Select speichern)."""
                            if isinstance(val, dict):
                                label = str(val.get("label") or val.get("value") or "").lower()
                                return "flex" if "flexibel" in label else "fixed"
                            s = str(val).strip().lower()
                            return "flex" if s == "flex" else "fixed"

                        scroll_mode = _normalize_scroll_content_mode(app_opt.get("scroll_content_mode", "fixed"))
                        scroll_mode_select = ui.select(
                            options={"fixed": "Fixe Höhe (Scrollbereich mit max. Höhe)", "flex": "Flexibel (gesamte Seite scrollt)"},
                            value=scroll_mode,
                            label="Modus",
                        ).classes("w-full").props("dense")
                        scroll_mode_select.on(
                            "update:model-value",
                            lambda e: app_opt.update({"scroll_content_mode": _normalize_scroll_content_mode(getattr(e, "args", "fixed"))}),
                        )
                        with ui.row().classes("items-center gap-2 w-full mt-1"):
                            ui.label("Scrollbereich max. Höhe (nur bei „Fixe Höhe“):").classes("w-48 shrink-0")
                            scroll_max_inp = ui.input(
                                value=_appearance_value(app_opt.get("scroll_area_max_height")) or "calc(100vh - 180px)",
                                placeholder="z. B. calc(100vh - 180px) oder 80vh",
                            ).classes("flex-grow").props("dense")
                            scroll_max_inp.on(
                                "update:model-value",
                                lambda e: app_opt.update({"scroll_area_max_height": getattr(e, "args", "") or "calc(100vh - 180px)"}),
                            )
                        ui.label(
                            "Fixe Höhe = nur der Inhaltsbereich scrollt; flexibel = ganze Seite scrollt wie vor Sticky-Header."
                        ).classes("text-caption text-grey")

                        ui.label("Layout speichern (Tab Properties) und Seite neu laden, um Änderungen zu sehen.").classes(
                            "text-caption text-grey"
                        )
                        ui.button("Layout speichern (layout.json)", on_click=save_layout_json).props(
                            "flat dense color=primary"
                        )

            def _on_tab_change(e) -> None:
                val = getattr(e, "args", None)
                if val == "Code" or val is tab_code:
                    _load_editor_for_current_selection()
                elif val == "Properties" or val is tab_props:
                    refresh_props_panel()

            tab_panels.on("update:model-value", _on_tab_change)

    def _persist_state() -> None:
        """Schreibt state in session_state.json (für Disconnect und bei Widget-Änderung)."""
        reg = getattr(ui.context.client, "state_input_registry", None)
        if reg:
            for path_id, w in reg.items():
                try:
                    val = getattr(w, "value", None)
                    if val is not None:
                        state[path_id] = val
                except Exception:
                    pass
        save_state(state, APP_ROOT / SESSION_STATE_FILENAME)

    def _schedule_persist_state() -> None:
        """Speichert state nach 1,5 s Verzögerung (debounce), damit nicht bei jedem Slider-Tick geschrieben wird."""
        if _persist_state_timer_ref[0] is not None:
            try:
                _persist_state_timer_ref[0].cancel()
            except Exception:
                pass
            _persist_state_timer_ref[0] = None

        def _do_persist() -> None:
            _persist_state_timer_ref[0] = None
            try:
                _persist_state()
            except Exception:
                pass

        t = ui.timer(1.5, _do_persist, once=True)
        _persist_state_timer_ref[0] = t

    def _save_before_disconnect():
        _persist_state()

    ui.context.client.on_disconnect(_save_before_disconnect)


def main() -> None:
    ui.run(
        root=build_root,
        port=int(__import__("os").environ.get("DEV_APP_PORT", "8081")),
        title="Development-App (App-Builder PoC)",
        reload=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()