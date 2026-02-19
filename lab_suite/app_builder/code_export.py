"""
Export layout.json als statischen Python-Code (NiceGUI-Aufrufe).

Option für Deployment: Statt zur Laufzeit den Renderer + layout.json zu nutzen,
wird aus dem Layout einmalig eine .py-Datei erzeugt, die dieselbe UI mit
reinen NiceGUI-Aufrufen baut. Kein Renderer, kein layout.json in der ausgelieferten App.

Verwendung:
  from app_builder.code_export import layout_to_python
  code = layout_to_python(layout)
  Path("deployed_ui.py").write_text(code, encoding="utf-8")

  # In der Ziel-App:
  from deployed_ui import build_ui
  build_ui(ui, state, callbacks, title="Meine App")
"""
from __future__ import annotations

from typing import Any


def _path(parent_path: str, node_id: str) -> str:
    return f"{parent_path}.{node_id}" if parent_path else (node_id or "dashboard")


def _repr_val(v: Any) -> str:
    """Sichere Python-Literal-Darstellung für generierten Code."""
    if v is None:
        return "None"
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return repr(v)
    if isinstance(v, (list, tuple)):
        return repr(v)
    if isinstance(v, dict):
        return repr(v)
    return repr(v)


class CodeWriter:
    def __init__(self, indent: str = "    ") -> None:
        self.indent_str = indent
        self._level = 0
        self._lines: list[str] = []

    def line(self, s: str = "") -> None:
        if s:
            self._lines.append(self._level * self.indent_str + s)
        else:
            self._lines.append("")

    def block(self, header: str, body: list[str]) -> None:
        self.line(header)
        self._level += 1
        for x in body:
            self._lines.append(self._level * self.indent_str + x)
        self._level -= 1

    def emit_children(
        self,
        children: list[dict],
        parent_path: str,
    ) -> None:
        for node in children:
            self._emit_node(node, parent_path)

    def _emit_node(self, node: dict, parent_path: str) -> None:
        node_id = node.get("id", "")
        path_id = _path(parent_path, node_id)
        node_type = node.get("type", "widget")

        if node_type == "widget":
            self._emit_widget(node, path_id)
            return

        if node_type == "group":
            label = node.get("label", "")
            self.line('with ui.column().classes("gap-1"):')
            self._level += 1
            if label:
                self.line(f"ui.label({repr(label)}).classes(\"text-weight-medium\")")
            self.emit_children(node.get("children", []), path_id)
            self._level -= 1
            return

        if node_type == "tab":
            return  # Tabs werden im tabs-Container behandelt

        if node_type != "container":
            return

        layout_type = node.get("layout_type", "rows_columns")
        style = node.get("style") or {}
        style_str = "; ".join(f"{k}: {v}" for k, v in style.items()) if style else ""

        if layout_type == "rows_columns":
            if style_str:
                self.line(f'with ui.element("div").style({repr(style_str)}):')
                self._level += 1
            self.line('with ui.row().classes("gap-4 items-center flex-wrap"):')
            self._level += 1
            self.emit_children(node.get("children", []), path_id)
            self._level -= 1
            if style_str:
                self._level -= 1
        elif layout_type == "column":
            if style_str:
                self.line(f'with ui.element("div").style({repr(style_str)}):')
                self._level += 1
            self.line('with ui.column().classes("gap-2 w-full"):')
            self._level += 1
            self.emit_children(node.get("children", []), path_id)
            self._level -= 1
            if style_str:
                self._level -= 1
        elif layout_type == "grid":
            columns = node.get("columns", 2)
            rows = node.get("rows")
            grid_args = f"columns={repr(columns)}"
            if rows is not None:
                grid_args += f", rows={repr(rows)}"
            if style_str:
                self.line(f'with ui.element("div").style({repr(style_str)}):')
                self._level += 1
            self.line(f"with ui.grid({grid_args}).classes(\"w-full gap-4\"):")
            self._level += 1
            for child in node.get("children", []):
                cs = child.get("col_span", 1)
                rs = child.get("row_span", 1)
                span_cls = f"col-span-{min(12, max(1, int(cs) if isinstance(cs, (int, float)) else 1))} row-span-{min(12, max(1, int(rs) if isinstance(rs, (int, float)) else 1))}"
                self.line(f'with ui.element("div").classes("{span_cls}"):')
                self._level += 1
                self._emit_node(child, path_id)
                self._level -= 1
            self._level -= 1
            if style_str:
                self._level -= 1
        elif layout_type == "expansion":
            label = node.get("label", node_id) or node_id
            if style_str:
                self.line(f'with ui.element("div").style({repr(style_str)}):')
                self._level += 1
            self.line(f'with ui.expansion({repr(label)}, value=False).classes("w-full"):')
            self._level += 1
            self.emit_children(node.get("children", []), path_id)
            self._level -= 1
            if style_str:
                self._level -= 1
        elif layout_type == "scroll":
            if style_str:
                self.line(f'with ui.element("div").style({repr(style_str)}):')
                self._level += 1
            self.line('with ui.scroll_area().classes("w-full gap-2"):')
            self._level += 1
            self.emit_children(node.get("children", []), path_id)
            self._level -= 1
            if style_str:
                self._level -= 1
        elif layout_type == "card":
            if style_str:
                self.line(f'with ui.element("div").style({repr(style_str)}):')
                self._level += 1
            self.line('with ui.card().classes("w-full gap-2"):')
            self._level += 1
            self.emit_children(node.get("children", []), path_id)
            self._level -= 1
            if style_str:
                self._level -= 1
        elif layout_type == "splitter":
            children = node.get("children", [])
            value = node.get("value", 30)
            orientation = node.get("orientation", "horizontal")
            if style_str:
                self.line(f'with ui.element("div").style({repr(style_str)}):')
                self._level += 1
            self.line(f"splitter = ui.splitter(value={float(value)}).classes(\"w-full\")")
            if orientation == "vertical":
                self.line('splitter.props("vertical")')
            self.line("with splitter.before:")
            self._level += 1
            for n in children[:1]:
                self._emit_node(n, path_id)
            self._level -= 1
            self.line("with splitter.after:")
            self._level += 1
            for n in children[1:2]:
                self._emit_node(n, path_id)
            self._level -= 1
            if style_str:
                self._level -= 1
        elif layout_type == "tabs":
            self._emit_tabs(node, path_id)
        elif layout_type == "xy":
            s = "position: relative; " + style_str if style_str else "position: relative;"
            self.line(f'with ui.element("div").style({repr(s)}):')
            self._level += 1
            self.emit_children(node.get("children", []), path_id)
            self._level -= 1
        else:
            self.line('with ui.row().classes("gap-4 flex-wrap"):')
            self._level += 1
            self.emit_children(node.get("children", []), path_id)
            self._level -= 1

    def _emit_tabs(self, node: dict, path: str) -> None:
        children = [c for c in node.get("children", []) if c.get("type") == "tab"]
        if not children:
            return
        labels = [c.get("label", c.get("id", "")) for c in children]
        first = labels[0] if labels else ""
        self.line("with ui.tabs() as tabs:")
        self._level += 1
        for lbl in labels:
            self.line(f"ui.tab({repr(lbl)})")
        self._level -= 1
        self.line(f'with ui.tab_panels(tabs, value={repr(first)}).classes("w-full"):')
        self._level += 1
        for tab_node, tlabel in zip(children, labels):
            self.line(f"with ui.tab_panel({repr(tlabel)}):")
            self._level += 1
            self.emit_children(tab_node.get("children", []), path)
            self._level -= 1
        self._level -= 1

    def _emit_widget(self, node: dict, path_id: str) -> None:
        widget_type = node.get("widget_type", "")
        props = node.get("props", {})

        def get_prop(key: str, default: Any = None) -> str:
            return _repr_val(props.get(key, default))

        if widget_type == "checkbox":
            default = props.get("value", False)
            self.line(f"path_id = {repr(path_id)}")
            self.line(f"val = state.get(path_id, {_repr_val(default)})")
            self.line(f"el = ui.checkbox({get_prop('label', node.get('id', ''))}, value=val)")
            self.line('el.on("update:model-value", lambda e, _pid=path_id: _on_value_change(state, callbacks, _pid, getattr(e, "args", getattr(getattr(e, "sender", None), "value", None))))')
        elif widget_type == "slider":
            default = props.get("value", 1)
            pmin = props.get("min", 0)
            pmax = props.get("max", 10)
            pstep = props.get("step", 0.01)
            self.line(f"path_id = {repr(path_id)}")
            self.line(f"val = float(state.get(path_id, {_repr_val(default)}))")
            self.line(f"el = ui.slider(min={_repr_val(pmin)}, max={_repr_val(pmax)}, value=val, step={_repr_val(pstep)}).classes(\"min-w-24\")")
            self.line('el.on("update:model-value", lambda e, _pid=path_id, w=el: _on_value_change(state, callbacks, _pid, float(getattr(e, "args", getattr(w, "value", val)))))')
            self.line(f"ui.label({get_prop('label', node.get('id', ''))}).classes(\"shrink-0 text-caption\")")
        elif widget_type == "button":
            self.line(f"path_id = {repr(path_id)}")
            self.line(f"ui.button({get_prop('label', node.get('id', ''))}, on_click=lambda _pid=path_id: (callbacks.get(_pid) or (lambda: None))())")
        elif widget_type == "number_input":
            default = props.get("value", 0)
            lbl = props.get("label", node.get("id", ""))
            self.line(f"path_id = {repr(path_id)}")
            self.line(f"val = float(state.get(path_id, {_repr_val(default)}))")
            self.line(f"el = ui.number(value=val).props(\"label={repr(lbl)}\")")
            self.line('el.on("update:model-value", lambda e, _pid=path_id, w=el: _on_value_change(state, callbacks, _pid, float(getattr(e, "args", getattr(w, "value", val)))))')
        elif widget_type == "input":
            default = props.get("value", "")
            self.line(f"path_id = {repr(path_id)}")
            self.line(f"val = state.get(path_id, {_repr_val(default)})")
            self.line(f"el = ui.input({get_prop('label', node.get('id', ''))}, value=val)")
            self.line('el.on("update:model-value", lambda e, _pid=path_id, w=el: _on_value_change(state, callbacks, _pid, getattr(e, "args", getattr(w, "value", val))))')
        elif widget_type == "select":
            default = props.get("value")
            opts = props.get("options", [])
            self.line(f"path_id = {repr(path_id)}")
            self.line(f"val = state.get(path_id, {_repr_val(default)})")
            self.line(f"el = ui.select({_repr_val(opts)}, value=val, label={get_prop('label', node.get('id', ''))})")
            self.line('el.on("update:model-value", lambda e, _pid=path_id, w=el: _on_value_change(state, callbacks, _pid, getattr(e, "args", getattr(w, "value", val))))')
        elif widget_type == "label":
            text = props.get("text", node.get("id", "Label"))
            heading = props.get("heading", "")
            if isinstance(heading, int) and 1 <= heading <= 6:
                h = ("h1", "h2", "h3", "h4", "h5", "h6")[heading - 1]
            elif isinstance(heading, str) and heading.strip().lower() in ("h1", "h2", "h3", "h4", "h5", "h6"):
                h = heading.strip().lower()
            else:
                h = ""
            self.line(f"lbl = ui.label({_repr_val(text)})")
            if h:
                self.line(f'lbl.classes("text-{h}")')
        elif widget_type == "link":
            url = (props.get("url") or "#").strip()
            if url and not url.startswith(("http://", "https://")):
                url = "https://" + url
            text = props.get("text", url)
            target = props.get("target", "_blank")
            self.line(f"ui.link({_repr_val(text)}, {_repr_val(url)}).props(\"target=\" + {_repr_val(target)})")
        elif widget_type == "image":
            src = props.get("src", "")
            alt = props.get("alt", "")
            if src:
                self.line(f"img = ui.image({_repr_val(src)})")
                if alt:
                    self.line(f"img.props(f'alt=\"{alt}\"')")
        elif widget_type == "table":
            cols = props.get("columns", [])
            if cols:
                self.line(f"path_id = {repr(path_id)}")
                self.line(f"cols = {_repr_val(cols)}")
                self.line('col_defs = [{"name": c.get("field", c.get("name", "")), "label": c.get("name", c.get("field", "")), "field": c.get("field", c.get("name", ""))} for c in cols]')
                self.line("rows = state.get(path_id, [])")
                self.line('ui.table(columns=col_defs, rows=rows).classes("w-full")')
        else:
            self.line(f"# Widget {repr(widget_type)} (path_id={repr(path_id)}): kein Export-Mapping, Platzhalter")
            self.line(f"ui.label({repr(f'[{widget_type}]')}).classes(\"text-grey\")")

    def get_code(self) -> str:
        return "\n".join(self._lines)


def layout_to_python(layout: dict) -> str:
    """
    Erzeugt aus dem Layout-Dict Python-Quelltext, der dieselbe UI mit NiceGUI baut.

    Die generierte Funktion hat die Signatur:
      build_ui(ui, state, callbacks, *, title=None)

    Nutzung in der Ziel-App (ohne Renderer, ohne layout.json):
      from nicegui import ui
      from deployed_ui import build_ui
      state = {}; callbacks = {}
      build_ui(ui, state, callbacks, title="Meine App")
      ui.run()
    """
    w = CodeWriter()
    w.line('"""Generated from layout.json by app_builder.code_export. Do not edit by hand."""')
    w.line("from __future__ import annotations")
    w.line("")
    w.line("")
    w.line("def _on_value_change(state, callbacks, path_id, value):")
    w._level += 1
    w.line("state[path_id] = value")
    w.line("if path_id in callbacks:")
    w._level += 1
    w.line("callbacks[path_id](value)")
    w._level -= 1
    w._level -= 1
    w.line("")
    w.line("")
    w.line("def build_ui(ui, state, callbacks, *, title=None):")
    w._level += 1
    w.line('if title:')
    w._level += 1
    w.line("ui.label(title).classes(\"text-h4\")")
    w._level -= 1
    w.line("")
    dashboard = layout.get("dashboard", {})
    children = dashboard.get("children", [])
    parent_path = ""
    w.emit_children(children, parent_path)
    w._level -= 1
    return w.get_code()


def main() -> None:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Export layout.json to static Python (NiceGUI) for deployment.")
    parser.add_argument("layout", type=Path, help="Path to layout.json")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output .py file (default: stdout)")
    args = parser.parse_args()
    layout_path = args.layout
    if not layout_path.exists():
        raise SystemExit(f"Layout file not found: {layout_path}")
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    code = layout_to_python(layout)
    if args.output:
        args.output.write_text(code, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(code)


if __name__ == "__main__":
    main()
