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

PRIORITY_ORDER: dict[str, int] = {"P1": 1, "P2": 2, "P3": 3}


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
        f'<div style="border-radius:6px;overflow:hidden;margin-bottom:0;">\n'
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


def main():
    """Render the Kanban board."""
    import streamlit as st

    from src.yaml_store import load_all, save_item

    st.set_page_config(page_title="agile-backlog", layout="wide")

    # --- Load data ---
    all_items = load_all()

    # --- Filter bar ---
    st.markdown("## agile-backlog")

    filter_cols = st.columns([1, 1, 1, 2])

    with filter_cols[0]:
        priority_options = [None, "P1", "P2+", "P3+"]
        priority_labels = {None: "All priorities", "P1": "P1 only", "P2+": "P1 & P2", "P3+": "All (P1-P3)"}
        priority_filter = st.selectbox(
            "Priority",
            priority_options,
            format_func=lambda x: priority_labels.get(x, str(x)),
        )
    with filter_cols[1]:
        categories = sorted({i.category for i in all_items})
        category_filter = st.selectbox(
            "Category", [None, *categories], format_func=lambda x: "All categories" if x is None else x
        )
    with filter_cols[2]:
        sprints = sorted({i.sprint_target for i in all_items if i.sprint_target is not None})
        sprint_filter = st.selectbox(
            "Sprint", [None, *sprints], format_func=lambda x: "All sprints" if x is None else f"Sprint {x}"
        )
    with filter_cols[3]:
        search = st.text_input("Search", placeholder="Filter by title, description, tags...")

    # --- Apply filters only to backlog ---
    backlog_items = [i for i in all_items if i.status == "backlog"]
    doing_items = [i for i in all_items if i.status == "doing"]
    done_items = [i for i in all_items if i.status == "done"]

    filtered_backlog = filter_items(
        backlog_items, priority=priority_filter, category=category_filter, sprint=sprint_filter, search=search
    )

    columns_map = {
        "backlog": filtered_backlog,
        "doing": doing_items,
        "done": done_items,
    }

    # --- Render columns ---
    col_backlog, col_doing, col_done = st.columns(3)

    statuses = ["backlog", "doing", "done"]
    column_widgets = [col_backlog, col_doing, col_done]
    labels = ["BACKLOG", "DOING", "DONE"]

    for col_widget, status, label in zip(column_widgets, statuses, labels):
        items_in_col = columns_map[status]
        with col_widget:
            st.markdown(f"### {label} ({len(items_in_col)})")
            st.divider()

            if not items_in_col:
                if status == "backlog":
                    no_items_msg = "No items yet — use `agile-backlog add` to create one."
                    st.caption("No items match filters." if all_items else no_items_msg)
                else:
                    st.caption("No items.")
                continue

            for item in items_in_col:
                with st.container(border=True):
                    # Render styled card
                    st.markdown(render_card_html(item), unsafe_allow_html=True)

                    # Move buttons
                    other_statuses = [s for s in statuses if s != status]
                    btn_cols = st.columns(len(other_statuses))
                    for btn_col, target in zip(btn_cols, other_statuses):
                        with btn_col:
                            if st.button(f"→ {target}", key=f"move_{item.id}_{target}", use_container_width=True):
                                item.status = target
                                save_item(item)
                                st.rerun()

                    # Detail expander
                    with st.expander(f"Details: {item.title}"):
                        if item.description:
                            st.markdown(item.description)
                        if item.acceptance_criteria:
                            st.markdown("**Acceptance Criteria:**")
                            for ac in item.acceptance_criteria:
                                st.markdown(f"- {ac}")
                        if item.notes:
                            st.markdown(f"**Notes:** {item.notes}")
                        if item.tags:
                            st.markdown(f"**Tags:** {', '.join(item.tags)}")
                        if item.depends_on:
                            st.markdown(f"**Depends on:** {', '.join(item.depends_on)}")
                        detail_cols = st.columns(3)
                        with detail_cols[0]:
                            st.caption(f"Sprint: {item.sprint_target or 'Unplanned'}")
                        with detail_cols[1]:
                            st.caption(f"Created: {item.created}")
                        with detail_cols[2]:
                            st.caption(f"Updated: {item.updated}")


if __name__ == "__main__":
    main()
