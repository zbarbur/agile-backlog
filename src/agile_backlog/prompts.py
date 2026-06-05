"""Shared registry of actionable fix-prompt templates for Dashboard v2.

PURE module — no NiceGUI import, so it stays unit-testable like pure.py.
Templates receive all project/user data via the ``context`` dict and MUST NOT
read files themselves. Each rendered prompt (a) names the specific finding,
(b) inlines the relevant data, and (c) ends with a concrete ask.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    id: str
    label: str
    template: str
    required_keys: tuple[str, ...]


_TEMPLATES: tuple[PromptTemplate, ...] = (
    PromptTemplate(
        id="claude_md_audit",
        label="Audit CLAUDE.md",
        template=(
            "Audit the project memory file `{file_path}` ({line_count} lines, ~{token_estimate} tokens).\n\n"
            "Findings to investigate:\n{findings}\n\n"
            "For each finding, decide whether the instruction is load-bearing, redundant, or stale. "
            "Propose concrete edits (remove / merge / tighten) and explain the token impact of each. "
            "Audit the file now and report your recommendations."
        ),
        required_keys=("file_path", "line_count", "token_estimate", "findings"),
    ),
    PromptTemplate(
        id="claude_md_trim",
        label="Trim CLAUDE.md",
        template=(
            "The memory file `{file_path}` is ~{token_estimate} tokens, over the {target_tokens}-token budget.\n\n"
            "Sections present: {sections}\n\n"
            "Trim it to fit the budget without losing any load-bearing instruction: collapse duplicate "
            "warnings, fold examples into rules, and cut prose that the model already infers. "
            "Rewrite the file to under {target_tokens} tokens and show a before/after token count."
        ),
        required_keys=("file_path", "token_estimate", "target_tokens", "sections"),
    ),
    PromptTemplate(
        id="skill_description_audit",
        label="Audit skill description",
        template=(
            "The skill `{skill_name}` scored {score}/100 on description quality.\n\n"
            'Current description: "{description}"\n'
            "Issues: {issues}\n\n"
            "A strong description names a clear TRIGGER (when to use), concrete examples, and is long enough "
            "to disambiguate. Rewrite the `{skill_name}` description to fix these issues and explain why each "
            "change improves trigger accuracy."
        ),
        required_keys=("skill_name", "description", "score", "issues"),
    ),
    PromptTemplate(
        id="skill_unused_analysis",
        label="Analyze unused skill",
        template=(
            "The skill `{skill_name}` has been invoked {invocation_count} times across {total_sessions} "
            "sessions in the {days_since_install} days since it was installed.\n\n"
            "Analyze why it is going unused: is the description failing to trigger, is the capability "
            "redundant with another skill, or is it genuinely not needed? Recommend whether to rewrite "
            "the trigger, merge it, or remove `{skill_name}`, and justify the call."
        ),
        required_keys=("skill_name", "invocation_count", "days_since_install", "total_sessions"),
    ),
    PromptTemplate(
        id="hook_coverage_gap",
        label="Fix hook coverage gap",
        template=(
            "Coverage gap on the `{event}` event for tool `{tool}`: {gap}\n\n"
            "Existing hooks: {existing_hooks}\n\n"
            "Design a `{event}` hook for `{tool}` that closes this gap. Provide the exact settings.json "
            "hook config and the script/command it runs, then recommend whether to enforce or block."
        ),
        required_keys=("event", "tool", "gap", "existing_hooks"),
    ),
    PromptTemplate(
        id="permission_consolidate",
        label="Consolidate permissions",
        template=(
            "These permissions in `{scope}` overlap and can be consolidated:\n{permissions}\n\n"
            "Suggested consolidation: {suggestion}\n\n"
            "Verify the suggestion is safe (no broadening beyond intent), then rewrite the permission list "
            "in `{scope}` to the consolidated form and show the exact before/after entries."
        ),
        required_keys=("scope", "permissions", "suggestion"),
    ),
    PromptTemplate(
        id="context_budget_check",
        label="Check context budget",
        template=(
            "The session is using ~{current_tokens} tokens against a {budget_tokens}-token budget.\n\n"
            "Top consumers:\n{top_consumers}\n\n"
            "Analyze what is inflating the context and recommend specific reductions (avoid re-reads, use "
            "targeted offset/limit reads, drop stale file contents). Propose a plan to get back under "
            "{budget_tokens} tokens."
        ),
        required_keys=("current_tokens", "budget_tokens", "top_consumers"),
    ),
    PromptTemplate(
        id="re_read_waste_fix",
        label="Fix re-read waste",
        template=(
            "The file `{file_path}` was read {read_count} times in one session, wasting ~{wasted_tokens} "
            "tokens.\n\n"
            "Sessions affected: {sessions}\n\n"
            "Diagnose why `{file_path}` keeps getting re-read (missing memory of prior read, no targeted "
            "offset/limit, editing-then-verifying). Recommend a concrete fix — a CLAUDE.md rule, a "
            "PreToolUse hook, or a workflow change — to eliminate the repeated reads."
        ),
        required_keys=("file_path", "read_count", "wasted_tokens", "sessions"),
    ),
)

_REGISTRY: dict[str, PromptTemplate] = {t.id: t for t in _TEMPLATES}


def list_templates() -> list[PromptTemplate]:
    return list(_REGISTRY.values())


def get_prompt(template_id: str, context: dict) -> str:
    tmpl = _REGISTRY.get(template_id)
    if tmpl is None:
        known = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown prompt template id {template_id!r}. Known ids: {known}.")
    missing = [k for k in tmpl.required_keys if k not in context]
    if missing:
        raise KeyError(f"Prompt template {template_id!r} is missing required context key(s): {', '.join(missing)}.")
    return tmpl.template.format(**context)
