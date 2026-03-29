"""Click CLI for agile-backlog."""

import json
import os
from datetime import date
from pathlib import Path

import click
import yaml

import agile_backlog.yaml_store as _yaml_store
from agile_backlog.config import get_context_logs_dir, get_current_sprint, get_serve_port
from agile_backlog.context_report import generate_sprint_report
from agile_backlog.models import BacklogItem, slugify
from agile_backlog.yaml_store import delete_item, item_exists, load_all, load_item, save_item


@click.group()
@click.option(
    "--backlog-dir", "backlog_dir", type=click.Path(exists=False), default=None, help="Override backlog directory path."
)
def main(backlog_dir: str | None):
    """Lightweight Kanban board tool for agentic development."""
    if backlog_dir:
        from agile_backlog.yaml_store import set_backlog_dir

        set_backlog_dir(Path(backlog_dir))


@main.command()
@click.argument("title_pos", required=False, default=None, metavar="TITLE")
@click.option("--title", "title_opt", default=None, help="Item title (alternative to positional argument).")
@click.option("--priority", type=click.Choice(["P0", "P1", "P2", "P3", "P4"]), default="P2", help="Priority level.")
@click.option("--category", type=click.Choice(["bug", "feature", "docs", "chore"]), required=True, help="Category.")
@click.option("--description", default="", help="Item description.")
@click.option("--sprint", "sprint_target", type=int, default=None, help="Target sprint number.")
def add(
    title_pos: str | None,
    title_opt: str | None,
    priority: str,
    category: str,
    description: str,
    sprint_target: int | None,
):
    """Create a new backlog item."""
    if title_pos and title_opt:
        raise click.UsageError("Cannot specify both positional TITLE and --title option.")
    title = title_pos or title_opt
    if not title:
        raise click.UsageError("Missing title. Provide as positional argument or --title option.")
    item_id = slugify(title)

    # Handle slug collision
    if item_exists(item_id):
        n = 2
        while item_exists(f"{item_id}-{n}"):
            n += 1
        item_id = f"{item_id}-{n}"

    item = BacklogItem(
        id=item_id,
        title=title,
        priority=priority,
        category=category,
        description=description,
        sprint_target=sprint_target,
    )
    save_item(item)
    click.echo(f"Created: {item_id}")


@main.command("list")
@click.option("--status", type=click.Choice(["backlog", "doing", "done"]), default=None)
@click.option("--priority", type=click.Choice(["P0", "P1", "P2", "P3", "P4"]), default=None)
@click.option("--category", type=click.Choice(["bug", "feature", "docs", "chore"]), default=None)
@click.option("--sprint", "sprint_target", type=int, default=None)
@click.option("--tags", multiple=True, help="Filter by tag (items matching ANY tag shown).")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON.")
def list_items(
    status: str | None,
    priority: str | None,
    category: str | None,
    sprint_target: int | None,
    tags: tuple,
    output_json: bool,
):
    """List backlog items with optional filters."""
    items = load_all()

    if status:
        items = [i for i in items if i.status == status]
    if priority:
        items = [i for i in items if i.priority == priority]
    if category:
        items = [i for i in items if i.category == category]
    if sprint_target is not None:
        items = [i for i in items if i.sprint_target == sprint_target]
    if tags:
        items = [i for i in items if set(tags) & set(i.tags)]

    if output_json:
        click.echo(json.dumps([item.to_dict() for item in items], indent=2))
        return

    if not items:
        click.echo("No items found.")
        return

    click.echo(f"{'ID':<30} {'Title':<30} {'Status':<10} {'Pri':<5} {'Category':<15} {'Phase':<10} {'Sprint':<7}")
    click.echo("-" * 107)
    for item in items:
        phase = item.phase or "-"
        sprint = str(item.sprint_target) if item.sprint_target is not None else "-"
        row = f"{item.id:<30} {item.title:<30} {item.status:<10} {item.priority:<5} {item.category:<15}"
        click.echo(f"{row} {phase:<10} {sprint:<7}")


@main.command()
@click.argument("item_ids", nargs=-1, required=True)
@click.option("--status", type=click.Choice(["backlog", "doing", "done"]), required=True)
@click.option(
    "--phase",
    type=click.Choice(["plan", "spec", "build", "review"]),
    default=None,
    help="Workflow phase.",
)
@click.option("--sprint", "sprint_target", type=int, default=None, help="Set sprint target.")
def move(item_ids: tuple[str, ...], status: str, phase: str | None, sprint_target: int | None):
    """Change an item's status (accepts multiple IDs)."""
    errors = False
    for item_id in item_ids:
        try:
            item = load_item(item_id)
        except FileNotFoundError:
            click.echo(f"Error: item '{item_id}' not found.", err=True)
            errors = True
            continue
        item.status = status
        if status == "doing":
            item.phase = phase or item.phase or "plan"
        elif status == "backlog":
            item.phase = None
        if sprint_target is not None:
            item.sprint_target = sprint_target
        item.updated = date.today()
        save_item(item)
        click.echo(f"Moved {item_id} → {status}")
    if errors:
        raise SystemExit(1)


@main.command()
@click.argument("item_id")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON.")
def show(item_id: str, output_json: bool):
    """Show full details for a backlog item."""
    try:
        item = load_item(item_id)
    except FileNotFoundError:
        raise SystemExit(f"Error: item '{item_id}' not found.")

    if output_json:
        click.echo(json.dumps(item.to_dict(), indent=2))
        return

    click.echo(f"ID:          {item.id}")
    click.echo(f"Title:       {item.title}")
    click.echo(f"Status:      {item.status}")
    click.echo(f"Priority:    {item.priority}")
    click.echo(f"Category:    {item.category}")
    click.echo(f"Sprint:      {item.sprint_target or 'unplanned'}")
    click.echo(f"Created:     {item.created}")
    click.echo(f"Updated:     {item.updated}")
    if item.phase:
        click.echo(f"Phase:       {item.phase}")
    if item.design_reviewed:
        click.echo("Design reviewed: yes")
    if item.code_reviewed:
        click.echo("Code reviewed:   yes")
    if item.tags:
        click.echo(f"Tags:        {', '.join(item.tags)}")
    if item.depends_on:
        click.echo(f"Depends on:  {', '.join(item.depends_on)}")
    if item.goal:
        click.echo(f"Goal:        {item.goal}")
    if item.complexity:
        click.echo(f"Complexity:  {item.complexity}")
    if item.technical_specs:
        click.echo("\nTechnical Specs:")
        for spec in item.technical_specs:
            click.echo(f"  - {spec}")
    if item.description:
        click.echo(f"\n{item.description}")
    if item.acceptance_criteria:
        click.echo("\nAcceptance Criteria:")
        for ac in item.acceptance_criteria:
            click.echo(f"  - {ac}")
    if item.test_plan:
        click.echo("\nTest Plan:")
        for tp in item.test_plan:
            click.echo(f"  - {tp}")
    if item.notes:
        click.echo(f"\nNotes:\n{item.notes}")
    if item.comments:
        click.echo("\nComments:")
        for n in item.comments:
            flag_marker = " [FLAGGED]" if n.get("flagged") else ""
            resolved_marker = " [resolved]" if n.get("resolved") else ""
            click.echo(f"  - {n['text']} ({n['created']}){flag_marker}{resolved_marker}")


@main.command()
@click.argument("item_ids", nargs=-1, required=True)
@click.option("--yes", "skip_confirm", is_flag=True, help="Skip confirmation prompt.")
def delete(item_ids: tuple[str, ...], skip_confirm: bool):
    """Delete backlog items (accepts multiple IDs)."""
    if not skip_confirm:
        names = ", ".join(item_ids)
        if not click.confirm(f"Delete {len(item_ids)} item(s): {names}?"):
            click.echo("Aborted.")
            return
    errors = False
    for item_id in item_ids:
        try:
            delete_item(item_id)
            click.echo(f"Deleted: {item_id}")
        except FileNotFoundError:
            click.echo(f"Error: item '{item_id}' not found.", err=True)
            errors = True
    if errors:
        raise SystemExit(1)


@main.command()
@click.argument("item_ids", nargs=-1, required=True)
@click.option("--title", default=None)
@click.option("--priority", type=click.Choice(["P0", "P1", "P2", "P3", "P4"]), default=None)
@click.option("--category", type=click.Choice(["bug", "feature", "docs", "chore"]), default=None)
@click.option("--description", default=None)
@click.option("--sprint", "sprint_target", type=int, default=None)
@click.option("--goal", default=None)
@click.option("--complexity", type=click.Choice(["S", "M", "L"]), default=None)
@click.option("--technical-specs", "technical_specs", multiple=True, help="Technical spec (repeatable).")
@click.option("--acceptance-criteria", "acceptance_criteria", multiple=True, help="DoD criterion (repeatable).")
@click.option("--test-plan", "test_plan", multiple=True, help="Test plan item (repeatable).")
@click.option(
    "--phase",
    type=click.Choice(["plan", "spec", "build", "review"]),
    default=None,
)
@click.option("--design-reviewed", "design_reviewed", is_flag=True, default=None, help="Mark design as reviewed.")
@click.option("--code-reviewed", "code_reviewed", is_flag=True, default=None, help="Mark code as reviewed.")
@click.option("--tags", multiple=True)
@click.option("--depends-on", "depends_on", multiple=True)
@click.option("--notes", default=None)
@click.option(
    "--resolve-notes", "resolve_notes", is_flag=True, default=False, help="Mark all flagged notes as resolved."
)
def edit(item_ids: tuple[str, ...], resolve_notes: bool, **kwargs):
    """Edit fields on a backlog item (accepts multiple IDs)."""
    errors = False
    for item_id in item_ids:
        try:
            item = load_item(item_id)
        except FileNotFoundError:
            click.echo(f"Error: item '{item_id}' not found.", err=True)
            errors = True
            continue

        for field, value in kwargs.items():
            if value is not None and value != ():
                if isinstance(value, tuple):
                    setattr(item, field, list(value))
                else:
                    setattr(item, field, value)

        if resolve_notes:
            for n in item.comments:
                if n.get("flagged"):
                    n["resolved"] = True

        save_item(item)
        click.echo(f"Updated: {item_id}")
    if errors:
        raise SystemExit(1)


@main.command()
@click.argument("item_id")
@click.argument("text")
@click.option("--flag", is_flag=True, help="Flag this note for agent attention.")
def note(item_id: str, text: str, flag: bool):
    """Add a note to a backlog item."""
    try:
        item = load_item(item_id)
    except FileNotFoundError:
        raise SystemExit(f"Error: item '{item_id}' not found.")
    item.comments.append(
        {
            "text": text,
            "flagged": flag,
            "resolved": False,
            "created": str(date.today()),
            "author": "agent",
        }
    )
    save_item(item)
    click.echo(f"Note added to {item_id}" + (" [FLAGGED]" if flag else ""))


@main.command()
@click.option("--json", "output_json", is_flag=True, help="Output as JSON.")
def flagged(output_json: bool):
    """List items with unresolved flagged notes."""
    items = load_all()
    flagged_items = [i for i in items if any(n.get("flagged") and not n.get("resolved") for n in i.comments)]

    if output_json:
        result = [
            {
                "id": item.id,
                "title": item.title,
                "status": item.status,
                "flagged_notes": [n for n in item.comments if n.get("flagged") and not n.get("resolved")],
            }
            for item in flagged_items
        ]
        click.echo(json.dumps(result, indent=2))
        return

    if not flagged_items:
        click.echo("No flagged notes.")
        return
    for item in flagged_items:
        click.echo(f"\n{item.id} ({item.status}):")
        for n in item.comments:
            if n.get("flagged") and not n.get("resolved"):
                click.echo(f"  🚩 {n['text']} ({n['created']})")


@main.command("resolve-note")
@click.argument("item_id")
@click.argument("note_index", type=int)
def resolve_note(item_id: str, note_index: int):
    """Resolve a specific note by index (0-based)."""
    try:
        item = load_item(item_id)
    except FileNotFoundError:
        raise SystemExit(f"Error: item '{item_id}' not found.")
    if note_index < 0 or note_index >= len(item.comments):
        raise SystemExit(f"Error: note index {note_index} out of range (item has {len(item.comments)} notes).")
    item.comments[note_index]["resolved"] = True
    save_item(item)
    click.echo(f"Resolved note {note_index} on {item_id}")


@main.command("set-sprint")
@click.argument("number", type=int)
def set_sprint(number: int):
    """Set the current sprint number."""
    from agile_backlog.config import set_current_sprint

    set_current_sprint(number)
    click.echo(f"Current sprint set to {number}")


@main.command("install-skills")
@click.option("--target", default=".claude/skills", help="Target directory for skills.")
@click.option("--force", is_flag=True, help="Overwrite existing skills.")
def install_skills(target: str, force: bool):
    """Install bundled sprint skills into the current project."""
    import shutil

    skills_src = Path(__file__).parent / "bundled_skills"
    if not skills_src.exists():
        raise SystemExit("Error: bundled skills not found in package.")

    target_dir = Path(target)
    target_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    skipped = []
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

    if installed:
        click.echo(f"Installed {len(installed)} skill(s): {', '.join(installed)}")
    if skipped:
        click.echo(f"Skipped {len(skipped)} existing skill(s): {', '.join(skipped)} (use --force to overwrite)")
    if not installed and not skipped:
        click.echo("No skills found to install.")


@main.command("sprint-status")
@click.option("--sprint", "sprint_number", type=int, default=None, help="Sprint number (default: current sprint).")
def sprint_status(sprint_number: int | None):
    """Show current sprint items grouped by phase."""
    target = sprint_number if sprint_number is not None else get_current_sprint()
    if target is None:
        raise SystemExit("Error: no current sprint set. Use 'set-sprint' or pass --sprint N.")

    items = [i for i in load_all() if i.sprint_target == target]
    if not items:
        click.echo(f"No items found for sprint {target}.")
        return

    phases = ["plan", "spec", "build", "review"]
    no_phase = [i for i in items if not i.phase or i.phase not in phases]
    done_items = [i for i in items if i.status == "done"]

    click.echo(f"Sprint {target} — {len(items)} items\n")

    for phase in phases:
        phase_items = [i for i in items if i.phase == phase]
        if not phase_items:
            continue
        click.echo(f"  {phase} ({len(phase_items)}):")
        for item in phase_items:
            click.echo(f"    {item.id:<50} {item.title}")

    if done_items:
        click.echo(f"  done ({len(done_items)}):")
        for item in done_items:
            click.echo(f"    {item.id:<50} {item.title}")

    if no_phase:
        click.echo(f"  unphased ({len(no_phase)}):")
        for item in no_phase:
            click.echo(f"    {item.id:<50} {item.title}")

    done_count = len(done_items)
    click.echo(f"\nProgress: {done_count}/{len(items)} complete")


@main.command()
@click.option("--sprint", "sprint_number", type=int, default=None, help="Sprint number (default: current sprint).")
def validate(sprint_number: int | None):
    """Check sprint items have required spec fields."""
    target = sprint_number if sprint_number is not None else get_current_sprint()
    if target is None:
        raise SystemExit("Error: no current sprint set. Use 'set-sprint' or pass --sprint N.")

    items = [i for i in load_all() if i.sprint_target == target]
    if not items:
        click.echo(f"No items found for sprint {target}.")
        raise SystemExit(0)

    any_fail = False
    for item in items:
        missing = []
        if not item.goal:
            missing.append("goal")
        if not item.complexity:
            missing.append("complexity")
        if len(item.acceptance_criteria) < 2:
            missing.append(f"acceptance_criteria (need >=2, have {len(item.acceptance_criteria)})")
        if len(item.technical_specs) < 1:
            missing.append(f"technical_specs (need >=1, have {len(item.technical_specs)})")

        if missing:
            any_fail = True
            click.echo(f"FAIL  {item.id}")
            for m in missing:
                click.echo(f"        missing: {m}")
        else:
            click.echo(f"PASS  {item.id}")

    if any_fail:
        raise SystemExit(1)


@main.command()
@click.option("--dry-run", is_flag=True, help="Show changes without applying them")
def migrate(dry_run: bool):
    """Migrate YAML files to new schema (categories, comments field)."""
    items = load_all()
    changes = []
    for item in items:
        path = _yaml_store.get_backlog_dir() / f"{item.id}.yaml"
        raw = yaml.safe_load(path.read_text())
        item_changes = []

        # Check category migration
        old_cat = raw.get("category", "")
        if old_cat != item.category:
            item_changes.append(f"category: {old_cat} → {item.category}")

        # Check agent_notes → comments
        if "agent_notes" in raw:
            item_changes.append("agent_notes → comments")

        # Check tags added by migration
        old_tags = set(raw.get("tags", []))
        new_tags = set(item.tags)
        added_tags = new_tags - old_tags
        if added_tags:
            item_changes.append(f"tags added: {', '.join(added_tags)}")

        if item_changes:
            changes.append((item.id, item_changes))
            if not dry_run:
                save_item(item)

    if not changes:
        click.echo("No migrations needed.")
        return

    for item_id, item_changes in changes:
        click.echo(f"\n{item_id}:")
        for change in item_changes:
            click.echo(f"  {change}")

    if dry_run:
        click.echo(f"\n{len(changes)} item(s) would be migrated. Run without --dry-run to apply.")
    else:
        click.echo(f"\n{len(changes)} item(s) migrated.")


@main.command("context-report")
@click.option("--log-dir", default=None, help="Directory with session tool logs (default: from config)")
@click.option("--output-dir", default="docs/sprints", help="Output directory for report")
@click.option("--sprint", required=True, type=int, help="Sprint number")
def context_report(log_dir, output_dir, sprint):
    """Generate a sprint context report from session read logs."""
    if log_dir is None:
        log_dir = str(get_context_logs_dir())
    report_path = generate_sprint_report(Path(log_dir), Path(output_dir), sprint)
    click.echo(f"Report generated: {report_path}")


def _pid_file() -> Path:
    """Return path to the server PID file."""
    return _yaml_store.get_backlog_dir().parent / ".agile-backlog.pid"


def _kill_server() -> bool:
    """Kill a running server and its child processes. Returns True if a process was killed."""
    import signal

    pf = _pid_file()
    if not pf.exists():
        return False
    pid = int(pf.read_text().strip())
    pf.unlink()
    try:
        # Kill the entire process group (parent + uvicorn workers)
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        return True
    except (ProcessLookupError, PermissionError):
        # Fallback: kill just the parent
        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except ProcessLookupError:
            return False


@main.command()
@click.option("--port", default=None, type=int, help="Port number (default: from sprint-config.yaml or 8501).")
@click.option("--host", default="127.0.0.1", help="Host address.")
@click.option("--reload", is_flag=True, help="Enable hot reload (dev mode).")
def serve(port: int | None, host: str, reload: bool):
    """Open the Kanban board in the browser."""
    if port is None:
        port = get_serve_port()
    import atexit

    try:
        from agile_backlog.app import run_app
    except ImportError:
        raise SystemExit("Error: NiceGUI is not installed. Install with: pip install agile-backlog[ui]")

    pf = _pid_file()
    pf.write_text(str(os.getpid()))
    atexit.register(lambda: pf.unlink(missing_ok=True))
    run_app(host=host, port=port, reload=reload)


@main.command()
def stop():
    """Stop a running agile-backlog server."""
    if _kill_server():
        click.echo("Server stopped.")
    else:
        click.echo("No running server found.")


@main.command()
@click.option("--port", default=None, type=int, help="Port number (default: from sprint-config.yaml or 8501).")
@click.option("--host", default="127.0.0.1", help="Host address.")
@click.option("--reload", is_flag=True, help="Enable hot reload (dev mode).")
@click.pass_context
def restart(ctx: click.Context, port: int | None, host: str, reload: bool):
    """Restart the agile-backlog server."""
    _kill_server()
    click.echo("Restarting server...")
    ctx.invoke(serve, port=port, host=host, reload=reload)
