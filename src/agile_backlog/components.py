"""NiceGUI UI components for agile-backlog."""

from datetime import date

from nicegui import ui

from agile_backlog.models import BacklogItem
from agile_backlog.pure import (
    _complexity_badge,
    category_style,
    comment_badge_html,
    comment_thread_html,
    detect_current_sprint,
    filter_items,
    group_items_by_section,
    render_card_html,
)
from agile_backlog.styles import STATUSES
from agile_backlog.tokens import PRIORITY_COLORS


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
        if item.comments:
            ui.html('<div style="font-size:11px;font-weight:600;color:#71717a;margin-bottom:6px;">COMMENTS</div>')
            for idx, note in enumerate(item.comments):
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
                            item.comments[note_idx]["resolved"] = True
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
            item.comments.append(
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
                comment_count = len(item.comments)
                has_flagged = any(n.get("flagged") and not n.get("resolved") for n in item.comments)
                icon_color = "#f87171" if has_flagged else "#52525b" if comment_count == 0 else "#60a5fa"
                badge_html = (
                    f'<span style="position:relative;cursor:pointer;color:{icon_color};'
                    f'font-size:14px;padding:2px 4px;">\U0001f4ac' + comment_badge_html(item.comments) + "</span>"
                )
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

    # Comments
    if item.comments:
        ui.html(f'<div style="{label_style}">Comments</div>')
        for note in item.comments:
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


def _render_side_panel_content(
    item: BacklogItem,
    save_fn,
    refresh_fn,
    close_fn,
) -> None:
    """Render the side panel content for a backlog item detail view."""
    label_style = (
        "font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;"
        "color:#52525b;text-transform:uppercase;letter-spacing:0.08em;"
        "margin-top:10px;margin-bottom:3px;"
    )
    value_style = "color:#d4d4d8;font-size:12px;font-family:'DM Sans',sans-serif;"
    cat_color, cat_bg = category_style(item.category)
    pri_color, pri_bg = PRIORITY_COLORS.get(item.priority, ("#888", "#f3f4f6"))

    # Header: Close button (left) + Edit button (right)
    with ui.element("div").style("display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;"):
        ui.button(
            "\u2715",
            on_click=close_fn,
        ).props("flat dense no-caps").style("color:#71717a;font-size:14px;min-width:28px;padding:2px;")
        if save_fn and refresh_fn:
            ui.button(
                "Edit",
                on_click=lambda i=item: (
                    close_fn(),
                    _show_edit_dialog(i, save_fn, refresh_fn),
                ),
            ).props("flat dense no-caps").style("color:#3b82f6;font-size:11px;")

    # Title
    ui.html(
        f'<div style="font-size:16px;font-weight:700;color:#e4e4e7;line-height:1.3;'
        f"font-family:'DM Sans',sans-serif;\">{item.title}</div>"
    )

    # Metadata grid
    pill_base = (
        "font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;"
        "padding:1px 5px;border-radius:3px;letter-spacing:0.03em;white-space:nowrap;"
    )

    meta_items = []
    meta_items.append(("Status", f'<span style="{pill_base}color:#a1a1aa;background:#1e1e23;">{item.status}</span>'))
    if item.phase:
        meta_items.append(
            (
                "Phase",
                f'<span style="{pill_base}font-style:italic;text-transform:none;color:#71717a;'
                f'background:#1e1e23;">{item.phase}</span>',
            )
        )
    meta_items.append(
        (
            "Priority",
            f'<span style="{pill_base}text-transform:uppercase;color:{pri_color};background:{pri_bg}">'
            f"{item.priority}</span>",
        )
    )
    if item.complexity:
        meta_items.append(("Complexity", _complexity_badge(item.complexity)))
    meta_items.append(
        (
            "Category",
            f'<span style="{pill_base}text-transform:uppercase;color:{cat_color};background:{cat_bg}">'
            f"{item.category}</span>",
        )
    )
    meta_items.append(
        (
            "Sprint",
            f'<span style="{pill_base}font-weight:500;color:#52525b;background:transparent;'
            f'border:1px solid #27272a;">'
            f"{'S' + str(item.sprint_target) if item.sprint_target is not None else 'Unplanned'}"
            f"</span>",
        )
    )
    if item.tags:
        tag_html = " ".join(
            f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;"
            f"background:#1e1e23;color:#a1a1aa;padding:1px 6px;"
            f'border-radius:3px;">{t}</span>'
            for t in item.tags
        )
        meta_items.append(("Tags", tag_html))

    meta_html = '<div style="display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin-top:10px;">'
    for label, value in meta_items:
        meta_html += (
            f'<div style="{label_style}margin-top:0;">{label}</div>'
            f'<div style="display:flex;align-items:center;gap:4px;">{value}</div>'
        )
    meta_html += "</div>"
    ui.html(meta_html)

    # Description
    if item.description:
        ui.html(f'<div style="{label_style}">Description</div>')
        ui.markdown(item.description).style(value_style)

    # Acceptance Criteria
    if item.acceptance_criteria:
        ui.html(f'<div style="{label_style}">Acceptance Criteria</div>')
        li_items = "".join(
            f'<li style="margin-bottom:1px;color:#a1a1aa;font-size:11px;">{ac}</li>' for ac in item.acceptance_criteria
        )
        ui.html(f'<ul style="padding-left:14px;">{li_items}</ul>')

    # Technical Specs
    if item.technical_specs:
        ui.html(f'<div style="{label_style}">Technical Specs</div>')
        li_items = "".join(
            f'<li style="margin-bottom:1px;color:#a1a1aa;font-size:11px;">{ts}</li>' for ts in item.technical_specs
        )
        ui.html(f'<ul style="padding-left:14px;">{li_items}</ul>')

    # Comments thread
    ui.html(f'<div style="{label_style}">Comments</div>')
    if item.comments:
        ui.html(comment_thread_html(item.comments))

        # Resolve buttons for flagged, unresolved comments
        for idx, comment in enumerate(item.comments):
            if comment.get("flagged") and not comment.get("resolved"):
                preview = comment.get("text", "")[:40]

                def _resolve_comment(comment_idx=idx):
                    item.comments[comment_idx]["resolved"] = True
                    save_fn(item)
                    refresh_fn()

                with ui.element("div").style("display:flex;align-items:center;gap:6px;margin:2px 0 2px 12px;"):
                    ui.html(
                        f'<span style="font-size:10px;color:#71717a;font-style:italic;">Resolve: "{preview}..."</span>'
                    )
                    ui.button(
                        "\u2713 Resolve",
                        on_click=_resolve_comment,
                    ).props("flat dense no-caps").style("color:#4ade80;font-size:10px;min-width:0;padding:1px 6px;")
    else:
        ui.html('<div style="font-size:11px;color:#52525b;font-style:italic;">No comments yet.</div>')

    # Comment input
    ui.html(
        '<div style="border-top:1px solid #27272a;margin-top:12px;padding-top:10px;">'
        f'<div style="{label_style}">Add Comment</div></div>'
    )
    comment_text = (
        ui.textarea()
        .props("outlined dense rows=3 placeholder='Write a comment...'")
        .style("width:100%;font-size:12px;")
    )
    with ui.element("div").style("display:flex;align-items:center;gap:8px;margin-top:6px;"):
        flag_check = ui.checkbox("Flag for AI").style("font-size:11px;color:#a1a1aa;")
        ui.element("div").style("flex:1;")

        def _send_comment():
            text = (comment_text.value or "").strip()
            if not text:
                return
            item.comments.append(
                {
                    "text": text,
                    "flagged": flag_check.value,
                    "resolved": False,
                    "created": str(date.today()),
                    "author": "user",
                }
            )
            save_fn(item)
            refresh_fn()

        ui.button("Send", on_click=_send_comment).props("flat dense no-caps").style(
            "color:#3b82f6;font-size:11px;font-weight:600;"
        )

    # Footer
    ui.html(
        '<div style="display:flex;gap:12px;margin-top:12px;padding-top:8px;border-top:1px solid #1e1e23;">'
        "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;color:#3f3f46;\">"
        f"Created: {item.created}</span>"
        "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;color:#3f3f46;\">"
        f"Updated: {item.updated}</span>"
        "</div>"
    )


def _render_backlog_list(
    all_items: list[BacklogItem],
    current_sprint: int | None,
    move_fn,
    save_fn,
    refresh_fn,
    *,
    priorities: list[str] | None = None,
    categories: list[str] | None = None,
    tags: list[str] | None = None,
    search: str = "",
) -> None:
    """Render the backlog planning view with three resizable sections and a side panel."""
    # Group all items into sections
    sections = group_items_by_section(all_items, current_sprint)
    backlog_items = sections["backlog"]
    vnext_items = sections["vnext"]
    vfuture_items = sections["vfuture"]

    # Apply filters to backlog section ONLY
    filtered_backlog = backlog_items
    if priorities:
        filtered_backlog = [i for i in filtered_backlog if i.priority in priorities]
    if categories:
        filtered_backlog = [i for i in filtered_backlog if i.category in categories]
    if tags:
        tag_set = set(tags)
        filtered_backlog = [i for i in filtered_backlog if tag_set & set(i.tags)]
    if search:
        filtered_backlog = filter_items(filtered_backlog, search=search)

    # Side panel state
    panel_state = {"selected_id": None}
    list_container_ref: dict[str, object] = {"el": None}
    panel_container_ref: dict[str, object] = {"el": None}

    def _open_side_panel(item: BacklogItem):
        panel_state["selected_id"] = item.id
        if list_container_ref["el"]:
            list_container_ref["el"].style("flex:6;min-width:0;")
        if panel_container_ref["el"]:
            panel_container_ref["el"].style("flex:4;min-width:320px;display:block;")
            panel_container_ref["el"].clear()
            with panel_container_ref["el"]:
                _render_side_panel_content(item, save_fn, refresh_fn, _close_side_panel)

    def _close_side_panel():
        panel_state["selected_id"] = None
        if list_container_ref["el"]:
            list_container_ref["el"].style("flex:1;min-width:0;")
        if panel_container_ref["el"]:
            panel_container_ref["el"].style("display:none;")
            panel_container_ref["el"].clear()

    ui.keyboard(on_key=lambda e: _close_side_panel() if e.key == "Escape" and not e.action.repeat else None)

    def _move_to_section(item: BacklogItem, target_sprint: int | None):
        item.sprint_target = target_sprint
        save_fn(item)
        refresh_fn()

    move_btn_style = (
        "font-size:9px;padding:1px 6px;min-height:0;border-radius:3px;"
        "font-family:'IBM Plex Mono',monospace;letter-spacing:0.03em;"
    )

    # Zoom state: which section is zoomed (None = normal proportions)
    zoom_state: dict[str, str | None] = {"zoomed": None}
    # References to section containers for zoom toggling
    section_refs: dict[str, dict[str, object]] = {
        "backlog": {"outer": None, "content": None},
        "vnext": {"outer": None, "content": None},
        "vfuture": {"outer": None, "content": None},
    }

    def _toggle_zoom(section_key: str):
        """Toggle zoom for a section: expand it, collapse others to header-only."""
        if zoom_state["zoomed"] == section_key:
            # Un-zoom: restore all sections
            zoom_state["zoomed"] = None
            for key in section_refs:
                outer = section_refs[key]["outer"]
                content = section_refs[key]["content"]
                if outer:
                    outer.style("flex:1;min-height:44px;overflow:hidden;")
                if content:
                    content.style("flex:1;overflow-y:auto;display:block;")
        else:
            # Zoom this section, collapse others
            zoom_state["zoomed"] = section_key
            for key in section_refs:
                outer = section_refs[key]["outer"]
                content = section_refs[key]["content"]
                if key == section_key:
                    if outer:
                        outer.style("flex:1;min-height:44px;overflow:hidden;")
                    if content:
                        content.style("flex:1;overflow-y:auto;display:block;")
                else:
                    if outer:
                        outer.style("flex:0 0 44px;min-height:44px;overflow:hidden;")
                    if content:
                        content.style("display:none;")

    def _render_section_items(items: list[BacklogItem], section: str):
        if not items:
            ui.html(
                '<div style="font-size:11px;color:#52525b;padding:8px 12px;'
                "font-style:italic;font-family:'DM Sans',sans-serif;\">No items.</div>"
            )
            return

        next_sprint = (current_sprint or 0) + 1
        future_sprint = (current_sprint or 0) + 2

        for card_item in items:
            # Card row with hover-revealed move buttons
            with ui.element("div").classes("mc-card-row").style("position:relative;margin:2px 0;padding:0 4px;"):
                # Card (clickable)
                card_container = ui.element("div").style("cursor:pointer;")
                card_container.on("click", lambda _e, i=card_item: _open_side_panel(i))
                with card_container:
                    ui.html(render_card_html(card_item))

                # Hover-revealed move buttons
                with ui.element("div").classes("mc-move-buttons"):
                    if section == "backlog":
                        ui.button(
                            "\u2192 vNext",
                            on_click=lambda _e, i=card_item, s=next_sprint: _move_to_section(i, s),
                        ).props("flat dense no-caps unelevated").style(
                            f"{move_btn_style}color:#ca8a04;background:rgba(202,138,4,0.1);"
                        )
                        ui.button(
                            "\u2192 vFuture",
                            on_click=lambda _e, i=card_item, s=future_sprint: _move_to_section(i, s),
                        ).props("flat dense no-caps unelevated").style(
                            f"{move_btn_style}color:#22c55e;background:rgba(34,197,94,0.1);"
                        )
                    elif section == "vnext":
                        ui.button(
                            "\u2190 Backlog",
                            on_click=lambda _e, i=card_item: _move_to_section(i, None),
                        ).props("flat dense no-caps unelevated").style(
                            f"{move_btn_style}color:#71717a;background:rgba(113,113,122,0.1);"
                        )
                        ui.button(
                            "\u2192 vFuture",
                            on_click=lambda _e, i=card_item, s=future_sprint: _move_to_section(i, s),
                        ).props("flat dense no-caps unelevated").style(
                            f"{move_btn_style}color:#22c55e;background:rgba(34,197,94,0.1);"
                        )
                    elif section == "vfuture":
                        ui.button(
                            "\u2190 Backlog",
                            on_click=lambda _e, i=card_item: _move_to_section(i, None),
                        ).props("flat dense no-caps unelevated").style(
                            f"{move_btn_style}color:#71717a;background:rgba(113,113,122,0.1);"
                        )
                        ui.button(
                            "\u2190 vNext",
                            on_click=lambda _e, i=card_item, s=next_sprint: _move_to_section(i, s),
                        ).props("flat dense no-caps unelevated").style(
                            f"{move_btn_style}color:#ca8a04;background:rgba(202,138,4,0.1);"
                        )

    def _section_header_el(label: str, count: int, color: str, section_key: str):
        """Render a section header with collapse arrow, label, count badge, and zoom button."""
        with ui.element("div").style(
            "display:flex;align-items:center;gap:8px;padding:8px 12px;flex-shrink:0;user-select:none;"
        ):
            # Colored label
            ui.html(
                f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:10px;"
                f"font-weight:700;text-transform:uppercase;letter-spacing:0.12em;"
                f'color:{color};">{label}</span>'
            )
            # Count badge
            ui.html(
                f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;"
                f"font-weight:500;color:#3f3f46;background:#1e1e23;padding:1px 6px;"
                f'border-radius:4px;">{count}</span>'
            )
            # Spacer
            ui.element("div").style("flex:1;")
            # Zoom button
            ui.button(
                "\u2922",
                on_click=lambda _e, sk=section_key: _toggle_zoom(sk),
            ).props("flat dense no-caps unelevated").style(
                "font-size:14px;min-width:28px;min-height:24px;padding:0 4px;color:#52525b;border-radius:4px;"
            ).tooltip("Zoom section")

    # Filter info for backlog section
    has_filters = bool(priorities or categories or tags or search)
    backlog_label = "BACKLOG"
    if has_filters:
        backlog_label += f" \u2014 filtered {len(filtered_backlog)}/{len(backlog_items)}"

    vnext_label = f"vNEXT \u2014 Sprint {(current_sprint or 0) + 1}"
    vfuture_label = f"vFUTURE \u2014 Sprint {(current_sprint or 0) + 2}+"

    # Two-column layout: list (left) + side panel (right)
    with ui.element("div").style("display:flex;gap:0;height:100%;"):
        # Left column: three vertically stacked sections
        list_container = ui.element("div").style(
            "flex:1;min-width:0;display:flex;flex-direction:column;overflow:hidden;height:100%;"
        )
        list_container_ref["el"] = list_container

        with list_container:
            # --- BACKLOG section ---
            backlog_outer = ui.element("div").style(
                "flex:1;min-height:44px;overflow:hidden;"
                "display:flex;flex-direction:column;background:#111116;border-radius:8px;margin-bottom:4px;"
            )
            section_refs["backlog"]["outer"] = backlog_outer
            with backlog_outer:
                _section_header_el(backlog_label, len(filtered_backlog), "#71717a", "backlog")
                backlog_content = ui.element("div").style("flex:1;overflow-y:auto;padding:0 4px 4px;")
                section_refs["backlog"]["content"] = backlog_content
                with backlog_content:
                    _render_section_items(filtered_backlog, "backlog")

            # --- vNEXT section ---
            vnext_outer = ui.element("div").style(
                "flex:1;min-height:44px;overflow:hidden;"
                "display:flex;flex-direction:column;background:#14130e;border:1px solid #2a2618;"
                "border-radius:8px;margin-bottom:4px;"
            )
            section_refs["vnext"]["outer"] = vnext_outer
            with vnext_outer:
                _section_header_el(vnext_label, len(vnext_items), "#ca8a04", "vnext")
                vnext_content = ui.element("div").style("flex:1;overflow-y:auto;padding:0 4px 4px;")
                section_refs["vnext"]["content"] = vnext_content
                with vnext_content:
                    _render_section_items(vnext_items, "vnext")

            # --- vFUTURE section ---
            vfuture_outer = ui.element("div").style(
                "flex:1;min-height:44px;overflow:hidden;"
                "display:flex;flex-direction:column;background:#0f1210;border-radius:8px;"
            )
            section_refs["vfuture"]["outer"] = vfuture_outer
            with vfuture_outer:
                _section_header_el(vfuture_label, len(vfuture_items), "#22c55e", "vfuture")
                vfuture_content = ui.element("div").style("flex:1;overflow-y:auto;padding:0 4px 4px;")
                section_refs["vfuture"]["content"] = vfuture_content
                with vfuture_content:
                    _render_section_items(vfuture_items, "vfuture")

        # Right column: side panel (hidden by default)
        panel_container = ui.element("div").classes("mc-side-panel").style("display:none;padding:16px;")
        panel_container_ref["el"] = panel_container
