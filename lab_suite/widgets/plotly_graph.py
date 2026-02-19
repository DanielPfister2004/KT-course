"""
Generisches Plotly-Graph-Widget – eine Vue-Komponente für alle Modi.

Spektrum, Oszilloskop (Time-Domain), Scatter, 3D: ein gemeinsamer Graph-Container;
Steuerung und Defaults (RBW, Time-Base, …) bleiben in spezialisierten Wrappern oder
in der App (z. B. SpectrumPanel mit PlotlyGraph + Frequenz-/Pegel-Controls).

Daten: data/layout können NumPy-Arrays enthalten (x, y, z in Traces); sie werden
intern zu Listen konvertiert (JSON-Serialisierung, Performance: .tolist() ist schnell).
"""
from __future__ import annotations

from typing import Any

from nicegui.element import Element


def _to_serializable(obj: Any) -> Any:
    """Konvertiert NumPy-Arrays/Skalare in listen/json-serialisierbare Python-Typen (für Plotly/Vue)."""
    if obj is None:
        return None
    try:
        import numpy as np
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
    except ImportError:
        pass
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_serializable(v) for v in obj]
    return obj


class PlotlyGraph(Element, component="plotly_graph.js"):

    def __init__(
        self,
        data: list[dict] | None = None,
        layout: dict | None = None,
        config: dict | None = None,
        *,
        height: str = "400px",
        plotly_script_url: str = "",
    ) -> None:
        super().__init__()
        self._props["data"] = _to_serializable(data or [])
        self._props["layout"] = _to_serializable(layout or {})
        self._props["config"] = config or {"responsive": True}
        self._props["height"] = height
        self._props["plotlyScriptUrl"] = plotly_script_url

    def update_figure(
        self,
        data: list[dict],
        layout: dict | None = None,
        config: dict | None = None,
        *,
        restyle_only: bool = False,
    ) -> None:
        """
        Graphen aktualisieren (neue Traces/Layout).
        data/traces dürfen NumPy-Arrays in x/y/z enthalten.
        restyle_only=True: nur x/y per restyle senden (weniger Daten, oft flüssiger bei Animation).
        """
        self._props["data"] = _to_serializable(data)
        self._props["restyleOnly"] = restyle_only
        if layout is not None:
            self._props["layout"] = _to_serializable(layout)
        if config is not None:
            self._props["config"] = config
        self.update()

    def update_from_figure(self, fig: Any) -> None:
        """Figure von plotly.graph_objects (go.Figure) übernehmen (z. B. fig.to_plotly_json())."""
        try:
            out = fig.to_plotly_json()
            self._props["data"] = _to_serializable(out.get("data", []))
            self._props["layout"] = _to_serializable(out.get("layout", {}))
            if "config" in out:
                self._props["config"] = out["config"]
            self.update()
        except Exception:
            pass
