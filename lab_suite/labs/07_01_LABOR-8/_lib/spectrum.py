"""FFT-Fenster und einfache Spektrum-Helfer fuer SDR-Notebooks."""

from __future__ import annotations

import numpy as np


def fft_window(n: int, *, use_window: bool = True, kind: str = "hann") -> np.ndarray:
    if not use_window:
        return np.ones(n)
    if kind == "hann":
        return np.hanning(n)
    if kind == "hamming":
        return np.hamming(n)
    return np.ones(n)


def periodogram_psd_db(
    x: np.ndarray,
    fs_hz: float,
    n_fft: int,
    *,
    use_window: bool = True,
    window_kind: str = "hann",
    floor_db: float = -160.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Einseitige PSD-Schätzung [dB/Hz], Frequenzachse [Hz]."""
    x = np.asarray(x)
    n = min(int(n_fft), x.size)
    seg = x[:n]
    w = fft_window(n, use_window=use_window, kind=window_kind)
    xw = seg * w
    scale = np.sum(w**2) / fs_hz
    X = np.fft.fft(xw, n=n)
    psd = (np.abs(X) ** 2) / (fs_hz * scale)
    psd = psd[: n // 2 + 1]
    f = np.fft.fftfreq(n, d=1.0 / fs_hz)[: n // 2 + 1]
    psd_db = 10.0 * np.log10(np.maximum(psd, 10.0 ** (floor_db / 10.0)))
    return f, psd_db
