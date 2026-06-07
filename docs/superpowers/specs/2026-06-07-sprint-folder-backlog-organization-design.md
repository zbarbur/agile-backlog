# Sprint-folder Backlog Organization — Design

**Date:** 2026-06-07
**Status:** Approved (design); implementation scheduled as a Sprint 32 item
**Author:** brainstorming session

## Motivation

The backlog is ~40+ flat `backlog/*.yaml` files and growing. Three goals drive this change:

1. **Declutter** the flat directory so it is navigable in the editor and on GitHub.
2. **Archive past sprints** so the live working set shows only current/future work.
3. **Per-sprint isolation** — each sprint's items as a self-contained, easily diffable set.

Explicitly **not** a goal: making the folder the source of truth for sprint membership. `sprint_target` stays authoritative; the folder is derived from it.

## Directory Layout

```
backlog/
  unplanned/        # sprint_target = null
  sprint{N}/        # N >= current_sprint  (current + future)
  archive/
    sprint{N}/      # N <  current_sprint  (completed)
```

Underscore-prefixed files **and directories** are ignored everywhere (extends the rule shipped in Sprint 31's `list-warns` item).

## Source of Truth — Derived, Not Duplicated

`sprint_target` (on the item) plus `current_sprint` (from `.claude/sprint-config.yaml`) remain the single authority. A pure function maps an item to its folder:

```python
def item_dir(sprint_target: int | None, current_sprint: int) -> Path:
    if sprint_target is None:
        return backlog / "unplanned"
    if sprint_target >= current_sprint:
        return backlog / f"sprint{sprint_target}"
    return backlog / "archive" / f"sprint{sprint_target}"
```

Because the folder is always a function of the field, the two cannot disagree. There is no new field and no second source of truth.

## Component Changes

### `yaml_store.py` (core change — becomes tier-aware)

Current state (verified): an item's identity **is** its filename (`load_all` sets `item_id = path.stem`); `save_item`/`load_item`/`delete_item`/`item_exists` all assume a flat `backlog/<id>.yaml`; `load_all` uses a non-recursive `glob("*.yaml")` that already skips underscore-prefixed names.

Changes:

- **`load_all()`** — recurse the tiers instead of a flat glob. Skip underscore-prefixed files and directories. Preserve the quiet-skip behavior for foreign/incomplete YAML (one summary line, no per-file warnings).
- **`item_path(item_id) -> Path | None`** (new) — locate a file by stem across the tiers. Filenames (= ids) are globally unique, so a stem resolves to at most one file. A per-process cache/index is acceptable; the working set is dozens of files, so a walk is negligible.
- **`load_item(id)` / `delete_item(id)` / `item_exists(id)`** — resolve via `item_path`.
- **`save_item(item)`** — compute the target dir via `item_dir(...)`, `mkdir -p`, and **relocate the file if its sprint changed** (find any existing file for this id and move it to the derived dir before writing). This is the auto-relocate that keeps day-to-day operations correct.
- **Invariant** — id (filename stem) is globally unique across all tiers. `add` errors if the id already exists anywhere.

### `reconcile [--dry-run]` (new CLI command)

Walks every item, computes its correct tier from `(sprint_target, current_sprint)`, and moves any file whose current folder differs. Uses `git mv` when inside a git repo to preserve history; falls back to a plain move otherwise. `--dry-run` prints the planned moves without applying them.

`reconcile` is the home for three jobs:
1. **One-time migration** of today's flat files into the tiers.
2. **Sprint-close archival sweep** — when `current_sprint` advances, the just-closed sprint (now `< current`) slides into `archive/`.
3. **Drift safety net** — fix any item whose folder fell out of sync.

### Lifecycle integration

- `set-sprint` / `sprint-start` advancing `current_sprint` triggers a `reconcile` so the previous current sprint moves under `archive/`.
- `sprint-end` runs `reconcile` as part of close-out.

## Data Flow

All read paths (`dashboard`, `context_report`, `sprint-status`, `list`, `validate`) go through `load_all()`. Once `load_all` is recursive, they keep working unchanged — they already filter on `sprint_target`, not on path. The `archive_sprints: 5` board-hiding logic is orthogonal and continues to operate on `sprint_target`.

## Error Handling

- Foreign/incomplete YAML: same quiet-skip as today (single summary line, no stack traces).
- `item_path` miss: same `FileNotFoundError` contract as today's `load_item`.
- `reconcile` outside a git repo: fall back to plain filesystem move (no `git mv`).
- Duplicate id across tiers (should be impossible given the invariant): `reconcile` reports it as a conflict rather than silently overwriting.

## Migration

A single `reconcile` run relocates everything: `sprint_target` in `0..current-1` → `archive/sprint{N}/`, current/future → `sprint{N}/`, null → `unplanned/`. Filenames (ids) are unchanged; only directories move. Historical/odd `sprint_target` values (e.g. 0, 3, 18) map to `archive/sprint{N}` by the same rule — no special-casing.

## Testing

- `set_backlog_dir` override still works (tests point it at a tmp dir); add tier-aware fixtures.
- Unit: `item_dir` mapping (null / current / future / past); `save_item` relocation when `sprint_target` changes; `item_path` resolution across tiers; `load_all` recursion + underscore-dir skip.
- `reconcile`: dry-run lists correct moves; apply relocates; idempotent on a second run; reports duplicate-id conflicts.
- Regression: `list --sprint`, `validate`, `sprint-status`, dashboard load still return the same items post-migration.

## Risks & Interactions

- **Blast radius**: four `yaml_store` functions change; everything else reads through `load_all`. Keep the change behind the stable `load_item`/`save_item`/`load_all` interfaces so callers are untouched.
- **Git churn**: the one-time migration is a large file-move commit; use `git mv` so history follows.
- **`.backlogignore`** (separate deferred item): `load_all`/`reconcile` should honor it once it lands; the underscore-dir skip is the interim mechanism. This design leaves room for it at the same filter point.

## Out of Scope

- Folder as source of truth (rejected — `sprint_target` stays authoritative).
- Changing or renaming item ids.
- The `.backlogignore` file format and an `import`/`init` adoption command (tracked as separate Sprint 32 items).
