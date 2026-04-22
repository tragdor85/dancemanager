"""Dancer CRUD operations for Dance Manager.

Provides commands to add, list, show, remove, and export dancers.
"""

from typing import Optional

import click

from dancemanager.models import make_dancer_id
from dancemanager.utils import get_store, render_table


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
    dancers_coll = store.get_collection("dancers")

    if name in dancers_coll:
        click.echo(f"Error: dancer '{name}' already exists")
        return

    dancer_id = make_dancer_id(name)
    dancers_coll[dancer_id] = {
        "id": dancer_id,
        "name": name,
        "team_id": None,
        "class_ids": [],
        "notes": "",
    }

    if team:
        teams_coll = store.get_collection("teams")
        for tname, team_data in teams_coll.items():
            if tname.lower() == team.lower():
                dancers_coll[dancer_id]["team_id"] = team
                team_data["dancer_ids"].append(dancer_id)
                store.set_collection("teams", teams_coll)
                break
        else:
            click.echo(f"Warning: team '{team}' not found, dancer added without team.")

    store.set_collection("dancers", dancers_coll)
    click.echo(f"Added dancer: {name} (ID: {dancer_id})")


@dancers.command()
@click.pass_context
def list(ctx):
    """List all dancers."""
    store = get_store()
    dancers_coll = store.get_collection("dancers")

    if not dancers_coll:
        click.echo("No dancers found.")
        return

    headers = ["ID", "Name", "Team ID", "Class IDs", "Notes"]
    rows = []
    for did, dancer in sorted(dancers_coll.items(), key=lambda x: x[1]["name"]):
        rows.append(
            [
                did,
                dancer["name"],
                dancer.get("team_id", "") or "",
                ";".join(dancer.get("class_ids", [])),
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
    dancers_coll = store.get_collection("dancers")

    dancer = dancers_coll.get(dancer_id)
    if dancer is None:
        for did, d in dancers_coll.items():
            if d["name"].lower() == dancer_id.lower():
                dancer = d
                break
        if dancer is None:
            click.echo(f"Dancer not found: {dancer_id}")
            return

    click.echo(f"Name: {dancer['name']}")
    click.echo(f"Team ID: {dancer.get('team_id', '') or 'None'}")
    click.echo(f"Class IDs: {', '.join(dancer.get('class_ids', []) or [])}")
    click.echo(f"Notes: {dancer.get('notes', '')}")


@dancers.command()
@click.argument("dancer_id")
@click.pass_context
def remove(ctx, dancer_id):
    """Remove a dancer and clean up references."""
    store = get_store()
    dancers_coll = store.get_collection("dancers")

    dancer = dancers_coll.get(dancer_id)
    if dancer is None:
        for did, d in dancers_coll.items():
            if d["name"].lower() == dancer_id.lower():
                dancer_id = did
                dancer = d
                break
        if dancer is None:
            click.echo(f"Dancer not found: {dancer_id}")
            return

    del dancers_coll[dancer_id]
    store.set_collection("dancers", dancers_coll)

    teams_coll = store.get_collection("teams")
    for tname, team_data in teams_coll.items():
        if dancer_id in team_data.get("dancer_ids", []):
            team_data["dancer_ids"].remove(dancer_id)

    store.set_collection("teams", teams_coll)

    classes_coll = store.get_collection("classes")
    for cname, class_data in classes_coll.items():
        ids = class_data.get("dancer_ids", [])
        if dancer_id in ids:
            ids.remove(dancer_id)

    store.set_collection("classes", classes_coll)

    dances_coll = store.get_collection("dances")
    for dname, dance_data in dances_coll.items():
        ids = dance_data.get("dancer_ids", [])
        if dancer_id in ids:
            ids.remove(dancer_id)

    store.set_collection("dances", dances_coll)
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
