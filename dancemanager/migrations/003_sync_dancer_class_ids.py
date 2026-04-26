"""Data migration - sync dancer class_ids from classes table.

Rebuilds each dancer's class_ids by scanning all classes for:
- Direct dancer assignments (class.dancer_ids)
- Team-based assignments (class.team_ids -> team.dancer_ids)
"""

import json


def migrate_up(conn):
    """Sync all dancers' class_ids from the authoritative classes data."""
    cursor = conn.cursor()

    # Step 1: Initialize missing class_ids for CLI-created dancers
    cursor.execute("UPDATE dancers SET class_ids = '[]' WHERE class_ids IS NULL")

    # Step 2: Build team -> dancer mapping
    cursor.execute("SELECT id, dancer_ids FROM teams")
    teams = {}
    for row in cursor.fetchall():
        team_id, raw = row
        if raw:
            try:
                dancers_in_team = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                dancers_in_team = []
        else:
            dancers_in_team = []
        teams[team_id] = dancers_in_team

    # Step 3: For each class, find all member dancers and update their class_ids
    cursor.execute("SELECT id, dancer_ids, team_ids FROM classes")
    for row in cursor.fetchall():
        class_id, raw_dancer_ids, raw_team_ids = row

        # Collect direct dancer assignments
        if raw_dancer_ids:
            try:
                direct_dancers = json.loads(raw_dancer_ids)
            except (json.JSONDecodeError, TypeError):
                direct_dancers = []
        else:
            direct_dancers = []

        # Collect dancers from assigned teams
        team_dancers = set()
        if raw_team_ids:
            try:
                team_ids = json.loads(raw_team_ids)
            except (json.JSONDecodeError, TypeError):
                team_ids = []
            for tid in team_ids:
                if tid in teams:
                    team_dancers.update(teams[tid])

        # Union of all dancers in this class
        all_class_dancers = set(direct_dancers) | team_dancers

        # Update each dancer's class_ids
        for dancer_id in all_class_dancers:
            cursor.execute("SELECT class_ids FROM dancers WHERE id = ?", (dancer_id,))
            result = cursor.fetchone()
            if result is None:
                continue

            raw_class_ids = result[0]
            try:
                current_class_ids = json.loads(raw_class_ids) if raw_class_ids else []
            except (json.JSONDecodeError, TypeError):
                current_class_ids = []

            if class_id not in current_class_ids:
                current_class_ids.append(class_id)
                cursor.execute(
                    "UPDATE dancers SET class_ids = ? WHERE id = ?",
                    (json.dumps(current_class_ids), dancer_id),
                )

    conn.commit()


def migrate_down(conn):
    """Reset all class_ids to NULL so app falls back to showing 0."""
    cursor = conn.cursor()
    cursor.execute("UPDATE dancers SET class_ids = NULL")
    conn.commit()
