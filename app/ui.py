"""
terminal output helpers for the deploy pipeline: stage banners, pass/fail
lines with timings, and a final summary table.

stdlib only. colors and unicode symbols are skipped automatically when
output isn't a terminal (piped, CI logs) or NO_COLOR is set.
"""

import os
import sys

_CODES = {"green": "32", "red": "31", "yellow": "33", "cyan": "36", "dim": "2", "bold": "1"}


def _color_enabled():
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _unicode_enabled():
    return (getattr(sys.stdout, "encoding", None) or "").lower().replace("-", "") == "utf8"


def paint(text, color):
    if not _color_enabled():
        return text
    return f"\033[{_CODES[color]}m{text}\033[0m"


def symbol(status):
    if _unicode_enabled():
        return {"passed": "✓", "failed": "✗", "skipped": "–"}[status]
    return {"passed": "OK", "failed": "FAIL", "skipped": "--"}[status]


_COLOR_FOR = {"passed": "green", "failed": "red", "skipped": "dim"}


def stage_banner(index, total, name):
    print(paint(f"\n[{index}/{total}] {name}", "cyan"))


def stage_result(name, ok, seconds):
    status = "passed" if ok else "failed"
    print(paint(f"{symbol(status)} {name} {status} ({seconds:.1f}s)", _COLOR_FOR[status]))


def summary(results, total_seconds):
    """results: list of (name, status, seconds) with status passed/failed/skipped."""
    width = max(len(name) for name, _, _ in results)
    print(paint("\nSummary", "bold"))
    for name, status, seconds in results:
        timing = f"{seconds:.1f}s" if status != "skipped" else "not run"
        print(paint(f"  {symbol(status)} {name.ljust(width)}  {status:<8} {timing}", _COLOR_FOR[status]))
    print(paint(f"  total: {total_seconds:.1f}s", "dim"))
