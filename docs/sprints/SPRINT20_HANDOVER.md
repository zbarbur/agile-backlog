# Sprint 20 Handover — Adoption Hardening

**Date:** 2026-03-24
**Branch:** sprint20/main
**Tests:** 216 (was 204)
**Commits:** 4 (2 features + 1 fix + 1 docs)

## Completed Tasks (5/5)

| Item | Size | Category | Tags |
|------|------|----------|------|
| CLI reference skill | S | feature | cli |
| Config file discovery (--backlog-dir) | M | feature | cli |
| Bundled skills with install-skills command | M | feature | cli, plugin |
| Delete items command | S | feature | cli |
| Split CLI and UI dependencies | S | chore | packaging |

## Key Deliverables

### CLI Reference Skill
`.claude/skills/cli-reference/SKILL.md` — documents all 16 CLI commands with flags, values, and examples. Adopting agents no longer guess syntax. Added to adoption guide skills table.

### Config File Discovery
Global `--backlog-dir` flag on the CLI group. Overrides the default `_git_root()/backlog/` resolution. Backed by `set_backlog_dir()` / `_backlog_dir_override` in yaml_store. Fixes CWD confusion when agile-backlog is installed from a different repo.

### Bundled Skills + install-skills
Pivoted from Claude Code plugin (marketplace-based) to practical approach: skills bundled as package data in `src/agile_backlog/bundled_skills/`, deployed via `agile-backlog install-skills`. Skips existing skills by default, `--force` to overwrite. Update path: `pip upgrade` then `install-skills --force`.

### Delete Command
`agile-backlog delete ID [ID...] [--yes]` — removes YAML files. Multi-ID support, confirmation prompt, path traversal guard (`is_relative_to` check). Consistent with move/edit bulk patterns.

### Split CLI/UI Dependencies
NiceGUI moved from core `dependencies` to optional `[ui]` extra. `pip install agile-backlog` is now lightweight (click + pyyaml + pydantic). `serve` command catches ImportError with helpful message. `[dev]` extra includes NiceGUI for full test suite.

## Key Decisions

1. **install-skills over Claude Code plugin** — Claude Code plugins use their own marketplace, not pip. Bundling skills as package data with a CLI deploy command is practical and works now.
2. **--backlog-dir over config discovery** — simpler than walking up directories looking for config files. Explicit override is more predictable.
3. **Path traversal guard on delete** — `resolve()` + `is_relative_to()` prevents `../` escapes. Added after code review.
4. **Package data glob `**/*`** — catches all file types, not just `.md`, future-proofing for non-markdown skill assets.

## Architecture Changes

- `yaml_store.py` — `_backlog_dir_override` global + `set_backlog_dir()` + `delete_item()` with path traversal guard
- `cli.py` — `--backlog-dir` global option, `delete` command, `install-skills` command, `serve` ImportError handling, `delete_item` import
- `pyproject.toml` — NiceGUI to `[ui]` extra, `bundled_skills/**/*` in package-data
- `.claude/skills/cli-reference/` — new skill
- `src/agile_backlog/bundled_skills/` — 9 skills bundled as package data
- `docs/CLI.md` — 4 new command sections, updated install instructions
- `README.md` — updated features, install, phases, categories

## Known Issues

- `install-skills` requires manual re-run after `pip upgrade` — not fully automatic
- `--backlog-dir` must be passed on every invocation (no config-based persistence)
- README still references Claude Code plugin install that doesn't work yet

## Lessons Learned

1. **Real-world adoption testing finds real bugs** — BigQuery-connector adoption surfaced two P1 blockers (CLI reference, CWD confusion) that weren't obvious from the agile-backlog project alone.
2. **Claude Code plugin model doesn't fit pip** — marketplace-based distribution is separate from pip. Pragmatic package-data approach works better for Python tools.
3. **Documentation gaps compound** — README was outdated since Sprint 7 (still said Streamlit). New features without doc updates create confusion for adopting agents.

## Test Coverage

- 216 tests (up from 204)
- +2 tests for backlog dir override (yaml_store + CLI)
- +4 tests for delete command
- +1 test for serve without NiceGUI
- +3 tests for install-skills
- +2 tests for backlog dir CLI flag

## Recommendations for Next Sprint

1. **Test the adoption guide end-to-end** — BigQuery-connector adoption started but wasn't completed; validate the full flow with install-skills
2. **GitHub Actions CI** (P2) — still no automated CI on push
3. **UI items backlog** — markdown comments, sprint on board cards, image paste in Add dialog, archiving (all tagged Sprint 21)
