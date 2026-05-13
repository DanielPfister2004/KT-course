"""Mixer-Spektrum Plot und Replay-Zusammenfuehrung fuer Final-LAB."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import numpy as np

from .replay_json import load_replay_json, save_replay_json


def plot_mixer_spectrum(
    freq_hz: np.ndarray,
    p_dbm: np.ndarray,
    rbw_hz: Any,
    title: str,
    fig_id: str,
    *,
    replay: bool,
    widgets_module: Any = None,
    display_fn: Callable[..., None] | None = None,
) -> None:
    """Spektrum mit Marker. Matplotlib Slider + ipympl fuehren in Jupyter oft zu eingefrorenen Widgets;
    daher ipywidgets.IntSlider (Trace-Bin), continuous_update=False (Update beim Loslassen)."""
    import matplotlib.pyplot as plt

    if display_fn is None:
        from IPython.display import display as display_fn

    if widgets_module is None:
        try:
            import ipywidgets as widgets_module
        except ImportError:
            widgets_module = None

    _ipy_interactive = plt.isinteractive()
    plt.ioff()
    plt.close(fig_id)
    freq_mhz = np.asarray(freq_hz, dtype=float) / 1e6
    p_dbm = np.asarray(p_dbm, dtype=float)
    rbw_txt = f" | RBW={rbw_hz:.1f} Hz" if rbw_hz is not None else " | RBW=n/a"
    mode = "Replay" if replay else "Live"
    n = int(p_dbm.size)

    fig = plt.figure(figsize=(12.0, 5.8), num=fig_id)
    ax = fig.add_subplot(1, 1, 1)

    ax.plot(freq_mhz, p_dbm, color="C0", lw=1.0)
    ax.set_xlabel("Frequenz (MHz)")
    ax.set_ylabel("Leistung (dBm)")
    ax.set_title(f"{title} ({mode})" + rbw_txt)
    ax.grid(True, alpha=0.35)

    y0, y1 = float(np.min(p_dbm)), float(np.max(p_dbm))
    if np.isfinite(y0) and np.isfinite(y1) and (y1 > y0):
        pad = max(1.0, 0.05 * (y1 - y0))
        ax.set_ylim(y0 - pad, y1 + pad)

    info_text = ax.text(
        0.01,
        0.02,
        "",
        transform=ax.transAxes,
        fontsize=10,
        ha="left",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.85),
    )

    if n >= 2 and widgets_module is not None:
        idx0 = int(np.argmin(np.abs(freq_mhz - np.mean(freq_mhz))))
        (m_peak,) = ax.plot([freq_mhz[idx0]], [p_dbm[idx0]], "o", color="red", ms=7)

        def set_idx(i: int) -> None:
            i = max(0, min(n - 1, int(i)))
            m_peak.set_data([freq_mhz[i]], [p_dbm[i]])
            info_text.set_text(
                f"f={freq_mhz[i]:.6f} MHz | P={p_dbm[i]:.2f} dBm | Index={i}"
            )

        def on_idx(change: dict) -> None:
            set_idx(change["new"])

        idx_slider = widgets_module.IntSlider(
            value=idx0,
            min=0,
            max=n - 1,
            step=1,
            description="Trace-Bin",
            continuous_update=False,
            style={"description_width": "initial"},
            layout=widgets_module.Layout(width="95%"),
        )

        btn_minus = widgets_module.Button(
            description="-1",
            tooltip="Marker um eine Position nach links",
            layout=widgets_module.Layout(width="70px"),
        )
        btn_plus = widgets_module.Button(
            description="+1",
            tooltip="Marker um eine Position nach rechts",
            layout=widgets_module.Layout(width="70px"),
        )

        def on_minus(_: Any) -> None:
            idx_slider.value = max(idx_slider.min, idx_slider.value - 1)

        def on_plus(_: Any) -> None:
            idx_slider.value = min(idx_slider.max, idx_slider.value + 1)

        btn_minus.on_click(on_minus)
        btn_plus.on_click(on_plus)
        idx_slider.observe(on_idx, names="value")

        set_idx(idx0)
        nav_row = widgets_module.HBox([btn_minus, btn_plus])
        display_fn(widgets_module.VBox([fig.canvas, idx_slider, nav_row]))
    elif n >= 2:
        idx0 = int(np.argmin(np.abs(freq_mhz - np.mean(freq_mhz))))
        ax.plot([freq_mhz[idx0]], [p_dbm[idx0]], "o", color="red", ms=7)
        info_text.set_text(
            f"f={freq_mhz[idx0]:.6f} MHz | P={p_dbm[idx0]:.2f} dBm | Index={idx0} | pip install ipywidgets"
        )
        fig.canvas.draw_idle()
        plt.show()
    else:
        info_text.set_text(
            f"f={freq_mhz[0]:.6f} MHz | P={p_dbm[0]:.2f} dBm" if n == 1 else "Keine Daten"
        )
        fig.canvas.draw_idle()
        plt.show()

    if n > 0:
        print(f"Punkte: {n}, f = {freq_mhz[0]:.4f} … {freq_mhz[-1]:.4f} MHz")
    if _ipy_interactive:
        plt.ion()


def mixer_merge_save(
    key: str,
    freqs: list,
    amps: list,
    rbw_hz: Any,
    idn: str,
    *,
    replay_file: Path,
) -> None:
    if replay_file.exists():
        data = load_replay_json(replay_file)
    else:
        data = {"meta": {"type": "fpc1500_sa_mixer", "version": 1}}
    data["idn"] = idn
    data[key] = {"freqs_hz": list(freqs), "amps": list(amps), "rbw_hz": rbw_hz}
    save_replay_json(replay_file, data)
    verify = load_replay_json(replay_file)
    counts: dict[str, int] = {}
    for k in ("spectrum_lo", "spectrum_if", "spectrum_rf"):
        blk = verify.get(k)
        counts[k] = len(blk.get("amps", [])) if isinstance(blk, dict) else 0
    print("Replay gespeichert:", replay_file.resolve())
    print("  Spektren im File (Anzahl Samples):", counts)
