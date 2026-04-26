"""Tests for the DataStore persistence layer.

Tests cover initialization, CRUD operations, backups, migrations,
and edge cases.
"""

import json
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from dancemanager.models import DEFAULT_STORE_SCHEMA
from dancemanager.store import (
    DataStore,
    StoreError,
    StoreVersionError,
    get_store,
)


class TestDataStoreInit:
    """Test store initialization."""

    def test_default_path_created(self, tmp_path):
        store = DataStore(path=tmp_path / "test.json")
        assert store._path.exists()
        assert store._path.name == "test.json"

    def test_custom_path_used(self, tmp_path):
        custom_file = tmp_path / "custom.json"
        store = DataStore(path=custom_file)
        assert store._path == custom_file

    def test_empty_data_on_init(self, tmp_path):
        store = DataStore(tmp_path / "new.json")
        assert store._data == DEFAULT_STORE_SCHEMA

    def test_init_without_path_uses_default(self):
        """Test that DataStore with no path creates default data dir."""
        store = DataStore()
        assert store._path.exists()
        assert "store.db" in str(store._path)

    def test_get_store_without_path(self):
        """Test get_store without path argument returns the same instance."""
        import dancemanager.store

        store1 = dancemanager.store.get_store()
        store2 = dancemanager.store.get_store()
        assert store1 is store2


class TestDataStoreGet:
    """Test get operations."""

    def test_get_existing_item(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        result = store.get("dancers", "d1")
        assert result == {"id": "d1", "name": "Alice"}

    def test_get_missing_item(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        result = store.get("dancers", "d2")
        assert result is None

    def test_get_missing_collection(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        result = store.get("classes", "c1")
        assert result is None

    def test_get_returns_deep_copy(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        result = store.get("dancers", "d1")
        result["name"] = "Modified"
        stored = store.get("dancers", "d1")
        assert stored["name"] == "Alice"

    def test_get_all_existing(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        store.set("dancers", "d2", {"name": "Bob"})
        results = store.get_all("dancers")
        assert len(results) == 2
        assert {"id": "d1", "name": "Alice"} in results
        assert {"id": "d2", "name": "Bob"} in results

    def test_get_all_empty(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        results = store.get_all("dancers")
        assert results == []


class TestDataStoreSet:
    """Test set operations."""

    def test_set_existing_collection(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        store.set("dancers", "d2", {"name": "Bob"})
        assert store.get_collection("dancers") == {
            "d1": {"id": "d1", "name": "Alice"},
            "d2": {"id": "d2", "name": "Bob"},
        }

    def test_set_new_collection(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("classes", "c1", {"name": "Jazz"})
        assert "classes" in store._data

    def test_set_persists(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        store.save()
        assert store._path.exists()

    def test_set_returns_none(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        result = store.set("dancers", "d1", {"name": "Alice"})
        assert result is None


class TestDataStoreDelete:
    """Test delete operations."""

    def test_delete_existing(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        result = store.delete("dancers", "d1")
        assert result is True
        assert store.get("dancers", "d1") is None

    def test_delete_missing(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        result = store.delete("dancers", "d1")
        assert result is False


class TestDataStoreIterate:
    """Test iterate operations."""

    def test_iterate_existing(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        store.set("dancers", "d2", {"name": "Bob"})
        items = list(store.iterate("dancers"))
        assert len(items) == 2

    def test_iterate_empty(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        items = list(store.iterate("dancers"))
        assert items == []


class TestDataStoreVersion:
    """Test version operations."""

    def test_default_version(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        version = store.get_version()
        assert version == "1.0.0"

    def test_version_persisted(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.save()
        assert store.get_version() == "1.0.0"


class TestDataStoreMigration:
    """Test migration handling."""

    def test_migration_updates_version(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.save()
        store._data["version"] = "0.5.0"
        store._save()

        store2 = DataStore(tmp_path / "store.json")
        assert store2.get_version() == "1.0.0"


class TestDataStoreBackup:
    """Test backup creation on save."""

    def test_backup_created(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        backup_path = str(store._path) + ".bak"
        assert os.path.exists(backup_path)

    def test_backup_preserved(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})
        store.set("dancers", "d2", {"name": "Bob"})
        store.save()  # Must save AFTER both sets

        backup_path = str(store._path) + ".bak"
        assert os.path.exists(backup_path)
        # Verify the backup is a valid SQLite file by opening it
        conn = sqlite3.connect(backup_path)
        cursor = conn.execute("SELECT id, name FROM dancers")
        rows = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        assert "d1" in rows
        assert "d2" in rows
        assert rows["d1"] == "Alice"
        assert rows["d2"] == "Bob"


class TestDataStoreComplexTypes:
    """Test handling of complex data structures."""

    def test_nested_dict(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set(
            "dancers",
            "d1",
            {
                "name": "Alice",
                "team": {
                    "name": "Team A",
                    "captain": True,
                },
            },
        )
        result = store.get("dancers", "d1")
        assert result["name"] == "Alice"
        assert result["team"]["name"] == "Team A"
        assert result["team"]["captain"] is True

    def test_list_values(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"skills": ["jazz", "hiphop", "ballroom"]})
        result = store.get("dancers", "d1")
        assert result["skills"] == ["jazz", "hiphop", "ballroom"]


class TestGetStore:
    """Test the get_store singleton pattern."""

    def test_singleton_behavior(self, tmp_path):
        store1 = get_store(tmp_path / "store.json")
        store2 = get_store(tmp_path / "store.json")
        assert store1 is store2

    def test_different_path(self, tmp_path):
        store1 = get_store(tmp_path / "store1.json")
        store2 = get_store(tmp_path / "store2.json")

        assert store1 is not store2


class TestDataStoreEdgeCases:
    """Test edge cases and error conditions."""

    def test_special_characters_in_data(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": 'Alice "The Great" Johnson'})
        store.set("dancers", "d2", {"song": "Rock 'n' Roll"})
        result = store.get("dancers", "d1")
        assert result["name"] == 'Alice "The Great" Johnson'

    def test_unicode_characters(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set(
            "dances", "dance1", {"name": "Ballet", "description": "Beautiful dance! 🎭"}
        )
        result = store.get("dances", "dance1")
        assert result["name"] == "Ballet"

    def test_empty_dict_value(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"notes": {}})
        result = store.get("dancers", "d1")
        assert result["notes"] == {}

    def test_empty_list_value(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dances", "d1", {"dancer_ids": []})
        result = store.get("dances", "d1")
        assert result["dancer_ids"] == []

    def test_nested_empty_structures(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set(
            "classes",
            "c1",
            {
                "dancers": {},
                "songs": [],
                "schedule": {},
            },
        )
        result = store.get("classes", "c1")
        assert result["dancers"] == {}
        assert result["songs"] == []
        assert result["schedule"] == {}


class TestDataStoreIntegrity:
    """Test data integrity and consistency."""

    def test_multiple_gets_consistent(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})

        for _ in range(10):
            result = store.get("dancers", "d1")
            assert result == {"id": "d1", "name": "Alice"}

    def test_multiple_saves_preserve_data(self, tmp_path):
        store = DataStore(tmp_path / "store.json")
        store.set("dancers", "d1", {"name": "Alice"})

        store.save()
        store.save()
        store.save()

        assert store.get("dancers", "d1") == {"id": "d1", "name": "Alice"}


class TestDataStorePathHandling:
    """Test file path handling."""

    def test_path_with_spaces(self, tmp_path):
        custom_path = tmp_path / "my data" / "store.json"
        custom_path.parent.mkdir(parents=True, exist_ok=True)
        store = DataStore(path=str(custom_path))
        store.set("dancers", "d1", {"name": "Alice"})
        assert store.get("dancers", "d1") == {"id": "d1", "name": "Alice"}

    def test_nested_directories_created(self, tmp_path):
        nested_path = tmp_path / "a" / "b" / "c" / "store.json"
        store = DataStore(path=str(nested_path))
        assert store._path.exists()
        store.set("dancers", "d1", {"name": "Alice"})
        assert store.get("dancers", "d1") == {"id": "d1", "name": "Alice"}
