"""Class CRUD operations for Dance Manager.

Provides commands to add, list, show, remove, and manage classes.
"""

from typing import Optional

import click

from dancemanager.models import make_class_id
from dancemanager.utils import get_store


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
    classes_list = store.get_collection("classes")

    class_id = make_class_id(name)
    if class_id in classes_list:
        click.echo(f"Class already exists: {name}")
        return

    store.execute(
        "INSERT OR REPLACE INTO classes (id, name, instructor_id, notes) "
        "VALUES (?, ?, ?, ?)",
        (class_id, name.title(), None, ""),
    )

    if instructor:
        cursor = store.execute(
            "SELECT id FROM instructors WHERE LOWER(name) = ?",
            (instructor.lower(),),
        )
        if cursor and cursor[0]:
            instructor_id = cursor[0][0]
            store.execute(
                "UPDATE classes SET instructor_id = ? WHERE id = ?",
                (instructor_id, class_id),
            )
            store.execute(
                "INSERT OR IGNORE INTO class_team_assignments (class_id, team_id) "
                "SELECT id, ? FROM teams WHERE id = ?",
                (class_id, instructor_id),
            )
        else:
            click.echo(
                f"Warning: instructor '{instructor}' not found. "
                "Assign later with 'instructor assign-class'."
            )

    store.save()
    click.echo(f"Created class: {name} (ID: {class_id})")


@classes.command("list")
@click.pass_context
def list_classes(ctx):
    """List all classes."""
    store = get_store()
    classes_list = store.get_collection("classes")

    if not classes_list:
        click.echo("No classes found.")
        return

    headers = ["ID", "Name", "Instructor ID", "Notes"]
    rows = []
    for cid, cls in sorted(classes_list.items(), key=lambda x: x[1]["name"]):
        rows.append(
            [
                cid,
                cls["name"],
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
    cls = store.get("classes", class_id)

    if cls is None:
        for cid, c in store.iterate("classes"):
            if c["name"].lower() == class_id.lower():
                cls = c
                break
        if cls is None:
            click.echo(f"Class not found: {class_id}")
            return

    click.echo(f"Name: {cls['name']}")
    click.echo(f"Instructor ID: {cls.get('instructor_id', '') or 'None'}")
    click.echo(f"Notes: {cls.get('notes', '')}")


@classes.command()
@click.argument("class_id")
@click.pass_context
def remove(ctx, class_id):
    """Remove a class (does not remove dancers)."""
    store = get_store()
    cls = store.get("classes", class_id)

    if cls is None:
        for cid, c in store.iterate("classes"):
            if c["name"].lower() == class_id.lower():
                cls = c
                class_id = cid
                break
        if cls is None:
            click.echo(f"Class not found: {class_id}")
            return

    store.execute("DELETE FROM classes WHERE id = ?", (class_id,))
    store.save()
    click.echo(f"Removed class: {cls['name']}")


@classes.command()
@click.argument("class_id")
@click.argument("team_id")
@click.pass_context
def team_add(ctx, class_id, team_id):
    """Assign a team to a class."""
    store = get_store()
    classes_list = store.get_collection("classes")
    teams_list = store.get_collection("teams")

    cls = store.get("classes", class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
        return

    team = store.get("teams", team_id)
    if team is None:
        click.echo(f"Team not found: {team_id}")
        return

    store.execute(
        "INSERT OR IGNORE INTO class_team_assignments (class_id, team_id) "
        "VALUES (?, ?)",
        (class_id, team_id),
    )

    store.save()
    click.echo(f"Assigned team '{team['name']}' to class '{cls['name']}'.")


@classes.command()
@click.argument("class_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_add(ctx, class_id, dancer_id):
    """Add an individual dancer to a class."""
    store = get_store()
    classes_list = store.get_collection("classes")
    dancers_list = store.get_collection("dancers")

    cls = store.get("classes", class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
        return

    store.execute(
        "INSERT OR IGNORE INTO class_dancer_assignments (class_id, dancer_id) "
        "VALUES (?, ?)",
        (class_id, dancer_id),
    )

    dancer = store.get("dancers", dancer_id)
    if dancer:
        store.execute(
            "INSERT OR IGNORE INTO class_dancer_assignments (class_id, dancer_id) "
            "SELECT ?, id FROM classes WHERE id = ?",
            (class_id, dancer_id),
        )

    store.save()
    click.echo(f"Added dancer {dancer_id} to class '{cls['name']}'.")


@classes.command()
@click.argument("class_id")
@click.argument("dancer_id")
@click.pass_context
def dancer_remove(ctx, class_id, dancer_id):
    """Remove a dancer from a class."""
    store = get_store()
    classes_list = store.get_collection("classes")
    dancers_list = store.get_collection("dancers")

    cls = store.get("classes", class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
        return

    store.execute(
        "DELETE FROM class_dancer_assignments WHERE class_id = ? AND dancer_id = ?",
        (class_id, dancer_id),
    )

    dancer = store.get("dancers", dancer_id)
    if dancer:
        store.execute(
            "DELETE FROM class_dancer_assignments WHERE class_id = ? AND dancer_id = ?",
            (class_id, dancer_id),
        )

    store.save()
    click.echo(f"Removed dancer {dancer_id} from class '{cls['name']}'.")


@classes.command()
@click.argument("class_id")
@click.argument("instructor_id")
@click.pass_context
def instructor_assign(ctx, class_id, instructor_id):
    """Assign an instructor to a class."""
    store = get_store()
    classes_list = store.get_collection("classes")
    instructors_list = store.get_collection("instructors")

    cls = store.get("classes", class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
        return

    instructor = store.get("instructors", instructor_id)
    if instructor is None:
        click.echo(f"Instructor not found: {instructor_id}")
        return

    store.execute(
        "UPDATE classes SET instructor_id = ? WHERE id = ?",
        (instructor_id, class_id),
    )
    store.execute(
        "INSERT OR IGNORE INTO class_team_assignments (class_id, team_id) "
        "SELECT id, ? FROM teams WHERE id = ?",
        (class_id, instructor_id),
    )

    store.save()
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
