#!/usr/bin/env python3
"""
Matplotlib-Demo: Sinussignal erzeugen und anzeigen.

Dieses Skript zeigt den typischen Ablauf:
  1. Signalparameter am Anfang definieren (gut lesbar für Änderungen)
  2. Zeitachse und Sinussignal mit NumPy erzeugen
  3. Mit Matplotlib in einem Fenster plotten

Ausführen (aus lab_suite):  python labs/01_01_Signale_basics/matplotlib-demo.py
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Signalparameter – hier anpassen (für Studierende gut sichtbar)
# =============================================================================

# Frequenz des Sinus in Hz (wie oft pro Sekunde eine volle Schwingung)
FREQUENCY_HZ = 2.0

# Amplitude (maximale Auslenkung des Signals, Einheit z. B. Volt oder normiert)
AMPLITUDE = 1.0

# Abtastrate in Hz (wie viele Werte pro Sekunde wir aufnehmen)
# Sollte mindestens doppelt so groß wie FREQUENCY_HZ sein (Abtasttheorem)
SAMPLE_RATE_HZ = 100.0

# Dauer des Signals in Sekunden
DURATION_S = 2.0

# =============================================================================
# Zeitachse und Sinussignal erzeugen
# =============================================================================

# Anzahl der Abtastwerte
num_samples = int(SAMPLE_RATE_HZ * DURATION_S)

# Zeitpunkte: von 0 bis (DURATION_S - 1/SAMPLE_RATE_HZ), gleichmäßig verteilt
t = np.linspace(0, DURATION_S, num_samples, endpoint=False)

# Sinussignal:  x(t) = A * sin(2 * pi * f * t)
# np.sin erwartet Winkel im Bogenmaß; 2*pi*f*t liefert die Phase pro Zeit t
signal = AMPLITUDE * np.sin(2 * np.pi * FREQUENCY_HZ * t)

# =============================================================================
# Mit Matplotlib plotten
# =============================================================================

plt.figure(figsize=(10, 4))
plt.plot(t, signal, color="C0", linewidth=1.5, label=f"sin, f={FREQUENCY_HZ} Hz")
plt.xlabel("Zeit (s)")
plt.ylabel("Amplitude")
plt.title("Sinussignal (Matplotlib-Demo)")
plt.grid(True, alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()
