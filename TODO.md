# TODO — agile-backlog

> Active sprint tasks only. Backlog lives in `backlog/*.yaml`.

---

## Sprint 1 — Complete

- [x] BacklogItem Pydantic model + slugify + tests (12 tests)
- [x] YAML store with git-root detection + tests (13 tests)
- [x] Click CLI: add, list, move, show, serve + tests (16 tests)
- [x] Full CI green (41 tests, ruff clean)
- [x] Entry point `agile-backlog` works via pip install

## Sprint 2 — Complete

- [x] Pure functions: category_style, filter_items, render_card_html + tests (24 tests)
- [x] Streamlit Kanban board with styled cards, filters, move-via-dropdown, expanders
- [x] CLI `serve` command launches Streamlit
- [x] Full CI green (65 tests, ruff clean)
- [x] Dogfooding: backlog managed via YAML files

## Sprint 3 — Complete

- [x] T3.1 — Unify card layout (bordered containers + move buttons)
- [x] T3.2 — Smarter filtering (backlog-only, priority ranges, dimmed done)
- [x] T3.3 — Polish frontend design (compact layout, styled headers, CSS overhaul)
- [x] T3.4 — Sprint indicator badge in header
- [x] T3.5 — Claude Code plugin (/backlog command)
- [x] Full CI green (73 tests, ruff clean)
- [x] Professional frontend redesign (light-mode colors, shadows, pills)

## Sprint 4 — Design-First Polish + Workflow Phases + Installable

**Theme:** Get the board looking great with a proper design system, add workflow phases to items, and make the tool installable.

### T4.1 — UI/UX research and design system
- **Goal:** Research existing Kanban tools and define a design system to guide all future UI work
- **Specialist:** python-architect
- **Complexity:** M
- **Depends on:** None
- **DoD:**
  - [ ] Research doc covers Linear, Notion, Trello, GitHub Projects card designs
  - [ ] Card anatomy defined (layout, sizing, spacing, element placement)
  - [ ] Color system defined (category, priority, status — works on light backgrounds)
  - [ ] Typography scale defined (headings, body, badges, captions)
  - [ ] Component library sketched (buttons, badges, expanders, filters, column headers)
  - [ ] Interaction patterns documented (move, expand, filter, search)
  - [ ] Design spec saved to `docs/superpowers/specs/`
- **Technical Specs:**
  - Output: `docs/superpowers/specs/2026-03-21-design-system.md`
  - Research via web — screenshots/references from Linear, Notion, Trello, GitHub Projects
  - Define CSS variables / token system for consistent styling
  - Include mockups or detailed descriptions for card states (default, hover, expanded, done)
- **Test Plan:**
  - No code — document only
- **Demo Data Impact:** None

### T4.2 — Add phase field to BacklogItem
- **Goal:** Add a phase field to track workflow stage for items in "doing" status
- **Specialist:** python-architect
- **Complexity:** M
- **Depends on:** None
- **DoD:**
  - [ ] `phase` field added to BacklogItem model (optional, nullable)
  - [ ] Valid phases: scoping, spec, spec-review, design, design-review, coding, code-review, testing
  - [ ] CLI `move` command accepts `--phase` option
  - [ ] Phase shown on card in the board UI
  - [ ] Phase stored in YAML files
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Modify `src/models.py`: add `phase: Literal[...] | None = None` field
  - Modify `src/cli.py`: add `--phase` option to `move` command, add `phase` display to `show`
  - Modify `src/app.py`: show phase badge on card, clear phase when status != "doing"
  - Update `src/schema.yaml` with phase field
- **Test Plan:**
  - `tests/test_models.py` — test phase validation, default None
  - `tests/test_cli.py` — test `move --phase coding`
  - `tests/test_app.py` — test phase displayed in render_card_html

### T4.3 — Task definition per backlog item
- **Goal:** Support structured task definitions (Goal, DoD, Tech Specs, Test Plan) in backlog items
- **Specialist:** python-architect
- **Complexity:** M
- **Depends on:** T4.2
- **DoD:**
  - [ ] BacklogItem model supports `goal`, `complexity`, `technical_specs` fields
  - [ ] CLI `add` or `edit` supports setting these fields
  - [ ] Task definition required before moving to `coding` phase (warning if missing)
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Modify `src/models.py`: add `goal: str = ""`, `complexity: Literal["S","M","L"] | None = None`, `technical_specs: list[str] = []`
  - Existing fields already cover: `description`, `acceptance_criteria` (= DoD), `notes`
  - Modify `src/cli.py`: show these fields in `show` command
  - Update `src/schema.yaml`
- **Test Plan:**
  - `tests/test_models.py` — test new fields, defaults, validation

### T4.4 — Display task details formatted per template
- **Goal:** Render task definitions beautifully in the card expander, not as raw text
- **Specialist:** python-architect
- **Complexity:** M
- **Depends on:** T4.3, T4.1
- **DoD:**
  - [ ] Expander shows Goal prominently
  - [ ] Complexity shown as badge (S/M/L)
  - [ ] Acceptance criteria rendered as checkbox list
  - [ ] Technical specs rendered as bullet list
  - [ ] Styling follows design system from T4.1
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Modify `src/app.py`: rewrite expander content rendering
  - Use HTML/CSS from design system for consistent styling
  - Group fields: Overview (goal, complexity) → DoD → Tech Specs → Metadata (dates, tags, deps)
- **Test Plan:**
  - Manual verification in browser
  - `tests/test_app.py` — if rendering extracted to pure function, test HTML output

### T4.5 — Card design v2
- **Goal:** Implement the card design from the design system research
- **Specialist:** python-architect
- **Complexity:** M
- **Depends on:** T4.1, T4.2
- **DoD:**
  - [ ] Cards follow design system (colors, typography, spacing)
  - [ ] Title, category, priority, phase all visible and well-placed
  - [ ] Move buttons styled per design system
  - [ ] Done cards visually distinct
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Modify `src/app.py`: rewrite `render_card_html()` and CSS per design system
  - Apply design tokens (CSS variables) for consistent styling
- **Test Plan:**
  - `tests/test_app.py` — render_card_html tests updated
  - Manual verification in browser

### T4.6 — Make agile-backlog installable (pip/pipx from GitHub)
- **Goal:** Document and verify installation via pip/pipx from GitHub repo
- **Specialist:** python-architect
- **Complexity:** S
- **Depends on:** None
- **DoD:**
  - [ ] `pip install git+https://github.com/zbarbur/agile-backlog.git` works
  - [ ] `pipx install git+https://github.com/zbarbur/agile-backlog.git` works
  - [ ] `agile-backlog --help` works after install
  - [ ] `agile-backlog serve` works after install
  - [ ] README.md created with installation instructions
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Verify `pyproject.toml` has correct metadata (author, license, classifiers)
  - Create `README.md` with: project description, install instructions, usage examples, screenshot
  - Test install in clean venv
- **Test Plan:**
  - Manual: install in fresh venv, run CLI commands
- **Demo Data Impact:** None
