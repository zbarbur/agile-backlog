# src/app.py
"""Streamlit Kanban board for agile-backlog."""

from src.models import BacklogItem

CATEGORY_STYLES: dict[str, tuple[str, str, str]] = {
    # category: (emoji, text_color, bg_color)
    "bug": ("🐛", "#f472b6", "#3a1a2a"),
    "feature": ("✨", "#60a5fa", "#1a2a3a"),
    "tech-debt": ("🔧", "#fbbf24", "#2a2a1a"),
    "docs": ("📚", "#34d399", "#1a3a2a"),
    "security": ("🔒", "#a78bfa", "#2a1a3a"),
    "infra": ("🏗️", "#22d3ee", "#1a2a2a"),
}

PRIORITY_COLORS: dict[str, str] = {
    "P1": "#ef4444",
    "P2": "#3b82f6",
    "P3": "#f59e0b",
}


def category_style(category: str) -> tuple[str, str, str]:
    """Return (emoji, text_color, bg_color) for a category."""
    return CATEGORY_STYLES.get(category, ("📋", "#9ca3af", "#2a2a2a"))


def filter_items(
    items: list[BacklogItem],
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    sprint: int | None = None,
    search: str = "",
) -> list[BacklogItem]:
    """Apply filters to items. Multiple filters combine with AND logic."""
    result = items
    if status:
        result = [i for i in result if i.status == status]
    if priority:
        result = [i for i in result if i.priority == priority]
    if category:
        result = [i for i in result if i.category == category]
    if sprint is not None:
        result = [i for i in result if i.sprint_target == sprint]
    if search:
        q = search.lower()
        result = [
            i
            for i in result
            if q in i.title.lower() or q in i.description.lower() or any(q in t.lower() for t in i.tags)
        ]
    return result


def render_card_html(item: BacklogItem) -> str:
    """Generate the HTML string for a styled card."""
    emoji, cat_color, cat_bg = category_style(item.category)
    pri_color = PRIORITY_COLORS.get(item.priority, "#888")
    sprint_text = f"S{item.sprint_target}" if item.sprint_target is not None else "Unplanned"

    pri_badge_style = (
        f"margin-left:auto;font-size:11px;background:rgba(0,0,0,0.3);"
        f"color:{pri_color};padding:2px 8px;border-radius:4px;font-weight:700;"
    )
    return (
        f'<div style="border-radius:8px;overflow:hidden;margin-bottom:8px;border:1px solid #333;">\n'
        f'  <div style="background:{cat_bg};padding:4px 10px;display:flex;align-items:center;gap:6px;">\n'
        f"    <span>{emoji}</span>\n"
        f'    <span style="font-size:12px;color:{cat_color};font-weight:600;text-transform:uppercase;">'
        f"{item.category}</span>\n"
        f'    <span style="{pri_badge_style}">{item.priority}</span>\n'
        f"  </div>\n"
        f'  <div style="padding:8px 10px;">\n'
        f'    <div style="font-size:14px;font-weight:500;">{item.title}</div>\n'
        f'    <div style="font-size:11px;color:#888;margin-top:2px;">{sprint_text}</div>\n'
        f"  </div>\n"
        f"</div>"
    )
