"""SCPI / Messgeraete – gemeinsame Schnittstelle fuer Notebooks mit Bench-Instrumenten.

In den aktuellen ``09_01_LABOR-8-solution`` Notebooks werden keine SCPI-Befehle
genutzt; dieses Modul liefert eine schlanke, optionale Kapselung fuer spätere
Labs oder Kopien aus anderen Ordnern.

Installation (optional)::

    pip install pyvisa pyvisa-py

Beispiel::

    from lib.scpi import ScpiTcpInstrument
    inst = ScpiTcpInstrument("TCPIP0::192.168.1.10::inst0::INSTR")
    print(inst.query("*IDN?"))
"""

from __future__ import annotations

from typing import Any


try:
    import pyvisa  # type: ignore

    _HAS_PYVISA = True
except Exception:
    pyvisa = None  # type: ignore
    _HAS_PYVISA = False


def pyvisa_available() -> bool:
    return _HAS_PYVISA


class ScpiSession:
    """Minimaler SCPI-Wrapper (resource string wie bei NI-VISA)."""

    def __init__(self, resource: str, *, timeout_ms: int = 5000) -> None:
        if not _HAS_PYVISA:
            raise RuntimeError("pyvisa nicht installiert — pip install pyvisa pyvisa-py")
        self._rm = pyvisa.ResourceManager()
        self._inst = self._rm.open_resource(resource)
        self._inst.timeout = int(timeout_ms)

    def write(self, cmd: str) -> None:
        self._inst.write(cmd)

    def query(self, cmd: str) -> str:
        return self._inst.query(cmd).strip()

    def close(self) -> None:
        try:
            self._inst.close()
        except Exception:
            pass
        try:
            self._rm.close()
        except Exception:
            pass

    def __enter__(self) -> ScpiSession:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def quick_idn(resource: str) -> str:
    with ScpiSession(resource) as s:
        return s.query("*IDN?")
