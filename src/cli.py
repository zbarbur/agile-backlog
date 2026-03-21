"""Click CLI for agile-backlog."""

from datetime import date

import click

from src.models import BacklogItem, slugify
from src.yaml_store import item_exists, load_all, load_item, save_item


@click.group()
def main():
    """Lightweight Kanban board tool for agentic development."""


@main.command()
@click.argument("title")
@click.option("--priority", type=click.Choice(["P1", "P2", "P3"]), default="P2", help="Priority level.")
@click.option("--category", required=True, help="Category tag (e.g., feature, security, docs).")
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
@click.option("--priority", type=click.Choice(["P1", "P2", "P3"]), default=None)
@click.option("--category", default=None)
@click.option("--sprint", "sprint_target", type=int, default=None)
def list_items(status: str | None, priority: str | None, category: str | None, sprint_target: int | None):
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

    if not items:
        click.echo("No items found.")
        return

    click.echo(f"{'ID':<30} {'Title':<30} {'Status':<10} {'Pri':<5} {'Category':<15}")
    click.echo("-" * 90)
    for item in items:
        click.echo(f"{item.id:<30} {item.title:<30} {item.status:<10} {item.priority:<5} {item.category:<15}")


@main.command()
@click.argument("item_id")
@click.option("--status", type=click.Choice(["backlog", "doing", "done"]), required=True)
@click.option(
    "--phase",
    type=click.Choice(["plan", "build", "review"]),
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
        item.phase = phase
    else:
        item.phase = None
    item.updated = date.today()
    save_item(item)
    click.echo(f"Moved {item_id} → {status}")


@main.command()
@click.argument("item_id")
def show(item_id: str):
    """Show full details for a backlog item."""
    try:
        item = load_item(item_id)
    except FileNotFoundError:
        raise SystemExit(f"Error: item '{item_id}' not found.")

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


@main.command()
@click.argument("item_id")
@click.option("--title", default=None)
@click.option("--priority", type=click.Choice(["P1", "P2", "P3"]), default=None)
@click.option("--category", default=None)
@click.option("--description", default=None)
@click.option("--sprint", "sprint_target", type=int, default=None)
@click.option("--goal", default=None)
@click.option("--complexity", type=click.Choice(["S", "M", "L"]), default=None)
@click.option("--technical-specs", "technical_specs", multiple=True, help="Technical spec (repeatable).")
@click.option("--acceptance-criteria", "acceptance_criteria", multiple=True, help="DoD criterion (repeatable).")
@click.option("--test-plan", "test_plan", multiple=True, help="Test plan item (repeatable).")
@click.option(
    "--phase",
    type=click.Choice(["plan", "build", "review"]),
    default=None,
)
@click.option("--design-reviewed", "design_reviewed", is_flag=True, default=None, help="Mark design as reviewed.")
@click.option("--code-reviewed", "code_reviewed", is_flag=True, default=None, help="Mark code as reviewed.")
@click.option("--tags", multiple=True)
@click.option("--depends-on", "depends_on", multiple=True)
@click.option("--notes", default=None)
def edit(item_id, **kwargs):
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

    save_item(item)
    click.echo(f"Updated: {item_id}")


@main.command()
def serve():
    """Open the Kanban board in the browser."""
    import subprocess
    import sys
    from pathlib import Path

    app_path = Path(__file__).parent / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
