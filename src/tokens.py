"""Design tokens for agile-backlog — framework-agnostic color and sizing constants."""

# Category colors: (text_color, bg_color) — dark text on light pastel background
CATEGORY_STYLES: dict[str, tuple[str, str]] = {
    "bug": ("#be185d", "#fce7f3"),
    "feature": ("#1d4ed8", "#dbeafe"),
    "tech-debt": ("#92400e", "#fef3c7"),
    "docs": ("#065f46", "#d1fae5"),
    "security": ("#5b21b6", "#ede9fe"),
    "infra": ("#155e75", "#cffafe"),
}

# Priority colors: (text_color, bg_color)
PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "P1": ("#dc2626", "#fef2f2"),
    "P2": ("#2563eb", "#eff6ff"),
    "P3": ("#d97706", "#fffbeb"),
}

# Priority ordering for range filters
PRIORITY_ORDER: dict[str, int] = {"P1": 1, "P2": 2, "P3": 3}

# Column background tints
COLUMN_BG: dict[str, str] = {
    "backlog": "#f1f5f9",
    "doing": "#fefce8",
    "done": "#f0fdf4",
}
