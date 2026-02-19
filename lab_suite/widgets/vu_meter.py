"""
VU-Meter – Anzeige wie ein analoges Voltmeter (Skala + Nadel), Vue/JS.

Reines Anzeige-Widget: value wird von außen gesetzt (z. B. aus Audio-Pegel).
Kein Klick/Drag – nur Darstellung.
"""
from __future__ import annotations

from nicegui.element import Element


class VuMeter(Element, component="vu_meter.js"):

    def __init__(
        self,
        value: float = 0.0,
        *,
        min_: float = 0.0,
        max_: float = 1.0,
        show_value: bool = True,
        width: str = "120px",
        height: str = "80px",
    ) -> None:
        super().__init__()
        self._props["value"] = value
        self._props["min"] = min_
        self._props["max"] = max_
        self._props["showValue"] = show_value
        self._props["width"] = width
        self._props["height"] = height

    def set_value(self, value: float) -> None:
        """Anzeige aktualisieren (z. B. aus Timer/Callback)."""
        self._props["value"] = value
        self.update()
