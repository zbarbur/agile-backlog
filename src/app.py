# src/app.py
"""Streamlit Kanban board for agile-backlog."""

from src.models import BacklogItem

CATEGORY_STYLES: dict[str, tuple[str, str]] = {
    # category: (text_color, bg_color)
    "bug": ("#be185d", "#fce7f3"),
    "feature": ("#1d4ed8", "#dbeafe"),
    "tech-debt": ("#92400e", "#fef3c7"),
    "docs": ("#065f46", "#d1fae5"),
    "security": ("#5b21b6", "#ede9fe"),
    "infra": ("#155e75", "#cffafe"),
}

PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "P1": ("#dc2626", "#fef2f2"),
    "P2": ("#2563eb", "#eff6ff"),
    "P3": ("#d97706", "#fffbeb"),
}

PRIORITY_ORDER: dict[str, int] = {"P1": 1, "P2": 2, "P3": 3}


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
    """Generate the HTML string for a styled card (two-row design)."""
    cat_color, cat_bg = category_style(item.category)
    pri_color, pri_bg = PRIORITY_COLORS.get(item.priority, ("#888", "#f3f4f6"))

    # P1 left border accent
    p1_border = "border-left:3px solid #ef4444;" if item.priority == "P1" else ""

    # Category pill — uppercase, no emoji
    category_html = (
        f'<span style="display:inline-flex;align-items:center;height:20px;'
        f"font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.02em;"
        f"color:{cat_color};background:{cat_bg};"
        f'padding:2px 8px;border-radius:4px;white-space:nowrap;">'
        f"{item.category}</span>"
    )

    # Priority pill
    priority_html = (
        f'<span style="display:inline-flex;align-items:center;height:20px;'
        f"font-size:11px;font-weight:600;text-transform:uppercase;"
        f"color:{pri_color};background:{pri_bg};"
        f'padding:2px 8px;border-radius:4px;white-space:nowrap;">'
        f"{item.priority}</span>"
    )

    # Phase pill — lowercase italic, gray
    phase_html = ""
    if item.phase:
        phase_html = (
            f'<span style="display:inline-flex;align-items:center;height:20px;'
            f"font-size:11px;font-weight:600;font-style:italic;text-transform:none;"
            f"color:#6b7280;background:#f3f4f6;"
            f'padding:2px 8px;border-radius:4px;white-space:nowrap;">'
            f"{item.phase}</span>"
        )

    # Sprint pill — outlined style
    sprint_html = ""
    if item.sprint_target is not None:
        sprint_html = (
            f'<span style="display:inline-flex;align-items:center;height:20px;'
            f"font-size:11px;font-weight:500;"
            f"color:#6b7280;background:transparent;border:1px solid #e5e7eb;"
            f'padding:2px 8px;border-radius:4px;white-space:nowrap;">'
            f"S{item.sprint_target}</span>"
        )

    return (
        f'<div style="margin:0;padding:2px 0;{p1_border}">\n'
        f'  <div style="font-size:14px;font-weight:600;color:#111827;line-height:1.35;'
        f'margin-bottom:6px;">{item.title}</div>\n'
        f'  <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">\n'
        f"    {category_html}\n"
        f"    {priority_html}\n"
        f"    {phase_html}\n"
        f"    {sprint_html}\n"
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


def main():
    """Render the Kanban board."""
    import streamlit as st

    from src.yaml_store import load_all, save_item

    st.set_page_config(page_title="agile-backlog", layout="wide")

    # --- Custom CSS using design system tokens ---
    st.markdown(
        """
    <style>
        :root {
            --color-border: #e5e7eb;
            --color-border-hover: #d1d5db;
            --color-shadow-default: rgba(0, 0, 0, 0.04);
            --color-shadow-hover: rgba(0, 0, 0, 0.08);
            --color-text-primary: #111827;
            --color-text-secondary: #6b7280;
            --color-text-muted: #9ca3af;
        }

        /* Tighter vertical spacing */
        [data-testid="stVerticalBlock"] > div { gap: 0.25rem; }

        /* Compact move buttons — ghost-style */
        .stButton > button {
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 500;
            border: 1px solid var(--color-border);
            background: transparent;
            color: var(--color-text-secondary);
            border-radius: 6px;
            transition: all 0.15s ease;
        }
        .stButton > button:hover {
            background: #f3f4f6;
            color: var(--color-text-primary);
            border-color: var(--color-border-hover);
        }

        /* Column header — clean, professional */
        .col-header {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--color-text-secondary);
            padding: 8px 12px 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .col-header .count {
            background: #e5e7eb;
            color: #4b5563;
            padding: 1px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
        }

        /* Card containers — 8px radius, design system shadow */
        [data-testid="stVerticalBlock"] [data-testid="stContainer"] {
            border: 1px solid var(--color-border) !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px var(--color-shadow-default) !important;
            padding: 10px 14px !important;
            transition: box-shadow 0.15s ease;
        }
        [data-testid="stVerticalBlock"] [data-testid="stContainer"]:hover {
            box-shadow: 0 2px 8px var(--color-shadow-hover) !important;
        }

        /* Done column dimmed with strikethrough */
        .done-card { opacity: 0.5; }
        .done-card:hover { opacity: 1; transition: opacity 0.15s ease; }
        .done-card .card-title {
            text-decoration: line-through;
            color: #9ca3af !important;
        }

        /* Compact expander — subtle trigger text */
        .streamlit-expanderHeader {
            font-size: 12px;
            color: var(--color-text-muted);
            font-weight: 400;
        }

        /* Hide default heading spacing */
        h2 { margin-bottom: 0.1rem !important; }

        /* Filter bar — subtle bottom border */
        .filter-bar {
            border-bottom: 1px solid var(--color-border);
            padding-bottom: 12px;
            margin-bottom: 10px;
        }

        /* Column background tints */
        .col-bg-backlog { background: #f9fafb; border-radius: 8px; padding: 0.4rem; }
        .col-bg-doing { background: #fffbeb; border-radius: 8px; padding: 0.4rem; }
        .col-bg-done { background: #f0fdf4; border-radius: 8px; padding: 0.4rem; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # --- Load data ---
    all_items = load_all()

    # --- Header ---
    current_sprint = detect_current_sprint(all_items)
    sprint_text = f" · Sprint {current_sprint}" if current_sprint is not None else ""
    st.markdown(
        f'<h2 style="font-weight:700;color:#111827;margin:0.2rem 0 0.1rem;">📋 agile-backlog'
        f'<span style="font-weight:400;color:#9ca3af;font-size:0.6em;">{sprint_text}</span></h2>',
        unsafe_allow_html=True,
    )

    # --- Filters ---
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        priority_options = [None, "P1", "P2+", "P3+"]
        priority_labels = {None: "All priorities", "P1": "P1 only", "P2+": "P1 & P2", "P3+": "All (P1-P3)"}
        priority_filter = st.selectbox(
            "Priority", priority_options, format_func=lambda x: priority_labels.get(x, str(x))
        )
    with f2:
        categories = sorted({i.category for i in all_items})
        category_filter = st.selectbox(
            "Category", [None, *categories], format_func=lambda x: "All categories" if x is None else x
        )
    with f3:
        sprints = sorted({i.sprint_target for i in all_items if i.sprint_target is not None})
        sprint_filter = st.selectbox(
            "Sprint", [None, *sprints], format_func=lambda x: "All sprints" if x is None else f"Sprint {x}"
        )
    with f4:
        search = st.text_input("Search", placeholder="Filter by title, description, tags...")
    st.markdown("</div>", unsafe_allow_html=True)

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
    labels = ["BACKLOG", "IN PROGRESS", "DONE"]
    col_bg_classes = ["col-bg-backlog", "col-bg-doing", "col-bg-done"]

    for col_widget, status, label, bg_class in zip(column_widgets, statuses, labels, col_bg_classes):
        items_in_col = columns_map[status]
        with col_widget:
            st.markdown(
                f'<div class="{bg_class}">'
                f'<div class="col-header">{label}<span class="count">{len(items_in_col)}</span></div>'
                f"</div>",
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

                    # Detail expander — contextual label
                    expander_label = f"{item.id}"
                    with st.expander(expander_label):
                        # Goal prominently at top
                        if item.goal:
                            st.markdown(f"**Goal:** {item.goal}")

                        # Complexity badge
                        if item.complexity:
                            st.markdown(f"**Complexity:** {_complexity_badge(item.complexity)}", unsafe_allow_html=True)

                        # Description
                        if item.description:
                            st.markdown(item.description)

                        # Acceptance Criteria as bullet list
                        if item.acceptance_criteria:
                            st.markdown("**Acceptance Criteria:**")
                            for ac in item.acceptance_criteria:
                                st.markdown(f"- {ac}")

                        # Technical Specs as bullet list
                        if item.technical_specs:
                            st.markdown("**Technical Specs:**")
                            for ts in item.technical_specs:
                                st.markdown(f"- {ts}")

                        # Notes
                        if item.notes:
                            st.markdown(f"**Notes:** {item.notes}")

                        # Tags as small gray pills
                        if item.tags:
                            tag_html = " ".join(
                                f'<span style="display:inline-flex;align-items:center;height:18px;'
                                f"background:#f3f4f6;color:#4b5563;padding:1px 8px;"
                                f'border-radius:4px;font-size:11px;margin-right:2px;">{t}</span>'
                                for t in item.tags
                            )
                            st.markdown(f"**Tags:** {tag_html}", unsafe_allow_html=True)

                        # Depends on
                        if item.depends_on:
                            st.markdown(f"**Depends on:** {', '.join(item.depends_on)}")

                        # Footer row: Sprint / Created / Updated
                        detail_cols = st.columns(3)
                        with detail_cols[0]:
                            st.caption(f"Sprint: {item.sprint_target or 'Unplanned'}")
                        with detail_cols[1]:
                            st.caption(f"Created: {item.created}")
                        with detail_cols[2]:
                            st.caption(f"Updated: {item.updated}")

                    # Move buttons — compact row
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
