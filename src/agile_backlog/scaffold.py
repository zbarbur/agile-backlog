"""Project scaffolding for `agile-backlog init` — detection, sprint-config, skills, hooks, settings merge."""

import json
import shutil
from pathlib import Path

PACKAGE_DIR = Path(__file__).parent
HOOK_NAME = "post-tool-logger.sh"
HOOK_MATCHERS = ["Read", "Grep", "Glob", "Bash", "WebFetch", "Agent", "Edit", "Write", "Skill"]
HOOK_COMMAND = f"bash .claude/hooks/{HOOK_NAME}"
GITIGNORE_LINE = ".claude/context-logs/"
DOC_DIRS = ["docs/sprints", "docs/process", "docs/superpowers/specs", "docs/superpowers/plans"]


def detect_project(root: Path) -> dict:
    detected: dict = {
        "project_name": root.resolve().name,
        "language": None,
        "test_command": None,
        "lint_command": None,
        "format_command": None,
        "cli_command": "agile-backlog",
    }
    pyproject = root / "pyproject.toml"
    package_json = root / "package.json"
    if pyproject.exists():
        text = pyproject.read_text()
        prefix = ".venv/bin/" if (root / ".venv" / "bin").exists() else ""
        detected["language"] = "python"
        detected["cli_command"] = f"{prefix}agile-backlog"
        if "pytest" in text:
            detected["test_command"] = f"{prefix}pytest tests/ -v"
        if "ruff" in text:
            detected["lint_command"] = f"{prefix}ruff check . && {prefix}ruff format --check ."
            detected["format_command"] = f"{prefix}ruff format ."
    elif package_json.exists():
        data = json.loads(package_json.read_text())
        detected["language"] = "typescript" if (root / "tsconfig.json").exists() else "javascript"
        detected["project_name"] = data.get("name") or detected["project_name"]
        scripts = data.get("scripts", {})
        if "test" in scripts:
            detected["test_command"] = "npm test"
        if "lint" in scripts:
            detected["lint_command"] = "npm run lint"
        if "format" in scripts:
            detected["format_command"] = "npm run format"
    return detected


SPRINT_CONFIG_TEMPLATE = """\
# Project Sprint Configuration — read by all sprint skills
project_name: {project_name}
language: {language}

current_sprint: 1

# Commands
test_command: "{test_command}"
lint_command: "{lint_command}"
format_command: "{format_command}"
ci_command: "{ci_command}"

# Backlog tool
backlog_tool: agile-backlog
backlog_commands:
  list: "{cli_command} list"
  list_doing: "{cli_command} list --status doing"
  list_done: "{cli_command} list --status done"
  list_backlog: "{cli_command} list --status backlog"
  list_bugs: "{cli_command} list --category bug --status backlog"
  show: "{cli_command} show {{id}}"
  add: "{cli_command} add \\"{{title}}\\" --category {{category}} --priority {{priority}}"
  move: "{cli_command} move {{id}} --status {{status}}"
  edit: "{cli_command} edit {{id}}"
  flagged: "{cli_command} flagged"
  context_report: "{cli_command} context-report"

# Documentation paths
docs:
  handover_dir: "docs/sprints/"
  specs_dir: "docs/superpowers/specs/"
  plans_dir: "docs/superpowers/plans/"
  project_context: "docs/process/PROJECT_CONTEXT.md"
  definition_of_done: "docs/process/DEFINITION_OF_DONE.md"

# Branch conventions
branch_pattern: "sprint{{N}}/main"
commit_style: conventional

# Sprint settings
default_sprint_capacity:
  small: 3-4
  medium: 2-3
  large: 1-2
"""


def render_sprint_config(values: dict) -> str:
    return SPRINT_CONFIG_TEMPLATE.format(**values)


def scaffold_sprint_config(root: Path, values: dict, force: bool = False) -> bool:
    path = root / ".claude" / "sprint-config.yaml"
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_sprint_config(values))
    return True


def ensure_doc_dirs(root: Path) -> list[str]:
    created = []
    for rel in DOC_DIRS:
        path = root / rel
        if not path.exists():
            path.mkdir(parents=True)
            created.append(rel)
    return created


def ensure_gitignore(root: Path) -> bool:
    path = root / ".gitignore"
    lines = path.read_text().splitlines() if path.exists() else []
    if GITIGNORE_LINE in lines:
        return False
    lines.append(GITIGNORE_LINE)
    path.write_text("\n".join(lines) + "\n")
    return True


def install_hooks(root: Path, force: bool = False) -> bool:
    src = PACKAGE_DIR / "bundled_hooks" / HOOK_NAME
    dest = root / ".claude" / "hooks" / HOOK_NAME
    if dest.exists() and not force:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True


def merge_settings_hooks(root: Path) -> bool:
    path = root / ".claude" / "settings.local.json"
    if path.exists():
        try:
            settings = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"Error: {path} is not valid JSON ({exc}).\n"
                "Left it untouched — fix the file and re-run 'agile-backlog init' (it is safe to re-run)."
            ) from exc
    else:
        settings = {}
    post = settings.setdefault("hooks", {}).setdefault("PostToolUse", [])
    for entry in post:
        for hook in entry.get("hooks", []):
            if HOOK_NAME in hook.get("command", ""):
                return False
    post.append(
        {
            "matcher": "|".join(HOOK_MATCHERS),
            "hooks": [{"type": "command", "command": HOOK_COMMAND}],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n")
    return True


CLAUDE_MD_BLOCK = """\
## Commands

- **CI:** `{ci_command}`
- **Sprint config:** `.claude/sprint-config.yaml`

## Design Principles

- Research first, design second, code third
- Code review before every merge
- DRY, YAGNI, TDD

## Context

| File | Purpose |
|---|---|
| `.claude/sprint-config.yaml` | Commands, paths, sprint settings |
| `backlog/*.yaml` | Backlog items (single source of truth) |
"""


def install_skills_from_package(target_dir: Path, force: bool = False) -> tuple[list[str], list[str]]:
    skills_src = PACKAGE_DIR / "bundled_skills"
    if not skills_src.exists():
        raise FileNotFoundError("bundled skills not found in package")
    target_dir.mkdir(parents=True, exist_ok=True)
    installed, skipped = [], []
    for skill_dir in sorted(skills_src.iterdir()):
        if not skill_dir.is_dir():
            continue
        dest = target_dir / skill_dir.name
        if dest.exists() and not force:
            skipped.append(skill_dir.name)
            continue
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        installed.append(skill_dir.name)
    return installed, skipped
