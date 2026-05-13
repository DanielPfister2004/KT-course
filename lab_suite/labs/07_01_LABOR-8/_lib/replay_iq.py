"""IQ-Replays als JSON (kompatibel zu FM-/AM-SDR Notebooks in diesem Labor)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def save_replay_complex_json(
    path: Path,
    iq: np.ndarray,
    fs_hz: float,
    *,
    center_freq_hz: float | None = None,
    gain_db: float | None = None,
    meta: dict[str, Any] | None = None,
    indent: int | None = 2,
    key_style: str = "iq_re_im",
) -> None:
    """Speichert komplexes IQ als JSON.

    key_style:
      - ``iq_re_im``: Schlüssel ``iq_re`` / ``iq_im`` (wie 4-ASK-SDR)
      - ``iq_real_imag``: Schlüssel ``iq_real`` / ``iq_imag`` (wie ältere FM-Replay-Zellen)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    z = np.asarray(iq).astype(np.complex64).ravel()
    re = np.real(z).astype(np.float32)
    im = np.imag(z).astype(np.float32)

    if key_style == "iq_real_imag":
        payload: dict[str, Any] = {
            "fs_hz": float(fs_hz),
            "iq_real": re.tolist(),
            "iq_imag": im.tolist(),
        }
    else:
        payload = {
            "fs_hz": float(fs_hz),
            "iq_re": re.tolist(),
            "iq_im": im.tolist(),
        }

    if center_freq_hz is not None:
        payload["center_freq_hz"] = float(center_freq_hz)
    if gain_db is not None:
        payload["gain_db"] = float(gain_db)
    if meta:
        payload["meta"] = meta

    path.write_text(json.dumps(payload, indent=indent), encoding="utf-8")


def load_replay_complex_json(path: Path) -> tuple[np.ndarray, float, dict[str, Any]]:
    """Lädt IQ; erkennt automatisch ``iq_re``/``iq_im`` oder ``iq_real``/``iq_imag``."""
    raw = json.loads(path.read_text(encoding="utf-8"))

    if "iq_re" in raw and "iq_im" in raw:
        re = np.asarray(raw["iq_re"], dtype=np.float32)
        im = np.asarray(raw["iq_im"], dtype=np.float32)
    elif "iq_real" in raw and "iq_imag" in raw:
        re = np.asarray(raw["iq_real"], dtype=np.float32)
        im = np.asarray(raw["iq_imag"], dtype=np.float32)
    else:
        raise KeyError("Replay-JSON braucht iq_re/iq_im oder iq_real/iq_imag")

    fs_hz = float(raw.get("fs_hz", raw.get("sample_rate_hz", 0.0)))
    iq = (re + 1j * im).astype(np.complex64)
    return iq, fs_hz, raw


def save_replay_am_sdr_v1(
    path: Path,
    iq: np.ndarray,
    *,
    sample_rate_hz: float,
    center_freq_hz: float,
    gain_db: float,
) -> None:
    """Format wie in ``4-ASK-SDR-demod-iq.ipynb`` (meta type am_sdr_iq)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    z = np.asarray(iq).astype(np.complex64).ravel()
    data = {
        "meta": {"type": "am_sdr_iq", "version": 1},
        "sample_rate_hz": float(sample_rate_hz),
        "center_freq_hz": float(center_freq_hz),
        "gain_db": float(gain_db),
        "iq_re": np.real(z).astype(float).tolist(),
        "iq_im": np.imag(z).astype(float).tolist(),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_replay_am_sdr_v1(path: Path) -> np.ndarray:
    """Nur IQ-Vektor (kompatibel zur bisherigen ``load_replay_iq``)."""
    iq, _, _ = load_replay_complex_json(path)
    return iq
