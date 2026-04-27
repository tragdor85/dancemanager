"""Dancer CRUD operations for Dance Manager.

Provides commands to add, list, show, remove, and export dancers.
"""

import json

import click

from dancemanager.models import make_dancer_id
from dancemanager.utils import get_store


@click.group()
def dancers():
    """Dancer management commands."""
    pass


@dancers.command()
@click.argument("name")
@click.option("--team", default=None, help="Assign dancer to a team by name.")
@click.pass_context
def add(ctx, name, team):
    """Add a dancer by name, optionally assigning to a team."""
    store = get_store()
    store.execute(
        "INSERT OR REPLACE INTO dancers (id, name, team_id, class_ids, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (make_dancer_id(name), name.title(), None, json.dumps([]), ""),
    )

    if team:
        cursor = store.execute(
            "SELECT id FROM teams WHERE LOWER(name) = ?",
            (team.lower(),),
        )
        if cursor and cursor[0]:
            team_id = cursor[0][0]
            store.execute(
                "UPDATE dancers SET team_id = ? WHERE id = ?",
                (team_id, make_dancer_id(name)),
            )
            store.execute(
                "INSERT OR IGNORE INTO teams (id, name, notes) " "VALUES (?, ?, ?)",
                (team_id, team, ""),
            )
        else:
            click.echo(f"Warning: team '{team}' not found, dancer added without team.")

    store.save()
    click.echo(f"Added dancer: {name} (ID: {make_dancer_id(name)})")


@dancers.command()
@click.pass_context
def list_dancers(ctx):
    """List all dancers."""
    store = get_store()
    dancers_list = store.get_collection("dancers")

    if not dancers_list:
        click.echo("No dancers found.")
        return

    headers = ["ID", "Name", "Team ID", "Notes"]
    rows = []
    for did, dancer in sorted(dancers_list.items(), key=lambda x: x[1]["name"]):
        rows.append(
            [
                did,
                dancer["name"],
                dancer.get("team_id", "") or "",
                dancer.get("notes", ""),
            ]
        )

    click.echo(render_table(headers, rows))


@dancers.command()
@click.argument("dancer_id")
@click.pass_context
def show(ctx, dancer_id):
    """Show details for a single dancer."""
    store = get_store()
    dancer = store.get("dancers", dancer_id)

    if dancer is None:
        for did, d in store.iterate("dancers"):
            if d["name"].lower() == dancer_id.lower():
                dancer = d
                break
        if dancer is None:
            click.echo(f"Dancer not found: {dancer_id}")
            return

    click.echo(f"Name: {dancer['name']}")
    click.echo(f"Team ID: {dancer.get('team_id', '') or 'None'}")
    click.echo(f"Notes: {dancer.get('notes', '')}")


@dancers.command()
@click.argument("dancer_id")
@click.pass_context
def remove(ctx, dancer_id):
    """Remove a dancer and clean up references."""
    store = get_store()
    dancer = store.get("dancers", dancer_id)

    if dancer is None:
        for did, d in store.iterate("dancers"):
            if d["name"].lower() == dancer_id.lower():
                dancer = d
                dancer_id = did
                break
        if dancer is None:
            click.echo(f"Dancer not found: {dancer_id}")
            return

    store.execute("DELETE FROM dancers WHERE id = ?", (dancer_id,))
    store.save()

    store.execute(
        "UPDATE teams SET notes = ? WHERE id = ?",
        ("", dancer_id),
    )

    store.execute(
        "UPDATE classes SET notes = ? WHERE id = ?",
        ("", dancer_id),
    )

    store.execute(
        "UPDATE dances SET notes = ? WHERE id = ?",
        ("", dancer_id),
    )

    store.save()
    click.echo(f"Removed dancer: {dancer['name']}")


@dancers.command()
@click.option("--filepath", default="dancers.csv", help="Output CSV filepath.")
@click.pass_context
def export(ctx, filepath):
    """Export all dancers to CSV."""
    from dancemanager.utils import csv_export_dancers

    store = get_store()
    csv_export_dancers(store, filepath)
    click.echo(f"Exported dancers to {filepath}")
