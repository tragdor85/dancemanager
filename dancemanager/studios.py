"""Studio management for Dance Manager.

Provides commands to add, list, show, remove studios and manage reservations.
"""

import json
from typing import List, Optional, Tuple

import click

from dancemanager.utils import get_store, render_table


def _make_studio_id(name: str) -> str:
    """Return a deterministic ID for a studio."""
    return f"studio-{name.strip().lower().replace(' ', '-')}"


# -- CRUD operations -------------------------------------------------------


def add_studio(
    name: str,
    location: str = "",
    capacity: int = 20,
    equipment: Optional[List[str]] = None,
) -> str:
    """Create a new studio. Returns the studio ID."""
    store = get_store()
    studio_id = _make_studio_id(name)

    existing = store.get("studios", studio_id)
    if existing:
        raise ValueError(f"Studio already exists: {name}")

    extra_fields: dict = {}
    if equipment:
        extra_fields["equipment"] = equipment

    store.execute(
        "INSERT OR REPLACE INTO studios "
        "(id, name, location, capacity, schedule, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (studio_id, title(name), location, capacity, json.dumps([]), ""),
    )

    if extra_fields:
        store.execute(
            "UPDATE studios SET extra = ? WHERE id = ?",
            (json.dumps(extra_fields), studio_id),
        )

    store.save()
    return studio_id


def get_studio(id: str) -> Optional[dict]:
    """Retrieve a studio by ID."""
    store = get_store()
    return store.get("studios", id)


def list_studios() -> List[dict]:
    """List all studios sorted by name."""
    store = get_store()
    studios_list = store.get_collection("studios")
    return sorted(studios_list.values(), key=lambda s: s["name"])


def remove_studio(id: str) -> bool:
    """Delete a studio. Returns True if it existed."""
    store = get_store()
    existing = store.get("studios", id)
    if not existing:
        return False

    # Cancel all reservations for this studio
    schedule = existing.get("schedule", [])
    if schedule:
        for slot in schedule:
            reserved_by = slot.get("reserved_by")
            if reserved_by:
                reservation_type = slot.get("reservation_type", "")
                if reservation_type == "class":
                    store.execute(
                        "UPDATE classes SET extra = json_remove("
                        "COALESCE(extra, '{}'), '$.studio_id') WHERE id = ?",
                        (reserved_by,),
                    )

    store.execute("DELETE FROM studios WHERE id = ?", (id,))
    store.save()
    return True


# -- Reservation operations ------------------------------------------------


def reserve_slot(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str,
    reservation_type: str,
    reservation_id: str,
) -> bool:
    """Reserve a time slot in a studio.

    Returns True if successful, False if conflict or studio not found.
    """
    store = get_store()
    studio = store.get("studios", studio_id)
    if not studio:
        return False

    if is_slot_conflicted(studio_id, date, start_time, end_time):
        return False

    duration_minutes = _calc_duration(start_time, end_time)

    slot = {
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": duration_minutes,
        "reserved_by": reservation_id,
        "reservation_type": reservation_type,
    }

    schedule = studio.get("schedule", [])
    if not isinstance(schedule, list):
        try:
            schedule = json.loads(schedule)
        except (json.JSONDecodeError, TypeError):
            schedule = []

    schedule.append(slot)

    store.execute(
        "UPDATE studios SET schedule = ? WHERE id = ?",
        (json.dumps(schedule), studio_id),
    )

    # If this is a class reservation, link the studio to the class
    if reservation_type == "class":
        store.execute(
            "UPDATE classes SET extra = json_set("
            "COALESCE(extra, '{}'), '$.studio_id', ?) WHERE id = ?",
            (reservation_id, reservation_id),
        )

    store.save()
    return True


def cancel_reservation(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str,
    reservation_id: str,
) -> bool:
    """Cancel a reservation. Returns True if found and removed."""
    store = get_store()
    studio = store.get("studios", studio_id)
    if not studio:
        return False

    schedule = studio.get("schedule", [])
    if not isinstance(schedule, list):
        try:
            schedule = json.loads(schedule)
        except (json.JSONDecodeError, TypeError):
            schedule = []

    original_len = len(schedule)
    schedule = [
        slot
        for slot in schedule
        if not (
            slot.get("date") == date
            and slot.get("start_time") == start_time
            and slot.get("end_time") == end_time
            and slot.get("reserved_by") == reservation_id
        )
    ]

    if len(schedule) == original_len:
        return False

    store.execute(
        "UPDATE studios SET schedule = ? WHERE id = ?",
        (json.dumps(schedule), studio_id),
    )

    # If this was a class reservation, unlink the studio from the class
    if (
        _find_slot(studio.get("schedule", []), date, start_time).get("reservation_type")
        == "class"
    ):
        store.execute(
            "UPDATE classes SET extra = json_remove("
            "COALESCE(extra, '{}'), '$.studio_id') WHERE id = ?",
            (reservation_id,),
        )

    store.save()
    return True


def is_slot_conflicted(
    studio_id: str, date: str, start_time: str, end_time: str
) -> bool:
    """Check if a time slot is already reserved. Returns True if conflict."""
    studio = get_studio(studio_id)
    if not studio:
        return True

    schedule = studio.get("schedule", [])
    if not isinstance(schedule, list):
        try:
            schedule = json.loads(schedule)
        except (json.JSONDecodeError, TypeError):
            schedule = []

    for slot in schedule:
        if slot.get("date") == date and _times_overlap(
            slot["start_time"], slot["end_time"], start_time, end_time
        ):
            return True

    return False


def get_available_slots(
    studio_id: str, date: str, start_time: str, end_time: str
) -> bool:
    """Check if a slot is available for booking."""
    return not is_slot_conflicted(studio_id, date, start_time, end_time)


def get_studio_schedule(studio_id: str) -> List[dict]:
    """Get all scheduled slots for a studio, sorted by date and time."""
    studio = get_studio(studio_id)
    if not studio:
        return []

    schedule = studio.get("schedule", [])
    if not isinstance(schedule, list):
        try:
            schedule = json.loads(schedule)
        except (json.JSONDecodeError, TypeError):
            schedule = []

    return sorted(schedule, key=lambda s: (s.get("date", ""), s.get("start_time", "")))


def find_conflicts(
    studio_id: str, date: str, start_time: str, end_time: str
) -> List[dict]:
    """Find all conflicting reservations for a time slot."""
    studio = get_studio(studio_id)
    if not studio:
        return []

    schedule = studio.get("schedule", [])
    if not isinstance(schedule, list):
        try:
            schedule = json.loads(schedule)
        except (json.JSONDecodeError, TypeError):
            schedule = []

    conflicts = []
    for slot in schedule:
        if slot.get("date") == date and _times_overlap(
            slot["start_time"], slot["end_time"], start_time, end_time
        ):
            conflicts.append(
                {
                    "date": slot.get("date"),
                    "start_time": slot.get("start_time"),
                    "end_time": slot.get("end_time"),
                    "reserved_by": slot.get("reserved_by"),
                    "reservation_type": slot.get("reservation_type"),
                }
            )

    return conflicts


def can_book_slot(
    studio_id: str, date: str, start_time: str, end_time: str
) -> Tuple[bool, List]:
    """Check if a slot can be booked. Returns (is_available, conflict_details)."""
    conflicts = find_conflicts(studio_id, date, start_time, end_time)
    return len(conflicts) == 0, conflicts


# -- CLI commands ----------------------------------------------------------


@click.group()
def studio():
    """Manage dance studios."""
    pass


@studio.command("add")
@click.argument("name")
@click.option("--location", default="", help="Studio location/address.")
@click.option("--capacity", default=20, type=int, help="Maximum dancer capacity.")
@click.option(
    "--equipment",
    default=None,
    help="Comma-separated list of equipment (mirrors,barre,sound_system).",
)
@click.pass_context
def add_studio_cmd(ctx, name, location, capacity, equipment):
    """Add a new studio."""
    store = get_store()

    # Check for existing studio with same name
    studios_list = store.get_collection("studios")
    for sid, s in studios_list.items():
        if s["name"].lower() == name.lower():
            click.echo(f"Studio already exists: {name}")
            return

    equip_list = None
    if equipment:
        equip_list = [e.strip() for e in equipment.split(",")]

    studio_id = add_studio(name, location, capacity, equip_list)
    click.echo(f"Created studio: {name} (ID: {studio_id})")


@studio.command("list")
@click.pass_context
def list_studios_cmd(ctx):
    """List all studios."""
    studios = list_studios()

    if not studios:
        click.echo("No studios found.")
        return

    headers = ["ID", "Name", "Location", "Capacity"]
    rows = []
    for s in studios:
        rows.append(
            [
                s["id"],
                s["name"],
                s.get("location", "") or "",
                s.get("capacity", 20),
            ]
        )

    click.echo(render_table(headers, rows))


@studio.command()
@click.argument("studio_id")
@click.pass_context
def show(ctx, studio_id):
    """Show studio details including schedule."""
    store = get_store()
    studio = store.get("studios", studio_id)

    if not studio:
        # Try case-insensitive lookup
        for sid, s in store.iterate("studios"):
            if s["name"].lower() == studio_id.lower():
                studio = s
                studio_id = sid
                break

    if not studio:
        click.echo(f"Studio not found: {studio_id}")
        return

    click.echo(f"Name: {studio['name']}")
    click.echo(f"Location: {studio.get('location', '') or 'Not set'}")
    click.echo(f"Capacity: {studio.get('capacity', 20)}")

    equipment = studio.get("equipment", [])
    if equipment:
        click.echo(f"Equipment: {', '.join(equipment)}")

    schedule = get_studio_schedule(studio_id)
    if schedule:
        click.echo("")
        click.echo("Schedule:")
        for slot in schedule:
            date_str = slot.get("date", "")
            time_range = f"{slot['start_time']}-{slot['end_time']}"
            reserved_by = slot.get("reserved_by", "")
            res_type = slot.get("reservation_type", "")
            click.echo(f"  {date_str} {time_range} - {res_type}: {reserved_by}")
    else:
        click.echo("")
        click.echo("No scheduled reservations.")


@studio.command()
@click.argument("studio_id")
@click.pass_context
def remove(ctx, studio_id):
    """Remove a studio."""
    store = get_store()
    studio = store.get("studios", studio_id)

    if not studio:
        for sid, s in store.iterate("studios"):
            if s["name"].lower() == studio_id.lower():
                studio = s
                studio_id = sid
                break

    if not studio:
        click.echo(f"Studio not found: {studio_id}")
        return

    remove_studio(studio_id)
    click.echo(f"Removed studio: {studio['name']}")


@studio.command()
@click.argument("studio_id")
@click.option("--date", required=True, help="Date in YYYY-MM-DD format.")
@click.option("--start-time", required=True, help="Start time in HH:MM format (24h).")
@click.option("--end-time", required=True, help="End time in HH:MM format (24h).")
@click.option(
    "--reservation-type",
    required=True,
    type=click.Choice(["class", "individual"]),
    help=(
        "'class' for recurring classes, "
        "'individual' for one-time dancer/instructor bookings."
    ),
)
@click.option(
    "--reservation-id",
    required=True,
    help="Class ID or dancer/instructor ID.",
)
@click.pass_context
def reserve(
    ctx, studio_id, date, start_time, end_time, reservation_type, reservation_id
):
    """Reserve a time slot in a studio."""
    store = get_store()
    studio = store.get("studios", studio_id)

    if not studio:
        for sid, s in store.iterate("studios"):
            if s["name"].lower() == studio_id.lower():
                studio = s
                studio_id = sid
                break

    if not studio:
        click.echo(f"Studio not found: {studio_id}")
        return

    # Validate time format
    try:
        _parse_time(start_time)
        _parse_time(end_time)
    except ValueError as e:
        click.echo(f"Error: Invalid time format - {e}")
        return

    success = reserve_slot(
        studio_id=studio_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        reservation_type=reservation_type,
        reservation_id=reservation_id,
    )

    if success:
        click.echo(
            f"Reservation successful: {date} {start_time}-{end_time} "
            f"({reservation_type}: {reservation_id})"
        )
    else:
        conflicts = find_conflicts(studio_id, date, start_time, end_time)
        if conflicts:
            click.echo("Error: Time slot already reserved:")
            for c in conflicts:
                click.echo(
                    f"  - {c['date']} {c['start_time']}-{c['end_time']} "
                    f"({c['reservation_type']}: {c['reserved_by']})"
                )
        else:
            click.echo("Error: Could not reserve slot.")


@studio.command()
@click.argument("studio_id")
@click.option("--date", required=True, help="Date in YYYY-MM-DD format.")
@click.option("--start-time", required=True, help="Start time in HH:MM format (24h).")
@click.option("--end-time", required=True, help="End time in HH:MM format (24h).")
@click.option("--reservation-id", required=True, help="The reservation ID to cancel.")
@click.pass_context
def cancel(ctx, studio_id, date, start_time, end_time, reservation_id):
    """Cancel a reservation."""
    store = get_store()
    studio = store.get("studios", studio_id)

    if not studio:
        for sid, s in store.iterate("studios"):
            if s["name"].lower() == studio_id.lower():
                studio = s
                studio_id = sid
                break

    if not studio:
        click.echo(f"Studio not found: {studio_id}")
        return

    success = cancel_reservation(
        studio_id=studio_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        reservation_id=reservation_id,
    )

    if success:
        click.echo(f"Reservation cancelled: {date} {start_time}-{end_time}")
    else:
        click.echo("Error: Reservation not found.")


@studio.command()
@click.argument("studio_id")
@click.pass_context
def schedule(ctx, studio_id):
    """Show full studio schedule."""
    store = get_store()
    studio = store.get("studios", studio_id)

    if not studio:
        for sid, s in store.iterate("studios"):
            if s["name"].lower() == studio_id.lower():
                studio = s
                studio_id = sid
                break

    if not studio:
        click.echo(f"Studio not found: {studio_id}")
        return

    schedule = get_studio_schedule(studio_id)

    if not schedule:
        click.echo(f"No scheduled reservations for {studio['name']}.")
        return

    headers = ["Date", "Time", "Duration", "Type", "Reserved By"]
    rows = []
    for slot in schedule:
        duration = slot.get("duration_minutes", 0)
        hours, mins = divmod(duration, 60)
        dur_str = f"{hours}h {mins}m" if hours else f"{mins}m"

        # Try to resolve the reservation name
        reserved_by = slot.get("reserved_by", "")
        res_type = slot.get("reservation_type", "")
        if reserved_by:
            if res_type == "class":
                cls = store.get("classes", reserved_by)
                if cls:
                    reserved_by = cls["name"]
            elif res_type == "individual":
                dancer = store.get("dancers", reserved_by)
                if not dancer:
                    instructor = store.get("instructors", reserved_by)
                    if instructor:
                        reserved_by = instructor["name"]
                    else:
                        reserved_by = f"{reserved_by} (unknown)"
                else:
                    reserved_by = dancer["name"]

        rows.append(
            [
                slot.get("date", ""),
                f'{slot["start_time"]}-{slot["end_time"]}',
                dur_str,
                res_type.title(),
                reserved_by or "Unknown",
            ]
        )

    click.echo(f"Schedule for {studio['name']}:")
    click.echo("")
    click.echo(render_table(headers, rows))


# -- Helpers ---------------------------------------------------------------


def _calc_duration(start_time: str, end_time: str) -> int:
    """Calculate duration in minutes between two HH:MM times."""
    start_h, start_m = _parse_time(start_time)
    end_h, end_m = _parse_time(end_time)
    return (end_h * 60 + end_m) - (start_h * 60 + start_m)


def _parse_time(time_str: str) -> Tuple[int, int]:
    """Parse HH:MM time string into (hours, minutes)."""
    parts = time_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_str}")
    return int(parts[0]), int(parts[1])


def _times_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    """Check if two time ranges overlap."""
    s1 = _parse_time(start1)
    e1 = _parse_time(end1)
    s2 = _parse_time(start2)
    e2 = _parse_time(end2)

    # Two intervals overlap if one starts before the other ends
    return s1 < e2 and s2 < e1


def _find_slot(schedule, date: str, start_time: str) -> dict:
    """Find a slot matching date and start_time."""
    for slot in schedule:
        if slot.get("date") == date and slot.get("start_time") == start_time:
            return slot
    return {}


def title(s: str) -> str:
    """Title-case helper that preserves known lowercase words."""
    lowercase = {"studio", "the"}
    return " ".join(w if w.lower() in lowercase else w.title() for w in s.split())
