"""Team CRUD operations for Dance Manager.

Provides commands to add, list, show, remove, assign, and export teams.
"""

import click

from dancemanager.models import make_team_id
from dancemanager.utils import get_store, render_table


@click.group()
def teams():
    """Team management commands."""
    pass


@teams.command()
@click.argument("name")
@click.option(
    "--dancer",
    "dancers",
    multiple=True,
    help="Add dancer by name.",
)
@click.pass_context
def add(ctx, name, dancers):
    """Create a team with optional dancers."""
    store = get_store()
    teams_coll = store.get_collection("teams")
    dancers_coll = store.get_collection("dancers")

    team_id = make_team_id(name)
    if team_id in [t["id"] for t in teams_coll.values()]:
        click.echo(f"Team already exists: {name}")
        return

    teams_coll[team_id] = {
        "id": team_id,
        "name": name,
        "dancer_ids": [],
        "notes": "",
    }

    for d_name in dancers:
        for did, d in dancers_coll.items():
            if d["name"].lower() == d_name.lower():
                teams_coll[team_id]["dancer_ids"].append(did)
                d["team_id"] = team_id
                break

    store.set_collection("teams", teams_coll)
    store.set_collection("dancers", dancers_coll)
    click.echo(f"Created team: {name} (ID: {team_id})")


@teams.command("list")
@click.pass_context
def list(ctx):
    """List all teams."""
    store = get_store()
    teams_coll = store.get_collection("teams")

    if not teams_coll:
        click.echo("No teams found.")
        return

    headers = ["ID", "Name", "Dancer IDs", "Notes"]
    rows = []
    for tid, team in sorted(teams_coll.items(), key=lambda x: x[1]["name"]):
        rows.append(
            [
                tid,
                team["name"],
                ";".join(team.get("dancer_ids", [])),
                team.get("notes", ""),
            ]
        )

    click.echo(render_table(headers, rows))


@teams.command()
@click.argument("team_id")
@click.pass_context
def show(ctx, team_id):
    """Show details for a single team."""
    store = get_store()
    teams_coll = store.get_collection("teams")

    team = teams_coll.get(team_id)
    if team is None:
        for tid, t in teams_coll.items():
            if t["name"].lower() == team_id.lower():
                team = t
                break
        if team is None:
            click.echo(f"Team not found: {team_id}")
            return

    click.echo(f"Name: {team['name']}")
    click.echo(f"Dancer IDs: {', '.join(team.get('dancer_ids', []) or [])}")
    click.echo(f"Notes: {team.get('notes', '')}")


@teams.command()
@click.argument("team_id")
@click.pass_context
def remove(ctx, team_id):
    """Remove a team (does not remove dancers)."""
    store = get_store()
    teams_coll = store.get_collection("teams")

    team = teams_coll.get(team_id)
    if team is None:
        for tid, t in teams_coll.items():
            if t["name"].lower() == team_id.lower():
                team = t
                break
        if team is None:
            click.echo(f"Team not found: {team_id}")
            return

    del teams_coll[team_id]
    store.set_collection("teams", teams_coll)
    click.echo(f"Removed team: {team['name']}")


@teams.command()
@click.argument("team_id")
@click.argument("class_name")
@click.pass_context
def assign(ctx, team_id, class_name):
    """Assign a team to a class."""
    store = get_store()
    teams_coll = store.get_collection("teams")
    classes_coll = store.get_collection("classes")

    team = teams_coll.get(team_id)
    if team is None:
        click.echo(f"Team not found: {team_id}")
        return

    for cname, class_data in classes_coll.items():
        if class_data["name"].lower() == class_name.lower():
            cid = class_data["id"]
            if team_id not in class_data.get("team_ids", []):
                class_data["team_ids"].append(team_id)
            store.set_collection("classes", classes_coll)
            click.echo(f"Assigned team '{team['name']}' to class '{cname}'.")
            return

    click.echo(f"Class not found: {class_name}")


@teams.command()
@click.argument("team_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_add(ctx, team_id, dancer_id):
    """Add a dancer to a team."""
    store = get_store()
    teams_coll = store.get_collection("teams")
    dancers_coll = store.get_collection("dancers")

    team = teams_coll.get(team_id)
    if team is None:
        click.echo(f"Team not found: {team_id}")
        return

    if dancer_id not in team["dancer_ids"]:
        team["dancer_ids"].append(dancer_id)

    dancer = dancers_coll.get(dancer_id)
    if dancer:
        dancer["team_id"] = team_id

    store.set_collection("teams", teams_coll)
    store.set_collection("dancers", dancers_coll)
    click.echo(f"Added dancer {dancer_id} to team '{team['name']}'.")


@teams.command()
@click.argument("team_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_remove(ctx, team_id, dancer_id):
    """Remove a dancer from a team."""
    store = get_store()
    teams_coll = store.get_collection("teams")
    dancers_coll = store.get_collection("dancers")

    team = teams_coll.get(team_id)
    if team is None:
        click.echo(f"Team not found: {team_id}")
        return

    if dancer_id in team["dancer_ids"]:
        team["dancer_ids"].remove(dancer_id)

    dancer = dancers_coll.get(dancer_id)
    if dancer and dancer.get("team_id") == team_id:
        dancer["team_id"] = None

    store.set_collection("teams", teams_coll)
    store.set_collection("dancers", dancers_coll)
    click.echo(f"Removed dancer {dancer_id} from team '{team['name']}'.")


@teams.command()
@click.option("--filepath", default="teams.csv", help="Output CSV filepath.")
@click.pass_context
def export(ctx, filepath):
    """Export all teams to CSV."""
    from dancemanager.utils import csv_export_teams

    store = get_store()
    csv_export_teams(store, filepath)
    click.echo(f"Exported teams to {filepath}")
