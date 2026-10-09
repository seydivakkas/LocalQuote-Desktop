"""Standalone entrypoint for PyInstaller; intentionally independent of cwd."""
from localquote.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
