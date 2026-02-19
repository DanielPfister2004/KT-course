"""
Grid-Editor (Stufe 2): 2D-Zellen-Matrix, Zelle = Widget oder Container (hierarchisch).
Auswahl per Klick/Cursor, Palette (Widgets + Container), Property-Panel, Kinder verwalten.
Layout = layout.json; Live-Preview mit gleicher Engine wie development_app.

Root vs. Child / Layout-Modell:
- Root-Ebene: Im Editor state["cells"] (2D), state["rows"]/["cols"], state["selected_cell"] (r,c).
  Export (grid_to_layout): Pro Zeile ein Container layout_type "rows_columns", children = Zelleninhalt.
  Import (layout_to_grid): Nur layouts mit dashboard.children = nur rows_columns-Container (eine Zeile = ein Container).
  → Root ist fest als „Grid über rows_columns“ (keine Auswahl anderer Root-Layouts).
- Child-Container (in einer Zelle): Können layout_type "grid", "rows_columns", "expansion", etc. haben.
  Grid: ng["children"] (flach), ng["columns"]; Editor zeigt 2D-Grid, Platzieren = Zelle ersetzen oder anhängen.
  rows_columns: rc["children"] (flach); Editor zeigt 2D mit ROWS_COLS_EDITOR_COLUMNS Spalten; Platzieren = Zelle ersetzen oder anhängen.
  Platzieren in markierter Zelle = Inhalt dieser Zelle ersetzen (wie Root); nur der letzte „—“-Slot fügt neu ein.
"""
from __future__ import annotations

import copy
import html
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Grid-Editor eine Ebene höher (lab_suite/grid_editor) – parent = lab_suite
_lab_suite_root = Path(__file__).resolve().parent.parent
if str(_lab_suite_root) not in sys.path:
    sys.path.insert(0, str(_lab_suite_root))

from nicegui import ui

from app_builder import (
    build_ui_from_layout,
    collect_callback_names,
    collect_state_entries,
)
from .grid_model import (
    CONTAINER_LAYOUT_TYPES_IN_CELL,
    clamp_selection,
    default_grid_state,
    delete_cell,
    delete_column,
    delete_row,
    get_cell_children,
    grid_swap_cells,
    grid_to_layout,
    insert_cell,
    insert_column,
    insert_row,
    is_container,
    is_container_or_group,
    is_group,
    is_widget,
    layout_to_grid,
    next_container_id,
    next_widget_id,
    resize_grid,
)
from app_builder.layout_model import CONTAINER_DEFAULTS, WIDGET_DEFAULTS, get_prop_editor_specs
from app_creator import create_app_from_template
from app_creator.sync import diff_template_lab, sync_lab_to_template

# Ziel-Apps = Unterordner von lab_suite/labs (development_app, geklonte Apps, …)
LABS_DIR = _lab_suite_root / "labs"
TEMPLATES_DIR = _lab_suite_root / "templates"
_CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
_DEFAULT_TARGET_APP = "development_app"


def _normalize_loaded_cells(cells: list) -> None:
    """Nach Load: Props bereinigen ([value, event] -> value), fehlende Default-Props (z. B. render_markdown, font) ergänzen."""
    def coerce_value(v):
        if isinstance(v, list) and len(v) > 0:
            first = v[0]
            if isinstance(first, (bool, int, float, str)) and first is not None:
                return first
        return v

    def normalize_node(node: dict) -> None:
        if node.get("type") == "widget":
            props = node.setdefault("props", {})
            wt = node.get("widget_type", "")
            defaults = (WIDGET_DEFAULTS.get(wt) or {}).get("props") or {}
            for key, default in defaults.items():
                if key not in props:
                    props[key] = copy.deepcopy(default)
            for key in list(props.keys()):
                props[key] = coerce_value(props[key])
            if wt == "markdown":
                f = props.get("font")
                if isinstance(f, str):
                    f = f.strip().lower()
                else:
                    f = "default"
                if f not in ("default", "monospace"):
                    f = "default"
                props["font"] = f
        for ch in node.get("children") or []:
            if isinstance(ch, dict):
                normalize_node(ch)

    for row in cells:
        for cell in row:
            if isinstance(cell, dict):
                normalize_node(cell)


def _list_app_folders() -> list[str]:
    """Ordner unter labs/, die als Ziel-App nutzbar sind (Verzeichnisse, keine versteckten)."""
    if not LABS_DIR.exists():
        return []
    return sorted(
        p.name for p in LABS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )


def _load_target_app_config() -> str:
    """Gelesene Ziel-App aus config.json; sonst Default, falls in Liste."""
    apps = _list_app_folders()
    if not apps:
        return _DEFAULT_TARGET_APP
    try:
        if _CONFIG_PATH.exists():
            data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            name = (data.get("target_app") or "").strip()
            if name and name in apps:
                return name
    except Exception:
        pass
    return _DEFAULT_TARGET_APP if _DEFAULT_TARGET_APP in apps else apps[0]


def _save_target_app_config(target_app: str) -> None:
    """Gewählte Ziel-App in config.json speichern (für nächsten Aufruf)."""
    try:
        _CONFIG_PATH.write_text(
            json.dumps({"target_app": target_app}, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def _user_module_for_app(app_dir: Path) -> str:
    """assignments.user_callbacks wenn assignments/user_callbacks.py existiert, sonst user_callbacks."""
    if (app_dir / "assignments" / "user_callbacks.py").exists():
        return "assignments.user_callbacks"
    return "user_callbacks"


def _parse_list_or_keep(value) -> list | str:
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


def _to_num(value, default: int | float, is_int: bool = False) -> int | float:
    """Coerce value to int or float so Quasar sliders/numbers never get strings (avoids toFixed error)."""
    if value is None or value == "":
        return int(default) if is_int else float(default)
    if isinstance(value, (int, float)):
        return int(value) if is_int else float(value)
    try:
        n = float(value)
        return int(n) if is_int else n
    except (TypeError, ValueError):
        return int(default) if is_int else float(default)


def _safe_int_for_ui(value, default: int) -> int:
    """Immer int für NiceGUI Number .value (vermeidet TypeError in sanitize)."""
    return int(float(_to_num(value, default, is_int=True)))


# Leerer Slot in verschachtelten Grids (Renderer lässt Platzhalter aus)
PLACEHOLDER_NODE: dict = {"type": "placeholder"}
# Zeilenanzahl in der rows_columns-Editor-Ansicht; "Insert row" fügt so viele Slots ein
ROWS_COLS_EDITOR_COLUMNS = 4


def _cell_label(cell) -> str:
    if cell is None:
        return "—"
    if isinstance(cell, dict) and cell.get("type") == "widget":
        return cell.get("widget_type", "?") or cell.get("id", "?")
    if isinstance(cell, dict) and cell.get("type") == "container":
        lt = cell.get("layout_type", "?")
        children = cell.get("children") or []
        n = len(children)
        return f"[{lt}]" if n == 0 else f"[{lt}: {n}]"
    if isinstance(cell, dict) and cell.get("type") == "group":
        children = cell.get("children") or []
        n = len(children)
        return "[group]" if n == 0 else f"[group: {n}]"
    if isinstance(cell, dict) and cell.get("type") == "placeholder":
        return "—"
    return "?"


def main() -> None:
    state = default_grid_state(rows=4, cols=6)
    state["editing_path"] = []  # Drill-Down: Liste von Kinder-Indizes; [] = Zelle selbst bearbeiten
    state["selected_nested_index"] = 0  # Bei Grid-Container: ausgewählter Zellen-Index (0..len(children))
    grid_container: list = []
    rows_cols_ref: list = []  # [rows_input, cols_input] for syncing after insert/delete/resize
    _last_disable_rc: list = [None]  # nur .props(disable=...) setzen wenn sich geändert (Vue beforeUnmount-Fehler vermeiden)
    props_container: list = []
    refresh_props_timer: list = []  # [timer | None] zum Abbrechen bei erneutem refresh_props
    preview_container: list = []
    copied_props_ref: list = []
    target_app_select_ref: list = []  # [ui.select] für gewählte Ziel-App (labs/<name>)

    def get_state():
        return state

    def get_selected() -> tuple[int, int]:
        return state["selected_cell"]

    def set_selected(row: int, col: int) -> None:
        r, c = state["rows"], state["cols"]
        state["selected_cell"] = (max(0, min(row, r - 1)), max(0, min(col, c - 1))) if r and c else (0, 0)
        state["editing_path"] = []
        state["selected_nested_index"] = 0
        refresh_grid()
        refresh_props()

    def get_editing_container(cell: dict | None, path: list[int]) -> dict | None:
        """Liefert den Container, der aktuell bearbeitet wird (Zelle oder Kind-Container)."""
        if cell is None or not is_container_or_group(cell):
            return cell
        node = cell
        for i in path:
            children = node.get("children") or []
            if i < 0 or i >= len(children):
                return node
            node = children[i]
        return node if is_container_or_group(node) or is_widget(node) else cell

    def get_editing_container_for_add(cell: dict | None, path: list[int]) -> dict | None:
        """Wie get_editing_container, aber gibt immer einen Container/Group zurück (für Add child)."""
        node = get_editing_container(cell, path)
        return node if node and is_container_or_group(node) else cell

    def _get_nested_grid_container() -> dict | None:
        """Wenn aktuell ein Grid-Container bearbeitet wird, diesen zurückgeben; sonst None."""
        path = state.get("editing_path") or []
        if not path:
            return None
        r, c = state["selected_cell"]
        cells = state["cells"]
        if r >= len(cells) or c >= len(cells[r]):
            return None
        cell = cells[r][c]
        current = get_editing_container(cell, path)
        if current and current.get("type") == "container" and current.get("layout_type") == "grid":
            return current
        return None

    def _nested_grid_rows_cols(ng: dict) -> tuple[int, int]:
        """(rows, cols) für einen Grid-Container."""
        cols = max(1, int(_to_num(ng.get("columns"), 2, is_int=True)))
        children = ng.get("children") or []
        n = len(children)
        rows_explicit = ng.get("rows")
        rows = max(1, int(_to_num(rows_explicit, 1, is_int=True))) if rows_explicit is not None else max(1, (n + 1 + cols - 1) // cols)
        return rows, cols

    def _is_editing_nested_non_grid() -> bool:
        """True, wenn ein verschachtelter Container bearbeitet wird, der kein Grid ist (z. B. rows_columns). Dann dürfen Rows/Cols nicht das Root-Grid ändern."""
        return _get_editing_nested_non_grid_container() is not None

    def _get_editing_nested_non_grid_container() -> dict | None:
        """Wenn aktuell ein verschachtelter Container bearbeitet wird, der kein Grid ist (z. B. rows_columns), diesen zurückgeben; sonst None."""
        path = state.get("editing_path") or []
        if not path:
            return None
        r, c = state["selected_cell"]
        cells = state["cells"]
        if r >= len(cells) or c >= len(cells[r]):
            return None
        cell = cells[r][c]
        current = get_editing_container(cell, path)
        if not current or current.get("type") != "container":
            return None
        return current if current.get("layout_type") != "grid" else None

    def _sync_rows_cols_inputs() -> None:
        if len(rows_cols_ref) < 2:
            return
        ng = _get_nested_grid_container()
        disable_rc = _is_editing_nested_non_grid()
        if ng is not None:
            children = ng.get("children") or []
            cols = max(1, _safe_int_for_ui(ng.get("columns"), 2))
            n = len(children)
            rows_val = ng.get("rows")
            if rows_val is None:
                rows_val = max(1, (n + 1 + cols - 1) // cols)
            rows_cols_ref[0].value = str(_safe_int_for_ui(rows_val, 1))
            rows_cols_ref[1].value = str(_safe_int_for_ui(cols, 2))
        else:
            rows_cols_ref[0].value = str(_safe_int_for_ui(state.get("rows"), 4))
            rows_cols_ref[1].value = str(_safe_int_for_ui(state.get("cols"), 6))
        # Rows/Cols nur für Root oder Grid-Container – bei rows_columns etc. deaktivieren; nur bei Änderung setzen (Vue-Fehler vermeiden)
        if _last_disable_rc[0] is not disable_rc and len(rows_cols_ref) >= 2:
            _last_disable_rc[0] = disable_rc
            try:
                if hasattr(rows_cols_ref[0], "props"):
                    rows_cols_ref[0].props(disable=disable_rc)
                if hasattr(rows_cols_ref[1], "props"):
                    rows_cols_ref[1].props(disable=disable_rc)
            except Exception:
                pass

    def apply_resize(new_rows: int, new_cols: int) -> None:
        """Grid auf new_rows × new_cols setzen (Root oder verschachtelter Grid-Container). Nicht anwenden, wenn rows_columns o. ä. bearbeitet wird."""
        if _is_editing_nested_non_grid():
            _sync_rows_cols_inputs()
            return
        new_rows = max(1, _to_num(new_rows, 4, is_int=True))
        new_cols = max(1, _to_num(new_cols, 6, is_int=True))
        ng = _get_nested_grid_container()
        if ng is not None:
            ng["rows"] = new_rows
            ng["columns"] = new_cols
            _sync_rows_cols_inputs()
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        state["rows"], state["cols"] = resize_grid(state["cells"], new_rows, new_cols)
        state["selected_cell"] = clamp_selection(state["selected_cell"], state["rows"], state["cols"])
        _sync_rows_cols_inputs()
        refresh_grid()
        refresh_props()
        refresh_preview()

    def do_insert_row() -> None:
        rc = _get_editing_nested_non_grid_container()
        if rc is not None:
            children = rc.setdefault("children", [])
            sel = state.get("selected_nested_index", 0)
            cols_rc = ROWS_COLS_EDITOR_COLUMNS
            if _do_edit_on_flat_grid(children, cols_rc, sel, "insert_row"):
                state["selected_nested_index"] = min(sel + cols_rc, len(children) - 1) if children else 0
                refresh_grid()
                refresh_props()
                refresh_preview()
            return
        ng = _get_nested_grid_container()
        if ng is not None:
            children = ng.setdefault("children", [])
            rows, cols = _nested_grid_rows_cols(ng)
            sel = state.get("selected_nested_index", 0)
            sel_row = sel // cols
            idx = min(sel_row * cols, len(children))
            for _ in range(cols):
                children.insert(idx, copy.deepcopy(PLACEHOLDER_NODE))
            state["selected_nested_index"] = min(sel + cols, len(children) - 1) if children else 0
            _sync_rows_cols_inputs()
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        r, c = state["selected_cell"]
        state["rows"], state["cols"] = insert_row(state["cells"], state["rows"], state["cols"], r)
        state["selected_cell"] = clamp_selection((r, c), state["rows"], state["cols"])
        _sync_rows_cols_inputs()
        refresh_grid()
        refresh_props()
        refresh_preview()

    def _do_edit_on_flat_grid(children: list, cols: int, sel: int, op: str) -> bool:
        """Gemeinsame Edit-Logik für flache children-Liste (rows_columns + ggf. nested grid).
        cols = Spaltenanzahl für Zeilen/Spalten-Berechnung; op = insert_cell|insert_row|insert_column|delete_cell|delete_row|delete_column.
        Wird für rows_columns (cols=ROWS_COLS_EDITOR_COLUMNS) genutzt; nested grid hat eigene Zweige (ng['columns'])."""
        n = len(children)
        rows = max(1, (n + 1 + cols - 1) // cols)
        if op == "insert_cell":
            idx = min(sel, n)
            children.insert(idx, copy.deepcopy(PLACEHOLDER_NODE))
            return True
        if op == "insert_row":
            sel_row = sel // cols
            idx = min(sel_row * cols, n)
            for _ in range(cols):
                children.insert(idx, copy.deepcopy(PLACEHOLDER_NODE))
            return True
        if op == "insert_column":
            sel_col = sel % cols
            for r in range(rows - 1, -1, -1):
                idx = r * cols + sel_col
                if idx <= len(children):
                    children.insert(idx, copy.deepcopy(PLACEHOLDER_NODE))
            return True
        if op == "delete_cell":
            if sel < n:
                children.pop(sel)
            return True
        if op == "delete_row":
            if rows <= 1:
                return False
            sel_row = sel // cols
            start = sel_row * cols
            for _ in range(cols):
                if start < len(children):
                    children.pop(start)
            return True
        if op == "delete_column":
            if cols <= 1:
                return False
            sel_col = sel % cols
            for r in range(rows - 1, -1, -1):
                idx = r * cols + sel_col
                if idx < len(children):
                    children.pop(idx)
            return True
        return False

    def do_insert_cell() -> None:
        rc = _get_editing_nested_non_grid_container()
        if rc is not None:
            children = rc.setdefault("children", [])
            sel = state.get("selected_nested_index", 0)
            cols_rc = ROWS_COLS_EDITOR_COLUMNS
            if _do_edit_on_flat_grid(children, cols_rc, sel, "insert_cell"):
                state["selected_nested_index"] = min(sel + 1, len(children) - 1) if children else 0
                refresh_grid()
                refresh_props()
                refresh_preview()
            return
        ng = _get_nested_grid_container()
        if ng is not None:
            children = ng.setdefault("children", [])
            sel = state.get("selected_nested_index", 0)
            idx = min(sel, len(children))
            children.insert(idx, copy.deepcopy(PLACEHOLDER_NODE))
            state["selected_nested_index"] = min(sel + 1, len(children) - 1) if children else 0
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        r, c = state["selected_cell"]
        state["rows"], state["cols"] = insert_cell(state["cells"], state["rows"], state["cols"], r, c)
        state["selected_cell"] = clamp_selection((r, c), state["rows"], state["cols"])
        _sync_rows_cols_inputs()
        refresh_grid()
        refresh_props()
        refresh_preview()

    def do_insert_column() -> None:
        rc = _get_editing_nested_non_grid_container()
        if rc is not None:
            children = rc.setdefault("children", [])
            sel = state.get("selected_nested_index", 0)
            cols_rc = ROWS_COLS_EDITOR_COLUMNS
            if _do_edit_on_flat_grid(children, cols_rc, sel, "insert_column"):
                state["selected_nested_index"] = min(sel + 1, len(children) - 1) if children else 0
                refresh_grid()
                refresh_props()
                refresh_preview()
            return
        ng = _get_nested_grid_container()
        if ng is not None:
            children = ng.setdefault("children", [])
            rows, cols = _nested_grid_rows_cols(ng)
            sel = state.get("selected_nested_index", 0)
            sel_col = sel % cols
            for r in range(rows - 1, -1, -1):
                idx = r * cols + sel_col
                if idx <= len(children):
                    children.insert(idx, copy.deepcopy(PLACEHOLDER_NODE))
            state["selected_nested_index"] = min(sel + 1, (rows * (cols + 1)) - 1) if rows else 0
            ng["columns"] = cols + 1
            _sync_rows_cols_inputs()
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        r, c = state["selected_cell"]
        state["rows"], state["cols"] = insert_column(state["cells"], state["rows"], state["cols"], c)
        state["selected_cell"] = clamp_selection((r, c + 1), state["rows"], state["cols"])
        _sync_rows_cols_inputs()
        refresh_grid()
        refresh_props()
        refresh_preview()

    def do_delete_row() -> None:
        rc = _get_editing_nested_non_grid_container()
        if rc is not None:
            children = rc.setdefault("children", [])
            sel = state.get("selected_nested_index", 0)
            cols_rc = ROWS_COLS_EDITOR_COLUMNS
            if not _do_edit_on_flat_grid(children, cols_rc, sel, "delete_row"):
                ui.notify("Mindestens eine Zeile erforderlich.", type="warning")
                return
            rows_rc = max(1, (len(children) + 1 + cols_rc - 1) // cols_rc)
            state["selected_nested_index"] = max(0, min(sel - cols_rc, (rows_rc - 1) * cols_rc - 1)) if cols_rc else 0
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        ng = _get_nested_grid_container()
        if ng is not None:
            children = ng.setdefault("children", [])
            rows, cols = _nested_grid_rows_cols(ng)
            if rows <= 1:
                ui.notify("Mindestens eine Zeile erforderlich.", type="warning")
                return
            sel = state.get("selected_nested_index", 0)
            sel_row = sel // cols
            start = sel_row * cols
            for _ in range(cols):
                if start < len(children):
                    children.pop(start)
            state["selected_nested_index"] = max(0, min(sel - cols, (rows - 1) * cols - 1)) if cols else 0
            _sync_rows_cols_inputs()
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        if state["rows"] <= 1:
            ui.notify("Mindestens eine Zeile erforderlich.", type="warning")
            return
        r, c = state["selected_cell"]
        state["rows"], state["cols"] = delete_row(state["cells"], state["rows"], state["cols"], r)
        state["selected_cell"] = clamp_selection((min(r, state["rows"] - 1), c), state["rows"], state["cols"])
        _sync_rows_cols_inputs()
        refresh_grid()
        refresh_props()
        refresh_preview()

    def do_delete_column() -> None:
        rc = _get_editing_nested_non_grid_container()
        if rc is not None:
            children = rc.setdefault("children", [])
            sel = state.get("selected_nested_index", 0)
            cols_rc = ROWS_COLS_EDITOR_COLUMNS
            if not _do_edit_on_flat_grid(children, cols_rc, sel, "delete_column"):
                ui.notify("Mindestens eine Spalte erforderlich.", type="warning")
                return
            rows_rc = max(1, (len(children) + 1 + cols_rc - 1) // cols_rc)
            state["selected_nested_index"] = max(0, min(sel - 1, rows_rc * (cols_rc - 1) - 1)) if rows_rc and cols_rc > 1 else 0
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        ng = _get_nested_grid_container()
        if ng is not None:
            children = ng.setdefault("children", [])
            rows, cols = _nested_grid_rows_cols(ng)
            if cols <= 1:
                ui.notify("Mindestens eine Spalte erforderlich.", type="warning")
                return
            sel = state.get("selected_nested_index", 0)
            sel_col = sel % cols
            for r in range(rows - 1, -1, -1):
                idx = r * cols + sel_col
                if idx < len(children):
                    children.pop(idx)
            ng["columns"] = cols - 1
            state["selected_nested_index"] = max(0, min(sel - 1, (rows * (cols - 1)) - 1)) if rows else 0
            _sync_rows_cols_inputs()
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        if state["cols"] <= 1:
            ui.notify("Mindestens eine Spalte erforderlich.", type="warning")
            return
        r, c = state["selected_cell"]
        state["rows"], state["cols"] = delete_column(state["cells"], state["rows"], state["cols"], c)
        state["selected_cell"] = clamp_selection((r, min(c, state["cols"] - 1)), state["rows"], state["cols"])
        _sync_rows_cols_inputs()
        refresh_grid()
        refresh_props()
        refresh_preview()

    def do_delete_cell() -> None:
        """Löscht die markierte Zelle, Zellen rechts in der Zeile rücken nach links."""
        rc = _get_editing_nested_non_grid_container()
        if rc is not None:
            children = rc.setdefault("children", [])
            sel = state.get("selected_nested_index", 0)
            cols_rc = ROWS_COLS_EDITOR_COLUMNS
            if cols_rc <= 1 and len(children) <= 1:
                ui.notify("Mindestens eine Zelle erforderlich.", type="warning")
                return
            _do_edit_on_flat_grid(children, cols_rc, sel, "delete_cell")
            state["selected_nested_index"] = max(0, min(sel, len(children) - 1)) if children else 0
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        ng = _get_nested_grid_container()
        if ng is not None:
            children = ng.setdefault("children", [])
            rows, cols = _nested_grid_rows_cols(ng)
            if cols <= 1 and len(children) <= 1:
                ui.notify("Mindestens eine Zelle erforderlich.", type="warning")
                return
            sel = state.get("selected_nested_index", 0)
            if sel < len(children):
                children.pop(sel)
            state["selected_nested_index"] = max(0, min(sel, len(children) - 1)) if children else 0
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        if state["cols"] <= 1:
            ui.notify("Mindestens eine Spalte erforderlich.", type="warning")
            return
        r, c = state["selected_cell"]
        state["rows"], state["cols"] = delete_cell(state["cells"], state["rows"], state["cols"], r, c)
        state["selected_cell"] = clamp_selection((r, min(c, state["cols"] - 1)), state["rows"], state["cols"])
        _sync_rows_cols_inputs()
        refresh_grid()
        refresh_props()
        refresh_preview()

    def set_nested_selection(index: int) -> None:
        """Auswahl im verschachtelten Grid (bei Edit eines Grid-Containers)."""
        state["selected_nested_index"] = index
        refresh_grid()
        refresh_props()

    def refresh_grid() -> None:
        if not grid_container:
            return
        cont = grid_container[0]
        cont.clear()
        cells = state["cells"]
        path = state.get("editing_path") or []
        r, c = state["selected_cell"]
        # Verschachtelter Container: Grid oder rows_columns
        if path and r < len(cells) and c < len(cells[r]):
            cell = cells[r][c]
            current = get_editing_container(cell, path)
            if current and current.get("type") == "container":
                lt = current.get("layout_type", "")
                if lt == "grid":
                    cols = max(1, int(current.get("columns") or 2))
                    children = current.get("children") or []
                    n = len(children)
                    rows_explicit = current.get("rows")
                    rows = max(1, int(rows_explicit)) if rows_explicit is not None else max(1, (n + 1 + cols - 1) // cols)
                    sel_idx = state.get("selected_nested_index", 0)
                    with cont:
                        ui.label(f"Nested grid: {current.get('id', 'grid')} — Zelle wählen, dann aus Palette platzieren").classes(
                            "text-caption text-weight-medium mb-1"
                        )
                        for row in range(rows):
                            with ui.row().classes("gap-1 flex-nowrap shrink-0"):
                                for col in range(cols):
                                    idx = row * cols + col
                                    child = children[idx] if idx < len(children) else None
                                    is_selected = sel_idx == idx
                                    style = (
                                        "min-width: 72px; width: 72px; min-height: 48px; flex-shrink: 0; "
                                        "border: 1px solid #ccc; border-radius: 4px; display: flex; "
                                        "align-items: center; justify-content: center; cursor: pointer; font-size: 0.85rem;"
                                    )
                                    if is_selected:
                                        style += " background: rgba(0,0,255,.2); border-color: #3366ff;"
                                    with ui.element("div").classes("flex items-center justify-center").style(style).on(
                                        "click", lambda idx=idx: set_nested_selection(idx)
                                    ):
                                        ui.label(_cell_label(child) if child else "—")
                    return
                if lt == "rows_columns":
                    children = current.get("children") or []
                    sel_idx = state.get("selected_nested_index", 0)
                    cols_rc = current.get("columns") or ROWS_COLS_EDITOR_COLUMNS
                    current.setdefault("columns", ROWS_COLS_EDITOR_COLUMNS)
                    num_slots = len(children) + 1
                    rows_rc = max(1, (num_slots + cols_rc - 1) // cols_rc)
                    current["rows"] = rows_rc
                    with cont:
                        ui.label(f"rows_columns: {current.get('id', '')} — Slot wählen, Insert row = neue Zeile").classes(
                            "text-caption text-weight-medium mb-1"
                        )
                        for row in range(rows_rc):
                            with ui.row().classes("gap-1 flex-nowrap shrink-0"):
                                for col in range(cols_rc):
                                    idx = row * cols_rc + col
                                    child = children[idx] if idx < len(children) else None
                                    is_selected = sel_idx == idx
                                    style = (
                                        "min-width: 72px; width: 72px; min-height: 48px; flex-shrink: 0; "
                                        "border: 1px solid #ccc; border-radius: 4px; display: flex; "
                                        "align-items: center; justify-content: center; cursor: pointer; font-size: 0.85rem;"
                                    )
                                    if is_selected:
                                        style += " background: rgba(0,0,255,.2); border-color: #3366ff;"
                                    with ui.element("div").classes("flex items-center justify-center").style(style).on(
                                        "click", lambda idx=idx: set_nested_selection(idx)
                                    ):
                                        ui.label(_cell_label(child) if child else "—")
                    return
        # Root-Grid
        rows, cols = state["rows"], state["cols"]
        sel = state["selected_cell"]
        with cont:
            for r in range(rows):
                with ui.row().classes("gap-1 flex-nowrap shrink-0"):
                    for c in range(cols):
                        cell = cells[r][c] if r < len(cells) and c < len(cells[r]) else None
                        is_selected = (r, c) == sel
                        style = (
                            "min-width: 72px; width: 72px; min-height: 48px; flex-shrink: 0; "
                            "border: 1px solid #ccc; border-radius: 4px; display: flex; "
                            "align-items: center; justify-content: center; cursor: pointer; font-size: 0.85rem;"
                        )
                        if is_selected:
                            style += " background: rgba(0,0,255,.2); border-color: #3366ff;"
                        with ui.element("div").classes("flex items-center justify-center").style(style).on(
                            "click", lambda r=r, c=c: set_selected(r, c)
                        ):
                            ui.label(_cell_label(cell))

    def _add_child_to_cell(kind: str, is_widget: bool) -> None:
        """Add widget or container. Root = Zelle ersetzen (cells[r][c]=…). Grid/rows_columns = markierte Zelle ersetzen (wie Root), nur bei „—"-Slot anhängen."""
        r, c = state["selected_cell"]
        cells = state["cells"]
        if r >= len(cells) or c >= len(cells[r]):
            return
        cell = cells[r][c]
        path = state.get("editing_path") or []
        current = get_editing_container_for_add(cell, path)
        if not current or not is_container_or_group(current):
            return
        current.setdefault("children", [])
        children = current["children"]
        # Grid/rows_columns: markierte Zelle = Slot; wenn Slot belegt (Index < len) → ersetzen (wie Root), sonst anhängen
        replace_slot = False
        insert_index = len(children)
        if path and current.get("type") == "container" and current.get("layout_type") in ("grid", "rows_columns"):
            idx = min(state.get("selected_nested_index", 0), len(children))
            if idx < len(children):
                replace_slot = True
                insert_index = idx
            else:
                insert_index = len(children)
        if is_widget and kind in WIDGET_DEFAULTS:
            child = copy.deepcopy(WIDGET_DEFAULTS[kind])
            child["id"] = next_widget_id(cells, "widget")
            props = child.setdefault("props", {})
            if "label" in props and not (props.get("label") or "").strip():
                props["label"] = kind.replace("_", " ").title()
            if "text" in props and not (props.get("text") or "").strip():
                props["text"] = kind.replace("_", " ").title()
            if replace_slot:
                children[insert_index] = child
            else:
                children.insert(insert_index, child)
        elif kind in CONTAINER_DEFAULTS:
            child = copy.deepcopy(CONTAINER_DEFAULTS[kind])
            child["id"] = next_container_id(cells, kind if kind != "group" else "group")
            if kind == "expansion":
                child["label"] = child.get("label") or "Aufklappen"
            if replace_slot:
                children[insert_index] = child
            else:
                children.insert(insert_index, child)
        refresh_grid()
        refresh_props()
        refresh_preview()

    def refresh_props() -> None:
        if not props_container:
            return
        if refresh_props_timer and refresh_props_timer[0] is not None:
            try:
                refresh_props_timer[0].cancel()
            except Exception:
                pass
            refresh_props_timer[0] = None
        cont = props_container[0]
        r, c = state["selected_cell"]
        cells = state["cells"]
        cell = cells[r][c] if r < len(cells) and c < len(cells[r]) else None

        def _build_props_content() -> None:
            if refresh_props_timer:
                refresh_props_timer[0] = None
            cont.clear()
            with cont:
                ui.label("Properties").classes("text-weight-medium")
                # Zeilen-Optionen (align_items) immer sichtbar, wenn eine Zelle der Zeile ausgewählt ist (Root-Grid)
                path = state.get("editing_path") or []
                if len(path) == 0:
                    row_index = state["selected_cell"][0]
                    state.setdefault("row_options", {})
                    row_opts = state["row_options"].setdefault(row_index, {})
                    align = (row_opts.get("align_items") or "center").strip().lower()
                    if align not in ("start", "center", "end", "stretch"):
                        align = "center"

                    VALID_ALIGN = ("start", "center", "end", "stretch")
                    ROW_ALIGN_OPTIONS = [
                        ("start", "Zeile: Oben (start)"),
                        ("center", "Zeile: Mitte (center)"),
                        ("end", "Zeile: Unten (end)"),
                        ("stretch", "Zeile: Strecken (stretch)"),
                    ]
                    def set_row_align(val: str, r: int = row_index) -> None:
                        v = (val or "center").strip().lower() if isinstance(val, str) else "center"
                        if v not in VALID_ALIGN:
                            v = "center"
                        state.setdefault("row_options", {})[r] = state["row_options"].get(r, {}) | {"align_items": v}
                        refresh_preview()

                    def _row_align_from_event(e) -> str:
                        # Bevorzugt: on_change liefert ValueChangeEventArguments mit bereits konvertiertem e.value ("start" etc.)
                        v = getattr(e, "value", None)
                        if v is not None and isinstance(v, str) and v in VALID_ALIGN:
                            return v
                        v = getattr(e, "args", None)
                        if isinstance(v, list) and len(v) > 0:
                            v = v[0]
                        if isinstance(v, dict):
                            v = v.get("value") if "value" in v else (v.get("key") or v.get("label"))
                        if isinstance(v, (int, float)):
                            idx = int(v)
                            if 0 <= idx < len(VALID_ALIGN):
                                return VALID_ALIGN[idx]
                        if isinstance(v, str):
                            v = v.strip().lower()
                            if v in VALID_ALIGN:
                                return v
                            if v.isdigit():
                                idx = int(v)
                                if 0 <= idx < len(VALID_ALIGN):
                                    return VALID_ALIGN[idx]
                            for key, label in ROW_ALIGN_OPTIONS:
                                if key in v or f"({key})" in v or label.lower() == v:
                                    return key
                        return "center"

                    ui.select(
                        {"start": "Zeile: Oben (start)", "center": "Zeile: Mitte (center)", "end": "Zeile: Unten (end)", "stretch": "Zeile: Strecken (stretch)"},
                        value=align,
                        label=f"Vertikale Ausrichtung (Zeile {row_index})",
                    ).classes("w-full").on("update:model-value", lambda e: set_row_align(_row_align_from_event(e)))
                    ui.separator()
                if cell is None:
                    ui.label("Cell empty — choose widget or container from palette").classes("text-grey")
                elif is_container_or_group(cell):
                    # Drill-Down: aktuell bearbeiteter Container (Zelle oder Kind)
                    path = state.get("editing_path") or []
                    current = get_editing_container(cell, path)
                    if path:
                        def go_back():
                            state["editing_path"] = path[:-1]
                            state["selected_nested_index"] = 0
                            _sync_rows_cols_inputs()
                            refresh_grid()
                            refresh_props()
                        with ui.row().classes("items-center gap-1 w-full"):
                            ui.button(icon="arrow_back", on_click=go_back).props("flat dense size=sm")
                            ui.label("← Back").classes("text-caption")
                    if current and is_container_or_group(current):
                        ui.label(f"id: {current.get('id', '')}").classes("text-caption")
                        if current.get("type") == "container":
                            ui.label(f"layout_type: {current.get('layout_type', '')}").classes("text-caption")
                            if current.get("layout_type") == "rows_columns":
                                align = (current.get("align_items") or "center").strip().lower()
                                if align not in ("start", "center", "end", "stretch"):
                                    align = "center"

                                def set_align(val, node=current):
                                    v = (val or "center").strip().lower() if isinstance(val, str) else "center"
                                    if v not in ("start", "center", "end", "stretch"):
                                        v = "center"
                                    node["align_items"] = v
                                    refresh_preview()

                                _nested_align_options = ("start", "center", "end", "stretch")
                                def _nested_align_from_event(e):
                                    v = getattr(e, "value", None)
                                    if v is not None and isinstance(v, str) and v in _nested_align_options:
                                        return v
                                    v = getattr(e, "args", None)
                                    if isinstance(v, list) and len(v) > 0:
                                        v = v[0]
                                    if isinstance(v, dict):
                                        v = v.get("value") if "value" in v else (v.get("key") or v.get("label"))
                                    if isinstance(v, (int, float)):
                                        idx = int(v)
                                        if 0 <= idx < len(_nested_align_options):
                                            return _nested_align_options[idx]
                                    if isinstance(v, str) and v in _nested_align_options:
                                        return v
                                    if isinstance(v, str) and v.isdigit():
                                        idx = int(v)
                                        if 0 <= idx < len(_nested_align_options):
                                            return _nested_align_options[idx]
                                    return "center"

                                ui.select(
                                    {"start": "Oben (start)", "center": "Mitte (center)", "end": "Unten (end)", "stretch": "Strecken (stretch)"},
                                    value=align,
                                    label="Vertikale Ausrichtung (Zeile)",
                                ).classes("w-full").on("update:model-value", lambda e: set_align(_nested_align_from_event(e)))
                        label_key = "label"
                        if label_key in current:
                            def set_label(val, node=current):
                                node["label"] = val
                                refresh_preview()
                            ui.input("Label", value=str(current.get("label", "") or "")).classes("w-full").props("dense").on(
                                "update:model-value", lambda e, n=current: set_label(e.args, n)
                            )
                        if not path:
                            ui.button("Remove container", on_click=delete_widget).props("flat dense color=negative size=sm")
                        else:
                            def remove_from_parent():
                                parent = get_editing_container(cell, path[:-1])
                                if parent and path:
                                    idx = path[-1]
                                    parent.setdefault("children", [])[:] = [c for j, c in enumerate(parent["children"]) if j != idx]
                                    state["editing_path"] = path[:-1]
                                    refresh_grid()
                                    refresh_props()
                                    refresh_preview()
                            ui.button("Remove from parent", on_click=remove_from_parent).props("flat dense color=orange size=sm")
                        children = get_cell_children(current)
                        ui.label(f"Children ({len(children)})").classes("text-weight-medium mt-2")
                        for i, ch in enumerate(children):
                            ch_label = (ch.get("widget_type") or ch.get("layout_type") or ch.get("type") or "?")
                            with ui.row().classes("items-center gap-1 w-full"):
                                ui.label(f"{i+1}. {ch_label}").classes("text-caption flex-grow")
                                if is_container_or_group(ch):
                                    def drill_into(idx):
                                        state.setdefault("editing_path", [])[:] = path + [idx]
                                        state["selected_nested_index"] = 0
                                        _sync_rows_cols_inputs()
                                        refresh_grid()
                                        refresh_props()
                                    ui.button("Edit", on_click=lambda idx=i: drill_into(idx)).props("flat dense size=sm")
                                def remove_child(idx, node=current):
                                    node.setdefault("children", [])[:] = [c for j, c in enumerate(node["children"]) if j != idx]
                                    refresh_grid()
                                    refresh_props()
                                    refresh_preview()
                                ui.button(icon="delete", on_click=lambda idx=i, node=current: remove_child(idx, node)).props("flat dense size=sm color=negative")
                        with ui.row().classes("gap-1 mt-2 flex-wrap"):
                            ui.label("Add child (widget):").classes("text-caption self-center")
                            for wkind in WIDGET_DEFAULTS:
                                ui.button(wkind.replace("_", " "), on_click=lambda k=wkind: _add_child_to_cell(k, is_widget=True)).props("flat dense size=sm")
                        ui.label("Or add container:").classes("text-caption mt-1")
                        with ui.row().classes("gap-1 flex-wrap"):
                            for ckind in CONTAINER_LAYOUT_TYPES_IN_CELL + ("group",):
                                if ckind in CONTAINER_DEFAULTS:
                                    ui.button(ckind.replace("_", " "), on_click=lambda k=ckind: _add_child_to_cell(k, is_widget=False)).props("flat dense size=sm")
                else:
                    widget_type = cell.get("widget_type", "")
                    ui.label(f"id: {cell.get('id', '')}").classes("text-caption")
                    ui.label(f"widget_type: {widget_type}").classes("text-caption")
                    with ui.row().classes("gap-1"):
                        ui.button("Copy properties", on_click=lambda: (
                            copied_props_ref.clear(),
                            copied_props_ref.append(copy.deepcopy(cell.get("props", {}))),
                            ui.notify("Properties copied.", type="positive"),
                        )).props("flat dense size=sm")
                        ui.button("Paste properties", on_click=lambda: (
                            (cell.setdefault("props", {}).update(copy.deepcopy(copied_props_ref[0])), refresh_preview(), refresh_props(), ui.notify("Pasted.", type="positive"))
                            if copied_props_ref
                            else ui.notify("Copy a widget's properties first.", type="warning")
                        )).props("flat dense size=sm")
                    ui.button("Remove widget", on_click=delete_widget).props("flat dense color=negative size=sm")

                    def set_prop(key: str, value) -> None:
                        cell.setdefault("props", {})[key] = value
                        refresh_preview()

                    props = cell.setdefault("props", {})
                    for spec in get_prop_editor_specs(widget_type):
                        key = spec["key"]
                        current = props.get(key, spec["default"])
                        label = spec.get("label", key)
                        prop_type = spec.get("type", "string")
                        if prop_type == "boolean":
                            def _set_bool_prop(e, k=key):
                                v = getattr(e, "args", None)
                                set_prop(k, v[0] if isinstance(v, list) and len(v) > 0 else v)
                            ui.checkbox(label, value=bool(current)).classes("w-full").on(
                                "update:model-value", _set_bool_prop
                            )
                        elif prop_type in ("integer", "number"):
                            num_min = spec.get("min")
                            num_max = spec.get("max")
                            default = spec["default"]
                            is_int = prop_type == "integer"
                            num_val = _to_num(current, default if isinstance(default, (int, float)) else (0 if is_int else 0.0), is_int)
                            props_str = "dense"
                            if num_min is not None:
                                props_str += f" min={num_min}"
                            if num_max is not None:
                                props_str += f" max={num_max}"
                            ui.number(label, value=num_val).classes("w-full").props(
                                props_str
                            ).on(
                                "update:model-value",
                                lambda e, k=key, d=default, i=is_int: set_prop(k, _to_num(e.args, d if isinstance(d, (int, float)) else (0 if i else 0.0), i)),
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
                                picker = ui.color_picker(
                                    on_pick=lambda e, k=key: (
                                        set_prop(k, _coerce_color(getattr(e, "color", None)) or ""),
                                        refresh_preview(),
                                    )
                                )
                                def _open_picker():
                                    picker.set_color(inp.value or "#000000")
                                    picker.open()
                                ui.button(icon="colorize", on_click=_open_picker).props("flat round dense")
                        elif spec.get("options"):
                            opts = list(spec["options"])
                            # NiceGUI select sends {value: index, label: str}; index must be mapped to opts[i]
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
                            ui.input(label, value=str(current) if current is not None else "").classes(
                                "w-full"
                            ).props("dense").on("update:model-value", lambda e, k=key: set_prop(k, e.args))

        # Kurz verzögern, damit Vue/NiceGUI den laufenden Zyklus abschließt. Timer im Props-Container erstellen (nicht im Grid-Zell-Kontext, der nach refresh_grid() gelöscht ist).
        with cont:
            t = ui.timer(0.03, _build_props_content, once=True)
        if not refresh_props_timer:
            refresh_props_timer.append(t)
        else:
            refresh_props_timer[0] = t

    def place_widget(kind: str) -> None:
        # Im verschachtelten Grid (Edit bei Grid-Container): Widget in Grid-Zelle platzieren
        path = state.get("editing_path") or []
        if path:
            r, c = state["selected_cell"]
            cells = state["cells"]
            if r < len(cells) and c < len(cells[r]):
                cell = cells[r][c]
                current = get_editing_container(cell, path)
                if current and current.get("type") == "container" and current.get("layout_type") in ("grid", "rows_columns"):
                    _add_child_to_cell(kind, is_widget=True)
                    return
        cells = state["cells"]
        r, c = state["selected_cell"]
        if kind not in WIDGET_DEFAULTS:
            return
        spec = copy.deepcopy(WIDGET_DEFAULTS[kind])
        spec["id"] = next_widget_id(cells, "widget")
        # Default label so widgets are recognizable in preview
        props = spec.setdefault("props", {})
        default_label = kind.replace("_", " ").title()
        if "label" in props and not (props.get("label") or "").strip():
            props["label"] = default_label
        if "text" in props and not (props.get("text") or "").strip():
            props["text"] = default_label
        while len(state["cells"]) <= r:
            state["cells"].append([None] * state["cols"])
        while len(state["cells"][r]) <= c:
            state["cells"][r].append(None)
        state["cells"][r][c] = spec
        refresh_grid()
        refresh_props()

    def place_container(kind: str) -> None:
        """Place a container (or group) in the active cell or in the nested grid cell."""
        path = state.get("editing_path") or []
        if path:
            r, c = state["selected_cell"]
            cells = state["cells"]
            if r < len(cells) and c < len(cells[r]):
                cell = cells[r][c]
                current = get_editing_container(cell, path)
                if current and current.get("type") == "container" and current.get("layout_type") in ("grid", "rows_columns"):
                    _add_child_to_cell(kind, is_widget=False)
                    return
        if kind not in CONTAINER_DEFAULTS:
            return
        cells = state["cells"]
        r, c = state["selected_cell"]
        spec = copy.deepcopy(CONTAINER_DEFAULTS[kind])
        prefix = "container" if kind != "group" else "group"
        spec["id"] = next_container_id(cells, kind if kind != "group" else "group")
        if kind == "group" and "label" in spec:
            spec["label"] = spec["label"] or f"Group {spec['id']}"
        if kind == "expansion" and "label" in spec:
            spec["label"] = spec["label"] or "Aufklappen"
        while len(state["cells"]) <= r:
            state["cells"].append([None] * state["cols"])
        while len(state["cells"][r]) <= c:
            state["cells"][r].append(None)
        state["cells"][r][c] = spec
        refresh_grid()
        refresh_props()
        refresh_preview()

    def delete_widget() -> None:
        """Remove widget or container in the active cell."""
        r, c = state["selected_cell"]
        cells = state["cells"]
        if r < len(cells) and c < len(cells[r]) and cells[r][c] is not None:
            state["cells"][r][c] = None
            refresh_grid()
            refresh_props()
            refresh_preview()
            ui.notify("Removed")

    def move_selected(direction: str) -> None:
        rc = _get_editing_nested_non_grid_container()
        if rc is not None:
            children = rc.get("children") or []
            cols_rc = ROWS_COLS_EDITOR_COLUMNS
            n = len(children) + 1
            total = max(1, (n + cols_rc - 1) // cols_rc) * cols_rc
            sel = state.get("selected_nested_index", 0)
            if direction == "up" and sel >= cols_rc:
                state["selected_nested_index"] = sel - cols_rc
            elif direction == "down" and sel + cols_rc < total:
                state["selected_nested_index"] = sel + cols_rc
            elif direction == "left" and sel % cols_rc > 0:
                state["selected_nested_index"] = sel - 1
            elif direction == "right" and sel % cols_rc < cols_rc - 1 and sel + 1 < total:
                state["selected_nested_index"] = sel + 1
            else:
                return
            refresh_grid()
            refresh_props()
            return
        ng = _get_nested_grid_container()
        if ng is not None:
            rows, cols = _nested_grid_rows_cols(ng)
            total = rows * cols
            sel = state.get("selected_nested_index", 0)
            if direction == "up" and sel >= cols:
                state["selected_nested_index"] = sel - cols
            elif direction == "down" and sel + cols < total:
                state["selected_nested_index"] = sel + cols
            elif direction == "left" and sel % cols > 0:
                state["selected_nested_index"] = sel - 1
            elif direction == "right" and sel % cols < cols - 1 and sel + 1 < total:
                state["selected_nested_index"] = sel + 1
            else:
                return
            refresh_grid()
            refresh_props()
            return
        r, c = get_selected()
        rows, cols = state["rows"], state["cols"]
        if direction == "up" and r > 0:
            set_selected(r - 1, c)
        elif direction == "down" and r < rows - 1:
            set_selected(r + 1, c)
        elif direction == "left" and c > 0:
            set_selected(r, c - 1)
        elif direction == "right" and c < cols - 1:
            set_selected(r, c + 1)

    def swap_with_neighbor(direction: str) -> None:
        rc = _get_editing_nested_non_grid_container()
        if rc is not None:
            children = rc.get("children") or []
            cols_rc = ROWS_COLS_EDITOR_COLUMNS
            sel = state.get("selected_nested_index", 0)
            dr = {"up": -cols_rc, "down": cols_rc}.get(direction, 0)
            dc = {"left": -1, "right": 1}.get(direction, 0)
            other = sel + dr + dc
            if 0 <= other < len(children) and 0 <= sel < len(children) and sel != other:
                children[sel], children[other] = children[other], children[sel]
                state["selected_nested_index"] = other
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        ng = _get_nested_grid_container()
        if ng is not None:
            children = ng.get("children") or []
            rows, cols = _nested_grid_rows_cols(ng)
            sel = state.get("selected_nested_index", 0)
            dr = {"up": -cols, "down": cols}.get(direction, 0)
            dc = {"left": -1, "right": 1}.get(direction, 0)
            other = sel + dr + dc
            if 0 <= other < len(children) and 0 <= sel < len(children) and sel != other:
                children[sel], children[other] = children[other], children[sel]
                state["selected_nested_index"] = other
            refresh_grid()
            refresh_props()
            refresh_preview()
            return
        if grid_swap_cells(
            state["cells"], state["rows"], state["cols"], state["selected_cell"], direction
        ):
            r, c = state["selected_cell"]
            dr = {"up": -1, "down": 1}.get(direction, 0)
            dc = {"left": -1, "right": 1}.get(direction, 0)
            state["selected_cell"] = (r + dr, c + dc)
            refresh_grid()
            refresh_props()

    def get_current_layout() -> dict:
        """Current grid as layout.json dict."""
        raw = state.get("row_options") or {}
        row_options = {int(k): v for k, v in raw.items() if isinstance(v, dict)}
        return grid_to_layout(
            state["cells"], state["rows"], state["cols"],
            row_options=row_options,
        )

    def refresh_preview() -> None:
        """Rebuild live preview from current grid (same engine as development_app)."""
        if not preview_container:
            return
        layout = get_current_layout()
        preview_state = collect_state_entries(layout)
        callbacks = {
            path_id: (lambda *a, **k: None)
            for path_id, *_ in collect_callback_names(layout)
        }
        cont = preview_container[0]
        layout_snapshot = copy.deepcopy(layout)
        cont.clear()
        # Kurz verzögern, damit Vue/NiceGUI vor dem Neubau fertig unmounten (vermindert "reading 'props' of undefined" in input.js beforeUnmount)
        def _rebuild_preview() -> None:
            with cont:
                build_ui_from_layout(
                    layout_snapshot,
                    preview_state,
                    callbacks,
                    title=None,
                )
        ui.timer(0.05, _rebuild_preview, once=True)

    def _get_target_app_dir():
        """Aktuell gewählte Ziel-App (labs/<name>). None wenn keine Auswahl."""
        if not target_app_select_ref:
            return None
        sel = target_app_select_ref[0]
        name = sel.value if hasattr(sel, "value") else None
        if not name or not _list_app_folders():
            return None
        if name not in _list_app_folders():
            return None
        return LABS_DIR / name

    def do_save_to_dev_app() -> None:
        target_dir = _get_target_app_dir()
        if not target_dir:
            ui.notify("Bitte zuerst eine Ziel-App auswählen.", type="warning")
            return
        path = target_dir / "layout.json"
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(get_current_layout(), f, indent=2, ensure_ascii=False)
            ui.notify(f"Gespeichert: {path.relative_to(_lab_suite_root)}")
        except Exception as ex:
            ui.notify(f"Error: {ex}", type="negative")

    def do_load_from_dev_app() -> None:
        target_dir = _get_target_app_dir()
        if not target_dir:
            ui.notify("Bitte zuerst eine Ziel-App auswählen.", type="warning")
            return
        path = target_dir / "layout.json"
        if not path.exists():
            ui.notify(f"Nicht gefunden: {path.relative_to(_lab_suite_root)}", type="warning")
            return
        try:
            with open(path, encoding="utf-8") as f:
                layout = json.load(f)
            grid_state = layout_to_grid(layout)
            if grid_state is None:
                ui.notify("Layout is not grid-compatible.", type="warning")
                return
            state["rows"] = int(grid_state["rows"]) if grid_state.get("rows") is not None else 4
            state["cols"] = int(grid_state["cols"]) if grid_state.get("cols") is not None else 6
            state["cells"] = grid_state["cells"]
            _normalize_loaded_cells(state["cells"])
            state["selected_cell"] = tuple(grid_state["selected_cell"]) if grid_state.get("selected_cell") else (0, 0)
            raw_row_opts = grid_state.get("row_options") or {}
            state["row_options"] = {int(k): v for k, v in raw_row_opts.items() if isinstance(v, dict)}
            state["editing_path"] = []
            state["selected_nested_index"] = 0
            _sync_rows_cols_inputs()
            refresh_grid()
            refresh_props()
            refresh_preview()
            ui.notify(f"Geladen: {path.relative_to(_lab_suite_root)}")
        except Exception as ex:
            ui.notify(f"Error: {ex}", type="negative")

    def do_skeleton() -> None:
        """Generate callback_skeleton.py, model_schema.py and user_callbacks.py (merge) from current grid layout."""
        target_dir = _get_target_app_dir()
        if not target_dir:
            ui.notify("Bitte zuerst eine Ziel-App auswählen.", type="warning")
            return
        lab_path = target_dir
        user_module = _user_module_for_app(lab_path)
        tmp = None
        try:
            layout = get_current_layout()
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as f:
                json.dump(layout, f, indent=2, ensure_ascii=False)
                tmp = f.name
            cmd = [
                sys.executable, "-m", "app_builder.skeleton", tmp,
                "--out", str(lab_path), "--model", "--user-module", user_module,
            ]
            if (lab_path / "_core").is_dir():
                cmd.extend(["--out-internal", "_core"])
            subprocess.run(
                cmd,
                cwd=str(_lab_suite_root),
                check=True,
                capture_output=True,
                text=True,
            )
            n_callbacks = len(collect_callback_names(layout))
            if n_callbacks == 0:
                ui.notify(
                    "Skeleton generated (callback_skeleton, model_schema, user_callbacks). "
                    "Current layout has no widgets with callbacks — add buttons, checkboxes, sliders, etc. to get callback stubs.",
                    type="warning",
                )
            else:
                ui.notify(
                    f"Skeleton generated: callback_skeleton.py, model_schema.py, user_callbacks.py ({n_callbacks} callbacks; merge preserves #begin user code)"
                )
        except subprocess.CalledProcessError as err:
            ui.notify(f"Error: {err.stderr or err}", type="negative")
        except Exception as ex:
            ui.notify(f"Error: {ex}", type="negative")
        finally:
            if tmp and os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    # ---- UI ----
    ui.label("Grid Editor (Stage 1)").classes("text-h4")

    # Linke Spalte: flex-1 = nutzt verfügbaren Platz; min-w-0 erlaubt Overflow/Scroll. Rechte Spalte: feste Breite, damit das Grid mehr Platz hat.
    with ui.row().classes("w-full gap-4 flex-nowrap"):
        with ui.column().classes("flex-1 min-w-0 gap-2"):
            ui.label("Palette — click to place in active cell").classes("text-weight-medium")
            with ui.row().classes("flex-wrap gap-1"):
                for kind in WIDGET_DEFAULTS:
                    ui.button(kind.replace("_", " "), on_click=lambda k=kind: place_widget(k)).props("flat dense size=sm")
            ui.label("Containers (hierarchical)").classes("text-weight-medium mt-2")
            with ui.row().classes("flex-wrap gap-1"):
                for kind in CONTAINER_LAYOUT_TYPES_IN_CELL:
                    if kind in CONTAINER_DEFAULTS:
                        ui.button(kind.replace("_", " "), on_click=lambda k=kind: place_container(k)).props("flat dense size=sm outline")
                if "group" in CONTAINER_DEFAULTS:
                    ui.button("Group", on_click=lambda: place_container("group")).props("flat dense size=sm outline")

            ui.label("Grid — click to select cell, cursor ↑/↓/←/→ to navigate").classes("text-weight-medium")
            with ui.row().classes("items-center gap-2"):
                ui.label("Rows:").classes("text-caption")
                def _on_rows_change(e):
                    other = _safe_int_for_ui(rows_cols_ref[1].value, 6) if len(rows_cols_ref) >= 2 else state["cols"]
                    apply_resize(_safe_int_for_ui(e.args, 4), _safe_int_for_ui(other, 6))
                def _on_cols_change(e):
                    other = _safe_int_for_ui(rows_cols_ref[0].value, 4) if len(rows_cols_ref) >= 2 else state["rows"]
                    apply_resize(_safe_int_for_ui(other, 4), _safe_int_for_ui(e.args, 6))
                # ui.input statt ui.number, um TypeError in NiceGUI number.py (sanitize str/float) zu vermeiden
                rows_input = ui.input(value=str(_safe_int_for_ui(state.get("rows"), 4))).props("dense type=number min=1 max=50").classes("w-20").on(
                    "update:model-value", _on_rows_change
                )
                ui.label("Cols:").classes("text-caption")
                cols_input = ui.input(value=str(_safe_int_for_ui(state.get("cols"), 6))).props("dense type=number min=1 max=50").classes("w-20").on(
                    "update:model-value", _on_cols_change
                )
                rows_cols_ref.extend([rows_input, cols_input])

            # Grid-Box dynamisch an Zellanzahl anpassen:
            # 1) overflow-x/y-auto: bei vielen Zellen Scrollbalken, keine Zeilenumbrüche
            # 2) flex-nowrap + shrink-0 + feste Zellbreite: Zellen werden nicht auseinandergezogen
            # 3) Linke Spalte flex-1: Box nutzt verfügbaren Platz; bei Bedarf mehr Platz durch kleinere Props-Spalte (w-96)
            grid_col = ui.column().classes("border rounded p-2 gap-1 overflow-x-auto overflow-y-auto")
            grid_container.append(grid_col)

            with ui.row().classes("gap-2 mt-2 flex-wrap"):
                ui.button("← Left", on_click=lambda: swap_with_neighbor("left")).props("flat dense size=sm")
                ui.button("→ Right", on_click=lambda: swap_with_neighbor("right")).props("flat dense size=sm")
                ui.button("↑ Up", on_click=lambda: swap_with_neighbor("up")).props("flat dense size=sm")
                ui.button("↓ Down", on_click=lambda: swap_with_neighbor("down")).props("flat dense size=sm")
                ui.space()
                ui.label("Insert/Delete:").classes("text-caption self-center")
                ui.button("Insert row", on_click=do_insert_row).props("flat dense size=sm")
                ui.button("Insert cell", on_click=do_insert_cell).props("flat dense size=sm")
                ui.button("Insert column", on_click=do_insert_column).props("flat dense size=sm")
                ui.button("Delete row", on_click=do_delete_row).props("flat dense size=sm color=orange")
                ui.button("Delete column", on_click=do_delete_column).props("flat dense size=sm color=orange")
                ui.button("Delete cell", on_click=do_delete_cell).props("flat dense size=sm color=orange")

        with ui.column().classes("w-96 min-w-80 gap-2 border rounded p-2 shrink-0"):
            props_col = ui.column().classes("w-full gap-2")
            props_container.append(props_col)

    with ui.row().classes("w-full gap-2 mt-2 items-center"):
        ui.label("Ziel-App").classes("text-weight-medium")
        app_folders = _list_app_folders()
        default_app = _load_target_app_config()
        if not app_folders:
            default_app = None
        elif default_app not in app_folders:
            default_app = app_folders[0]
        target_select = ui.select(
            options=app_folders,
            value=default_app,
            label="App aus labs/",
            on_change=lambda e: _save_target_app_config(getattr(e, "value", "") or ""),
        ).classes("w-52")
        target_app_select_ref.append(target_select)
        ui.label("(Save/Load/Skeleton beziehen sich auf diese App)").classes("text-caption text-grey")

        def do_create_app_from_template() -> None:
            with ui.dialog() as dlg, ui.card().classes("p-4 min-w-80"):
                ui.label("Neue App aus Template (standard_app)").classes("text-h6")
                name_input = ui.input("App-Name (Ordner unter labs/)", placeholder="z. B. 01_04_Modulation").classes("w-full")
                name_input.props("outlined")

                def on_create() -> None:
                    name = (name_input.value or "").strip()
                    if not name:
                        ui.notify("Bitte einen App-Namen angeben.", type="warning")
                        return
                    try:
                        create_app_from_template(
                            "standard_app",
                            name,
                            LABS_DIR,
                            TEMPLATES_DIR,
                        )
                    except ValueError as e:
                        ui.notify(str(e), type="negative")
                        return
                    # Dropdown aktualisieren und neue App auswählen
                    new_folders = _list_app_folders()
                    if target_app_select_ref:
                        sel = target_app_select_ref[0]
                        sel.options = new_folders
                        sel.value = name
                        sel.update()
                    _save_target_app_config(name)
                    dlg.close()
                    ui.notify(f"App erstellt: labs/{name}. Jetzt Layout gestalten und speichern.")

                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button("Abbrechen", on_click=dlg.close).props("flat")
                    ui.button("Erstellen", on_click=on_create).props("unelevated")
            dlg.open()

        ui.button("Neue App aus Template", on_click=do_create_app_from_template).props("flat dense").classes("ml-2")

        def do_diff_template_lab() -> None:
            target_dir = _get_target_app_dir()
            if not target_dir or not target_dir.exists():
                ui.notify("Bitte zuerst eine Ziel-App aus labs/ wählen.", type="warning")
                return
            template_path = TEMPLATES_DIR / "standard_app"
            if not template_path.is_dir():
                ui.notify("Template nicht gefunden: standard_app", type="negative")
                return
            with ui.dialog() as opt_dlg, ui.card().classes("p-4 min-w-80"):
                ui.label("Diff: Optionen").classes("text-h6")
                cb_include_layout = ui.checkbox("layout.json einbeziehen", value=True).props("dense")
                ui.label("Ohne layout.json siehst du nur Unterschiede in _core, assignments usw.").classes("text-caption text-grey")

                def show_diff() -> None:
                    include_layout = bool(cb_include_layout.value if hasattr(cb_include_layout, "value") else True)
                    opt_dlg.close()
                    diff_text = diff_template_lab(template_path, target_dir, include_layout=include_layout)
                    with ui.dialog() as res_dlg, ui.card().classes("p-4 max-w-4xl max-h-[80vh]"):
                        ui.label("Diff: Template vs. Ziel-App (nur Template-Dateien)").classes("text-h6")
                        with ui.scroll_area().classes("w-full border rounded"):
                            ui.html(f"<pre class='p-4 text-caption' style='white-space: pre-wrap; font-family: monospace;'>{html.escape(diff_text)}</pre>")
                        ui.button("Schließen", on_click=res_dlg.close).props("flat").classes("mt-2")
                    res_dlg.open()

                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button("Abbrechen", on_click=opt_dlg.close).props("flat")
                    ui.button("Diff anzeigen", on_click=show_diff).props("unelevated")
            opt_dlg.open()

        def do_sync_to_template() -> None:
            target_dir = _get_target_app_dir()
            if not target_dir or not target_dir.exists():
                ui.notify("Bitte zuerst eine Ziel-App aus labs/ wählen.", type="warning")
                return
            template_path = TEMPLATES_DIR / "standard_app"
            if not template_path.is_dir():
                ui.notify("Template nicht gefunden: standard_app", type="negative")
                return
            with ui.dialog() as dlg, ui.card().classes("p-4 min-w-80"):
                ui.label("Sync: Ziel-App → Template").classes("text-h6")
                cb_layout = ui.checkbox("layout.json mit übernehmen", value=False)
                cb_apply = ui.checkbox("Jetzt schreiben (Apply, sonst nur Dry-run)", value=False)

                def on_sync() -> None:
                    dry_run = not (cb_apply.value if hasattr(cb_apply, "value") else False)
                    include_layout = bool(cb_layout.value if hasattr(cb_layout, "value") else False)
                    copied = sync_lab_to_template(
                        target_dir,
                        template_path,
                        include_layout=include_layout,
                        dry_run=dry_run,
                    )
                    dlg.close()
                    if dry_run:
                        ui.notify(f"Dry-run: würde kopieren: {', '.join(copied) or '(keine)'}. Mit 'Apply' tatsächlich schreiben.")
                    else:
                        ui.notify(f"Template aktualisiert: {', '.join(copied) or '(keine)'}")

                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    ui.button("Abbrechen", on_click=dlg.close).props("flat")
                    ui.button("Sync", on_click=on_sync).props("unelevated")
            dlg.open()

        ui.button("Diff Template↔App", on_click=do_diff_template_lab).props("flat dense")
        ui.button("Sync App→Template", on_click=do_sync_to_template).props("flat dense")

    with ui.row().classes("w-full gap-2 mt-2"):
        ui.label("Layout").classes("text-weight-medium")
        ui.button("Update live preview", on_click=refresh_preview).props("flat dense")
        ui.button("Save layout", on_click=do_save_to_dev_app).props("flat dense")
        ui.button("Load layout", on_click=do_load_from_dev_app).props("flat dense")

    with ui.row().classes("w-full gap-2 mt-2 items-center"):
        ui.label("Skeleton").classes("text-weight-medium")
        ui.button("Generate skeleton", on_click=do_skeleton).props("flat dense")
        ui.label("Aktualisiert callback_skeleton.py, model_schema.py, user_callbacks.py in der gewählten Ziel-App.").classes("text-caption text-grey")

    with ui.expansion("Live-Preview", icon="preview").classes("w-full mt-2"):
        preview_col = ui.column().classes("w-full gap-2 border rounded p-2 bg-grey-1")
        preview_container.append(preview_col)

    def on_key(e):
        key = getattr(e, "key", None) or (e.args.get("key") if isinstance(getattr(e, "args", None), dict) else None)
        if hasattr(key, "name"):
            key = getattr(key, "name", key)
        if key in ("ArrowUp", "Up"):
            move_selected("up")
        elif key in ("ArrowDown", "Down"):
            move_selected("down")
        elif key in ("ArrowLeft", "Left"):
            move_selected("left")
        elif key in ("ArrowRight", "Right"):
            move_selected("right")

    ui.keyboard(on_key=on_key)
    ui.label("Cursor ↑/↓/←/→: change cell | Palette: place widget in active cell").classes("text-caption")

    refresh_grid()
    refresh_props()
    refresh_preview()

    ui.run(port=8083, title="Grid Editor", reload=False)


if __name__ == "__main__":
    main()
