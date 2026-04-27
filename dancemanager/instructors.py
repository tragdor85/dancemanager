"""Instructor CRUD operations for Dance Manager.

Provides commands to add, list, show, remove, and assign instructors.
"""

from typing import Optional

import click

from dancemanager.models import make_instructor_id
from dancemanager.utils import get_store, render_table


@click.group()
def instructors():
    """Instructor management commands."""
    pass


@instructors.command()
@click.argument("name")
@click.pass_context
def add(ctx, name):
    """Add an instructor."""
    store = get_store()
    instructors_list = store.get_collection("instructors")

    instructor_id = make_instructor_id(name)
    if instructor_id in instructors_list:
        click.echo(f"Instructor already exists: {name}")
        return

    store.execute(
        "INSERT OR REPLACE INTO instructors (id, name, notes) " "VALUES (?, ?, ?)",
        (instructor_id, name.title(), ""),
    )

    store.save()
    click.echo(f"Added instructor: {name} (ID: {instructor_id})")


@instructors.command("list")
@click.pass_context
def list_instructors(ctx):
    """List all instructors."""
    store = get_store()
    instructors_list = store.get_collection("instructors")

    if not instructors_list:
        click.echo("No instructors found.")
        return

    headers = ["ID", "Name", "Notes"]
    rows = []
    for iid, inst in sorted(instructors_list.items(), key=lambda x: x[1]["name"]):
        rows.append(
            [
                iid,
                inst["name"],
                inst.get("notes", ""),
            ]
        )

    click.echo(render_table(headers, rows))


@instructors.command()
@click.argument("instructor_id")
@click.pass_context
def show(ctx, instructor_id):
    """Show details for a single instructor."""
    store = get_store()
    instructor = store.get("instructors", instructor_id)

    if instructor is None:
        for iid, i in store.iterate("instructors"):
            if i["name"].lower() == instructor_id.lower():
                instructor = i
                break
        if instructor is None:
            click.echo(f"Instructor not found: {instructor_id}")
            return

    click.echo(f"Name: {instructor['name']}")
    click.echo(f"Notes: {instructor.get('notes', '')}")


@instructors.command()
@click.argument("instructor_id")
@click.pass_context
def remove(ctx, instructor_id):
    """Remove an instructor."""
    store = get_store()
    instructor = store.get("instructors", instructor_id)

    if instructor is None:
        for iid, i in store.iterate("instructors"):
            if i["name"].lower() == instructor_id.lower():
                instructor = i
                break
        if instructor is None:
            click.echo(f"Instructor not found: {instructor_id}")
            return

    store.execute("DELETE FROM instructors WHERE id = ?", (instructor_id,))
    store.save()
    click.echo(f"Removed instructor: {instructor['name']}")


@instructors.command()
@click.argument("instructor_id")
@click.argument("class_id")
@click.pass_context
def assign_class(ctx, instructor_id, class_id):
    """Assign an instructor to a class."""
    store = get_store()
    instructors_list = store.get_collection("instructors")
    classes_list = store.get_collection("classes")

    instructor = store.get("instructors", instructor_id)
    if instructor is None:
        click.echo(f"Instructor not found: {instructor_id}")
        return

    cls = store.get("classes", class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
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


@instructors.command()
@click.argument("instructor_id")
@click.argument("dance_id")
@click.pass_context
def assign_dance(ctx, instructor_id, dance_id):
    """Assign an instructor to a dance."""
    store = get_store()
    instructors_list = store.get_collection("instructors")
    dances_list = store.get_collection("dances")

    instructor = store.get("instructors", instructor_id)
    if instructor is None:
        click.echo(f"Instructor not found: {instructor_id}")
        return

    dance = store.get("dances", dance_id)
    if dance is None:
        click.echo(f"Dance not found: {dance_id}")
        return

    store.execute(
        "UPDATE dances SET instructor_id = ? WHERE id = ?",
        (instructor_id, dance_id),
    )
    store.execute(
        "INSERT OR IGNORE INTO dance_assignments (dance_id, dancer_id) "
        "SELECT id, ? FROM dances WHERE id = ?",
        (dance_id, instructor_id),
    )

    store.save()
    click.echo(
        f"Assigned instructor '{instructor['name']}' to dance '{dance['name']}'."
    )


@instructors.command()
@click.option("--filepath", default="instructors.csv", help="Output CSV filepath.")
@click.pass_context
def export(ctx, filepath):
    """Export all instructors to CSV."""
    from dancemanager.utils import csv_export_instructors

    store = get_store()
    csv_export_instructors(store, filepath)
    click.echo(f"Exported instructors to {filepath}")
