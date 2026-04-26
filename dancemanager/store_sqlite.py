"""SQLite persistence layer for Dance Manager.

Provides load/save, typed getters/setters, and migration support for all
data collections using SQLite with foreign key support.
"""

import copy
import json
import os
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


class DataStore:
    """SQLite store for Dance Manager.

    All reads return deep copies to prevent in-memory mutation leaking
    into the database. Every save creates a .bak backup first.
    """

    def __init__(self, path: StorePath = None):
        if path is None:
            self._path = Path(__file__).parent.parent / "data" / "store.db"
        else:
            self._path = Path(path)

        self._db_path = self._path
        self._backup_path = str(self._path) + ".bak"

        self._data: Dict[str, Any] = {}
        self._load()

    def get(self, collection: str, key: str) -> Optional[Any]:
        """Return a deep copy of the item at *collection*[*key*]."""
        collection_data = self._data.get(collection)
        if collection_data is None:
            return None
        item = collection_data.get(key)
        if item is None:
            return None
        return copy.deepcopy(item)

    def set(self, collection: str, key: str, value: Any) -> None:
        """Save *value* into *collection* under *key*, then persist."""
        if collection not in self._data:
            self._data[collection] = {}
        self._data[collection][key] = copy.deepcopy(value)
        self._save()

    def get_collection(self, collection: str) -> Dict[str, Any]:
        """Return a deep copy of the entire collection dict."""
        collection_data = self._data.get(collection)
        if collection_data is None:
            return {}
        return copy.deepcopy(collection_data)

    def set_collection(self, collection: str, data: Dict[str, Any]) -> None:
        """Replace an entire collection and persist."""
        self._data[collection] = copy.deepcopy(data)
        self._save()

    def get_all(self, collection: str) -> List[Any]:
        """Return every item in *collection* as a list of deep copies."""
        items = self.get_collection(collection)
        return [copy.deepcopy(v) for v in items.values()]

    def iterate(self, collection: str):
        """Yield (key, value) pairs for *collection* (deep-copied values)."""
        for key, value in self.get_collection(collection).items():
            yield key, copy.deepcopy(value)

    def delete(self, collection: str, key: str) -> bool:
        """Remove an item.  Returns ``True`` if it existed."""
        collection_data = self._data.get(collection)
        if collection_data is None:
            return False
        if key not in collection_data:
            return False
        del collection_data[key]
        self._save()
        return True

    def save(self) -> None:
        """Persist current in-memory state to disk."""
        self._save()

    def get_version(self) -> str:
        """Return the current schema version string."""
        return self._data.get("version", "0.0.0")

    def execute(self, sql: str, params: tuple = ()) -> List[tuple]:
        """Execute a SQL query and return all rows."""
        with self._connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchall()

    def execute_one(self, sql: str, params: tuple = ()) -> tuple:
        """Execute a SQL query and return a single row."""
        with self._connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()

    def execute_many(self, sql: str, params_list: List[tuple]) -> None:
        """Execute a SQL query with multiple parameter sets."""
        with self._connection() as conn:
            conn.executemany(sql, params_list)
            conn.commit()

    def _connection(self):
        """Return a connection to the database with foreign keys enabled."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _load(self) -> None:
        """Read store.db (or initialise an empty store) into memory."""
        if self._db_path.exists():
            try:
                import sqlite3

                conn = sqlite3.connect(str(self._db_path))
                conn.execute("PRAGMA foreign_keys = ON")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                for collection in DEFAULT_STORE_SCHEMA.keys():
                    if collection not in tables:
                        self._create_table(collection)

                for collection in DEFAULT_STORE_SCHEMA.keys():
                    if collection in tables:
                        cursor.execute(f"SELECT * FROM {collection}")
                        rows = cursor.fetchall()
                        self._data[collection] = {
                            row[0]: dict(row._asdict()) for row in rows
                        }

                cursor.execute("SELECT version FROM metadata")
                row = cursor.fetchone()
                if row:
                    stored_version = row[0]
                else:
                    stored_version = "0.0.0"

                conn.close()
            except sqlite3.Error as exc:
                raise StoreVersionError(
                    f"Invalid database at {self._db_path}: {exc}"
                ) from exc

            if stored_version != CURRENT_VERSION:
                self._migrate(stored_version)
        else:
            self._data = copy.deepcopy(DEFAULT_STORE_SCHEMA)
            self._save()

    def _save(self) -> None:
        """Write self._data to SQLite, creating a .bak backup first."""
        import sqlite3

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        if self._db_path.exists():
            with open(self._db_path, "rb") as src:
                backup_content = src.read()
            with open(self._backup_path, "wb") as dst:
                dst.write(backup_content)

        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        for collection, data in self._data.items():
            if collection == "version":
                continue
            if not data:
                continue

            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {collection} (id TEXT PRIMARY KEY, data TEXT)"
            )

            for key, value in data.items():
                json_str = json.dumps(value)
                cursor.execute(
                    f"INSERT OR REPLACE INTO {collection} (id, data) VALUES (?, ?)",
                    (key, json_str),
                )

        conn.commit()
        conn.close()

    def _migrate(self, from_version: str) -> None:
        """Apply migrations until data version matches CURRENT_VERSION."""
        import sqlite3

        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("SELECT version FROM metadata")
        row = cursor.fetchone()
        if row:
            stored_version = row[0]
        else:
            stored_version = from_version

        if stored_version != CURRENT_VERSION:
            cursor.execute("DELETE FROM metadata")
            cursor.execute(
                "INSERT INTO metadata (version) VALUES (?)", (CURRENT_VERSION,)
            )
            conn.commit()

        conn.close()

    def _create_table(self, collection: str) -> None:
        """Create a table for a collection if it doesn't exist."""
        import sqlite3

        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {collection} (id TEXT PRIMARY KEY, data TEXT)"
        )

        conn.commit()
        conn.close()


_store_cache: dict = {}


def get_store(path=None):
    """Get or create the store instance."""
    if path is None:
        path = str(Path(__file__).parent.parent / "data" / "store.db")
    if path not in _store_cache:
        _store_cache[path] = DataStore(path=path)
    return _store_cache[path]
