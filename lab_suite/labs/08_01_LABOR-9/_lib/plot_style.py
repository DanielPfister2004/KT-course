"""Einheitliche Matplotlib-Darstellung fuer Labor-Notebooks."""

from __future__ import annotations

from typing import Any


def apply_lab_matplotlib_style(
    *,
    figsize: tuple[float, float] = (11.0, 4.0),
    grid: bool = True,
) -> None:
    import matplotlib.pyplot as plt

    plt.rcParams["figure.figsize"] = figsize
    plt.rcParams["axes.grid"] = grid


def rc_params_snapshot() -> dict[str, Any]:
    import matplotlib.pyplot as plt

    return {
        "figure.figsize": tuple(plt.rcParams["figure.figsize"]),
        "axes.grid": bool(plt.rcParams["axes.grid"]),
    }
