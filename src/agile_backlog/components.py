"""NiceGUI UI components for agile-backlog."""

import base64
import html as _html
from datetime import date
from pathlib import Path

from nicegui import ui

from agile_backlog.models import BacklogItem
from agile_backlog.pure import (
    apply_reopen,
    category_style,
    comment_thread_html,
    filter_items,
    group_items_by_section,
    relative_time,
    render_card_html,
)
from agile_backlog.tokens import PRIORITY_COLORS
from agile_backlog.yaml_store import get_backlog_dir


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
    ui.html(f'<span style="{style}">{_html.escape(text)}</span>')


def _render_reopen_dialog(item: BacklogItem, save_fn, refresh_fn) -> None:
    """Show a dialog prompting for a reason, then reopen the done item back to doing."""
    reopen_dialog = ui.dialog().classes("mc-detail-dialog")
    with (
        reopen_dialog,
        ui.card().style(
            "background:#18181b;border:1px solid #27272a;color:#e4e4e7;"
            "padding:20px;max-width:480px;width:480px;border-radius:8px;"
        ),
    ):
        ui.html(
            f'<div style="font-size:14px;font-weight:700;color:#e4e4e7;margin-bottom:12px;">'
            f"Reopen: {_html.escape(item.title)}</div>"
        )
        reason_input = (
            ui.textarea(placeholder="Why is this being reopened?")
            .props("outlined autogrow rows=3")
            .style("width:100%;font-size:12px;")
        )
        reopen_error = ui.label("").style("color:#f87171;font-size:11px;display:none;")

        def _do_reopen():
            reason = (reason_input.value or "").strip()
            if not reason:
                reopen_error.style("display:block;")
                reopen_error.set_text("A reason is required to reopen an item.")
                return
            apply_reopen(item, reason)
            save_fn(item)
            reopen_dialog.close()
            refresh_fn()

        with ui.row().classes("gap-2 mt-3"):
            ui.button("Reopen", on_click=_do_reopen).props("flat dense no-caps").style("color:#f59e0b;font-weight:600;")
            ui.button("Cancel", on_click=reopen_dialog.close).props("flat dense no-caps").style("color:#a1a1aa;")
    reopen_dialog.open()


def _render_card(item: BacklogItem, status: str, move_fn, save_fn=None, refresh_fn=None, on_card_click=None) -> None:
    """Render a single Kanban card using the unified render_card_html design.

    If on_card_click is provided, clicking opens side panel.
    Move buttons appear below the card for non-done items.
    """
    is_done = status == "done"
    move_btn_style = (
        "font-family:'IBM Plex Mono',monospace;font-size:9px;padding:1px 6px;"
        "border-radius:3px;min-height:0;height:20px;"
    )

    with (
        ui.element("div")
        .classes("mc-board-card")
        .style("margin:2px 0;")
        .props(f'draggable="true" data-item-id="{item.id}" data-status="{status}"')
    ):
        # Card (clickable)
        card_container = ui.element("div").style("cursor:pointer;")
        if on_card_click:
            card_container.on("click", lambda _e, i=item: on_card_click(i))
        with card_container:
            ui.html(render_card_html(item))

        # Move buttons for non-done items
        if not is_done:
            all_statuses = ["backlog", "doing", "done"]
            other_statuses = [s for s in all_statuses if s != status]
            with ui.element("div").style("display:flex;gap:4px;padding:2px 10px 4px;"):
                for target in other_statuses:
                    arrow = "\u2190" if all_statuses.index(target) < all_statuses.index(status) else "\u2192"
                    ui.button(
                        f"{arrow} {target}",
                        on_click=lambda _e, i=item, t=target: move_fn(i, t),
                    ).props("flat dense unelevated no-caps").style(
                        f"{move_btn_style}color:#52525b;background:transparent;"
                    )
        else:
            # Reopen button for done items
            with ui.element("div").style("display:flex;gap:4px;padding:2px 10px 4px;"):

                def _show_reopen_dialog(_e, i=item):
                    _render_reopen_dialog(i, save_fn, refresh_fn)

                ui.button(
                    "\u21a9 Reopen",
                    on_click=_show_reopen_dialog,
                ).props("flat dense unelevated no-caps").style(f"{move_btn_style}color:#f59e0b;background:transparent;")


def _render_side_panel_content(
    item: BacklogItem,
    save_fn,
    refresh_fn,
    close_fn,
    all_items: list[BacklogItem] | None = None,
) -> None:
    """Render the side panel with click-to-edit fields, comments thread, and pinned comment input."""
    from agile_backlog.yaml_store import load_all as _load_all

    if all_items is None:
        all_items = _load_all()

    pill_base = (
        "font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;"
        "padding:2px 6px;border-radius:3px;letter-spacing:0.03em;white-space:nowrap;cursor:pointer;"
    )
    label_style = (
        "font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;"
        "color:#52525b;text-transform:uppercase;letter-spacing:0.08em;"
        "margin-top:10px;margin-bottom:3px;"
    )
    cat_color, cat_bg = category_style(item.category)
    pri_color, pri_bg = PRIORITY_COLORS.get(item.priority, ("#888", "#f3f4f6"))

    def _save_and_refresh():
        save_fn(item)
        refresh_fn()

    # Outer flex column: scrollable content + pinned comment input
    with ui.element("div").style("display:flex;flex-direction:column;height:100%;"):
        # === Scrollable content area ===
        with ui.element("div").style("flex:1;overflow-y:auto;padding-bottom:8px;"):
            # 1. Header: Close button only
            with ui.element("div").style("display:flex;justify-content:flex-end;align-items:center;margin-bottom:8px;"):
                ui.button(
                    "\u2715",
                    on_click=close_fn,
                ).props("flat dense no-caps").style("color:#71717a;font-size:14px;min-width:28px;padding:2px;")

            # 2. Title — click to edit
            title_container = ui.element("div")
            with title_container:
                _render_editable_title(item, title_container, _save_and_refresh)

            # 3. Metadata pills row 1: status, phase, priority, complexity, category
            with ui.element("div").style("display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px;"):
                _render_metadata_pill(
                    item,
                    "status",
                    item.status,
                    pill_base,
                    "#a1a1aa",
                    "#1e1e23",
                    options=["backlog", "doing", "done"],
                    save_and_refresh=_save_and_refresh,
                )
                _render_metadata_pill(
                    item,
                    "phase",
                    item.phase or "(no phase)",
                    pill_base,
                    "#71717a",
                    "#1e1e23",
                    options=[None, "plan", "spec", "build", "review"],
                    labels={None: "(no phase)", "plan": "plan", "spec": "spec", "build": "build", "review": "review"},
                    save_and_refresh=_save_and_refresh,
                    italic=True,
                )
                _render_metadata_pill(
                    item,
                    "priority",
                    item.priority,
                    pill_base,
                    pri_color,
                    pri_bg,
                    options=["P0", "P1", "P2", "P3", "P4"],
                    save_and_refresh=_save_and_refresh,
                )
                _render_metadata_pill(
                    item,
                    "complexity",
                    item.complexity or "(none)",
                    pill_base,
                    "#60a5fa",
                    "rgba(59,130,246,0.12)",
                    options=[None, "S", "M", "L"],
                    labels={None: "(none)", "S": "S", "M": "M", "L": "L"},
                    save_and_refresh=_save_and_refresh,
                )
                _render_metadata_pill(
                    item,
                    "category",
                    item.category,
                    pill_base,
                    cat_color,
                    cat_bg,
                    options=["bug", "feature", "docs", "chore"],
                    save_and_refresh=_save_and_refresh,
                )

            # 4. Tags row 2: tag pills + "+ tag" + updated timestamp
            with ui.element("div").style("display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-top:6px;"):
                _render_editable_tags(item, all_items, _save_and_refresh)
                # Updated timestamp
                ui.html(
                    f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;"
                    f'color:#3f3f46;margin-left:auto;">updated {relative_time(item.updated)}</span>'
                )

            # 5. Divider
            ui.html('<div style="border-top:1px solid #1e1e23;margin:10px 0;"></div>')

            # 6. Goal — click to edit (markdown)
            ui.html(f'<div style="{label_style}">Goal</div>')
            goal_container = ui.element("div")
            with goal_container:
                _render_editable_textarea(
                    item,
                    "goal",
                    item.goal,
                    goal_container,
                    _save_and_refresh,
                    use_markdown=True,
                )

            # 7. Description — click to edit (markdown)
            ui.html(f'<div style="{label_style}">Description</div>')
            desc_container = ui.element("div")
            with desc_container:
                _render_editable_textarea(
                    item,
                    "description",
                    item.description,
                    desc_container,
                    _save_and_refresh,
                    use_markdown=True,
                )

            # 8. Acceptance Criteria — click to edit
            ui.html(f'<div style="{label_style}">Acceptance Criteria</div>')
            ac_container = ui.element("div")
            with ac_container:
                _render_editable_list_field(
                    item,
                    "acceptance_criteria",
                    item.acceptance_criteria,
                    ac_container,
                    _save_and_refresh,
                )

            # 9. Technical Specs — click to edit
            ui.html(f'<div style="{label_style}">Technical Specs</div>')
            ts_container = ui.element("div")
            with ts_container:
                _render_editable_list_field(
                    item,
                    "technical_specs",
                    item.technical_specs,
                    ts_container,
                    _save_and_refresh,
                )

            # 10. Notes — click to edit (markdown)
            ui.html(f'<div style="{label_style}">Notes</div>')
            notes_container = ui.element("div")
            with notes_container:
                _render_editable_textarea(
                    item,
                    "notes",
                    item.notes,
                    notes_container,
                    _save_and_refresh,
                    use_markdown=True,
                )

            # 11. Images section
            ui.html(f'<div style="{label_style}">Images</div>')
            _render_images_section(item, _save_and_refresh)

            # 12. Divider
            ui.html('<div style="border-top:1px solid #1e1e23;margin:10px 0;"></div>')

            # 13. Comments thread
            ui.html(f'<div style="{label_style}">Comments</div>')
            if item.comments:
                ui.html(comment_thread_html(item.comments))
                # Resolve buttons for flagged, unresolved comments
                for idx, comment in enumerate(item.comments):
                    if comment.get("flagged") and not comment.get("resolved"):
                        preview = comment.get("text", "")[:40]

                        def _resolve_comment(comment_idx=idx):
                            item.comments[comment_idx]["resolved"] = True
                            _save_and_refresh()

                        with ui.element("div").style("display:flex;align-items:center;gap:6px;margin:2px 0 2px 12px;"):
                            ui.html(
                                f'<span style="font-size:10px;color:#71717a;font-style:italic;">'
                                f'Resolve: "{preview}..."</span>'
                            )
                            ui.button(
                                "\u2713 Resolve",
                                on_click=_resolve_comment,
                            ).props("flat dense no-caps").style(
                                "color:#4ade80;font-size:10px;min-width:0;padding:1px 6px;"
                            )
            else:
                ui.html('<div style="font-size:11px;color:#52525b;font-style:italic;">No comments yet.</div>')

        # === Pinned comment input area (flex-shrink:0) ===
        with ui.element("div").style("flex-shrink:0;border-top:1px solid #27272a;padding-top:10px;"):
            comment_text = (
                ui.textarea()
                .props("outlined dense rows=2 placeholder='Write a comment...'")
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
                    _save_and_refresh()

                ui.button("Send", on_click=_send_comment).props("flat dense no-caps").style(
                    "color:#3b82f6;font-size:11px;font-weight:600;"
                )


def _render_editable_title(item: BacklogItem, container, save_and_refresh) -> None:
    """Render a click-to-edit title field."""
    title_style = (
        "font-size:16px;font-weight:700;color:#e4e4e7;line-height:1.3;font-family:'DM Sans',sans-serif;padding:2px 4px;"
    )

    def _show_label():
        container.clear()
        with container:
            label_el = ui.html(f'<div style="{title_style}">{_html.escape(item.title)}</div>').classes("mc-editable")
            label_el.on("click", lambda _e: _show_input())

    def _show_input():
        container.clear()
        with container:
            inp = ui.input(value=item.title).props("outlined dense").style("width:100%;font-size:14px;font-weight:600;")

            def _save(e=None):
                new_val = (inp.value or "").strip()
                if new_val and new_val != item.title:
                    item.title = new_val
                    save_and_refresh()
                else:
                    _show_label()

            inp.on("blur", _save)
            inp.on("keydown.enter", _save)

    _show_label()


def _render_metadata_pill(
    item: BacklogItem,
    field: str,
    display_text: str,
    pill_base: str,
    text_color: str,
    bg_color: str,
    options: list,
    save_and_refresh,
    labels: dict | None = None,
    italic: bool = False,
) -> None:
    """Render a clickable metadata pill with a dropdown menu."""
    extra_style = "font-style:italic;text-transform:none;" if italic else "text-transform:uppercase;"
    with (
        ui.element("span")
        .classes("mc-editable")
        .style(f"{pill_base}{extra_style}color:{text_color};background:{bg_color};")
    ):
        ui.label(display_text).style("font-size:inherit;color:inherit;font-weight:inherit;")
        with ui.menu() as menu:
            for opt in options:
                opt_label = labels[opt] if labels and opt in labels else (opt if opt is not None else "(none)")

                def _select(val=opt, m=menu):
                    setattr(item, field, val)
                    m.close()
                    save_and_refresh()

                ui.menu_item(opt_label, on_click=_select)


def _render_editable_tags(item: BacklogItem, all_items: list[BacklogItem], save_and_refresh) -> None:
    """Render tag pills with remove buttons and a + tag button."""
    all_tags = sorted({t for i in all_items for t in i.tags})

    for tag in list(item.tags):
        tag_html = (
            f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;"
            f"background:#1e1e23;color:#a1a1aa;padding:1px 6px;"
            f'border-radius:3px;display:inline-flex;align-items:center;gap:3px;">'
            f'{_html.escape(tag)} <span style="cursor:pointer;color:#71717a;font-size:11px;">\u00d7</span></span>'
        )
        tag_el = ui.html(tag_html).style("cursor:pointer;")

        def _remove_tag(_e, t=tag):
            if t in item.tags:
                item.tags.remove(t)
                save_and_refresh()

        tag_el.on("click", _remove_tag)

    # + tag button with autocomplete input
    add_tag_container = ui.element("span")
    with add_tag_container:

        def _show_tag_input():
            add_tag_container.clear()
            with add_tag_container:
                tag_inp = (
                    ui.select(
                        options=all_tags,
                        with_input=True,
                        new_value_mode="add-unique",
                        value=None,
                    )
                    .props("dense outlined placeholder='tag'")
                    .style("min-width:80px;max-width:120px;font-size:9px;")
                    .classes("mc-select")
                )

                def _add_tag(e):
                    val = tag_inp.value
                    if val and val not in item.tags:
                        item.tags.append(val)
                        save_and_refresh()
                    else:
                        _show_add_button()

                tag_inp.on("update:model-value", _add_tag)

        def _show_add_button():
            add_tag_container.clear()
            with add_tag_container:
                add_btn = ui.html(
                    "<span style=\"font-family:'IBM Plex Mono',monospace;font-size:9px;"
                    "background:#1e1e23;color:#52525b;padding:1px 6px;"
                    'border-radius:3px;cursor:pointer;">+ tag</span>'
                )
                add_btn.on("click", lambda _e: _show_tag_input())

        _show_add_button()


def _render_editable_textarea(
    item: BacklogItem,
    field: str,
    current_value: str,
    container,
    save_and_refresh,
    use_markdown: bool = False,
) -> None:
    """Render a click-to-edit text area field."""
    value_style = "color:#d4d4d8;font-size:12px;font-family:'DM Sans',sans-serif;padding:2px 4px;"
    empty_style = "font-size:11px;color:#52525b;font-style:italic;padding:2px 4px;"

    def _show_display():
        container.clear()
        with container:
            if current_value:
                if use_markdown:
                    el = ui.markdown(current_value).style(value_style).classes("mc-editable")
                else:
                    escaped = _html.escape(current_value)
                    el = ui.html(f'<div style="{value_style}">{escaped}</div>').classes("mc-editable")
            else:
                el = ui.html(f'<div style="{empty_style}">Click to add...</div>').classes("mc-editable")
            el.on("click", lambda _e: _show_editor())

    def _show_editor():
        container.clear()
        with container:
            ta = (
                ui.textarea(value=getattr(item, field))
                .props("outlined autogrow rows=4")
                .style("width:100%;font-size:12px;")
            )
            with ui.row().classes("gap-2").style("margin-top:4px;"):

                def _save():
                    setattr(item, field, ta.value or "")
                    save_and_refresh()

                ui.button("Save", on_click=_save).props("flat dense no-caps").style("color:#3b82f6;font-size:10px;")
                ui.button("Cancel", on_click=lambda: _show_display()).props("flat dense no-caps").style(
                    "color:#a1a1aa;font-size:10px;"
                )

    _show_display()


def _render_editable_list_field(
    item: BacklogItem,
    field: str,
    current_values: list[str],
    container,
    save_and_refresh,
) -> None:
    """Render a click-to-edit list field (one item per line)."""
    empty_style = "font-size:11px;color:#52525b;font-style:italic;padding:2px 4px;"

    def _show_display():
        container.clear()
        with container:
            if current_values:
                li_items = "".join(
                    f'<li style="margin-bottom:1px;color:#a1a1aa;font-size:11px;">{_html.escape(v)}</li>'
                    for v in current_values
                )
                el = ui.html(f'<ul style="padding-left:14px;">{li_items}</ul>').classes("mc-editable")
            else:
                el = ui.html(f'<div style="{empty_style}">Click to add...</div>').classes("mc-editable")
            el.on("click", lambda _e: _show_editor())

    def _show_editor():
        container.clear()
        with container:
            current_text = "\n".join(getattr(item, field))
            ta = ui.textarea(value=current_text).props("outlined autogrow rows=4").style("width:100%;font-size:12px;")
            with ui.row().classes("gap-2").style("margin-top:4px;"):

                def _save():
                    lines = [line.strip() for line in (ta.value or "").split("\n") if line.strip()]
                    setattr(item, field, lines)
                    save_and_refresh()

                ui.button("Save", on_click=_save).props("flat dense no-caps").style("color:#3b82f6;font-size:10px;")
                ui.button("Cancel", on_click=lambda: _show_display()).props("flat dense no-caps").style(
                    "color:#a1a1aa;font-size:10px;"
                )

    _show_display()


def _get_images_dir(item_id: str) -> Path:
    images_dir = get_backlog_dir() / "images" / item_id
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


def _render_images_section(item: BacklogItem, save_and_refresh) -> None:
    images_container = ui.element("div")

    def _refresh_images():
        images_container.clear()
        with images_container:
            if item.images:
                with ui.element("div").style("display:flex;flex-wrap:wrap;gap:6px;margin:4px 0;"):
                    for idx, img_entry in enumerate(item.images):
                        fname = img_entry.get("filename", "")
                        img_path = _get_images_dir(item.id) / fname
                        if not img_path.exists():
                            continue
                        with (
                            ui.element("div")
                            .style("position:relative;width:80px;height:80px;")
                            .classes("mc-thumb-wrapper")
                        ):
                            ui.image(str(img_path)).style(
                                "width:80px;height:80px;object-fit:cover;border-radius:4px;border:1px solid #27272a;"
                            )

                            def _delete_image(_e, i=idx):
                                item.images.pop(i)
                                save_and_refresh()

                            ui.button(
                                "\u00d7",
                                on_click=_delete_image,
                            ).props("flat dense no-caps").style(
                                "position:absolute;top:0;right:0;min-width:18px;min-height:18px;"
                                "padding:0;font-size:12px;color:#f87171;background:rgba(0,0,0,0.6);"
                                "border-radius:0 4px 0 4px;line-height:1;"
                            ).classes("mc-thumb-delete")
            else:
                ui.html(
                    '<div style="font-size:11px;color:#52525b;font-style:italic;">No images yet. '
                    "Paste (Ctrl+V) or upload.</div>"
                )

            def _handle_upload(e):
                content = e.content.read()
                fname = e.name
                images_dir = _get_images_dir(item.id)
                dest = images_dir / fname
                # Avoid overwriting — add suffix if exists
                counter = 1
                while dest.exists():
                    stem = Path(fname).stem
                    suffix = Path(fname).suffix
                    dest = images_dir / f"{stem}-{counter}{suffix}"
                    counter += 1
                dest.write_bytes(content)
                item.images.append({"filename": dest.name, "created": str(date.today())})
                save_and_refresh()

            ui.upload(
                on_upload=_handle_upload,
                auto_upload=True,
                label="Upload image",
            ).props("accept=image/* flat dense").style("max-width:200px;font-size:11px;")

            # Hidden trigger for paste — JS stores data URL in window._pastedImage, then clicks trigger
            paste_trigger = ui.element("div").props('id="mc-paste-trigger"').style("display:none;")

            async def _handle_paste(_e):
                data_url = await ui.run_javascript("window._pastedImage || null")
                if not data_url or not isinstance(data_url, str):
                    return
                if not data_url.startswith("data:image/"):
                    return
                header, b64data = data_url.split(",", 1)
                mime = header.split(":")[1].split(";")[0]
                ext_map = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp"}
                ext = ext_map.get(mime, ".png")
                img_bytes = base64.b64decode(b64data)
                images_dir = _get_images_dir(item.id)
                counter = len(item.images) + 1
                fname = f"pasted-{counter}{ext}"
                dest = images_dir / fname
                while dest.exists():
                    counter += 1
                    fname = f"pasted-{counter}{ext}"
                    dest = images_dir / fname
                dest.write_bytes(img_bytes)
                item.images.append({"filename": fname, "created": str(date.today())})
                save_and_refresh()

            paste_trigger.on("click", _handle_paste)

            # JS paste listener — same pattern as drag-and-drop hidden trigger
            _paste_js = """
document.addEventListener('paste', function(e) {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
        if (item.type.startsWith('image/')) {
            const blob = item.getAsFile();
            const reader = new FileReader();
            reader.onload = function() {
                window._pastedImage = reader.result;
                const trigger = document.getElementById('mc-paste-trigger');
                if (trigger) trigger.click();
            };
            reader.readAsDataURL(blob);
            e.preventDefault();
            break;
        }
    }
});
"""
            ui.timer(0.1, lambda: ui.run_javascript(_paste_js), once=True)

    _refresh_images()


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

    # Keyboard navigation state
    nav_state: dict[str, int | None] = {"index": None}
    all_section_items = filtered_backlog + vnext_items + vfuture_items

    def _open_side_panel(item: BacklogItem):
        panel_state["selected_id"] = item.id
        # Sync keyboard nav index
        try:
            nav_state["index"] = all_section_items.index(item)
        except ValueError:
            nav_state["index"] = None
        if list_container_ref["el"]:
            list_container_ref["el"].style("flex:6;min-width:0;")
        if panel_container_ref["el"]:
            panel_container_ref["el"].style("flex:4;min-width:320px;display:block;")
            panel_container_ref["el"].clear()
            with panel_container_ref["el"]:
                _render_side_panel_content(item, save_fn, refresh_fn, _close_side_panel, all_items=all_items)

    def _close_side_panel():
        panel_state["selected_id"] = None
        if list_container_ref["el"]:
            list_container_ref["el"].style("flex:1;min-width:0;")
        if panel_container_ref["el"]:
            panel_container_ref["el"].style("display:none;")
            panel_container_ref["el"].clear()

    def _handle_key(e):
        if e.action.repeat:
            return
        if e.key == "Escape":
            _close_side_panel()
            nav_state["index"] = None
            return
        if e.key in ("ArrowDown", "ArrowUp") and all_section_items:
            current = nav_state["index"]
            if e.key == "ArrowDown":
                if current is None:
                    nav_state["index"] = 0
                else:
                    nav_state["index"] = min(current + 1, len(all_section_items) - 1)
            elif e.key == "ArrowUp":
                if current is None:
                    nav_state["index"] = len(all_section_items) - 1
                else:
                    nav_state["index"] = max(current - 1, 0)
            focused_item = all_section_items[nav_state["index"]]
            _open_side_panel(focused_item)
            # Scroll the focused item into view
            ui.run_javascript(
                "const s = document.querySelector('.mc-card-row.mc-selected');"
                "if (s) s.scrollIntoView({block: 'nearest', behavior: 'smooth'});"
            )

    ui.keyboard(on_key=_handle_key)

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
            selected_class = " mc-selected" if panel_state["selected_id"] == card_item.id else ""
            with (
                ui.element("div")
                .classes(f"mc-card-row{selected_class}")
                .style("position:relative;margin:2px 0;padding:0 4px;")
                .props(f'draggable="true" data-item-id="{card_item.id}" data-section="{section}"')
            ):
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

    # Hidden drop handler — JS stores drop data in window._lastDrop, then clicks this element
    next_sprint = (current_sprint or 0) + 1
    future_sprint = (current_sprint or 0) + 2
    drop_trigger = ui.element("div").props('id="mc-drop-trigger"').style("display:none;")

    async def _handle_drop(_e):
        detail = await ui.run_javascript("window._lastDrop || null")
        if not detail:
            return
        item_id = detail.get("item_id")
        sprint_target_str = detail.get("sprint_target")
        sprint_target = None if sprint_target_str == "null" else int(sprint_target_str)
        item = next((i for i in all_items if i.id == item_id), None)
        if item:
            _move_to_section(item, sprint_target)

    drop_trigger.on("click", _handle_drop)

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
                backlog_content = (
                    ui.element("div")
                    .classes("mc-drop-zone")
                    .props('data-section="backlog" data-sprint-target="null"')
                    .style("flex:1;overflow-y:auto;padding:0 4px 4px;")
                )
                section_refs["backlog"]["content"] = backlog_content
                with backlog_content:
                    _render_section_items(filtered_backlog, "backlog")

            ui.html('<div class="mc-resize-handle"></div>')

            # --- vNEXT section ---
            vnext_outer = ui.element("div").style(
                "flex:1;min-height:44px;overflow:hidden;"
                "display:flex;flex-direction:column;background:#14130e;border:1px solid #2a2618;"
                "border-radius:8px;margin-bottom:4px;"
            )
            section_refs["vnext"]["outer"] = vnext_outer
            with vnext_outer:
                _section_header_el(vnext_label, len(vnext_items), "#ca8a04", "vnext")
                vnext_content = (
                    ui.element("div")
                    .classes("mc-drop-zone")
                    .props(f'data-section="vnext" data-sprint-target="{next_sprint}"')
                    .style("flex:1;overflow-y:auto;padding:0 4px 4px;")
                )
                section_refs["vnext"]["content"] = vnext_content
                with vnext_content:
                    _render_section_items(vnext_items, "vnext")

            ui.html('<div class="mc-resize-handle"></div>')

            # --- vFUTURE section ---
            vfuture_outer = ui.element("div").style(
                "flex:1;min-height:44px;overflow:hidden;"
                "display:flex;flex-direction:column;background:#0f1210;border-radius:8px;"
            )
            section_refs["vfuture"]["outer"] = vfuture_outer
            with vfuture_outer:
                _section_header_el(vfuture_label, len(vfuture_items), "#22c55e", "vfuture")
                vfuture_content = (
                    ui.element("div")
                    .classes("mc-drop-zone")
                    .props(f'data-section="vfuture" data-sprint-target="{future_sprint}"')
                    .style("flex:1;overflow-y:auto;padding:0 4px 4px;")
                )
                section_refs["vfuture"]["content"] = vfuture_content
                with vfuture_content:
                    _render_section_items(vfuture_items, "vfuture")

        # Inject drag-to-resize JS for section handles
        _resize_js = """
document.querySelectorAll('.mc-resize-handle').forEach(handle => {
    handle.addEventListener('mousedown', function(e) {
        e.preventDefault();
        // NiceGUI wraps each element in a container div, so we navigate via the wrapper
        const wrapper = handle.parentElement;
        const above = wrapper.previousElementSibling;
        const below = wrapper.nextElementSibling;
        if (!above || !below) return;
        const startY = e.clientY;
        const startAboveH = above.getBoundingClientRect().height;
        const startBelowH = below.getBoundingClientRect().height;

        function onMove(ev) {
            const dy = ev.clientY - startY;
            const newAbove = Math.max(44, startAboveH + dy);
            const newBelow = Math.max(44, startBelowH - dy);
            above.style.flex = '0 0 ' + newAbove + 'px';
            below.style.flex = '0 0 ' + newBelow + 'px';
        }
        function onUp() {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        }
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
});
"""
        _drag_drop_js = """
document.querySelectorAll('.mc-card-row[draggable]').forEach(row => {
    row.addEventListener('dragstart', function(e) {
        e.dataTransfer.setData('text/plain', row.getAttribute('data-item-id'));
        e.dataTransfer.effectAllowed = 'move';
        row.classList.add('mc-dragging');
    });
    row.addEventListener('dragend', function() {
        row.classList.remove('mc-dragging');
        document.querySelectorAll('.mc-drag-over').forEach(el => el.classList.remove('mc-drag-over'));
    });
});

document.querySelectorAll('.mc-drop-zone').forEach(zone => {
    zone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        zone.classList.add('mc-drag-over');
    });
    zone.addEventListener('dragleave', function(e) {
        if (!zone.contains(e.relatedTarget)) {
            zone.classList.remove('mc-drag-over');
        }
    });
    zone.addEventListener('drop', function(e) {
        e.preventDefault();
        zone.classList.remove('mc-drag-over');
        const itemId = e.dataTransfer.getData('text/plain');
        const sprintTarget = zone.getAttribute('data-sprint-target');
        window._lastDrop = {item_id: itemId, sprint_target: sprintTarget};
        document.getElementById('mc-drop-trigger').click();
    });
});
"""
        _all_js = _resize_js + "\n" + _drag_drop_js
        ui.timer(0.1, lambda: ui.run_javascript(_all_js), once=True)

        # Right column: side panel (hidden by default)
        panel_container = ui.element("div").classes("mc-side-panel").style("display:none;padding:16px;")
        panel_container_ref["el"] = panel_container
