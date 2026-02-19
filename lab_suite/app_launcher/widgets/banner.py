"""
Banner – Vue-Widget für Kommunikationstechnik-Optik (Funk/Signal, Verlauf, 3 Textfelder).

Volle Breite (flex), Höhe über Prop. Drei Texte für konsequente Übungsbenennung (z. B. Modul, Thema, Nr.).
"""
from __future__ import annotations

from nicegui.element import Element


class Banner(Element, component="banner.js"):
    def __init__(
        self,
        text1: str = "",
        text2: str = "",
        text3: str = "",
        *,
        height: str = "80px",
        font_family: str = "",
        font_size1: str = "",
        font_size2: str = "",
        font_size3: str = "",
        text_color: str = "",
        gradient_start: str = "#0d47a1",
        gradient_end: str = "#1565c0",
    ) -> None:
        super().__init__()
        self._props["text1"] = text1
        self._props["text2"] = text2
        self._props["text3"] = text3
        self._props["height"] = height
        self._props["font_family"] = font_family
        self._props["font_size1"] = font_size1
        self._props["font_size2"] = font_size2
        self._props["font_size3"] = font_size3
        self._props["text_color"] = text_color
        self._props["gradient_start"] = gradient_start
        self._props["gradient_end"] = gradient_end
