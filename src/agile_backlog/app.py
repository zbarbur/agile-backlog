# src/app.py
"""NiceGUI Kanban board for agile-backlog — Mission Control dark theme."""

from nicegui import ui

from agile_backlog.models import BacklogItem, slugify
from agile_backlog.tokens import CATEGORY_STYLES, PRIORITY_COLORS, PRIORITY_ORDER

# ---------------------------------------------------------------------------
# Pure functions — importable, framework-independent, fully tested
# ---------------------------------------------------------------------------


def category_style(category: str) -> tuple[str, str]:
    """Return (text_color, bg_color) for a category."""
    return CATEGORY_STYLES.get(category, ("#4b5563", "#f3f4f6"))


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


# ---------------------------------------------------------------------------
# NiceGUI UI — Mission Control dark theme
# ---------------------------------------------------------------------------

STATUSES = ["backlog", "doing", "done"]
LABELS = {"backlog": "BACKLOG", "doing": "IN PROGRESS", "done": "DONE"}

COLUMN_STYLES = {
    "backlog": ("background:#111116;border-radius:8px;padding:8px;", "#71717a"),
    "doing": ("background:#14130e;border:1px solid #2a2618;border-radius:8px;padding:8px;", "#ca8a04"),
    "done": ("background:#0f1210;border-radius:8px;padding:8px;", "#22c55e"),
}

# Global CSS injected into the page head
GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=IBM+Plex+Mono:wght@400;500;600;700"
    "&family=DM+Sans:wght@400;500;600;700&display=swap"
)
GLOBAL_CSS = (
    f'<link href="{GOOGLE_FONTS_URL}" rel="stylesheet">'
    + """
<style>
body {
    background: #0a0a0f !important;
    color: #e4e4e7;
    font-family: 'DM Sans', sans-serif !important;
}
.nicegui-content {
    padding: 0 !important;
}
.q-card {
    box-shadow: none !important;
}
/* Dark dropdown menus */
.q-menu {
    background: #18181b !important;
    border: 1px solid #27272a !important;
}
.q-item {
    color: #e4e4e7 !important;
}
.q-item:hover, .q-item--active {
    background: #27272a !important;
}
.q-item__label {
    color: #e4e4e7 !important;
}
/* Dark select field text */
.q-field__native, .q-field__input {
    color: #e4e4e7 !important;
}
/* Multi-select chips dark styling */
.mc-select .q-chip {
    background: rgba(59,130,246,0.12) !important;
    color: #93c5fd !important;
    font-size: 10px !important;
    height: 20px !important;
}
.mc-select .q-chip__icon {
    color: #93c5fd !important;
}
.mc-search .q-field__control {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    color: #d4d4d8 !important;
    height: 32px !important;
    min-height: 32px !important;
}
.mc-search .q-field__control:focus-within {
    border-color: #3b82f6 !important;
}
.mc-search .q-field__native {
    color: #d4d4d8 !important;
    font-size: 11px !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0 10px !important;
}
.mc-search .q-field__label {
    display: none !important;
}
.mc-search .q-field__control::before,
.mc-search .q-field__control::after {
    display: none !important;
}
.mc-select .q-field__control {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    color: #a1a1aa !important;
    min-height: 32px !important;
}
.mc-select .q-field__native,
.mc-select .q-select__dropdown-icon {
    color: #a1a1aa !important;
    font-size: 11px !important;
}
.mc-select .q-field__label {
    color: #52525b !important;
    font-size: 11px !important;
}
.mc-select .q-field__control::before,
.mc-select .q-field__control::after {
    display: none !important;
}
.mc-done-check .q-checkbox__label {
    font-size: 11px !important;
    color: #71717a !important;
}
.mc-done-check .q-checkbox__inner {
    color: #3b82f6 !important;
}
.mc-card {
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 4px;
    transition: all 0.15s;
    cursor: pointer;
}
.mc-card:hover {
    border-color: #3f3f46;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.mc-card.mc-p1 {
    border-left: 3px solid #ef4444 !important;
}
.mc-card.mc-p2 {
    border-left: 3px solid #3b82f6 !important;
}
.mc-card.mc-p3 {
    border-left: 3px solid #f59e0b !important;
}
.mc-card.mc-done {
    opacity: 0.65;
    color: #71717a;
}
.mc-card.mc-done:hover {
    opacity: 1.0;
}
.mc-move-btn {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important;
    font-weight: 500 !important;
    padding: 2px 7px !important;
    border: 1px solid #27272a !important;
    border-radius: 4px !important;
    background: transparent !important;
    color: #52525b !important;
    cursor: pointer !important;
    transition: all 0.12s !important;
    text-transform: none !important;
    min-height: 0 !important;
    line-height: 1.2 !important;
}
.mc-move-btn:hover {
    border-color: #3f3f46 !important;
    color: #a1a1aa !important;
    background: #1e1e23 !important;
}
/* Detail modal dark styling */
.mc-detail-dialog .q-card {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    color: #e4e4e7 !important;
    max-width: 720px !important;
    width: 720px !important;
}
/* Active filter chip styling */
.mc-filter-chip {
    font-size: 10px !important;
    height: 24px !important;
}
.mc-filter-chip .q-chip__content {
    color: #93c5fd !important;
}
.mc-filter-chip .q-chip__icon--remove {
    color: #93c5fd !important;
    opacity: 0.7;
}
/* Dark form inputs for edit dialogs */
.q-field--outlined .q-field__control {
    border-color: #27272a !important;
    background: #111116 !important;
}
.q-field--outlined .q-field__control:hover {
    border-color: #3f3f46 !important;
}
.q-field--outlined.q-field--focused .q-field__control {
    border-color: #3b82f6 !important;
}
.q-textarea .q-field__native {
    color: #e4e4e7 !important;
}
.q-field__label {
    color: #71717a !important;
}
/* Dark backlog table */
.q-table { background: #18181b !important; color: #e4e4e7 !important; }
.q-table th {
    color: #a1a1aa !important; background: #111116 !important;
    font-size: 11px !important; text-transform: uppercase !important; letter-spacing: 0.05em !important;
}
.q-table td { border-color: #27272a !important; color: #d4d4d8 !important; font-size: 12px !important; }
.q-table tbody tr:hover td { background: #1e1e23 !important; }
.q-table .q-table__bottom { background: #111116 !important; color: #71717a !important; }
</style>
"""
)


def _render_pill(text: str, text_color: str, bg_color: str, *, italic: bool = False, outlined: bool = False) -> None:
    """Render a small badge pill using ui.html with inline styles."""
    style = (
        "display:inline-flex;align-items:center;height:18px;"
        "font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;letter-spacing:0.03em;"
        f"padding:1px 5px;border-radius:3px;white-space:nowrap;color:{text_color};"
    )
    if outlined:
        style += f"background:transparent;border:1px solid {bg_color};"
    else:
        style += f"background:{bg_color};"
    if italic:
        style += "font-style:italic;text-transform:none;"
    else:
        style += "text-transform:uppercase;"
    ui.html(f'<span style="{style}">{text}</span>')


def _show_comment_dialog(item: BacklogItem, save_fn, refresh_fn) -> None:
    """Open a comment dialog for the given backlog item."""
    from datetime import date

    comment_dialog = ui.dialog().classes("mc-detail-dialog")
    with (
        comment_dialog,
        ui.card().style(
            "background:#18181b;border:1px solid #27272a;color:#e4e4e7;"
            "padding:20px;max-width:720px;width:720px;border-radius:8px;"
        ),
    ):
        ui.html(
            '<div style="font-size:14px;font-weight:700;color:#e4e4e7;margin-bottom:12px;">'
            f"\U0001f4ac Comment on: {item.title}</div>"
        )
        # Show existing comments first
        if item.agent_notes:
            ui.html('<div style="font-size:11px;font-weight:600;color:#71717a;margin-bottom:6px;">COMMENTS</div>')
            for idx, note in enumerate(item.agent_notes):
                icon = "\U0001f916" if note.get("flagged") else "\U0001f4ac"
                resolved_style = "opacity:0.5;text-decoration:line-through;" if note.get("resolved") else ""
                author = note.get("author", "")
                author_label = f' <span style="font-size:8px;color:#52525b;">[{author}]</span>' if author else ""
                with ui.element("div").style(
                    f"display:flex;align-items:center;gap:6px;font-size:12px;color:#d4d4d8;"
                    f"margin-bottom:6px;padding:6px 8px;background:#111116;border-radius:4px;{resolved_style}"
                ):
                    ui.html(
                        f'<div style="flex:1;">'
                        f"{icon} {note['text']}{author_label}"
                        f'<span style="font-size:9px;color:#52525b;margin-left:8px;">'
                        f"{note.get('created', '')}</span>"
                        f"</div>"
                    )
                    if not note.get("resolved"):

                        def _resolve_note(note_idx=idx):
                            item.agent_notes[note_idx]["resolved"] = True
                            save_fn(item)
                            comment_dialog.close()
                            refresh_fn()
                            _show_comment_dialog(item, save_fn, refresh_fn)

                        ui.button(
                            "\u2713",
                            on_click=_resolve_note,
                        ).props("flat dense no-caps").style("color:#4ade80;font-size:12px;min-width:24px;padding:2px;")
            ui.html('<div style="border-top:1px solid #27272a;margin:10px 0;"></div>')

        ui.html('<div style="font-size:11px;font-weight:600;color:#71717a;margin-bottom:6px;">ADD COMMENT</div>')
        comment_text = ui.textarea("Comment").props("outlined rows=8").style("width:100%;")
        flag_check = ui.checkbox("Flag for AI").style("font-size:11px;color:#a1a1aa;")

        def _save_comment():
            text = (comment_text.value or "").strip()
            if not text:
                return
            item.agent_notes.append(
                {
                    "text": text,
                    "flagged": flag_check.value,
                    "resolved": False,
                    "created": str(date.today()),
                    "author": "user",
                }
            )
            save_fn(item)
            comment_dialog.close()
            refresh_fn()

        with ui.row().classes("gap-2 mt-3"):
            ui.button("Save", on_click=_save_comment).props("flat dense no-caps").style("color:#3b82f6;")
            ui.button("Cancel", on_click=comment_dialog.close).props("flat dense no-caps").style("color:#a1a1aa;")
    comment_dialog.open()


def _render_card(item: BacklogItem, status: str, move_fn, save_fn=None, refresh_fn=None) -> None:
    """Render a single Kanban card with Mission Control dark theme — click opens detail modal."""
    cat_color, cat_bg = category_style(item.category)
    pri_color, pri_bg = PRIORITY_COLORS.get(item.priority, ("#888", "#f3f4f6"))
    is_done = status == "done"

    card_css = "mc-card"
    pri_class = {"P1": " mc-p1", "P2": " mc-p2", "P3": " mc-p3"}.get(item.priority, "")
    card_css += pri_class
    if is_done:
        card_css += " mc-done"

    # Build the detail dialog
    detail_dialog = ui.dialog().classes("mc-detail-dialog")
    with (
        detail_dialog,
        ui.card().style(
            "background:#18181b;border:1px solid #27272a;color:#e4e4e7;"
            "padding:20px;max-width:720px;width:720px;border-radius:8px;"
            "max-height:80vh;overflow-y:auto;"
        ),
    ):
        _render_detail_modal_content(item, is_done)
        with ui.row().classes("gap-2").style("margin-top:12px;"):
            if not is_done and save_fn and refresh_fn:
                ui.button(
                    "Edit",
                    on_click=lambda d=detail_dialog, i=item: (
                        d.close(),
                        _show_edit_dialog(i, save_fn, refresh_fn),
                    ),
                ).props("flat dense no-caps").style("color:#3b82f6;font-size:11px;")
            ui.button("Close", on_click=detail_dialog.close).props("flat dense no-caps").style(
                "color:#a1a1aa;font-size:11px;"
            )

    card_el = ui.element("div").classes(card_css)
    card_el.on("click", lambda _e, d=detail_dialog: d.open())

    with card_el:
        # Row 1: title (left) + comment button (top-right corner)
        with ui.element("div").style("display:flex;align-items:flex-start;justify-content:space-between;gap:8px;"):
            title_style = "font-size:12.5px;font-weight:600;line-height:1.3;font-family:'DM Sans',sans-serif;"
            if is_done:
                title_style += "text-decoration:line-through;color:#52525b;"
            else:
                title_style += "color:#e4e4e7;"
            ui.html(f'<div style="{title_style}">{item.title}</div>').style("flex:1;min-width:0;")

            # Comment button (top-right corner)
            if not is_done and save_fn and refresh_fn:
                comment_count = len(item.agent_notes)
                has_flagged = any(n.get("flagged") and not n.get("resolved") for n in item.agent_notes)
                icon_color = "#f87171" if has_flagged else "#52525b" if comment_count == 0 else "#60a5fa"
                badge_html = (
                    f'<span style="position:relative;cursor:pointer;color:{icon_color};'
                    f'font-size:14px;padding:2px 4px;">\U0001f4ac'
                )
                if comment_count > 0:
                    badge_html += (
                        f'<span style="position:absolute;top:-4px;right:-4px;font-size:8px;'
                        f"background:#3b82f6;color:white;border-radius:50%;width:14px;height:14px;"
                        f'display:flex;align-items:center;justify-content:center;">{comment_count}</span>'
                    )
                badge_html += "</span>"
                comment_btn = ui.element("div").style("flex-shrink:0;")
                comment_btn.on("click.stop", lambda _e, i=item: _show_comment_dialog(i, save_fn, refresh_fn))
                with comment_btn:
                    ui.html(badge_html)

        # Row 2: move buttons (left) + badges (right)
        opacity = "opacity:0.5;" if is_done else ""
        pill_base = (
            "font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;"
            "padding:1px 5px;border-radius:3px;letter-spacing:0.03em;white-space:nowrap;"
        )

        with ui.element("div").style("display:flex;align-items:center;justify-content:space-between;margin-top:5px;"):
            # Move buttons (left)
            if not is_done:
                with ui.element("div").style("display:flex;gap:4px;"):
                    other_statuses = [s for s in STATUSES if s != status]
                    for target in other_statuses:
                        arrow = "\u2190" if STATUSES.index(target) < STATUSES.index(status) else "\u2192"
                        ui.button(
                            f"{arrow} {target}",
                            on_click=lambda _e, i=item, t=target: move_fn(i, t),
                        ).classes("mc-move-btn").props("flat dense unelevated no-caps")
            else:
                ui.element("div")  # spacer for done cards

            # Badges (bottom-right)
            badges_html = (
                f'<span style="{pill_base}text-transform:uppercase;'
                f'color:{cat_color};background:{cat_bg};{opacity}">{item.category}</span> '
                f'<span style="{pill_base}text-transform:uppercase;'
                f'color:{pri_color};background:{pri_bg};{opacity}">{item.priority}</span>'
            )
            if item.phase:
                badges_html += (
                    f' <span style="{pill_base}'
                    f'font-style:italic;text-transform:none;color:#71717a;background:#1e1e23;">'
                    f"{item.phase}</span>"
                )
            if item.sprint_target is not None:
                sprint_opacity = "opacity:0.4;" if is_done else ""
                badges_html += (
                    f' <span style="{pill_base}font-weight:500;text-transform:none;'
                    f'color:#52525b;background:transparent;border:1px solid #27272a;{sprint_opacity}">'
                    f"S{item.sprint_target}</span>"
                )
            ui.html(f'<div style="display:flex;gap:4px;align-items:center;">{badges_html}</div>')

        # Row 3: tags
        if item.tags:
            tags_html = " ".join(
                f'<span style="font-size:8px;color:#6b7280;background:#1e1e23;'
                f"padding:1px 5px;border-radius:3px;font-family:'IBM Plex Mono',monospace;"
                f'white-space:nowrap;">{tag}</span>'
                for tag in item.tags
            )
            ui.html(f'<div style="display:flex;gap:3px;flex-wrap:wrap;margin-top:4px;">{tags_html}</div>')


def _render_detail_modal_content(item: BacklogItem, is_done: bool = False) -> None:
    """Render the content inside the detail modal dialog."""
    cat_color, cat_bg = category_style(item.category)
    pri_color, pri_bg = PRIORITY_COLORS.get(item.priority, ("#888", "#f3f4f6"))

    label_style = (
        "font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;"
        "color:#52525b;text-transform:uppercase;letter-spacing:0.08em;"
        "margin-top:10px;margin-bottom:3px;"
    )
    value_style = "color:#d4d4d8;font-size:12px;font-family:'DM Sans',sans-serif;"

    # Title
    title_style = "font-size:16px;font-weight:700;color:#e4e4e7;line-height:1.3;font-family:'DM Sans',sans-serif;"
    if is_done:
        title_style += "text-decoration:line-through;color:#52525b;"
    ui.html(f'<div style="{title_style}">{item.title}</div>')

    # Badges row
    pill_base = (
        "font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;"
        "padding:1px 5px;border-radius:3px;letter-spacing:0.03em;white-space:nowrap;"
    )
    badges_html = (
        f'<span style="{pill_base}text-transform:uppercase;color:{cat_color};background:{cat_bg}">'
        f"{item.category}</span> "
        f'<span style="{pill_base}text-transform:uppercase;color:{pri_color};background:{pri_bg}">'
        f"{item.priority}</span>"
    )
    if item.phase:
        badges_html += (
            f' <span style="{pill_base}font-style:italic;text-transform:none;'
            f'color:#71717a;background:#1e1e23;">{item.phase}</span>'
        )
    if item.design_reviewed:
        badges_html += (
            f' <span style="{pill_base}font-size:8px;color:#4ade80;'
            f'background:rgba(74,222,128,0.1);">&#10003; design</span>'
        )
    if item.code_reviewed:
        badges_html += (
            f' <span style="{pill_base}font-size:8px;color:#4ade80;'
            f'background:rgba(74,222,128,0.1);">&#10003; code</span>'
        )
    if item.sprint_target is not None:
        badges_html += (
            f' <span style="{pill_base}font-weight:500;text-transform:none;'
            f'color:#52525b;background:transparent;border:1px solid #27272a;">'
            f"S{item.sprint_target}</span>"
        )
    ui.html(f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;">{badges_html}</div>')

    # Detail fields
    if item.goal:
        ui.html(f'<div style="{label_style}">Goal</div>')
        ui.html(f'<div style="{value_style}">{item.goal}</div>')

    if item.complexity:
        ui.html(f'<div style="{label_style}">Complexity</div>')
        ui.html(
            "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:700;"
            f'padding:1px 6px;border-radius:3px;background:rgba(59,130,246,0.12);color:#60a5fa;">'
            f"{item.complexity}</span>"
        )

    if item.description:
        ui.html(f'<div style="{label_style}">Description</div>')
        ui.markdown(item.description).style(value_style)

    if item.acceptance_criteria:
        ui.html(f'<div style="{label_style}">Acceptance Criteria</div>')
        li_items = "".join(
            f'<li style="margin-bottom:1px;color:#a1a1aa;font-size:11px;">{ac}</li>' for ac in item.acceptance_criteria
        )
        ui.html(f'<ul style="padding-left:14px;">{li_items}</ul>')

    if item.technical_specs:
        ui.html(f'<div style="{label_style}">Technical Specs</div>')
        li_items = "".join(
            f'<li style="margin-bottom:1px;color:#a1a1aa;font-size:11px;">{ts}</li>' for ts in item.technical_specs
        )
        ui.html(f'<ul style="padding-left:14px;">{li_items}</ul>')

    if item.test_plan:
        ui.html(f'<div style="{label_style}">Test Plan</div>')
        li_items = "".join(
            f'<li style="margin-bottom:1px;color:#a1a1aa;font-size:11px;">{tp}</li>' for tp in item.test_plan
        )
        ui.html(f'<ul style="padding-left:14px;">{li_items}</ul>')

    if item.notes:
        ui.html(f'<div style="{label_style}">Notes</div>')
        ui.html(f'<div style="{value_style}">{item.notes}</div>')

    if item.tags:
        ui.html(f'<div style="{label_style}">Tags</div>')
        tag_html = " ".join(
            "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;"
            f"background:#1e1e23;color:#a1a1aa;padding:1px 6px;"
            f'border-radius:3px;margin-right:2px;">{t}</span>'
            for t in item.tags
        )
        ui.html(tag_html)

    if item.depends_on:
        ui.html(f'<div style="{label_style}">Depends on</div>')
        ui.html(f'<div style="{value_style}">{", ".join(item.depends_on)}</div>')

    # Comments (agent_notes)
    if item.agent_notes:
        ui.html(f'<div style="{label_style}">Comments</div>')
        for note in item.agent_notes:
            flagged = note.get("flagged", False)
            resolved = note.get("resolved", False)
            text = note.get("text", "")
            created = note.get("created", "")

            if resolved:
                icon = "&#10003;"
                row_style = "opacity:0.5;text-decoration:line-through;"
                icon_style = "color:#71717a;margin-right:6px;"
            elif flagged:
                icon = "\U0001f916"
                row_style = ""
                icon_style = "color:#f87171;margin-right:6px;"
            else:
                icon = ""
                row_style = ""
                icon_style = ""

            note_html = (
                f'<div style="display:flex;align-items:baseline;gap:4px;font-size:11px;'
                f'color:#a1a1aa;margin-bottom:3px;{row_style}">'
            )
            if icon:
                note_html += f'<span style="{icon_style}">{icon}</span>'
            note_html += f"<span>{text}</span>"
            if created:
                note_html += (
                    f'<span style="margin-left:auto;font-size:9px;color:#3f3f46;'
                    f"font-family:'IBM Plex Mono',monospace;white-space:nowrap;\">{created}</span>"
                )
            note_html += "</div>"
            ui.html(note_html)

    # Footer
    ui.html(
        '<div style="display:flex;gap:12px;margin-top:10px;padding-top:8px;border-top:1px solid #1e1e23;">'
        "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;color:#3f3f46;\">"
        f"Sprint: {item.sprint_target or 'Unplanned'}</span>"
        "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;color:#3f3f46;\">"
        f"Created: {item.created}</span>"
        "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;color:#3f3f46;\">"
        f"Updated: {item.updated}</span>"
        "</div>"
    )


def _show_edit_dialog(item: BacklogItem, save_fn, refresh_fn) -> None:
    """Open an edit dialog for the given backlog item."""
    edit_dialog = ui.dialog().classes("mc-detail-dialog")
    with (
        edit_dialog,
        ui.card().style(
            "background:#18181b;border:1px solid #27272a;color:#e4e4e7;"
            "padding:20px;max-width:720px;width:720px;border-radius:8px;"
        ),
    ):
        ui.html('<div style="font-size:14px;font-weight:700;color:#e4e4e7;margin-bottom:12px;">Edit Item</div>')

        title_input = ui.input("Title", value=item.title).props("dense outlined").style("width:100%;")
        from agile_backlog.yaml_store import load_all as _load_all

        _items = _load_all()
        all_categories = sorted({i.category for i in _items})
        with ui.row().classes("gap-2").style("width:100%;"):
            priority_input = (
                ui.select(label="Priority", options=["P1", "P2", "P3"], value=item.priority)
                .props("dense outlined")
                .style("min-width:100px;")
            )
            category_input = (
                ui.select(label="Category", options=all_categories, value=item.category, with_input=True)
                .props("dense outlined")
                .style("flex:1;")
            )
        with ui.row().classes("gap-2").style("width:100%;"):
            current = detect_current_sprint(_items)
            sprint_options_edit = {None: "Backlog (unplanned)"}
            if current is not None:
                sprint_options_edit[current] = f"Sprint {current} (current)"
                sprint_options_edit[current + 1] = f"Sprint {current + 1} (next)"
            if item.sprint_target is not None and item.sprint_target not in sprint_options_edit:
                sprint_options_edit[item.sprint_target] = f"Sprint {item.sprint_target}"
            sprint_input = (
                ui.select(label="Sprint", options=sprint_options_edit, value=item.sprint_target)
                .props("dense outlined")
                .style("min-width:120px;")
            )
            phase_input = (
                ui.select(
                    label="Phase",
                    options={None: "(none)", "plan": "plan", "spec": "spec", "build": "build", "review": "review"},
                    value=item.phase,
                )
                .props("dense outlined")
                .style("min-width:120px;")
            )
            complexity_input = (
                ui.select(
                    label="Complexity",
                    options={None: "(none)", "S": "S", "M": "M", "L": "L"},
                    value=item.complexity,
                )
                .props("dense outlined")
                .style("min-width:140px;")
            )
        all_tags = sorted({t for i in _items for t in i.tags})
        tag_input = (
            ui.select(
                label="Tags",
                options=all_tags,
                multiple=True,
                value=list(item.tags),
                with_input=True,
                new_value_mode="add-unique",
            )
            .props("dense outlined use-chips")
            .classes("mc-select")
            .style("width:100%;")
        )
        goal_input = ui.textarea("Goal", value=item.goal).props("dense outlined autogrow").style("width:100%;")
        description_input = (
            ui.textarea("Description", value=item.description).props("outlined autogrow rows=6").style("width:100%;")
        )
        ac_input = (
            ui.textarea("Acceptance Criteria (one per line)", value="\n".join(item.acceptance_criteria))
            .props("outlined autogrow rows=6")
            .style("width:100%;")
        )
        ts_input = (
            ui.textarea("Technical Specs (one per line)", value="\n".join(item.technical_specs))
            .props("outlined autogrow rows=6")
            .style("width:100%;")
        )
        tp_input = (
            ui.textarea("Test Plan (one per line)", value="\n".join(item.test_plan))
            .props("outlined autogrow rows=6")
            .style("width:100%;")
        )
        notes_input = ui.textarea("Notes", value=item.notes).props("outlined autogrow rows=6").style("width:100%;")

        def _split_lines(text: str) -> list[str]:
            return [line.strip() for line in text.split("\n") if line.strip()] if text else []

        def save_and_close():
            item.title = title_input.value or item.title
            item.priority = priority_input.value
            item.category = category_input.value or item.category
            sprint_val = sprint_input.value
            item.sprint_target = int(sprint_val) if sprint_val is not None and sprint_val != "" else None
            item.phase = phase_input.value
            item.complexity = complexity_input.value
            item.tags = list(tag_input.value or [])
            item.goal = goal_input.value or ""
            item.description = description_input.value or ""
            item.acceptance_criteria = _split_lines(ac_input.value)
            item.technical_specs = _split_lines(ts_input.value)
            item.test_plan = _split_lines(tp_input.value)
            item.notes = notes_input.value or ""
            save_fn(item)
            edit_dialog.close()
            refresh_fn()

        with ui.row().classes("gap-2 mt-3"):
            ui.button("Save", on_click=save_and_close).props("flat dense no-caps").style("color:#3b82f6;")
            ui.button("Cancel", on_click=edit_dialog.close).props("flat dense no-caps").style("color:#a1a1aa;")

    edit_dialog.open()


def _render_detail_panel(item: BacklogItem) -> None:
    """Render the expandable details section of a card."""
    label_style = (
        "font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;"
        "color:#52525b;text-transform:uppercase;letter-spacing:0.08em;"
        "margin-top:6px;margin-bottom:2px;"
    )
    value_style = "color:#d4d4d8;font-size:12px;font-family:'DM Sans',sans-serif;"

    with ui.element("div").style(
        "margin-top:8px;padding-top:8px;border-top:1px solid #1e1e23;font-size:11px;color:#a1a1aa;line-height:1.6;"
    ):
        if item.goal:
            ui.html(f'<div style="{label_style}">Goal</div>')
            ui.html(f'<div style="{value_style}">{item.goal}</div>')

        if item.complexity:
            ui.html(f'<div style="{label_style}">Complexity</div>')
            ui.html(
                "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:700;"
                f'padding:1px 6px;border-radius:3px;background:rgba(59,130,246,0.12);color:#60a5fa;">'
                f"{item.complexity}</span>"
            )

        if item.description:
            ui.html(f'<div style="{label_style}">Description</div>')
            ui.html(f'<div style="{value_style}">{item.description}</div>')

        if item.acceptance_criteria:
            ui.html(f'<div style="{label_style}">Acceptance Criteria</div>')
            li_items = "".join(
                f'<li style="margin-bottom:1px;color:#a1a1aa;font-size:11px;">{ac}</li>'
                for ac in item.acceptance_criteria
            )
            ui.html(f'<ul style="padding-left:14px;">{li_items}</ul>')

        if item.technical_specs:
            ui.html(f'<div style="{label_style}">Technical Specs</div>')
            li_items = "".join(
                f'<li style="margin-bottom:1px;color:#a1a1aa;font-size:11px;">{ts}</li>' for ts in item.technical_specs
            )
            ui.html(f'<ul style="padding-left:14px;">{li_items}</ul>')

        if item.test_plan:
            ui.html(f'<div style="{label_style}">Test Plan</div>')
            li_items = "".join(
                f'<li style="margin-bottom:1px;color:#a1a1aa;font-size:11px;">{tp}</li>' for tp in item.test_plan
            )
            ui.html(f'<ul style="padding-left:14px;">{li_items}</ul>')

        if item.notes:
            ui.html(f'<div style="{label_style}">Notes</div>')
            ui.html(f'<div style="{value_style}">{item.notes}</div>')

        if item.tags:
            ui.html(f'<div style="{label_style}">Tags</div>')
            tag_html = " ".join(
                "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;"
                f"background:#1e1e23;color:#a1a1aa;padding:1px 6px;"
                f'border-radius:3px;margin-right:2px;">{t}</span>'
                for t in item.tags
            )
            ui.html(tag_html)

        if item.depends_on:
            ui.html(f'<div style="{label_style}">Depends on</div>')
            ui.html(f'<div style="{value_style}">{", ".join(item.depends_on)}</div>')

        # Footer
        ui.html(
            '<div style="display:flex;gap:12px;margin-top:8px;padding-top:6px;border-top:1px solid #1e1e23;">'
            "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;color:#3f3f46;\">"
            f"Sprint: {item.sprint_target or 'Unplanned'}</span>"
            "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;color:#3f3f46;\">"
            f"Created: {item.created}</span>"
            "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;color:#3f3f46;\">"
            f"Updated: {item.updated}</span>"
            "</div>"
        )


BACKLOG_SORT_OPTIONS = {"priority": "Priority", "category": "Category", "title": "Title"}


def _render_backlog_list(
    backlog_items: list[BacklogItem],
    current_sprint: int | None,
    move_fn,
    save_fn,
    refresh_fn,
) -> None:
    """Render the backlog management list view as a sortable table."""
    # Header
    with ui.element("div").style("display:flex;align-items:center;gap:10px;margin-bottom:10px;"):
        ui.html(
            "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:10px;"
            "font-weight:700;text-transform:uppercase;letter-spacing:0.12em;"
            'color:#71717a;">BACKLOG</span>'
        )
        ui.html(
            f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;"
            f"font-weight:500;color:#3f3f46;background:#1e1e23;padding:1px 6px;"
            f'border-radius:4px;">{len(backlog_items)}</span>'
        )

    if not backlog_items:
        ui.html(
            '<div style="font-size:11px;color:#52525b;padding:8px 6px;'
            "font-style:italic;font-family:'DM Sans',sans-serif;\">No backlog items match filters.</div>"
        )
        return

    # Build item lookup for row-click
    item_lookup = {item.id: item for item in backlog_items}

    # Table columns
    columns = [
        {"name": "title", "label": "Title", "field": "title", "sortable": True, "align": "left"},
        {"name": "priority", "label": "Priority", "field": "priority", "sortable": True},
        {"name": "category", "label": "Category", "field": "category", "sortable": True},
        {"name": "sprint", "label": "Sprint", "field": "sprint", "sortable": True},
        {"name": "phase", "label": "Phase", "field": "phase", "sortable": True},
        {"name": "complexity", "label": "Complexity", "field": "complexity", "sortable": True},
        {"name": "created", "label": "Created", "field": "created", "sortable": True},
        {"name": "updated", "label": "Updated", "field": "updated", "sortable": True},
    ]
    rows = [
        {
            "id": item.id,
            "title": item.title,
            "priority": item.priority,
            "category": item.category,
            "sprint": f"S{item.sprint_target}" if item.sprint_target is not None else "",
            "phase": item.phase or "",
            "complexity": item.complexity or "",
            "created": str(item.created),
            "updated": str(item.updated),
        }
        for item in backlog_items
    ]

    # Inject dark table CSS
    ui.add_head_html("""<style>
    .mc-backlog-table .q-table { background: #18181b !important; color: #e4e4e7 !important; }
    .mc-backlog-table .q-table th { color: #71717a !important; background: #111116 !important; }
    .mc-backlog-table .q-table td { border-color: #27272a !important; }
    .mc-backlog-table .q-table tbody tr:hover { background: #27272a !important; cursor: pointer; }
    .mc-backlog-table .q-table thead tr { border-bottom: 1px solid #27272a !important; }
    .mc-backlog-table .q-table__bottom { background: #111116 !important; color: #71717a !important; }
    </style>""")

    def open_detail_modal(item_id: str):
        item = item_lookup.get(item_id)
        if not item:
            return
        detail_dialog = ui.dialog().classes("mc-detail-dialog")
        with (
            detail_dialog,
            ui.card().style(
                "background:#18181b;border:1px solid #27272a;color:#e4e4e7;"
                "padding:20px;max-width:720px;width:720px;border-radius:8px;"
            ),
        ):
            _render_detail_modal_content(item, False)
            with ui.row().classes("gap-2").style("margin-top:12px;"):
                if save_fn and refresh_fn:
                    ui.button(
                        "Edit",
                        on_click=lambda d=detail_dialog, i=item: (
                            d.close(),
                            _show_edit_dialog(i, save_fn, refresh_fn),
                        ),
                    ).props("flat dense no-caps").style("color:#3b82f6;font-size:11px;")
                ui.button("Close", on_click=detail_dialog.close).props("flat dense no-caps").style(
                    "color:#a1a1aa;font-size:11px;"
                )
        detail_dialog.open()

    with ui.element("div").classes("mc-backlog-table"):
        table = ui.table(columns=columns, rows=rows, row_key="id").props("flat bordered dense")
        table.on("row-click", lambda e: open_detail_modal(e.args[1]["id"]))


@ui.page("/")
def kanban_page():
    """Render the Kanban board — Mission Control dark theme."""
    from agile_backlog.yaml_store import item_exists, load_all, save_item

    # --- Inject global styles ---
    ui.add_head_html(GLOBAL_CSS)

    # --- Load data ---
    all_items = load_all()
    # Config-based sprint takes precedence over inference
    from agile_backlog.config import get_current_sprint

    current_sprint = get_current_sprint() or detect_current_sprint(all_items)

    with ui.element("div").style("width:100%;padding:16px 24px;"):
        # === Header Row 1 ===
        with ui.element("div").style("display:flex;align-items:center;gap:12px;margin-bottom:12px;"):
            ui.html(
                '<span style="font-size:16px;font-weight:700;color:#fafafa;'
                "letter-spacing:-0.02em;font-family:'DM Sans',sans-serif;"
                '">agile-backlog</span>'
            )
            if current_sprint is not None:
                ui.html(
                    f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:600;"
                    f"color:#3b82f6;background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.25);"
                    f'padding:2px 10px;border-radius:4px;letter-spacing:0.05em;">'
                    f"SPRINT {current_sprint}</span>"
                )

            ui.element("div").style("flex:1;")

            # View toggle — track state in a mutable dict
            view_mode = {"current": "board"}

            toggle_container = ui.element("div").style(
                "display:flex;background:#18181b;border:1px solid #27272a;border-radius:6px;overflow:hidden;"
            )

            def _set_view(mode: str):
                view_mode["current"] = mode
                # Update button styles
                if mode == "board":
                    board_btn_el.style("background:#fafafa;color:#09090b;")
                    backlog_btn_el.style("background:transparent;color:#71717a;")
                else:
                    board_btn_el.style("background:transparent;color:#71717a;")
                    backlog_btn_el.style("background:#fafafa;color:#09090b;")
                render_board.refresh()

            with toggle_container:
                board_btn_el = (
                    ui.button("Board", on_click=lambda: _set_view("board"))
                    .props("flat dense no-caps unelevated")
                    .style(
                        "font-size:11px;font-weight:600;padding:4px 14px;border-radius:0;"
                        "background:#fafafa;color:#09090b;min-height:0;"
                    )
                )
                backlog_btn_el = (
                    ui.button("Backlog", on_click=lambda: _set_view("backlog"))
                    .props("flat dense no-caps unelevated")
                    .style(
                        "font-size:11px;font-weight:600;padding:4px 14px;border-radius:0;"
                        "background:transparent;color:#71717a;min-height:0;"
                    )
                )

            # Add Item button
            def _show_add_dialog():
                add_dialog = ui.dialog().classes("mc-detail-dialog")
                with (
                    add_dialog,
                    ui.card().style(
                        "background:#18181b;border:1px solid #27272a;color:#e4e4e7;"
                        "padding:20px;max-width:720px;width:720px;border-radius:8px;"
                    ),
                ):
                    ui.html(
                        '<div style="font-size:16px;font-weight:700;color:#e4e4e7;margin-bottom:16px;">'
                        "New Backlog Item</div>"
                    )
                    add_title = ui.input("Title *").props("outlined").style("width:100%;")
                    with ui.row().classes("gap-2").style("width:100%;"):
                        add_priority = (
                            ui.select(label="Priority", options=["P1", "P2", "P3"], value="P2")
                            .props("dense outlined")
                            .style("min-width:100px;")
                        )
                        all_cats = sorted({i.category for i in all_items})
                        add_category = (
                            ui.select(label="Category *", options=all_cats, value=None, with_input=True)
                            .props("dense outlined")
                            .style("flex:1;")
                        )
                        add_sprint_options = {None: "Backlog (unplanned)"}
                        if current_sprint is not None:
                            add_sprint_options[current_sprint] = f"Sprint {current_sprint} (current)"
                            add_sprint_options[current_sprint + 1] = f"Sprint {current_sprint + 1} (next)"
                        add_sprint = (
                            ui.select(
                                label="Target",
                                options=add_sprint_options,
                                value=None,
                            )
                            .props("dense outlined")
                            .style("min-width:120px;")
                        )
                    add_description = ui.textarea("Description").props("outlined").style("width:100%;min-height:150px;")
                    add_error = ui.label("").style("color:#f87171;font-size:11px;display:none;")

                    def _save_new_item():
                        title = (add_title.value or "").strip()
                        cat = (add_category.value or "").strip()
                        if not title or not cat:
                            add_error.style("display:block;")
                            add_error.set_text("Title and Category are required.")
                            return
                        item_id = slugify(title)
                        if not item_id:
                            add_error.style("display:block;")
                            add_error.set_text("Title produces an invalid ID.")
                            return
                        # Handle slug collision
                        base_id = item_id
                        counter = 2
                        while item_exists(item_id):
                            item_id = f"{base_id}-{counter}"
                            counter += 1
                        sprint_val = add_sprint.value
                        new_item = BacklogItem(
                            id=item_id,
                            title=title,
                            priority=add_priority.value,
                            category=cat,
                            description=add_description.value or "",
                            sprint_target=int(sprint_val) if sprint_val is not None and sprint_val != "" else None,
                        )
                        save_item(new_item)
                        add_dialog.close()
                        render_board.refresh()

                    with ui.row().classes("gap-2 mt-3"):
                        ui.button("Save", on_click=_save_new_item).props("flat dense no-caps").style("color:#3b82f6;")
                        ui.button("Cancel", on_click=add_dialog.close).props("flat dense no-caps").style(
                            "color:#a1a1aa;"
                        )
                add_dialog.open()

            ui.button("+ Add Item", on_click=_show_add_dialog).props("flat dense no-caps unelevated").style(
                "font-size:11px;font-weight:600;color:#3b82f6;background:rgba(59,130,246,0.08);"
                "border:1px solid rgba(59,130,246,0.2);border-radius:6px;padding:4px 14px;min-height:0;"
            )

            # Show done checkbox
            done_check = (
                ui.checkbox("Show done", value=True).classes("mc-done-check").style("font-size:11px;color:#71717a;")
            )

        # === Filter Row 2 ===
        priority_options = {"P1": "P1", "P2": "P2", "P3": "P3"}
        categories = sorted({i.category for i in all_items})
        category_options = {c: c for c in categories}
        sprints = sorted({i.sprint_target for i in all_items if i.sprint_target is not None})
        sprint_options = {}
        if current_sprint is not None:
            sprint_options["current"] = f"Current (S{current_sprint})"
        sprint_options["unplanned"] = "Unplanned"
        for s in sprints:
            sprint_options[s] = f"Sprint {s}"
        phases = sorted({i.phase for i in all_items if i.phase})
        phase_options = {None: "All phases", **{p: p for p in phases}}
        all_tags_filter = sorted({t for i in all_items for t in i.tags})

        with ui.element("div").style(
            "display:flex;gap:8px;padding-bottom:12px;border-bottom:1px solid #1e1e23;"
            "margin-bottom:4px;align-items:end;"
        ):
            priority_select = (
                ui.select(label="Priority", options=priority_options, multiple=True, value=[])
                .props("dense outlined use-chips")
                .classes("mc-select")
                .style("min-width:130px;")
            )
            category_select = (
                ui.select(label="Category", options=category_options, multiple=True, value=[])
                .props("dense outlined use-chips")
                .classes("mc-select")
                .style("min-width:130px;")
            )
            sprint_select = (
                ui.select(label="Sprint", options=sprint_options, multiple=True, value=[])
                .props("dense outlined use-chips")
                .classes("mc-select")
                .style("min-width:130px;")
            )
            phase_select = (
                ui.select(label="Phase", options=phase_options, value=None)
                .props("dense outlined")
                .classes("mc-select")
                .style("width:130px;")
            )
            tag_select = (
                ui.select(label="Tags", options=all_tags_filter, multiple=True, value=[])
                .props("dense outlined use-chips")
                .classes("mc-select")
                .style("min-width:130px;")
            )
            search_input = (
                ui.input(placeholder="Search by title, description, tags...")
                .props("dense outlined")
                .classes("mc-search")
                .style("flex:1;min-height:32px;")
            )

        # === Active Filter Chips ===
        filter_chips_row = ui.row().classes("gap-1 flex-wrap").style("margin-bottom:10px;")

        def _refresh_chips():
            filter_chips_row.clear()
            with filter_chips_row:
                pvals = priority_select.value or []
                for pv in pvals:
                    chip = ui.chip(f"Priority: {pv}", removable=True, color="blue-grey-9").classes("mc-filter-chip")
                    chip.on(
                        "remove",
                        lambda _e, v=pv: (
                            priority_select.set_value([x for x in (priority_select.value or []) if x != v]),
                            render_board.refresh(),
                        ),
                    )
                cvals = category_select.value or []
                for cv in cvals:
                    chip = ui.chip(f"Category: {cv}", removable=True, color="blue-grey-9").classes("mc-filter-chip")
                    chip.on(
                        "remove",
                        lambda _e, v=cv: (
                            category_select.set_value([x for x in (category_select.value or []) if x != v]),
                            render_board.refresh(),
                        ),
                    )
                svals = sprint_select.value or []
                for sv in svals:
                    label = sprint_options.get(sv, str(sv))
                    chip = ui.chip(f"Sprint: {label}", removable=True, color="blue-grey-9").classes("mc-filter-chip")
                    chip.on(
                        "remove",
                        lambda _e, v=sv: (
                            sprint_select.set_value([x for x in (sprint_select.value or []) if x != v]),
                            render_board.refresh(),
                        ),
                    )
                if phase_select.value is not None:
                    chip = ui.chip(f"Phase: {phase_select.value}", removable=True, color="blue-grey-9").classes(
                        "mc-filter-chip"
                    )
                    chip.on(
                        "remove",
                        lambda _e: (phase_select.set_value(None), render_board.refresh()),
                    )
                tvals = tag_select.value or []
                for tv in tvals:
                    chip = ui.chip(f"Tag: {tv}", removable=True, color="blue-grey-9").classes("mc-filter-chip")
                    chip.on(
                        "remove",
                        lambda _e, v=tv: (
                            tag_select.set_value([x for x in (tag_select.value or []) if x != v]),
                            render_board.refresh(),
                        ),
                    )
                sq = search_input.value or ""
                if sq:
                    chip = ui.chip(f'Search: "{sq}"', removable=True, color="blue-grey-9").classes("mc-filter-chip")
                    chip.on(
                        "remove",
                        lambda _e: (search_input.set_value(""), render_board.refresh()),
                    )

        # === Board ===
        def move_item(item: BacklogItem, target: str):
            item.status = target
            if target == "doing":
                item.phase = item.phase or "plan"
            elif target == "backlog":
                item.phase = None
            save_item(item)
            render_board.refresh()

        @ui.refreshable
        def render_board():
            _refresh_chips()
            items = load_all()

            pf_list = priority_select.value or []
            cf_list = category_select.value or []
            sf_list = sprint_select.value or []
            phf = phase_select.value
            tf_list = tag_select.value or []
            sq = search_input.value or ""
            sd = done_check.value

            # Resolve "current" sprint value to actual sprint number
            resolved_sprints: list[int | str] = []
            for sv in sf_list:
                if sv == "current" and current_sprint is not None:
                    resolved_sprints.append(current_sprint)
                else:
                    resolved_sprints.append(sv)

            backlog_items = [i for i in items if i.status == "backlog"]
            doing_items = [i for i in items if i.status == "doing"]
            done_items = [i for i in items if i.status == "done"]

            # Apply search filter via filter_items (sprint handled below for multi-select)
            filtered_backlog = filter_items(backlog_items, search=sq)
            filtered_doing = doing_items
            filtered_done = done_items

            # Multi-select priority filter
            if pf_list:
                filtered_backlog = [i for i in filtered_backlog if i.priority in pf_list]
                filtered_doing = [i for i in filtered_doing if i.priority in pf_list]
                filtered_done = [i for i in filtered_done if i.priority in pf_list]

            # Multi-select category filter
            if cf_list:
                filtered_backlog = [i for i in filtered_backlog if i.category in cf_list]
                filtered_doing = [i for i in filtered_doing if i.category in cf_list]
                filtered_done = [i for i in filtered_done if i.category in cf_list]

            # Multi-select sprint filter
            if resolved_sprints:
                has_unplanned = "unplanned" in resolved_sprints
                numeric_sprints = [s for s in resolved_sprints if s != "unplanned"]

                def _sprint_match(item_sprint: int | None) -> bool:
                    if item_sprint is None:
                        return has_unplanned
                    return item_sprint in numeric_sprints

                filtered_backlog = [i for i in filtered_backlog if _sprint_match(i.sprint_target)]
                filtered_doing = [i for i in filtered_doing if _sprint_match(i.sprint_target)]
                filtered_done = [i for i in filtered_done if _sprint_match(i.sprint_target)]

            if phf is not None:
                filtered_backlog = [i for i in filtered_backlog if i.phase == phf]
                filtered_doing = [i for i in filtered_doing if i.phase == phf]
                filtered_done = [i for i in filtered_done if i.phase == phf]

            # Multi-select tag filter (ANY match)
            if tf_list:
                tf_set = set(tf_list)
                filtered_backlog = [i for i in filtered_backlog if tf_set & set(i.tags)]
                filtered_doing = [i for i in filtered_doing if tf_set & set(i.tags)]
                filtered_done = [i for i in filtered_done if tf_set & set(i.tags)]

            # Apply search to doing/done too
            if sq:
                q = sq.lower()
                filtered_doing = [
                    i
                    for i in filtered_doing
                    if q in i.title.lower() or q in i.description.lower() or any(q in t.lower() for t in i.tags)
                ]
                filtered_done = [
                    i
                    for i in filtered_done
                    if q in i.title.lower() or q in i.description.lower() or any(q in t.lower() for t in i.tags)
                ]

            columns_map = {
                "backlog": filtered_backlog,
                "doing": filtered_doing,
                "done": filtered_done if sd else [],
            }

            if view_mode["current"] == "backlog":
                # --- Backlog management view ---
                _render_backlog_list(filtered_backlog, current_sprint, move_item, save_item, render_board.refresh)
            else:
                # --- Kanban board view ---
                with ui.element("div").style("display:flex;gap:10px;align-items:flex-start;"):
                    for col_status in STATUSES:
                        items_in_col = columns_map[col_status]
                        col_style, label_color = COLUMN_STYLES[col_status]

                        with ui.element("div").style(f"flex:1;min-width:0;{col_style}"):
                            with ui.element("div").style(
                                "display:flex;align-items:center;gap:6px;padding:4px 6px 8px;"
                            ):
                                ui.html(
                                    f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:10px;"
                                    f"font-weight:700;text-transform:uppercase;letter-spacing:0.12em;"
                                    f'color:{label_color};">{LABELS[col_status]}</span>'
                                )
                                ui.html(
                                    f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;"
                                    f"font-weight:500;color:#3f3f46;background:#1e1e23;padding:1px 6px;"
                                    f'border-radius:4px;">{len(items_in_col)}</span>'
                                )

                            if not items_in_col:
                                if col_status == "backlog":
                                    msg = (
                                        "No items match filters."
                                        if items
                                        else "No items yet \u2014 use `agile-backlog add` to create one."
                                    )
                                elif col_status == "done" and not sd:
                                    msg = "Done items hidden."
                                else:
                                    msg = "No items."
                                ui.html(
                                    f'<div style="font-size:11px;color:#52525b;padding:8px 6px;'
                                    f"font-style:italic;font-family:'DM Sans',sans-serif;\">{msg}</div>"
                                )
                                continue

                            for card_item in items_in_col:
                                _render_card(card_item, col_status, move_item, save_item, render_board.refresh)

        priority_select.on_value_change(lambda _: render_board.refresh())
        category_select.on_value_change(lambda _: render_board.refresh())
        sprint_select.on_value_change(lambda _: render_board.refresh())
        phase_select.on_value_change(lambda _: render_board.refresh())
        tag_select.on_value_change(lambda _: render_board.refresh())
        search_input.on_value_change(lambda _: render_board.refresh())
        done_check.on_value_change(lambda _: render_board.refresh())

        render_board()


def run_app(host: str = "127.0.0.1", port: int = 8501, reload: bool = True):
    """Start the NiceGUI Kanban board server."""
    ui.run(title="agile-backlog", host=host, port=port, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    run_app()
