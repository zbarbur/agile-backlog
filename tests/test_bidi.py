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
