#!/usr/bin/env python3
"""
Lädt Plotly.js (Version wie im Widget) herunter und speichert sie als plotly.min.js.
Damit können Labs offline laufen, ohne CDN-Zugriff.

Standard: Eine Kopie in widgets/static/ – alle Apps nutzen /widgets-static/plotly.min.js
(Platzersparnis bei vielen Labs). Einmal ausführen reicht.

Aufruf (aus lab_suite):
  python -m app_builder.fetch_plotly_offline
  python -m app_builder.fetch_plotly_offline --target labs/mein_lab/static   # nur bei Bedarf pro App
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PLOTLY_JS_URL = "https://cdn.plot.ly/plotly-2.27.0.min.js"
OUTPUT_FILENAME = "plotly.min.js"


def main() -> int:
    app_builder = Path(__file__).resolve().parent
    lab_suite = app_builder.parent
    default_target = lab_suite / "widgets" / "static"

    parser = argparse.ArgumentParser(description="Plotly.js für Offline-Nutzung herunterladen.")
    parser.add_argument(
        "--target",
        "-t",
        type=Path,
        default=default_target,
        help=f"Zielordner für plotly.min.js (default: {default_target})",
    )
    args = parser.parse_args()
    target_dir = Path(args.target).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / OUTPUT_FILENAME

    try:
        import urllib.request
        req = urllib.request.Request(PLOTLY_JS_URL, headers={"User-Agent": "KT-lab_suite/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except Exception as e:
        print(f"Download fehlgeschlagen: {e}", file=sys.stderr)
        print("Bitte plotly-2.27.0.min.js manuell von cdn.plot.ly herunterladen und als", out_path, "speichern.", file=sys.stderr)
        return 1

    out_path.write_bytes(data)
    print(f"Gespeichert: {out_path} ({len(data) // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
