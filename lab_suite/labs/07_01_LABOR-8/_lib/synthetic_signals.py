"""Synthetische Testsignale (FM-artig) fuer SDR-Fallbacks."""

from __future__ import annotations

import numpy as np


def synthetic_fm_fallback(fs_hz: float, total_samples: int) -> np.ndarray:
    """Wie im Notebook ``5-FSK-SDR-demod``: FM mit sinusfoermiger Modulation."""
    t = np.arange(total_samples) / fs_hz
    f_if = 35_000.0
    f_m = 1_000.0
    delta_f = 3_000.0
    u = np.cos(2 * np.pi * f_m * t)
    int_u = np.cumsum(u) / fs_hz
    phase = 2 * np.pi * f_if * t + 2 * np.pi * delta_f * int_u
    z = np.exp(1j * phase)
    return z.astype(np.complex64)
