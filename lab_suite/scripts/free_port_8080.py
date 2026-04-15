#!/usr/bin/env python3
"""
Port 8082 (App-Launcher) freimachen – beendet verwaiste Prozesse, die den Port belegen.

Verwendung (aus KT-workspace):
  python lab_suite/scripts/free_port_8080.py

Danach kann der Launcher wieder gestartet werden (z. B. .\start_launcher.ps1).
"""
from __future__ import annotations

import os
import sys

# Gleiches Verzeichnis für Import von check_ports
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

# check_ports mit Port 8080 und --kill aufrufen
sys.argv = ["check_ports.py", "8080", "-k"]
from check_ports import main  # noqa: E402

if __name__ == "__main__":
    print("Port 8080 (App-Launcher) freigeben …")
    main()
