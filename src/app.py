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
    emoji, cat_color, _ = category_style(item.category)
    pri_color = PRIORITY_COLORS.get(item.priority, "#888")
    sprint_text = f"S{item.sprint_target}" if item.sprint_target is not None else ""

    sprint_html = f' · <span style="color:#888;">{sprint_text}</span>' if sprint_text else ""

    return (
        f'<div style="margin-bottom:0;padding:4px 0 2px 0;">\n'
        f'  <div style="display:flex;align-items:baseline;gap:4px;flex-wrap:wrap;">\n'
        f'    <span style="font-size:13px;font-weight:500;word-wrap:break-word;overflow-wrap:break-word;">'
        f"{item.title}</span>\n"
        f'    <span style="font-size:10px;color:{cat_color};font-weight:600;text-transform:uppercase;">'
        f"{emoji} {item.category}</span>\n"
        f'    <span style="font-size:10px;color:{pri_color};font-weight:700;">{item.priority}</span>\n'
        f"{sprint_html}\n"
        f"  </div>\n"
        f"</div>"
    )


def detect_current_sprint(items: list[BacklogItem]) -> int | None:
    """Detect the current sprint from items in 'doing' status. Returns the most common sprint_target."""
    doing_sprints = [i.sprint_target for i in items if i.status == "doing" and i.sprint_target is not None]
    if not doing_sprints:
        return None
    from collections import Counter

    return Counter(doing_sprints).most_common(1)[0][0]


def main():
    """Render the Kanban board."""
    import streamlit as st

    from src.yaml_store import load_all, save_item

    st.set_page_config(page_title="agile-backlog", layout="wide")

    # --- Custom CSS ---
    st.markdown(
        """
    <style>
        /* Reduce top padding */
        .block-container { padding-top: 1rem; }
        /* Tighter spacing between elements */
        [data-testid="stVerticalBlock"] > div { gap: 0.3rem; }
        /* Compact buttons */
        .stButton > button { padding: 0.15rem 0.5rem; font-size: 0.8rem; }
        /* Column header styling */
        .col-header {
            font-size: 0.9rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.3rem 0;
            border-bottom: 2px solid #333;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .col-header .count {
            background: rgba(255,255,255,0.1);
            padding: 0.1rem 0.5rem;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 400;
        }
        /* Done column dimmed */
        .done-card { opacity: 0.6; }
        .done-card:hover { opacity: 1; }
        /* Hide default streamlit header spacing */
        h2 { margin-bottom: 0.2rem !important; }
        /* Compact expander */
        .streamlit-expanderHeader { font-size: 0.8rem; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # --- Load data ---
    all_items = load_all()

    # --- Header with sprint indicator ---
    current_sprint = detect_current_sprint(all_items)
    sprint_badge = ""
    if current_sprint is not None:
        sprint_badge = (
            f' <span style="font-size:0.6em;background:#2563eb;color:white;'
            f'padding:2px 10px;border-radius:12px;vertical-align:middle;">Sprint {current_sprint}</span>'
        )
    st.markdown(
        f'<div style="font-size:1.2rem;font-weight:700;margin:0 0 0.5rem 0;">📋 agile-backlog{sprint_badge}</div>',
        unsafe_allow_html=True,
    )

    filter_cols = st.columns(4)

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
            st.markdown(
                f'<div class="col-header">{label}<span class="count">{len(items_in_col)}</span></div>',
                unsafe_allow_html=True,
            )

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
                    card_html = render_card_html(item)
                    if status == "done":
                        card_html = f'<div class="done-card">{card_html}</div>'
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Detail expander
                    with st.expander("details"):
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

                    # Move buttons at bottom
                    other_statuses = [s for s in statuses if s != status]
                    btn_cols = st.columns(len(other_statuses))
                    for btn_col, target in zip(btn_cols, other_statuses):
                        with btn_col:
                            arrow = "←" if statuses.index(target) < statuses.index(status) else "→"
                            if st.button(f"{arrow} {target}", key=f"move_{item.id}_{target}", use_container_width=True):
                                item.status = target
                                save_item(item)
                                st.rerun()


if __name__ == "__main__":
    main()
