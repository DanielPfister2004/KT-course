"""
GainControlVue – Gain-Control als NiceGUI Custom-Element (Vue/JS).

Verwendung wie die Python-Klasse GainControl:
  from lab_suite.widgets import GainControlVue
  gain = GainControlVue('Gain', min_=0, max_=10, value=1, on_change=lambda e: ...)
  # Wert aus Event: e.args (float)
  # Reset von außen: gain.reset()
"""
from __future__ import annotations

from collections.abc import Callable

from nicegui.element import Element


class GainControlVue(Element, component="gain_control.js"):

    def __init__(
        self,
        label: str = "Gain",
        *,
        min_: float = 0,
        max_: float = 10,
        value: float = 1,
        on_change: Callable | None = None,
    ) -> None:
        super().__init__()
        self._props["label"] = label
        self._props["min"] = min_
        self._props["max"] = max_
        self._props["value"] = value
        if on_change is not None:
            self.on("change", on_change)

    def reset(self) -> None:
        """Reset auf 1 (ruft Methode in der Vue-Komponente auf)."""
        self.run_method("reset")
