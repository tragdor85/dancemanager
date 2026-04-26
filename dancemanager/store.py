"""SQLite persistence layer for Dance Manager.

Provides load/save with typed getters/setters and relationship support.
"""

import json
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dancemanager.models import DEFAULT_STORE_SCHEMA

CURRENT_VERSION = "1.0.0"

StorePath = Optional[Union[str, os.PathLike[str]]]


class StoreError(Exception):
    """Base exception for store-related errors."""

    pass


class StoreVersionError(StoreError):
    """Raised when the stored version is incompatible."""

    pass


# Global singleton instance for get_store()
_store_instance: Optional["DataStore"] = None


def _row_to_dict(cursor, row) -> Dict[str, Any]:
    """Convert a cursor row to a dict using column names."""
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


class DataStore:
    """SQLite store for Dance Manager."""

    def __init__(self, path: StorePath = None):
        global _store_instance
        if path is None:
            self._path = Path(__file__).parent.parent / "data" / "store.db"
        else:
            self._path = Path(path)

        # Ensure parent directory exists
        self._path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.commit()
        # Maintain _data for test compatibility (in-memory cache of schema)
        self._data = dict(DEFAULT_STORE_SCHEMA)
        self._create_tables()
        self._create_indexes()
        self._migrate()

    def close(self):
        """Close the database connection."""
        self._conn.close()

    # -- public helpers --------------------------------------------------

    def get(self, collection: str, key: str) -> Optional[Dict]:
        """Return a copy of the item at *collection*[*key*]."""
        result = self._query(f"SELECT * FROM {collection} WHERE id = ?", (key,))
        if result:
            row = dict(result[0])
            # Filter out None/NULL values but keep 'id' and 'extra' since they're needed
            row = {k: v for k, v in row.items() if v is not None}
            # Merge extra fields back from the 'extra' column
            extra_str = row.pop("extra", None)
            if extra_str:
                try:
                    extra = json.loads(extra_str)
                    row.update(extra)
                except (json.JSONDecodeError, TypeError):
                    pass
            # Deserialize JSON list fields back to Python lists
            for field in ("dancer_ids", "class_ids", "team_ids", "performance_order"):
                val = row.get(field)
                if isinstance(val, str):
                    try:
                        row[field] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        row[field] = [] if field != "performance_order" else {}
            # Try to deserialize notes if it's a JSON string
            notes_val = row.get("notes")
            if isinstance(notes_val, str):
                try:
                    parsed = json.loads(notes_val)
                    if not isinstance(parsed, str):
                        row["notes"] = parsed
                except (json.JSONDecodeError, TypeError):
                    pass
            return row
        return None

    def set(self, collection: str, key: str, value: Dict) -> None:
        """Save *value* into *collection* under *key*, then persist."""
        # Build column list and values dynamically based on value keys
        columns = []
        params = []

        # Known schema fields that map directly to table columns
        known_fields = {
            "id", "name", "song_name", "instructor_id", "team_id",
            "dancer_ids", "class_ids", "team_ids", "performance_order", "notes"
        }

        # Always use key as id if not explicitly provided in value
        row_id = value.get("id", key)
        columns.append("id")
        params.append(row_id)
        # Provide defaults for required fields to handle edge cases
        if "name" in value:
            columns.append("name")
            params.append(value["name"])
        else:
            columns.append("name")
            params.append("")
        if "song_name" in value:
            columns.append("song_name")
            params.append(value["song_name"])
        elif collection == "dances":
            columns.append("song_name")
            params.append("")
        if "instructor_id" in value:
            columns.append("instructor_id")
            params.append(value["instructor_id"])
        if "team_id" in value:
            columns.append("team_id")
            params.append(value["team_id"])
        # Serialize list fields to JSON strings for storage
        if "dancer_ids" in value:
            val = value["dancer_ids"]
            if isinstance(val, (list, tuple)):
                val = json.dumps(list(val))
            columns.append("dancer_ids")
            params.append(val)
        if "class_ids" in value:
            val = value["class_ids"]
            if isinstance(val, (list, tuple)):
                val = json.dumps(list(val))
            columns.append("class_ids")
            params.append(val)
        if "team_ids" in value:
            val = value["team_ids"]
            if isinstance(val, (list, tuple)):
                val = json.dumps(list(val))
            columns.append("team_ids")
            params.append(val)
        if "performance_order" in value:
            val = value["performance_order"]
            if isinstance(val, (list, tuple)):
                # Handle both legacy format (list of dance_id strings) and new format (list of dicts)
                normalized = []
                for p in val:
                    if isinstance(p, dict):
                        normalized.append(p)
                    else:
                        normalized.append({"dance_id": str(p), "position": 0})
                val = json.dumps(normalized)
            columns.append("performance_order")
            params.append(val)
        if "notes" in value:
            val = value["notes"]
            # Serialize dict values to JSON for storage
            if isinstance(val, (dict, list)):
                val = json.dumps(val)
            columns.append("notes")
            params.append(val)

        # Collect unknown fields and store as JSON in extra column
        extra_fields = {k: v for k, v in value.items() if k not in known_fields}
        if extra_fields:
            columns.append("extra")
            params.append(json.dumps(extra_fields))

        placeholders = ", ".join(["?" for _ in columns])
        sql = f"INSERT OR REPLACE INTO {collection} ({', '.join(columns)}) VALUES ({placeholders})"

        self._conn.execute(sql, params)
        self._save()

    def get_collection(self, collection: str) -> Dict[str, Any]:
        """Return a deep copy of the entire collection dict."""
        result = self._query(f"SELECT * FROM {collection}")
        out = {}
        for row in result:
            item = dict(row)
            # Filter out None/NULL values but keep 'id' since templates need it
            item_id = item.pop("id", None)
            item = {k: v for k, v in item.items() if v is not None and k != "extra"}
            # Add id back to the item so templates can access dancer.id, etc.
            if item_id is not None:
                item["id"] = item_id
            # Merge extra fields back from the 'extra' column
            extra_str = item.pop("extra", None)
            if extra_str:
                try:
                    extra = json.loads(extra_str)
                    item.update(extra)
                except (json.JSONDecodeError, TypeError):
                    pass
            # Deserialize JSON list fields back to Python lists
            for field in ("dancer_ids", "class_ids", "team_ids", "performance_order"):
                val = item.get(field)
                if isinstance(val, str):
                    try:
                        item[field] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        item[field] = [] if field != "performance_order" else {}
            out[item_id] = item
        return out

    def set_collection(self, collection: str, data: List[Dict]) -> None:
        """Replace an entire collection and persist."""
        self._conn.execute(f"DELETE FROM {collection}")
        for item in data:
            # Build column list and values dynamically
            columns = []
            params = []

            if "id" in item:
                columns.append("id")
                params.append(item["id"])
            if "name" in item:
                columns.append("name")
                params.append(item["name"])
            if "song_name" in item:
                columns.append("song_name")
                params.append(item["song_name"])
            if "instructor_id" in item:
                columns.append("instructor_id")
                params.append(item["instructor_id"])
            if "team_id" in item:
                columns.append("team_id")
                params.append(item["team_id"])
            # Serialize list fields to JSON strings for storage
            if "dancer_ids" in item:
                val = item["dancer_ids"]
                if isinstance(val, (list, tuple)):
                    val = json.dumps(list(val))
                columns.append("dancer_ids")
                params.append(val)
            if "class_ids" in item:
                val = item["class_ids"]
                if isinstance(val, (list, tuple)):
                    val = json.dumps(list(val))
                columns.append("class_ids")
                params.append(val)
            if "team_ids" in item:
                val = item["team_ids"]
                if isinstance(val, (list, tuple)):
                    val = json.dumps(list(val))
                columns.append("team_ids")
                params.append(val)
            if "performance_order" in item:
                val = item["performance_order"]
                if isinstance(val, (list, tuple)):
                    val = json.dumps([dict(p) for p in val])
                columns.append("performance_order")
                params.append(val)
            if "notes" in item:
                columns.append("notes")
                params.append(item["notes"])

            placeholders = ", ".join(["?" for _ in columns])
            sql = f"INSERT INTO {collection} ({', '.join(columns)}) VALUES ({placeholders})"
            self._conn.execute(sql, params)

        self._conn.commit()

    def get_all(self, collection: str) -> List[Dict]:
        """Return every item in *collection* as a list of copies."""
        return list(self.get_collection(collection).values())

    def iterate(self, collection: str):
        """Yield (key, value) pairs for *collection*."""
        coll = self.get_collection(collection)
        for key in sorted(coll.keys(), key=lambda k: coll[k].get("name", "")):
            yield key, dict(coll[key])

    def delete(self, collection: str, key: str) -> bool:
        """Remove an item. Returns True if it existed."""
        existing = self.get(collection, key)
        if existing is None:
            return False
        self._conn.execute(f"DELETE FROM {collection} WHERE id = ?", (key,))
        self._conn.commit()
        return True

    def save(self) -> None:
        """Persist current in-memory state to disk."""
        self._conn.commit()

    def _save(self):
        """Save and create a WAL backup for crash safety."""
        self._conn.commit()
        # In WAL mode, SQLite handles concurrent access well.
        # Create a backup copy if the file exists and is non-empty.
        if self._path.exists() and self._path.stat().st_size > 0:
            backup_path = str(self._path) + ".bak"
            try:
                shutil.copy2(str(self._path), backup_path)
            except (OSError, shutil.Error):
                pass  # Non-critical, continue

    def get_version(self) -> str:
        """Return the current schema version string."""
        result = self._query("SELECT value FROM metadata WHERE key = ?", ("version",))
        if result:
            row = dict(result[0])
            return json.loads(row["value"])
        return CURRENT_VERSION

    # -- relationship helpers ---------------------------------------------

    def get_dancer_teams(self, dancer_id: str) -> List[Dict]:
        """Get all teams for a dancer."""
        result = self._query(
            """
            SELECT * FROM teams
            WHERE id IN (SELECT team_id FROM dancers WHERE id = ?)
            """
        )
        return [dict(row) for row in result]

    def get_dancer_classes(self, dancer_id: str) -> List[Dict]:
        """Get all classes for a dancer."""
        result = self._query(
            """
            SELECT * FROM classes
            WHERE id IN (SELECT class_id FROM class_dancer_assignments WHERE dancer_id = ?)
            """
        )
        return [dict(row) for row in result]

    def get_dancer_dances(self, dancer_id: str) -> List[Dict]:
        """Get all dances for a dancer."""
        result = self._query(
            """
            SELECT * FROM dances
            WHERE id IN (SELECT dance_id FROM dance_assignments WHERE dancer_id = ?)
            """
        )
        return [dict(row) for row in result]

    def get_team_classes(self, team_id: str) -> List[Dict]:
        """Get all classes for a team."""
        result = self._query(
            """
            SELECT * FROM classes
            WHERE id IN (SELECT class_id FROM class_team_assignments WHERE team_id = ?)
            """
        )
        return [dict(row) for row in result]

    def get_team_dancers(self, team_id: str) -> List[Dict]:
        """Get all dancers for a team."""
        result = self._query(
            """
            SELECT * FROM dancers
            WHERE team_id = ?
            """
        )
        return [dict(row) for row in result]

    def get_recital_dances(self, recital_id: str) -> List[Dict]:
        """Get dances in recital order."""
        result = self._query(
            """
            SELECT rd.*, d.*
            FROM recital_dances rd
            JOIN dances d ON rd.dance_id = d.id
            WHERE rd.recital_id = ?
            ORDER BY rd.position
            """
        )
        return [dict(row) for row in result]

    # -- internal --------------------------------------------------------

    def _create_tables(self):
        """Create all tables."""
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS instructors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                class_ids TEXT,
                dance_ids TEXT,
                notes TEXT,
                extra TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                dancer_ids TEXT,
                notes TEXT,
                extra TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dancers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                team_id TEXT,
                class_ids TEXT,
                notes TEXT,
                extra TEXT,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                instructor_id TEXT,
                team_ids TEXT,
                dancer_ids TEXT,
                notes TEXT,
                extra TEXT,
                FOREIGN KEY (instructor_id) REFERENCES instructors(id)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dances (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                song_name TEXT NOT NULL,
                instructor_id TEXT,
                dancer_ids TEXT,
                notes TEXT,
                extra TEXT,
                FOREIGN KEY (instructor_id) REFERENCES instructors(id)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recitals (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                performance_order TEXT,
                notes TEXT,
                extra TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dance_assignments (
                dance_id TEXT NOT NULL,
                dancer_id TEXT NOT NULL,
                PRIMARY KEY (dance_id, dancer_id),
                FOREIGN KEY (dance_id) REFERENCES dances(id),
                FOREIGN KEY (dancer_id) REFERENCES dancers(id)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS class_team_assignments (
                class_id TEXT NOT NULL,
                team_id TEXT NOT NULL,
                PRIMARY KEY (class_id, team_id),
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (team_id) REFERENCES teams(id)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS class_dancer_assignments (
                class_id TEXT NOT NULL,
                dancer_id TEXT NOT NULL,
                PRIMARY KEY (class_id, dancer_id),
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (dancer_id) REFERENCES dancers(id)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recital_dances (
                recital_id TEXT NOT NULL,
                dance_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (recital_id, dance_id, position),
                FOREIGN KEY (recital_id) REFERENCES recitals(id),
                FOREIGN KEY (dance_id) REFERENCES dances(id)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                notes TEXT,
                extra TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS studios (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                notes TEXT,
                extra TEXT
            )
            """
        )

        # Set version in metadata
        self._conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("version", json.dumps(CURRENT_VERSION)),
        )
        self._conn.commit()

    def _create_indexes(self):
        """Create indexes for common queries."""
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_dancers_team_id ON dancers(team_id)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_classes_instructor_id ON classes(instructor_id)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_dances_instructor_id ON dances(instructor_id)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_recital_dances_recital_id ON recital_dances(recital_id)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_class_team_assignments_class_id ON class_team_assignments(class_id)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_class_dancer_assignments_class_id ON class_dancer_assignments(class_id)"
        )
        self._conn.commit()

    def _migrate(self):
        """Ensure metadata version is set. Data should already be in tables."""
        result = self._query("SELECT value FROM metadata WHERE key = ?", ("version",))
        if not result:
            # No version set - data may need to be migrated from JSON
            json_path = self._path.with_suffix(".json")
            if json_path.exists():
                try:
                    with open(json_path, "r") as fh:
                        data = json.load(fh)

                    def get_items(collection):
                        items = data.get(collection, {})
                        if isinstance(items, dict):
                            return list(items.values())
                        return items

                    # Migrate instructors
                    for instructor in get_items("instructors"):
                        self._conn.execute(
                            "INSERT OR REPLACE INTO instructors (id, name, notes) VALUES (?, ?, ?)",
                            (instructor["id"], instructor["name"], instructor.get("notes", "")),
                        )

                    # Migrate teams
                    for team in get_items("teams"):
                        self._conn.execute(
                            "INSERT OR REPLACE INTO teams (id, name, notes) VALUES (?, ?, ?)",
                            (team["id"], team["name"], team.get("notes", "")),
                        )

                    # Migrate dancers
                    for dancer in get_items("dancers"):
                        self._conn.execute(
                            "INSERT OR REPLACE INTO dancers (id, name, team_id, notes) VALUES (?, ?, ?, ?)",
                            (dancer["id"], dancer["name"], dancer.get("team_id"), dancer.get("notes", "")),
                        )

                    # Migrate classes
                    for cls in get_items("classes"):
                        self._conn.execute(
                            "INSERT OR REPLACE INTO classes (id, name, instructor_id, notes) VALUES (?, ?, ?, ?)",
                            (cls["id"], cls["name"], cls.get("instructor_id"), cls.get("notes", "")),
                        )

                    # Migrate dances
                    for dance in get_items("dances"):
                        self._conn.execute(
                            "INSERT OR REPLACE INTO dances (id, name, song_name, instructor_id, notes) VALUES (?, ?, ?, ?, ?)",
                            (dance["id"], dance["name"], dance["song_name"], dance.get("instructor_id"), dance.get("notes", "")),
                        )

                    # Migrate recitals
                    for recital in get_items("recitals"):
                        self._conn.execute(
                            "INSERT OR REPLACE INTO recitals (id, name, notes) VALUES (?, ?, ?)",
                            (recital["id"], recital["name"], recital.get("notes", "")),
                        )

                    # Migrate dance assignments
                    for dance in get_items("dances"):
                        dance_id = dance["id"]
                        for dancer_id in dance.get("dancer_ids", []):
                            self._conn.execute(
                                "INSERT OR IGNORE INTO dance_assignments (dance_id, dancer_id) VALUES (?, ?)",
                                (dance_id, dancer_id),
                            )

                    # Migrate class-team assignments
                    for cls in get_items("classes"):
                        class_id = cls["id"]
                        for team_id in cls.get("team_ids", []):
                            self._conn.execute(
                                "INSERT OR IGNORE INTO class_team_assignments (class_id, team_id) VALUES (?, ?)",
                                (class_id, team_id),
                            )

                    # Migrate class-dancer assignments
                    for cls in get_items("classes"):
                        class_id = cls["id"]
                        for dancer_id in cls.get("dancer_ids", []):
                            self._conn.execute(
                                "INSERT OR IGNORE INTO class_dancer_assignments (class_id, dancer_id) VALUES (?, ?)",
                                (class_id, dancer_id),
                            )

                    # Set version
                    self._conn.execute(
                        "INSERT OR REPLACE INTO metadata (key, value) VALUES ('version', '\"1.0.0\"')",
                    )
                    self._conn.commit()
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass  # JSON file is corrupted or not valid, skip migration

    def _query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute a query and return results as list of dicts."""
        cursor = self._conn.execute(sql, params)
        if cursor.description is None:
            return []
        rows = []
        for row in cursor.fetchall():
            d = {}
            for i, col in enumerate(cursor.description):
                d[col[0]] = row[i]
            rows.append(d)
        return rows

    def _execute(self, sql: str, params: tuple = ()) -> None:
        """Execute a statement without returning results."""
        self._conn.execute(sql, params)
        self._conn.commit()

    def query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute a raw SQL query and return results as dicts."""
        return self._query(sql, params)

    def execute(self, sql: str, params: tuple = ()):
        """Execute a raw SQL statement. Returns rows if SELECT, else None."""
        cursor = self._conn.execute(sql, params)
        # Check if it's a SELECT by seeing if description exists
        if cursor.description is not None:
            return [tuple(row) for row in cursor.fetchall()]
        self._conn.commit()
        return None

    def execute_many(self, sql: str, params_list: List[tuple]) -> None:
        """Execute a statement with multiple parameter sets."""
        self._conn.executemany(sql, params_list)
        self._conn.commit()


# Cache of store instances by path for singleton behavior
_store_cache: Dict[str, DataStore] = {}


def get_store(path=None):
    """Get or create the store instance (singleton pattern)."""
    global _store_instance
    if path is not None:
        path_key = str(Path(path))
        if path_key in _store_cache:
            return _store_cache[path_key]
        instance = DataStore(path=path)
        _store_cache[path_key] = instance
        return instance
    if _store_instance is None:
        _store_instance = DataStore()
    return _store_instance
