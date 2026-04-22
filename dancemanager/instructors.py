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
    instructors_coll = store.get_collection("instructors")

    instructor_id = make_instructor_id(name)
    if instructor_id in [i["id"] for i in instructors_coll.values()]:
        click.echo(f"Instructor already exists: {name}")
        return

    instructors_coll[instructor_id] = {
        "id": instructor_id,
        "name": name,
        "class_ids": [],
        "dance_ids": [],
        "notes": "",
    }

    store.set_collection("instructors", instructors_coll)
    click.echo(f"Added instructor: {name} (ID: {instructor_id})")


@instructors.command("list")
@click.pass_context
def list(ctx):
    """List all instructors."""
    store = get_store()
    instructors_coll = store.get_collection("instructors")

    if not instructors_coll:
        click.echo("No instructors found.")
        return

    headers = ["ID", "Name", "Class IDs", "Dance IDs", "Notes"]
    rows = []
    for iid, inst in sorted(instructors_coll.items(), key=lambda x: x[1]["name"]):
        rows.append(
            [
                iid,
                inst["name"],
                ";".join(inst.get("class_ids", [])),
                ";".join(inst.get("dance_ids", [])),
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
    instructors_coll = store.get_collection("instructors")

    instructor = instructors_coll.get(instructor_id)
    if instructor is None:
        for iid, i in instructors_coll.items():
            if i["name"].lower() == instructor_id.lower():
                instructor = i
                break
        if instructor is None:
            click.echo(f"Instructor not found: {instructor_id}")
            return

    click.echo(f"Name: {instructor['name']}")
    click.echo(f"Class IDs: {', '.join(instructor.get('class_ids', []) or [])}")
    click.echo(f"Dance IDs: {', '.join(instructor.get('dance_ids', []) or [])}")
    click.echo(f"Notes: {instructor.get('notes', '')}")


@instructors.command()
@click.argument("instructor_id")
@click.pass_context
def remove(ctx, instructor_id):
    """Remove an instructor."""
    store = get_store()
    instructors_coll = store.get_collection("instructors")

    instructor = instructors_coll.get(instructor_id)
    if instructor is None:
        for iid, i in instructors_coll.items():
            if i["name"].lower() == instructor_id.lower():
                instructor = i
                break
        if instructor is None:
            click.echo(f"Instructor not found: {instructor_id}")
            return

    del instructors_coll[instructor_id]
    store.set_collection("instructors", instructors_coll)
    click.echo(f"Removed instructor: {instructor['name']}")


@instructors.command()
@click.argument("instructor_id")
@click.argument("class_id")
@click.pass_context
def assign_class(ctx, instructor_id, class_id):
    """Assign an instructor to a class."""
    store = get_store()
    instructors_coll = store.get_collection("instructors")
    classes_coll = store.get_collection("classes")

    instructor = instructors_coll.get(instructor_id)
    if instructor is None:
        click.echo(f"Instructor not found: {instructor_id}")
        return

    cls = classes_coll.get(class_id)
    if cls is None:
        click.echo(f"Class not found: {class_id}")
        return

    instructor["class_ids"].append(class_id)
    cls["instructor_id"] = instructor_id

    store.set_collection("instructors", instructors_coll)
    store.set_collection("classes", classes_coll)
    click.echo(f"Assigned instructor '{instructor['name']}' to class '{cls['name']}'.")


@instructors.command()
@click.argument("instructor_id")
@click.argument("dance_id")
@click.pass_context
def assign_dance(ctx, instructor_id, dance_id):
    """Assign an instructor to a dance."""
    store = get_store()
    instructors_coll = store.get_collection("instructors")
    dances_coll = store.get_collection("dances")

    instructor = instructors_coll.get(instructor_id)
    if instructor is None:
        click.echo(f"Instructor not found: {instructor_id}")
        return

    dance = dances_coll.get(dance_id)
    if dance is None:
        click.echo(f"Dance not found: {dance_id}")
        return

    instructor["dance_ids"].append(dance_id)
    dance["instructor_id"] = instructor_id

    store.set_collection("instructors", instructors_coll)
    store.set_collection("dances", dances_coll)
    click.echo(
        f"Assigned instructor '{instructor['name']}' to dance '{dance['name']}'."
    )
