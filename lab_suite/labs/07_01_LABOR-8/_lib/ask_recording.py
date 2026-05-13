"""Speichern/Laden von ``ask_recording_v1`` (JSON zwischen Notebook 1 und 2/3)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


FORMAT_KEY = "ask_recording_v1"


@dataclass
class AskRecording:
    """Normalisierte Sicht auf recordings/ask.json."""

    fs_hz: float
    f_carrier_hz: float
    phi_carrier_rad: float
    U_c: float
    modulation_index: float
    prbs_order: int
    samples_per_bit: int
    bit_rate_hz: float
    n_bits: int
    n_samples: int
    samples: np.ndarray
    bits: np.ndarray
    raw: dict[str, Any]


def save_ask_recording_v1(
    path: Path,
    *,
    fs_hz: float,
    f_carrier_hz: float,
    phi_carrier_rad: float,
    U_c: float,
    modulation_index: float,
    prbs_order: int,
    samples_per_bit: int,
    bit_rate_hz: float,
    n_bits: int,
    n_samples: int,
    bits: np.ndarray,
    samples: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    recording = {
        "format": FORMAT_KEY,
        "fs_hz": float(fs_hz),
        "f_carrier_hz": float(f_carrier_hz),
        "phi_carrier_rad": float(phi_carrier_rad),
        "U_c": float(U_c),
        "modulation_index": float(modulation_index),
        "prbs_order": int(prbs_order),
        "samples_per_bit": int(samples_per_bit),
        "bit_rate_hz": float(bit_rate_hz),
        "n_bits": int(n_bits),
        "n_samples": int(n_samples),
        "bits": np.asarray(bits).astype(int).tolist(),
        "samples": np.asarray(samples, dtype=np.float32).tolist(),
    }
    path.write_text(json.dumps(recording), encoding="utf-8")


def load_ask_recording_v1(path: Path) -> AskRecording:
    if not path.exists():
        raise FileNotFoundError(f"{path} nicht gefunden.")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("format") != FORMAT_KEY:
        pass  # ältere Dateien ohne format: trotzdem versuchen

    fs_hz = float(raw["fs_hz"])
    samples_per_bit = int(raw["samples_per_bit"])
    R_b = float(raw.get("bit_rate_hz", fs_hz / samples_per_bit))

    rec = AskRecording(
        fs_hz=fs_hz,
        f_carrier_hz=float(raw["f_carrier_hz"]),
        phi_carrier_rad=float(raw.get("phi_carrier_rad", 0.0)),
        U_c=float(raw.get("U_c", 1.0)),
        modulation_index=float(raw["modulation_index"]),
        prbs_order=int(raw.get("prbs_order", 15)),
        samples_per_bit=samples_per_bit,
        bit_rate_hz=R_b,
        n_bits=int(raw["n_bits"]),
        n_samples=int(raw["n_samples"]),
        samples=np.asarray(raw["samples"], dtype=np.float64),
        bits=np.asarray(raw["bits"], dtype=np.int8),
        raw=raw,
    )
    return rec
