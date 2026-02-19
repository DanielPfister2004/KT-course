"""
LED-Widget – Erscheinung per State (off / on / warning / error).

Einfaches Symbol mit Zustandslogik: set_state('on'), set_state(2) für warning, etc.
"""
from __future__ import annotations

from nicegui.element import Element


class Led(Element, component="led.js"):

    def __init__(
        self,
        state: str | int = "off",
        *,
        label: str = "",
        size: int | str = 16,
    ) -> None:
        super().__init__()
        self._props["state"] = state
        self._props["label"] = label
        self._props["size"] = size

    def set_state(self, state: str | int) -> None:
        """State setzen: 'off'|'on'|'warning'|'error' oder 0|1|2|3."""
        self._props["state"] = state
        self.update()
