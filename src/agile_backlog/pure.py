"""Pure functions for agile-backlog — framework-independent, fully tested."""

from datetime import date, timedelta

from agile_backlog.models import BacklogItem
from agile_backlog.tokens import CATEGORY_STYLES, PRIORITY_COLORS, PRIORITY_ORDER


def category_style(category: str) -> tuple[str, str]:
    """Return (text_color, bg_color) for a category."""
    return CATEGORY_STYLES.get(category, ("#9ca3af", "rgba(156,163,175,0.10)"))


def filter_items(
    items: list[BacklogItem],
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    sprint: int | None = None,
    search: str = "",
) -> list[BacklogItem]:
    """Apply filters to items. Multiple filters combine with AND logic.

    Priority supports ranges: "P1" (exact), "P2+" (P1 and P2), "P3+" (all).
    """
    result = items
    if status:
        result = [i for i in result if i.status == status]
    if priority:
        if priority.endswith("+"):
            max_level = PRIORITY_ORDER.get(priority[:-1], 3)
            result = [i for i in result if PRIORITY_ORDER.get(i.priority, 99) <= max_level]
        else:
            result = [i for i in result if i.priority == priority]
    if category:
        result = [i for i in result if i.category == category]
    if sprint == "unplanned":
        result = [i for i in result if i.sprint_target is None]
    elif sprint is not None:
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
    """Generate the HTML string for a styled card (two-row design)."""
    cat_color, cat_bg = category_style(item.category)
    pri_color, pri_bg = PRIORITY_COLORS.get(item.priority, ("#888", "#f3f4f6"))

    p1_style = "border-left:3px solid #ef4444;" if item.priority == "P1" else ""
    pill = "font-size:11px;font-weight:600;padding:2px 8px;border-radius:4px;white-space:nowrap"

    badges = [
        f'<span style="{pill};text-transform:uppercase;color:{cat_color};background:{cat_bg}">{item.category}</span>',
        f'<span style="{pill};text-transform:uppercase;color:{pri_color};background:{pri_bg}">{item.priority}</span>',
    ]
    if item.phase:
        badges.append(f'<span style="{pill};font-style:italic;color:#71717a;background:#1e1e23">{item.phase}</span>')
    review_badge = "font-size:10px;color:#4ade80;background:rgba(74,222,128,0.1);padding:1px 6px;border-radius:3px"
    if item.design_reviewed:
        badges.append(f'<span style="{review_badge}">&#10003; design</span>')
    if item.code_reviewed:
        badges.append(f'<span style="{review_badge}">&#10003; code</span>')
    if item.sprint_target is not None:
        badges.append(
            f'<span style="{pill};font-weight:500;color:#52525b;background:none;'
            f'border:1px solid #27272a">S{item.sprint_target}</span>'
        )

    badge_row = " ".join(badges)

    return (
        f'<div style="margin:0;padding:2px 0;{p1_style}">'
        f'<div style="font-size:14px;font-weight:600;color:#e4e4e7;line-height:1.35;'
        f'margin-bottom:6px">{item.title}</div>'
        f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">'
        f"{badge_row}</div></div>"
    )


def detect_current_sprint(items: list[BacklogItem]) -> int | None:
    """Detect the current sprint. Checks doing items first, then falls back to highest sprint number."""
    doing_sprints = [i.sprint_target for i in items if i.status == "doing" and i.sprint_target is not None]
    if doing_sprints:
        from collections import Counter

        return Counter(doing_sprints).most_common(1)[0][0]
    # Fallback: highest sprint number across all items (sprint is active until closed)
    all_sprints = [i.sprint_target for i in items if i.sprint_target is not None]
    return max(all_sprints) if all_sprints else None


def _complexity_badge(complexity: str) -> str:
    """Return an HTML badge for complexity (S/M/L)."""
    colors = {"S": ("#065f46", "#d1fae5"), "M": ("#92400e", "#fef3c7"), "L": ("#dc2626", "#fef2f2")}
    text_color, bg_color = colors.get(complexity, ("#4b5563", "#f3f4f6"))
    return (
        f'<span style="display:inline-flex;align-items:center;height:20px;'
        f"font-size:11px;font-weight:600;text-transform:uppercase;"
        f"color:{text_color};background:{bg_color};"
        f'padding:2px 8px;border-radius:4px;">{complexity}</span>'
    )


def comment_badge_html(comments: list[dict]) -> str:
    """Return HTML for the comment badge on a card."""
    if not comments:
        return ""
    flagged_count = sum(1 for n in comments if n.get("flagged") and not n.get("resolved"))
    total_count = len(comments)
    _badge = "border-radius:9999px;padding:1px 7px;font-size:11px;margin-left:6px;color:#fff;"
    if flagged_count > 0:
        # Red badge for unresolved flagged
        return f'<span style="background:#f87171;{_badge}">{flagged_count}</span>'
    elif total_count > 0:
        # Blue badge for total comments (no unresolved flagged)
        return f'<span style="background:#3b82f6;{_badge}">{total_count}</span>'
    return ""


def group_items_by_section(items: list[BacklogItem], current_sprint: int | None) -> dict[str, list[BacklogItem]]:
    """Group backlog/unplanned items into three planning sections.

    Items with status 'doing' or 'done' are excluded (they belong on the board).
    """
    backlog, vnext, vfuture = [], [], []
    for item in items:
        if item.status in ("doing", "done"):
            continue
        if current_sprint is None or item.sprint_target is None:
            backlog.append(item)
        elif item.sprint_target == current_sprint + 1:
            vnext.append(item)
        elif item.sprint_target >= current_sprint + 2:
            vfuture.append(item)
        else:
            backlog.append(item)

    def _sort_key(i: BacklogItem) -> tuple:
        return (PRIORITY_ORDER.get(i.priority, 99), str(i.updated))

    backlog.sort(key=_sort_key)
    vnext.sort(key=_sort_key)
    vfuture.sort(key=_sort_key)
    return {"backlog": backlog, "vnext": vnext, "vfuture": vfuture}


def render_comment_html(comment: dict) -> str:
    """Render a single comment as an HTML bubble."""
    author = comment.get("author", "agent")
    text = comment.get("text", "")
    created = comment.get("created", "")
    flagged = comment.get("flagged", False)
    resolved = comment.get("resolved", False)

    icon = "\U0001f464" if author == "user" else "\U0001f916"
    border_color = "#f87171" if flagged and not resolved else "transparent"
    opacity = "0.5" if resolved else "1.0"
    text_style = "text-decoration:line-through;" if resolved else ""

    return (
        f'<div style="border-left:3px solid {border_color};padding:8px 12px;'
        f'margin:4px 0;border-radius:6px;background:rgba(255,255,255,0.04);opacity:{opacity};">'
        f'<div style="font-size:11px;color:#71717a;margin-bottom:4px;">'
        f"{icon} {author} &nbsp; {created}</div>"
        f'<div style="{text_style}color:#d4d4d8;font-size:13px;">{text}</div>'
        f"</div>"
    )


def comment_thread_html(comments: list[dict]) -> str:
    """Render a full comment thread as HTML."""
    return "".join(render_comment_html(c) for c in comments)


def is_recently_done(item: BacklogItem, days: int = 7) -> bool:
    """Return True if item should be visible on the board.

    Non-done items are always visible. Done items are visible only if
    updated within the last `days` days.
    """
    if item.status != "done":
        return True
    cutoff = date.today() - timedelta(days=days)
    return item.updated >= cutoff


def relative_time(dt: date) -> str:
    """Format a date as a relative timestamp for card display."""
    days = (date.today() - dt).days
    if days <= 0:
        return "today"
    if days <= 6:
        return f"{days}d"
    if days <= 28:
        return f"{days // 7}w"
    return dt.strftime("%b %-d")


def render_backlog_card_html(item: BacklogItem) -> str:
    """Render a backlog card row as HTML for the planning view."""
    pri_color = PRIORITY_COLORS.get(item.priority, ("#6b7280", "rgba(107,114,128,0.1)"))
    bar_color = pri_color[0] if item.priority in ("P0", "P1") else "transparent"
    cat_style = category_style(item.category)

    badge = comment_badge_html(item.comments)
    complexity = _complexity_badge(item.complexity) if item.complexity else ""

    tag_chips = "".join(
        f'<span style="font-size:10px;color:#9ca3af;background:rgba(156,163,175,0.10);'
        f'padding:1px 6px;border-radius:4px;margin-right:4px;">{t}</span>'
        for t in item.tags
    )

    cat_pill = (
        f'<span style="font-size:10px;color:{cat_style[0]};background:{cat_style[1]};'
        f'padding:1px 8px;border-radius:4px;margin-right:4px;">{item.category}</span>'
    )

    return (
        f'<div style="border-left:3px solid {bar_color};padding:8px 12px;cursor:pointer;'
        f'border-radius:6px;background:rgba(255,255,255,0.03);margin:2px 0;" '
        f'class="backlog-card-row">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="color:#e4e4e7;font-size:13px;">{item.title}</span>'
        f"<span>{badge}{complexity}</span>"
        f"</div>"
        f'<div style="margin-top:4px;">{cat_pill}{tag_chips}</div>'
        f"</div>"
    )
