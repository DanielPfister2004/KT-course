#!/usr/bin/env python3
"""Visualisiert eine TX-Stream-Aufzeichnung (.c64 + optional .meta.json).

Beispiel:
  python lab_suite/scripts/plot_stream_tx_capture.py lab_suite/app_pluto_mod/debug_captures/tx_stream_20260328_120000.c64

Es werden Zeitreihe (Betrag), Histogramm |z| und PSD (Welch) geplottet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def main() -> int:
    p = argparse.ArgumentParser(description="Plot Pluto TX stream capture (.c64)")
    p.add_argument("c64_path", type=Path, help="Pfad zur .c64-Datei (complex64)")
    p.add_argument("--meta", type=Path, default=None, help="Optional .meta.json (sonst .c64 -> .meta.json)")
    p.add_argument("--max-time-ms", type=float, default=5.0, help="Zeitfenster fuer Wellenform [ms]")
    p.add_argument("--no-show", action="store_true", help="Figure speichern statt Fenster")
    p.add_argument("-o", "--output", type=Path, default=None, help="PNG bei --no-show")
    args = p.parse_args()

    iq_path = args.c64_path
    if not iq_path.is_file():
        print(f"Datei fehlt: {iq_path}", file=sys.stderr)
        return 1

    meta_path = args.meta
    if meta_path is None:
        meta_path = iq_path.with_suffix(".meta.json")

    fs_hz = None
    if meta_path.is_file():
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            fs_hz = float(meta.get("fs_hz", 0) or 0) or None
        except Exception:
            meta = {}
    else:
        meta = {}

    raw = np.fromfile(iq_path, dtype=np.complex64)
    n = raw.size
    if n < 2:
        print("Zu wenige Samples.", file=sys.stderr)
        return 1

    if fs_hz is None:
        fs_hz = float(meta.get("fs_hz", 2_048_000)) if meta else 2_048_000.0
        print(f"Hinweis: fs_hz aus Fallback {fs_hz:g} Hz — ggf. .meta.json pruefen.", file=sys.stderr)

    mag = np.abs(raw)

    try:
        import matplotlib.pyplot as plt
        from scipy import signal as scipy_signal
    except ImportError as e:
        print(f"matplotlib/scipy noetig: {e}", file=sys.stderr)
        return 1

    n_vis = min(int(fs_hz * args.max_time_ms / 1000.0), n)
    t = np.arange(n_vis) / fs_hz

    fig, axes = plt.subplots(3, 1, figsize=(11, 8), constrained_layout=True)

    axes[0].plot(t * 1e3, mag[:n_vis], lw=0.8)
    axes[0].set_ylabel("|IQ|")
    axes[0].set_xlabel("t [ms]")
    axes[0].set_title(f"TX-Stream capture: {iq_path.name}  (n={n}, fs={fs_hz:g} Hz)")

    axes[1].hist(mag, bins=min(80, max(20, n // 5000)), color="steelblue", alpha=0.85)
    axes[1].set_xlabel("|IQ|")
    axes[1].set_ylabel("count")

    nfft = min(131072, max(1024, 1 << int(np.log2(n))))
    f, pxx = scipy_signal.welch(
        raw,
        fs=fs_hz,
        nperseg=min(nfft, n),
        return_onesided=False,
        scaling="density",
    )
    f = np.fft.fftshift(f)
    pxx = np.fft.fftshift(pxx)
    axes[2].semilogy(f / 1e3, pxx + 1e-20)
    axes[2].set_xlabel("f [kHz]")
    axes[2].set_ylabel("PSD (Welch)")
    axes[2].set_xlim(-min(fs_hz / 2, 500), min(fs_hz / 2, 500))

    if args.no_show:
        out = args.output or iq_path.with_suffix(".png")
        fig.savefig(out, dpi=120)
        print(out)
    else:
        plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
