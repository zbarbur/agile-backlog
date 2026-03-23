"""Pure functions for agile-backlog — framework-independent, fully tested."""

import html as _html
from datetime import date, timedelta

from agile_backlog.config import get_current_sprint
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
    """Render a unified two-line card row as HTML. Used by both board and backlog views."""
    pri_color = PRIORITY_COLORS.get(item.priority, ("#6b7280", "rgba(107,114,128,0.08)"))
    bar_color = pri_color[0]
    cat_style = category_style(item.category)
    title_color = "#71717a" if item.priority in ("P3", "P4") else "#e4e4e7"

    badge = comment_badge_html(item.comments)
    esc_cat = _html.escape(item.category)
    cat_pill = (
        f'<span style="font-size:9px;color:{cat_style[0]};background:{cat_style[1]};'
        f'padding:1px 6px;border-radius:3px;">{esc_cat}</span>'
    )
    esc_pri = _html.escape(item.priority)
    pri_pill = (
        f'<span style="font-size:9px;color:{pri_color[0]};background:{pri_color[1]};'
        f'padding:1px 6px;border-radius:3px;font-weight:600;">{esc_pri}</span>'
    )
    complexity = _complexity_badge(item.complexity) if item.complexity else ""

    tag_chips = "".join(
        f'<span style="font-size:9px;color:#52525b;background:rgba(82,82,91,0.10);'
        f'padding:1px 6px;border-radius:3px;margin-right:4px;">{_html.escape(t)}</span>'
        for t in item.tags
    )

    ts = relative_time(item.updated)

    return (
        f'<div style="border-left:2px solid {bar_color};padding:6px 10px;cursor:pointer;'
        f'border-radius:5px;margin:1px 0;" class="mc-card-row">'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<span style="color:{title_color};font-size:12.5px;font-weight:500;'
        f'flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{_html.escape(item.title)}</span>'
        f'<span style="display:flex;gap:5px;align-items:center;flex-shrink:0;">'
        f"{badge}{complexity}{cat_pill}{pri_pill}</span>"
        f"</div>"
        f'<div style="display:flex;align-items:center;gap:5px;margin-top:3px;">'
        f"{tag_chips}"
        f'<span style="font-size:9px;color:#27272a;margin-left:auto;">{ts}</span>'
        f"</div>"
        f"</div>"
    )


def detect_current_sprint(items: list[BacklogItem]) -> int | None:
    """Return the current sprint number. Checks config first, infers from doing items second."""
    configured = get_current_sprint()
    if configured is not None:
        return configured
    sprints = [i.sprint_target for i in items if i.status == "doing" and i.sprint_target]
    return max(sprints) if sprints else None


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
    """Render a single comment as an iMessage-style chat bubble."""
    author = comment.get("author", "agent")
    text = comment.get("text", "")
    created = comment.get("created", "")
    flagged = comment.get("flagged", False)
    resolved = comment.get("resolved", False)

    is_user = author == "user"
    align = "flex-end" if is_user else "flex-start"
    icon = "👤" if is_user else "🤖"
    bg = "rgba(59,130,246,0.12)" if is_user else "#18181b"
    flat_corner = "border-bottom-right-radius:4px;" if is_user else "border-bottom-left-radius:4px;"
    meta_align = "text-align:right;" if is_user else "text-align:left;"
    border = "border-left:2px solid #f87171;" if flagged and not resolved else ""
    opacity = "opacity:0.35;" if resolved else ""

    return (
        f'<div style="display:flex;flex-direction:column;max-width:82%;align-self:{align};{opacity}">'
        f'<div style="font-size:9px;color:#3f3f46;margin-bottom:2px;padding:0 4px;{meta_align}">'
        f"{icon} {_html.escape(author)} · {_html.escape(str(created))}"
        f"{'  · 🚩' if flagged and not resolved else ''}</div>"
        f'<div style="padding:8px 12px;border-radius:12px;{flat_corner}'
        f'background:{bg};color:#d4d4d8;font-size:12px;line-height:1.5;{border}">'
        f"{_html.escape(text)}</div>"
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
