# src/app.py
"""NiceGUI Kanban board for agile-backlog."""

from nicegui import ui

from src.models import BacklogItem
from src.tokens import CATEGORY_STYLES, COLUMN_BG, PRIORITY_COLORS, PRIORITY_ORDER

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
        badges.append(f'<span style="{pill};font-style:italic;color:#6b7280;background:#f3f4f6">{item.phase}</span>')
    review_badge = "font-size:10px;color:#059669;background:#d1fae5;padding:1px 6px;border-radius:3px"
    if item.design_reviewed:
        badges.append(f'<span style="{review_badge}">&#10003; design</span>')
    if item.code_reviewed:
        badges.append(f'<span style="{review_badge}">&#10003; code</span>')
    if item.sprint_target is not None:
        badges.append(
            f'<span style="{pill};font-weight:500;color:#6b7280;background:none;'
            f'border:1px solid #e5e7eb">S{item.sprint_target}</span>'
        )

    badge_row = " ".join(badges)

    return (
        f'<div style="margin:0;padding:2px 0;{p1_style}">'
        f'<div style="font-size:14px;font-weight:600;color:#111827;line-height:1.35;'
        f'margin-bottom:6px">{item.title}</div>'
        f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">'
        f"{badge_row}</div></div>"
    )


def detect_current_sprint(items: list[BacklogItem]) -> int | None:
    """Detect the current sprint from items in 'doing' status. Returns the most common sprint_target."""
    doing_sprints = [i.sprint_target for i in items if i.status == "doing" and i.sprint_target is not None]
    if not doing_sprints:
        return None
    from collections import Counter

    return Counter(doing_sprints).most_common(1)[0][0]


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
# NiceGUI UI
# ---------------------------------------------------------------------------

STATUSES = ["backlog", "doing", "done"]
LABELS = {"backlog": "BACKLOG", "doing": "IN PROGRESS", "done": "DONE"}


@ui.page("/")
def kanban_page():
    """Render the Kanban board."""
    from src.yaml_store import load_all, save_item

    # --- Custom CSS ---
    ui.add_head_html("""
    <style>
        .done-card { opacity: 0.5; transition: opacity 0.15s ease; }
        .done-card:hover { opacity: 1; }
        .done-card .card-title {
            text-decoration: line-through;
            color: #9ca3af !important;
        }
    </style>
    """)

    # --- Header ---
    all_items = load_all()
    current_sprint = detect_current_sprint(all_items)
    sprint_text = f" \u00b7 Sprint {current_sprint}" if current_sprint is not None else ""
    ui.html(
        f'<h2 style="font-weight:700;color:#111827;margin:0.2rem 0 0.1rem;">'
        f"\U0001f4cb agile-backlog"
        f'<span style="font-weight:400;color:#9ca3af;font-size:0.6em;">{sprint_text}</span></h2>'
    )

    # --- Filter widgets ---
    priority_options = {None: "All priorities", "P1": "P1 only", "P2+": "P1 & P2", "P3+": "All (P1-P3)"}
    categories = sorted({i.category for i in all_items})
    category_options = {None: "All categories", **{c: c for c in categories}}
    sprints = sorted({i.sprint_target for i in all_items if i.sprint_target is not None})
    sprint_options = {None: "All sprints", "unplanned": "Unplanned", **{s: f"Sprint {s}" for s in sprints}}

    with ui.row().classes("w-full gap-4 pb-3 border-b items-end"):
        priority_select = ui.select(
            label="Priority",
            options=priority_options,
            value=None,
        ).classes("w-48")
        category_select = ui.select(
            label="Category",
            options=category_options,
            value=None,
        ).classes("w-48")
        sprint_select = ui.select(
            label="Sprint",
            options=sprint_options,
            value=None,
        ).classes("w-48")
        search_input = ui.input(label="Search", placeholder="Filter by title, description, tags...").classes("w-64")

    # --- Board ---
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
        items = load_all()

        # Read filter values from widgets
        pf = priority_select.value
        cf = category_select.value
        sf = sprint_select.value
        sq = search_input.value or ""

        backlog_items = [i for i in items if i.status == "backlog"]
        doing_items = [i for i in items if i.status == "doing"]
        done_items = [i for i in items if i.status == "done"]

        filtered_backlog = filter_items(backlog_items, priority=pf, category=cf, sprint=sf, search=sq)

        if sf == "unplanned":
            doing_items = [i for i in doing_items if i.sprint_target is None]
            done_items = [i for i in done_items if i.sprint_target is None]
        elif sf is not None:
            doing_items = [i for i in doing_items if i.sprint_target == sf]
            done_items = [i for i in done_items if i.sprint_target == sf]

        columns_map = {
            "backlog": filtered_backlog,
            "doing": doing_items,
            "done": done_items,
        }

        with ui.row().classes("w-full gap-4"):
            for status in STATUSES:
                items_in_col = columns_map[status]
                bg = COLUMN_BG[status]

                with ui.column().classes("flex-1 min-w-0").style(f"background:{bg};border-radius:8px;padding:0.5rem;"):
                    # Column header
                    with ui.row().classes("items-center gap-2 px-3 pt-2 pb-1"):
                        ui.label(LABELS[status]).classes("text-xs font-bold uppercase tracking-wider text-gray-500")
                        ui.badge(str(len(items_in_col))).props("rounded").classes("text-xs bg-gray-200 text-gray-600")

                    # Empty state
                    if not items_in_col:
                        if status == "backlog":
                            msg = (
                                "No items match filters."
                                if items
                                else "No items yet \u2014 use `agile-backlog add` to create one."
                            )
                            ui.label(msg).classes("text-xs text-gray-400 px-3 py-2")
                        else:
                            ui.label("No items.").classes("text-xs text-gray-400 px-3 py-2")
                        continue

                    # Cards
                    for item in items_in_col:
                        done_class = "done-card" if status == "done" else ""
                        with ui.card().classes(f"w-full {done_class}").style("padding:10px 14px;"):
                            ui.html(render_card_html(item))

                            # Detail expander
                            with ui.expansion(item.id).classes("w-full text-xs text-gray-400"):
                                if item.goal:
                                    ui.html(f"<b>Goal:</b> {item.goal}")
                                if item.complexity:
                                    ui.html(f"<b>Complexity:</b> {_complexity_badge(item.complexity)}")
                                if item.description:
                                    ui.markdown(item.description)
                                if item.acceptance_criteria:
                                    ui.html("<b>Acceptance Criteria:</b>")
                                    for ac in item.acceptance_criteria:
                                        ui.markdown(f"- {ac}")
                                if item.technical_specs:
                                    ui.html("<b>Technical Specs:</b>")
                                    for ts in item.technical_specs:
                                        ui.markdown(f"- {ts}")
                                if item.test_plan:
                                    ui.html("<b>Test Plan:</b>")
                                    for tp in item.test_plan:
                                        ui.markdown(f"- {tp}")
                                if item.notes:
                                    ui.html(f"<b>Notes:</b> {item.notes}")
                                if item.tags:
                                    tag_html = " ".join(
                                        f'<span style="display:inline-flex;align-items:center;height:18px;'
                                        f"background:#f3f4f6;color:#4b5563;padding:1px 8px;"
                                        f'border-radius:4px;font-size:11px;margin-right:2px;">{t}</span>'
                                        for t in item.tags
                                    )
                                    ui.html(f"<b>Tags:</b> {tag_html}")
                                if item.depends_on:
                                    ui.html(f"<b>Depends on:</b> {', '.join(item.depends_on)}")
                                # Footer row
                                with ui.row().classes("w-full gap-4 mt-2"):
                                    ui.label(f"Sprint: {item.sprint_target or 'Unplanned'}").classes(
                                        "text-xs text-gray-400"
                                    )
                                    ui.label(f"Created: {item.created}").classes("text-xs text-gray-400")
                                    ui.label(f"Updated: {item.updated}").classes("text-xs text-gray-400")

                            # Move buttons
                            other_statuses = [s for s in STATUSES if s != status]
                            with ui.row().classes("gap-2 mt-1"):
                                for target in other_statuses:
                                    arrow = "\u2190" if STATUSES.index(target) < STATUSES.index(status) else "\u2192"
                                    ui.button(
                                        f"{arrow} {target}",
                                        on_click=lambda _e, i=item, t=target: move_item(i, t),
                                    ).props("flat dense size=sm").classes(
                                        "text-xs text-gray-500 border border-gray-200"
                                    )

    # Wire filter changes to board refresh
    priority_select.on_value_change(lambda _: render_board.refresh())
    category_select.on_value_change(lambda _: render_board.refresh())
    sprint_select.on_value_change(lambda _: render_board.refresh())
    search_input.on_value_change(lambda _: render_board.refresh())

    render_board()


def run_app(host: str = "127.0.0.1", port: int = 8501):
    """Start the NiceGUI Kanban board server."""
    ui.run(title="agile-backlog", host=host, port=port, reload=False)


if __name__ in {"__main__", "__mp_main__"}:
    run_app()
