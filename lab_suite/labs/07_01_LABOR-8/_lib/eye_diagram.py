"""Augendiagramm fuer digitale Basisbandsignale (z. B. ASK nach Demodulation).

Ohne Taktsynchronisation zeigen **zufaellig** gewaehlte Fenster alle Symbolphasen —
Flanken liegen dann gleichmaessig ueber die normierte Zeitachse (wirkt wie
„Spaghetti“). Sinnvoller Standard: aufeinanderfolgende Bloecke fester Laenge
``num_bits_visible * samples_per_bit``, beginnend bei ``start_offset``. Nur wenn
dieses Raster zu den echten Bitgrenzen passt (``start_offset`` ggf. in
``0 .. round(samples_per_bit)-1`` durchprobieren), schliesst sich das Auge.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

TraceMode = Literal["chunks", "random", "stride"]


def plot_eye_diagram(
    y: np.ndarray,
    *,
    samples_per_bit: float,
    num_bits_visible: int,
    start_offset: int = 0,
    trace_mode: TraceMode = "chunks",
    stride_samples: int = 128,
    max_traces: int = 500,
    rng_seed: int = 42,
    ax=None,
    title: str | None = None,
):
    """Ueberlagert Ausschnitte der Laenge ``num_bits_visible * samples_per_bit``.

    Horizontale Achse: **Bitperioden** normiert (0 .. ``num_bits_visible``).

    Parameters
    ----------
    trace_mode
        ``chunks`` (**Standard**): Zerlegung von ``y`` in **nicht ueberlappende**
        Fenster der Laenge ``win = round(num_bits_visible * samples_per_bit)`` mit
        Starts ``start_offset``, ``start_offset + win``, ``start_offset + 2*win``, …
        (bis zu ``max_traces`` Kurven). Entspricht genau der „fix in Bloecke
        schneiden und ueberlagern“-Vorgehensweise.

        ``random``: gleichverteilte Zufallsstarts im gueltigen Indexbereich —
        alle Phasen gemischt; typisch **kein** geschlossenes Auge (Illustration).

        ``stride``: arithmetische Starts mit Schritt ``stride_samples`` (feine
        Ueberlappung moeglich; Schritt ``samples_per_bit/4`` erzeugt oft kuenstlich
        vier vertikale Flankenbuendel).
    start_offset
        Index des **ersten** Fensters. Raster ``start_offset + k*win`` muss zu den
        Bitgrenzen im Signal passen — sonst ``start_offset`` variieren.
    """
    import matplotlib.pyplot as plt

    spb = float(samples_per_bit)
    if spb <= 0:
        raise ValueError("samples_per_bit muss positiv sein.")

    nb = int(num_bits_visible)
    if nb < 1:
        raise ValueError("num_bits_visible muss mindestens 1 sein.")

    win = int(round(nb * spb))

    y = np.asarray(y, dtype=float).ravel()

    lo = int(start_offset)
    if y.size < win + max(0, lo):
        raise ValueError(
            f"Zu wenige Samples ({y.size}) fuer Fensterlaenge {win} und start_offset={lo}."
        )

    if ax is None:
        plt.close("eye_diagram")
        _, ax = plt.subplots(figsize=(11.0, 4.5), num="eye_diagram")
    else:
        ax.clear()

    t_bits = np.arange(win, dtype=float) / spb

    hi = int(y.size - win)
    if hi < lo:
        raise ValueError(
            f"start_offset={lo} und Fenster {win} lassen keine gueltigen Starts zu."
        )

    starts: np.ndarray

    if trace_mode == "chunks":
        starts = np.arange(lo, hi + 1, win, dtype=np.int64)
        if starts.size > max_traces:
            idx = np.linspace(0, starts.size - 1, max_traces, dtype=int)
            starts = starts[idx]

    elif trace_mode == "random":
        span = int(hi - lo + 1)
        n_take = int(min(max_traces, span))
        rng = np.random.default_rng(int(rng_seed))
        off = rng.choice(span, size=n_take, replace=False)
        starts = np.sort(lo + off.astype(np.int64))

    elif trace_mode == "stride":
        st = max(1, int(stride_samples))
        starts = np.arange(lo, hi + 1, st, dtype=np.int64)
        if starts.size > max_traces:
            idx = np.linspace(0, starts.size - 1, max_traces, dtype=int)
            starts = starts[idx]

    else:
        raise ValueError(f"Unbekannter trace_mode: {trace_mode!r}")

    if starts.size == 0:
        raise ValueError("Keine gueltigen Fensterstarts — Daten zu kurz oder start_offset zu gross.")

    for s in starts:
        s = int(s)
        ax.plot(t_bits, y[s : s + win], color="C0", alpha=0.07, lw=0.9)

    for k in range(1, nb):
        ax.axvline(k, color="gray", ls=":", alpha=0.45)

    ax.set_xlim(0.0, float(nb))
    ax.set_xlabel("Zeit / Bitperioden (normiert)")
    ax.set_ylabel("Amplitude")
    if title:
        ax.set_title(title)
    ax.grid(True, alpha=0.3)
    return ax
