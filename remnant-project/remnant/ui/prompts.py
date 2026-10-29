"""
ui/prompts.py — Shared input/output helpers for all UI modes.
Stdlib only. Gracefully handles non-UTF-8 terminals.
"""

import sys

_UTF8 = sys.stdout.encoding and sys.stdout.encoding.lower() in ("utf-8", "utf8")


def print_line(text: str = ""):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def separator(char: str = "-", width: int = 60) -> str:
    return char * width


def print_separator(char: str = "-", width: int = 60):
    print_line(separator(char, width))


def prompt_input(prompt_text: str) -> str:
    try:
        return input(prompt_text + " ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def prompt_choice(items: list, prompt: str = "Choose") -> int:
    """Display numbered list and return 0-based index. Returns -1 on invalid input."""
    for i, item in enumerate(items, 1):
        print_line(f"  [{i}] {item}")
    raw = prompt_input(f"{prompt} (1-{len(items)}):")
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(items):
            return idx
    except (ValueError, TypeError):
        pass
    return -1
