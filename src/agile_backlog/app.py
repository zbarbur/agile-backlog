# src/app.py
"""NiceGUI Kanban board for agile-backlog — Mission Control dark theme."""

from nicegui import ui

from agile_backlog.components import (
    _render_backlog_list,
    _render_card,
    _render_side_panel_content,
)
from agile_backlog.models import BacklogItem, slugify
from agile_backlog.pure import (
    backlog_dir_mtime,
    detect_current_sprint,
    filter_items,
    group_done_by_sprint,
    is_recent_sprint,
    safe_html,
)
from agile_backlog.styles import (
    COLUMN_STYLES,
    GLOBAL_CSS,
    LABELS,
    STATUSES,
)
from agile_backlog.tokens import PRIORITY_ORDER

# Sort option definitions: key -> (label, sort_key_fn, reverse)
SORT_OPTIONS = {
    "priority_desc": "Priority \u2193",
    "priority_asc": "Priority \u2191",
    "updated_desc": "Updated \u2193",
    "updated_asc": "Updated \u2191",
    "created_desc": "Created \u2193",
    "title_asc": "Title A-Z",
}


def _sort_items(items: list[BacklogItem], sort_key: str) -> list[BacklogItem]:
    """Sort items according to the chosen sort option."""
    if sort_key == "priority_desc":
        return sorted(items, key=lambda i: PRIORITY_ORDER.get(i.priority, 99))
    if sort_key == "priority_asc":
        return sorted(items, key=lambda i: PRIORITY_ORDER.get(i.priority, 99), reverse=True)
    if sort_key == "updated_desc":
        return sorted(items, key=lambda i: i.updated, reverse=True)
    if sort_key == "updated_asc":
        return sorted(items, key=lambda i: i.updated)
    if sort_key == "created_desc":
        return sorted(items, key=lambda i: i.created, reverse=True)
    if sort_key == "title_asc":
        return sorted(items, key=lambda i: i.title.lower())
    return items


@ui.page("/")
def kanban_page():
    """Render the Kanban board — Mission Control dark theme."""
    from agile_backlog.yaml_store import get_backlog_dir, item_exists, load_all, load_item, save_item

    # --- Inject global styles ---
    ui.add_head_html(GLOBAL_CSS)

    # --- Load data ---
    all_items = load_all()
    current_sprint = detect_current_sprint(all_items)

    # Outer column: header (flex-shrink:0), filter bar (flex-shrink:0), content (flex:1)
    with ui.element("div").style("width:100%;height:100vh;display:flex;flex-direction:column;padding:0;"):
        # === Header Row ===
        with ui.element("div").style(
            "flex-shrink:0;display:flex;align-items:center;gap:12px;padding:12px 24px;border-bottom:1px solid #1e1e23;"
        ):
            from agile_backlog.config import get_project_name, get_version

            project_name = get_project_name()
            version = get_version()
            ui.html(
                f'<span style="font-size:16px;font-weight:700;color:#fafafa;'
                f"letter-spacing:-0.02em;font-family:'DM Sans',sans-serif;"
                f'">{safe_html(project_name)}</span>'
            )
            ui.html(
                f"<span style=\"font-family:'IBM Plex Mono',monospace;font-size:10px;"
                f'color:#52525b;letter-spacing:0.02em;">v{safe_html(version)}</span>'
            )

            # Sprint badge container — visibility toggled by view mode
            sprint_badge_el = ui.element("div")
            if current_sprint is not None:
                with sprint_badge_el:
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
                ui.run_javascript(f"localStorage.setItem('ab_view_mode', '{mode}')")
                # Update button styles
                board_btn_el.style(
                    "background:#fafafa;color:#09090b;" if mode == "board" else "background:transparent;color:#71717a;"
                )
                backlog_btn_el.style(
                    "background:#fafafa;color:#09090b;"
                    if mode == "backlog"
                    else "background:transparent;color:#71717a;"
                )
                done_btn_el.style(
                    "background:#fafafa;color:#09090b;" if mode == "done" else "background:transparent;color:#71717a;"
                )
                context_btn_el.style(
                    "background:#fafafa;color:#09090b;"
                    if mode == "context"
                    else "background:transparent;color:#71717a;"
                )
                process_btn_el.style(
                    "background:#fafafa;color:#09090b;"
                    if mode == "process"
                    else "background:transparent;color:#71717a;"
                )
                sprint_badge_el.style("display:block;" if mode == "board" else "display:none;")
                archive_toggle.style(
                    "display:block;font-size:11px;color:#71717a;" if mode == "board" else "display:none;"
                )
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
                done_btn_el = (
                    ui.button("Done", on_click=lambda: _set_view("done"))
                    .props("flat dense no-caps unelevated")
                    .style(
                        "font-size:11px;font-weight:600;padding:4px 14px;border-radius:0;"
                        "background:transparent;color:#71717a;min-height:0;"
                    )
                )
                # --- Divider between Sprint views and Observability views ---
                ui.element("div").style("width:1px;height:20px;background:#3f3f46;margin:0 8px;")
                context_btn_el = (
                    ui.button("Context", on_click=lambda: _set_view("context"))
                    .props("flat dense no-caps unelevated")
                    .style(
                        "font-size:11px;font-weight:600;padding:4px 14px;border-radius:0;"
                        "background:transparent;color:#71717a;min-height:0;"
                    )
                )
                process_btn_el = (
                    ui.button("Process", on_click=lambda: _set_view("process"))
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
                            add_sprint_options[current_sprint + 2] = f"Sprint {current_sprint + 2}+ (future)"
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

                    # Image paste/upload in add dialog — store in memory until save
                    pending_images: list[dict] = []
                    images_preview = ui.element("div")

                    def _refresh_add_preview():
                        images_preview.clear()
                        if not pending_images:
                            return
                        with images_preview:
                            with ui.element("div").style("display:flex;flex-wrap:wrap;gap:6px;margin:8px 0;"):
                                for pidx, pimg in enumerate(pending_images):
                                    with ui.element("div").style(
                                        "position:relative;width:80px;height:60px;overflow:hidden;"
                                        "border-radius:4px;border:1px solid #27272a;"
                                    ):
                                        ui.image(f"data:{pimg['mime']};base64,{pimg['b64']}").style(
                                            "width:100%;height:100%;object-fit:cover;"
                                        )

                                        def _remove(i=pidx):
                                            pending_images.pop(i)
                                            _refresh_add_preview()

                                        ui.button("\u00d7", on_click=_remove).props("flat dense no-caps").style(
                                            "position:absolute;top:1px;right:1px;min-width:16px;min-height:16px;"
                                            "padding:0;font-size:11px;color:#f87171;background:rgba(0,0,0,0.7);"
                                            "border-radius:3px;line-height:1;"
                                        )

                    add_paste_trigger = ui.element("div").props('id="mc-add-paste-trigger"').style("display:none;")

                    async def _handle_add_paste(_e):
                        data_url = await ui.run_javascript("window._addPastedImage || null")
                        if not data_url or not isinstance(data_url, str):
                            return
                        await ui.run_javascript("window._addPastedImage = null")
                        if not data_url.startswith("data:image/"):
                            return
                        header, b64data = data_url.split(",", 1)
                        mime = header.split(":")[1].split(";")[0]
                        ext_map = {
                            "image/png": ".png",
                            "image/jpeg": ".jpg",
                            "image/gif": ".gif",
                            "image/webp": ".webp",
                        }
                        ext = ext_map.get(mime, ".png")
                        fname = f"pasted-{len(pending_images) + 1}{ext}"
                        pending_images.append({"filename": fname, "mime": mime, "b64": b64data})
                        _refresh_add_preview()

                    add_paste_trigger.on("click", _handle_add_paste)

                    _add_paste_js = """
if (!window._mcAddPasteListenerAdded) {
    window._mcAddPasteListenerAdded = true;
    document.addEventListener('paste', function(e) {
        const trigger = document.getElementById('mc-add-paste-trigger');
        if (!trigger) return;
        const items = e.clipboardData?.items;
        if (!items) return;
        for (const item of items) {
            if (item.type.startsWith('image/')) {
                const blob = item.getAsFile();
                const reader = new FileReader();
                reader.onload = function() {
                    window._addPastedImage = reader.result;
                    trigger.click();
                };
                reader.readAsDataURL(blob);
                e.preventDefault();
                break;
            }
        }
    });
}
"""
                    ui.timer(0.1, lambda: ui.run_javascript(_add_paste_js), once=True)

                    ui.html('<div style="font-size:10px;color:#52525b;margin-top:4px;">Paste image with Cmd+V</div>')

                    add_error = ui.label("").style("color:#f87171;font-size:11px;display:none;")

                    def _save_new_item():
                        import base64 as _b64

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
                        base_id = item_id
                        counter = 2
                        while item_exists(item_id):
                            item_id = f"{base_id}-{counter}"
                            counter += 1
                        sprint_val = add_sprint.value
                        image_entries = []
                        if pending_images:
                            images_dir = get_backlog_dir() / "images" / item_id
                            images_dir.mkdir(parents=True, exist_ok=True)
                            for pimg in pending_images:
                                dest = images_dir / pimg["filename"]
                                dest.write_bytes(_b64.b64decode(pimg["b64"]))
                                from datetime import date as _date

                                image_entries.append({"filename": pimg["filename"], "created": str(_date.today())})
                        new_item = BacklogItem(
                            id=item_id,
                            title=title,
                            priority=add_priority.value,
                            category=cat,
                            description=add_description.value or "",
                            sprint_target=int(sprint_val) if sprint_val is not None and sprint_val != "" else None,
                            images=image_entries,
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

            # Archive toggle + sprints config — only visible in Board view
            from agile_backlog.config import get_archive_sprints as _get_as
            from agile_backlog.config import set_archive_sprints as _set_as

            archive_sprints_options = {1: "1 sprint", 2: "2 sprints", 3: "3 sprints", 5: "5 sprints"}
            current_as = _get_as()

            def _on_archive_sprints_change(e):
                if e.value is not None:
                    _set_as(int(e.value))
                    render_board.refresh()

            with ui.element("div").style("display:flex;align-items:center;gap:6px;"):
                archive_toggle = (
                    ui.checkbox("Show archived", value=False)
                    .classes("mc-done-check")
                    .style("font-size:12px;color:#a1a1aa;")
                )
                (
                    ui.select(options=archive_sprints_options, value=current_as, on_change=_on_archive_sprints_change)
                    .props("dense borderless dark")
                    .style(
                        "min-width:80px;max-width:95px;font-size:11px;color:#a1a1aa;"
                        "font-family:'IBM Plex Mono',monospace;"
                    )
                )

        # === Filter Bar ===
        priority_options = {"P1": "P1", "P2": "P2", "P3": "P3"}
        categories = sorted({i.category for i in all_items})
        category_options = {c: c for c in categories}
        all_sprints = sorted({i.sprint_target for i in all_items if i.sprint_target is not None})
        sprint_options = {}
        if current_sprint is not None:
            sprint_options["current"] = f"Current (S{current_sprint})"
        sprint_options["unplanned"] = "Unplanned"
        # Show only recent sprints (current -2 to current +2) to avoid long dropdown
        if current_sprint is not None:
            recent_range = range(max(1, current_sprint - 2), current_sprint + 3)
            for s in all_sprints:
                if s in recent_range:
                    sprint_options[s] = f"Sprint {s}"
        else:
            for s in all_sprints:
                sprint_options[s] = f"Sprint {s}"
        phases = sorted({i.phase for i in all_items if i.phase})
        phase_options = {None: "All phases", **{p: p for p in phases}}
        all_tags_filter = sorted({t for i in all_items for t in i.tags})

        with ui.element("div").style(
            "flex-shrink:0;display:flex;flex-wrap:wrap;gap:8px;padding:8px 24px 10px;"
            "border-bottom:1px solid #1e1e23;align-items:center;"
        ):
            priority_select = (
                ui.select(label="Priority", options=priority_options, multiple=True, value=[])
                .props("dense outlined use-chips")
                .classes("mc-select")
                .style("min-width:110px;max-width:160px;")
            )
            category_select = (
                ui.select(label="Category", options=category_options, multiple=True, value=[])
                .props("dense outlined use-chips")
                .classes("mc-select")
                .style("min-width:110px;max-width:160px;")
            )
            sprint_select = (
                ui.select(label="Sprint", options=sprint_options, multiple=True, value=[])
                .props("dense outlined use-chips")
                .classes("mc-select")
                .style("min-width:110px;max-width:160px;")
            )
            phase_select = (
                ui.select(label="Phase", options=phase_options, value=None)
                .props("dense outlined")
                .classes("mc-select")
                .style("min-width:100px;max-width:140px;")
            )
            tag_select = (
                ui.select(label="Tags", options=all_tags_filter, multiple=True, value=[])
                .props("dense outlined use-chips")
                .classes("mc-select")
                .style("min-width:110px;max-width:160px;")
            )

            # Sort control
            sort_select = (
                ui.select(label="Sort", options=SORT_OPTIONS, value="priority_desc")
                .props("dense outlined")
                .classes("mc-select")
                .style("min-width:110px;max-width:150px;")
            )

            search_input = (
                ui.input(placeholder="Search...")
                .props("dense outlined")
                .classes("mc-search")
                .style("flex:1;min-width:120px;min-height:32px;")
            )

            # Inline filter chips — rendered inside the filter bar
            filter_chips_container = ui.element("div").style("display:flex;flex-wrap:wrap;gap:4px;align-items:center;")

        def _render_inline_chips():
            """Render removable filter chips inline in the filter bar."""
            filter_chips_container.clear()
            with filter_chips_container:
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

        # === Main Content Area ===
        main_content = ui.element("div").style("flex:1;overflow:auto;padding:8px 24px 16px;")

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
            _render_inline_chips()
            items = load_all()

            pf_list = priority_select.value or []
            cf_list = category_select.value or []
            sf_list = sprint_select.value or []
            phf = phase_select.value
            tf_list = tag_select.value or []
            sq = search_input.value or ""
            show_archived = archive_toggle.value
            active_sort = sort_select.value or "priority_desc"

            # Resolve "current" sprint value to actual sprint number
            resolved_sprints: list[int | str] = []
            for sv in sf_list:
                if sv == "current" and current_sprint is not None:
                    resolved_sprints.append(current_sprint)
                else:
                    resolved_sprints.append(sv)

            backlog_items = [i for i in items if i.status == "backlog"]
            doing_items = [i for i in items if i.status == "doing"]
            from agile_backlog.config import get_archive_sprints

            archive_sprints = get_archive_sprints()
            done_items = [
                i
                for i in items
                if i.status == "done"
                and (
                    show_archived
                    or is_recent_sprint(i, current_sprint=current_sprint or 0, archive_sprints=archive_sprints)
                )
            ]

            # Apply search filter to all columns
            filtered_backlog = filter_items(backlog_items, search=sq)
            filtered_doing = filter_items(doing_items, search=sq)
            filtered_done = filter_items(done_items, search=sq)

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

            # Apply sorting
            filtered_backlog = _sort_items(filtered_backlog, active_sort)
            filtered_doing = _sort_items(filtered_doing, active_sort)
            filtered_done = _sort_items(filtered_done, active_sort)

            columns_map = {
                "backlog": filtered_backlog,
                "doing": filtered_doing,
                "done": filtered_done,
            }

            if view_mode["current"] == "done":
                # --- Done view: all completed items grouped by sprint ---
                from agile_backlog.pure import parse_sprint_handover

                handover_dir = "docs/sprints"
                # Apply filters to ALL done items (not just recent), then group by sprint
                all_done = [i for i in items if i.status == "done"]
                all_done = filter_items(all_done, search=sq)
                if pf_list:
                    all_done = [i for i in all_done if i.priority in pf_list]
                if cf_list:
                    all_done = [i for i in all_done if i.category in cf_list]
                if resolved_sprints:
                    all_done = [i for i in all_done if _sprint_match(i.sprint_target)]
                if tf_list:
                    all_done = [i for i in all_done if tf_set & set(i.tags)]
                sprint_groups = group_done_by_sprint(all_done)

                done_panel_state: dict[str, str | None] = {"selected_id": None}
                done_list_ref: dict[str, object] = {"el": None}
                done_panel_ref: dict[str, object] = {"el": None}

                def _reselect_done_panel(item_id: str):
                    try:
                        reloaded = load_item(item_id)
                        _open_done_panel(reloaded)
                    except FileNotFoundError:
                        pass

                def _open_done_panel(item: BacklogItem):
                    done_panel_state["selected_id"] = item.id
                    if done_list_ref["el"]:
                        done_list_ref["el"].style("flex:6;min-width:0;overflow:auto;")
                    if done_panel_ref["el"]:
                        done_panel_ref["el"].style("flex:4;min-width:320px;display:block;")
                        done_panel_ref["el"].clear()
                        with done_panel_ref["el"]:
                            _render_side_panel_content(
                                item,
                                save_item,
                                render_board.refresh,
                                _close_done_panel,
                                all_items=items,
                                reselect_fn=_reselect_done_panel,
                            )

                def _close_done_panel():
                    done_panel_state["selected_id"] = None
                    if done_list_ref["el"]:
                        done_list_ref["el"].style("flex:1;min-width:0;overflow:auto;")
                    if done_panel_ref["el"]:
                        done_panel_ref["el"].style("display:none;")
                        done_panel_ref["el"].clear()

                ui.keyboard(
                    on_key=lambda e: _close_done_panel() if e.key == "Escape" and not e.action.repeat else None,
                )

                with ui.element("div").style("display:flex;gap:0;height:100%;"):
                    done_list = ui.element("div").style("flex:1;min-width:0;overflow:auto;")
                    done_list_ref["el"] = done_list
                    with done_list:
                        if not sprint_groups:
                            ui.html(
                                '<div style="font-size:12px;color:#a1a1aa;padding:24px 10px;'
                                "font-style:italic;font-family:'DM Sans',sans-serif;"
                                'text-align:center;">No completed items yet</div>'
                            )
                        else:
                            for sprint_num, sprint_items in sprint_groups.items():
                                header = f"Sprint {sprint_num}" if sprint_num is not None else "Unplanned"
                                meta = (
                                    parse_sprint_handover(handover_dir, sprint_num) if sprint_num is not None else None
                                )
                                subtitle = ""
                                if meta:
                                    parts = []
                                    if meta.get("theme"):
                                        parts.append(meta["theme"])
                                    if meta.get("date"):
                                        parts.append(meta["date"])
                                    if meta.get("tests"):
                                        parts.append(f"{meta['tests']} tests")
                                    if meta.get("commits"):
                                        parts.append(f"{meta['commits']} commits")
                                    subtitle = " · ".join(parts)
                                with (
                                    ui.expansion(f"{header} ({len(sprint_items)})", value=bool(sq))
                                    .classes("mc-done-section")
                                    .style("width:100%;margin-bottom:4px;")
                                ):
                                    if subtitle:
                                        ui.html(
                                            f'<div style="font-size:10px;color:#71717a;padding:2px 0 6px;'
                                            f"font-family:'IBM Plex Mono',monospace;\">"
                                            f"{safe_html(subtitle)}</div>"
                                        )
                                    # Context report summary for this sprint
                                    if sprint_num is not None:
                                        import json as _json
                                        from pathlib import Path as _Path

                                        _rpt_path = _Path(handover_dir) / f"SPRINT{sprint_num}_CONTEXT_REPORT.json"
                                        if _rpt_path.exists():
                                            try:
                                                _rpt = _json.loads(_rpt_path.read_text())
                                                _tc = _rpt.get("tool_usage", {}).get("total_tool_calls", 0)
                                                _rr = round(_rpt.get("reread_ratio", 0) * 100, 1)
                                                _tk = _rpt.get("estimated_tokens", 0)
                                                _tk_d = f"{_tk // 1000}k" if _tk >= 1000 else str(_tk)
                                                _sess = len(_rpt.get("sessions", []))
                                                _rr_c = "#22c55e" if _rr < 15 else "#ca8a04" if _rr < 30 else "#f87171"
                                                ui.html(
                                                    f"<div style='display:flex;gap:16px;padding:6px 8px;"
                                                    f"margin:2px 0 8px;background:#1e1e23;border-radius:6px;"
                                                    f"border:1px solid #27272a;font-size:10px;"
                                                    f'font-family:"IBM Plex Mono",monospace;\'>'
                                                    f"<span style='color:#71717a;'>Sessions: "
                                                    f"<b style='color:#d4d4d8;'>{_sess}</b></span>"
                                                    f"<span style='color:#71717a;'>Tool calls: "
                                                    f"<b style='color:#d4d4d8;'>{_tc}</b></span>"
                                                    f"<span style='color:#71717a;'>Re-read: "
                                                    f"<b style='color:{_rr_c};'>{_rr}%</b></span>"
                                                    f"<span style='color:#71717a;'>Tokens: "
                                                    f"<b style='color:#d4d4d8;'>{safe_html(_tk_d)}</b></span>"
                                                    f"</div>"
                                                )
                                            except Exception:
                                                pass
                                    for card_item in sprint_items:
                                        _render_card(
                                            card_item,
                                            "done",
                                            move_item,
                                            save_item,
                                            render_board.refresh,
                                            on_card_click=_open_done_panel,
                                        )

                    done_panel = ui.element("div").style("display:none;")
                    done_panel_ref["el"] = done_panel
            elif view_mode["current"] == "context":
                # --- Context analysis dashboard ---
                from agile_backlog.config import (
                    get_context_logs_dir,
                )
                from agile_backlog.config import (
                    get_current_sprint as _get_sprint,
                )
                from agile_backlog.context_report import (
                    analyze_efficiency,
                    analyze_reads,
                    analyze_tool_usage,
                    parse_read_log,
                )

                sprint_num = _get_sprint() or current_sprint or "?"
                log_dir = get_context_logs_dir()
                all_entries: list[dict] = []
                session_data: list[tuple[str, list[dict]]] = []
                if log_dir.exists():
                    for log_file in sorted(log_dir.glob("tools-*.jsonl")):
                        entries = parse_read_log(log_file)
                        if entries:
                            session_data.append((log_file.stem.replace("tools-", ""), entries))
                            all_entries.extend(entries)
                    for log_file in sorted(log_dir.glob("reads-*.jsonl")):
                        entries = parse_read_log(log_file)
                        if entries:
                            session_data.append((log_file.stem.replace("reads-", ""), entries))
                            all_entries.extend(entries)

                ui.html(
                    f'<div style="font-size:16px;font-weight:700;color:#fafafa;padding:8px 0 16px;'
                    f"font-family:'DM Sans',sans-serif;\">"
                    f"Context Analysis &mdash; Sprint {safe_html(str(sprint_num))}</div>"
                )

                if not all_entries:
                    ui.html(
                        '<div style="font-size:12px;color:#a1a1aa;padding:24px 10px;'
                        "font-style:italic;font-family:'DM Sans',sans-serif;"
                        'text-align:center;">No context logs found. '
                        "Run Claude Code sessions with context hooks enabled to generate data.</div>"
                    )
                else:
                    reads = analyze_reads(all_entries)
                    tools = analyze_tool_usage(all_entries)

                    # Summary cards row
                    card_style = (
                        "background:#1e1e23;border:1px solid #27272a;border-radius:8px;"
                        "padding:16px 20px;flex:1;min-width:140px;"
                    )
                    label_style = (
                        "font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:500;"
                        "color:#71717a;text-transform:uppercase;letter-spacing:0.05em;"
                    )
                    value_style = "font-size:24px;font-weight:700;color:#fafafa;margin-top:4px;"
                    with ui.element("div").style("display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;"):
                        with ui.element("div").style(card_style):
                            ui.html(f'<div style="{label_style}">Total Tool Calls</div>')
                            ui.html(f'<div style="{value_style}">{safe_html(str(tools["total_tool_calls"]))}</div>')
                        with ui.element("div").style(card_style):
                            ui.html(f'<div style="{label_style}">Read Calls</div>')
                            ui.html(f'<div style="{value_style}">{safe_html(str(reads["total_reads"]))}</div>')
                        with ui.element("div").style(card_style):
                            reread_pct = round(reads["reread_ratio"] * 100, 1)
                            color = "#22c55e" if reread_pct < 15 else "#ca8a04" if reread_pct < 30 else "#f87171"
                            ui.html(f'<div style="{label_style}">Re-read Ratio</div>')
                            ui.html(f'<div style="{value_style}color:{color};">{safe_html(str(reread_pct))}%</div>')
                        with ui.element("div").style(card_style):
                            tokens = reads["estimated_tokens"]
                            token_display = f"{tokens // 1000}k" if tokens >= 1000 else str(tokens)
                            ui.html(f'<div style="{label_style}">Est. Tokens</div>')
                            ui.html(f'<div style="{value_style}">{safe_html(token_display)}</div>')

                    # Tool usage breakdown with drilldown
                    ui.html(
                        '<div style="font-size:13px;font-weight:600;color:#e4e4e7;margin:16px 0 8px;'
                        "font-family:'DM Sans',sans-serif;\">Tool Usage Breakdown</div>"
                    )
                    by_tool = tools.get("by_tool", {})
                    if by_tool:
                        max_count = max(by_tool.values()) if by_tool else 1
                        # Group entries by tool for drilldown
                        from collections import Counter as _Counter

                        tool_details: dict[str, list[str]] = {}
                        for _e in all_entries:
                            _t = _e.get("tool", "")
                            if _t == "Bash":
                                tool_details.setdefault(_t, []).append(_e.get("command", "?")[:80])
                            elif _t == "Read":
                                _f = _e.get("file", "?")
                                tool_details.setdefault(_t, []).append(_f.split("/")[-1] if "/" in _f else _f)
                            elif _t == "Grep":
                                tool_details.setdefault(_t, []).append(_e.get("pattern", "?"))
                            elif _t == "Edit":
                                _f = _e.get("file", "?")
                                tool_details.setdefault(_t, []).append(_f.split("/")[-1] if "/" in _f else _f)
                            elif _t == "Write":
                                _f = _e.get("file", "?")
                                tool_details.setdefault(_t, []).append(_f.split("/")[-1] if "/" in _f else _f)
                            elif _t == "Skill":
                                tool_details.setdefault(_t, []).append(_e.get("skill", "?"))
                            elif _t == "Agent":
                                tool_details.setdefault(_t, []).append(_e.get("prompt", "?")[:60])

                        with ui.element("div").style(
                            "background:#1e1e23;border:1px solid #27272a;border-radius:8px;overflow:hidden;"
                        ):
                            for tool_name, count in sorted(by_tool.items(), key=lambda x: -x[1]):
                                bar_width = int((count / max_count) * 100)
                                bar_html = (
                                    f"<div style='display:flex;align-items:center;gap:10px;width:100%;'>"
                                    f"<span style='color:#d4d4d8;font-size:12px;min-width:60px;"
                                    f'font-family:"IBM Plex Mono",monospace;\'>{safe_html(tool_name)}</span>'
                                    f"<span style='color:#a1a1aa;font-size:12px;min-width:40px;text-align:right;"
                                    f'font-family:"IBM Plex Mono",monospace;\'>{count}</span>'
                                    f"<div style='flex:1;'>"
                                    f"<div style='background:rgba(59,130,246,0.25);height:14px;"
                                    f"border-radius:3px;width:{bar_width}%;'></div></div></div>"
                                )
                                details = tool_details.get(tool_name, [])
                                if details:
                                    top_items = _Counter(details).most_common(10)
                                    with ui.expansion("").style("width:100%;border-bottom:1px solid #27272a;margin:0;"):
                                        ui.html(bar_html).style("padding:0;")
                                        for val, cnt in top_items:
                                            pct = round(cnt / count * 100)
                                            ui.html(
                                                f"<div style='display:flex;gap:8px;padding:2px 8px 2px 70px;"
                                                f'font-size:10px;font-family:"IBM Plex Mono",monospace;\'>'
                                                f"<span style='color:#71717a;min-width:30px;text-align:right;'>"
                                                f"{cnt}x</span>"
                                                f"<span style='color:#71717a;min-width:30px;'>({pct}%)</span>"
                                                f"<span style='color:#a1a1aa;overflow:hidden;text-overflow:ellipsis;"
                                                f"white-space:nowrap;'>{safe_html(val)}</span></div>"
                                            )
                                else:
                                    with ui.element("div").style("padding:8px 10px;border-bottom:1px solid #27272a;"):
                                        ui.html(bar_html)

                    # Top files heatmap
                    ui.html(
                        '<div style="font-size:13px;font-weight:600;color:#e4e4e7;margin:20px 0 8px;'
                        "font-family:'DM Sans',sans-serif;\">Top Files (by read count)</div>"
                    )
                    top_files = reads.get("top_files", [])
                    if top_files:
                        file_rows = ""
                        max_file_count = top_files[0]["count"] if top_files else 1
                        for tf in top_files:
                            intensity = min(tf["count"] / max_file_count, 1.0)
                            r = int(59 + intensity * (248 - 59))
                            g = int(130 + intensity * (113 - 130))
                            b = int(246 + intensity * (113 - 246))
                            bg = f"rgba({r},{g},{b},0.12)"
                            fname = tf["file"]
                            short = fname.split("/")[-1] if "/" in fname else fname
                            file_rows += (
                                f"<tr><td style='padding:5px 10px;color:#93c5fd;font-size:11px;"
                                f'font-family:"IBM Plex Mono",monospace;border-bottom:1px solid #27272a;'
                                f"background:{bg};' title='{safe_html(fname)}'>"
                                f"{safe_html(short)}</td>"
                                f"<td style='padding:5px 10px;color:#d4d4d8;font-size:11px;text-align:center;"
                                f'font-family:"IBM Plex Mono",monospace;border-bottom:1px solid #27272a;'
                                f"background:{bg};white-space:nowrap;'>"
                                f"{safe_html(str(tf['count']))}</td>"
                                f"<td style='padding:5px 10px;color:#71717a;font-size:10px;"
                                f"border-bottom:1px solid #27272a;background:{bg};max-width:300px;"
                                f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>"
                                f"{safe_html(fname)}</td></tr>"
                            )
                        ui.html(
                            f"<table style='width:100%;border-collapse:collapse;background:#1e1e23;"
                            f"border:1px solid #27272a;border-radius:8px;overflow:hidden;'>"
                            f"<thead><tr><th style='padding:6px 10px;text-align:left;color:#71717a;"
                            f"font-size:10px;text-transform:uppercase;letter-spacing:0.05em;"
                            f'font-family:"IBM Plex Mono",monospace;border-bottom:1px solid #27272a;\'>'
                            f"File</th><th style='padding:6px 10px;text-align:center;color:#71717a;"
                            f"font-size:10px;text-transform:uppercase;letter-spacing:0.05em;"
                            f'font-family:"IBM Plex Mono",monospace;border-bottom:1px solid #27272a;\'>'
                            f"Reads</th><th style='padding:6px 10px;text-align:left;color:#71717a;"
                            f"font-size:10px;text-transform:uppercase;letter-spacing:0.05em;"
                            f'font-family:"IBM Plex Mono",monospace;border-bottom:1px solid #27272a;\'>'
                            f"Path</th></tr></thead><tbody>{file_rows}</tbody></table>"
                        )

                    # Per-session breakdown
                    if session_data:
                        ui.html(
                            '<div style="font-size:13px;font-weight:600;color:#e4e4e7;margin:20px 0 8px;'
                            "font-family:'DM Sans',sans-serif;\">Sessions</div>"
                        )
                        for sess_id, sess_entries in session_data:
                            s_reads = analyze_reads(sess_entries)
                            s_tools = analyze_tool_usage(sess_entries)
                            s_eff = analyze_efficiency(sess_entries)
                            s_reread = round(s_reads["reread_ratio"] * 100, 1)
                            s_tokens = s_reads["estimated_tokens"]
                            s_token_display = f"{s_tokens // 1000}k" if s_tokens >= 1000 else str(s_tokens)
                            summary = (
                                f"{safe_html(str(s_tools['total_tool_calls']))} calls &middot; "
                                f"{safe_html(str(s_reads['total_reads']))} reads &middot; "
                                f"{safe_html(str(s_reread))}% re-read &middot; "
                                f"{safe_html(s_token_display)} tokens"
                            )
                            with ui.expansion(safe_html(sess_id)).style(
                                "width:100%;margin-bottom:4px;background:#1e1e23;"
                                "border:1px solid #27272a;border-radius:6px;"
                            ):
                                ui.html(
                                    f"<div style='font-size:11px;color:#a1a1aa;"
                                    f'font-family:"IBM Plex Mono",monospace;'
                                    f"padding:4px 0;'>{summary}</div>"
                                )
                                if s_eff["exact_reread_count"] > 0:
                                    ui.html(
                                        f"<div style='font-size:10px;color:#f87171;padding:2px 0;'>"
                                        f"Exact re-reads: "
                                        f"{safe_html(str(s_eff['exact_reread_count']))}</div>"
                                    )
                                if s_reads.get("wasteful_reads"):
                                    for w in s_reads["wasteful_reads"]:
                                        ui.html(
                                            f"<div style='font-size:10px;color:#ca8a04;padding:1px 0;'>"
                                            f"Wasteful: {safe_html(w['file'])} "
                                            f"({safe_html(str(w['count']))}x)</div>"
                                        )

            elif view_mode["current"] == "process":
                # --- Process management tools review ---
                import json as _json
                import re as _re
                from pathlib import Path as _Path

                import yaml as _yaml

                from agile_backlog.config import get_context_logs_dir as _get_ctx_dir
                from agile_backlog.context_report import parse_read_log as _parse_log
                from agile_backlog.context_report import skill_usage_stats as _skill_stats
                from agile_backlog.yaml_store import _git_root

                git_root = _git_root()

                ui.html(
                    '<div style="font-size:16px;font-weight:700;color:#fafafa;padding:8px 0 12px;'
                    "font-family:'DM Sans',sans-serif;\">Process Management Tools</div>"
                )

                tab_bar_style = "background:#1e1e23;color:#8b8b9b;"
                tab_panel_style = "background:#14141a;padding:16px;"

                with ui.tabs().classes("w-full").style(tab_bar_style) as proc_tabs:
                    skills_tab = ui.tab("Skills")
                    claude_md_tab = ui.tab("CLAUDE.md")
                    handovers_tab = ui.tab("Handovers")
                    hooks_tab = ui.tab("Hooks")
                    permissions_tab = ui.tab("Permissions")

                with ui.tab_panels(proc_tabs, value=skills_tab).classes("w-full").style(tab_panel_style):
                    # --- Skills Tab ---
                    with ui.tab_panel(skills_tab):
                        from pathlib import Path as _SkPath

                        skills_found: list[dict] = []

                        def _scan_skills(base_dir: _SkPath, source: str):
                            if not base_dir.is_dir():
                                return
                            for skill_dir in sorted(base_dir.iterdir()):
                                skill_md = skill_dir / "SKILL.md"
                                if skill_dir.is_dir() and skill_md.exists():
                                    content = skill_md.read_text()
                                    fm_match = _re.match(r"^---\s*\n(.*?)\n---", content, _re.DOTALL)
                                    name = skill_dir.name
                                    desc = ""
                                    if fm_match:
                                        try:
                                            fm = _yaml.safe_load(fm_match.group(1)) or {}
                                            name = fm.get("name", name)
                                            desc = fm.get("description", "")
                                        except Exception:
                                            pass
                                    skills_found.append({"name": name, "description": desc, "source": source})

                        # Project skills
                        _scan_skills(git_root / ".claude" / "skills", "project")
                        # Personal skills
                        _scan_skills(_SkPath.home() / ".claude" / "skills", "personal")
                        # Plugin skills
                        plugins_cache = _SkPath.home() / ".claude" / "plugins" / "cache"
                        if plugins_cache.is_dir():
                            # Structure: cache/vendor/plugin/version/skills/
                            for vendor_dir in sorted(plugins_cache.iterdir()):
                                if not vendor_dir.is_dir():
                                    continue
                                for plugin_dir in sorted(vendor_dir.iterdir()):
                                    if not plugin_dir.is_dir():
                                        continue
                                    for version_dir in plugin_dir.iterdir():
                                        if version_dir.is_dir():
                                            _scan_skills(
                                                version_dir / "skills",
                                                f"plugin:{plugin_dir.name}",
                                            )

                        # Load skill usage stats from context logs
                        ctx_log_dir = _get_ctx_dir()
                        all_ctx_entries: list[dict] = []
                        if ctx_log_dir.exists():
                            for lf in sorted(ctx_log_dir.glob("tools-*.jsonl")):
                                all_ctx_entries.extend(_parse_log(lf))
                        skill_counts = _skill_stats(all_ctx_entries)

                        ui.html(
                            f'<div style="font-size:11px;color:#71717a;padding:4px 0 8px;">'
                            f"Found {len(skills_found)} skills "
                            f"(project, personal, plugins)</div>"
                        )
                        if not skills_found:
                            ui.html(
                                '<div style="font-size:12px;color:#a1a1aa;padding:16px;font-style:italic;">'
                                "No skills found</div>"
                            )
                        else:
                            _th = (
                                "padding:8px 12px;text-align:left;color:#71717a;font-size:10px;"
                                "text-transform:uppercase;letter-spacing:0.05em;border-bottom:1px solid #27272a;"
                            )
                            rows_html = ""
                            for sk in skills_found:
                                usage = skill_counts.get(sk["name"], 0)
                                src = sk.get("source", "")
                                src_color = (
                                    "#3b82f6" if src == "project" else "#a78bfa" if src == "personal" else "#71717a"
                                )
                                # Truncate long descriptions
                                desc = sk["description"]
                                if len(desc) > 120:
                                    desc = desc[:117] + "..."
                                rows_html += (
                                    f"<tr><td style='padding:6px 12px;color:#e4e4e7;font-size:12px;"
                                    f"font-weight:600;border-bottom:1px solid #27272a;white-space:nowrap;'>"
                                    f"{safe_html(sk['name'])}</td>"
                                    f"<td style='padding:6px 8px;color:{src_color};font-size:10px;"
                                    f"border-bottom:1px solid #27272a;white-space:nowrap;"
                                    f'font-family:"IBM Plex Mono",monospace;\'>'
                                    f"{safe_html(src)}</td>"
                                    f"<td style='padding:6px 12px;color:#a1a1aa;font-size:11px;"
                                    f"border-bottom:1px solid #27272a;'>"
                                    f"{safe_html(desc)}</td>"
                                    f"<td style='padding:6px 12px;color:#71717a;font-size:11px;"
                                    f"text-align:center;border-bottom:1px solid #27272a;"
                                    f'font-family:"IBM Plex Mono",monospace;\'>'
                                    f"{safe_html(str(usage))}</td></tr>"
                                )
                            ui.html(
                                f"<table style='width:100%;border-collapse:collapse;background:#1e1e23;"
                                f"border:1px solid #27272a;border-radius:8px;overflow:hidden;'>"
                                f"<thead><tr>"
                                f"<th style='{_th}'>Skill</th>"
                                f"<th style='{_th}'>Source</th>"
                                f"<th style='{_th}'>Description</th>"
                                f"<th style='{_th}text-align:center;'>Usage</th>"
                                f"</tr></thead><tbody>{rows_html}</tbody></table>"
                            )

                    # --- CLAUDE.md Tab ---
                    with ui.tab_panel(claude_md_tab):
                        claude_md_path = git_root / "CLAUDE.md"
                        if claude_md_path.exists():
                            claude_content = claude_md_path.read_text()
                            file_size = claude_md_path.stat().st_size
                            approx_tokens = len(claude_content) // 4
                            ui.html(
                                f'<div style="display:flex;gap:16px;margin-bottom:12px;">'
                                f'<span style="font-size:11px;color:#71717a;">'
                                f"Size: {safe_html(str(file_size))} bytes</span>"
                                f'<span style="font-size:11px;color:#71717a;">'
                                f"~{safe_html(str(approx_tokens))} tokens</span>"
                                f"</div>"
                            )
                            ui.html(
                                '<div style="font-size:10px;color:#ca8a04;background:rgba(202,138,4,0.08);'
                                'padding:8px 12px;border-radius:6px;margin-bottom:12px;">'
                                "Guideline: Keep CLAUDE.md under ~2K tokens for optimal prompt budget.</div>"
                            )
                            ui.html(
                                f'<pre style="background:#1e1e23;border:1px solid #27272a;border-radius:8px;'
                                f"padding:16px;color:#d4d4d8;font-size:11px;overflow-x:auto;"
                                f'font-family:&quot;IBM Plex Mono&quot;,monospace;white-space:pre-wrap;">'
                                f"{safe_html(claude_content)}</pre>"
                            )
                        else:
                            ui.html(
                                '<div style="font-size:12px;color:#a1a1aa;padding:16px;font-style:italic;">'
                                "No CLAUDE.md found at project root.</div>"
                            )

                    # --- Handovers Tab ---
                    with ui.tab_panel(handovers_tab):
                        handover_dir = git_root / "docs" / "sprints"
                        handover_files: list[tuple[int, _Path]] = []
                        if handover_dir.is_dir():
                            for hf in handover_dir.glob("SPRINT*_HANDOVER.md"):
                                m = _re.search(r"SPRINT(\d+)_HANDOVER\.md$", hf.name)
                                if m:
                                    handover_files.append((int(m.group(1)), hf))
                        handover_files.sort(key=lambda x: x[0], reverse=True)

                        if not handover_files:
                            ui.html(
                                '<div style="font-size:12px;color:#a1a1aa;padding:16px;font-style:italic;">'
                                "No handover files found in docs/sprints/</div>"
                            )
                        else:
                            for sprint_num, hf_path in handover_files:
                                hf_content = hf_path.read_text()
                                with ui.expansion(f"Sprint {sprint_num} Handover").style(
                                    "width:100%;margin-bottom:4px;background:#1e1e23;"
                                    "border:1px solid #27272a;border-radius:6px;"
                                ):
                                    ui.html(
                                        f'<pre style="color:#d4d4d8;font-size:11px;overflow-x:auto;'
                                        f'font-family:&quot;IBM Plex Mono&quot;,monospace;white-space:pre-wrap;">'
                                        f"{safe_html(hf_content)}</pre>"
                                    )

                    # --- Hooks Tab ---
                    with ui.tab_panel(hooks_tab):
                        settings_path = git_root / ".claude" / "settings.json"
                        if settings_path.exists():
                            try:
                                settings_data = _json.loads(settings_path.read_text())
                                hooks = settings_data.get("hooks", {})
                                if not hooks:
                                    ui.html(
                                        '<div style="font-size:12px;color:#a1a1aa;padding:16px;'
                                        'font-style:italic;">No hooks configured in settings.json</div>'
                                    )
                                else:
                                    total_hooks = 0
                                    for event_type, hook_list in hooks.items():
                                        if not isinstance(hook_list, list):
                                            continue
                                        total_hooks += len(hook_list)
                                    ui.html(
                                        f'<div style="font-size:12px;color:#a1a1aa;margin-bottom:12px;">'
                                        f"Total hooks: <strong style='color:#fafafa;'>"
                                        f"{safe_html(str(total_hooks))}</strong></div>"
                                    )
                                    for event_type, hook_list in hooks.items():
                                        if not isinstance(hook_list, list):
                                            continue
                                        ui.html(
                                            f'<div style="font-size:13px;font-weight:600;color:#e4e4e7;'
                                            f"margin:12px 0 6px;font-family:'DM Sans',sans-serif;\">"
                                            f"{safe_html(event_type)} "
                                            f"<span style='color:#71717a;font-weight:400;font-size:11px;'>"
                                            f"({safe_html(str(len(hook_list)))})</span></div>"
                                        )
                                        for hook in hook_list:
                                            matcher = hook.get("matcher", "")
                                            command = hook.get("command", "")
                                            ui.html(
                                                f'<div style="background:#1e1e23;border:1px solid #27272a;'
                                                f'border-radius:6px;padding:10px 14px;margin-bottom:4px;">'
                                                f'<div style="font-size:10px;color:#71717a;">matcher</div>'
                                                f'<div style="font-size:12px;color:#d4d4d8;'
                                                f'font-family:&quot;IBM Plex Mono&quot;,monospace;">'
                                                f"{safe_html(str(matcher))}</div>"
                                                f'<div style="font-size:10px;color:#71717a;margin-top:6px;">'
                                                f"command</div>"
                                                f'<div style="font-size:11px;color:#a1a1aa;'
                                                f"font-family:&quot;IBM Plex Mono&quot;,monospace;"
                                                f'word-break:break-all;">{safe_html(str(command))}</div>'
                                                f"</div>"
                                            )
                            except (ValueError, KeyError):
                                ui.html(
                                    '<div style="font-size:12px;color:#f87171;padding:16px;">'
                                    "Error reading settings.json</div>"
                                )
                        else:
                            ui.html(
                                '<div style="font-size:12px;color:#a1a1aa;padding:16px;font-style:italic;">'
                                "No .claude/settings.json found.</div>"
                            )

                    # --- Permissions Tab ---
                    with ui.tab_panel(permissions_tab):
                        local_settings_path = git_root / ".claude" / "settings.local.json"
                        if local_settings_path.exists():
                            try:
                                local_data = _json.loads(local_settings_path.read_text())
                                allow_list = local_data.get("permissions", {}).get("allow", [])
                                if not allow_list:
                                    ui.html(
                                        '<div style="font-size:12px;color:#a1a1aa;padding:16px;'
                                        'font-style:italic;">No permissions configured.</div>'
                                    )
                                else:
                                    # Group by category
                                    categories: dict[str, list[str]] = {}
                                    for perm in allow_list:
                                        p = str(perm)
                                        if p.startswith("Bash(git"):
                                            cat = "git"
                                        elif "pytest" in p or "test" in p.lower():
                                            cat = "test"
                                        elif "ruff" in p or "lint" in p.lower():
                                            cat = "lint"
                                        elif "agile-backlog" in p:
                                            cat = "CLI tool"
                                        elif "python" in p or ".venv/bin/python" in p:
                                            cat = "python"
                                        elif "http" in p or "serve" in p or "browser" in p:
                                            cat = "web"
                                        else:
                                            cat = "other"
                                        categories.setdefault(cat, []).append(p)

                                    ui.html(
                                        f'<div style="font-size:12px;color:#a1a1aa;margin-bottom:12px;">'
                                        f"Total permissions: <strong style='color:#fafafa;'>"
                                        f"{safe_html(str(len(allow_list)))}</strong></div>"
                                    )

                                    cat_rows = ""
                                    for cat_name in sorted(categories.keys()):
                                        cat_items = categories[cat_name]
                                        cat_rows += (
                                            f"<tr><td style='padding:6px 12px;color:#e4e4e7;font-size:12px;"
                                            f"font-weight:600;border-bottom:1px solid #27272a;'>"
                                            f"{safe_html(cat_name)}</td>"
                                            f"<td style='padding:6px 12px;color:#a1a1aa;font-size:12px;"
                                            f"text-align:center;border-bottom:1px solid #27272a;"
                                            f'font-family:"IBM Plex Mono",monospace;\'>'
                                            f"{safe_html(str(len(cat_items)))}</td></tr>"
                                        )
                                    ui.html(
                                        f"<table style='width:100%;border-collapse:collapse;background:#1e1e23;"
                                        f"border:1px solid #27272a;border-radius:8px;overflow:hidden;"
                                        f"margin-bottom:12px;'>"
                                        f"<thead><tr>"
                                        f"<th style='padding:6px 12px;text-align:left;color:#71717a;"
                                        f"font-size:10px;text-transform:uppercase;letter-spacing:0.05em;"
                                        f"border-bottom:1px solid #27272a;'>Category</th>"
                                        f"<th style='padding:6px 12px;text-align:center;color:#71717a;"
                                        f"font-size:10px;text-transform:uppercase;letter-spacing:0.05em;"
                                        f"border-bottom:1px solid #27272a;'>Count</th>"
                                        f"</tr></thead><tbody>{cat_rows}</tbody></table>"
                                    )

                                    with ui.expansion("Full Permission List").style(
                                        "width:100%;background:#1e1e23;border:1px solid #27272a;border-radius:6px;"
                                    ):
                                        perm_items = "".join(
                                            f'<div style="font-size:11px;color:#d4d4d8;padding:3px 0;'
                                            f'font-family:&quot;IBM Plex Mono&quot;,monospace;">'
                                            f"{safe_html(str(p))}</div>"
                                            for p in allow_list
                                        )
                                        ui.html(perm_items)
                            except (ValueError, KeyError):
                                ui.html(
                                    '<div style="font-size:12px;color:#f87171;padding:16px;">'
                                    "Error reading settings.local.json</div>"
                                )
                        else:
                            ui.html(
                                '<div style="font-size:12px;color:#a1a1aa;padding:16px;font-style:italic;">'
                                "No .claude/settings.local.json found.</div>"
                            )

            elif view_mode["current"] == "backlog":
                # --- Backlog management view ---
                _render_backlog_list(
                    items,
                    current_sprint,
                    move_item,
                    save_item,
                    render_board.refresh,
                    priorities=pf_list or None,
                    categories=cf_list or None,
                    tags=tf_list or None,
                    search=sq,
                )
            else:
                # --- Kanban board view with side panel ---
                board_panel_state = {"selected_id": None}
                board_list_ref: dict[str, object] = {"el": None}
                board_panel_ref: dict[str, object] = {"el": None}

                def _reselect_board_panel(item_id: str):
                    try:
                        reloaded = load_item(item_id)
                        _open_board_panel(reloaded)
                    except FileNotFoundError:
                        pass

                def _open_board_panel(item: BacklogItem):
                    board_panel_state["selected_id"] = item.id
                    if board_list_ref["el"]:
                        board_list_ref["el"].style(
                            "flex:6;min-width:0;display:flex;gap:10px;align-items:flex-start;height:100%;"
                        )
                    if board_panel_ref["el"]:
                        board_panel_ref["el"].style("flex:4;min-width:320px;display:block;")
                        board_panel_ref["el"].clear()
                        with board_panel_ref["el"]:
                            _render_side_panel_content(
                                item,
                                save_item,
                                render_board.refresh,
                                _close_board_panel,
                                all_items=items,
                                reselect_fn=_reselect_board_panel,
                            )

                def _close_board_panel():
                    board_panel_state["selected_id"] = None
                    if board_list_ref["el"]:
                        board_list_ref["el"].style(
                            "flex:1;min-width:0;display:flex;gap:10px;align-items:flex-start;height:100%;"
                        )
                    if board_panel_ref["el"]:
                        board_panel_ref["el"].style("display:none;")
                        board_panel_ref["el"].clear()

                ui.keyboard(
                    on_key=lambda e: _close_board_panel() if e.key == "Escape" and not e.action.repeat else None,
                )

                with ui.element("div").style("display:flex;gap:0;height:100%;"):
                    # Left: board columns
                    board_columns = ui.element("div").style(
                        "flex:1;min-width:0;display:flex;gap:10px;align-items:flex-start;height:100%;"
                    )
                    board_list_ref["el"] = board_columns

                    # Hidden drop trigger for board drag-and-drop
                    board_drop_trigger = ui.element("div").props('id="mc-board-drop-trigger"').style("display:none;")

                    async def _handle_board_drop(_e):
                        detail = await ui.run_javascript("window._lastBoardDrop || null")
                        if not detail:
                            return
                        item_id = detail.get("item_id")
                        target_status = detail.get("target_status")
                        if item_id and target_status:
                            item = next((i for i in items if i.id == item_id), None)
                            if item:
                                move_item(item, target_status)

                    board_drop_trigger.on("click", _handle_board_drop)

                    with board_columns:
                        for col_status in STATUSES:
                            items_in_col = columns_map[col_status]
                            col_style, label_color = COLUMN_STYLES[col_status]

                            with (
                                ui.element("div")
                                .classes("mc-board-drop-zone")
                                .style(f"flex:1;min-width:0;overflow-y:auto;{col_style}")
                                .props(f'data-target-status="{col_status}"')
                            ):
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
                                    elif col_status == "done" and not show_archived:
                                        msg = (
                                            "No recent done items. Toggle \u2018Show archived\u2019 to see older items."
                                        )
                                    else:
                                        msg = "No items."
                                    ui.html(
                                        f'<div style="font-size:11px;color:#a1a1aa;padding:12px 10px;'
                                        f"font-style:italic;font-family:'DM Sans',sans-serif;"
                                        f"background:rgba(63,63,70,0.15);border-radius:4px;"
                                        f'margin:4px 0;">{msg}</div>'
                                    )
                                    continue

                                for card_item in items_in_col:
                                    _render_card(
                                        card_item,
                                        col_status,
                                        move_item,
                                        save_item,
                                        render_board.refresh,
                                        on_card_click=_open_board_panel,
                                    )

                    # Inject board drag-and-drop JS
                    _board_dnd_js = """
document.querySelectorAll('.mc-board-card[draggable]').forEach(card => {
    card.addEventListener('dragstart', function(e) {
        e.dataTransfer.setData('text/plain', card.getAttribute('data-item-id'));
        e.dataTransfer.effectAllowed = 'move';
        card.classList.add('mc-dragging');
    });
    card.addEventListener('dragend', function() {
        card.classList.remove('mc-dragging');
        document.querySelectorAll('.mc-drag-over').forEach(el => el.classList.remove('mc-drag-over'));
    });
});
document.querySelectorAll('.mc-board-drop-zone').forEach(zone => {
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
        const targetStatus = zone.getAttribute('data-target-status');
        window._lastBoardDrop = {item_id: itemId, target_status: targetStatus};
        document.getElementById('mc-board-drop-trigger').click();
    });
});
"""
                    ui.timer(0.1, lambda: ui.run_javascript(_board_dnd_js), once=True)

                    # Right: side panel (hidden by default)
                    board_panel = ui.element("div").classes("mc-side-panel").style("display:none;padding:16px;")
                    board_panel_ref["el"] = board_panel

        with main_content:
            priority_select.on_value_change(lambda _: render_board.refresh())
            category_select.on_value_change(lambda _: render_board.refresh())
            sprint_select.on_value_change(lambda _: render_board.refresh())
            phase_select.on_value_change(lambda _: render_board.refresh())
            tag_select.on_value_change(lambda _: render_board.refresh())
            sort_select.on_value_change(lambda _: render_board.refresh())
            search_input.on_value_change(lambda _: render_board.refresh())
            archive_toggle.on_value_change(lambda _: render_board.refresh())

            render_board()

            # Restore view mode from localStorage
            async def _restore_view():
                saved = await ui.run_javascript("localStorage.getItem('ab_view_mode')")
                if saved in ("board", "backlog", "done", "context", "process") and saved != view_mode["current"]:
                    _set_view(saved)

            ui.timer(0.1, _restore_view, once=True)

            # Auto-reload when YAML files change on disk
            last_mtime = {"value": backlog_dir_mtime(get_backlog_dir())}

            def _check_file_changes():
                current_mtime = backlog_dir_mtime(get_backlog_dir())
                if current_mtime > last_mtime["value"]:
                    last_mtime["value"] = current_mtime
                    render_board.refresh()

            ui.timer(2.0, _check_file_changes)


def run_app(host: str = "127.0.0.1", port: int = 8501, reload: bool = False):
    """Start the NiceGUI Kanban board server."""
    ui.run(title="agile-backlog", host=host, port=port, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    run_app()
