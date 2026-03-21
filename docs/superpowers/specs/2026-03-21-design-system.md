# agile-backlog Design System

> **Date:** 2026-03-21
> **Type:** UI/UX design spec (no code)
> **Scope:** Streamlit Kanban board — visual language, component specs, interaction patterns
> **Constraints:** Pure CSS + HTML via `st.markdown(unsafe_allow_html=True)`. No JavaScript, no React, no external CSS frameworks.

---

## Research Summary

Patterns observed across Linear, Notion, Trello, and GitHub Projects that inform this design system:

### Linear
- **Cards are minimal:** title is dominant, metadata is secondary. No visual noise.
- **Priority icons** use a filled-circle system (urgent=red filled, high=orange half, medium=yellow quarter, low=gray outline). Compact, scannable without reading text.
- **Status indicators** are small colored dots (not badges), placed left of the title.
- **Typography is tight:** 13-14px titles, 11px metadata. System font stack. High information density without clutter.
- **Color is restrained:** mostly grayscale UI with color reserved for status dots, priority icons, and label pills.
- **Hover reveals actions:** move, assign, and context menus appear on hover, keeping the default card clean.

### Notion
- **Property badges** are the standout pattern: small rounded pills with colored backgrounds for each property (status, priority, category). Each property type has its own color palette.
- **Board cards** show title prominently, then a horizontal row of property pills below.
- **Flexible layout:** users choose which properties to show on cards, but the default is title + 2-3 property pills.
- **Soft colors:** pastel backgrounds with slightly darker text for badges. Never saturated.
- **Cover images optional:** adds visual weight but not relevant for our tool.

### Trello
- **Labels as color bars:** thin colored strips at the top of cards. Hovering reveals the label text. Very space-efficient.
- **Card structure:** optional cover image, then colored label strips, then title, then small icons for attachments/comments/due dates.
- **Rounded corners** (8px) and subtle shadow give cards a physical feel.
- **Column backgrounds** are tinted (light gray) to visually separate from the white cards.
- **Quick actions on hover:** edit, move, copy appear as small icon buttons.

### GitHub Projects
- **Status field** drives the column, so cards don't repeat it.
- **Labels** are colored pills with high contrast (colored background, white or dark text).
- **Priority** shown as a small text label or colored dot.
- **Assignee avatars** are common but not relevant for single-user tool.
- **Minimal chrome:** cards are borderless rows in the column, separated by subtle dividers. Very dense.
- **Field badges** shown inline after title, similar to Notion but more compact.

### Synthesis: Design Principles for agile-backlog

1. **Title dominance** (Linear/GitHub): the card title is the most prominent element. Everything else is secondary.
2. **Horizontal badge row** (Notion/GitHub): metadata as a row of small pills below the title. Scannable left-to-right.
3. **Color restraint** (Linear): color is meaningful, not decorative. Category gets a colored pill, priority gets a colored pill, everything else is grayscale.
4. **Soft palettes** (Notion): pastel/muted backgrounds for pills. Never saturated colors on backgrounds.
5. **Column differentiation** (Trello): subtle background tints distinguish columns without competing with card content.
6. **Progressive disclosure** (Linear): cards show minimal info; details expand on demand. Move actions are compact.

---

## 1. Card Anatomy

### Element Hierarchy (most to least prominent)

1. **Title** — largest text, bold, dark. The thing you read first.
2. **Category pill** — colored background, identifies what kind of work this is.
3. **Priority pill** — colored text/background, indicates urgency.
4. **Phase pill** — grayscale, shows current workflow phase.
5. **Sprint indicator** — subtle, small, right-aligned or last in the badge row.
6. **Move actions** — ghost buttons, bottom of card. Visually quiet.

### Layout: Two-Row Card

```
+----------------------------------------------+
|  Card title goes here                        |  <- Row 1: Title
|  [bug] [P1] [coding] [S2]                   |  <- Row 2: Badge row
+----------------------------------------------+
|  > item-id (click to expand)                 |  <- Expander trigger
|  [<- backlog] [-> done]                      |  <- Move buttons
+----------------------------------------------+
```

- Row 1: Title only. No emoji prefix (emoji goes inside the category pill).
- Row 2: Horizontal flex row of badge pills. Order: category, priority, phase, sprint.
- Below the HTML card: Streamlit expander + move buttons (native Streamlit widgets).

### Sizing and Spacing

| Element | Value |
|---------|-------|
| Card outer padding | 10px 14px |
| Card inner gap (title to badges) | 6px |
| Badge row gap | 6px |
| Badge pill internal padding | 2px 8px |
| Move button row gap | 6px |
| Space between cards (column gap) | 8px |

### Card States

| State | Visual Treatment |
|-------|-----------------|
| **Default** | White background, 1px `#e5e7eb` border, subtle shadow `0 1px 2px rgba(0,0,0,0.04)` |
| **Hover** | Shadow deepens to `0 2px 8px rgba(0,0,0,0.08)`. No other change. |
| **Done** | Opacity 0.5. Title gets `text-decoration: line-through` in `#9ca3af`. Badges desaturate. |
| **Done:hover** | Opacity restores to 1.0 (allows reading details). |
| **P1 (urgent)** | Left border accent: 3px solid `#ef4444`. Adds visual urgency without coloring the whole card. |

---

## 2. Color System

All colors are defined as CSS custom properties for consistency and future theming.

### CSS Custom Properties

```css
:root {
    /* --- Category colors --- */
    /* Each has a text color (for pill text) and bg color (for pill background) */
    --color-cat-bug-text: #be185d;
    --color-cat-bug-bg: #fce7f3;
    --color-cat-feature-text: #1d4ed8;
    --color-cat-feature-bg: #dbeafe;
    --color-cat-tech-debt-text: #92400e;
    --color-cat-tech-debt-bg: #fef3c7;
    --color-cat-docs-text: #065f46;
    --color-cat-docs-bg: #d1fae5;
    --color-cat-security-text: #5b21b6;
    --color-cat-security-bg: #ede9fe;
    --color-cat-infra-text: #155e75;
    --color-cat-infra-bg: #cffafe;
    --color-cat-default-text: #4b5563;
    --color-cat-default-bg: #f3f4f6;

    /* --- Priority colors --- */
    --color-pri-p1-text: #dc2626;
    --color-pri-p1-bg: #fef2f2;
    --color-pri-p1-accent: #ef4444;
    --color-pri-p2-text: #2563eb;
    --color-pri-p2-bg: #eff6ff;
    --color-pri-p3-text: #d97706;
    --color-pri-p3-bg: #fffbeb;

    /* --- Phase colors --- */
    /* Phases are intentionally grayscale to avoid competing with category/priority */
    --color-phase-text: #6b7280;
    --color-phase-bg: #f3f4f6;
    --color-phase-active-text: #4b5563;
    --color-phase-active-bg: #e5e7eb;

    /* --- Sprint indicator (outlined style — no background fill) --- */
    --color-sprint-text: #6b7280;
    --color-sprint-bg: transparent;
    --color-sprint-border: #e5e7eb;

    /* --- Column backgrounds --- */
    --color-col-backlog: #f9fafb;
    --color-col-doing: #fffbeb;
    --color-col-done: #f0fdf4;

    /* --- Chrome / UI --- */
    --color-border: #e5e7eb;
    --color-border-hover: #d1d5db;
    --color-shadow-default: rgba(0, 0, 0, 0.04);
    --color-shadow-hover: rgba(0, 0, 0, 0.08);
    --color-text-primary: #111827;
    --color-text-secondary: #6b7280;
    --color-text-muted: #9ca3af;
    --color-bg-card: #ffffff;
    --color-bg-page: #ffffff;
}
```

### Category Color Rationale

Colors shifted from the Sprint 2 spec. Key change: **use darker text on lighter backgrounds** instead of using the accent color as text. This improves readability and follows Notion's approach.

| Category | Emoji | Text | Background | Reasoning |
|----------|-------|------|------------|-----------|
| bug | (none) | `#be185d` (dark pink) | `#fce7f3` (light pink) | Bugs = pink/red family. Dark text on light bg. |
| feature | (none) | `#1d4ed8` (dark blue) | `#dbeafe` (light blue) | Features = blue. Primary work. |
| tech-debt | (none) | `#92400e` (dark amber) | `#fef3c7` (light amber) | Tech debt = amber/warning. Needs attention. |
| docs | (none) | `#065f46` (dark green) | `#d1fae5` (light green) | Docs = green. Supportive. |
| security | (none) | `#5b21b6` (dark purple) | `#ede9fe` (light purple) | Security = purple. Distinct from bug. |
| infra | (none) | `#155e75` (dark cyan) | `#cffafe` (light cyan) | Infra = cyan. Operational. |
| *(other)* | (none) | `#4b5563` (dark gray) | `#f3f4f6` (light gray) | Unknown = neutral. |

**Emoji removed from pills.** Emoji rendering is inconsistent across OS/browsers and adds visual noise. Category text alone (uppercased, in a colored pill) is sufficient. Emoji may optionally be kept in column headers or page title only.

### Priority Visual Treatment

| Priority | Pill Text | Pill BG | Left Border Accent | Meaning |
|----------|-----------|---------|-------------------|---------|
| P1 | `#dc2626` | `#fef2f2` | 3px solid `#ef4444` | Urgent. Red accent draws eye. |
| P2 | `#2563eb` | `#eff6ff` | none | Standard. Blue is neutral-professional. |
| P3 | `#d97706` | `#fffbeb` | none | Low priority. Amber = not urgent. |

---

## 3. Typography

### Font Stack

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

Streamlit uses a similar system font stack by default. No custom fonts needed.

### Type Scale

| Element | Size | Weight | Color | Line Height |
|---------|------|--------|-------|-------------|
| **Page title** | 20px | 700 | `--color-text-primary` | 1.3 |
| **Column header** | 12px | 700 (uppercase, letter-spacing 0.08em) | `--color-text-secondary` | 1.0 |
| **Column count badge** | 11px | 600 | `--color-text-secondary` | 1.0 |
| **Card title** | 14px | 600 | `--color-text-primary` | 1.35 |
| **Badge/pill text** | 11px | 600 (uppercase, letter-spacing 0.02em) | per-category/priority | 1.0 |
| **Sprint indicator** | 10px | 500 | `--color-text-muted` | 1.0 |
| **Expander trigger** | 12px | 400 | `--color-text-muted` | 1.0 |
| **Detail body text** | 13px | 400 | `--color-text-primary` | 1.5 |
| **Detail labels** | 11px | 600 | `--color-text-secondary` | 1.0 |
| **Filter labels** | 12px | 500 | `--color-text-secondary` | 1.0 |
| **Move button text** | 11px | 500 | `--color-text-secondary` | 1.0 |

### Key Typography Decisions

- **Card title at 14px** (up from 13px in current code). Linear uses 14px. This is the primary scannable element and needs to be comfortably readable.
- **Badges at 11px uppercase.** Small enough to be secondary, but uppercase + weight 600 keeps them readable. 10px (current) is too small on some displays.
- **No bold in detail body.** Only labels (like "Acceptance Criteria:") are bold. Body text is regular weight for comfortable reading.

---

## 4. Component Specs

### 4.1 Card

```css
.card {
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    box-shadow: 0 1px 2px var(--color-shadow-default);
    padding: 10px 14px;
    transition: box-shadow 0.15s ease;
}
.card:hover {
    box-shadow: 0 2px 8px var(--color-shadow-hover);
}
.card--done {
    opacity: 0.5;
}
.card--done:hover {
    opacity: 1;
}
.card--p1 {
    border-left: 3px solid var(--color-pri-p1-accent);
}
.card__title {
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-primary);
    line-height: 1.35;
    margin: 0 0 6px 0;
}
.card--done .card__title {
    text-decoration: line-through;
    color: var(--color-text-muted);
}
.card__badges {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
```

**Border radius:** 8px (up from 6px). Matches modern tools (Linear uses 8px, Notion uses 6-8px). Slightly softer.

**P1 left accent:** Inspired by Linear's urgent indicator. A colored left border is more subtle than coloring the whole card but still draws the eye when scanning a column.

### 4.2 Badge / Pill

All metadata pills share the same base shape. Color varies by type.

```css
.badge {
    display: inline-flex;
    align-items: center;
    height: 20px;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    white-space: nowrap;
}
```

| Badge Type | Text Color | Background | Extra |
|------------|-----------|------------|-------|
| Category | `--color-cat-{name}-text` | `--color-cat-{name}-bg` | — |
| Priority | `--color-pri-{level}-text` | `--color-pri-{level}-bg` | — |
| Phase | `--color-phase-text` | `--color-phase-bg` | No uppercase. Lowercase italic to differentiate from category/priority. |
| Sprint | `--color-sprint-text` | `--color-sprint-bg` | `border: 1px solid var(--color-sprint-border)`. Outlined style to be the most subtle badge. |

**Phase badge exception:** Phase uses lowercase italic text (`font-style: italic; text-transform: none`) to visually distinguish it from category and priority badges, which are uppercase. This avoids a "wall of pills" where everything looks the same.

**Sprint badge outlined:** Sprint is the least important badge. An outlined pill (transparent bg, 1px border) makes it recede visually.

### 4.3 Move Buttons

```css
.move-btn {
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 500;
    color: var(--color-text-secondary);
    background: transparent;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
}
.move-btn:hover {
    background: #f3f4f6;
    color: var(--color-text-primary);
    border-color: var(--color-border-hover);
}
```

**Style: ghost/outline.** Buttons should be visually quiet. They are actions, not content. Ghost style (transparent bg, subtle border) keeps them subordinate to card content.

**Labels:** Use directional arrows with target status name:
- From Backlog: `-> doing` `-> done`
- From Doing: `<- backlog` `-> done`
- From Done: `<- backlog` `<- doing`

**Placement:** Below the expander, full-width row. Two buttons side by side using `st.columns`.

### 4.4 Column Header

```css
.col-header {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-secondary);
    padding: 8px 12px 6px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.col-header__count {
    background: #e5e7eb;
    color: #4b5563;
    padding: 1px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
}
```

Column headers are uppercase labels like "BACKLOG", "IN PROGRESS", "DONE" followed by a count pill.

**Column background tints** (applied to the column container, not the header):

| Column | Background | Rationale |
|--------|------------|-----------|
| Backlog | `#f9fafb` (cool gray) | Neutral. Waiting. |
| In Progress | `#fffbeb` (warm cream) | Warm = active. Subtle energy. |
| Done | `#f0fdf4` (soft green) | Green = complete. Positive. |

Tints are very subtle (2-3% away from white) so cards remain the visual focus.

### 4.5 Expander (Detail View)

```css
/* Streamlit expander overrides */
.streamlit-expanderHeader {
    font-size: 12px;
    color: var(--color-text-muted);
    font-weight: 400;
}
```

**Trigger label:** The item ID (slug), e.g., `fix-auth-leak`. This doubles as a unique identifier for the item. Styled in muted gray to be unobtrusive.

**Content layout inside expander:**

```
Description paragraph(s)

**Acceptance Criteria:**
- Criterion 1
- Criterion 2

**Notes:** Note text here.

**Tags:** [tag1] [tag2] [tag3]       <- styled as small gray pills
**Depends on:** item-id-1, item-id-2

Sprint: 2          Created: 2026-03-21       Updated: 2026-03-21
^-- three-column footer row using st.columns, st.caption
```

**Content padding:** Streamlit expanders have default padding. No override needed.

### 4.6 Filter Bar

```css
.filter-bar {
    border-bottom: 1px solid var(--color-border);
    padding-bottom: 12px;
    margin-bottom: 10px;
}
```

**Layout:** Four columns using `st.columns(4)`:
1. Priority selectbox
2. Category selectbox
3. Sprint selectbox
4. Search text input

**Active filter indication:** Streamlit selectboxes show the selected value natively. For search, the text input shows the query. No additional indicator needed.

**Future enhancement (not in scope now):** Active filters could be shown as dismissible chips above the columns, similar to Notion's filter bar.

---

## 5. Interaction Patterns

### 5.1 Move Items

| Aspect | Specification |
|--------|--------------|
| **Trigger** | Two `st.button` widgets below the expander |
| **Labels** | Directional: `<- backlog`, `-> done`, etc. |
| **Placement** | Bottom of each card container, full-width row |
| **Feedback** | `st.rerun()` refreshes the board. Item appears in new column. |
| **Confirmation** | None needed. Moves are easily reversible. |

### 5.2 Expand Details

| Aspect | Specification |
|--------|--------------|
| **Trigger** | `st.expander` — native Streamlit click-to-toggle |
| **Label** | Item ID slug (e.g., `fix-auth-leak`) |
| **Animation** | Streamlit default (smooth expand/collapse) |
| **Content** | Read-only detail view (description, acceptance criteria, notes, tags, metadata) |
| **Multiple open** | Allowed. Each expander is independent. |

### 5.3 Filter

| Aspect | Specification |
|--------|--------------|
| **Controls** | `st.selectbox` for priority, category, sprint. `st.text_input` for search. |
| **Logic** | AND combination. All filters must match. |
| **Scope** | Filters apply to the Backlog column only (Doing and Done show all items). |
| **State** | `st.session_state` persists filter values across reruns. |
| **Reset** | Select the "All..." option in each selectbox. Clear the search input. |
| **Empty result** | Show "No items match filters." caption in the column. |

### 5.4 Scan Pattern

The visual hierarchy guides the user's eye:

1. **Column headers** orient: which column am I looking at?
2. **Card titles** scan: what work exists?
3. **Category pills** distinguish: is this a bug? Feature?
4. **Priority pills** triage: is this urgent?
5. **Phase pills** (if present) inform: where is this in the workflow?
6. **Expander** drills down: what are the details?
7. **Move buttons** act: move this to the next stage.

---

## 6. Implementation Notes

These are design-level notes for when this spec is implemented. No code in this document.

### Streamlit Constraints

1. **CSS injection:** All styles go into a single `<style>` block via `st.markdown`. CSS custom properties (`:root { --var: value }`) work in Streamlit's webview.
2. **Card HTML:** Each card's HTML is generated by `render_card_html()` and rendered inside `st.container(border=True)`. The container provides the card's border and padding (override via CSS).
3. **No JS hover effects:** CSS `:hover` works. CSS `transition` works. No JS-based interactions.
4. **Expander styling:** Limited. The trigger text styling can be overridden via `.streamlit-expanderHeader`. The expand/collapse icon is Streamlit-native and cannot be changed.
5. **Button styling:** All `st.button` instances share the same CSS rules unless differentiated by wrapper classes (not straightforward in Streamlit). The current approach of styling all buttons as ghost-style move buttons is acceptable because move buttons are the only buttons on the board.
6. **Column backgrounds:** Cannot directly apply a class to `st.columns`. Use `st.markdown` to inject a tinted div before the column content, or override container backgrounds globally per column position.

### Migration from Current Implementation

Key changes from the current `app.py`:

1. **Remove emoji from category pills.** Replace with uppercase text-only pills.
2. **Shift to darker text / lighter bg for pills.** Current code uses accent colors as text. New spec uses dark-on-light for readability.
3. **Add P1 left border accent.** New feature.
4. **Add done state strikethrough.** Current code uses opacity only. Add `text-decoration: line-through`.
5. **Add phase badge.** Not currently rendered. Requires adding `phase` field to BacklogItem model (or reading from YAML if already present).
6. **Increase card title to 14px.** Up from 13px.
7. **Increase badge text to 11px.** Up from 10px.
8. **Update border-radius to 8px.** Up from 6px.
9. **Update color values** to match the new CSS custom properties.
10. **Consolidate CSS** into custom property-based system for maintainability.

### Accessibility Considerations

- All color combinations meet WCAG AA contrast ratio (4.5:1 minimum for text). The dark-text-on-light-bg approach ensures this.
- Priority is communicated by both color and text label (P1/P2/P3), not color alone.
- Category is communicated by text, not color alone.
- Done state uses both opacity reduction and strikethrough, providing two visual cues.
- Move buttons have text labels, not icon-only.

---

## 7. Visual Reference (ASCII)

### Full Board Layout

```
+------------------------------------------------------------------+
|  agile-backlog . Sprint 2                                         |
+------------------------------------------------------------------+
|  Priority: [All v]  Category: [All v]  Sprint: [All v]  Search: [_____] |
+------------------------------------------------------------------+
|                                                                    |
|  BACKLOG (3)          |  IN PROGRESS (2)     |  DONE (1)          |
|  ~~~~~~~~~~~~~~~~~~~~~ | ~~~~~~~~~~~~~~~~~~~~~ | ~~~~~~~~~~~~~~~~~~~ |
|                        |                       |                    |
|  +------------------+  |  +------------------+ |  +--------------+  |
|  | Fix auth leak    |  |  | Add CLI filters  | |  | Setup repo   |  |
|  | [SECURITY] [P1]  |  |  | [FEATURE] [P2]   | |  | [INFRA] [P3] |  |
|  |  coding  S2      |  |  |  testing  S1      | |  |  S1          |  |
|  | > fix-auth-leak  |  |  | > add-cli-filter | |  | > setup-repo |  |
|  | [<-back] [->done]|  |  | [<-back] [->done]| |  | [<-back][<-do]|  |
|  +------------------+  |  +------------------+ |  +--------------+  |
|  | border-left: red |  |                       |  | opacity: 0.5 |  |
|  +------------------+  |  +------------------+ |  | strikethrough|  |
|  | Update docs      |  |  | Refactor store   | |  +--------------+  |
|  | [DOCS] [P3]      |  |  | [TECH-DEBT] [P2] | |                    |
|  |  scoping  S3     |  |  |  coding  S2       | |                    |
|  | > update-docs    |  |  | > refactor-store | |                    |
|  | [->doing] [->done]| |  | [<-back] [->done]| |                    |
|  +------------------+  |  +------------------+ |                    |
|                        |                       |                    |
+------------------------------------------------------------------+
```

### Single Card Detail (Expanded)

```
+----------------------------------------------+
|  Fix authentication leak                      |   <- 14px, weight 600
|  [SECURITY] [P1] [coding] [S2]               |   <- 11px pills
+----------------------------------------------+
|  v fix-auth-leak                              |   <- expander open
|  +-----------------------------------------+  |
|  | Current SAILPOINT_API_TOKEN is a        |  |
|  | hardcoded dummy bearer token. Need      |  |
|  | OAuth2/JWT validation for production.   |  |
|  |                                         |  |
|  | **Acceptance Criteria:**                |  |
|  | - OAuth2 token validation implemented   |  |
|  | - Static token removed from .env        |  |
|  | - Tests cover auth flow                 |  |
|  |                                         |  |
|  | **Notes:** Sprint 2 PR review flagged   |  |
|  | this as a security gap.                 |  |
|  |                                         |  |
|  | Sprint: 2    Created: 3/21   Updated: 3/21 |
|  +-----------------------------------------+  |
|  [<- backlog]  [-> done]                      |   <- ghost buttons
+----------------------------------------------+
```

---

## 8. Design Token Summary

Quick-reference table of all numeric tokens.

| Token | Value | Used By |
|-------|-------|---------|
| `--radius-card` | 8px | Card container |
| `--radius-badge` | 4px | All badge pills |
| `--radius-count` | 10px | Column count pill (fully rounded) |
| `--radius-button` | 6px | Move buttons |
| `--shadow-default` | `0 1px 2px rgba(0,0,0,0.04)` | Card rest state |
| `--shadow-hover` | `0 2px 8px rgba(0,0,0,0.08)` | Card hover state |
| `--spacing-card-padding` | 10px 14px | Card internal padding |
| `--spacing-badge-padding` | 2px 8px | Badge internal padding |
| `--spacing-badge-gap` | 6px | Between badges |
| `--spacing-card-gap` | 8px | Between cards in column |
| `--spacing-title-to-badges` | 6px | Title bottom margin |
| `--border-width` | 1px | Card border, filter bar divider |
| `--border-p1-accent` | 3px | P1 card left border |
| `--badge-height` | 20px | All badge pills |
| `--font-title` | 14px / 600 | Card title |
| `--font-badge` | 11px / 600 | Badge text |
| `--font-col-header` | 12px / 700 | Column header |
| `--font-page-title` | 20px / 700 | Page title |
| `--font-body` | 13px / 400 | Detail body |
| `--font-button` | 11px / 500 | Move button text |
| `--font-expander` | 12px / 400 | Expander trigger |
