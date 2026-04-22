#!/usr/bin/env python3
"""
RTL-SDR Spektrum und FM-Demod (Phase-Diskriminator)

Liest kontinuierlich IQ-Daten vom RTL-SDR, berechnet das Leistungsdichtespektrum (FFT)
und zeigt es als Animation. Darueber hinaus wird ein einfacher FM-Demodulator
(Phase-Diskriminator auf Basis von `angle(iq[n]*conj(iq[n-1]))`) berechnet und optional
als Audio-Zeitverlauf gezeichnet.

Voraussetzung: RTL-SDR angeschlossen, pyrtlsdr installiert (pip install pyrtlsdr).
Unter Windows ggf. Zadig-Treiber für den Stick nötig.

Chunk-Grenzen brauchen Zustand (IQ-Übergang, Filter zi). Zusätzlich: Wenn die GUI seltener
liest als SAMPLE_RATE_HZ, staut/stirbt der USB-Puffer — es fehlen dann **massenhaft IQ-Samples**
zwischen zwei read_samples (Phasensprünge im Demod). Daher: eigener Lese-/Demod-Thread in
Volllast; die Animation zeigt nur noch den gemeinsamen Puffer.

Lautsprecher-Hörcheck: standardmäßig **ein** (sounddevice). Ohne Ton: ``python rtlsdr_fm.py --no-audio``

Sample-Rate erzwingen (ein Treiber-Versuch, z. B. nach Access-Violation): ``python rtlsdr_fm.py --rate=256000``

**IQ verlustfrei?** Nur wenn die Verarbeitung **durchschnittlich mindestens mit Fs** mitkommt. Ein RAM-Puffer
kann **kurze** Jitter ausgleichen; dauerhaft zu langsame FFT/Demod → USB-Überlauf → verworfene Samples
**(unvermeidbar in Software)**. Optionen: ``--no-spectrum`` / ``--spectrum-every=N``, niedrigere Fs,
weniger CPU-Last, oder Aufnahme mit ``rtl_sdr``/Soapy/GNU Radio und Offline-Demod.

Performance: ``python rtlsdr_fm.py --spectrum-every=20`` (FFT seltener). Nur Demod/Ton: ``--no-spectrum``.
"""
from __future__ import annotations

import math
import os
import sys
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

import threading

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from scipy.signal import resample_poly, butter, sosfilt, sosfilt_zi, firwin, lfilter, lfilter_zi

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

try:
    import sounddevice as sd
except ImportError:
    sd = None  # type: ignore[assignment, misc]


def _parse_spectrum_options() -> tuple[bool, int]:
    """``--no-spectrum`` schaltet FFT aus; ``--spectrum-every=12`` nur jedes N-te Block."""
    enable = "--no-spectrum" not in sys.argv
    every = 12
    for a in sys.argv:
        if a.startswith("--spectrum-every="):
            try:
                every = max(1, int(a.split("=", 1)[1].strip()))
            except ValueError:
                pass
    return enable, every


FM_ENABLE_SPECTRUM, FM_SPECTRUM_EVERY_N_BLOCKS = _parse_spectrum_options()


def _parse_cli_or_env_rate_hz() -> float | None:
    """Eine feste Rate erzwingen: ``python rtlsdr_fm.py --rate=256000`` oder Env ``RTLSRD_FM_RATE``."""
    for i, a in enumerate(sys.argv):
        if a.startswith("--rate="):
            try:
                return float(a.split("=", 1)[1].strip())
            except ValueError:
                pass
        if a == "--rate" and i + 1 < len(sys.argv):
            try:
                return float(sys.argv[i + 1].strip())
            except ValueError:
                pass
    env = os.environ.get("RTLSRD_FM_RATE", "").strip()
    if env:
        return float(env)
    return None


# =============================================================================
# Parameter
# =============================================================================

# librtlsdr: niedriges Band ca. 225k–300k, hohes ab ~900k; 384k oft ungültig (-22).
# Mehrere fehlgeschlagene set_sample_rate-Aufrufe können unter Windows zu Access
# Violation führen — daher **256k zuerst** (häufig stabil), optional nur eine Rate:
_cli_rate = _parse_cli_or_env_rate_hz()
if _cli_rate is not None:
    SDR_RATE_CANDIDATES_HZ = (_cli_rate,)
else:
    SDR_RATE_CANDIDATES_HZ = (
        256_000.0,  # 256/8=32k → 48k Audio mit 3/2; oft zuverlässig
        288_000.0,  # 288/8=36k → 48k mit 4/3
        384_000.0,  # 8×48k wenn Stick mitspielt
        480_000.0,  # Zwischenband — oft nicht setzbar
        1_024_000.0,  # hohes Band
    )
# Wird nach erfolgreichem rtlsdr_set_sample_rate gesetzt:
SAMPLE_RATE_HZ = 256_000.0
FFT_SIZE = 2048             # FFT-Länge für Spektrum

# Slider: Mittenfrequenz in MHz (hier UKW/Funkband für Test)
# In dieser Laborübung begrenzen wir auf 88–108 MHz.
CENTER_FREQ_MHZ_MIN = 88.0
CENTER_FREQ_MHZ_MAX = 108.0
CENTER_FREQ_MHZ_INIT = 100.0  # Start z. B. 100 MHz

# Slider: Gain in dB (Verstärkung des Empfängers)
GAIN_DB_MIN = 0.0
GAIN_DB_MAX = 50.0
GAIN_DB_INIT = 20.0

# =============================================================================
# FM-Demod Parameter
# =============================================================================
FM_DEMOD_DECIM = 8               # Dezimationsfaktor fuer Audio
FM_AUDIO_PLOT_SAMPLES = 4096     # Laenge des Audio-Rolling-Puffers (FFT/Debug)
# Nur so viele Samples im unteren Plot: bei 48 kS/s sind 960 Samples = 20 ms
# => ca. 20 Zyklen bei 1 kHz — die Sinusform bleibt erkennbar (statt ~85 Zyklen).
FM_AUDIO_DISPLAY_SAMPLES = 960
FM_AUDIO_YLIM_HZ = 50_000.0     # Fixe Skalierung (Audio in Hz-Offset); verhindert störendes Autoscale
FM_AUDIO_AUTO_YLIM = False       # Autoscale aus (stabiler Vergleich bei großem Hub)
FM_AUDIO_GAIN = 1.0             # Skalierung fuer Anzeige
FM_PLOT_AUDIO = True            # Audio-Zeitverlauf live plotten


def _parse_demod_decim_cli() -> int | None:
    """``--demod-decim=4`` überschreibt den Decimationsfaktor vor dem FM-Demod."""
    for a in sys.argv:
        if a.startswith("--demod-decim="):
            try:
                v = int(a.split("=", 1)[1].strip())
                if v >= 1:
                    return v
            except ValueError:
                pass
    return None


_cli_demod_decim = _parse_demod_decim_cli()
if _cli_demod_decim is not None:
    FM_DEMOD_DECIM = _cli_demod_decim

# Kontinuierliche Wiedergabe (Final Check „mit dem Ohr“). Aus: Kommandozeile --no-audio
FM_AUDIO_PLAYBACK = "--no-audio" not in sys.argv
# Skalierung: demodulierte Werte sind Hz-Offset; für Lautsprecher ~[-1,1] anpeilen.
FM_AUDIO_PLAYBACK_SCALE = 3e-5
# Peak-basierte Schutz-/Pegelregelung für die Soundausgabe.
# In Sprachpausen kann ein harter per-Block-Scaler “pumpen”/stören, daher:
# - per CLI komplett deaktivierbar
# - oder geglättet (Attack/Release)
FM_AUDIO_LIMITER_ENABLE = "--no-audio-limiter" not in sys.argv
FM_AUDIO_LIMITER_TARGET_PEAK = 0.98
FM_AUDIO_LIMITER_ATTACK_ALPHA = 0.35   # schneller beim Runterregeln
FM_AUDIO_LIMITER_RELEASE_ALPHA = 0.01  # langsamer beim Wiederhochregeln
# PortAudio holt Audio in **festen** Blöcken (Callback) — vermeidet „pulsieren“ durch
# variable stream.write()-Längen. Ring puffert Jitter zwischen Demod und Wiedergabe.
FM_AUDIO_BLOCKSIZE = 512
FM_AUDIO_RING_CAPACITY = 48_000 * 20  # bis ~20 s Puffer (gegen seltene Underflows)

# Anti-Aliasing: FIR-Lowpass vor IQ-Slice-Decimation (gegen alias/broken Discriminator bei großem Hub)
FM_IQ_LP_ENABLE = True
FM_IQ_LP_NUMTAPS = 129
# cutoff = 0.95 * (fs_dec/2)  => sicher unterhalb Nyquist der decimierten IQ-Rate
FM_IQ_LP_CUTOFF_FRAC_NYQUIST = 0.95

# DC-Entfernung: kein blockweises np.mean — das erzeugt Sprünge an jeder Chunk-Grenze (~2 ms).
FM_AUDIO_DC_HP_HZ = 35.0
FM_AUDIO_DC_HP_ORDER = 2

# De-Emphasis (FM Broadcast). Standard in DE/Europa oft ~50 us.
FM_DEEMP_ENABLE = "--no-deemph" not in sys.argv
FM_DEEMP_TAU_S = 50e-6

# Ziel-Ausgaberate fuer Audio (im Labor z.B. 48 kS/s)
FM_AUDIO_OUT_RATE_HZ = 48_000.0

# Nach Discriminator: Rate = SAMPLE_RATE_HZ / FM_DEMOD_DECIM → rational auf 48 kS/s
FM_RESAMPLE_UP = 1
FM_RESAMPLE_DOWN = 1


def _apply_sample_rate_dependent_globals(srate_hz: float) -> None:
    """Setzt SAMPLE_RATE_HZ und FM_RESAMPLE_* passend zu FM_DEMOD_DECIM und Audio-48k."""
    global SAMPLE_RATE_HZ, FM_RESAMPLE_UP, FM_RESAMPLE_DOWN
    SAMPLE_RATE_HZ = float(srate_hz)
    fs_disc = int(round(SAMPLE_RATE_HZ / FM_DEMOD_DECIM))
    out_i = int(round(FM_AUDIO_OUT_RATE_HZ))
    g = math.gcd(out_i, fs_disc)
    FM_RESAMPLE_UP = out_i // g
    FM_RESAMPLE_DOWN = fs_disc // g

# Nach dem Discriminator ist das Signal typischerweise stark verrauscht.
# Ein Low-Pass macht den Audio-Ton sichtbar(er).
FM_AUDIO_LP_CUTOFF_HZ = 20_000.0  # FM-Broadcast baseband bis ~15 kHz; verhindert harte Verzerrung bei größerem Hub
FM_AUDIO_LP_ORDER = 4

# Debug/Feinabstimmung:
# Zeige (zeitweise) Spektrum-Peak-Offset und die dominierende Audio-Frequenz.
FM_DEBUG_EVERY_S = 0.8
FM_AUDIO_DOMINANT_MAX_HZ = 6000.0

# Stream-Diagnose: erwartete vs. gelesene IQ-Samples (Erkennung von USB-Überläufen)
FM_STREAM_DEBUG = True
FM_STREAM_DEBUG_EVERY_S = 2.0

# =============================================================================
# RTL-SDR öffnen
# =============================================================================

try:
    sdr = RtlSdr()
except Exception as e:
    raise SystemExit(f"RTL-SDR konnte nicht geöffnet werden: {e}") from e

_chosen_rate: float | None = None
_last_rate_err: Exception | None = None
for _cand in SDR_RATE_CANDIDATES_HZ:
    try:
        sdr.sample_rate = int(_cand)
        _chosen_rate = float(_cand)
        break
    except Exception as _ex:
        _last_rate_err = _ex
if _chosen_rate is None:
    raise SystemExit(
        "RTL-SDR: keine der Kandidaten-Raten akzeptiert "
        f"{SDR_RATE_CANDIDATES_HZ}.\nLetzter Fehler: {_last_rate_err}\n"
        "Tipp: Stick neu stecken; dann nur eine Rate probieren: "
        "python rtlsdr_fm.py --rate=256000"
    ) from _last_rate_err

_apply_sample_rate_dependent_globals(_chosen_rate)
print(
    f"[SDR] sample_rate = {SAMPLE_RATE_HZ/1000:.0f} kS/s | "
    f"FM nach Decim {FM_DEMOD_DECIM}: {SAMPLE_RATE_HZ/FM_DEMOD_DECIM/1000:.0f} kS/s → "
    f"Audio {FM_AUDIO_OUT_RATE_HZ/1000:.0f} kS/s (resample {FM_RESAMPLE_UP}/{FM_RESAMPLE_DOWN})"
)

sdr.gain = GAIN_DB_INIT
sdr.center_freq = CENTER_FREQ_MHZ_INIT * 1e6

# =============================================================================
# Matplotlib: Spektrum + optional Audio, Slider
# =============================================================================

fig, (ax_spec, ax_audio) = plt.subplots(
    2,
    1,
    figsize=(10, 7),
    sharex=False,
    gridspec_kw={"height_ratios": [3, 1]},
)
plt.subplots_adjust(bottom=0.22, hspace=0.35)

# Frequenzachse (wird in update gesetzt; hier Platzhalter)
freq_mhz = np.fft.fftshift(np.fft.fftfreq(FFT_SIZE, 1 / SAMPLE_RATE_HZ)) / 1e6
power_dB = np.zeros(FFT_SIZE)
(spec_line,) = ax_spec.plot(freq_mhz, power_dB, color="C0", linewidth=0.8)
ax_spec.set_xlabel("Frequenz relativ zur Mittenfrequenz (MHz)")
ax_spec.set_ylabel("Leistung (dB)")
ax_spec.set_title("RTL-SDR Spektrum")
ax_spec.grid(True, alpha=0.5)
ax_spec.set_ylim(-60, 60)

_display_n = min(FM_AUDIO_DISPLAY_SAMPLES, FM_AUDIO_PLOT_SAMPLES)
audio_time_display = np.arange(_display_n, dtype=np.float64) / FM_AUDIO_OUT_RATE_HZ
audio_buf = np.zeros(FM_AUDIO_PLOT_SAMPLES, dtype=np.float64)
(audio_line,) = ax_audio.plot(
    audio_time_display,
    audio_buf[-_display_n:],
    color="C1",
    linewidth=1.2,
)
ax_audio.set_xlabel("Zeit (s)")
ax_audio.set_ylabel("FM Audio (Hz-Offset)")
ax_audio.grid(True, alpha=0.5)
ax_audio.set_ylim(-FM_AUDIO_YLIM_HZ, FM_AUDIO_YLIM_HZ)
if not FM_PLOT_AUDIO:
    ax_audio.set_visible(False)

# Low-Pass auf die Audio-Ausgabe nach Resampling (hilft gegen Rauschen)
audio_sos_lp = butter(
    FM_AUDIO_LP_ORDER,
    FM_AUDIO_LP_CUTOFF_HZ,
    btype="low",
    output="sos",
    fs=FM_AUDIO_OUT_RATE_HZ,
)

# Hochpass gegen DC (ersetzt blockweises mean(); vermeidet Sprünge alle ~2 ms)
audio_sos_dc = butter(
    FM_AUDIO_DC_HP_ORDER,
    FM_AUDIO_DC_HP_HZ,
    btype="high",
    output="sos",
    fs=FM_AUDIO_OUT_RATE_HZ,
)

# Gemeinsamer Anzeige-Zustand (Worker schreibt, GUI liest)
_stream_lock = threading.Lock()
_shared_freq_rel_mhz = np.zeros(FFT_SIZE, dtype=np.float64)
_shared_power_dB = np.zeros(FFT_SIZE, dtype=np.float64)
_shared_audio_buf = np.zeros(FM_AUDIO_PLOT_SAMPLES, dtype=np.float64)
_stream_stop = threading.Event()
_stream_thread: threading.Thread | None = None
_stream_samples_read = 0
_stream_t0_perf = 0.0
_stream_last_debug_perf = 0.0

class _AudioRingBuffer:
    """Thread-sicherer Ring: SDR-Worker schreibt, PortAudio-Callback liest (feste Blockgröße)."""

    __slots__ = ("buf", "capacity", "count", "lock", "r", "w")

    def __init__(self, capacity: int) -> None:
        self.capacity = max(int(capacity), FM_AUDIO_BLOCKSIZE * 4)
        self.buf = np.zeros(self.capacity, dtype=np.float32)
        self.w = 0
        self.r = 0
        self.count = 0
        self.lock = threading.Lock()

    def write(self, x: np.ndarray) -> None:
        n = int(x.shape[0])
        if n <= 0:
            return
        xf = np.asarray(x, dtype=np.float32, order="C")
        with self.lock:
            overflow = self.count + n - self.capacity
            if overflow > 0:
                self.r = (self.r + overflow) % self.capacity
                self.count -= overflow
            w = self.w
            first = min(n, self.capacity - w)
            self.buf[w : w + first] = xf[:first]
            if n > first:
                self.buf[: n - first] = xf[first:n]
            self.w = (w + n) % self.capacity
            self.count += n

    def read_into(self, out: np.ndarray) -> None:
        frames = int(out.shape[0])
        with self.lock:
            take = min(frames, self.count)
            if take == 0:
                out.fill(0.0)
                return
            r = self.r
            first = min(take, self.capacity - r)
            out[:first] = self.buf[r : r + first]
            if take > first:
                out[first:take] = self.buf[: take - first]
            self.r = (r + take) % self.capacity
            self.count -= take
            if take < frames:
                out[take:].fill(0.0)
                # Unterlauf: Callback braucht frames, Ring hatte nur take Samples.
                global _audio_underflow_count, _audio_last_underflow_print
                _audio_underflow_count += 1
                now = time.perf_counter()
                if now - _audio_last_underflow_print >= 1.0:
                    _audio_last_underflow_print = now
                    print(
                        f"[AUDIO] Ring underflow (missing={frames - take} frames, "
                        f"underflow_count={_audio_underflow_count})"
                    )


# optionale Soundausgabe (Ring + Callback-Stream)
_audio_ring: _AudioRingBuffer | None = None
_play_stream = None  # sounddevice.OutputStream | None

# PortAudio Status / Underflow debugging
_audio_underflow_count = 0
_audio_last_underflow_print = 0.0

# Smoother gain applied in the audio output path (reduces pumping in pauses).
_audio_limiter_gain = 1.0


def _ensure_playback_stream() -> None:
    """Startet OutputStream mit Callback — feste Blockgröße, Daten aus Ringpuffer."""
    global _audio_ring, _play_stream
    if not FM_AUDIO_PLAYBACK or sd is None:
        return
    if _play_stream is not None:
        return
    _audio_ring = _AudioRingBuffer(FM_AUDIO_RING_CAPACITY)

    def _callback(outdata: np.ndarray, frames: int, _time, status) -> None:  # type: ignore[no-untyped-def]
        global _audio_underflow_count, _audio_last_underflow_print
        if status:
            _audio_underflow_count += 1
            now = time.perf_counter()
            if now - _audio_last_underflow_print >= 1.0:
                _audio_last_underflow_print = now
                print(f"[AUDIO] PortAudio Status: {status} | underflow_count={_audio_underflow_count}")
        assert _audio_ring is not None
        _audio_ring.read_into(outdata[:, 0])

    try:
        _play_stream = sd.OutputStream(
            samplerate=int(FM_AUDIO_OUT_RATE_HZ),
            channels=1,
            dtype="float32",
            blocksize=int(FM_AUDIO_BLOCKSIZE),
            callback=_callback,
            latency="high",  # etwas mehr PortAudio-Puffer → weniger Knackser bei Jitter
        )
        _play_stream.start()
    except Exception as ex:
        _audio_ring = None
        _play_stream = None
        print("[FM_AUDIO] OutputStream (Callback):", ex)


def _push_playback(audio_f32: np.ndarray) -> None:
    if _audio_ring is None:
        return
    _audio_ring.write(audio_f32)


# Debug-Print throttling (closure)
last_debug_t = [0.0]

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
    ax_spec.set_title(f"RTL-SDR Spektrum — Mitte: {val_mhz:.1f} MHz, Gain: {gain_slider.val:.0f} dB")


def on_gain_slider_change(val_dB: float) -> None:
    """Slider-Änderung: Gain des Empfängers setzen."""
    sdr.gain = val_dB
    ax_spec.set_title(f"RTL-SDR Spektrum — Mitte: {freq_slider.val:.1f} MHz, Gain: {val_dB:.0f} dB")


freq_slider.on_changed(on_freq_slider_change)
gain_slider.on_changed(on_gain_slider_change)
ax_spec.set_title(f"RTL-SDR Spektrum — Mitte: {CENTER_FREQ_MHZ_INIT:.1f} MHz, Gain: {GAIN_DB_INIT:.0f} dB")

#
# Zweistufige Pipeline: SDR-Reader (nur Lesen) -> Demodulator (DSP)
# Ziel: sicherstellen, dass die IQ-Blöcke vollständig von der USB-Seite geholt werden,
# bevor sie demoduliert werden (100% Chunk-Rate: Reader ≈ Fs).
#
FM_IQ_RING_CAPACITY_BLOCKS = 512  # bei Drops ggf. erhöhen


class _IQRingBuffer:
    """Thread-sicherer Ringpuffer für IQ-Blöcke (komplex64)."""

    __slots__ = ("buf", "capacity", "w", "r", "count", "cond", "dropped")

    def __init__(self, capacity_blocks: int) -> None:
        self.capacity = max(int(capacity_blocks), 2)
        self.buf = np.zeros((self.capacity, FFT_SIZE), dtype=np.complex64)
        self.w = 0
        self.r = 0
        self.count = 0
        self.dropped = 0
        self.cond = threading.Condition(threading.Lock())

    def get_fill(self) -> int:
        with self.cond:
            return int(self.count)

    def write(self, x: np.ndarray) -> None:
        # Bei zu langsamen Demod kann der Ring überlaufen; wir droppen dann älteste Blöcke.
        # Wichtig: der Reader bleibt dabei trotzdem schnell (kein DSP im Reader-Thread).
        xb = np.asarray(x, dtype=np.complex64, order="C")
        if xb.shape[0] != FFT_SIZE:
            xb = xb[-FFT_SIZE:]

        with self.cond:
            if self.count == self.capacity:
                # overwrite oldest
                self.r = (self.r + 1) % self.capacity
                self.count -= 1
                self.dropped += 1
            self.buf[self.w, :] = xb
            self.w = (self.w + 1) % self.capacity
            self.count += 1
            self.cond.notify()

    def read_block(self) -> np.ndarray | None:
        with self.cond:
            while self.count == 0 and not _stream_stop.is_set():
                self.cond.wait(timeout=0.1)
            if self.count == 0:
                return None
            y = self.buf[self.r, :].copy()
            self.r = (self.r + 1) % self.capacity
            self.count -= 1
            return y


# Shared state für Reader/Demod/Spectrum
_iq_ring: _IQRingBuffer | None = None
_iq_latest_lock = threading.Lock()
_iq_latest_block = np.zeros(FFT_SIZE, dtype=np.complex64)
_iq_latest_seq = 0

_iq_blocks_read = 0
_iq_blocks_demod = 0


def _iq_reader_worker() -> None:
    """Reader-Thread: liest nur IQ-Blöcke und schreibt sie in den IQ-Ringpuffer."""
    global _iq_blocks_read, _iq_latest_seq, _iq_latest_block
    assert _iq_ring is not None

    t0 = time.perf_counter()
    t_last = t0
    read0 = 0

    while not _stream_stop.is_set():
        try:
            iq_raw = sdr.read_samples(FFT_SIZE)
        except Exception as ex:
            print("[IQ] read_samples:", ex)
            time.sleep(0.01)
            continue

        iq_block = np.asarray(iq_raw, dtype=np.complex64, order="C")
        if iq_block.shape[0] != FFT_SIZE:
            iq_block = iq_block[-FFT_SIZE:]

        _iq_ring.write(iq_block)

        with _iq_latest_lock:
            np.copyto(_iq_latest_block, iq_block)
            _iq_latest_seq += 1

        _iq_blocks_read += 1

        if FM_STREAM_DEBUG:
            now = time.perf_counter()
            if now - t_last >= FM_STREAM_DEBUG_EVERY_S:
                t_last = now
                elapsed = max(now - t0, 1e-6)
                rate_hz = _iq_blocks_read * FFT_SIZE / elapsed
                fill = _iq_ring.get_fill()
                status = "OK" if _iq_ring.dropped == 0 else f"WARN: dropped={_iq_ring.dropped}"
                print(
                    f"[IQ] Reader: {rate_hz/1000:.0f} kS/s (~Fs={SAMPLE_RATE_HZ/1000:.0f} kS/s) | "
                    f"ring_fill={fill}/{_iq_ring.capacity} | {status}"
                )


def _fm_demod_worker() -> None:
    """Demod-Thread: nimmt IQ-Blöcke aus dem Ringpuffer und demoduliert Audio."""
    global _iq_blocks_demod
    assert _iq_ring is not None

    fm_iq_dec_prev: complex | None = None
    zi_dc = sosfilt_zi(audio_sos_dc) * 0.0
    zi_lp = sosfilt_zi(audio_sos_lp) * 0.0
    zi_deemp = None
    deemp_b = None
    deemp_a = None
    if FM_DEEMP_ENABLE:
        deemp_alpha = math.exp(-1.0 / (FM_AUDIO_OUT_RATE_HZ * float(FM_DEEMP_TAU_S)))
        # y[n] = (1-alpha)*x[n] + alpha*y[n-1]
        deemp_b = np.array([1.0 - deemp_alpha], dtype=np.float64)
        deemp_a = np.array([1.0, -deemp_alpha], dtype=np.float64)
        zi_deemp = lfilter_zi(deemp_b, deemp_a) * 0.0

    d = int(FM_DEMOD_DECIM)
    fs_dec = SAMPLE_RATE_HZ / FM_DEMOD_DECIM
    demod_last_debug_perf = time.perf_counter()
    t0 = demod_last_debug_perf
    audio_samples_total = 0
    dphi_samples_total = 0

    # FIR Anti-Aliasing Filter vor IQ-Decimation (slice).
    iq_fir_taps = None
    iq_fir_zi = None
    if FM_IQ_LP_ENABLE:
        # cutoff in Hz bezogen auf SAMPLE_RATE_HZ.
        iq_lpf_cutoff_hz = float(FM_IQ_LP_CUTOFF_FRAC_NYQUIST) * 0.5 * float(fs_dec)
        iq_lpf_cutoff_hz = min(iq_lpf_cutoff_hz, 0.49 * SAMPLE_RATE_HZ)
        iq_fir_taps = firwin(
            numtaps=int(FM_IQ_LP_NUMTAPS),
            cutoff=iq_lpf_cutoff_hz,
            window="blackman",
            pass_zero=True,
            fs=float(SAMPLE_RATE_HZ),
        ).astype(np.float64)
        iq_fir_zi = np.zeros(len(iq_fir_taps) - 1, dtype=np.complex64)

    while not _stream_stop.is_set():
        iq_block = _iq_ring.read_block()
        if iq_block is None:
            break
        _iq_blocks_demod += 1

        if iq_fir_taps is not None and iq_fir_zi is not None:
            iq_filt, iq_fir_zi = lfilter(iq_fir_taps, [1.0], iq_block, zi=iq_fir_zi)
            iq_dec = iq_filt[::d]
        else:
            iq_dec = iq_block[::d]

        # Phase-Discriminator (robuster, keine unwrap-spezifischen Artefakte):
        # angle(iq[n] * conj(iq[n-1])) = dphi in [-pi, pi]
        if fm_iq_dec_prev is None:
            iq_prev = np.empty_like(iq_dec)
            iq_prev[0] = iq_dec[0]
            iq_prev[1:] = iq_dec[:-1]
        else:
            iq_prev = np.empty_like(iq_dec)
            iq_prev[0] = fm_iq_dec_prev
            iq_prev[1:] = iq_dec[:-1]

        # dphi in [-pi, pi], entspricht der Phasendifferenz zwischen aufeinanderfolgenden IQ-Samples.
        # Das enthält ggf. auch einen konstanten Rest-Carrier-Offset (LO-Fehlanpassung), der die Wrap-Marge reduziert.
        dphi = np.angle(iq_dec * np.conj(iq_prev))  # rad in [-pi, pi]
        dphi_samples_total += int(dphi.shape[0])

        fm_iq_dec_prev = complex(iq_dec[-1])

        # f_offset = dphi / (2*pi) * fs
        freq_offset_hz = dphi * fs_dec / (2.0 * np.pi)

        do_dbg = False
        dbg_phase_max = 0.0
        dbg_audio_peak = 0.0
        dbg_warn = ""

        if FM_STREAM_DEBUG and (time.perf_counter() - demod_last_debug_perf) >= FM_STREAM_DEBUG_EVERY_S:
            demod_last_debug_perf = time.perf_counter()
            phase_max = float(np.max(np.abs(dphi)))
            wrap_thr = 0.98 * float(np.pi)
            audio_peak = float(np.max(np.abs(freq_offset_hz)))
            dbg_warn = " (WRAP-NÄHE)" if phase_max >= wrap_thr else ""
            do_dbg = True
            dbg_phase_max = phase_max
            dbg_audio_peak = audio_peak

        if FM_RESAMPLE_UP == FM_RESAMPLE_DOWN == 1:
            audio = freq_offset_hz.astype(np.float64, copy=False)
        else:
            audio = resample_poly(freq_offset_hz, up=FM_RESAMPLE_UP, down=FM_RESAMPLE_DOWN)
            audio = audio.astype(np.float64, copy=False)

        audio, zi_dc = sosfilt(audio_sos_dc, audio, zi=zi_dc)
        audio, zi_lp = sosfilt(audio_sos_lp, audio, zi=zi_lp)
        if FM_DEEMP_ENABLE and zi_deemp is not None and deemp_b is not None and deemp_a is not None:
            audio, zi_deemp = lfilter(deemp_b, deemp_a, audio, zi=zi_deemp)
        audio = audio * FM_AUDIO_GAIN
        audio_samples_total += int(audio.shape[0])

        if do_dbg:
            elapsed = max(time.perf_counter() - t0, 1e-6)
            audio_rate_hz = audio_samples_total / elapsed
            audio_peak_abs = float(np.max(np.abs(audio)))
            pb_peak = audio_peak_abs * FM_AUDIO_PLAYBACK_SCALE
            print(
                f"[DEMOD] phase_max {dbg_phase_max:.3f} rad{dbg_warn} | "
                f"peak f_offset {dbg_audio_peak:.0f} Hz | "
                f"audio_len {len(audio)} | audio_rate ~{audio_rate_hz/1000:.1f} kS/s | "
                f"demod-decim {FM_DEMOD_DECIM} | "
                f"audio_peak_abs {audio_peak_abs:.3f} | "
                f"playback_peak {pb_peak:.3f}"
            )

        # Audio-Rolling-Puffer fürs Plot / debug.
        n = len(audio)
        with _stream_lock:
            ab = _shared_audio_buf
            if n >= FM_AUDIO_PLOT_SAMPLES:
                ab[:] = audio[-FM_AUDIO_PLOT_SAMPLES:]
            elif n > 0:
                ab[:-n] = ab[n:]
                ab[-n:] = audio

        if FM_AUDIO_PLAYBACK and sd is not None:
            _ensure_playback_stream()
            out = audio * FM_AUDIO_PLAYBACK_SCALE

            # Peak-basierter Limiter für PortAudio-Clipping — aber geglättet,
            # damit es in Sprachpausen nicht “pumpt”.
            if FM_AUDIO_LIMITER_ENABLE:
                mx = float(np.max(np.abs(out)))
                required_gain = 1.0
                if mx > FM_AUDIO_LIMITER_TARGET_PEAK and mx > 1e-12:
                    required_gain = float(FM_AUDIO_LIMITER_TARGET_PEAK / mx)

                global _audio_limiter_gain
                if required_gain < _audio_limiter_gain:
                    alpha = float(FM_AUDIO_LIMITER_ATTACK_ALPHA)
                else:
                    alpha = float(FM_AUDIO_LIMITER_RELEASE_ALPHA)
                _audio_limiter_gain = (1.0 - alpha) * _audio_limiter_gain + alpha * required_gain
                out = out * _audio_limiter_gain

            out_pb = out.astype(np.float32, copy=False)
            _push_playback(out_pb)


def _spectrum_worker() -> None:
    """Spectrum-Thread: berechnet FFT nur mit niedriger Rate aus dem 'latest IQ block'."""
    assert FM_ENABLE_SPECTRUM
    window = np.hanning(FFT_SIZE)
    freq_rel_mhz = np.fft.fftshift(np.fft.fftfreq(FFT_SIZE, 1 / SAMPLE_RATE_HZ)) / 1e6
    last_seq = -1

    while not _stream_stop.is_set():
        # poll: cheap im Vergleich zu FFT
        with _iq_latest_lock:
            seq = _iq_latest_seq
            iq = _iq_latest_block.copy()

        if seq == last_seq:
            time.sleep(0.02)
            continue

        last_seq = seq
        if FM_SPECTRUM_EVERY_N_BLOCKS <= 1 or (seq % FM_SPECTRUM_EVERY_N_BLOCKS) == 0:
            spectrum = np.fft.fftshift(np.fft.fft(iq * window))
            power = np.abs(spectrum) ** 2
            power_dB = 10 * np.log10(power + 1e-20)

            with _stream_lock:
                _shared_freq_rel_mhz[:] = freq_rel_mhz
                _shared_power_dB[:] = power_dB.astype(np.float64, copy=False)


def _sdr_stream_worker() -> None:
    """
    Liest IQ so schnell wie möglich (Volllast) und demoduliert fortlaufend.
    So entsteht keine zeitliche Lücke wie bei read_samples nur alle Animations-Frames.
    """
    global _stream_samples_read, _stream_t0_perf, _stream_last_debug_perf

    fm_iq_dec_prev: complex | None = None
    zi_dc = sosfilt_zi(audio_sos_dc) * 0.0
    zi_lp = sosfilt_zi(audio_sos_lp) * 0.0

    _stream_t0_perf = time.perf_counter()
    _stream_last_debug_perf = _stream_t0_perf
    samples_read = 0
    _spec_block = 0
    _last_freq_rel_mhz = (
        np.fft.fftshift(np.fft.fftfreq(FFT_SIZE, 1 / SAMPLE_RATE_HZ)) / 1e6
    ).astype(np.float64)
    _last_power_dB = np.full(FFT_SIZE, -60.0, dtype=np.float64)

    while not _stream_stop.is_set():
        try:
            # Nur FFT_SIZE pro Aufruf (weniger Kopieren als 2×FFT); Demod nutzt jeden Block.
            iq_raw = sdr.read_samples(FFT_SIZE)
            iq = np.asarray(iq_raw, dtype=np.complex128)
        except Exception as ex:
            print("[STREAM] read_samples:", ex)
            time.sleep(0.05)
            continue

        samples_read += FFT_SIZE
        _stream_samples_read = samples_read

        # FFT ist teuer — nur alle N Blöcke, sonst bleibt letztes Spektrum (Demod: jeden Block).
        if FM_ENABLE_SPECTRUM and (
            _spec_block % FM_SPECTRUM_EVERY_N_BLOCKS == 0
        ):
            window = np.hanning(FFT_SIZE)
            spectrum = np.fft.fft(iq * window)
            power = np.abs(spectrum) ** 2
            power_dB = 10 * np.log10(power + 1e-20)
            _last_power_dB[:] = np.fft.fftshift(power_dB)
            _last_freq_rel_mhz[:] = np.fft.fftshift(
                np.fft.fftfreq(FFT_SIZE, 1 / SAMPLE_RATE_HZ)
            ) / 1e6
        _spec_block += 1

        d = int(FM_DEMOD_DECIM)
        iq_dec = iq[::d]
        fs_dec = SAMPLE_RATE_HZ / FM_DEMOD_DECIM

        if fm_iq_dec_prev is None:
            phase = np.unwrap(np.angle(iq_dec))
            dphi = np.diff(phase)
        else:
            iq_seq = np.empty(len(iq_dec) + 1, dtype=np.complex128)
            iq_seq[0] = fm_iq_dec_prev
            iq_seq[1:] = iq_dec
            phase = np.unwrap(np.angle(iq_seq))
            dphi = np.diff(phase)
        fm_iq_dec_prev = complex(iq_dec[-1])

        freq_offset_hz = dphi * fs_dec / (2.0 * np.pi)

        if FM_RESAMPLE_UP == FM_RESAMPLE_DOWN == 1:
            audio = freq_offset_hz.astype(np.float64, copy=False)
        else:
            audio = resample_poly(freq_offset_hz, up=FM_RESAMPLE_UP, down=FM_RESAMPLE_DOWN)
            audio = audio.astype(np.float64, copy=False)

        audio, zi_dc = sosfilt(audio_sos_dc, audio, zi=zi_dc)
        audio, zi_lp = sosfilt(audio_sos_lp, audio, zi=zi_lp)
        audio = audio * FM_AUDIO_GAIN

        if FM_AUDIO_PLAYBACK and sd is not None:
            _ensure_playback_stream()
            out_pb = (audio * FM_AUDIO_PLAYBACK_SCALE).astype(np.float32)
            _push_playback(out_pb)

        n = len(audio)
        with _stream_lock:
            if FM_ENABLE_SPECTRUM:
                _shared_freq_rel_mhz[:] = _last_freq_rel_mhz
                _shared_power_dB[:] = _last_power_dB
            ab = _shared_audio_buf
            if n >= FM_AUDIO_PLOT_SAMPLES:
                ab[:] = audio[-FM_AUDIO_PLOT_SAMPLES:]
            elif n > 0:
                ab[:-n] = ab[n:]
                ab[-n:] = audio

        now = time.perf_counter()
        if FM_STREAM_DEBUG and (now - _stream_last_debug_perf) >= FM_STREAM_DEBUG_EVERY_S:
            _stream_last_debug_perf = now
            elapsed = max(now - _stream_t0_perf, 1e-6)
            rate_hz = samples_read / elapsed
            pct = 100.0 * rate_hz / SAMPLE_RATE_HZ
            # Klartext: „erwartet M“ war verwirrend — entscheidend ist erreichte IQ-Rate vs. Fs
            if rate_hz >= 0.92 * SAMPLE_RATE_HZ:
                status = "OK (Fs erreicht)"
            else:
                status = (
                    "WARN: IQ-Rate < Fs → USB-Drops, Demod-Sprünge — SAMPLE_RATE_HZ senken oder Rechner entlasten"
                )
            print(
                f"[STREAM] IQ-Rate ~{rate_hz/1000:.0f} kS/s von {SAMPLE_RATE_HZ/1000:.0f} kS/s "
                f"({pct:.0f}%) | {status}"
            )


def update_frame(_frame: int) -> tuple:
    """Plottet den zuletzt vom Stream-Thread geschriebenen Zustand (kein read_samples)."""
    with _stream_lock:
        freq_rel_mhz = _shared_freq_rel_mhz.copy()
        power_dB = _shared_power_dB.copy()
        audio_copy = _shared_audio_buf.copy()

    spec_line.set_data(freq_rel_mhz, power_dB)
    ax_spec.set_xlim(freq_rel_mhz.min(), freq_rel_mhz.max())

    if FM_PLOT_AUDIO:
        audio_line.set_data(audio_time_display, audio_copy[-_display_n:])
        if FM_AUDIO_AUTO_YLIM:
            seg = audio_copy[-_display_n:]
            base = float(np.percentile(np.abs(seg), 99.0))
            base = max(base, 50.0)
            ax_audio.set_ylim(-base * 1.15, base * 1.15)
        else:
            ax_audio.set_ylim(-FM_AUDIO_YLIM_HZ, FM_AUDIO_YLIM_HZ)

        now_t = time.perf_counter()
        if now_t - last_debug_t[0] >= FM_DEBUG_EVERY_S:
            last_debug_t[0] = now_t
            peak_bin = int(np.argmax(power_dB))
            peak_rel_hz = float(freq_rel_mhz[peak_bin] * 1e6)

            audio_latest = audio_copy
            w = np.hanning(len(audio_latest))
            af = np.fft.rfft(audio_latest * w)
            freqs_af = np.fft.rfftfreq(len(audio_latest), d=1.0 / FM_AUDIO_OUT_RATE_HZ)
            dom_freq_hz = float("nan")
            if af is not None and freqs_af is not None:
                mask = (freqs_af >= 0) & (freqs_af <= FM_AUDIO_DOMINANT_MAX_HZ)
                if np.any(mask):
                    dom_idx = int(np.argmax(np.abs(af[mask])))
                    dom_freq_hz = float(freqs_af[mask][dom_idx])

            print(
                f"[FM_DEBUG] LO {sdr.center_freq/1e6:.3f} MHz | "
                f"spec_peak_rel {peak_rel_hz/1e3:.2f} kHz | "
                f"audio_dom ~{dom_freq_hz:.0f} Hz"
            )
        return (spec_line, audio_line)

    return (spec_line,)


_stream_stop.clear()
_iq_ring = _IQRingBuffer(FM_IQ_RING_CAPACITY_BLOCKS)
_iq_reader_thread = threading.Thread(
    target=_iq_reader_worker,
    daemon=True,
    name="rtlsdr_iq_reader",
)
_iq_demod_thread = threading.Thread(
    target=_fm_demod_worker,
    daemon=True,
    name="rtlsdr_fm_demod",
)

_iq_reader_thread.start()
_iq_demod_thread.start()
if FM_ENABLE_SPECTRUM:
    _spectrum_thread = threading.Thread(
        target=_spectrum_worker,
        daemon=True,
        name="rtlsdr_spectrum",
    )
    _spectrum_thread.start()
else:
    _spectrum_thread = None

print(
    "[PIPE] 2-stufig: Reader->Demod (Reader misst Chunk-Rate in [IQ]) "
    "GUI plottet nur."
)
if FM_ENABLE_SPECTRUM:
    print(
        f"[PIPE] Spectrum-Thread: FFT alle {FM_SPECTRUM_EVERY_N_BLOCKS} Blocks "
        "(aus latest IQ, niedrigere Rate)."
    )
else:
    print("[PIPE] Spectrum aus (--no-spectrum).")

if FM_AUDIO_PLAYBACK:
    print("[FM_AUDIO] Ton an (ohne: --no-audio). Lautstärke: FM_AUDIO_PLAYBACK_SCALE im Skript.")
else:
    print("[FM_AUDIO] Ton aus (--no-audio).")

# Plot-Refresh entkoppelt von der IQ-Rate (10 fps reichen für die Anzeige).
anim = FuncAnimation(
    fig,
    update_frame,
    interval=100,
    blit=not FM_AUDIO_AUTO_YLIM,
    cache_frame_data=False,
)

if FM_AUDIO_PLAYBACK and sd is None:
    print("[FM_AUDIO] sounddevice fehlt: pip install sounddevice (sonst kein Ton).")

try:
    plt.show()
finally:
    _stream_stop.set()
    if _iq_reader_thread is not None:
        _iq_reader_thread.join(timeout=3.0)
    if _iq_demod_thread is not None:
        _iq_demod_thread.join(timeout=3.0)
    if _spectrum_thread is not None:
        _spectrum_thread.join(timeout=3.0)
    if _play_stream is not None:
        try:
            _play_stream.stop()
            _play_stream.close()
        except Exception:
            pass
        _play_stream = None
    sdr.close()
