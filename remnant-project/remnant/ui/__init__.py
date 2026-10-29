"""
ui/__init__.py — UI detection logic.
Selects TUI if textual is available, else falls back to PlainUI.
"""


def get_ui(force: str = None):
    """
    Return the appropriate UI implementation.
    force: 'plain' | 'tui' | None (auto-detect)
    """
    if force == "plain":
        from ui.plain import PlainUI
        return PlainUI()
    if force == "tui":
        try:
            from ui.tui import TUI
            return TUI()
        except ImportError:
            from ui.plain import PlainUI
            return PlainUI()
    try:
        import textual  # noqa: F401
        from ui.tui import TUI
        return TUI()
    except ImportError:
        from ui.plain import PlainUI
        return PlainUI()
