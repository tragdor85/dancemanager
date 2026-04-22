"""Dance CRUD operations for Dance Manager.

Provides commands to add, list, show, remove, and manage dances.
"""

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
@click.pass_context
def add(ctx, name, song_name, instructor):
    """Create a dance with a song, optionally assigning an instructor."""
    store = get_store()
    dances_coll = store.get_collection("dances")

    dance_id = make_dance_id(name)
    if dance_id in [d["id"] for d in dances_coll.values()]:
        click.echo(f"Dance already exists: {name}")
        return

    dances_coll[dance_id] = {
        "id": dance_id,
        "name": name,
        "song_name": song_name,
        "instructor_id": None,
        "dancer_ids": [],
        "notes": "",
    }

    if instructor:
        instructors_coll = store.get_collection("instructors")
        for iname, inst_data in instructors_coll.items():
            if inst_data["name"].lower() == instructor.lower():
                dances_coll[dance_id]["instructor_id"] = iname
                inst_data["dance_ids"].append(dance_id)
                store.set_collection("instructors", instructors_coll)
                break
        else:
            click.echo(
                f"Warning: instructor '{instructor}' not found. "
                "Assign later with 'instructor assign-dance'."
            )

    store.set_collection("dances", dances_coll)
    click.echo(f"Created dance: {name} (song: {song_name})")


@dances.command("list")
@click.pass_context
def list(ctx):
    """List all dances."""
    store = get_store()
    dances_coll = store.get_collection("dances")

    if not dances_coll:
        click.echo("No dances found.")
        return

    headers = [
        "ID",
        "Name",
        "Song",
        "Instructor ID",
        "Dancer IDs",
        "Notes",
    ]
    rows = []
    for did, dance in sorted(dances_coll.items(), key=lambda x: x[1]["name"]):
        rows.append(
            [
                did,
                dance["name"],
                dance.get("song_name", ""),
                dance.get("instructor_id", "") or "",
                ";".join(dance.get("dancer_ids", [])),
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
    dances_coll = store.get_collection("dances")

    dance = dances_coll.get(dance_id)
    if dance is None:
        for did, d in dances_coll.items():
            if d["name"].lower() == dance_id.lower():
                dance = d
                break
        if dance is None:
            click.echo(f"Dance not found: {dance_id}")
            return

    click.echo(f"Name: {dance['name']}")
    click.echo(f"Song: {dance.get('song_name', '')}")
    click.echo(f"Instructor ID: {dance.get('instructor_id', '') or 'None'}")
    click.echo(f"Dancer IDs: {', '.join(dance.get('dancer_ids', []) or [])}")
    click.echo(f"Notes: {dance.get('notes', '')}")


@dances.command()
@click.argument("dance_id")
@click.pass_context
def remove(ctx, dance_id):
    """Remove a dance."""
    store = get_store()
    dances_coll = store.get_collection("dances")

    dance = dances_coll.get(dance_id)
    if dance is None:
        for did, d in dances_coll.items():
            if d["name"].lower() == dance_id.lower():
                dance = d
                dance_id = did
                break
        if dance is None:
            click.echo(f"Dance not found: {dance_id}")
            return

    del dances_coll[dance_id]
    store.set_collection("dances", dances_coll)
    click.echo(f"Removed dance: {dance['name']}")


@dances.command()
@click.argument("dance_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_add(ctx, dance_id, dancer_id):
    """Add a dancer to a dance."""
    store = get_store()
    dances_coll = store.get_collection("dances")

    dance = dances_coll.get(dance_id)
    if dance is None:
        click.echo(f"Dance not found: {dance_id}")
        return

    if dancer_id not in dance.get("dancer_ids", []):
        dance["dancer_ids"].append(dancer_id)

    store.set_collection("dances", dances_coll)
    click.echo(f"Added dancer {dancer_id} to dance '{dance['name']}'.")


@dances.command()
@click.argument("dance_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_remove(ctx, dance_id, dancer_id):
    """Remove a dancer from a dance."""
    store = get_store()
    dances_coll = store.get_collection("dances")

    dance = dances_coll.get(dance_id)
    if dance is None:
        click.echo(f"Dance not found: {dance_id}")
        return

    dancer_ids = dance.get("dancer_ids", [])
    if dancer_id in dancer_ids:
        dancer_ids.remove(dancer_id)

    store.set_collection("dances", dances_coll)
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
