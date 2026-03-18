# RTL-SDR im Lab 03_01 Übertragungskanal

## Treiber im Repo-Root (Windows 64-bit)

Der Treiber liegt im **Root des Repos** (KT-workspace):

```
KT-workspace/rtl-sdr-driver/
  librtlsdr.dll
  …
```

Das Skript `rtlsdr_spectrum_plot.py` bindet diesen Ordner beim Start automatisch in den DLL-Suchpfad ein – keine System-weite PATH-Anpassung nötig.

## Voraussetzungen

- **pyrtlsdr** installiert: `pip install pyrtlsdr`
- RTL-SDR-Stick per USB angeschlossen; unter Windows ggf. **Zadig** für den USB-Treiber des Sticks verwenden (libusb/WinUSB).

## Treiber-Pfad (librtlsdr.dll)

- **Skript** `rtlsdr_spectrum_plot.py`: Ermittelt das Repo-Root über `Path(__file__).parent.parent.parent` (KT-workspace) und hängt `rtl-sdr-driver` an `PATH` und `os.add_dll_directory()` – Treiber muss in **KT-workspace/rtl-sdr-driver** liegen.
- **Notebook** (z. B. `jupyter_labs/rtl_sdr_samples.ipynb`): Hat keine `__file__`-Pfadlogik. Dort die Zelle „Windows: Treiber-Pfad setzen“ **zuerst** ausführen; sie sucht den Ordner `rtl-sdr-driver` im aktuellen Verzeichnis oder in übergeordneten Ordnern. Dafür Jupyter am besten aus **KT-workspace** oder **lab_suite** starten (`cd KT-workspace` bzw. `cd lab_suite` → `jupyter notebook`), damit der Treiber gefunden wird.
