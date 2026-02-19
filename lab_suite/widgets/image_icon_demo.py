"""
Demo-Widget: Rastergrafik (PNG/GIF) und Inline-SVG-Icon in einem Vue-Widget.

- image_src: URL zum Bild (z. B. /static/foo.png nach ui.add_static_files).
- Inline-SVG ist im .js-Template eingebaut (z. B. von heroicons.com kopiert).
"""
from __future__ import annotations

from nicegui.element import Element


class ImageIconDemo(Element, component="image_icon_demo.js"):

    def __init__(
        self,
        *,
        image_src: str = "",
        image_alt: str = "Image",
        show_icon: bool = True,
        label: str = "",
    ) -> None:
        super().__init__()
        self._props["imageSrc"] = image_src
        self._props["imageAlt"] = image_alt
        self._props["showIcon"] = show_icon
        self._props["label"] = label
