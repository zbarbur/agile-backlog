# Phase 2: Drag-and-Drop + Keyboard Navigation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add drag-and-drop between backlog sections and keyboard navigation for the backlog planning view.

**Architecture:** Two independent features added to the existing backlog view in `components.py`. Drag-and-drop uses the HTML5 Drag API with JS injected via `ui.run_javascript`. Keyboard navigation extends the existing `ui.keyboard` handler. Both features reuse the existing `_move_to_section()` function for data updates.

**Tech Stack:** Python 3.11+, NiceGUI, HTML5 Drag API, JavaScript

---

## File Map

| File | Action | Tasks |
|------|--------|-------|
| `src/agile_backlog/components.py` | Modify | 1, 2 |
| `src/agile_backlog/styles.py` | Modify | 1 |

---

## Task 1: Drag-and-Drop Between Backlog Sections

**Files:**
- Modify: `src/agile_backlog/components.py:600-665` — add `draggable` attributes and data attributes to card rows
- Modify: `src/agile_backlog/components.py:713-754` — add drop zone data attributes to section content divs
- Modify: `src/agile_backlog/components.py` (end of function) — inject drag-and-drop JS
- Modify: `src/agile_backlog/styles.py:132-140` — add drag feedback CSS

### Approach

Use the HTML5 Drag and Drop API:
1. Each card row gets `draggable="true"` and a `data-item-id` attribute
2. Each section content div gets a `data-section` attribute and `data-sprint-target` attribute
3. JavaScript handles `dragstart`, `dragover`, `drop`, `dragend` events
4. On drop, a NiceGUI endpoint is called to update the item's `sprint_target`

The key challenge is bridging JS → Python. NiceGUI's `ui.run_javascript` is Python→JS only. For JS→Python callbacks, we use NiceGUI's `app.storage` or emit custom events. The simplest approach: use `emitEvent` from NiceGUI's client-side API to call a Python handler.

Actually, the cleanest NiceGUI pattern is to create a hidden element with an `on()` handler that JS can trigger via `element.click()` or similar. But even simpler: we can use `ui.run_javascript` to return the drop result and handle it.

**Simplest approach:** After a drop, the JS calls `emitEvent('drop_item', {item_id, section})` which NiceGUI routes to a Python handler. NiceGUI supports this via `ui.on('drop_item', handler)`.

- [ ] **Step 1: Add drag feedback CSS to styles.py**

Add after the `.mc-resize-handle` block (after line 152):

```css
/* Drag-and-drop */
.mc-card-row[draggable="true"] { cursor: grab; }
.mc-card-row.mc-dragging { opacity: 0.4; }
.mc-drop-zone.mc-drag-over { background: rgba(59,130,246,0.06) !important; outline: 2px dashed rgba(59,130,246,0.3); outline-offset: -2px; border-radius: 6px; }
```

- [ ] **Step 2: Add data attributes to card rows**

In `_render_section_items()` (line 614), modify the card row element to include `draggable` and `data-item-id`:

Change:
```python
with (
    ui.element("div")
    .classes(f"mc-card-row{selected_class}")
    .style("position:relative;margin:2px 0;padding:0 4px;")
):
```

To:
```python
with (
    ui.element("div")
    .classes(f"mc-card-row{selected_class}")
    .style("position:relative;margin:2px 0;padding:0 4px;")
    .props(f'draggable="true" data-item-id="{card_item.id}" data-section="{section}"')
):
```

Note: NiceGUI's `.props()` adds HTML attributes to the underlying DOM element.

- [ ] **Step 3: Add data attributes to section content divs**

In the section layout (lines 713-754), add `data-section` and `data-sprint-target` to each section's content div. Also add the `mc-drop-zone` class.

For the backlog content div (line 720):
```python
backlog_content = (
    ui.element("div")
    .classes("mc-drop-zone")
    .props('data-section="backlog" data-sprint-target="null"')
    .style("flex:1;overflow-y:auto;padding:0 4px 4px;")
)
```

For the vnext content div (line 734):
```python
vnext_content = (
    ui.element("div")
    .classes("mc-drop-zone")
    .props(f'data-section="vnext" data-sprint-target="{next_sprint}"')
    .style("flex:1;overflow-y:auto;padding:0 4px 4px;")
)
```

For the vfuture content div (line 748):
```python
vfuture_content = (
    ui.element("div")
    .classes("mc-drop-zone")
    .props(f'data-section="vfuture" data-sprint-target="{future_sprint}"')
    .style("flex:1;overflow-y:auto;padding:0 4px 4px;")
)
```

**Important:** Use `.props()` method (not `._props` dict) to ensure attributes render correctly to the DOM. If `.props()` doesn't support `data-*` attributes in NiceGUI, fall back to injecting them via JS after render: `ui.run_javascript('document.querySelector(".mc-drop-zone[...]").setAttribute("data-sprint-target", "...")')`.

- [ ] **Step 4: Create a hidden trigger element for drop callbacks**

Before the section layout (around line 710), create a hidden element that JS can programmatically click to trigger a Python callback:

```python
# Hidden drop handler — JS triggers this by dispatching a custom event
drop_trigger = ui.element("div").style("display:none;").props('id="drop-trigger"')

async def _handle_drop(e):
    """Handle drag-and-drop from JS custom event."""
    detail = await ui.run_javascript(
        'window._lastDrop || null'
    )
    if not detail:
        return
    item_id = detail.get("item_id")
    sprint_target_str = detail.get("sprint_target")
    sprint_target = None if sprint_target_str == "null" else int(sprint_target_str)
    # Find the item and move it
    item = next((i for i in all_items if i.id == item_id), None)
    if item:
        _move_to_section(item, sprint_target)

drop_trigger.on("click", _handle_drop)
```

- [ ] **Step 5: Inject drag-and-drop JavaScript**

Add this JS constant at the module level or inline, injected via `ui.timer(0.1, ..., once=True)` alongside the resize JS:

```javascript
// Drag-and-drop between backlog sections
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
        // Only remove if leaving the zone entirely (not entering a child)
        if (!zone.contains(e.relatedTarget)) {
            zone.classList.remove('mc-drag-over');
        }
    });
    zone.addEventListener('drop', function(e) {
        e.preventDefault();
        zone.classList.remove('mc-drag-over');
        const itemId = e.dataTransfer.getData('text/plain');
        const sprintTarget = zone.getAttribute('data-sprint-target');
        // Store the drop data and trigger the hidden element
        window._lastDrop = {item_id: itemId, sprint_target: sprintTarget};
        document.getElementById('drop-trigger').click();
    });
});
```

- [ ] **Step 6: Combine JS injection**

The existing resize JS is injected at line 784. Combine both JS blocks into a single `ui.timer` call:

```python
_drag_drop_js = """..."""  # The JS from Step 5

_all_backlog_js = _resize_js + "\n" + _drag_drop_js

ui.timer(0.1, lambda: ui.run_javascript(_all_backlog_js), once=True)
```

- [ ] **Step 7: Test manually**

1. Run `agile-backlog serve`
2. Go to Backlog view
3. Drag an item from Backlog section to vNext — verify it moves and sprint_target updates
4. Drag from vNext to vFuture — verify
5. Drag from vFuture back to Backlog — verify sprint_target is null
6. Verify move buttons still work
7. Verify side panel still opens on click (not on drag)

- [ ] **Step 8: Run tests and lint**

Run: `.venv/bin/pytest tests/ -v && .venv/bin/ruff check . && .venv/bin/ruff format --check .`
Expected: ALL PASS

- [ ] **Step 9: Commit**

```bash
git add src/agile_backlog/components.py src/agile_backlog/styles.py
git commit -m "feat: add drag-and-drop between backlog sections"
```

---

## Task 2: Keyboard Navigation

**Files:**
- Modify: `src/agile_backlog/components.py:550` — extend keyboard handler

### Approach

Extend the existing `ui.keyboard` handler (currently only handles Escape) to support:
- Up/Down arrows: navigate between items within and across sections
- The selection should track a "focused" item, updating the side panel

The ordered list of items across all sections is: `filtered_backlog + vnext_items + vfuture_items`. We track an index into this combined list.

- [ ] **Step 1: Create navigation state and combined item list**

Add navigation state near the panel_state (around line 527), and define the combined list in the **outer scope** of `_render_backlog_list` so both `_handle_key` and `_open_side_panel` can access it:

```python
nav_state: dict[str, int | None] = {"index": None}
# Combined ordered list for keyboard nav — must be in outer scope
all_section_items = filtered_backlog + vnext_items + vfuture_items
```

- [ ] **Step 2: Extend keyboard handler**

Replace the current keyboard handler at line 550:

```python
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
        # Open side panel for the focused item
        focused_item = all_section_items[nav_state["index"]]
        _open_side_panel(focused_item)

ui.keyboard(on_key=_handle_key)
```

- [ ] **Step 3: Sync click selection with nav state**

Update `_open_side_panel` to sync the nav_state index when a card is clicked:

```python
# Inside _open_side_panel, after setting panel_state:
try:
    nav_state["index"] = all_section_items.index(item)
except ValueError:
    nav_state["index"] = None
```

- [ ] **Step 4: Add visual scroll-into-view**

When navigating with arrow keys, the focused item should scroll into view. Add JS after updating the side panel:

```python
# After updating nav_state["index"] in _handle_key:
ui.run_javascript(f'''
    const selected = document.querySelector('.mc-card-row.mc-selected');
    if (selected) selected.scrollIntoView({{block: 'nearest', behavior: 'smooth'}});
''')
```

- [ ] **Step 5: Test manually**

1. Open Backlog view with items in multiple sections
2. Press Down arrow — first item selects, side panel opens
3. Keep pressing Down — moves through items, crosses section boundaries
4. Press Up — moves backward
5. Press Escape — closes panel, deselects
6. Click an item, then use arrows — continues from clicked item

- [ ] **Step 6: Run tests and lint**

Run: `.venv/bin/pytest tests/ -v && .venv/bin/ruff check . && .venv/bin/ruff format --check .`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/components.py
git commit -m "feat: add keyboard navigation (arrow keys) in backlog view"
```

---

## Execution Order

| Order | Task | Complexity | Deps |
|-------|------|-----------|------|
| 1 | Drag-and-drop | M | None |
| 2 | Keyboard navigation | S | None (independent) |

Both tasks are independent but touch the same file, so execute sequentially.

## Important Notes

- The drag-and-drop JS→Python bridge is the trickiest part. The hidden element click pattern is the simplest NiceGUI approach, but if `_props` for data attributes doesn't work, the implementer should explore alternatives (e.g., `ui.html()` wrappers with data attributes, or NiceGUI's `app.on()` event system).
- Keyboard navigation uses the combined list `filtered_backlog + vnext_items + vfuture_items` — this means filter changes affect which items are navigable. This is correct behavior (you can only navigate visible items).
