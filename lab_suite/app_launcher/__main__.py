"""Einstieg: python -m app_launcher (aus lab_suite)."""
from __future__ import annotations

from .app import run

# Ohne Guard, damit auch der ggf. von NiceGUI gespawnte Prozess ui.run() ausführt
run()
