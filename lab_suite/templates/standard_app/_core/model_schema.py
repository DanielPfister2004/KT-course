"""
Model schema: state defaults from layout.json. Session persistence (JSON).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATE_DEFAULTS: dict[str, Any] = {
    'row_0.widget_1': None,
    'row_1.widget_2': '',
    'row_1.widget_5': 1.0,
    'row_2.widget_3': '',
    'row_2.widget_4': '',
    'row_2.widget_6': '',
}


def _coerce_like_default(value: Any, default: Any) -> Any:
    """If default is int/float, coerce value to number so sliders never get strings (avoids Quasar toFixed)."""
    if isinstance(default, (int, float)) and not isinstance(default, bool):
        if value is None or value == "":
            return float(default) if isinstance(default, float) else int(default)
        try:
            n = float(value)
            return n if isinstance(default, float) else int(n)
        except (TypeError, ValueError):
            return float(default) if isinstance(default, float) else int(default)
    return value

def load_state(path: Path | str) -> dict[str, Any]:
    out = STATE_DEFAULTS.copy()
    p = Path(path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            if k in out:
                out[k] = _coerce_like_default(v, out[k])
    return out


def save_state(state: dict[str, Any], path: Path | str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
