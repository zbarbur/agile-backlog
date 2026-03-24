# Claude Code Agent Optimization Guide

**Memory, Skills & Context Management**
*Comprehensive Implementation Guide — March 2026*

*Preventing context drift, enforcing tool usage, and maximizing session efficiency*

---

## Table of Contents

1. [The Problem: Why Agents Forget](#1-the-problem-why-agents-forget)
2. [Architecture: Tiered Memory System](#2-architecture-tiered-memory-system)
3. [CLAUDE.md: The Foundation](#3-claudemd-the-foundation)
4. [Memory Files: Structured Knowledge](#4-memory-files-structured-knowledge)
5. [Skills: Tool Discovery & Usage](#5-skills-tool-discovery--usage)
6. [Session Handoffs: Preserving State](#6-session-handoffs-preserving-state)
7. [Context Window Management](#7-context-window-management)
8. [Monitoring & Diagnostics](#8-monitoring--diagnostics)
9. [Self-Analysis & Feedback Loops](#9-self-analysis--feedback-loops)
10. [Anti-Patterns to Avoid](#10-anti-patterns-to-avoid)
11. [Implementation Checklist](#11-implementation-checklist)
12. [Appendix: Templates](#appendix-templates)

---

## 1. The Problem: Why Agents Forget

Claude Code agents operate within a finite context window (typically 200K tokens, expandable to 1M on certain plans). As conversations grow, earlier instructions lose prominence. This manifests as the agent guessing CLI commands instead of checking reference files, searching the web for information stored locally, and admitting after the fact that it should have consulted memory.

### 1.1 Root Causes

| Cause | Symptom | Solution |
|-------|---------|----------|
| Context overflow | Agent stops following early instructions | Compact, session breaks, trim files |
| Weak instruction phrasing | Agent acknowledges rules but doesn't follow them | Imperative + negative framing |
| Poor file discoverability | Agent doesn't know which file to check | Routing table in CLAUDE.md |
| Verbose memory files | High token cost on load, crowding context | Structured data (YAML/tables), not prose |
| Too many auto-loaded files | 30%+ context consumed before first message | Lazy-load non-essential files |
| Post-compact rule loss | Agent forgets rules after /compact | Re-read directive in CLAUDE.md |

### 1.2 The Diagnostic Signal

When the agent says "I should have checked that file" — it means the instruction **exists** but isn't **prominent enough**. That's specifically a CLAUDE.md positioning or phrasing issue, not a missing rule issue.

---

## 2. Architecture: Tiered Memory System

The key principle is separation of concerns across layers, each with a different loading strategy:

| Layer | File(s) | Purpose | Loading | Token Cost |
|-------|---------|---------|---------|------------|
| **L1: Rules** | `CLAUDE.md` | Permanent rules, conventions, routing table | Auto (every session) | LOW (< 2K tokens) |
| **L2: State** | `MEMORY.md` | Project state, decisions, open items | On-demand (agent reads) | MEDIUM |
| **L3: Reference** | `.claude/skills/*/SKILL.md`, `docs/*` | Tool reference, API specs, workflows | Skills: descriptions auto-loaded; full content on-demand. Docs: on-demand via routing table. | LOW (descriptions) + VARIES (full content) |
| **L4: Handoff** | `SESSION_STATE.md` | Session continuity notes | Start of new session | LOW-MEDIUM |

> **KEY PRINCIPLE:** Skills (L3) are auto-discovered by Claude Code via frontmatter descriptions. Non-skill references (L2, L4, docs) need the routing table in CLAUDE.md. The agent should use skills for actions and the routing table for state/context.

### 2.1 Directory Structure

```
project-root/
  CLAUDE.md                          # L1: Auto-loaded rules (KEEP LEAN)
  .claude/
    MEMORY.md                        # L2: Project state & decisions
    SESSION_STATE.md                 # L4: Current session handoff
    templates/
      handoff-template.md            # Template for session handoffs
    skills/                          # L3: Auto-discovered by Claude Code
      cli-reference/SKILL.md         #   → becomes /cli-reference command
      api-reference/SKILL.md         #   → becomes /api-reference command
      testing/SKILL.md               #   → becomes /testing command
      database/SKILL.md              #   → becomes /database command
  docs/
    architecture.md                  # L3: Non-skill reference (routing table)
    decisions.md                     # L3: ADR log
```

> **NOTE:** Skills in `.claude/skills/` are project-scoped. For personal skills across all projects, use `~/.claude/skills/`. Claude Code auto-discovers both locations — you don't need to manually register them.

---

## 3. CLAUDE.md: The Foundation

This is the single most important file. It auto-loads on every session, after `/clear`, and persists across `/compact`. It must be lean, authoritative, and contain the routing table that tells the agent where everything else lives.

> **⛔ CRITICAL:** Measure your CLAUDE.md token cost with `/context` on a fresh session. If it exceeds 2,000 tokens, you are overloading it. Move detail to L2/L3 files.

### 3.1 Structure

A well-structured CLAUDE.md has six sections in this exact order:

1. **STOP Rules** (top position) — imperative, negative-framed instructions
2. **Skills Reinforcement** — list skill names, enforce usage
3. **Routing Table** — for non-skill references (memory, docs, handoffs)
4. **Project Identity** — one-line project description and stack
5. **Conventions** — coding standards, naming, patterns
6. **STOP Rules (repeated)** — same rules again at the bottom

### 3.2 Example CLAUDE.md

```markdown
# STOP — READ BEFORE EVERY ACTION

BEFORE executing ANY command, API call, or code change:
1. Check if a SKILL exists for it (your skills are auto-loaded)
2. For non-skill references, check the ROUTING TABLE below
3. ONLY THEN proceed

DO NOT guess CLI commands. DO NOT search the web for
information that exists in our skills or reference files.
DO NOT proceed without consulting memory.
If you are about to guess, STOP. You are making a mistake.

## YOUR SKILLS (auto-discovered — use them)

You have skills for: cli-reference, api-reference, testing,
database. Use /skill-name or let them auto-invoke.
DO NOT bypass them by guessing commands directly.

## ROUTING TABLE (non-skill references)

| Need                  | Read This File                  |
|-----------------------|---------------------------------|
| Project state         | .claude/MEMORY.md               |
| Architecture          | docs/architecture.md            |
| Session continuity    | .claude/SESSION_STATE.md        |

## PROJECT

[Project name] — [one-line description]
Stack: [languages, frameworks, tools]

## CONVENTIONS

- [Convention 1]
- [Convention 2]
- [Convention 3]

## STOP — REMINDER

If you are about to guess a command or API call,
STOP. Check your skills first, then the ROUTING TABLE.
After /compact, re-read this file before continuing.
```

### 3.3 Phrasing That Works

| ❌ Weak (Agent Ignores) | ✅ Strong (Agent Follows) |
|--------------------------|---------------------------|
| You should check memory before acting | STOP. Check MEMORY.md before ANY action. |
| Please use our CLI reference | DO NOT guess CLI commands. ALWAYS use /cli-reference first. |
| Try to remember our conventions | NEVER write code without first reading CONVENTIONS above. |
| It would be good to check your skills | BEFORE executing: (1) Check if a skill covers it (2) Use /skill-name (3) Only then act |

### 3.4 Hierarchical CLAUDE.md Files

Claude Code loads CLAUDE.md files from multiple levels, and they stack:

| Location | Scope | Use For |
|----------|-------|---------|
| `~/.claude/CLAUDE.md` | Global (all projects) | Universal rules: always check memory, never guess |
| `{repo}/CLAUDE.md` | Project | Project-specific routing, conventions, stack |
| `{subfolder}/CLAUDE.md` | Directory | Module-specific patterns (e.g., test dir) |

> **💡 TIP:** Put your "always check memory first" rule in the global CLAUDE.md so it applies to every project automatically.

---

## 4. Memory Files: Structured Knowledge

Memory files hold project state, decisions, and accumulated knowledge. They are NOT auto-loaded — the agent reads them on demand, guided by the routing table in CLAUDE.md.

### 4.1 Format: Structured, Not Prose

> **⚠️ WARNING:** Prose burns tokens and requires interpretation. Structured formats (YAML, Markdown tables, key-value pairs) are cheaper to parse and more reliably used by the agent.

| ❌ Bad: Prose Memory | ✅ Good: Structured Memory |
|----------------------|---------------------------|
| We decided to use PostgreSQL for the database because it handles JSON well and the team has experience with it. The API uses REST with JWT auth and we deploy to AWS ECS with Fargate. | `database: PostgreSQL (JSON support)` | 
| | `api: REST + JWT auth` |
| | `deploy: AWS ECS Fargate` |
| | `decided: 2026-03-01` |
| | `status: in-progress` |

### 4.2 MEMORY.md Template

```markdown
# PROJECT MEMORY

## Current State
phase: [current phase]
sprint: [sprint number/name]
blockers: [list or 'none']

## Key Decisions
| Date       | Decision              | Rationale          |
|------------|-----------------------|--------------------|
| 2026-03-01 | Use PostgreSQL        | JSON support       |
| 2026-03-10 | REST over GraphQL     | Team familiarity   |

## Open Questions
- [ ] Auth provider selection
- [ ] Caching strategy

## Tool Inventory
| Tool          | Command/Location              |
|---------------|-------------------------------|
| Build         | npm run build                 |
| Test          | npm run test                  |
| Deploy        | ./scripts/deploy.sh           |
| Lint          | npm run lint                  |
```

---

## 5. Skills: How They Actually Work in Claude Code

### 5.1 Auto-Discovery — What Claude Code Does for You

Claude Code has a **built-in skill discovery system**. You don't need to manually register skills or create index files. Here's what happens automatically:

1. Claude Code scans `.claude/skills/` (project) and `~/.claude/skills/` (personal)
2. It reads the YAML **frontmatter** (`name` + `description`) from each `SKILL.md`
3. All skill descriptions are loaded into context so Claude knows what's available
4. The `name` field becomes a `/slash-command` (e.g., `name: cli-reference` → `/cli-reference`)
5. Claude can **auto-invoke** skills when the `description` matches the current task

> **⚠️ IMPORTANT:** Skill descriptions consume context. The budget is 2% of context window (~4K tokens for 200K window, ~16K character fallback). Run `/context` to check if skills are being excluded due to budget overflow.

### 5.2 Skill File Structure

Every skill lives in its own directory with a `SKILL.md` file:

```
.claude/skills/
  cli-reference/
    SKILL.md          # Frontmatter + instructions (required)
    helpers.sh        # Supporting files (optional)
  api-reference/
    SKILL.md
  database/
    SKILL.md
```

The `SKILL.md` has two parts — **frontmatter** (YAML between `---` markers) and **markdown content**:

```markdown
---
name: cli-reference
description: >
  USE THIS for ANY CLI command in this project including gcloud, bq,
  npm, docker, and deployment scripts. DO NOT guess CLI syntax —
  this skill has the exact commands. Covers: build, test, deploy,
  lint, database migrations, and infrastructure operations.
---

# CLI Reference

STOP. If you found this file, read it completely before running any command.

## Build & Test
| Action         | Command                    |
|----------------|----------------------------|
| Build          | npm run build              |
| Test (unit)    | npm run test               |
| Test (e2e)     | npm run test:e2e           |
| Lint           | npm run lint               |

## Deployment
| Action         | Command                    |
|----------------|----------------------------|
| Deploy staging | ./scripts/deploy.sh staging|
| Deploy prod    | ./scripts/deploy.sh prod   |
| Rollback       | ./scripts/rollback.sh      |

## GCP / BigQuery
| Action              | Command                              |
|---------------------|--------------------------------------|
| List datasets       | bq ls --project_id=PROJECT           |
| Query table         | bq query --use_legacy_sql=false 'SQL'|
| Get IAM policy      | bq show --format=prettyjson DATASET  |
```

### 5.3 The Description Is Everything

The `description` field is the **only thing Claude sees** when deciding whether to auto-invoke a skill. The full markdown content is only loaded when the skill is actually invoked. This means:

| ❌ Bad: Vague Description | ✅ Good: Specific Description |
|---------------------------|-------------------------------|
| `description: Database helper tool` | `description: USE THIS for ANY database operation including queries, migrations, schema changes, seed data, and backup/restore. DO NOT run SQL or database CLI commands directly.` |
| `description: Deployment utility` | `description: USE THIS for ALL deployments to staging or production. Includes build, push, rollback, health check. DO NOT use kubectl or docker commands directly.` |
| `description: Testing` | `description: USE THIS before committing ANY code. Covers unit tests, integration tests, linting, type checking. This skill defines the exact commands and order to run them.` |

**Rules for effective descriptions:**
- Start with "USE THIS" + specific trigger scenarios
- Include "DO NOT" to block the bypass behavior
- List the concrete actions covered (build, test, deploy, etc.)
- Keep under ~200 characters to stay within budget
- Use action-oriented language matching what the agent "thinks" before acting

### 5.4 Auto-Invocation vs Manual Invocation

Skills can be triggered two ways:

| Method | How | When It Works |
|--------|-----|---------------|
| **Auto-invoke** | Claude reads the description and decides to use the skill | Works when description closely matches the task. Can be unreliable — see 5.5. |
| **Manual invoke** | You type `/skill-name` in the terminal | Always works. Use for critical skills you don't want the agent to skip. |

You can also control invocation behavior with frontmatter:

```yaml
---
name: deploy
description: USE THIS for all deployments...
disable-model-invocation: true   # Agent can't auto-invoke, only /deploy works
allowed-tools: Bash, Read, Write # Tools the skill can use without approval
---
```

### 5.5 The Auto-Invocation Problem (and How to Fix It)

In practice, Claude Code often **doesn't** auto-invoke skills reliably, especially:
- When the task doesn't obviously match the description keywords
- In long sessions where context is crowded
- When the agent has enough general knowledge to "just do it" without the skill

**Fix 1: Reinforce in CLAUDE.md**

Add a section listing your skills and when to use them:

```markdown
## YOUR SKILLS (auto-discovered — use them)

You have skills for: cli-reference, api-reference, testing, database.
BEFORE running ANY command, check if a skill covers it.
DO NOT bypass skills by guessing commands directly.
```

**Fix 2: Make descriptions match the agent's "thought before acting"**

The agent thinks "I need to run a deploy command" before acting. Your description should match that thought pattern — not the human category name.

**Fix 3: Use manual invocation for critical skills**

For skills the agent must never skip, tell it explicitly in CLAUDE.md:

```markdown
ALWAYS use /cli-reference before running ANY CLI command.
ALWAYS use /testing before writing or running ANY test.
```

**Fix 4: Add STOP reminders inside the skill**

Even once a skill is loaded, the agent might skim it. Start every skill's markdown content with:

```markdown
STOP. If you found this file, read it completely before proceeding.
Do NOT skip to a section — read the full reference.
```

### 5.6 Skill Locations

| Location | Scope | Use For |
|----------|-------|---------|
| `.claude/skills/<name>/SKILL.md` | Project | Project-specific tools, APIs, workflows |
| `~/.claude/skills/<name>/SKILL.md` | Personal (all projects) | Universal patterns: code review, git workflow, testing |
| `--add-dir` directories | External/shared | Team-shared skills from a shared repo |

### 5.7 Monitoring Skill Budget

If you have many skills, their descriptions may exceed the character budget and some will be silently excluded:

```
/context    # Check for "excluded skills" warning
```

The budget is 2% of context window. To override:

```bash
export SLASH_COMMAND_TOOL_CHAR_BUDGET=32000  # Double the default
```

If you're hitting the limit, trim your descriptions — remember, only the description (not the full markdown content) counts toward this budget.

---

## 6. Session Handoffs: Preserving State

The most expensive moment is starting a new session. A structured handoff minimizes cold-start cost by giving the agent exactly what it needs to resume.

### 6.1 Handoff Template

```markdown
# SESSION HANDOFF

## Last Session Summary
date: [date]
duration: [approximate]
context_usage: [% at end]

## Completed This Session
- [task 1]
- [task 2]

## In Progress
- [task]: [current state, what's done, what remains]

## Blockers / Issues
- [blocker 1]

## Next Steps (Priority Order)
1. [immediate next action]
2. [following action]

## Key Files Modified
- [file path]: [what changed]

## Decisions Made
- [decision]: [rationale]
```

### 6.2 Handoff Workflow

1. **Before ending a session:** Ask the agent to write `SESSION_STATE.md` using the template
2. **Start new session:** First message is "Read .claude/SESSION_STATE.md and continue from where we left off"
3. **After resuming:** Agent updates MEMORY.md with any new decisions from the handoff

### 6.3 /compact vs /clear vs New Session

| Action | What Happens | Rules Preserved? | When to Use |
|--------|-------------|-------------------|-------------|
| **/compact** | Summarizes conversation, frees tokens | Partially — may lose emphasis | Mid-session when context > 70% |
| **/clear** | Wipes conversation, reloads CLAUDE.md | Yes — clean reload | Fresh start within same session |
| **New session** | Fresh context, loads CLAUDE.md | Yes — clean reload | New task or after handoff |

> **⚠️ IMPORTANT:** After `/compact`, the agent may lose emphasis on your rules even though CLAUDE.md is still present. Add this to your CLAUDE.md: "After any context compaction, re-read this file before continuing."

---

## 7. Context Window Management

### 7.1 Token Budget Allocation

A healthy session should allocate context roughly as follows:

| Component | Target | Notes |
|-----------|--------|-------|
| System prompt + CLAUDE.md | < 15% | Measure with `/context` on fresh session |
| Tool definitions + MCP | < 10% | Disable unused MCP servers per session |
| Working conversation | 50-60% | Your actual productive workspace |
| Auto-compact buffer | ~15% | Reserved by Claude Code for compaction |
| Safety margin | ~10% | Headroom for large responses |

### 7.2 Context Thresholds

| Usage | Status | Action |
|-------|--------|--------|
| **< 50%** | ✅ Healthy — agent reliably follows all instructions | Continue working normally |
| **50-70%** | ⚠️ Watch — agent may start drifting on lower-priority rules | Wrap up current task, prepare handoff |
| **> 70%** | 🔴 Danger — agent forgetting early instructions | Use `/compact` or end session with handoff |
| **> 80%** | ⛔ Critical — auto-compact imminent, quality degraded | End session immediately, write handoff |

### 7.3 Reducing Initial Context Cost

1. **Audit with /context:** Run on a fresh session to see what's consuming tokens before you even start
2. **Trim CLAUDE.md:** Move everything that isn't a rule or routing entry to MEMORY.md or skill files
3. **Disable unused MCP servers:** Run `/mcp` to see per-server costs. Disable those not needed this session
4. **Use lazy loading:** Only read reference files when the task requires them, not upfront
5. **Structured over prose:** Converting prose to YAML/tables can reduce token count by 30-50%

---

## 8. Monitoring & Diagnostics

### 8.1 Built-in Tools

| Command | What It Shows |
|---------|---------------|
| **/context** | Full token breakdown by category: system prompt, tools, MCP, conversation, free space, auto-compact buffer |
| **/compact** | Compresses conversation history, frees tokens while preserving summary |
| **/clear** | Wipes conversation, reloads CLAUDE.md fresh |
| **/mcp** | Per-server MCP token costs — identify expensive plugins |
| **/statusline** | Configure persistent status bar at terminal bottom |

### 8.2 Status Line Setup

The status line provides a persistent, always-visible context usage bar. Run `/statusline` in Claude Code and ask it to configure one, or create the script manually:

```bash
#!/bin/bash
# Save as ~/.claude/statusline.sh
# chmod +x ~/.claude/statusline.sh

data=$(cat)
pct=$(echo "$data" | jq -r '.context.used_percentage // 0')
model=$(echo "$data" | jq -r '.model // "unknown"')
cost=$(echo "$data" | jq -r '.cost.total // 0')

# Build visual bar
filled=$((pct / 10))
empty=$((10 - filled))
bar=$(printf '%0.s▓' $(seq 1 $filled))
bar+=$(printf '%0.s░' $(seq 1 $empty))

# Color code: green < 50, yellow < 70, red >= 70
if [ "$pct" -lt 50 ]; then color="32"
elif [ "$pct" -lt 70 ]; then color="33"
else color="31"; fi

printf "\e[${color}m%s %d%%\e[0m | %s | $%.4f" \
  "$bar" "$pct" "$model" "$cost"
```

### 8.3 Third-Party Monitoring Tools

| Tool | Install | Best For |
|------|---------|----------|
| **ccusage** | `npx ccusage@latest` | Usage by date, session, or project. Reads local JSONL files. Great for Pro/Max plans. |
| **ccstats** | `npx ccstats` | Per-session stats: tool invocations, message counts, thinking blocks, duration. |
| **Claude-Code-Usage-Monitor** | `pip install claude-code-usage-monitor` | Real-time dashboard with burn rate, predictions, and cost tracking. |
| **cccontext** | `npx cccontext` | Real-time context monitoring, especially for parallel sessions. |
| **claude-code-log** | `pip install claude-code-log` | Converts JSONL transcripts to readable HTML for post-session review. |

---

## 9. Self-Analysis & Feedback Loops

### 9.1 Ask Claude Code to Review Itself

Claude Code can analyze its own configuration and behavior. Use these prompts directly in a session:

**Review CLAUDE.md quality:**
```
Review your CLAUDE.md and tell me:
1. Are the STOP rules prominent enough?
2. Is the routing table complete?
3. Are there any ambiguous instructions you might misinterpret?
4. What would you add to prevent yourself from guessing commands?
```

**Audit context cost:**
```
Run /context and analyze the results. Tell me:
1. What percentage is consumed before I've said anything?
2. Which components are the most expensive?
3. What can I trim or lazy-load to free space?
```

**Skill trigger review:**
```
Read all skill files in skills/ and tell me:
1. Are the trigger descriptions specific enough for you to know when to use them?
2. Which triggers are vague or overlapping?
3. What scenarios might cause you to skip checking a skill?
```

**Post-session behavior review:**
```
Look at what you did this session. Were there any moments where you:
1. Guessed a CLI command instead of checking a reference file?
2. Searched the web for something stored locally?
3. Skipped reading a skill file when you should have consulted one?
What would have prevented each case?
```

### 9.2 Automated Session Statistics with ccstats

**ccstats** reads the JSONL session logs and gives you per-session breakdowns of tool usage, message counts, and duration.

**Basic usage:**
```bash
npx ccstats                    # Stats for current directory's latest session
npx ccstats -f <session-file>  # Stats for a specific session file
```

**Output includes:**
- Total messages (user vs. assistant)
- Tool invocations count
- Thinking blocks count
- Session duration
- Working directory and git branch

### 9.3 Automated Hooks for Continuous Monitoring

Set up hooks in your Claude Code configuration (`.claude/settings.json`) to automatically collect stats:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "description": "Show stats every 50 tool uses",
        "matcher": {
          "tools": ["*"],
          "modulo": 50
        },
        "hooks": [
          {
            "type": "command",
            "command": "npx ccstats"
          }
        ]
      }
    ],
    "Stop": [
      {
        "description": "Save session stats on stop",
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

This gives you:
- **Periodic check-ins** every 50 tool uses so you can spot drift mid-session
- **Automatic archival** of every session's stats for later analysis

### 9.4 Custom JSONL Analysis

The raw session data lives in `~/.claude/projects/`. You can build (or ask Claude Code to build) a custom analysis script that tracks exactly what you care about:

**Ask Claude Code to build an analyzer:**
```
Read the JSONL files in ~/.claude/projects/ for this project.
Build me a script that reports:
1. How many times each skill file was read (cat/view of skills/*.md)
2. How many bash commands were executed that weren't in our CLI reference
3. Ratio of "check reference then act" vs "act directly"
4. Any web searches for topics covered in our local files
Save results to .claude/session-analysis.yaml
```

**What to look for in the analysis:**
- **Skill read ratio:** If skill files are read < 50% of the time they're relevant, your triggers need improvement
- **Guessed commands:** Any bash command not preceded by a skill file read is a potential failure
- **Web searches for local info:** Each one is a routing table gap
- **Context usage at point of failure:** If failures cluster above 70%, it's a context issue, not a rules issue

### 9.5 The Feedback Loop

The goal is a continuous improvement cycle:

```
Session → Auto-save stats (Stop hook)
                ↓
        Review stats periodically
                ↓
        Identify failure patterns
                ↓
        Update CLAUDE.md / skills / memory
                ↓
        Next session (improved)
```

**Weekly review prompt:**
```
Review the session stats in ~/.claude/session-stats/ from the past week.
Identify:
1. Sessions where tool usage was lowest — what went wrong?
2. Sessions where context exceeded 70% — could they have been scoped better?
3. Any repeated patterns of guessing instead of checking references?
Suggest specific changes to CLAUDE.md and skill files based on the data.
```

---

## 10. Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Do This Instead |
|-------------|-------------|-----------------|
| Everything in CLAUDE.md | Bloats auto-load cost, crowding context from the start | Only rules + routing table in CLAUDE.md. Everything else in L2/L3 files. |
| Prose-heavy memory files | High token cost, agent must interpret meaning | YAML, tables, key-value pairs. Structured data only. |
| Polite instructions | "Please try to..." is treated as optional | Imperative + negative framing: "STOP. DO NOT. NEVER." |
| Rules only at top of file | Agent weighs boundaries more; middle content fades | Critical rules at TOP and BOTTOM of CLAUDE.md |
| Long unbroken sessions | Context fills, agent drifts, quality degrades | Scope tasks to complete within a session. Break + handoff. |
| No self-check pattern | Agent has no trigger to verify its own behavior | Add: "After completing any action, verify: Did I use our custom tools?" |
| Vague skill descriptions | Agent doesn't auto-invoke because description doesn't match its "thought before acting" | Start descriptions with "USE THIS for ANY..." + list concrete scenarios + add "DO NOT guess" |
| No post-compact rule | After /compact, emphasis on rules is diluted | Add to CLAUDE.md: "After compaction, re-read this file." |
| No monitoring | Flying blind on context usage and tool compliance | Status line + ccstats hooks + periodic self-review |
| Skills without frontmatter | Skill won't be discovered or available as /command | Every SKILL.md must have `---` YAML frontmatter with `name` and `description` |
| Too many verbose skill descriptions | Exceeds 2% context budget, skills get silently excluded | Keep descriptions concise (~200 chars). Check with `/context` for excluded skills. |
| Not reinforcing skills in CLAUDE.md | Agent has skills available but doesn't think to use them | List skill names in CLAUDE.md with "ALWAYS use /skill-name before [action]" |

---

## 11. Implementation Checklist

### 11.1 CLAUDE.md Audit

- [ ] STOP rules at both TOP and BOTTOM of file
- [ ] Routing table for non-skill references (MEMORY.md, docs, etc.)
- [ ] Skills reinforcement section listing skill names + "ALWAYS use /skill-name"
- [ ] Token cost < 2,000 tokens (measure with `/context`)
- [ ] Imperative, negative-framed language ("DO NOT", "NEVER", "STOP")
- [ ] Post-compact re-read instruction included
- [ ] No prose explanations — only rules and routing

### 11.2 Memory Files Audit

- [ ] Structured format (YAML/tables) not prose
- [ ] MEMORY.md contains: current state, key decisions, open questions, tool inventory
- [ ] Files are concise — no duplicated information across files
- [ ] Not auto-loaded — referenced via routing table only

### 11.3 Skills Audit

- [ ] Every SKILL.md has YAML frontmatter with `name` and `description`
- [ ] Descriptions start with "USE THIS" + specific trigger scenarios
- [ ] Descriptions include "DO NOT" to block bypass behavior
- [ ] Descriptions are concise (~200 chars) to stay within budget
- [ ] `/context` shows no "excluded skills" warning (budget not exceeded)
- [ ] CLAUDE.md lists skill names and reinforces "ALWAYS use /skill-name before [action]"
- [ ] Each skill's markdown content starts with a STOP reminder
- [ ] Skills are in `.claude/skills/<name>/SKILL.md` (project) or `~/.claude/skills/<name>/SKILL.md` (personal)

### 11.4 Session Management Audit

- [ ] Handoff template exists and is used consistently
- [ ] Context monitoring is active (status line or `/context` habit)
- [ ] Sessions are scoped to completable tasks
- [ ] Agent is prompted to write SESSION_STATE.md before ending
- [ ] `/compact` is used proactively at ~70%, not reactively at ~90%

### 11.5 Monitoring & Feedback Audit

- [ ] Status line configured for persistent context monitoring
- [ ] ccstats Stop hook auto-saves session stats
- [ ] Weekly self-analysis review scheduled
- [ ] Custom JSONL analyzer built for skill read ratio tracking
- [ ] Feedback loop: stats → identify failures → update config → next session

### 11.6 Global Setup

- [ ] `~/.claude/CLAUDE.md` exists with universal "check memory first" rule
- [ ] Unused MCP servers disabled per project
- [ ] Hooks configured in `.claude/settings.json`

---

## Appendix: Templates

### A.1 Global CLAUDE.md (`~/.claude/CLAUDE.md`)

```markdown
# GLOBAL RULES

BEFORE any action: check if a skill exists for it.
NEVER guess CLI commands or API calls — use your skills.
NEVER search the web for information in skills or reference files.
After /compact: re-read project CLAUDE.md immediately.
After completing any action: verify you used the appropriate skill.
```

### A.2 Handoff Template (`.claude/templates/handoff-template.md`)

```markdown
# SESSION HANDOFF
date: [YYYY-MM-DD]
context_usage_at_end: [X%]

## Completed
- [task]

## In Progress
- [task]: [state]

## Blockers
- [blocker or 'none']

## Next Steps
1. [action]

## Files Modified
- [path]: [change]

## Decisions
- [decision]: [rationale]
```

### A.3 Session Resume Prompt

```
Read .claude/SESSION_STATE.md and continue from where
we left off. Confirm what you understand about the
current state before taking any action.
```

### A.4 Self-Check Rule (add to CLAUDE.md)

```markdown
## SELF-CHECK
After EVERY action, verify:
- Did I check if a skill exists for this action?
- Did I use /skill-name or let it auto-invoke?
- Did I check the routing table for non-skill references?
- Did I use our custom tools (not guessed commands)?
If any answer is NO, STOP and redo correctly.
```

### A.5 Skill Template (`.claude/skills/<name>/SKILL.md`)

```markdown
---
name: [skill-name]
description: >
  USE THIS for [specific trigger scenarios].
  Covers: [list of concrete actions].
  DO NOT [bypass behavior to block].
---

# [Skill Name]

STOP. Read this file completely before proceeding.

## Commands

| Action         | Command                    |
|----------------|----------------------------|
| [action 1]     | [exact command]            |
| [action 2]     | [exact command]            |

## Examples

[concrete usage examples with expected output]

## Common Mistakes

- DO NOT [common mistake 1]
- DO NOT [common mistake 2]
```

### A.6 ccstats Hooks (`.claude/settings.json`)

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

### A.7 Weekly Review Prompt

```
Review the session stats in ~/.claude/session-stats/ from the past week.
Identify:
1. Sessions where tool usage was lowest — what went wrong?
2. Sessions where context exceeded 70% — could they have been scoped better?
3. Any repeated patterns of guessing instead of checking references?
Suggest specific changes to CLAUDE.md and skill files based on the data.
```
