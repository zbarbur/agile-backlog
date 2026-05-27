"""Done view — retrospective dashboard with per-sprint summaries and markdown rendering.

Extracted from app.py as the proof-of-pattern slice toward breaking up the giant
kanban_page() function. Preserves the shared-state-dict pattern for stale-closure
safety (Sprint 29 lesson) and safe_html() on all ui.html() calls (Sprint 29 XSS lesson).
"""

from collections.abc import Callable

from nicegui import ui

from agile_backlog.components import _render_card, _render_side_panel_content
from agile_backlog.models import BacklogItem
from agile_backlog.pure import filter_items, group_done_by_sprint, safe_html
from agile_backlog.yaml_store import load_item, save_item


def render_done_view(
    items: list[BacklogItem],
    search_query: str,
    priority_filter: list[str],
    category_filter: list[str],
    tag_filter_list: list[str],
    resolved_sprints: list[int | str],
    sprint_match_fn: Callable[[int | None], bool],
    move_item: Callable[[BacklogItem, str], None],
    refresh_board: Callable[[], None],
) -> None:
    from agile_backlog.pure import parse_sprint_handover

    handover_dir = "docs/sprints"
    # Apply filters to ALL done items (not just recent), then group by sprint
    all_done = [i for i in items if i.status == "done"]
    all_done = filter_items(all_done, search=search_query)
    if priority_filter:
        all_done = [i for i in all_done if i.priority in priority_filter]
    if category_filter:
        all_done = [i for i in all_done if i.category in category_filter]
    if resolved_sprints:
        all_done = [i for i in all_done if sprint_match_fn(i.sprint_target)]
    tf_set = set(tag_filter_list)
    if tag_filter_list:
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
                    refresh_board,
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
                # Cross-sprint comparison dashboard
                from pathlib import Path as _CmpPath

                from agile_backlog.context_report import compare_sprints, load_all_sprint_reports
                from agile_backlog.pure import format_trend_indicator

                _all_reports = load_all_sprint_reports(_CmpPath(handover_dir))
                if len(_all_reports) >= 2:
                    _comparison = compare_sprints(_all_reports)
                    _cmp_sprints = _comparison["sprints"][-5:]  # last 5
                    _trends = _comparison["trends"]

                    _tbl_style = (
                        "width:100%;border-collapse:collapse;font-family:'IBM Plex Mono',monospace;font-size:11px;"
                    )
                    _th_style = (
                        "color:#71717a;font-size:9px;text-transform:uppercase;"
                        "letter-spacing:0.05em;padding:6px 8px;text-align:right;"
                        "border-bottom:1px solid #27272a;"
                    )
                    _td_style = "color:#d4d4d8;padding:4px 8px;text-align:right;border-bottom:1px solid #1e1e23;"

                    _rows_html = ""
                    for _idx, _sd in enumerate(_cmp_sprints):
                        _rr_pct = round(_sd["reread_ratio"] * 100, 1)
                        _rr_clr = "#22c55e" if _rr_pct < 15 else "#ca8a04" if _rr_pct < 30 else "#f87171"
                        _err_pct = round(_sd["error_rate"] * 100, 1)
                        _tk_d = (
                            f"{_sd['estimated_tokens'] // 1000}k"
                            if _sd["estimated_tokens"] >= 1000
                            else str(_sd["estimated_tokens"])
                        )
                        _trend_html = ""
                        if _idx > 0:
                            _prev = _cmp_sprints[_idx - 1]
                            _trend_html = format_trend_indicator(
                                _sd["reread_ratio"], _prev["reread_ratio"], lower_is_better=True
                            )
                        else:
                            _trend_html = "<span style='color:#71717a;'>—</span>"

                        _rows_html += (
                            f"<tr>"
                            f"<td style='{_td_style}text-align:left;'>S{safe_html(str(_sd['sprint']))}</td>"
                            f"<td style='{_td_style}'>{safe_html(str(_sd['total_tool_calls']))}</td>"
                            f"<td style='{_td_style}'>{safe_html(str(_sd['read_calls']))}</td>"
                            f"<td style='{_td_style}color:{_rr_clr};'>{safe_html(str(_rr_pct))}%</td>"
                            f"<td style='{_td_style}'>{safe_html(str(_tk_d))}</td>"
                            f"<td style='{_td_style}'>{safe_html(str(_err_pct))}%</td>"
                            f"<td style='{_td_style}text-align:center;'>{_trend_html}</td>"
                            f"</tr>"
                        )

                    # Trend summary
                    _trend_labels = {
                        "improving": "<span style='color:#22c55e;'>improving ↓</span>",
                        "declining": "<span style='color:#f87171;'>declining ↑</span>",
                        "stable": "<span style='color:#71717a;'>stable →</span>",
                    }
                    _trend_summary = (
                        f"<div style='display:flex;gap:16px;padding:6px 8px;font-size:10px;"
                        f'font-family:"IBM Plex Mono",monospace;color:#71717a;\'>'
                        f"<span>Re-read: {_trend_labels[_trends['reread_ratio']]}</span>"
                        f"<span>Errors: {_trend_labels[_trends['error_rate']]}</span>"
                        f"<span>Tokens: {_trend_labels[_trends['token_usage']]}</span>"
                        f"</div>"
                    )

                    with (
                        ui.expansion("Sprint Trends").classes("mc-done-section").style("width:100%;margin-bottom:8px;")
                    ):
                        ui.html(
                            f"<table style='{_tbl_style}'>"
                            f"<thead><tr>"
                            f"<th style='{_th_style}text-align:left;'>Sprint</th>"
                            f"<th style='{_th_style}'>Tool Calls</th>"
                            f"<th style='{_th_style}'>Reads</th>"
                            f"<th style='{_th_style}'>Re-read %</th>"
                            f"<th style='{_th_style}'>Tokens</th>"
                            f"<th style='{_th_style}'>Errors</th>"
                            f"<th style='{_th_style}text-align:center;'>Trend</th>"
                            f"</tr></thead>"
                            f"<tbody>{_rows_html}</tbody>"
                            f"</table>"
                            f"{_trend_summary}"
                        )

                for sprint_num, sprint_items in sprint_groups.items():
                    header = f"Sprint {sprint_num}" if sprint_num is not None else "Unplanned"
                    meta = parse_sprint_handover(handover_dir, sprint_num) if sprint_num is not None else None
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
                        ui.expansion(f"{header} ({len(sprint_items)})", value=bool(search_query))
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
                                        f"<b style='color:#d4d4d8;'>{safe_html(str(_sess))}</b></span>"
                                        f"<span style='color:#71717a;'>Tool calls: "
                                        f"<b style='color:#d4d4d8;'>{safe_html(str(_tc))}</b></span>"
                                        f"<span style='color:#71717a;'>Re-read: "
                                        f"<b style='color:{_rr_c};'>{safe_html(str(_rr))}%</b></span>"
                                        f"<span style='color:#71717a;'>Tokens: "
                                        f"<b style='color:#d4d4d8;'>{safe_html(_tk_d)}</b></span>"
                                        f"</div>"
                                    )
                                    # Retro Details — tool breakdown and errors
                                    _by_tool = _rpt.get("tool_usage", {}).get("by_tool", {})
                                    if _by_tool:
                                        _sorted_tools = sorted(_by_tool.items(), key=lambda x: -x[1])[:5]
                                        _retro_rows = ""
                                        for _tn, _cnt in _sorted_tools:
                                            _t_pct = round(_cnt / _tc * 100, 1) if _tc else 0
                                            _retro_rows += (
                                                f"<tr><td style='color:#d4d4d8;padding:2px 8px;"
                                                f"font-size:10px;'>{safe_html(_tn)}</td>"
                                                f"<td style='color:#d4d4d8;padding:2px 8px;"
                                                f"font-size:10px;text-align:right;'>{_cnt}</td>"
                                                f"<td style='color:#71717a;padding:2px 8px;"
                                                f"font-size:10px;text-align:right;'>{_t_pct}%</td></tr>"
                                            )
                                        _err_info = _rpt.get("errors", {})
                                        _err_by_tool = _err_info.get("errors_by_tool", {})
                                        _err_html = ""
                                        if _err_by_tool:
                                            _err_items = ", ".join(
                                                f"{safe_html(t)}: {c}"
                                                for t, c in sorted(_err_by_tool.items(), key=lambda x: -x[1])
                                            )
                                            _err_html = (
                                                f"<div style='margin-top:6px;font-size:10px;"
                                                f'color:#f87171;font-family:"IBM Plex Mono",'
                                                f"monospace;'>Errors by tool: {_err_items}</div>"
                                            )
                                        with ui.expansion("Retro Details").style(
                                            "width:100%;margin:2px 0 6px;color:#d4d4d8;"
                                        ):
                                            ui.html(
                                                f"<table style='border-collapse:collapse;"
                                                f'font-family:"IBM Plex Mono",monospace;\'>'
                                                f"<thead><tr>"
                                                f"<th style='color:#71717a;font-size:9px;"
                                                f"text-transform:uppercase;padding:2px 8px;"
                                                f"text-align:left;'>Tool</th>"
                                                f"<th style='color:#71717a;font-size:9px;"
                                                f"text-transform:uppercase;padding:2px 8px;"
                                                f"text-align:right;'>Count</th>"
                                                f"<th style='color:#71717a;font-size:9px;"
                                                f"text-transform:uppercase;padding:2px 8px;"
                                                f"text-align:right;'>%</th>"
                                                f"</tr></thead>"
                                                f"<tbody>{_retro_rows}</tbody>"
                                                f"</table>"
                                                f"{_err_html}"
                                            )
                                except (_json.JSONDecodeError, KeyError, TypeError, OSError):
                                    pass
                            # Also check for markdown summary
                            _md_path = _Path(handover_dir) / f"SPRINT{sprint_num}_CONTEXT_SUMMARY.md"
                            if _md_path.exists():
                                try:
                                    _md_content = _md_path.read_text()
                                    with ui.expansion("Context Summary").style(
                                        "width:100%;margin:2px 0 8px;color:#d4d4d8;"
                                    ):
                                        ui.html(
                                            f"<pre style='background:#18181b;color:#a1a1aa;"
                                            f"padding:8px;border-radius:6px;font-size:10px;"
                                            f'font-family:"IBM Plex Mono",monospace;'
                                            f"white-space:pre-wrap;overflow-x:auto;'>"
                                            f"{safe_html(_md_content)}</pre>"
                                        )
                                except OSError:
                                    pass
                        for card_item in sprint_items:
                            _render_card(
                                card_item,
                                "done",
                                move_item,
                                save_item,
                                refresh_board,
                                on_card_click=_open_done_panel,
                            )

        done_panel = ui.element("div").style("display:none;")
        done_panel_ref["el"] = done_panel
