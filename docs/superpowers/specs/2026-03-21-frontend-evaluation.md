# Frontend Evaluation — Recommendation

> **Date:** 2026-03-21
> **Decision:** Migrate from Streamlit to NiceGUI
> **Status:** Approved

---

## Context

After 5 sprints building with Streamlit, we hit its design ceiling:
- Can't style individual widgets (all buttons share CSS)
- Can't set per-column backgrounds natively
- Extra whitespace between elements is not fully controllable
- No drag-and-drop with rich card rendering
- Dark mode breaks hardcoded light-mode colors
- Expanders and containers have rigid styling

## Options Evaluated

### A. NiceGUI (Recommended)

**What:** Python framework built on FastAPI + Vue.js + Quasar components + Tailwind CSS.

| Aspect | Assessment |
|--------|-----------|
| Styling control | Full — Tailwind classes, raw CSS, Quasar props on every element |
| Component library | Quasar (Material Design) — cards, badges, buttons, dialogs, drag-and-drop |
| Learning curve | Low — Python API similar to Streamlit but more explicit |
| Deployment | Single Python process, no Node.js, no build step |
| Drag-and-drop | Built-in via Quasar sortable |
| Dark mode | One-line toggle, colors adapt automatically |
| Hot reload | Yes |
| Community | Smaller than Streamlit, growing |

### B. Reflex

**What:** Python → compiles to Next.js + React with Radix UI components.

| Aspect | Assessment |
|--------|-----------|
| Styling control | Full — React + Radix UI, very polished |
| Learning curve | Steeper — React concepts, state management, compilation |
| Deployment | Requires Node.js for compilation |
| Startup time | Slower (compilation step) |
| Architecture | More opinionated, heavier |

**Verdict:** Too heavy for an internal dev tool. The Node.js dependency and compilation step add unnecessary complexity.

### C. Streamlit + Custom Components

**What:** Keep Streamlit, build a React component for the Kanban board in an iframe.

| Aspect | Assessment |
|--------|-----------|
| Migration effort | Low (incremental) |
| Styling control | Full inside the component, limited outside |
| Complexity | Two languages (Python + React/JS), iframe communication |
| Maintenance | Custom component needs separate build/test |

**Verdict:** Adds complexity without solving the fundamental layout issues. Still limited by Streamlit's outer layout system.

## Decision: NiceGUI

**Why:**
1. **Lightest migration** — Python API, no build step, no Node.js
2. **Full styling control** — Tailwind + Quasar + raw CSS on every element
3. **Drag-and-drop included** — Quasar sortable works with rich card content
4. **Same data layer** — models.py, yaml_store.py, cli.py unchanged. Only app.py replaced.
5. **Dark mode free** — Quasar handles theme switching
6. **Individual widget styling** — every button, card, badge independently stylable

## Migration Plan

### What changes
- `src/app.py` — complete rewrite using NiceGUI API
- `pyproject.toml` — replace `streamlit` + `streamlit-sortables` with `nicegui`
- `.streamlit/config.toml` — remove (no longer needed)
- `src/cli.py` serve command — update to launch NiceGUI instead of Streamlit

### What stays the same
- `src/models.py` — no changes
- `src/yaml_store.py` — no changes
- `src/cli.py` — all commands except `serve` unchanged
- `tests/test_models.py` — no changes
- `tests/test_yaml_store.py` — no changes
- `tests/test_cli.py` — update serve test
- `tests/test_app.py` — rewrite (pure functions may change signatures)
- `backlog/*.yaml` — no changes
- `plugin/` — no changes

### Estimated effort
- **Sprint 7:** Rewrite app.py with NiceGUI, basic board (columns, cards, filters, move)
- **Sprint 8:** Drag-and-drop, inline editing, polish

## Dependencies

```
nicegui>=2.0.0
```

Replaces: `streamlit>=1.30.0`, `streamlit-sortables>=0.3.0`
