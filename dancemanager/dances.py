"""Dance CRUD operations for Dance Manager.

Provides commands to add, list, show, remove, and manage dances.
"""

import json
from typing import Optional

import click

from dancemanager.models import make_dance_id
from dancemanager.utils import get_store, render_table


@click.group()
def dances():
    """Dance management commands."""
    pass


@dances.command()
@click.argument("name")
@click.argument("song_name")
@click.option("--instructor", default=None, help="Instructor by name.")
@click.option(
    "--team-ids",
    "team_ids_str",
    default="",
    help="Space-separated team IDs to include.",
)
@click.pass_context
def add(ctx, name, song_name, instructor, team_ids_str):
    """Create a dance with a song, optionally assigning an instructor and teams."""
    store = get_store()
    dances_list = store.get_collection("dances")

    dance_id = make_dance_id(name)
    if dance_id in dances_list:
        click.echo(f"Dance already exists: {name}")
        return

    team_ids = (
        [t.strip() for t in team_ids_str.split() if t.strip()] if team_ids_str else []
    )

    store.execute(
        "INSERT OR REPLACE INTO dances "
        "(id, name, song_name, instructor_id, dancer_ids, team_ids, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            dance_id,
            name.title(),
            song_name,
            None,
            json.dumps([]),
            json.dumps(team_ids),
            "",
        ),
    )

    if instructor:
        cursor = store.execute(
            "SELECT id FROM instructors WHERE LOWER(name) = ?",
            (instructor.lower(),),
        )
        if cursor and cursor[0]:
            instructor_id = cursor[0][0]
            store.execute(
                "UPDATE dances SET instructor_id = ? WHERE id = ?",
                (instructor_id, dance_id),
            )
            store.execute(
                "INSERT OR IGNORE INTO dance_assignments (dance_id, dancer_id) "
                "SELECT id, ? FROM dances WHERE id = ?",
                (dance_id, instructor_id),
            )
        else:
            click.echo(
                f"Warning: instructor '{instructor}' not found. "
                "Assign later with 'instructor assign-dance'."
            )

    store.save()
    click.echo(f"Created dance: {name} (song: {song_name})")


@dances.command("list")
@click.pass_context
def list_dances(ctx):
    """List all dances."""
    store = get_store()
    dances_list = store.get_collection("dances")

    if not dances_list:
        click.echo("No dances found.")
        return

    headers = ["ID", "Name", "Song", "Instructor ID", "Notes"]
    rows = []
    for did, dance in sorted(dances_list.items(), key=lambda x: x[1]["name"]):
        rows.append(
            [
                did,
                dance["name"],
                dance.get("song_name", ""),
                dance.get("instructor_id", "") or "",
                dance.get("notes", ""),
            ]
        )

    click.echo(render_table(headers, rows))


@dances.command()
@click.argument("dance_id")
@click.pass_context
def show(ctx, dance_id):
    """Show details for a single dance."""
    store = get_store()
    dance = store.get("dances", dance_id)

    if dance is None:
        for did, d in store.iterate("dances"):
            if d["name"].lower() == dance_id.lower():
                dance = d
                break
        if dance is None:
            click.echo(f"Dance not found: {dance_id}")
            return

    click.echo(f"Name: {dance['name']}")
    click.echo(f"Song: {dance.get('song_name', '')}")
    click.echo(f"Instructor ID: {dance.get('instructor_id', '') or 'None'}")
    click.echo(f"Notes: {dance.get('notes', '')}")


@dances.command()
@click.argument("dance_id")
@click.pass_context
def remove(ctx, dance_id):
    """Remove a dance."""
    store = get_store()
    dance = store.get("dances", dance_id)

    if dance is None:
        for did, d in store.iterate("dances"):
            if d["name"].lower() == dance_id.lower():
                dance = d
                dance_id = did
                break
        if dance is None:
            click.echo(f"Dance not found: {dance_id}")
            return

    store.execute("DELETE FROM dances WHERE id = ?", (dance_id,))
    store.save()
    click.echo(f"Removed dance: {dance['name']}")


@dances.command()
@click.argument("dance_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_add(ctx, dance_id, dancer_id):
    """Add a dancer to a dance."""
    store = get_store()
    dances_list = store.get_collection("dances")

    dance = store.get("dances", dance_id)
    if dance is None:
        click.echo(f"Dance not found: {dance_id}")
        return

    store.execute("PRAGMA foreign_keys = OFF")
    store.execute(
        "INSERT OR IGNORE INTO dance_assignments (dance_id, dancer_id) "
        "VALUES (?, ?)",
        (dance_id, dancer_id),
    )
    store.execute("PRAGMA foreign_keys = ON")

    store.save()
    click.echo(f"Added dancer {dancer_id} to dance '{dance['name']}'.")


@dances.command()
@click.argument("dance_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_remove(ctx, dance_id, dancer_id):
    """Remove a dancer from a dance."""
    store = get_store()
    dances_list = store.get_collection("dances")

    dance = store.get("dances", dance_id)
    if dance is None:
        click.echo(f"Dance not found: {dance_id}")
        return

    store.execute(
        "DELETE FROM dance_assignments WHERE dance_id = ? AND dancer_id = ?",
        (dance_id, dancer_id),
    )

    store.save()
    click.echo(f"Removed dancer {dancer_id} from dance '{dance['name']}'.")


@dances.command()
@click.option("--filepath", default="dances.csv", help="Output CSV filepath.")
@click.pass_context
def export(ctx, filepath):
    """Export all dances to CSV."""
    from dancemanager.utils import csv_export_dances

    store = get_store()
    csv_export_dances(store, filepath)
    click.echo(f"Exported dances to {filepath}")
