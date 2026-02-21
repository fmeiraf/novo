"""Detect the user's terminal and open new windows."""

import os
import subprocess
import sys
from pathlib import Path

# Map TERM_PROGRAM values to macOS app names
_TERM_PROGRAM_MAP: dict[str, str] = {
    "Apple_Terminal": "Terminal",
    "iTerm.app": "iTerm",
    "ghostty": "Ghostty",
    "WezTerm": "WezTerm",
    "kitty": "kitty",
    "alacritty": "Alacritty",
    "tmux": "Terminal",  # tmux inherits the outer terminal, fall back
}


def detect_terminal() -> str:
    """Return the macOS application name for the current terminal.

    Reads ``TERM_PROGRAM`` (set by most modern terminals) and maps it
    to the name used by ``open -a``.  Falls back to ``Terminal`` when
    the variable is missing or unrecognised.
    """
    term = os.environ.get("TERM_PROGRAM", "")
    return _TERM_PROGRAM_MAP.get(term, term or "Terminal")


def open_terminal_at(path: Path) -> None:
    """Open a new terminal window at *path*."""
    app_name = detect_terminal()

    if sys.platform == "darwin":
        subprocess.Popen(["open", "-a", app_name, str(path)])
    else:
        # Linux: most terminals accept a --working-directory flag
        subprocess.Popen([app_name.lower(), "--working-directory", str(path)])
