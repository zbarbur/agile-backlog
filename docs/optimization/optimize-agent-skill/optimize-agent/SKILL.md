---
name: optimize-agent
description: >
  USE THIS when asked to review, audit, improve, or optimize CLAUDE.md,
  skills, memory files, session handoffs, or context management. Also use
  when diagnosing why the agent is guessing commands instead of using tools,
  forgetting instructions, or drifting mid-session. Covers: full setup audit,
  skill frontmatter review, context budget analysis, phrasing improvements,
  and anti-pattern detection.
---

# Agent Optimization Skill

STOP. Read this file completely before making any changes.
For the full reference guide, read `full-guide.md` in this skill directory.

## AUDIT WORKFLOW

When asked to optimize or review the setup, execute these steps IN ORDER:

### Step 1: Audit CLAUDE.md

Read the project's `CLAUDE.md` and check:

- [ ] STOP rules at both TOP and BOTTOM of file
- [ ] Skills reinforcement section listing skill names + "ALWAYS use /skill-name"
- [ ] Routing table for non-skill references (MEMORY.md, docs, handoffs)
- [ ] Token cost < 2,000 tokens (run `/context` to measure)
- [ ] Imperative, negative-framed language ("DO NOT", "NEVER", "STOP")
- [ ] Post-compact re-read instruction: "After /compact, re-read this file"
- [ ] No prose explanations — only rules, routing, and conventions
- [ ] Global CLAUDE.md exists at `~/.claude/CLAUDE.md`

**Phrasing fixes — replace weak with strong:**

| Weak (agent ignores) | Strong (agent follows) |
|----------------------|------------------------|
| You should check memory | STOP. Check MEMORY.md before ANY action. |
| Please use our reference | DO NOT guess. ALWAYS use /skill-name first. |
| Try to remember conventions | NEVER write code without reading CONVENTIONS. |
| It would be good to check | BEFORE executing: (1) Check skills (2) Use /skill-name (3) Act |

### Step 2: Audit Skills

For every SKILL.md in `.claude/skills/` and `~/.claude/skills/`:

- [ ] Has YAML frontmatter with `name` and `description`
- [ ] Description starts with "USE THIS for ANY..." + specific trigger scenarios
- [ ] Description includes "DO NOT" to block bypass behavior
- [ ] Description is concise (~200 chars) to stay within 2% context budget
- [ ] Markdown content starts with "STOP. Read this file completely before proceeding."
- [ ] Contains structured commands (tables), not prose
- [ ] Includes "Common Mistakes" section with DO NOT rules

**Run `/context` and check for "excluded skills" warning.** If skills are excluded, trim descriptions or set:
```bash
export SLASH_COMMAND_TOOL_CHAR_BUDGET=32000
```

**Description quality check — replace vague with specific:**

| Bad | Good |
|-----|------|
| Database helper tool | USE THIS for ANY database operation including queries, migrations, schema changes, seed data. DO NOT run SQL directly. |
| Deployment utility | USE THIS for ALL deployments to staging/production. Includes: build, push, rollback, health check. DO NOT use kubectl directly. |
| Testing | USE THIS before committing ANY code. Covers: unit tests, integration tests, linting, type checking. Defines exact commands and order. |

### Step 3: Audit Memory Files

Read `.claude/MEMORY.md` and any other memory files:

- [ ] Structured format (YAML, tables, key-value) — NOT prose
- [ ] Contains: current state, key decisions, open questions, tool inventory
- [ ] Concise — no duplicated information across files
- [ ] Not auto-loaded — referenced via CLAUDE.md routing table only

**Format conversion — if prose found, convert:**

```
# BAD (prose)
We decided to use PostgreSQL because it handles JSON well.

# GOOD (structured)
database: PostgreSQL
rationale: JSON support
decided: 2026-03-01
```

### Step 4: Audit Context Budget

Run `/context` on a fresh session and analyze:

| Component | Target | Action if over |
|-----------|--------|----------------|
| System prompt + CLAUDE.md | < 15% | Trim CLAUDE.md, move detail to skills/memory |
| Tool definitions + MCP | < 10% | Disable unused MCP servers (`/mcp`) |
| Skill descriptions | < 2% | Trim descriptions, check for excluded skills |
| Working conversation | 50-60% | This is your productive workspace |

**Context thresholds during sessions:**

| Usage | Status | Action |
|-------|--------|--------|
| < 50% | Healthy | Continue |
| 50-70% | Watch | Wrap up, prepare handoff |
| > 70% | Danger | /compact or end session |
| > 80% | Critical | End immediately, write handoff |

### Step 5: Audit Session Management

- [ ] Handoff template exists at `.claude/templates/handoff-template.md`
- [ ] Sessions are scoped to completable tasks
- [ ] Agent writes `SESSION_STATE.md` before ending
- [ ] `/compact` used proactively at ~70%, not reactively at ~90%
- [ ] Post-compact rule in CLAUDE.md

### Step 6: Audit Monitoring

- [ ] Status line configured (`/statusline`)
- [ ] ccstats Stop hook auto-saves session stats
- [ ] Hooks configured in `.claude/settings.json`

## ANTI-PATTERNS TO FLAG

If you find any of these during audit, flag them as HIGH PRIORITY fixes:

| Anti-Pattern | Fix |
|-------------|-----|
| Everything in CLAUDE.md | Move to skills/memory. Only rules + routing in CLAUDE.md. |
| Prose memory files | Convert to YAML/tables. |
| Polite instructions ("please", "try to") | Replace with "STOP. DO NOT. NEVER." |
| Rules only at top of file | Repeat at BOTTOM. |
| Skills without frontmatter | Add `---` YAML with name + description. |
| Vague skill descriptions | Rewrite with "USE THIS for ANY..." + "DO NOT..." |
| No skill reinforcement in CLAUDE.md | Add section listing skills + "ALWAYS use /skill-name" |
| No post-compact rule | Add "After /compact, re-read this file." |
| No monitoring hooks | Add ccstats hooks to settings.json. |

## OUTPUT FORMAT

After completing the audit, present findings as:

```
## Audit Results

### Critical (fix immediately)
1. [issue]: [specific fix with before/after]

### Important (fix soon)
1. [issue]: [specific fix]

### Nice to Have
1. [improvement]

### Token Budget Summary
- CLAUDE.md: [X] tokens ([Y]% of window)
- Skill descriptions: [X] characters ([Y]% of budget)
- Free working space: [X]%
- Excluded skills: [list or 'none']
```

## TEMPLATES

Use these when creating new files during optimization.

### CLAUDE.md Structure

```markdown
# STOP — READ BEFORE EVERY ACTION

BEFORE executing ANY command, API call, or code change:
1. Check if a SKILL exists for it (your skills are auto-loaded)
2. For non-skill references, check the ROUTING TABLE below
3. ONLY THEN proceed

DO NOT guess CLI commands. DO NOT search the web for
information that exists in our skills or reference files.
If you are about to guess, STOP. You are making a mistake.

## YOUR SKILLS (auto-discovered — use them)

You have skills for: [list names].
BEFORE running ANY command, check if a skill covers it.
DO NOT bypass skills by guessing commands directly.

## ROUTING TABLE (non-skill references)

| Need                  | Read This File                  |
|-----------------------|---------------------------------|
| Project state         | .claude/MEMORY.md               |
| Architecture          | docs/architecture.md            |
| Session continuity    | .claude/SESSION_STATE.md        |

## PROJECT

[name] — [one-line description]
Stack: [languages, frameworks, tools]

## CONVENTIONS

- [Convention 1]
- [Convention 2]

## STOP — REMINDER

Check your skills first, then the ROUTING TABLE.
After /compact, re-read this file before continuing.
```

### Skill Template

```yaml
---
name: [skill-name]
description: >
  USE THIS for [specific triggers]. Covers: [actions].
  DO NOT [bypass behavior].
---
```

```markdown
# [Skill Name]

STOP. Read this file completely before proceeding.

## Commands
| Action | Command |
|--------|---------|
| [action] | [command] |

## Common Mistakes
- DO NOT [mistake 1]
- DO NOT [mistake 2]
```

### Handoff Template

```markdown
# SESSION HANDOFF
date: [YYYY-MM-DD]
context_usage_at_end: [X%]

## Completed
- [task]

## In Progress
- [task]: [state]

## Next Steps
1. [action]

## Files Modified
- [path]: [change]
```

### ccstats Hooks

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Show stats every 50 tool uses",
        "matcher": { "tools": ["*"], "modulo": 50 },
        "hooks": [{ "type": "command", "command": "npx ccstats" }]
      }
    ],
    "Stop": [
      {
        "description": "Auto-save session stats",
        "hooks": [
          {
            "type": "command",
            "command": "mkdir -p ~/.claude/session-stats && npx ccstats -o yaml -s ~/.claude/session-stats/$(date +%Y%m%d-%H%M%S).yaml"
          }
        ]
      }
    ]
  }
}
```
