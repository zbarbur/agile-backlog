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
def move(item_id: str, status: str):
    """Change an item's status."""
    try:
        item = load_item(item_id)
    except FileNotFoundError:
        raise SystemExit(f"Error: item '{item_id}' not found.")
    item.status = status
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
    if item.tags:
        click.echo(f"Tags:        {', '.join(item.tags)}")
    if item.depends_on:
        click.echo(f"Depends on:  {', '.join(item.depends_on)}")
    if item.description:
        click.echo(f"\n{item.description}")
    if item.acceptance_criteria:
        click.echo("\nAcceptance Criteria:")
        for ac in item.acceptance_criteria:
            click.echo(f"  - {ac}")
    if item.notes:
        click.echo(f"\nNotes:\n{item.notes}")


@main.command()
def serve():
    """Open the Kanban board in the browser."""
    click.echo("Streamlit Kanban board — coming in Sprint 2.")
