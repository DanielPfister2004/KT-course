#!/usr/bin/env python3
"""
RTL-SDR Spektrum mit Matplotlib-Animation und einstellbarer Mittenfrequenz.

Liest kontinuierlich IQ-Daten vom RTL-SDR, berechnet das Leistungsdichtespektrum (FFT)
und zeigt es als Animation. Die Mittenfrequenz lässt sich per Slider ändern.

Voraussetzung: RTL-SDR angeschlossen, pyrtlsdr installiert (pip install pyrtlsdr).
Unter Windows ggf. Zadig-Treiber für den Stick nötig.

Ausführen (aus lab_suite):  python labs/03_01_Übertragungskanal/rtlsdr_spectrum_plot.py
"""
from __future__ import annotations

import os
from pathlib import Path
import time

_driver_dir = None
for p in [Path.cwd()] + list(Path.cwd().parents):
    candidate = p / "rtl-sdr-driver"
    if candidate.exists() and (candidate / "librtlsdr.dll").exists():
        _driver_dir = candidate
        break
if _driver_dir is not None:
    _path = str(_driver_dir)
    os.environ["PATH"] = _path + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(_path)
    print("RTL-SDR Treiber gefunden:", _driver_dir)
else:
    print("Hinweis: rtl-sdr-driver (librtlsdr.dll) nicht gefunden.")
    while True:
        time.sleep(1)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider

try:
    from rtlsdr import RtlSdr
except ImportError as e:
    try:
        from pyrtlsdr import RtlSdr
    except ImportError:
        pass
    msg = str(e).lower()
    if "librtlsdr" in msg or "loading" in msg:
        raise SystemExit(
            "pyrtlsdr ist installiert, aber die Bibliothek librtlsdr konnte nicht geladen werden.\n"
            "Unter Windows: RTL-SDR Treiber (z. B. mit Zadig) installieren und ggf. librtlsdr-DLL im Pfad."
        ) from e
    raise SystemExit("pyrtlsdr nicht installiert. Bitte: pip install pyrtlsdr") from e

# =============================================================================
# Parameter
# =============================================================================

SAMPLE_RATE_HZ = 2.4e6      # Abtastrate (z. B. 2,4 MS/s)
FFT_SIZE = 2048             # FFT-Länge für Spektrum

# Slider: Mittenfrequenz in MHz (typischer RTL-SDR Bereich ca. 24–1766 MHz)
CENTER_FREQ_MHZ_MIN = 50.0
CENTER_FREQ_MHZ_MAX = 1700.0
CENTER_FREQ_MHZ_INIT = 100.0  # Start z. B. 100 MHz

# Slider: Gain in dB (Verstärkung des Empfängers)
GAIN_DB_MIN = 0.0
GAIN_DB_MAX = 50.0
GAIN_DB_INIT = 20.0

# =============================================================================
# RTL-SDR öffnen
# =============================================================================

try:
    sdr = RtlSdr()
except Exception as e:
    raise SystemExit(f"RTL-SDR konnte nicht geöffnet werden: {e}") from e

sdr.sample_rate = SAMPLE_RATE_HZ
sdr.gain = GAIN_DB_INIT
sdr.center_freq = CENTER_FREQ_MHZ_INIT * 1e6

# =============================================================================
# Matplotlib: Figure, Spektrum-Achse, Slider
# =============================================================================

fig, ax = plt.subplots(figsize=(10, 5))
plt.subplots_adjust(bottom=0.22)

# Frequenzachse (wird in update gesetzt; hier Platzhalter)
freq_mhz = np.fft.fftshift(np.fft.fftfreq(FFT_SIZE, 1 / SAMPLE_RATE_HZ)) / 1e6
power_dB = np.zeros(FFT_SIZE)
(line,) = ax.plot(freq_mhz, power_dB, color="C0", linewidth=0.8)
ax.set_xlabel("Frequenz relativ zur Mittenfrequenz (MHz)")
ax.set_ylabel("Leistung (dB)")
ax.set_title("RTL-SDR Spektrum")
ax.grid(True, alpha=0.5)
ax.set_ylim(-60, 60)

# Slider für Mittenfrequenz (in MHz)
ax_freq_slider = plt.axes([0.2, 0.08, 0.6, 0.03])
freq_slider = Slider(
    ax_freq_slider,
    "Mittenfrequenz (MHz)",
    CENTER_FREQ_MHZ_MIN,
    CENTER_FREQ_MHZ_MAX,
    valinit=CENTER_FREQ_MHZ_INIT,
    valstep=0.1,
)

# Slider für Gain (dB)
ax_gain_slider = plt.axes([0.2, 0.03, 0.6, 0.03])
gain_slider = Slider(
    ax_gain_slider,
    "Gain (dB)",
    GAIN_DB_MIN,
    GAIN_DB_MAX,
    valinit=GAIN_DB_INIT,
    valstep=1.0,
)


def on_freq_slider_change(val_mhz: float) -> None:
    """Slider-Änderung: Mittenfrequenz des SDR setzen."""
    sdr.center_freq = val_mhz * 1e6
    ax.set_title(f"RTL-SDR Spektrum — Mitte: {val_mhz:.1f} MHz, Gain: {gain_slider.val:.0f} dB")


def on_gain_slider_change(val_dB: float) -> None:
    """Slider-Änderung: Gain des Empfängers setzen."""
    sdr.gain = val_dB
    ax.set_title(f"RTL-SDR Spektrum — Mitte: {freq_slider.val:.1f} MHz, Gain: {val_dB:.0f} dB")


freq_slider.on_changed(on_freq_slider_change)
gain_slider.on_changed(on_gain_slider_change)
ax.set_title(f"RTL-SDR Spektrum — Mitte: {CENTER_FREQ_MHZ_INIT:.1f} MHz, Gain: {GAIN_DB_INIT:.0f} dB")


def update_frame(_frame: int) -> tuple:
    """Eine Animations-Frame: IQ lesen, FFT, Spektrum in dB, Plot aktualisieren."""
    try:
        # Mehr Samples lesen als FFT_SIZE, dann mittig verwenden (reduziert Randeffekte)
        num_read = FFT_SIZE * 2
        iq = sdr.read_samples(num_read)
        iq = iq[-FFT_SIZE:]  # letzte FFT_SIZE Samples
    except Exception:
        return (line,)

    # Leistungsdichtespektrum: FFT, Betrag quadrieren, in dB
    window = np.hanning(FFT_SIZE)
    spectrum = np.fft.fft(iq * window)
    power = np.abs(spectrum) ** 2
    power_dB = 10 * np.log10(power + 1e-20)
    power_dB = np.fft.fftshift(power_dB)

    # Frequenzachse relativ zur Mittenfrequenz (in MHz)
    freq_rel_mhz = np.fft.fftshift(np.fft.fftfreq(FFT_SIZE, 1 / SAMPLE_RATE_HZ)) / 1e6

    line.set_data(freq_rel_mhz, power_dB)
    ax.set_xlim(freq_rel_mhz.min(), freq_rel_mhz.max())
    return (line,)


anim = FuncAnimation(fig, update_frame, interval=100, blit=True, cache_frame_data=False)

try:
    plt.show()
finally:
    sdr.close()
