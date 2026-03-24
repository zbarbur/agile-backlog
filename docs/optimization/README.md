# Claude Code Agent Optimization — Complete Bundle

Everything you need to prevent context drift, enforce skill usage, and run sprint retrospectives.

---

## Contents

```
bundle/
  README.md                          ← You are here

  docs/
    claude-code-agent-optimization-guide.md
      Full reference guide: tiered memory architecture, CLAUDE.md structure,
      skill auto-discovery, session handoffs, context management, monitoring,
      self-analysis, anti-patterns, implementation checklist, templates.

    session-analytics-implementation-spec.md
      Implementation spec for the hooks + analytics system. Hand this to
      Claude Code and ask it to implement. Covers: all hook scripts, custom
      JSONL analyzer, sprint retrospective workflow, status line setup.

  optimize-agent-skill/
    install.sh                       Run to install the /optimize-agent skill
    optimize-agent/
      SKILL.md                       The skill — audit checklists + templates
      full-guide.md                  Full guide bundled as skill reference

  hooks/
    capture-start.sh                 SessionStart: save baseline metadata
    inject-reminders.sh              UserPromptSubmit: inject skill reminders
    validate-command.sh              PreToolUse: block guessed commands
    session-report.sh                SessionEnd: generate analytics report
    settings.json.template           Hook registrations — merge into your settings

  statusline/
    statusline.sh                    Context % + model + git branch display
```

---

## Quick Start

### 1. Install the optimization skill (global)

```bash
cd optimize-agent-skill
chmod +x install.sh && ./install.sh
```

Now available in all projects as `/optimize-agent`.

### 2. Set up the status line

```bash
cp statusline/statusline.sh ~/.claude/statusline.sh
chmod +x ~/.claude/statusline.sh
```

Then in Claude Code, run `/statusline` and point it to `~/.claude/statusline.sh`.

### 3. Install hooks (per project)

```bash
# Copy hooks to your project
mkdir -p .claude/hooks
cp hooks/capture-start.sh .claude/hooks/
cp hooks/inject-reminders.sh .claude/hooks/
cp hooks/validate-command.sh .claude/hooks/
cp hooks/session-report.sh .claude/hooks/
chmod +x .claude/hooks/*.sh
```

Then merge `hooks/settings.json.template` into your `.claude/settings.json`.
If you don't have a settings.json yet, just copy the template:

```bash
cp hooks/settings.json.template .claude/settings.json
```

### 4. Customize validate-command.sh

Edit `.claude/hooks/validate-command.sh` and update `SKILL_PATTERNS` to match
your project's skill-covered domains. The default patterns are:

```
gcloud|bq |kubectl|docker compose|docker build|terraform|deploy|migrate|rollback
```

### 5. Build the JSONL analyzer

Hand `docs/session-analytics-implementation-spec.md` to Claude Code:

```
Read docs/session-analytics-implementation-spec.md and implement Part 2
(the custom JSONL analyzer) and Part 3 (the sprint retrospective script).
```

### 6. Run your first audit

```
/optimize-agent Review my current setup and apply all checklists.
```

---

## Usage

### Daily

- **Status line** shows context % at all times — compact at 70%, handoff at 80%
- **Skill reminders** injected on every prompt automatically
- **Command validation** blocks guessed commands, forces skill usage
- **Session reports** auto-generated at end of every session

### Weekly / Per Sprint

```
/sprint-retro
```

Or ask Claude Code:

```
Review session reports in ~/.claude/session-stats/ from the past week.
Identify trends in skill usage, compliance ratio, and context efficiency.
Suggest specific improvements to CLAUDE.md and skill descriptions.
```

### As Needed

```
/optimize-agent                              Full setup audit
/optimize-agent Review my CLAUDE.md          Targeted audit
/optimize-agent Why is the agent guessing?   Diagnose issues
```

---

## How It All Fits Together

```
You type a prompt
    │
    ├── UserPromptSubmit hook injects: "check skills, check memory"
    │
    ▼
Claude processes your prompt
    │
    ├── Decides to run a command
    │
    ├── PreToolUse hook checks: is this a guessed command?
    │   ├── YES → BLOCKED. "Use /skill-name instead"
    │   │         Claude reads skill, retries with correct command
    │   └── NO  → Command executes normally
    │
    ├── PostToolUse (available for linting, formatting, etc.)
    │
    ▼
Claude responds
    │
    ├── Stop (fires on every response)
    │
    ▼
Session ends
    │
    ├── SessionEnd hook runs session-report.sh
    │   ├── ccstats captures tool/message/token stats
    │   ├── Custom analyzer captures skill compliance
    │   └── Report saved to ~/.claude/session-stats/
    │
    ▼
Sprint retro (/sprint-retro)
    │
    ├── Aggregates all session reports
    ├── Identifies trends and failures
    ├── Recommends changes to CLAUDE.md + skills
    └── You apply changes → next sprint improves
```

---

## Dependencies

- **jq** — JSON parsing in bash scripts
- **python3** — for the JSONL analyzer
- **npx ccstats** — session statistics (`npm install -g ccstats` or use `npx ccstats@latest`)
- **git** — branch detection in status line
