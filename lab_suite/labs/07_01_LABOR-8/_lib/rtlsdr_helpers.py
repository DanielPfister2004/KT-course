"""RTL-SDR: DLL-Pfad und Capture (optional, nur wenn pyrtlsdr installiert)."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np


def setup_rtlsdr_driver_path(verbose: bool = True) -> Path | None:
    """Sucht ``rtl-sdr-driver`` mit ``librtlsdr.dll`` aufwärts ab cwd."""
    driver_dir = None
    for p in [Path.cwd()] + list(Path.cwd().parents):
        cand = p / "rtl-sdr-driver"
        if cand.exists() and (cand / "librtlsdr.dll").exists():
            driver_dir = cand
            break

    if driver_dir is not None:
        os.environ["PATH"] = str(driver_dir) + os.pathsep + os.environ.get("PATH", "")
        try:
            os.add_dll_directory(str(driver_dir))
        except Exception:
            pass
        if verbose:
            print("RTL-SDR Treiber gefunden:", driver_dir)
    elif verbose:
        print("Hinweis: rtl-sdr-driver nicht gefunden, ggf. Fallback-Signal wird genutzt.")

    return driver_dir


def capture_rtlsdr(
    center_hz: float,
    fs_hz: float,
    gain_db: float,
    total_samples: int,
    *,
    setup_driver: bool = True,
) -> np.ndarray:
    if setup_driver:
        setup_rtlsdr_driver_path()
    try:
        from rtlsdr import RtlSdr
    except Exception as ex:
        raise RuntimeError(f"rtlsdr nicht verfügbar: {ex}") from ex

    sdr = RtlSdr()
    try:
        sdr.sample_rate = fs_hz
        sdr.center_freq = center_hz
        sdr.gain = gain_db
        iq = sdr.read_samples(int(total_samples)).astype(np.complex64)
        return iq
    finally:
        sdr.close()


def capture_iq_or_fallback(
    center_hz: float,
    fs_hz: float,
    gain_db: float,
    total_samples: int,
    *,
    f_if_fallback_hz: float = 0.0,
    f_mod_hz: float = 1000.0,
    am_depth: float = 0.6,
    noise_std: float = 0.02,
    setup_driver: bool = True,
) -> np.ndarray:
    """RTL-SDR Capture oder synthetisches AM-IQ (wie Notebook ``4-ASK-SDR-demod-iq``)."""
    if setup_driver:
        setup_rtlsdr_driver_path(verbose=False)
    try:
        return capture_rtlsdr(center_hz, fs_hz, gain_db, total_samples, setup_driver=False)
    except Exception as ex:
        print("RTL-SDR nicht verfügbar, nutze synthetischen Fallback:", ex)
        n = int(total_samples)
        t = np.arange(n, dtype=np.float64) / fs_hz
        env = 1.0 + am_depth * np.cos(2 * np.pi * f_mod_hz * t)
        x = env * np.exp(1j * 2 * np.pi * f_if_fallback_hz * t)
        noise = noise_std * (
            np.random.randn(n) + 1j * np.random.randn(n)
        )
        return (x + noise).astype(np.complex64)
