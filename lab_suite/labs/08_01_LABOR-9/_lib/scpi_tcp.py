"""SCPI ueber TCP (Roh-Socket) fuer FPC1500 — ohne pyvisa."""

from __future__ import annotations

import socket
from typing import Optional


def scpi_query(
    host: str,
    port: int,
    cmd: str,
    max_bytes: int = 4096,
    *,
    socket_timeout: float = 5.0,
) -> str:
    cmd = cmd.strip() + "\n"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(socket_timeout)
    try:
        s.connect((host, port))
        s.sendall(cmd.encode())
        buf = b""
        while len(buf) < max_bytes:
            chunk = s.recv(8192)
            if not chunk:
                break
            buf += chunk
            if b"\n" in buf:
                break
        return buf.decode("utf-8", errors="replace").strip()
    finally:
        s.close()


def get_trace_data(
    host: str,
    port: int,
    *,
    trace_read_max_bytes: int = 256 * 1024,
    socket_timeout: float = 5.0,
) -> Optional[tuple[list[float], list[float], Optional[float]]]:
    """Frequenzachse (Hz), Trace-Werte (dBm) und RBW (Hz)."""
    try:
        trace_s = scpi_query(
            host,
            port,
            "TRAC:DATA? TRACE1",
            max_bytes=trace_read_max_bytes,
            socket_timeout=socket_timeout,
        )
    except Exception:
        return None
    amps: list[float] = []
    for part in trace_s.replace(",", " ").split():
        try:
            amps.append(float(part))
        except ValueError:
            continue
    if not amps:
        return None
    try:
        star_s = scpi_query(host, port, "FREQ:STAR?", max_bytes=256, socket_timeout=socket_timeout)
        stop_s = scpi_query(host, port, "FREQ:STOP?", max_bytes=256, socket_timeout=socket_timeout)
        freq_start = float(star_s.strip())
        freq_stop = float(stop_s.strip())
    except Exception:
        try:
            cent_s = scpi_query(host, port, "FREQ:CENT?", max_bytes=256, socket_timeout=socket_timeout)
            span_s = scpi_query(host, port, "FREQ:SPAN?", max_bytes=256, socket_timeout=socket_timeout)
            cent = float(cent_s.strip())
            span = float(span_s.strip())
            freq_start = cent - span / 2
            freq_stop = cent + span / 2
        except Exception:
            return None
    rbw_hz: Optional[float] = None
    for rbw_cmd in ("BAND:RES?", "BANDwidth:RESolution?"):
        try:
            rbw_hz = float(
                scpi_query(host, port, rbw_cmd, max_bytes=256, socket_timeout=socket_timeout).strip()
            )
            break
        except Exception:
            continue
    n = len(amps)
    freqs = [freq_start + (freq_stop - freq_start) * i / max(1, n - 1) for i in range(n)]
    return (freqs, amps, rbw_hz)


def screenshot_save(
    host: str,
    port: int,
    filename: str = "screen.png",
    *,
    screenshot_timeout: float = 10.0,
) -> Optional[str]:
    commands = ["HCOP:DEV:LANG PNG", "HCOP:DEST 'MMEM'", f"MMEM:NAME '{filename}'", "HCOP:IMM"]
    cmd = "\n".join(commands) + "\n"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(screenshot_timeout)
    try:
        s.connect((host, port))
        s.sendall(cmd.encode())
        buf = b""
        while len(buf) < 4096:
            try:
                chunk = s.recv(1024)
                if not chunk:
                    break
                buf += chunk
                if b"\n" in buf:
                    break
            except socket.timeout:
                break
        reply = buf.decode("utf-8", errors="replace").strip()
        if reply and "error" in reply.lower():
            return reply
        return None
    except Exception as e:
        return str(e)
    finally:
        s.close()


def screenshot_read(
    host: str,
    port: int,
    filename: str,
    *,
    screenshot_timeout: float = 10.0,
) -> Optional[bytes]:
    cmd = f"MMEM:DATA? '{filename}'\n"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(screenshot_timeout)
    try:
        s.connect((host, port))
        s.sendall(cmd.encode())
        buf = b""
        while b"#" not in buf and len(buf) < 1024:
            chunk = s.recv(256)
            if not chunk:
                return None
            buf += chunk
        if b"#" not in buf:
            return None
        start = buf.index(b"#")
        buf = buf[start:]
        if len(buf) < 2:
            buf += s.recv(2 - len(buf))
        n_digits = int(chr(buf[1]))
        if n_digits < 1 or n_digits > 9:
            return None
        while len(buf) < 2 + n_digits:
            buf += s.recv(2 + n_digits - len(buf))
        data_len = int(buf[2 : 2 + n_digits].decode())
        buf = buf[2 + n_digits :]
        while len(buf) < data_len:
            chunk = s.recv(min(65536, data_len - len(buf)))
            if not chunk:
                break
            buf += chunk
        return buf[:data_len] if len(buf) >= data_len else None
    except Exception:
        return None
    finally:
        s.close()
