"""PRBS-7 / PRBS-15 Maximal-Length-Sequenzen (LSB out, Shift-Register wie in den Notebooks)."""

from __future__ import annotations

import numpy as np


def prbs_bits(n: int, order: int = 15, seed: int = 0x7FAC) -> np.ndarray:
    """Erzeugt die ersten ``n`` Bits einer PRBS-``order`` Sequenz (uint8 0/1)."""
    if order == 7:
        taps = (6, 5)
        mask = 0x7F
        seed = seed & mask if seed else 0x7F
    elif order == 15:
        taps = (14, 13)
        mask = 0x7FFF
        seed = seed & mask if seed else 0x7FFF
    else:
        raise ValueError("order must be 7 or 15")

    reg = int(seed)
    bits = np.empty(int(n), dtype=np.uint8)
    t1, t2 = taps
    for i in range(int(n)):
        bits[i] = reg & 1
        fb = ((reg >> t1) ^ (reg >> t2)) & 1
        reg = ((reg << 1) | fb) & mask
    return bits
