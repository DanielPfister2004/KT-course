"""
Git-Operationen für den App-Launcher: Repo-Root, Status, Log, Remote, Pull, Push (submissions-Ordner).
Alle Befehle werden ausgeführt und liefern (Erfolg, Ausgabe) zurück, damit Studierende sehen, was passiert.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def get_repo_root(cwd: Path) -> Path | None:
    """Git-Repo-Wurzel ermitteln (git rev-parse --show-toplevel). Bei Fehler None."""
    try:
        out = subprocess.run(
            [*_git_cmd(), "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    return Path(out.stdout.strip())


def _git_cmd() -> list[str]:
    return ["git"]


def run_git(args: list[str], cwd: Path) -> tuple[bool, str, str, str]:
    """
    Führt ein Git-Kommando aus. Rückgabe: (success, stdout, stderr, command_string).
    """
    cmd = _git_cmd() + args
    cmd_str = " ".join(cmd)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        return result.returncode == 0, out, err, cmd_str
    except Exception as e:
        return False, "", str(e), cmd_str


def push_submissions_folder(repo_root: Path, folder_name: str) -> tuple[bool, str, list[tuple[str, str, str]]]:
    """
    Führt aus: git add <path>, git commit -m "...", git push origin.
    path = lab_suite/labs/<folder_name>/submissions (relativ zu repo_root).
    Rückgabe: (success, kurze Meldung, [(cmd, stdout, stderr), ...]).
    """
    rel_path = f"lab_suite/labs/{folder_name}/submissions"
    steps: list[tuple[str, str, str]] = []

    # git add
    ok, out, err, cmd = run_git(["add", rel_path], repo_root)
    steps.append((cmd, out, err))
    if not ok:
        return False, f"git add fehlgeschlagen: {err or out}", steps

    # git commit
    msg = f"committing {rel_path}"
    ok, out, err, cmd = run_git(["commit", "-m", msg], repo_root)
    steps.append((cmd, out, err))
    if not ok:
        if "nothing to commit" in (out + err).lower():
            steps.pop()
            steps.append((cmd, "(nichts zu committen, Working tree clean)", ""))
        else:
            return False, f"git commit fehlgeschlagen: {err or out}", steps

    # git push origin
    ok, out, err, cmd = run_git(["push", "origin"], repo_root)
    steps.append((cmd, out, err))
    if not ok:
        return False, f"git push fehlgeschlagen: {err or out}", steps

    return True, f"Push erfolgreich: {rel_path}", steps
