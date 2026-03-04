# Tonausgabe im Notebook und Morse-Übung

## Kann man im Notebook Ton am PC-Lautsprecher ausgeben?

**Ja.** In Jupyter Notebooks geht das mit **`IPython.display.Audio`**:

- **Eingabe:** Ein 1D-NumPy-Array (Waveform) + Abtastrate.
- **Ausgabe:** Ein eingebetteter Audio-Player; Klick auf Play → Ton über PC-Lautsprecher/Kopfhörer.

Es werden **keine zusätzlichen Bibliotheken** benötigt (außer `numpy`, das im Kurs schon verwendet wird). `IPython.display` ist Teil der Jupyter/IPython-Umgebung.

### Minimalbeispiel (im Notebook ausführen)

```python
import numpy as np
import IPython.display as ipd

sr = 22050   # Abtastrate in Hz
dauer = 0.3  # Sekunden
t = np.linspace(0, dauer, int(sr * dauer), endpoint=False)
ton = 0.3 * np.sin(2 * np.pi * 440 * t)   # 440 Hz Sinus

ipd.Audio(ton, rate=sr)   # Player erscheint, Play klicken
# Optional: autoplay=True für automatisches Abspielen
```

---

## Morsezeichen ausgeben – passt das?

**Ja.** Morse eignet sich gut:

1. **Dictionary:** Zeichen (Buchstabe/Ziffer) → Morse-Code (z. B. `"A"` → `".-"`). Das ist genau die typische Dict-Anwendung: Lookup-Tabelle.
2. **Ton:** Kurzer Ton = Punkt (dit), langer Ton = Strich (dah), Stille = Pause. Ein einziger langer Ton-Array kann aus vielen kleinen Segmenten (Sinus + Stille) zusammengebaut werden.
3. **Standard-Timing (relativ):** Punkt = 1 Einheit, Strich = 3, Pause zwischen Zeichen im Buchstaben = 1, zwischen Buchstaben = 3, zwischen Wörtern = 7. Die absolute Dauer (z. B. 0.05 s pro Einheit) ist frei wählbar.

### Übungs-Idee für Dictionaries

- **Dictionary** `zeichen_zu_morse`: z. B. `{"A": ".-", "B": "-...", ...}`.
- Text Zeichen für Zeichen durchgehen, mit `zeichen_zu_morse.get(zeichen, "")` den Morse-String holen (unbekannte Zeichen überspringen).
- Aus der Morse-String-Folge einen großen Waveform-Array bauen (für jeden Punkt/Strich ein Sinus-Segment, dazwischen Stille).
- Am Ende einmal `IPython.display.Audio(waveform, rate=sr)` aufrufen → Morse erklingt.

So verbindet die Übung: **Dict-Lookup**, **Strings**, **Schleifen** und **NumPy-Arrays** (optional schon aus früheren Kapiteln).

---

## Hinweise

- **Lautstärke:** Amplitude z. B. `0.2`–`0.4`, damit es nicht zu laut ist.
- **Frequenz:** Typisch 600–800 Hz für Morse; 440 Hz funktioniert ebenfalls.
- **Browser/Umgebung:** Der Ton wird im Browser abgespielt (Jupyter im Browser). Lautsprecher/Headset müssen entsperrt und nicht stumm sein.

Ein konkretes Vertiefungs- oder Übungs-Notebook (z. B. `16_Morse_Code_Ton.ipynb`) kann darauf aufbauen: zuerst Dict und Text→Morse-String, dann optional Tonerzeugung und `Audio()`.
