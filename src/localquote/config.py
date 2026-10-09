"""Local-only configuration. No telemetry, sockets, or external service calls."""
from __future__ import annotations
import os
from pathlib import Path


def data_dir() -> Path:
    explicit = os.getenv("LOCALQUOTE_DATA_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()
    base = os.getenv("LOCALAPPDATA") or os.getenv("XDG_DATA_HOME")
    if not base:
        base = str(Path.home() / ".local" / "share")
    return Path(base) / "LocalQuote"


def database_path() -> Path:
    return data_dir() / "localquote.sqlite3"
