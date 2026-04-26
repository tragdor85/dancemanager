"""Team CRUD operations for Dance Manager.

Provides commands to add, list, show, remove, assign, and export teams.
"""

import click

from dancemanager.models import make_team_id
from dancemanager.utils import get_store


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
    teams_list = store.get_collection("teams")
    dancers_list = store.get_collection("dancers")

    team_id = make_team_id(name)
    if team_id in teams_list:
        click.echo(f"Team already exists: {name}")
        return

    store.execute(
        "INSERT OR REPLACE INTO teams (id, name, notes) VALUES (?, ?, ?)",
        (team_id, name, ""),
    )

    for d_name in dancers:
        for did, d in store.iterate("dancers"):
            if d["name"].lower() == d_name.lower():
                store.execute(
                    "INSERT OR IGNORE INTO class_dancer_assignments (class_id, dancer_id) "
                    "SELECT id, ? FROM classes WHERE id = ?",
                    (did, team_id),
                )
                store.execute(
                    "INSERT OR IGNORE INTO dance_assignments (dance_id, dancer_id) "
                    "SELECT id, ? FROM dances WHERE id = ?",
                    (did, team_id),
                )
                store.execute(
                    "UPDATE dancers SET team_id = ? WHERE id = ?",
                    (team_id, did),
                )

    store.save()
    click.echo(f"Created team: {name} (ID: {team_id})")


@teams.command("list")
@click.pass_context
def list_teams(ctx):
    """List all teams."""
    store = get_store()
    teams_list = store.get_collection("teams")

    if not teams_list:
        click.echo("No teams found.")
        return

    headers = ["ID", "Name", "Dancer Count", "Notes"]
    rows = []
    for tid, team in sorted(teams_list.items(), key=lambda x: x[1]["name"]):
        dancer_count = store.execute(
            "SELECT COUNT(*) FROM dancers WHERE team_id = ?",
            (tid,),
        )[0][0]
        rows.append(
            [
                tid,
                team["name"],
                dancer_count,
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
    team = store.get("teams", team_id)

    if team is None:
        for tid, t in store.iterate("teams"):
            if t["name"].lower() == team_id.lower():
                team = t
                break
        if team is None:
            click.echo(f"Team not found: {team_id}")
            return

    click.echo(f"Name: {team['name']}")
    click.echo(
        f"Dancer Count: {store.execute('SELECT COUNT(*) FROM dancers WHERE team_id = ?', (team_id,))[0][0]}"
    )
    click.echo(f"Notes: {team.get('notes', '')}")


@teams.command()
@click.argument("team_id")
@click.pass_context
def remove(ctx, team_id):
    """Remove a team (does not remove dancers)."""
    store = get_store()
    team = store.get("teams", team_id)

    if team is None:
        for tid, t in store.iterate("teams"):
            if t["name"].lower() == team_id.lower():
                team = t
                break
        if team is None:
            click.echo(f"Team not found: {team_id}")
            return

    store.execute("DELETE FROM teams WHERE id = ?", (team_id,))
    store.save()
    click.echo(f"Removed team: {team['name']}")


@teams.command()
@click.argument("team_id")
@click.argument("class_name")
@click.pass_context
def assign(ctx, team_id, class_name):
    """Assign a team to a class."""
    store = get_store()
    teams_list = store.get_collection("teams")
    classes_list = store.get_collection("classes")

    team = store.get("teams", team_id)
    if team is None:
        click.echo(f"Team not found: {team_id}")
        return

    for cname, class_data in classes_list.items():
        if class_data["name"].lower() == class_name.lower():
            cid = class_data["id"]
            store.execute(
                "INSERT OR IGNORE INTO class_team_assignments (class_id, team_id) "
                "VALUES (?, ?)",
                (cid, team_id),
            )
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
    teams_list = store.get_collection("teams")
    dancers_list = store.get_collection("dancers")

    team = store.get("teams", team_id)
    if team is None:
        click.echo(f"Team not found: {team_id}")
        return

    if dancer_id not in team.get("dancer_ids", []):
        team["dancer_ids"].append(dancer_id)

    dancer = store.get("dancers", dancer_id)
    if dancer:
        dancer["team_id"] = team_id

    store.save()
    click.echo(f"Added dancer {dancer_id} to team '{team['name']}'.")


@teams.command()
@click.argument("team_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_remove(ctx, team_id, dancer_id):
    """Remove a dancer from a team."""
    store = get_store()
    teams_list = store.get_collection("teams")
    dancers_list = store.get_collection("dancers")

    team = store.get("teams", team_id)
    if team is None:
        click.echo(f"Team not found: {team_id}")
        return

    if dancer_id in team["dancer_ids"]:
        team["dancer_ids"].remove(dancer_id)

    dancer = store.get("dancers", dancer_id)
    if dancer and dancer.get("team_id") == team_id:
        dancer["team_id"] = None

    store.save()
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
