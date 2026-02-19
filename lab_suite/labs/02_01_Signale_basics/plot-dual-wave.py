#!/usr/bin/env python3
"""
Zwei Sinussignale in einem gemeinsamen Plot.

Zeigt: zweites Signal mit eigenen Parametern (doppelte Frequenz, halbe Amplitude,
30° Phasenverschiebung) und wie mehrere Kurven in einem Matplotlib-Plot
zusammengeführt werden.

Ausführen (aus lab_suite):  python labs/01_01_Signale_basics/plot-dual-wave.py
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Gemeinsame Abtastparameter (für beide Signale)
# =============================================================================

SAMPLE_RATE_HZ = 100.0   # Abtastrate in Hz
DURATION_S = 2.0         # Dauer in Sekunden

# =============================================================================
# Signal 1 – erster Sinus
# =============================================================================

FREQ1_HZ = 2.0           # Frequenz in Hz
AMPLITUDE1 = 1.0         # Amplitude
PHASE1_DEG = 0.0         # Phasenverschiebung in Grad (0 = kein Versatz)

# =============================================================================
# Signal 2 – zweiter Sinus (doppelte Frequenz, halbe Amplitude, 30° Phase)
# =============================================================================

FREQ2_HZ = 2.0 * FREQ1_HZ       # doppelte Frequenz
AMPLITUDE2 = 0.5 * AMPLITUDE1    # halbe Amplitude
PHASE2_DEG = 30.0               # 30° Phasenverschiebung (nach links im Plot)

# =============================================================================
# Zeitachse und Signale erzeugen
# =============================================================================

num_samples = int(SAMPLE_RATE_HZ * DURATION_S)
t = np.linspace(0, DURATION_S, num_samples, endpoint=False)

# Phase von Grad in Bogenmaß (Mathematik: sin(2*pi*f*t + phi))
phi1_rad = np.deg2rad(PHASE1_DEG)
phi2_rad = np.deg2rad(PHASE2_DEG)

# x(t) = A * sin(2*pi*f*t + phi)
signal1 = AMPLITUDE1 * np.sin(2 * np.pi * FREQ1_HZ * t + phi1_rad)
signal2 = AMPLITUDE2 * np.sin(2 * np.pi * FREQ2_HZ * t + phi2_rad)

# =============================================================================
# Beide Signale in einem gemeinsamen Plot
# =============================================================================

plt.figure(figsize=(10, 4))
plt.plot(t, signal1, color="C0", linewidth=1.5, label=f"Signal 1: f={FREQ1_HZ} Hz, A={AMPLITUDE1}")
plt.plot(t, signal2, color="C1", linewidth=1.5, label=f"Signal 2: f={FREQ2_HZ} Hz, A={AMPLITUDE2}, φ={PHASE2_DEG}°")
plt.xlabel("Zeit (s)")
plt.ylabel("Amplitude")
plt.title("Zwei Sinussignale in einem Plot")
plt.grid(True, alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()
