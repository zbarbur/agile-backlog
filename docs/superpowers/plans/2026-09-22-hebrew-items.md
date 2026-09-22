# Hebrew backlog items Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An all-Hebrew backlog item can be created from the CLI and reads correctly on the board.

**Architecture:** Two independent changes. `add` gains an explicit `--id` option and refuses an empty slug instead of writing `backlog/.yaml`. The board's global stylesheet gains `unicode-bidi: plaintext` on every text-bearing element, which is CSS's `dir="auto"`: each paragraph takes its direction from its first strong character, so a Hebrew title with a digit in it reads in order and an English one is untouched.

**Tech Stack:** Python 3.11+, Click, Pydantic, NiceGUI, pytest. Run the whole CI locally with `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`.

**Spec:** `/Users/guyguzner/Projects/AI_Agency/docs/superpowers/specs/2026-09-22-domain-owner-proposal-lane-design.md` §6 — this plan is executed in **this** repository (`agile-backlog`), the spec lives in the consumer's.

## Global Constraints

- The item id is the filename. `save_item` writes `get_backlog_dir() / f"{item.id}.yaml"` with no check; an empty id writes a dotfile.
- `slugify` keeps only `[a-z0-9]`; it is used by both the CLI (`cli.py:78`) and the web UI (`app.py:765`). Do not change `slugify` — an ASCII-only id is the design, the fix is to let the caller supply one.
- Tests patch `agile_backlog.yaml_store.get_backlog_dir` to a `tmp_path` (see `tests/test_cli.py` fixtures `backlog_dir`, `_patch_backlog_dir`, `runner`). Reuse them; do not touch the real `backlog/`.
- `GLOBAL_CSS` lives in `src/agile_backlog/styles.py` and is injected once by `app.py:509` via `ui.add_head_html`. `tests/test_markdown.py::TestMarkdownCssInStyles` asserts on its text — follow that pattern.
- Existing CLI behaviour must not move: `test_add_slug_collision` still expects `duplicate-2`.

---

### Task 1: `add --id` and the empty-slug guard

**Files:**
- Modify: `src/agile_backlog/cli.py:49-100` (the `add` command)
- Test: `tests/test_cli.py` (class `TestAdd`)

**Interfaces:**
- Consumes: `slugify(title) -> str` from `models.py`; `item_exists(item_id) -> bool` and `save_item(item) -> Path` from `yaml_store.py`.
- Produces: `agile-backlog add TITLE --category C --id SLUG`. `--id` must match `^[a-z0-9]+(-[a-z0-9]+)*$`; without `--id`, a title that slugifies to `''` exits 2 with `Title produces an invalid ID; pass --id <ascii-slug>.` Collision handling is unchanged and applies to an explicit `--id` too.

- [ ] **Step 1: Write the failing tests**

Append to `class TestAdd` in `tests/test_cli.py`:

```python
    def test_add_hebrew_title_without_id_is_refused(self, runner: CliRunner, backlog_dir: Path):
        """An all-Hebrew title slugifies to '' — the CLI must refuse, not write backlog/.yaml."""
        result = runner.invoke(main, ["add", "דוח שאירים לפי לקוח", "--category", "feature"])
        assert result.exit_code == 2
        assert "Title produces an invalid ID" in result.output
        assert "--id" in result.output
        assert not (backlog_dir / ".yaml").exists()
        assert list(backlog_dir.iterdir()) == []

    def test_add_hebrew_title_with_id(self, runner: CliRunner, backlog_dir: Path):
        result = runner.invoke(
            main,
            ["add", "דוח שאירים לפי לקוח", "--category", "feature", "--id", "survivors-report-per-client"],
        )
        assert result.exit_code == 0, result.output
        assert "Created: survivors-report-per-client" in result.output
        path = backlog_dir / "survivors-report-per-client.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert data["id"] == "survivors-report-per-client"
        assert data["title"] == "דוח שאירים לפי לקוח"

    def test_add_id_must_be_an_ascii_slug(self, runner: CliRunner, backlog_dir: Path):
        for bad in ["דוח", "Has Spaces", "UPPER", "trailing-", "-leading", "double--dash"]:
            result = runner.invoke(main, ["add", "x", "--category", "feature", "--id", bad])
            assert result.exit_code == 2, bad
            assert "--id" in result.output, bad
        assert list(backlog_dir.iterdir()) == []

    def test_add_explicit_id_collides_like_a_slug(self, runner: CliRunner, backlog_dir: Path):
        runner.invoke(main, ["add", "a", "--category", "feature", "--id", "same"])
        result = runner.invoke(main, ["add", "b", "--category", "feature", "--id", "same"])
        assert result.exit_code == 0
        assert "same-2" in result.output
        assert (backlog_dir / "same.yaml").exists()
        assert (backlog_dir / "same-2.yaml").exists()
```

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv/bin/pytest tests/test_cli.py::TestAdd -v -k "hebrew or ascii_slug or explicit_id"`
Expected: 4 FAIL. The first fails on `exit_code == 2` (today it exits 0 and writes `.yaml`); the others fail with `No such option: --id`.

- [ ] **Step 3: Implement**

In `src/agile_backlog/cli.py`, add near the top (after the imports):

```python
import re

#: An item id is its filename and its cross-reference key, so it is ASCII
#: by design. `slugify` derives one from an English title; a title in any
#: other script derives nothing, and the caller supplies the id instead.
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
```

Add the option to `add` (after the `--tags` option, before `def add(`):

```python
@click.option(
    "--id",
    "item_id_opt",
    default=None,
    help="Explicit ASCII id (lowercase, digits, single dashes). Required when the title has no Latin letters.",
)
```

Add `item_id_opt: str | None,` as the last parameter of `def add(...)`.

Replace the single line `item_id = slugify(title)` with:

```python
    if item_id_opt is not None:
        if not ID_PATTERN.match(item_id_opt):
            raise click.BadParameter(
                "must be lowercase letters, digits and single dashes, e.g. survivors-report-per-client",
                param_hint="'--id'",
            )
        item_id = item_id_opt
    else:
        item_id = slugify(title)
        if not item_id:
            raise click.UsageError("Title produces an invalid ID; pass --id <ascii-slug>.")
```

- [ ] **Step 4: Run the tests to verify they pass, and that nothing else moved**

Run: `.venv/bin/pytest tests/test_cli.py -v`
Expected: all PASS, including `test_add_slug_collision` (`duplicate-2`) and `test_add_with_title_option`.

- [ ] **Step 5: Lint and format**

Run: `.venv/bin/ruff check . && .venv/bin/ruff format --check .`
Expected: clean. If `format --check` complains, run `.venv/bin/ruff format src/agile_backlog/cli.py tests/test_cli.py` and re-check.

- [ ] **Step 6: Document the option**

In `docs/CLI.md`, in the `add` options table, add the row:

```
| `--id` | no | ASCII slug | derived from the title; required when the title has no Latin letters (e.g. Hebrew) |
```

Also add the same row to the consumer's reference at `/Users/guyguzner/Projects/AI_Agency/.claude/skills/cli-reference/SKILL.md` under `### add` — that file is what the consumer's Claude sessions read, and it currently lists no `--id`.

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/cli.py tests/test_cli.py docs/CLI.md
git commit -m "feat(cli): add --id, and refuse a title that slugifies to nothing

An all-Hebrew title slugifies to '' and add wrote backlog/.yaml — a dotfile
no listing shows. The web UI already refused this; the CLI now does too,
and names the remedy: an explicit ASCII --id, validated as a slug and
subject to the same collision suffixing."
```

(The consumer-repo edit to `cli-reference/SKILL.md` is committed in the consumer repo, in the proposal-lane plan's Task 1.)

---

### Task 2: The board reads Hebrew in order

**Files:**
- Modify: `src/agile_backlog/styles.py` (`GLOBAL_CSS`)
- Test: `tests/test_bidi.py` (new)

**Interfaces:**
- Consumes: `GLOBAL_CSS: str` from `styles.py`, injected by `app.py:509`.
- Produces: a `unicode-bidi: plaintext` rule covering every element that renders item text — card titles (`.mc-card-row span`, `.mc-editable`), Quasar inputs and textareas (`.q-field__native`, `textarea`), markdown bodies (`.nicegui-markdown`, `.nicegui-markdown *`), and comments/list rows (`.q-item__label`). Nothing else changes.

Why CSS and not `dir="auto"` per element: titles are rendered in at least three places (`pure.py:153`, `components.py:82`, `components.py:458`) and goals, descriptions, criteria and comments in more; a per-site attribute would be the fifth hand-written site list in the consumer's memory notes, and would miss one. `unicode-bidi: plaintext` is the CSS equivalent of `dir="auto"` — per paragraph, first strong character wins — and one rule covers every present and future site.

- [ ] **Step 1: Write the failing test**

Create `tests/test_bidi.py`:

```python
# tests/test_bidi.py
# The board has to read Hebrew in order. A Hebrew title with a digit or a
# Latin token in it renders scrambled under a fixed LTR base direction; the
# fix is one CSS rule — unicode-bidi: plaintext — on every text-bearing
# element, which is what dir="auto" does, without a per-site attribute.

from pathlib import Path

STYLES = Path(__file__).parent.parent / "src" / "agile_backlog" / "styles.py"

TEXT_SELECTORS = [
    ".mc-card-row span",
    ".mc-editable",
    ".q-field__native",
    "textarea",
    ".nicegui-markdown",
    ".q-item__label",
]


def _plaintext_rule() -> str:
    css = STYLES.read_text()
    start = css.index("unicode-bidi: plaintext")
    block_start = css.rfind("{", 0, start)
    selector_start = css.rfind("}", 0, block_start) + 1
    return css[selector_start:block_start]


def test_global_css_declares_plaintext_bidi():
    assert "unicode-bidi: plaintext" in STYLES.read_text()


def test_every_text_bearing_selector_is_covered():
    selectors = _plaintext_rule()
    missing = [s for s in TEXT_SELECTORS if s not in selectors]
    assert not missing, f"selectors without unicode-bidi: plaintext: {missing}"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/pytest tests/test_bidi.py -v`
Expected: `test_global_css_declares_plaintext_bidi` FAIL (`unicode-bidi` absent); the second errors on `index` — same cause.

- [ ] **Step 3: Add the rule**

In `src/agile_backlog/styles.py`, inside the `<style>` block of `GLOBAL_CSS`, immediately after the `body { ... }` rule, add:

```css
/* Bidirectional text reads in order. Item titles, goals, criteria and
   comments may be Hebrew, English, or Hebrew with digits and Latin
   tokens; plaintext takes each paragraph's direction from its first
   strong character — the CSS form of dir="auto" — so nothing here needs
   to know which language an item was written in. */
.mc-card-row span,
.mc-editable,
.q-field__native,
textarea,
.nicegui-markdown,
.nicegui-markdown *,
.q-item__label {
    unicode-bidi: plaintext;
}
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/pytest tests/test_bidi.py tests/test_markdown.py -v`
Expected: all PASS.

- [ ] **Step 5: The screenshot gate (this is the acceptance, not the unit test)**

The unit test proves the rule is declared. Only a browser proves it renders. In a scratch backlog:

```bash
TMP=$(mktemp -d "${TMPDIR:-/tmp}/bidi.XXXXXX"); mkdir "$TMP/backlog"
.venv/bin/agile-backlog --backlog-dir "$TMP/backlog" add "מסך חדש: השוואת דמי ניהול 2026 מול Base44" \
  --category feature --id bidi-probe --goal "להציג 3 עמודות: קרן, דמי ניהול, פער מול Base44"
.venv/bin/agile-backlog --backlog-dir "$TMP/backlog" serve --port 8511
```

(If `--backlog-dir` is not a global option in this version, check `agile-backlog --help`; `cli.py:46` shows `set_backlog_dir(Path(backlog_dir))`, so the option exists — find its spelling there.)

Open `http://127.0.0.1:8511`, find the card, open it. Check by eye and record the answer in the commit message:

1. The card title reads `מסך חדש: השוואת דמי ניהול 2026 מול Base44` with `2026` and `Base44` in their places — not `Base44 מול 2026 ...` reversed.
2. The goal in the detail pane reads `להציג 3 עמודות: קרן, דמי ניהול, פער מול Base44` with the `3` after `להציג`.
3. Click the title to edit: the input shows the same order.
4. An existing English item (add one: `add "English control" --category chore`) is unchanged.

Take one screenshot of the detail pane and save it as `docs/design/2026-09-22-bidi-plaintext.png`. Stop the server: `.venv/bin/agile-backlog stop`.

If any of 1–3 reads out of order, the element is not covered by the selector list: find its class in DevTools, add it to both the rule and `TEXT_SELECTORS`, and repeat.

- [ ] **Step 6: Lint, format, full suite**

Run: `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`
Expected: clean, all PASS.

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/styles.py tests/test_bidi.py docs/design/2026-09-22-bidi-plaintext.png
git commit -m "fix(board): bidirectional text reads in order

One rule — unicode-bidi: plaintext on every text-bearing element — so a
Hebrew title with a digit or a Latin token in it renders in reading order,
and an English one is untouched. The CSS form of dir=auto, chosen over a
per-site attribute because titles alone render from three helpers.

Verified in a browser: card title, detail goal and the title editor all
read in order for 'מסך חדש: השוואת דמי ניהול 2026 מול Base44';
screenshot in docs/design/."
```
