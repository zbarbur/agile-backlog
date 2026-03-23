"""CSS constants and styling for agile-backlog Mission Control dark theme."""

STATUSES = ["backlog", "doing", "done"]
LABELS = {"backlog": "BACKLOG", "doing": "IN PROGRESS", "done": "DONE"}

COLUMN_STYLES = {
    "backlog": ("background:#111116;border-radius:8px;padding:8px;", "#71717a"),
    "doing": ("background:#14130e;border:1px solid #2a2618;border-radius:8px;padding:8px;", "#ca8a04"),
    "done": ("background:#0f1210;border-radius:8px;padding:8px;", "#22c55e"),
}

# Global CSS injected into the page head
GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=IBM+Plex+Mono:wght@400;500;600;700"
    "&family=DM+Sans:wght@400;500;600;700&display=swap"
)
GLOBAL_CSS = (
    f'<link href="{GOOGLE_FONTS_URL}" rel="stylesheet">'
    + """
<style>
body {
    background: #0a0a0f !important;
    color: #e4e4e7;
    font-family: 'DM Sans', sans-serif !important;
}
.nicegui-content {
    padding: 0 !important;
}
.q-card {
    box-shadow: none !important;
}
/* Dark dropdown menus */
.q-menu {
    background: #18181b !important;
    border: 1px solid #27272a !important;
}
.q-item {
    color: #e4e4e7 !important;
}
.q-item:hover, .q-item--active {
    background: #27272a !important;
}
.q-item__label {
    color: #e4e4e7 !important;
}
/* Dark select field text */
.q-field__native, .q-field__input {
    color: #e4e4e7 !important;
}
/* Multi-select chips dark styling */
.mc-select .q-chip {
    background: rgba(59,130,246,0.12) !important;
    color: #93c5fd !important;
    font-size: 10px !important;
    height: 20px !important;
}
.mc-select .q-chip__icon {
    color: #93c5fd !important;
}
.mc-search .q-field__control {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    color: #d4d4d8 !important;
    height: 32px !important;
    min-height: 32px !important;
}
.mc-search .q-field__control:focus-within {
    border-color: #3b82f6 !important;
}
.mc-search .q-field__native {
    color: #d4d4d8 !important;
    font-size: 11px !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0 10px !important;
}
.mc-search .q-field__label {
    display: none !important;
}
.mc-search .q-field__control::before,
.mc-search .q-field__control::after {
    display: none !important;
}
.mc-select .q-field__control {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    color: #a1a1aa !important;
    min-height: 32px !important;
}
.mc-select .q-field__native,
.mc-select .q-select__dropdown-icon {
    color: #a1a1aa !important;
    font-size: 11px !important;
}
.mc-select .q-field__label {
    color: #52525b !important;
    font-size: 11px !important;
}
.mc-select .q-field__control::before,
.mc-select .q-field__control::after {
    display: none !important;
}
.mc-done-check .q-checkbox__label {
    font-size: 11px !important;
    color: #71717a !important;
}
.mc-done-check .q-checkbox__inner {
    color: #3b82f6 !important;
}
.mc-card {
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 4px;
    transition: all 0.15s;
    cursor: pointer;
}
.mc-card:hover {
    border-color: #3f3f46;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.mc-card.mc-done {
    opacity: 0.7;
    color: #71717a;
}
.mc-card.mc-done:hover {
    opacity: 1.0;
}
/* Unified card row */
.mc-card-row { transition: background 0.1s; }
.mc-card-row:hover { background: rgba(255,255,255,0.03) !important; }
.mc-card-row.mc-selected { background: rgba(59,130,246,0.06) !important; border-left-color: #3b82f6 !important; }

/* Hover move buttons */
.mc-move-buttons { display:none; position:absolute; bottom:4px; right:8px; gap:3px; align-items:center; }
.mc-card-row:hover .mc-move-buttons { display:flex; }
.mc-card-row.mc-selected .mc-move-buttons { display:none; }

/* Click-to-edit affordance */
.mc-editable { border: 1px solid transparent; border-radius: 4px; cursor: pointer; transition: border-color 0.15s; }
.mc-editable:hover { border-color: #27272a; }

/* Resize handle */
.mc-resize-handle { height: 3px; cursor: row-resize; position: relative; }
.mc-resize-handle::after {
    content: ''; position: absolute; top: 0; left: 50%;
    transform: translateX(-50%); width: 40px; height: 3px; border-radius: 2px; background: #1e1e23;
}
.mc-resize-handle:hover::after { background: #3b82f6; }

/* Drag-and-drop */
.mc-card-row[draggable="true"] { cursor: grab; }
.mc-card-row.mc-dragging { opacity: 0.4; }
.mc-board-card[draggable="true"] { cursor: grab; }
.mc-board-card.mc-dragging { opacity: 0.4; }
.mc-drop-zone.mc-drag-over {
    background: rgba(59,130,246,0.06) !important;
    outline: 2px dashed rgba(59,130,246,0.3);
    outline-offset: -2px; border-radius: 6px;
}
.mc-board-drop-zone.mc-drag-over {
    background: rgba(59,130,246,0.06) !important;
    outline: 2px dashed rgba(59,130,246,0.3);
    outline-offset: -2px; border-radius: 6px;
}
.mc-move-btn {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important;
    font-weight: 500 !important;
    padding: 2px 7px !important;
    border: 1px solid #27272a !important;
    border-radius: 4px !important;
    background: transparent !important;
    color: #52525b !important;
    cursor: pointer !important;
    transition: all 0.12s !important;
    text-transform: none !important;
    min-height: 0 !important;
    line-height: 1.2 !important;
}
.mc-move-btn:hover {
    border-color: #3f3f46 !important;
    color: #a1a1aa !important;
    background: #1e1e23 !important;
}
/* Detail modal dark styling */
.mc-detail-dialog .q-card {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    color: #e4e4e7 !important;
    max-width: 720px !important;
    width: 720px !important;
}
/* Active filter chip styling */
.mc-filter-chip {
    font-size: 10px !important;
    height: 24px !important;
}
.mc-filter-chip .q-chip__content {
    color: #93c5fd !important;
}
.mc-filter-chip .q-chip__icon--remove {
    color: #93c5fd !important;
    opacity: 0.7;
}
/* Dark form inputs for edit dialogs */
.q-field--outlined .q-field__control {
    border-color: #27272a !important;
    background: #111116 !important;
}
.q-field--outlined .q-field__control:hover {
    border-color: #3f3f46 !important;
}
.q-field--outlined.q-field--focused .q-field__control {
    border-color: #3b82f6 !important;
}
.q-textarea .q-field__native {
    color: #e4e4e7 !important;
}
.q-field__label {
    color: #71717a !important;
}
/* Dark backlog table */
.q-table { background: #18181b !important; color: #e4e4e7 !important; }
.q-table th {
    color: #a1a1aa !important; background: #111116 !important;
    font-size: 11px !important; text-transform: uppercase !important; letter-spacing: 0.05em !important;
}
.q-table td { border-color: #27272a !important; color: #d4d4d8 !important; font-size: 12px !important; }
.q-table tbody tr:hover td { background: #1e1e23 !important; }
.q-table .q-table__bottom { background: #111116 !important; color: #71717a !important; }
/* Side panel */
.mc-side-panel {
    background: #0c0c0e;
    border-left: 1px solid #1e1e23;
    overflow-y: auto;
}
.mc-side-panel::-webkit-scrollbar { width: 4px; }
.mc-side-panel::-webkit-scrollbar-thumb { background: #27272a; border-radius: 2px; }
/* Image upload widget */
.mc-upload .q-uploader__header { display: none !important; }
.mc-upload .q-uploader__list { display: none !important; }
.mc-upload { background: #18181b !important; border: 1px dashed #27272a !important;
    border-radius: 6px !important; min-height: 0 !important; }
.mc-upload .q-btn { color: #71717a !important; font-size: 10px !important; }
/* Thumbnail hover */
.mc-thumb-wrapper .mc-thumb-delete { opacity: 0; transition: opacity 0.15s; }
.mc-thumb-wrapper:hover .mc-thumb-delete { opacity: 1; }
/* Markdown rendering in dark theme */
.nicegui-markdown h1,
.nicegui-markdown h2,
.nicegui-markdown h3,
.nicegui-markdown h4,
.nicegui-markdown h5,
.nicegui-markdown h6 {
    color: #e4e4e7 !important;
    font-family: 'DM Sans', sans-serif !important;
    margin: 8px 0 4px 0 !important;
    line-height: 1.3 !important;
}
.nicegui-markdown h1 { font-size: 16px !important; font-weight: 700 !important; }
.nicegui-markdown h2 { font-size: 14px !important; font-weight: 700 !important; }
.nicegui-markdown h3 { font-size: 13px !important; font-weight: 600 !important; }
.nicegui-markdown h4,
.nicegui-markdown h5,
.nicegui-markdown h6 { font-size: 12px !important; font-weight: 600 !important; }
.nicegui-markdown p {
    color: #d4d4d8 !important;
    font-size: 12px !important;
    margin: 4px 0 !important;
    line-height: 1.5 !important;
}
.nicegui-markdown ul,
.nicegui-markdown ol {
    color: #d4d4d8 !important;
    font-size: 12px !important;
    padding-left: 18px !important;
    margin: 4px 0 !important;
}
.nicegui-markdown li {
    color: #d4d4d8 !important;
    margin-bottom: 2px !important;
}
.nicegui-markdown code {
    background: #1e1e23 !important;
    color: #93c5fd !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    padding: 1px 4px !important;
    border-radius: 3px !important;
}
.nicegui-markdown pre {
    background: #111116 !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    padding: 10px !important;
    margin: 6px 0 !important;
    overflow-x: auto !important;
}
.nicegui-markdown pre code {
    background: transparent !important;
    padding: 0 !important;
    color: #d4d4d8 !important;
    font-size: 11px !important;
}
.nicegui-markdown blockquote {
    border-left: 3px solid #3b82f6 !important;
    padding-left: 12px !important;
    margin: 6px 0 !important;
    color: #a1a1aa !important;
    font-style: italic !important;
    font-size: 12px !important;
}
.nicegui-markdown strong { color: #e4e4e7 !important; }
.nicegui-markdown em { color: #d4d4d8 !important; }
.nicegui-markdown a {
    color: #60a5fa !important;
    text-decoration: none !important;
}
.nicegui-markdown a:hover { text-decoration: underline !important; }
.nicegui-markdown hr {
    border: none !important;
    border-top: 1px solid #27272a !important;
    margin: 8px 0 !important;
}
</style>
"""
)
