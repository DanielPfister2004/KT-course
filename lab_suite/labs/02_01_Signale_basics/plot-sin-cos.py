#!/usr/bin/env python3
"""
Sinus und Cosinus: np.sin() und np.cos() sowie Umrechnung per Phasenverschiebung.

Mathematik: Cosinus und Sinus unterscheiden sich nur um eine Phase von 90° (π/2):
  cos(θ) = sin(θ + π/2)    bzw.    sin(θ) = cos(θ − π/2)

In NumPy: np.cos(x) und np.sin(x) für Arrays x. Umrechnung z. B. cos als sin mit
Phase: np.sin(x + np.pi/2) liefert dasselbe wie np.cos(x).

Ausführen (aus lab_suite):  python labs/01_01_Signale_basics/plot-sin-cos.py
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Parameter
# =============================================================================

FREQUENCY_HZ = 1.0
SAMPLE_RATE_HZ = 100.0
DURATION_S = 2.0

num_samples = int(SAMPLE_RATE_HZ * DURATION_S)
t = np.linspace(0, DURATION_S, num_samples, endpoint=False)

# Winkel (Phase) als Funktion der Zeit: 2*pi*f*t
angle_rad = 2 * np.pi * FREQUENCY_HZ * t

# =============================================================================
# Sinus und Cosinus – direkt mit np.sin und np.cos
# =============================================================================

signal_sin = np.sin(angle_rad)
signal_cos = np.cos(angle_rad)

# =============================================================================
# Umrechnung: Cosinus als Sinus mit 90° (π/2) Phasenverschiebung
# cos(θ) = sin(θ + π/2)
# =============================================================================

signal_cos_from_sin = np.sin(angle_rad + np.pi / 2)   # sollte gleich signal_cos sein

# Kontrolle (optional): max. Abweichung sollte nahe 0 sein
# print("Max. Differenz cos vs sin(θ+π/2):", np.max(np.abs(signal_cos - signal_cos_from_sin)))

# =============================================================================
# Plot: Sinus und Cosinus in einem gemeinsamen Diagramm
# =============================================================================

plt.figure(figsize=(10, 4))
plt.plot(t, signal_sin, color="C0", linewidth=1.5, label="sin(2πft)")
plt.plot(t, signal_cos, color="C1", linewidth=1.5, linestyle="--", label="cos(2πft)")
plt.xlabel("Zeit (s)")
plt.ylabel("Amplitude")
plt.title("Sinus und Cosinus (cos = sin mit 90° Phase)")
plt.grid(True, alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()

"""
plt.tight_layout() passt die Abstände und Ränder der aktuellen Figure so an, dass:
Nichts abgeschnitten wird: Achsenbeschriftungen, Titel, Legende und Ticks bleiben sichtbar und kollidieren nicht mit dem Figure-Rand oder anderen Elementen.
Platz genutzt wird: Die Subplots werden etwas enger und gleichmäßiger verteilt, ohne dass du Ränder und Abstände per Hand setzen musst.
Intern berechnet Matplotlib dafür die benötigten Größen (z. B. für Labels) und ändert subplots_adjust (left, right, top, bottom, wspace, hspace).
Typischer Einsatz: nach dem Aufbau des Plots, vor plt.show(), vor allem bei mehreren Subplots oder langen Labels. Bei einer einzelnen, einfachen Axes ist der Effekt oft gering, schadet aber nicht.
Optional: Mit plt.tight_layout(pad=1.2) kannst du den Abstand zwischen Subplots vergrößern.
"""