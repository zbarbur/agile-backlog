# tests/test_prompts.py
import pytest

from agile_backlog.prompts import _REGISTRY, PromptTemplate, get_prompt, list_templates

REQUIRED_IDS = {
    "claude_md_audit",
    "claude_md_trim",
    "skill_description_audit",
    "skill_unused_analysis",
    "hook_coverage_gap",
    "permission_consolidate",
    "context_budget_check",
    "re_read_waste_fix",
}

# (template_id, context, finding_substring) — finding_substring must appear in the rendered prompt.
CASES = [
    (
        "claude_md_audit",
        {
            "file_path": "CLAUDE.md",
            "line_count": 412,
            "token_estimate": 5800,
            "findings": "Duplicate 'DO NOT RE-READ' warning appears 3 times",
        },
        "CLAUDE.md",
    ),
    (
        "claude_md_trim",
        {
            "file_path": "CLAUDE.md",
            "token_estimate": 5800,
            "target_tokens": 2000,
            "sections": "Stack, Commands, Code Style, Design Principles, Context",
        },
        "5800",
    ),
    (
        "skill_description_audit",
        {
            "skill_name": "fix-bug",
            "description": "Fix a bug.",
            "score": 35,
            "issues": "no TRIGGER keyword, no examples, description too short",
        },
        "fix-bug",
    ),
    (
        "skill_unused_analysis",
        {
            "skill_name": "report-bug",
            "invocation_count": 0,
            "days_since_install": 45,
            "total_sessions": 120,
        },
        "report-bug",
    ),
    (
        "hook_coverage_gap",
        {
            "event": "PreToolUse",
            "tool": "Read",
            "gap": "no hook blocks re-reads of already-read files",
            "existing_hooks": "PostToolUse:Bash logging only",
        },
        "PreToolUse",
    ),
    (
        "permission_consolidate",
        {
            "scope": "project .claude/settings.json",
            "permissions": "Bash(git status), Bash(git diff), Bash(git log)",
            "suggestion": "collapse to Bash(git :*)",
        },
        "git status",
    ),
    (
        "context_budget_check",
        {
            "current_tokens": 142000,
            "budget_tokens": 100000,
            "top_consumers": "components.py read 4x, app.py read 3x",
        },
        "142000",
    ),
    (
        "re_read_waste_fix",
        {
            "file_path": "src/agile_backlog/components.py",
            "read_count": 4,
            "wasted_tokens": 12000,
            "sessions": "session-abc, session-def",
        },
        "components.py",
    ),
]

# Action verbs/phrases that signal a concrete ask at the end of a prompt.
ACTION_MARKERS = (
    "audit",
    "trim",
    "rewrite",
    "analyze",
    "add",
    "consolidate",
    "reduce",
    "fix",
    "propose",
    "recommend",
    "suggest",
    "review",
    "?",
)


def test_registry_has_exactly_required_ids():
    assert set(_REGISTRY.keys()) == REQUIRED_IDS
    assert len(_REGISTRY) == 8


def test_list_templates_returns_all():
    templates = list_templates()
    assert len(templates) == 8
    assert all(isinstance(t, PromptTemplate) for t in templates)
    assert {t.id for t in templates} == REQUIRED_IDS


@pytest.mark.parametrize("template_id, context, finding", CASES)
def test_get_prompt_renders(template_id, context, finding):
    result = get_prompt(template_id, context)
    # Non-empty string
    assert isinstance(result, str)
    assert result.strip()
    # Names the specific finding / inlines data
    assert finding in result
    # Ends with a concrete ask
    tail = result.strip().lower()[-160:]
    assert any(marker in tail for marker in ACTION_MARKERS)


def test_all_required_ids_covered_by_cases():
    assert {c[0] for c in CASES} == REQUIRED_IDS


def test_unknown_template_raises():
    with pytest.raises(ValueError) as exc:
        get_prompt("does_not_exist", {})
    assert "does_not_exist" in str(exc.value)


def test_missing_required_key_raises():
    # claude_md_audit requires several keys; omit one.
    with pytest.raises((KeyError, ValueError)) as exc:
        get_prompt("claude_md_audit", {"file_path": "CLAUDE.md"})
    msg = str(exc.value)
    assert "claude_md_audit" in msg or "line_count" in msg or "missing" in msg.lower()


def test_template_objects_are_frozen():
    tmpl = next(iter(_REGISTRY.values()))
    with pytest.raises(Exception):
        tmpl.id = "mutated"  # type: ignore[misc]
