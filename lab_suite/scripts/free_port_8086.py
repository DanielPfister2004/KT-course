#!/usr/bin/env python3
"""
Port 8086 (Pluto Lab NiceGUI) freimachen – beendet Prozesse, die den Port belegen.

Verwendung (aus KT-workspace):
  python lab_suite/scripts/free_port_8086.py

Danach erneut: python -m lab_suite.pluto_lab
"""
from __future__ import annotations

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

sys.argv = ["check_ports.py", "8086", "-k"]
from check_ports import main  # noqa: E402

if __name__ == "__main__":
    print("Port 8086 (Pluto Lab) freigeben …")
    main()
