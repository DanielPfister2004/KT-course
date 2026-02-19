"""
Erzeugt aus einem Layout-JSON das Callback-Skeleton und die Modell-State-Definition.

Verwendung:
  python -m app_builder.skeleton path/to/layout.json --out path/to/app_dir/

Erzeugt:
  - callback_skeleton.py  (State + Registrierung; bei --user-module nur Imports aus User-Datei)
  - user_callbacks.py      (optional, bei --user-module: nur wenn nicht vorhanden – deine Logik bleibt erhalten)
  - model_schema.py        (optional: --model)

user_callbacks.py: Der Generator setzt pro Callback automatisch "#begin user code" und "#end user code".
Beim Merge bleiben diese Blöcke erhalten; neue Callbacks werden als Stubs inkl. Marker ergänzt. User muss keine Marker einfügen.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .layout_schema import (
    collect_callback_names,
    collect_state_entries,
    get_widget_node_by_path_id,
    load_layout,
    path_id_to_snake,
)

USER_CODE_START = "#begin user code"
USER_CODE_END = "#end user code"
WIDGET_MARKER = "# widget:"


def _expected_callback_args(kind: str, widget_type: str) -> str:
    """Kurze Inline-Doku: welche Variablen der Callback erwartet (für Studierende)."""
    if kind == "click":
        return "Callback args: (none)"
    if kind == "relayout":
        return "Callback args: relayout_data: Any (Plotly zoom/pan etc.)"
    if kind == "change":
        if widget_type in ("checkbox", "toggle_button"):
            return "Callback args: value: bool"
        if widget_type in ("slider", "number_input", "gain_control_vue"):
            return "Callback args: value: float"
        if widget_type in ("input", "select"):
            return "Callback args: value: str | Any"
    return "Callback args: value: Any"


def _get_widget_label(layout: dict, path_id: str) -> str:
    """Label aus Layout-Knoten (props.label oder id)."""
    node = get_widget_node_by_path_id(layout, path_id)
    if not node:
        return ""
    props = node.get("props") or {}
    return str(props.get("label", node.get("id", "")) or "").strip()


def generate_callback_skeleton(layout: dict) -> str:
    """Python-Quelltext für callback_skeleton.py."""
    state_entries = collect_state_entries(layout)
    callbacks = collect_callback_names(layout)

    lines = [
        '"""',
        "Callback-Skeleton: generated from layout.json by App-Builder.",
        "User code: fill in callback logic here. Access state via model.state['path_id'].",
        '"""',
        "from __future__ import annotations",
        "",
        "from typing import Any, Callable",
        "",
        "# ---- State-Defaults (Keys = Path-IDs) ----",
        "STATE_DEFAULTS: dict[str, Any] = {",
    ]
    for k, v in state_entries.items():
        repr_v = repr(v)
        lines.append(f'    {repr(k)}: {repr_v},')
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("# ---- Callbacks (user fills body) ----")
    lines.append("")

    for path_id, kind, py_name, widget_type, _merge_key in callbacks:
        args_doc = _expected_callback_args(kind, widget_type)
        if kind == "change":
            lines.append(f"def {py_name}(value: Any) -> None:")
            lines.append(f'    """Path-ID: {path_id}. {args_doc}"""')
            lines.append("    pass")
        elif kind == "relayout":
            lines.append(f"def {py_name}(relayout_data: Any) -> None:")
            lines.append(f'    """Path-ID: {path_id}. {args_doc}"""')
            lines.append("    pass")
        else:
            lines.append(f"def {py_name}() -> None:")
            lines.append(f'    """Path-ID: {path_id}. {args_doc}"""')
            lines.append("    pass")
        lines.append("")

    lines.append("# ---- Callback-Registry (for GUI layer) ----")
    lines.append("def get_callback_registry() -> dict[str, Callable]:")
    lines.append("    \"\"\"Mapping: path_id (or callback_name) -> Callable. Used by build_ui.\"\"\"")
    lines.append("    return {")
    for path_id, kind, py_name, _, _merge_key in callbacks:
        lines.append(f'        {repr(path_id)}: {py_name},')
    lines.append("    }")
    lines.append("")

    return "\n".join(lines)


def generate_callback_skeleton_registry_only(
    layout: dict, user_module: str, *, import_from_parent: bool = False
) -> str:
    """Wie generate_callback_skeleton, aber ohne Funktionsrümpfe – importiert aus user_module (z. B. user_callbacks).
    STATE_DEFAULTS nur in model_schema (single source), nicht hier.
    import_from_parent: Bei True (z. B. callback_skeleton in _core) Import from ..assignments.user_callbacks."""
    callbacks = collect_callback_names(layout)
    py_names = [py_name for _, _, py_name, _, _ in callbacks]
    lines = [
        '"""',
        "Callback-Skeleton: generated from layout.json by App-Builder.",
        "Logic lives in " + user_module + ".py (not overwritten).",
        "State defaults: model_schema.STATE_DEFAULTS (single source).",
        '"""',
        "from __future__ import annotations",
        "",
        "from typing import Callable",
        "",
        "# ---- Callbacks from " + user_module + ".py (user edits this file only) ----",
    ]
    import_path = (".." + user_module) if import_from_parent else ("." + user_module)
    lines.append(f"from {import_path} import " + ", ".join(py_names))
    lines.append("")
    lines.append("# ---- Callback-Registry (für GUI-Schicht) ----")
    lines.append("def get_callback_registry() -> dict[str, Callable]:")
    lines.append("    return {")
    for path_id, _, py_name, _, _ in callbacks:
        lines.append(f'        {repr(path_id)}: {py_name},')
    lines.append("    }")
    lines.append("")
    return "\n".join(lines)


def generate_user_callbacks_stubs(layout: dict) -> str:
    """Nur die Callback-Funktionen (Stubs) für user_callbacks.py. Jeder Block wird vom Generator mit #begin/#end user code umschlossen."""
    callbacks = collect_callback_names(layout)
    lines = [
        '"""',
        "User callbacks: logic for the GUI. Edit only the code between #begin user code and #end user code (inside each function).",
        "The function signature is generated; only the body is preserved when regenerating.",
        '"""',
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
    ]
    for path_id, kind, py_name, widget_type, merge_key in callbacks:
        label = _get_widget_label(layout, path_id)
        lines.extend(_stub_lines_for_callback(path_id, kind, py_name, widget_type, merge_key, label=label))
    return "\n".join(lines)


def _normalize_merge_key(raw: str) -> str:
    """Aus '# widget: user_id=power' oder '# widget: path_id: row_0.widget_1' → einheitlicher Merge-Key."""
    raw = raw.strip()
    if raw.startswith("user_id="):
        return raw
    if raw.startswith("path_id:"):
        rest = raw.split(":", 1)[-1].strip()
        return f"path_id:{rest}"
    # Legacy: nur path_id (z. B. "row_0.widget_1") → als path_id: key speichern
    return f"path_id:{raw}"


def _parse_user_callbacks_file(content: str) -> dict[str, Any]:
    """
    Parse existing user_callbacks.py into header and per-merge_key blocks.
    Block is "user" if it contains both USER_CODE_START and USER_CODE_END; else "stub".
    Returns {"header": str, "blocks": {merge_key: ("user"|"stub", content_str)}}.
    merge_key: "user_id=<id>" oder "path_id:<path_id>" (inkl. Legacy nur path_id).
    """
    lines = content.splitlines()
    header_lines: list[str] = []
    blocks: dict[str, tuple[str, str]] = {}
    i = 0
    # Header: everything before first "# widget:" or first "def on_..." (legacy callbacks)
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith(WIDGET_MARKER):
            break
        if stripped.startswith("def on_") and "(" in stripped:
            break
        header_lines.append(lines[i])
        i += 1
    header = "\n".join(header_lines).rstrip()

    # Blocks: from "# widget: <merge_key>" to next "# widget:" or EOF
    while i < len(lines):
        line = lines[i]
        if not line.strip().startswith(WIDGET_MARKER):
            i += 1
            continue
        raw = line.split(":", 1)[-1].strip()
        merge_key = _normalize_merge_key(raw)
        block_start = i
        i += 1
        while i < len(lines) and not lines[i].strip().startswith(WIDGET_MARKER):
            i += 1
        block_content = "\n".join(lines[block_start:i])
        if USER_CODE_START in block_content and USER_CODE_END in block_content:
            block_lines = lines[block_start:i]
            begin_idx = end_idx = -1
            for j, ln in enumerate(block_lines):
                if USER_CODE_START in ln:
                    begin_idx = j
                if USER_CODE_END in ln:
                    end_idx = j
                    break
            if begin_idx >= 0 and end_idx > begin_idx:
                body = "\n".join(block_lines[begin_idx + 1 : end_idx]).rstrip()
                if body.strip().startswith("def "):
                    blocks[merge_key] = ("user_legacy", block_content)
                else:
                    blocks[merge_key] = ("user", body)
            else:
                blocks[merge_key] = ("stub", block_content)
        else:
            blocks[merge_key] = ("stub", block_content)
    return {"header": header, "blocks": blocks}


def _stub_lines_for_callback(
    path_id: str,
    kind: str,
    py_name: str,
    widget_type: str,
    merge_key: str,
    body: str | None = None,
    label: str = "",
) -> list[str]:
    """Emit callback: # widget: <merge_key>, def + docstring, then #begin user code, body, #end user code.
    merge_key: user_id=<id> oder path_id:<path_id> – für Merge bei Regenerierung (user_id bleibt bei Umplatzierung stabil)."""
    args_doc = _expected_callback_args(kind, widget_type)
    widget_info = f"Widget: {widget_type!r}"
    if label:
        widget_info += f", label: {label!r}"
    widget_info += ". " + args_doc
    lines = [f"# widget: {merge_key}"]
    def _is_empty_or_pass(b: str | None) -> bool:
        if b is None:
            return True
        s = (b or "").strip()
        return s in ("", "pass")

    if kind == "change":
        lines.append(f"def {py_name}(value: Any) -> None:")
        lines.append(f'    """Path-ID: {path_id}. {widget_info}"""')
        default_body = "    # value = value\n    pass" if _is_empty_or_pass(body) else body
    elif kind == "relayout":
        lines.append(f"def {py_name}(relayout_data: Any) -> None:")
        lines.append(f'    """Path-ID: {path_id}. {widget_info}"""')
        default_body = "    # relayout_data = relayout_data\n    pass" if _is_empty_or_pass(body) else body
    else:
        lines.append(f"def {py_name}() -> None:")
        lines.append(f'    """Path-ID: {path_id}. {widget_info}"""')
        default_body = "    # (no arguments)\n    pass" if _is_empty_or_pass(body) else body
    lines.append(USER_CODE_START)
    lines.append(default_body.rstrip())
    lines.append(USER_CODE_END)
    lines.append("")
    return lines


def merge_user_callbacks_stubs(layout: dict, existing_content: str) -> str:
    """
    Merge layout-driven stubs with existing user_callbacks.py.
    - Header from existing file (or default if empty).
    - For each callback in layout: if existing file has a "user" block for that path_id, keep body; else emit new stub.
    - If the file has no callback blocks (e.g. user deleted all), all layout callbacks are emitted as new stubs.
    - New path_ids get a fresh stub; removed widgets are dropped.
    """
    callbacks = collect_callback_names(layout)
    parsed = _parse_user_callbacks_file(existing_content)
    header = (parsed["header"] or "").strip()
    if not header:
        header = (
            '"""\n'
            "User callbacks: logic for the GUI. Code between "
            '"#begin user code" and "#end user code" (inside each function) is preserved when regenerating.\n'
            '"""\n'
            "from __future__ import annotations\n\n"
            "from typing import Any"
        )
    out_lines: list[str] = [header.rstrip(), ""]
    for path_id, kind, py_name, widget_type, merge_key in callbacks:
        label = _get_widget_label(layout, path_id)
        if merge_key in parsed["blocks"]:
            tag, content = parsed["blocks"][merge_key]
            if tag == "user":
                out_lines.extend(_stub_lines_for_callback(path_id, kind, py_name, widget_type, merge_key, body=content, label=label))
                continue
            if tag == "user_legacy":
                out_lines.append(content)
                continue
        out_lines.extend(_stub_lines_for_callback(path_id, kind, py_name, widget_type, merge_key, label=label))
    return "\n".join(out_lines).rstrip() + "\n"


def generate_model_schema(layout: dict) -> str:
    """Python-Quelltext für model_schema.py (State-Defaults + load/save)."""
    state_entries = collect_state_entries(layout)
    lines = [
        '"""',
        "Model schema: state defaults from layout.json. Session persistence (JSON).",
        '"""',
        "from __future__ import annotations",
        "",
        "import json",
        "from pathlib import Path",
        "from typing import Any",
        "",
        "STATE_DEFAULTS: dict[str, Any] = {",
    ]
    for k, v in state_entries.items():
        lines.append(f'    {repr(k)}: {repr(v)},')
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("def _coerce_like_default(value: Any, default: Any) -> Any:")
    lines.append("    \"\"\"If default is int/float, coerce value to number so sliders never get strings (avoids Quasar toFixed).\"\"\"")
    lines.append("    if isinstance(default, (int, float)) and not isinstance(default, bool):")
    lines.append("        if value is None or value == \"\":")
    lines.append("            return float(default) if isinstance(default, float) else int(default)")
    lines.append("        try:")
    lines.append("            n = float(value)")
    lines.append("            return n if isinstance(default, float) else int(n)")
    lines.append("        except (TypeError, ValueError):")
    lines.append("            return float(default) if isinstance(default, float) else int(default)")
    lines.append("    return value")
    lines.append("")
    lines.append("def load_state(path: Path | str) -> dict[str, Any]:")
    lines.append("    out = STATE_DEFAULTS.copy()")
    lines.append("    p = Path(path)")
    lines.append("    if p.exists():")
    lines.append("        with open(p, encoding=\"utf-8\") as f:")
    lines.append("            data = json.load(f)")
    lines.append("        for k, v in data.items():")
    lines.append("            if k in out:")
    lines.append("                out[k] = _coerce_like_default(v, out[k])")
    lines.append("    return out")
    lines.append("")
    lines.append("")
    lines.append("def save_state(state: dict[str, Any], path: Path | str) -> None:")
    lines.append("    with open(path, \"w\", encoding=\"utf-8\") as f:")
    lines.append("        json.dump(state, f, indent=2)")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="App-Builder: generate skeleton from layout.json")
    parser.add_argument("layout_json", type=Path, help="Path to layout.json")
    parser.add_argument("--out", "-o", type=Path, default=Path("."), help="Output directory for generated files")
    parser.add_argument("--model", action="store_true", help="Also generate model_schema.py")
    parser.add_argument(
        "--user-module",
        default=None,
        metavar="NAME",
        help="User-callbacks module (e.g. user_callbacks). callback_skeleton.py imports from it; NAME.py is created if missing; your edits are preserved.",
    )
    parser.add_argument(
        "--out-internal",
        default=None,
        metavar="DIR",
        help="If set (e.g. _core), write callback_skeleton.py and model_schema.py to out/DIR/ instead of out/.",
    )
    args = parser.parse_args()

    layout = load_layout(args.layout_json)
    args.out.mkdir(parents=True, exist_ok=True)
    internal_dir = (args.out / args.out_internal) if args.out_internal else args.out
    if args.out_internal:
        internal_dir.mkdir(parents=True, exist_ok=True)

    if args.user_module:
        callback_py = internal_dir / "callback_skeleton.py"
        callback_py.write_text(
            generate_callback_skeleton_registry_only(
                layout, args.user_module, import_from_parent=bool(args.out_internal)
            ),
            encoding="utf-8",
        )
        print(f"Wrote {callback_py}")
        # Unterstützt z. B. user_callbacks (→ out/user_callbacks.py) oder assignments.user_callbacks (→ out/assignments/user_callbacks.py)
        parts = args.user_module.split(".")
        user_dir = args.out
        for p in parts[:-1]:
            user_dir = user_dir / p
        user_dir.mkdir(parents=True, exist_ok=True)
        user_py = user_dir / f"{parts[-1]}.py"
        if not user_py.exists():
            user_py.write_text(generate_user_callbacks_stubs(layout), encoding="utf-8")
            print(f"Wrote {user_py} (created; add your logic here)")
        else:
            merged = merge_user_callbacks_stubs(layout, user_py.read_text(encoding="utf-8"))
            user_py.write_text(merged, encoding="utf-8")
            print(f"Wrote {user_py} (merge: new callbacks added, '#begin user code' blocks preserved)")
    else:
        callback_py = internal_dir / "callback_skeleton.py"
        callback_py.write_text(generate_callback_skeleton(layout), encoding="utf-8")
        print(f"Wrote {callback_py}")

    if args.model:
        model_py = internal_dir / "model_schema.py"
        model_py.write_text(generate_model_schema(layout), encoding="utf-8")
        print(f"Wrote {model_py}")


if __name__ == "__main__":
    main()
