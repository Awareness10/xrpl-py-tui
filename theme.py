"""Custom OLED-friendly theme for XRPL Dashboard."""

from textual.theme import Theme

# OLED Dark theme with purple accent
OLED_DARK = Theme(
    name="oled-dark",
    primary="#7c3aed",        # Purple accent
    secondary="#a855f7",      # Lighter purple
    accent="#c084fc",         # Highlight purple
    foreground="#e4e4e7",     # Light gray text
    background="#000000",     # Pure OLED black
    surface="#0a0a0a",        # Slightly lifted black
    panel="#111111",          # Panel backgrounds
    success="#22c55e",        # Green
    warning="#eab308",        # Yellow
    error="#ef4444",          # Red
    dark=True,
    variables={
        "border": "#27272a",
        "border-blurred": "#18181b",
        "scrollbar": "#27272a",
        "scrollbar-hover": "#3f3f46",
        "scrollbar-active": "#52525b",
        "footer-key-foreground": "#a855f7",
        "footer-description-foreground": "#71717a",
    },
)

# Color constants for Rich markup (matching theme)
class Colors:
    """Color constants for Rich text markup."""

    # Status colors
    SUCCESS = "#22c55e"
    ERROR = "#ef4444"
    WARNING = "#eab308"

    # Accent colors
    PRIMARY = "#7c3aed"
    SECONDARY = "#a855f7"
    ACCENT = "#c084fc"

    # Text colors
    MUTED = "#71717a"
    DIM = "#52525b"

    @classmethod
    def success(cls, text: str) -> str:
        return f"[{cls.SUCCESS}]{text}[/]"

    @classmethod
    def error(cls, text: str) -> str:
        return f"[{cls.ERROR}]{text}[/]"

    @classmethod
    def warning(cls, text: str) -> str:
        return f"[{cls.WARNING}]{text}[/]"

    @classmethod
    def accent(cls, text: str) -> str:
        return f"[{cls.SECONDARY}]{text}[/]"

    @classmethod
    def muted(cls, text: str) -> str:
        return f"[{cls.MUTED}]{text}[/]"
