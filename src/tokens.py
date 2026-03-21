"""Design tokens for agile-backlog — Mission Control dark theme."""

# Category colors: (text_color, bg_color) — dark theme
CATEGORY_STYLES: dict[str, tuple[str, str]] = {
    "bug": ("#f472b6", "rgba(244,114,182,0.12)"),
    "feature": ("#60a5fa", "rgba(59,130,246,0.15)"),
    "tech-debt": ("#fbbf24", "rgba(251,191,36,0.12)"),
    "docs": ("#34d399", "rgba(52,211,153,0.12)"),
    "security": ("#a78bfa", "rgba(167,139,250,0.12)"),
    "infra": ("#22d3ee", "rgba(34,211,238,0.12)"),
}

# Priority colors: (text_color, bg_color)
PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "P1": ("#f87171", "rgba(248,113,113,0.15)"),
    "P2": ("#60a5fa", "rgba(96,165,250,0.12)"),
    "P3": ("#fbbf24", "rgba(251,191,36,0.12)"),
}

# Priority ordering for range filters
PRIORITY_ORDER: dict[str, int] = {"P1": 1, "P2": 2, "P3": 3}

# Column background tints
COLUMN_BG: dict[str, str] = {
    "backlog": "#111116",
    "doing": "#14130e",
    "done": "#0f1210",
}
