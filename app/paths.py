# stolen from macputty
import sys
from pathlib import Path

def resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path.cwd()
    return base.joinpath(*parts)