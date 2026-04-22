"""Class CRUD operations for Dance Manager.

Provides commands to add, list, show, remove, and manage classes.
"""

from typing import Optional

import click

from dancemanager.models import make_class_id
from dancemanager.utils import get_store, render_table


@click.group()
def classes():
    """Dance class management commands."""
    pass


@classes.command()
@click.argument("name")
@click.option(
    "--instructor",
    default=None,
    help="Lead instructor by name.",
)
@click.pass_context
def add(ctx, name, instructor):
    """Create a dance class."""
    store = get_store()
    classes_coll = store.get_collection("classes")

    class_id = make_class_id(name)
    if class_id in [c["id"] for c in classes_coll.values()]:
        click.echo(f"Class already exists: {name}")
        return

    classes_coll[class_id] = {
        "id": class_id,
        "name": name,
        "team_ids": [],
        "dancer_ids": [],
        "instructor_id": None,
        "notes": "",
    }

    if instructor:
        instructors_coll = store.get_collection("instructors")
        for iname, inst_data in instructors_coll.items():
            if inst_data["name"].lower() == instructor.lower():
                classes_coll[class_id]["instructor_id"] = iname
                inst_data["class_ids"].append(class_id)
                store.set_collection("instructors", instructors_coll)
                break
        else:
            click.echo(
                f"Warning: instructor '{instructor}' not found. "
                "Assign later with 'instructor assign-class'."
            )

    store.set_collection("classes", classes_coll)
    click.echo(f"Created class: {name} (ID: {class_id})")


@classes.command("list")
@click.pass_context
def list(ctx):
    """List all classes."""
    store = get_store()
    classes_coll = store.get_collection("classes")

    if not classes_coll:
        click.echo("No classes found.")
        return

    headers = ["ID", "Name", "Team IDs", "Dancer IDs", "Instructor ID", "Notes"]
    rows = []
    for cid, cls in sorted(classes_coll.items(), key=lambda x: x[1]["name"]):
        rows.append(
            [
                cid,
                cls["name"],
                ";".join(cls.get("team_ids", [])),
                ";".join(cls.get("dancer_ids", [])),
                cls.get("instructor_id", "") or "",
                cls.get("notes", ""),
            ]
        )

    click.echo(render_table(headers, rows))


@classes.command()
@click.argument("class_id")
@click.pass_context
def show(ctx, class_id):
    """Show details for a single class."""
    store = get_store()
    classes_coll = store.get_collection("classes")

    cls = classes_coll.get(class_id)
    if cls is None:
        for cid, c in classes_coll.items():
            if c["name"].lower() == class_id.lower():
                cls = c
                break
        if cls is None:
            click.echo(f"Class not found: {class_id}")
            return

    click.echo(f"Name: {cls['name']}")
    click.echo(f"Team IDs: {', '.join(cls.get('team_ids', []) or [])}")
    click.echo(f"Dancer IDs: {', '.join(cls.get('dancer_ids', []) or [])}")
    click.echo(f"Instructor ID: {cls.get('instructor_id', '') or 'None'}")
    click.echo(f"Notes: {cls.get('notes', '')}")


@classes.command()
@click.argument("class_id")
@click.pass_context
def remove(ctx, class_id):
    """Remove a class (does not remove dancers)."""
    store = get_store()
    classes_coll = store.get_collection("classes")

    cls = classes_coll.get(class_id)
    if cls is None:
        for cid, c in classes_coll.items():
            if c["name"].lower() == class_id.lower():
                cls = c
                class_id = cid
                break
        if cls is None:
            click.echo(f"Class not found: {class_id}")
            return

    del classes_coll[class_id]
    store.set_collection("classes", classes_coll)
    click.echo(f"Removed class: {cls['name']}")


@classes.command()
@click.argument("class_id")
@click.argument("team_id")
@click.pass_context
def team_add(ctx, class_id, team_id):
    """Assign a team to a class."""
    store = get_store()
    classes_coll = store.get_collection("classes")
    teams_coll = store.get_collection("teams")

    cls = classes_coll.get(class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
        return

    team = teams_coll.get(team_id)
    if team is None:
        click.echo(f"Team not found: {team_id}")
        return

    if team_id not in cls.get("team_ids", []):
        cls["team_ids"].append(team_id)

    store.set_collection("classes", classes_coll)
    click.echo(f"Assigned team '{team['name']}' to class '{cls['name']}'.")


@classes.command()
@click.argument("class_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_add(ctx, class_id, dancer_id):
    """Add an individual dancer to a class."""
    store = get_store()
    classes_coll = store.get_collection("classes")
    dancers_coll = store.get_collection("dancers")

    cls = classes_coll.get(class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
        return

    if dancer_id not in cls.get("dancer_ids", []):
        cls["dancer_ids"].append(dancer_id)

    dancer = dancers_coll.get(dancer_id)
    if dancer:
        if class_id not in dancer.get("class_ids", []):
            dancer["class_ids"].append(class_id)
        store.set_collection("dancers", dancers_coll)

    store.set_collection("classes", classes_coll)
    click.echo(f"Added dancer {dancer_id} to class '{cls['name']}'.")


@classes.command()
@click.argument("class_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_remove(ctx, class_id, dancer_id):
    """Remove a dancer from a class."""
    store = get_store()
    classes_coll = store.get_collection("classes")
    dancers_coll = store.get_collection("dancers")

    cls = classes_coll.get(class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
        return

    dancer_ids = cls.get("dancer_ids", [])
    if dancer_id in dancer_ids:
        dancer_ids.remove(dancer_id)

    dancer = dancers_coll.get(dancer_id)
    if dancer:
        class_ids = dancer.get("class_ids", [])
        if class_id in class_ids:
            class_ids.remove(class_id)
        store.set_collection("dancers", dancers_coll)

    store.set_collection("classes", classes_coll)
    click.echo(f"Removed dancer {dancer_id} from class '{cls['name']}'.")


@classes.command()
@click.argument("class_id")
@click.argument("instructor_id")
@click.pass_context
def instructor_assign(ctx, class_id, instructor_id):
    """Assign an instructor to a class."""
    store = get_store()
    classes_coll = store.get_collection("classes")
    instructors_coll = store.get_collection("instructors")

    cls = classes_coll.get(class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
        return

    instructor = instructors_coll.get(instructor_id)
    if instructor is None:
        click.echo(f"Instructor not found: {instructor_id}")
        return

    instructor["class_ids"].append(class_id)
    cls["instructor_id"] = instructor_id

    store.set_collection("instructors", instructors_coll)
    store.set_collection("classes", classes_coll)
    click.echo(f"Assigned instructor '{instructor['name']}' to class '{cls['name']}'.")


@classes.command()
@click.option("--filepath", default="classes.csv", help="Output CSV filepath.")
@click.pass_context
def export(ctx, filepath):
    """Export all classes to CSV."""
    from dancemanager.utils import csv_export_classes

    store = get_store()
    csv_export_classes(store, filepath)
    click.echo(f"Exported classes to {filepath}")
