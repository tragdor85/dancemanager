"""Recital management and scheduling engine.

Provides commands to add, list, show, remove, and reorder recitals,
plus an auto-scheduler that ensures every dancer gets at least 4
dances between performances.
"""

import json
from typing import Any, Dict, List, Optional

import click

from dancemanager.models import make_recital_id
from dancemanager.utils import get_store, render_table


MIN_BUFFER = 4  # Minimum dances between a dancer's performances


# ── CLI commands ────────────────────────────────────────────────────────


@click.group()
def recital():
    """Recital scheduling commands."""
    pass


@recital.command()
@click.argument("name")
@click.pass_context
def add(ctx, name):
    """Create a new recital."""
    store = get_store()
    recitals_list = store.get_collection("recitals")

    recital_id = make_recital_id(name)
    store.execute(
        "INSERT INTO recitals (id, name, performance_order, notes) "
        "VALUES (?, ?, ?, ?)",
        (recital_id, name.title(), "[]", ""),
    )

    store.save()
    click.echo(f"Created recital: {name} (ID: {recital_id})")


@recital.command("list")
@click.pass_context
def list_recitals(ctx):
    """List all recitals."""
    store = get_store()
    recitals_list = store.get_collection("recitals")

    if not recitals_list or len(recitals_list) == 0:
        click.echo("No recitals found.")
        return

    headers = ["ID", "Name", "Dances", "Notes"]
    rows = []
    for rid, rec in sorted(recitals_list.items(), key=lambda x: x[1]["name"]):
        po = rec.get("performance_order", [])
        dances_count = len(po) if isinstance(po, list) else 0
        rows.append(
            [
                rid,
                rec["name"],
                dances_count,
                rec.get("notes", ""),
            ]
        )

    click.echo(render_table(headers, rows))


@recital.command()
@click.argument("recital_id")
@click.pass_context
def show(ctx, recital_id):
    """Show details for a single recital."""
    store = get_store()
    rec = store.get("recitals", recital_id)

    if rec is None:
        for rid, r in store.iterate("recitals"):
            if r["name"].lower() == recital_id.lower():
                rec = r
                break
        if rec is None:
            click.echo(f"Recital not found: {recital_id}")
            return

    click.echo(f"Name: {rec['name']}")
    order = rec.get("performance_order", [])
    if order:
        for slot in sorted(order, key=lambda x: x["position"]):
            dance = store.get("dances", slot["dance_id"])
            if dance:
                click.echo(
                    f"  {slot['position']}. {dance['name']} "
                    f"({dance.get('song_name', '')})"
                )
    else:
        click.echo("  (no dances scheduled)")


@recital.command()
@click.argument("recital_id")
@click.pass_context
def remove(ctx, recital_id):
    """Remove a recital."""
    store = get_store()
    rec = store.get("recitals", recital_id)

    if rec is None:
        for rid, r in store.iterate("recitals"):
            if r["name"].lower() == recital_id.lower():
                rec = r
                break
        if rec is None:
            click.echo(f"Recital not found: {recital_id}")
            return

    store.execute("DELETE FROM recitals WHERE id = ?", (recital_id,))
    store.save()
    click.echo(f"Removed recital: {rec['name']}")


@recital.command()
@click.argument("recital_id")
@click.argument("dance_id")
@click.pass_context
def add_dance(ctx, recital_id, dance_id):
    """Add a dance to a recital's performance order."""
    store = get_store()
    recitals_list = store.get_collection("recitals")
    dances_list = store.get_collection("dances")

    rec = store.get("recitals", recital_id)
    if rec is None:
        click.echo(f"Recital not found: {recital_id}")
        return

    dance = store.get("dances", dance_id)
    if dance is None:
        click.echo(f"Dance not found: {dance_id}")
        return

    order = rec.get("performance_order", [])
    for slot in order:
        if slot["dance_id"] == dance_id:
            click.echo(f"Dance already in recital: {dance_id}")
            return

    position = len(order) + 1
    order.append({"dance_id": dance_id, "position": position})
    store.execute(
        "UPDATE recitals SET performance_order = ? WHERE id = ?",
        (json.dumps(order), recital_id),
    )
    click.echo(
        f"Added dance '{dance['name']}' to recital '{rec['name']}' "
        f"(position {position})."
    )


@recital.command()
@click.argument("recital_id")
@click.argument("position")
@click.argument("dance_id")
@click.pass_context
def reorder(ctx, recital_id, position, dance_id):
    """Reorder a dance to a new position in the recital."""
    store = get_store()
    recitals_list = store.get_collection("recitals")

    rec = store.get("recitals", recital_id)
    if rec is None:
        click.echo(f"Recital not found: {recital_id}")
        return

    order = rec.get("performance_order", [])
    old_pos = None
    for i, slot in enumerate(order):
        if slot["dance_id"] == dance_id:
            old_pos = i
            break

    if old_pos is None:
        click.echo(f"Dance not in recital: {dance_id}")
        return

    del order[old_pos]
    new_pos = int(position) - 1
    order.insert(new_pos, {"dance_id": dance_id, "position": position})

    for i, slot in enumerate(order):
        slot["position"] = i + 1

    store.execute(
        "UPDATE recitals SET performance_order = ? WHERE id = ?",
        (json.dumps(order), recital_id),
    )
    click.echo(f"Reordered '{dance_id}' to position {position}.")


@recital.command()
@click.argument("recital_id")
@click.pass_context
def generate_schedule(ctx, recital_id):
    """Auto-generate the optimal performance order."""
    store = get_store()
    recitals_list = store.get_collection("recitals")

    rec = store.get("recitals", recital_id)
    if rec is None:
        click.echo(f"Recital not found: {recital_id}")
        return

    dances_list = store.get_collection("dances")
    dance_ids = [s["dance_id"] for s in rec.get("performance_order", [])]

    if len(dance_ids) < 2:
        click.echo("Need at least 2 dances to generate a schedule.")
        return

    # Build dancer -> dances map
    dancer_dances: Dict[str, List[str]] = {}
    for did in dance_ids:
        dance = store.get("dances", did)
        if dance is None:
            continue
        for dancer_id in dance.get("dancer_ids", []):
            if dancer_id not in dancer_dances:
                dancer_dances[dancer_id] = []
            dancer_dances[dancer_id].append(did)

    result = greedy_schedule(dance_ids, dancer_dances, MIN_BUFFER)
    if result is None:
        click.echo(
            "Could not generate a valid schedule. "
            "Consider adding more dances or removing conflicts."
        )
        return

    # Save the schedule back to the store
    store.execute(
        "UPDATE recitals SET performance_order = ? WHERE id = ?",
        (
            json.dumps(
                [{"dance_id": did, "position": i + 1} for i, did in enumerate(result)]
            ),
            recital_id,
        ),
    )
    store.save()

    # Print formatted schedule
    click.echo(f"\nRecital: {rec['name']}")
    click.echo("")
    click.echo(f"{'Position':<10} {'Dance':<25} {'Song':<25} Performers")
    click.echo("-" * 80)

    for i, did in enumerate(result):
        dance = store.get("dances", did)
        if dance is None:
            continue
        song = dance.get("song_name", "")
        dancers_str = ", ".join(dance.get("dancer_ids", []))
        buffer_note = _get_buffer_note(
            result, i, dance.get("dancer_ids", []), dancer_dances
        )
        click.echo(
            f"{i + 1:<10} {dance['name']:<25} {song:<25} {dancers_str}{buffer_note}"
        )

    click.echo("")
    click.echo("Validation Report:")
    for dancer_id in sorted(dancer_dances):
        d_dances = dancer_dances[dancer_id]
        positions = []
        for pos, did in enumerate(result):
            if did in d_dances:
                positions.append(pos + 1)
        for idx, pos in enumerate(positions):
            for next_pos in positions[idx + 1 :]:
                gap = next_pos - pos - 1
                if gap < MIN_BUFFER:
                    click.echo(
                        f"  WARNING: {dancer_id} has only "
                        f"{gap} dance(s) buffer between "
                        f"position {pos} and {next_pos}!"
                    )
    click.echo("  Validation complete.")


# ── Scheduling algorithm ───────────────────────────────────────────────────


def _score_dance(
    dance_id: str,
    schedule: List[str],
    dancer_dances: Dict[str, List[str]],
    min_buffer: int,
) -> int:
    """Score a dance: count how many dancers are ready (4+ buffer)."""
    score = 0
    for dancer_id, d_list in dancer_dances.items():
        if dance_id not in d_list:
            continue
        d_positions = [i + 1 for i, s in enumerate(schedule) if s in d_list]
        if not d_positions:
            score += 1
            continue
        last_pos = max(d_positions)
        gap = len(schedule) - last_pos
        if gap >= min_buffer:
            score += 1
    return score


def greedy_schedule(
    dance_ids: List[str],
    dancer_dances: Dict[str, List[str]],
    min_buffer: int,
) -> Optional[List[str]]:
    """Greedy scheduling with backtracking fallback.

    Returns an ordered list of dance IDs, or None if no valid
    schedule could be found.
    """
    if not dance_ids:
        return []

    def _try_schedule(
        remaining: List[str],
        schedule: List[str],
        dancer_dances: Dict[str, List[str]],
        min_buffer: int,
    ) -> Optional[List[str]]:
        if not remaining:
            return list(schedule)

        scored = []
        for did in remaining:
            score = _score_dance(did, schedule, dancer_dances, min_buffer)
            scored.append((score, did))
        scored.sort(key=lambda x: -x[0])

        for _score, did in scored:
            new_remaining = [r for r in remaining if r != did]
            schedule.append(did)
            result = _try_schedule(new_remaining, schedule, dancer_dances, min_buffer)
            if result is not None:
                return result
            schedule.pop()

        return None

    return _try_schedule(list(dance_ids), [], dancer_dances, min_buffer)


# ── Helpers ───────────────────────────────────────────────────────────────


def _get_buffer_note(result, position, dancer_ids, dancer_dances):
    """Return a buffer note string for a dancer in the schedule."""
    if not dancer_ids:
        return ""
    notes = []
    for dancer_id in dancer_ids:
        if dancer_id not in dancer_dances:
            continue
        positions = []
        for idx, did in enumerate(result):
            if did in dancer_dances[dancer_id]:
                positions.append(idx)
        if len(positions) > 1:
            for i, pos in enumerate(positions):
                if pos == position and i > 0:
                    gap = positions[i] - positions[i - 1] - 1
                    notes.append(f"  ({dancer_id}: {gap} dance(s) buffer)")
        elif len(positions) == 1 and positions[0] == position:
            notes.append(f"  ({dancer_id}: 1st performance)")
    return "".join(notes)


def save_recital(store, recital_id, recital_data):
    """Persist a recital to the store."""
    recitals_coll = store.get_collection("recitals")
    recitals_coll[recital_id] = recital_data
    store.set_collection("recitals", recitals_coll)


def get_recital(store, recital_id, recitals_coll):
    """Find a recital by ID or name."""
    rec = recitals_coll.get(recital_id)
    if rec is not None:
        return rec
    for rid, r in recitals_coll.items():
        if r["name"].lower() == recital_id.lower():
            return r
    return None
