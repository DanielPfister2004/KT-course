"""
Grid-Modell für den Grid-Editor (Stufe 2: Container in Zelle).
Zellen-Matrix rows×cols; jede Zelle = None | Widget-Spec | Container-Spec | Group-Spec.
Hierarchie: Container/Group haben children (Widgets oder weitere Container), entspricht layout.json/Browser-DOM.
"""
from __future__ import annotations

import copy
from typing import Any

Cell = None | dict  # None | Widget (type=widget) | Container (type=container, layout_type, children) | Group (type=group, children)

# Erlaubte layout_type für Container in einer Zelle (alle außer tab, der nur Kind von tabs ist)
CONTAINER_LAYOUT_TYPES_IN_CELL = (
    "rows_columns",
    "column",
    "grid",
    "expansion",
    "scroll",
    "card",
    "splitter",
    "tabs",
)


def is_widget(cell: Cell) -> bool:
    """Zelle ist ein Widget (type == 'widget')."""
    return isinstance(cell, dict) and cell.get("type") == "widget"


def is_container(cell: Cell) -> bool:
    """Zelle ist ein Container (type == 'container' mit layout_type)."""
    return (
        isinstance(cell, dict)
        and cell.get("type") == "container"
        and cell.get("layout_type") in CONTAINER_LAYOUT_TYPES_IN_CELL
    )


def is_group(cell: Cell) -> bool:
    """Zelle ist eine Gruppe (type == 'group')."""
    return isinstance(cell, dict) and cell.get("type") == "group"


def is_container_or_group(cell: Cell) -> bool:
    """Zelle ist ein Container oder eine Gruppe (hat children)."""
    return is_container(cell) or is_group(cell)


def get_cell_children(cell: Cell) -> list[dict]:
    """Kinder einer Zelle (Container/Group); leere Liste bei Widget/None."""
    if not isinstance(cell, dict):
        return []
    return list(cell.get("children") or [])


def _collect_ids_from_node(node: dict, *, ids: set[str] | None = None) -> set[str]:
    """Sammelt alle id-Werte aus einem Knoten rekursiv (widget, container, group)."""
    if ids is None:
        ids = set()
    nid = node.get("id")
    if isinstance(nid, str) and nid:
        ids.add(nid)
    for ch in node.get("children") or []:
        if isinstance(ch, dict):
            _collect_ids_from_node(ch, ids=ids)
    return ids


def default_grid_state(rows: int = 4, cols: int = 6) -> dict[str, Any]:
    """Leerer Grid-Zustand: cells mit None gefüllt, selected_cell = (0, 0)."""
    cells: list[list[Cell]] = [[None] * cols for _ in range(rows)]
    return {
        "rows": rows,
        "cols": cols,
        "cells": cells,
        "selected_cell": (0, 0),
        "row_options": {},
    }


def _collect_widget_ids(cells: list[list[Cell]]) -> set[str]:
    """Sammelt alle Widget-IDs im Grid (inkl. in Containern/Gruppen, rekursiv)."""
    used: set[str] = set()

    def collect_rec(n: dict) -> None:
        if n.get("type") == "widget":
            wid = n.get("id")
            if isinstance(wid, str) and wid:
                used.add(wid)
        for ch in n.get("children") or []:
            if isinstance(ch, dict):
                collect_rec(ch)

    for row in cells:
        for cell in row:
            if isinstance(cell, dict):
                collect_rec(cell)
    return used


def next_widget_id(cells: list[list[Cell]], prefix: str = "widget") -> str:
    """Eindeutige Widget-ID im Grid (z. B. widget_1, widget_2)."""
    used = _collect_widget_ids(cells)
    for i in range(1, 1000):
        cand = f"{prefix}_{i}"
        if cand not in used:
            return cand
    return f"{prefix}_new"


def _collect_container_and_group_ids(cells: list[list[Cell]]) -> set[str]:
    """Sammelt alle id-Werte von Containern und Gruppen (rekursiv)."""
    used: set[str] = set()
    for row in cells:
        for cell in row:
            if isinstance(cell, dict):
                _collect_ids_from_node(cell, ids=used)
    return used


def next_container_id(cells: list[list[Cell]], prefix: str = "container") -> str:
    """Eindeutige Container-/Gruppen-ID im Grid (z. B. container_1, expansion_1)."""
    used = _collect_container_and_group_ids(cells)
    for i in range(1, 1000):
        cand = f"{prefix}_{i}"
        if cand not in used:
            return cand
    return f"{prefix}_new"


def grid_to_layout(
    cells: list[list[Cell]],
    rows: int,
    cols: int,
    *,
    dashboard_id: str = "dashboard",
    row_id_prefix: str = "row",
    row_options: dict | None = None,
) -> dict:
    """
    Erzeugt layout.json-kompatibles Dict aus dem Grid.
    Pro Zeile ein Container (rows_columns); Kinder = alle nicht-leeren Zellen
    (Widgets, Container, Gruppen) – hierarchischer Aufbau bleibt erhalten.
    row_options: optional { row_index: {"align_items": "start"|"center"|"end"|"stretch"} }.
    """
    row_options = row_options if isinstance(row_options, dict) else {}
    row_options = {int(k): v for k, v in row_options.items() if isinstance(v, dict)}
    row_containers: list[dict] = []
    for r in range(rows):
        row_cells = cells[r] if r < len(cells) else []
        children: list[dict] = []
        for c in range(min(cols, len(row_cells))):
            cell = row_cells[c]
            if isinstance(cell, dict):
                children.append(copy.deepcopy(cell))
        opts = row_options.get(r) or {}
        raw_align = opts.get("align_items") or "center"
        if not isinstance(raw_align, str):
            raw_align = getattr(raw_align, "key", None) or getattr(raw_align, "value", None) or "center"
        align = str(raw_align).strip().lower()
        if align not in ("start", "center", "end", "stretch"):
            align = "center"
        row_containers.append({
            "type": "container",
            "id": f"{row_id_prefix}_{r}",
            "layout_type": "rows_columns",
            "align_items": align,
            "children": children,
        })
    return {
        "version": 1,
        "dashboard": {
            "id": dashboard_id,
            "layout_type": "column",
            "children": row_containers,
        },
    }


def _row_child_allowed(node: dict) -> bool:
    """Prüft, ob ein Zeilen-Kind erlaubt ist (Widget, Container, Gruppe)."""
    if node.get("type") == "widget":
        return True
    if node.get("type") == "container" and node.get("layout_type") in CONTAINER_LAYOUT_TYPES_IN_CELL:
        return True
    if node.get("type") == "group":
        return True
    return False


def layout_to_grid(
    layout: dict,
    *,
    min_rows: int = 1,
    min_cols: int = 1,
    default_rows: int = 4,
    default_cols: int = 6,
) -> dict[str, Any] | None:
    """
    Liest layout.json in Grid-State. None wenn nicht grid-kompatibel.
    Kompatibel: dashboard.children nur Container mit layout_type rows_columns,
    deren children = Widgets und/oder Container (erlaubte layout_type) und/oder Gruppen.
    """
    dashboard = layout.get("dashboard") or {}
    children = dashboard.get("children") or []
    if not children:
        rows = max(min_rows, default_rows)
        cols = max(min_cols, default_cols)
        return default_grid_state(rows, cols)

    cells_rows: list[list[Cell]] = []
    row_options: dict[int, dict] = {}
    for r, child in enumerate(children):
        if child.get("type") != "container" or child.get("layout_type") != "rows_columns":
            return None
        raw_align = child.get("align_items") or "center"
        if not isinstance(raw_align, str):
            raw_align = getattr(raw_align, "key", None) or getattr(raw_align, "value", None) or "center"
        align = str(raw_align).strip().lower()
        if align not in ("start", "center", "end", "stretch"):
            align = "center"
        row_options[r] = {"align_items": align}
        row_children = child.get("children") or []
        row_cells: list[Cell] = []
        for node in row_children:
            if _row_child_allowed(node):
                row_cells.append(copy.deepcopy(node))
            else:
                return None
        cells_rows.append(row_cells)

    if not cells_rows:
        return default_grid_state(default_rows, default_cols)

    rows = len(cells_rows)
    max_row_len = max(len(r) for r in cells_rows)
    cols = max(min_cols, max_row_len, default_cols)
    # Normieren: jede Zeile auf Länge cols, None auffüllen
    cells: list[list[Cell]] = []
    for r in range(rows):
        row = cells_rows[r]
        cells.append([row[c] if c < len(row) else None for c in range(cols)])

    return {
        "rows": rows,
        "cols": cols,
        "cells": cells,
        "selected_cell": (0, 0),
        "row_options": row_options,
    }


def grid_swap_cells(
    cells: list[list[Cell]],
    rows: int,
    cols: int,
    from_pos: tuple[int, int],
    direction: str,
) -> bool:
    """
    Tauscht Zelle from_pos mit Nachbar in direction (up, down, left, right).
    Modifiziert cells in-place. Gibt True zurück wenn getauscht.
    """
    r, c = from_pos
    delta = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
    dr, dc = delta.get(direction, (0, 0))
    to_r, to_c = r + dr, c + dc
    if to_r < 0 or to_r >= rows or to_c < 0 or to_c >= cols:
        return False
    # Zeilen/Spalten ggf. erweitern
    while len(cells) <= to_r:
        cells.append([None] * cols)
    while len(cells[r]) <= to_c:
        cells[r].append(None)
    while len(cells[to_r]) <= to_c:
        cells[to_r].append(None)
    cells[r][c], cells[to_r][to_c] = cells[to_r][to_c], cells[r][c]
    return True


def _ensure_cells_rectangular(cells: list[list[Cell]], rows: int, cols: int) -> None:
    """Pad or trim cells to exactly rows×cols in-place."""
    while len(cells) < rows:
        cells.append([None] * cols)
    del cells[rows:]
    for r in range(len(cells)):
        row = cells[r]
        while len(row) < cols:
            row.append(None)
        del row[cols:]


def resize_grid(
    cells: list[list[Cell]],
    new_rows: int,
    new_cols: int,
    *,
    min_rows: int = 1,
    min_cols: int = 1,
) -> tuple[int, int]:
    """
    Setzt Grid auf new_rows × new_cols. Erweitert mit None, schneidet ab bei Verkleinerung.
    Modifiziert cells in-place. Gibt (rows, cols) zurück (geclampt auf min).
    """
    rows = max(min_rows, new_rows)
    cols = max(min_cols, new_cols)
    _ensure_cells_rectangular(cells, rows, cols)
    return rows, cols


def insert_row(
    cells: list[list[Cell]],
    rows: int,
    cols: int,
    at_row: int,
) -> tuple[int, int]:
    """
    Fügt eine leere Zeile an Position at_row ein, darunter liegende Zeilen nach unten.
    Modifiziert cells in-place. Gibt (neue rows, cols) zurück.
    """
    at_row = max(0, min(at_row, rows))
    cells.insert(at_row, [None] * cols)
    return rows + 1, cols


def insert_cell(
    cells: list[list[Cell]],
    rows: int,
    cols: int,
    at_row: int,
    at_col: int,
) -> tuple[int, int]:
    """
    Fügt eine leere Zelle nur in Zeile at_row an Position at_col ein, Zellen nach rechts.
    Modifiziert cells in-place. Gibt (rows, neue cols) zurück.
    """
    if at_row < 0 or at_row >= len(cells):
        return rows, cols
    at_col = max(0, min(at_col, len(cells[at_row])))
    cells[at_row].insert(at_col, None)
    new_cols = max(cols, len(cells[at_row]))
    # Andere Zeilen auf new_cols auffüllen, damit Anzeige rechteckig bleibt
    for r in range(len(cells)):
        if r != at_row:
            while len(cells[r]) < new_cols:
                cells[r].append(None)
    return rows, new_cols


def insert_column(
    cells: list[list[Cell]],
    rows: int,
    cols: int,
    at_col: int,
) -> tuple[int, int]:
    """
    Fügt eine leere Spalte an Position at_col ein, Spalten danach nach rechts.
    Modifiziert cells in-place. Gibt (rows, neue cols) zurück.
    """
    at_col = max(0, min(at_col, cols))
    for r in range(len(cells)):
        row = cells[r]
        while len(row) < at_col:
            row.append(None)
        row.insert(at_col, None)
    return rows, cols + 1


def delete_row(
    cells: list[list[Cell]],
    rows: int,
    cols: int,
    at_row: int,
) -> tuple[int, int]:
    """
    Löscht die Zeile an Position at_row. Zeilen darunter rücken nach oben.
    Modifiziert cells in-place. Gibt (neue rows, cols) zurück. Mindestens 1 Zeile.
    """
    if rows <= 1:
        return rows, cols
    at_row = max(0, min(at_row, rows - 1))
    cells.pop(at_row)
    return rows - 1, cols


def delete_column(
    cells: list[list[Cell]],
    rows: int,
    cols: int,
    at_col: int,
) -> tuple[int, int]:
    """
    Löscht die Spalte an Position at_col. Spalten danach rücken nach links.
    Modifiziert cells in-place. Gibt (rows, neue cols) zurück. Mindestens 1 Spalte.
    """
    if cols <= 1:
        return rows, cols
    at_col = max(0, min(at_col, cols - 1))
    for row in cells:
        if at_col < len(row):
            row.pop(at_col)
    return rows, cols - 1


def delete_cell(
    cells: list[list[Cell]],
    rows: int,
    cols: int,
    at_row: int,
    at_col: int,
) -> tuple[int, int]:
    """
    Löscht nur die markierte Zelle in Zeile at_row an Position at_col.
    Zellen rechts davon in derselben Zeile rücken um 1 nach links (keine Lücke).
    cols wird neu aus maximaler Zeilenlänge bestimmt; kürzere Zeilen werden aufgefüllt.
    Modifiziert cells in-place. Gibt (rows, neue cols) zurück. Mindestens 1 Spalte.
    """
    if cols <= 1:
        return rows, cols
    if at_row < 0 or at_row >= len(cells):
        return rows, cols
    row = cells[at_row]
    if at_col < 0 or at_col >= len(row):
        return rows, cols
    row.pop(at_col)
    new_cols = max((len(r) for r in cells), default=1)
    new_cols = max(1, new_cols)
    for r in range(len(cells)):
        while len(cells[r]) < new_cols:
            cells[r].append(None)
    return rows, new_cols


def clamp_selection(selected_cell: tuple[int, int], rows: int, cols: int) -> tuple[int, int]:
    """Selection auf gültigen Bereich begrenzen."""
    r, c = selected_cell
    return (max(0, min(r, rows - 1)), max(0, min(c, cols - 1))) if rows and cols else (0, 0)
