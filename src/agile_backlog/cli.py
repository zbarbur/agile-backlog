"""Click CLI for agile-backlog."""

import json
import os
from datetime import date
from pathlib import Path

import click
import yaml

import agile_backlog.yaml_store as _yaml_store
from agile_backlog.models import BacklogItem, slugify
from agile_backlog.yaml_store import item_exists, load_all, load_item, save_item


@click.group()
def main():
    """Lightweight Kanban board tool for agentic development."""


@main.command()
@click.argument("title")
@click.option("--priority", type=click.Choice(["P0", "P1", "P2", "P3", "P4"]), default="P2", help="Priority level.")
@click.option("--category", type=click.Choice(["bug", "feature", "docs", "chore"]), required=True, help="Category.")
@click.option("--description", default="", help="Item description.")
@click.option("--sprint", "sprint_target", type=int, default=None, help="Target sprint number.")
def add(title: str, priority: str, category: str, description: str, sprint_target: int | None):
    """Create a new backlog item."""
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
@click.argument("item_id")
@click.option("--status", type=click.Choice(["backlog", "doing", "done"]), required=True)
@click.option(
    "--phase",
    type=click.Choice(["plan", "spec", "build", "review"]),
    default=None,
    help="Workflow phase.",
)
def move(item_id: str, status: str, phase: str | None):
    """Change an item's status."""
    try:
        item = load_item(item_id)
    except FileNotFoundError:
        raise SystemExit(f"Error: item '{item_id}' not found.")
    item.status = status
    if status == "doing":
        item.phase = phase or item.phase or "plan"
    elif status == "backlog":
        item.phase = None
    item.updated = date.today()
    save_item(item)
    click.echo(f"Moved {item_id} → {status}")


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
@click.argument("item_id")
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
def edit(item_id, resolve_notes: bool, **kwargs):
    """Edit fields on a backlog item."""
    try:
        item = load_item(item_id)
    except FileNotFoundError:
        raise SystemExit(f"Error: item '{item_id}' not found.")

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
@click.option("--port", default=8501, type=int, help="Port number.")
@click.option("--host", default="127.0.0.1", help="Host address.")
@click.option("--no-reload", is_flag=True, help="Disable hot reload.")
def serve(port: int, host: str, no_reload: bool):
    """Open the Kanban board in the browser."""
    import atexit

    from agile_backlog.app import run_app

    pf = _pid_file()
    pf.write_text(str(os.getpid()))
    atexit.register(lambda: pf.unlink(missing_ok=True))
    run_app(host=host, port=port, reload=not no_reload)


@main.command()
def stop():
    """Stop a running agile-backlog server."""
    if _kill_server():
        click.echo("Server stopped.")
    else:
        click.echo("No running server found.")


@main.command()
@click.option("--port", default=8501, type=int, help="Port number.")
@click.option("--host", default="127.0.0.1", help="Host address.")
@click.option("--no-reload", is_flag=True, help="Disable hot reload.")
@click.pass_context
def restart(ctx: click.Context, port: int, host: str, no_reload: bool):
    """Restart the agile-backlog server."""
    _kill_server()
    click.echo("Restarting server...")
    ctx.invoke(serve, port=port, host=host, no_reload=no_reload)
