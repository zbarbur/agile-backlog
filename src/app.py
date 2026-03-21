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
        priority_filter = st.selectbox(
            "Priority", [None, "P1", "P2", "P3"], format_func=lambda x: "All priorities" if x is None else x
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

    filtered = filter_items(
        all_items, priority=priority_filter, category=category_filter, sprint=sprint_filter, search=search
    )

    # --- Group by status ---
    columns_map = {"backlog": [], "doing": [], "done": []}
    for item in filtered:
        columns_map[item.status].append(item)

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
                no_items_msg = "No items yet — use `agile-backlog add` to create one."
                st.caption("No items match filters." if all_items else no_items_msg)
                continue

            for item in items_in_col:
                # Render styled card
                st.markdown(render_card_html(item), unsafe_allow_html=True)

                # Move selectbox
                other_statuses = [s for s in statuses if s != status]
                move_key = f"move_{item.id}"
                new_status = st.selectbox(
                    "Move to",
                    [status, *other_statuses],
                    key=move_key,
                    label_visibility="collapsed",
                    format_func=lambda s, current=status: f"Move to → {s}" if s != current else f"📍 {current}",
                )
                if new_status != status:
                    item.status = new_status
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
