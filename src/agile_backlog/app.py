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
    is_recently_done,
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

            # Archive toggle + days config — only visible in Board view
            from agile_backlog.config import get_archive_days as _get_ad
            from agile_backlog.config import set_archive_days as _set_ad

            archive_days_options = {7: "7d", 14: "14d", 30: "30d", 90: "90d"}
            current_ad = _get_ad()

            def _on_archive_days_change(e):
                if e.value is not None:
                    _set_ad(int(e.value))
                    render_board.refresh()

            with ui.element("div").style("display:flex;align-items:center;gap:6px;"):
                archive_toggle = (
                    ui.checkbox("Show archived", value=False)
                    .classes("mc-done-check")
                    .style("font-size:12px;color:#a1a1aa;")
                )
                (
                    ui.select(options=archive_days_options, value=current_ad, on_change=_on_archive_days_change)
                    .props("dense borderless dark")
                    .style(
                        "min-width:55px;max-width:65px;font-size:11px;color:#a1a1aa;"
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
            from agile_backlog.config import get_archive_days

            archive_days = get_archive_days()
            done_items = [
                i for i in items if i.status == "done" and (show_archived or is_recently_done(i, days=archive_days))
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
                if saved in ("board", "backlog", "done") and saved != view_mode["current"]:
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
