# Plan — edit repeatable list flags: add --append-* opt-in

## Reframe

The original bug description ("edit --acceptance-criteria APPENDS") does NOT reproduce in this codebase. `cli.py:273` has always replaced (`setattr(item, field, list(value))`). The incident was in data_classifier against a forked/older CLI.

Scope pivots from "fix append bug" to: **keep replace as default (correct, desired), and add `--append-*` opt-in flags for the accumulation use case.** Plus regression tests to lock in replace semantics so a future refactor can't silently swap them.

## Changes

### `src/agile_backlog/cli.py`

Three new Click options on the `edit` command (mirror of existing repeatable flags):

```python
@click.option("--append-technical-specs", "append_technical_specs", multiple=True,
              help="Append to technical_specs instead of replacing (use with repeated values).")
@click.option("--append-acceptance-criteria", "append_acceptance_criteria", multiple=True,
              help="Append to acceptance_criteria instead of replacing.")
@click.option("--append-test-plan", "append_test_plan", multiple=True,
              help="Append to test_plan instead of replacing.")
```

Handler change — pop the 3 append keys from `kwargs` before the main setattr loop, then extend after:

```python
append_specs = kwargs.pop("append_technical_specs", ()) or ()
append_ac    = kwargs.pop("append_acceptance_criteria", ()) or ()
append_test  = kwargs.pop("append_test_plan", ()) or ()

for field, value in kwargs.items():
    if value is not None and value != ():
        if isinstance(value, tuple):
            setattr(item, field, list(value))
        else:
            setattr(item, field, value)

if append_specs:
    item.technical_specs.extend(append_specs)
if append_ac:
    item.acceptance_criteria.extend(append_ac)
if append_test:
    item.test_plan.extend(append_test)
```

**Combined flags semantic:** if the user passes both `--acceptance-criteria A --append-acceptance-criteria B`, result is `[A, B]` (replace first, then append). Intuitive and documented in the help text.

### `tests/test_cli.py`

Replace the anemic `test_edit_acceptance_criteria` (currently just checks exit code) with richer coverage. Add tests:

1. **test_edit_list_flag_replaces_existing** — parametrized over the 3 fields. Populate list with 2 items, re-edit with a different value, verify final list == `[new]` only.
2. **test_edit_append_flag_extends_existing** — parametrized. Populate with 2 items, use `--append-*` with 1 value, verify final list has all 3.
3. **test_edit_replace_then_append_in_one_call** — one test covering the combined-flag edge case to document the "replace first, then append" semantic.

Use `parametrize` with tuples of `(flag_name, append_flag_name, model_field)`.

## Execution order (TDD)

1. Write the 3 tests first (with current code, #1 passes, #2 and #3 fail — confirms test validity).
2. Add the 3 Click options + handler change.
3. Re-run tests — all 3 pass.
4. Full CI: ruff check + format + pytest.

## Acceptance

Maps to existing item AC (all 5):
- AC1 "Running edit with a repeatable list flag replaces the existing list" → test #1
- AC2 "--append-* flag preserves append behavior as opt-in" → new Click options + test #2
- AC3 "Regression test covers replace-default and append-opt-in semantics for all 3 list fields" → parametrized tests #1 + #2
- AC4 "Tests pass" → pytest green
- AC5 "Lint clean" → ruff check + format clean

## Post-merge follow-up

Update item's goal to reflect the reframe (from "fix append bug" → "add append opt-in").
