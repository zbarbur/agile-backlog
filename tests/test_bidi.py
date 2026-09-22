# tests/test_bidi.py
# The board has to read Hebrew in order. A Hebrew title with a digit or a
# Latin token in it renders scrambled under a fixed LTR base direction; the
# fix is one CSS rule — unicode-bidi: plaintext — on every text-bearing
# element, which is what dir="auto" does, without a per-site attribute.
#
# unicode-bidi is NOT inherited. A wrapper-only rule (".mc-editable" with
# no descendant form) is a no-op: every .mc-editable site is a bare
# ui.html(...) wrapper, and the text lives in an element ui.html() creates
# one level in (components.py:445, :626), so the rule must reach the
# wrapper's descendants too. That is exactly the defect a hand-written
# selector list cannot catch — ".mc-editable" is textually present either
# way — so the wrapper-class coverage below is DERIVED from components.py
# at test time, not hand-maintained.

import re
from pathlib import Path

STYLES = Path(__file__).parent.parent / "src" / "agile_backlog" / "styles.py"
COMPONENTS = Path(__file__).parent.parent / "src" / "agile_backlog" / "components.py"

# Framework/tag selectors that carry text directly on the element itself
# (not an app-defined wrapper class), so there is no source list to derive
# them from and no descendant form is needed.
FRAMEWORK_TEXT_SELECTORS = [
    ".mc-card-row span",
    ".q-field__native",
    "textarea",
    ".nicegui-markdown",
]

# Matches the actual defect site: a class applied via .classes("mc-...")
# directly on a ui.html(...) call, e.g.
#   ui.html(f'<div ...>{safe_html(item.title)}</div>').classes("mc-editable")
# Verified against the real sites at components.py:445 and :626.
_WRAPPER_CLASS_RE = re.compile(r'ui\.html\([^\n]*\)\.classes\("(mc-[\w-]+)"\)')


def _plaintext_rule() -> str:
    css = STYLES.read_text()
    start = css.index("unicode-bidi: plaintext")
    block_start = css.rfind("{", 0, start)
    selector_start = css.rfind("}", 0, block_start) + 1
    return css[selector_start:block_start]


def _selector_present(selectors: str, selector: str) -> bool:
    """True if `selector` appears in `selectors` as a whole selector, not
    merely as a prefix of some other, longer selector (e.g. ".mc-editable"
    must not match a hypothetical ".mc-editable-foo")."""
    pattern = re.compile(r"(?<![\w-])" + re.escape(selector) + r"(?=[,\s{]|$)")
    return bool(pattern.search(selectors))


def _wrapper_classes_needing_descendant_coverage() -> set[str]:
    """Classes applied to a bare ui.html(...) wrapper in components.py."""
    return set(_WRAPPER_CLASS_RE.findall(COMPONENTS.read_text()))


def test_global_css_declares_plaintext_bidi():
    assert "unicode-bidi: plaintext" in STYLES.read_text()


def test_framework_text_selectors_are_covered():
    selectors = _plaintext_rule()
    missing = [s for s in FRAMEWORK_TEXT_SELECTORS if not _selector_present(selectors, s)]
    assert not missing, f"selectors without unicode-bidi: plaintext: {missing}"


def test_every_wrapper_class_is_covered_as_wrapper_and_descendant():
    """Derived from source, not hand-written (final-review Important 2): a
    hand-written list is textually satisfied by ".mc-editable" alone and
    stays green on the broken wrapper-only rule. Deriving the class from
    the actual ui.html(...).classes(...) call sites and requiring BOTH the
    wrapper form and the descendant form (`X` and `X *`) is what makes this
    test fail on the wrapper-only rule."""
    classes = _wrapper_classes_needing_descendant_coverage()
    assert classes, "no ui.html(...).classes('mc-...') sites found in components.py — regex is stale"

    selectors = _plaintext_rule()
    missing = []
    for cls in sorted(classes):
        if not _selector_present(selectors, f".{cls}"):
            missing.append(f".{cls}")
        if not _selector_present(selectors, f".{cls} *"):
            missing.append(f".{cls} *")
    assert not missing, f"wrapper classes missing wrapper/descendant coverage: {missing}"
