"""Data migration - populate SQLite database from JSON store."""

import json
from pathlib import Path


def migrate_up(conn):
    """Migrate data from JSON to SQLite."""
    cursor = conn.cursor()

    # Read JSON store
    json_path = Path(__file__).parent.parent / "data" / "store.json"
    if not json_path.exists():
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    # Collections are stored as dicts: {id: {...}, ...}
    def get_items(collection):
        items = data.get(collection, {})
        if isinstance(items, dict):
            return list(items.values())
        return items

    # Migrate instructors
    for instructor in get_items("instructors"):
        cursor.execute(
            "INSERT OR REPLACE INTO instructors (id, name, notes) VALUES (?, ?, ?)",
            (instructor["id"], instructor["name"], instructor.get("notes", "")),
        )

    # Migrate teams
    for team in get_items("teams"):
        cursor.execute(
            "INSERT OR REPLACE INTO teams (id, name, notes) VALUES (?, ?, ?)",
            (team["id"], team["name"], team.get("notes", "")),
        )

    # Migrate dancers
    for dancer in get_items("dancers"):
        cursor.execute(
            "INSERT OR REPLACE INTO dancers (id, name, team_id, notes) VALUES (?, ?, ?, ?)",
            (
                dancer["id"],
                dancer["name"],
                dancer.get("team_id"),
                dancer.get("notes", ""),
            ),
        )

    # Migrate classes
    for cls in get_items("classes"):
        cursor.execute(
            "INSERT OR REPLACE INTO classes (id, name, instructor_id, notes) VALUES (?, ?, ?, ?)",
            (cls["id"], cls["name"], cls.get("instructor_id"), cls.get("notes", "")),
        )

    # Migrate dances
    for dance in get_items("dances"):
        cursor.execute(
            "INSERT OR REPLACE INTO dances (id, name, song_name, instructor_id, notes) VALUES (?, ?, ?, ?, ?)",
            (
                dance["id"],
                dance["name"],
                dance["song_name"],
                dance.get("instructor_id"),
                dance.get("notes", ""),
            ),
        )

    # Migrate recitals
    for recital in get_items("recitals"):
        cursor.execute(
            "INSERT OR REPLACE INTO recitals (id, name, notes) VALUES (?, ?, ?)",
            (recital["id"], recital["name"], recital.get("notes", "")),
        )

    # Migrate dance assignments (many-to-many: dances <-> dancers)
    for dance in get_items("dances"):
        dance_id = dance["id"]
        for dancer_id in dance.get("dancer_ids", []):
            cursor.execute(
                "INSERT OR IGNORE INTO dance_assignments (dance_id, dancer_id) VALUES (?, ?)",
                (dance_id, dancer_id),
            )

    # Migrate class-team assignments (many-to-many: classes <-> teams)
    for cls in get_items("classes"):
        class_id = cls["id"]
        for team_id in cls.get("team_ids", []):
            cursor.execute(
                "INSERT OR IGNORE INTO class_team_assignments (class_id, team_id) VALUES (?, ?)",
                (class_id, team_id),
            )

    # Migrate class-dancer assignments (many-to-many: classes <-> dancers)
    for cls in get_items("classes"):
        class_id = cls["id"]
        for dancer_id in cls.get("dancer_ids", []):
            cursor.execute(
                "INSERT OR IGNORE INTO class_dancer_assignments (class_id, dancer_id) VALUES (?, ?)",
                (class_id, dancer_id),
            )

    # Migrate recital dances (recital performance order)
    for recital in get_items("recitals"):
        recital_id = recital["id"]
        for item in recital.get("performance_order", []):
            dance_id = item["dance_id"]
            position = item["position"]
            cursor.execute(
                "INSERT OR IGNORE INTO recital_dances (recital_id, dance_id, position) VALUES (?, ?, ?)",
                (recital_id, dance_id, position),
            )

    # Clear all data from metadata table and set version
    cursor.execute("DELETE FROM metadata")
    cursor.execute(
        "INSERT INTO metadata (key, value) VALUES (?, ?)",
        ("version", '"1.0.0"'),
    )
    conn.commit()


def migrate_down(conn):
    """Drop all data and tables."""
    cursor = conn.cursor()

    # Drop all tables
    cursor.execute("DROP TABLE IF EXISTS recital_dances")
    cursor.execute("DROP TABLE IF EXISTS class_dancer_assignments")
    cursor.execute("DROP TABLE IF EXISTS class_team_assignments")
    cursor.execute("DROP TABLE IF EXISTS dance_assignments")
    cursor.execute("DROP TABLE IF EXISTS schedules")
    cursor.execute("DROP TABLE IF EXISTS studios")
    cursor.execute("DROP TABLE IF EXISTS recitals")
    cursor.execute("DROP TABLE IF EXISTS dances")
    cursor.execute("DROP TABLE IF EXISTS classes")
    cursor.execute("DROP TABLE IF EXISTS dancers")
    cursor.execute("DROP TABLE IF EXISTS teams")
    cursor.execute("DROP TABLE IF EXISTS instructors")

    # Clear metadata
    cursor.execute("DELETE FROM metadata")
    conn.commit()
