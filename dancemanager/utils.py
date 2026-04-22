"""Shared utilities and helpers for Dance Manager.

Includes CSV import/export, CLI helpers, and utility functions used across modules.
"""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from dancemanager.models import (
    make_class_id,
    make_dance_id,
    make_dancer_id,
    make_team_id,
)
from dancemanager.store import DataStore

logger = logging.getLogger(__name__)

# ── CLI Helpers ───────────────────────────────────────────────────────────


_store_instance: Optional[DataStore] = None


def get_store(store_path: Optional[str] = None) -> DataStore:
    """Return a DataStore instance, supporting injection for tests."""
    global _store_instance
    ctx = click.get_current_context(silent=True)
    if ctx is not None:
        if hasattr(ctx, "store"):
            return ctx.store
        if ctx.obj is not None:
            obj_sp = ctx.obj.get("store_path") if isinstance(ctx.obj, dict) else None
            if obj_sp and _store_instance is None:
                _store_instance = DataStore(path=obj_sp)
                return _store_instance
    if _store_instance is not None:
        return _store_instance
    _store_instance = DataStore(
        path=store_path or str(Path(__file__).parent.parent / "data" / "store.json")
    )
    return _store_instance


def set_default_store(store: DataStore) -> None:
    """Inject a store for all subsequent get_store() calls (tests only)."""
    global _store_instance
    _store_instance = store


def reset_default_store() -> None:
    """Clear the injected store so get_store() starts fresh."""
    global _store_instance
    _store_instance = None


def render_table(headers, rows):
    """Return a formatted text table."""
    if not rows:
        return "(no results)"

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = str(cell)
            col_widths[i] = max(col_widths[i], len(cell_str))

    sep_line = "       ".join("-" * w for w in col_widths)
    header_line = "       ".join(
        str(h).ljust(col_widths[i]) for i, h in enumerate(headers)
    )
    row_lines = [
        "       ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        for row in rows
    ]

    return "\n".join([header_line, sep_line] + row_lines)


# ── CSV Import ──────────────────────────────────────────────────────────


def csv_import_classes(store, filepath):
    """Parse a class CSV and create classes + dancers in one pass.

    Expected format::

        Classical Ballet
        Alice
        Bob
        Carol

    (blank lines are skipped)

    Returns an import summary dict.
    """
    summary = {
        "created": {"classes": 0, "dancers": 0},
        "skipped": 0,
        "errors": 0,
    }

    with open(filepath) as fh:
        content = fh.read()

    classes = store.get_collection("classes")
    dancers = store.get_collection("dancers")
    dancer_names_seen = {}
    header_mode = True

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if header_mode:
            class_name = stripped
            class_id = make_class_id(class_name)
            classes[class_id] = {
                "id": class_id,
                "name": class_name,
                "team_ids": [],
                "dancer_ids": [],
                "instructor_id": None,
                "notes": "",
            }
            summary["created"]["classes"] += 1
            header_mode = False
            continue

        dancer_name = stripped
        dancer_id = make_dancer_id(dancer_name)

        if dancer_name in dancer_names_seen:
            summary["skipped"] += 1
            logger.warning("Duplicate dancer name skipped: %s", dancer_name)
            continue

        dancer_names_seen[dancer_name] = dancer_id
        dancers[dancer_id] = {
            "id": dancer_id,
            "name": dancer_name,
            "team_id": None,
            "class_ids": [],
            "notes": "",
        }
        summary["created"]["dancers"] += 1

    store.set_collection("classes", classes)
    store.set_collection("dancers", dancers)
    return summary


def csv_import_teams(store, filepath):
    """Parse a team CSV and create teams + dancers in one pass.

    Expected format::

        Jazz Ensemble
        Alice
        Bob

    Returns an import summary dict.
    """
    summary = {
        "created": {"teams": 0, "dancers": 0},
        "skipped": 0,
        "errors": 0,
    }

    with open(filepath) as fh:
        content = fh.read()

    teams = store.get_collection("teams")
    dancers = store.get_collection("dancers")
    dancer_names_seen = {}
    current_team_name = None
    current_team_id = None

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if current_team_name is None:
            current_team_name = stripped
            current_team_id = make_team_id(current_team_name)
            teams[current_team_id] = {
                "id": current_team_id,
                "name": current_team_name,
                "dancer_ids": [],
                "notes": "",
            }
            summary["created"]["teams"] += 1
            continue

        dancer_name = stripped
        dancer_id = make_dancer_id(dancer_name)

        if dancer_name in dancer_names_seen:
            summary["skipped"] += 1
            logger.warning("Duplicate dancer name skipped: %s", dancer_name)
            continue

        dancer_names_seen[dancer_name] = dancer_id
        dancers[dancer_id] = {
            "id": dancer_id,
            "name": dancer_name,
            "team_id": None,
            "class_ids": [],
            "notes": "",
        }
        summary["created"]["dancers"] += 1

        teams[current_team_id]["dancer_ids"].append(dancer_id)

    store.set_collection("teams", teams)
    store.set_collection("dancers", dancers)
    return summary


def csv_import_dancers(store, filepath):
    """Import dancers from a 2-column CSV: name, team_name (optional)."""
    summary = {"created": 0, "skipped": 0, "errors": 0}
    dancers = store.get_collection("dancers")

    with open(filepath) as fh:
        reader = csv.reader(fh)
        next(reader)  # skip header row
        for row in reader:
            if not row or len(row) < 1:
                summary["skipped"] += 1
                continue
            name = row[0].strip()
            if not name:
                summary["skipped"] += 1
                continue
            dancer_id = make_dancer_id(name)
            team_name = row[1].strip() if len(row) > 1 else ""
            dancers[dancer_id] = {
                "id": dancer_id,
                "name": name,
                "team_id": team_name if team_name else None,
                "class_ids": [],
                "notes": "",
            }
            summary["created"] += 1

    store.set_collection("dancers", dancers)
    return summary


# ── CSV Export ──────────────────────────────────────────────────────────


def csv_export_dancers(store, filepath):
    """Export all dancers to a CSV file."""
    dancers = store.get_collection("dancers")

    with open(filepath, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "name", "team_id", "class_ids", "notes"])
        for did, dancer in sorted(dancers.items(), key=lambda x: x[1]["name"]):
            writer.writerow(
                [
                    did,
                    dancer["name"],
                    dancer.get("team_id", "") or "",
                    ";".join(dancer.get("class_ids", [])),
                    dancer.get("notes", ""),
                ]
            )


def csv_export_teams(store, filepath):
    """Export all teams to a CSV file."""
    teams = store.get_collection("teams")

    with open(filepath, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "name", "dancer_ids", "notes"])
        for tid, team in sorted(teams.items(), key=lambda x: x[1]["name"]):
            writer.writerow(
                [
                    tid,
                    team["name"],
                    ";".join(team.get("dancer_ids", [])),
                    team.get("notes", ""),
                ]
            )


def csv_export_classes(store, filepath):
    """Export all classes to a CSV file."""
    classes = store.get_collection("classes")

    with open(filepath, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "id",
                "name",
                "team_ids",
                "dancer_ids",
                "instructor_id",
                "notes",
            ]
        )
        for cid, cls in sorted(classes.items(), key=lambda x: x[1]["name"]):
            writer.writerow(
                [
                    cid,
                    cls["name"],
                    ";".join(cls.get("team_ids", [])),
                    ";".join(cls.get("dancer_ids", [])),
                    cls.get("instructor_id", "") or "",
                    cls.get("notes", ""),
                ]
            )


def csv_export_dances(store, filepath):
    """Export all dances to a CSV file."""
    dances = store.get_collection("dances")

    with open(filepath, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "id",
                "name",
                "song_name",
                "instructor_id",
                "dancer_ids",
                "notes",
            ]
        )
        for did, dance in sorted(dances.items(), key=lambda x: x[1]["name"]):
            writer.writerow(
                [
                    did,
                    dance["name"],
                    dance.get("song_name", ""),
                    dance.get("instructor_id", ""),
                    ";".join(dance.get("dancer_ids", [])),
                    dance.get("notes", ""),
                ]
            )


def csv_export_recital(store, filepath, recital_id):
    """Export a recital schedule to a CSV file."""
    recital = store.get("recitals", recital_id)
    if recital is None:
        raise ValueError(f"Recital not found: {recital_id}")

    with open(filepath, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "position",
                "dance_id",
                "dance_name",
                "song_name",
                "dancer_ids",
            ]
        )
        for slot in sorted(
            recital.get("performance_order", []),
            key=lambda x: x["position"],
        ):
            dance_id = slot["dance_id"]
            dance = store.get("dances", dance_id)
            if dance:
                writer.writerow(
                    [
                        slot["position"],
                        dance_id,
                        dance["name"],
                        dance.get("song_name", ""),
                        ";".join(dance.get("dancer_ids", [])),
                    ]
                )


# ── Helpers ─────────────────────────────────────────────────────────────


def is_class_name(name):
    """Heuristic: a class name typically is short with no whitespace."""
    return len(name) < 30 and " " not in name
