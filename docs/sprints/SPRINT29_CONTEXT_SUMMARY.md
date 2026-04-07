# Sprint Context Summary — Sprint 29

## Overview

- **Total tool calls:** 751
- **Sessions:** 2
- **Read calls:** 224
- **Re-read ratio:** 78.0%
- **Estimated tokens (all tools):** 257,710

## Tool Breakdown

| Tool | Count | % | Est. Tokens |
|------|------:|--:|------------:|
| Bash | 315 | 41.9% | ~25k |
| Read | 224 | 29.8% | ~208k |
| Edit | 97 | 12.9% | ~9k |
| Grep | 68 | 9.1% | ~3k |
| Glob | 16 | 2.1% | ~320 |
| Agent | 15 | 2.0% | ~7k |
| Write | 13 | 1.7% | ~2k |
| Skill | 3 | 0.4% | ~90 |

## Read Efficiency

- **Re-read ratio:** 78.0% (Poor)
- **Top re-read files:**
  - `/Users/guyguzner/Projects/agile-backlog/src/agile_backlog/app.py` — 88 reads
  - `/Users/guyguzner/Projects/agile-backlog/src/agile_backlog/pure.py` — 15 reads
  - `/Users/guyguzner/Projects/agile-backlog/src/agile_backlog/context_report.py` — 15 reads
  - `/Users/guyguzner/Projects/agile-backlog/tests/test_pure.py` — 11 reads
  - `/Users/guyguzner/Projects/agile-backlog/tests/test_context_report.py` — 11 reads
- **Wasteful reads (identical range):**
  - `/Users/guyguzner/.claude/projects/-Users-guyguzner-Projects-agile-backlog/memory/project_sprint21_status.md` — 3 reads
  - `/Users/guyguzner/.claude/projects/-Users-guyguzner-Projects-agile-backlog/memory/MEMORY.md` — 5 reads
  - `/Users/guyguzner/Projects/agile-backlog/.claude/sprint-config.yaml` — 5 reads
  - `/Users/guyguzner/Projects/agile-backlog/.claude/hooks/post-tool-logger.sh` — 5 reads
  - `/Users/guyguzner/Projects/agile-backlog/src/agile_backlog/context_report.py` — 15 reads

## Optimization Suggestions

- High re-read ratio — consider using offset/limit for targeted reads
- Critical re-read ratio — pass file content to subagents instead of re-reading
- File `/Users/guyguzner/Projects/agile-backlog/src/agile_backlog/app.py` read 88 times — consider extracting relevant sections
