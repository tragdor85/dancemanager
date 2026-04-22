"""JSON persistence layer for Dance Manager.

Provides load/save with backup, typed getters/setters, and migration
support for all data collections.
"""

import copy
import json
import os
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
    """Single-file JSON store for Dance Manager.

    All reads return deep copies to prevent in-memory mutation leaking
    into the file on disk.  Every save creates a .bak backup first.
    """

    def __init__(self, path: StorePath = None):
        if path is None:
            self._path = Path(__file__).parent.parent / "data" / "store.json"
        else:
            self._path = Path(path)

        self._data: Dict[str, Any] = {}
        self._load()

    # -- public helpers --------------------------------------------------

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

    # -- internal --------------------------------------------------------

    def _load(self) -> None:
        """Read store.json (or initialise an empty store) into memory."""
        if self._path.exists():
            try:
                with open(self._path, "r") as fh:
                    data = json.load(fh)
            except json.JSONDecodeError as exc:
                raise StoreVersionError(f"Invalid JSON in {self._path}: {exc}") from exc

            stored_version = data.get("version", "0.0.0")
            if stored_version != CURRENT_VERSION:
                data = self._migrate(data, stored_version)

            self._data = data
        else:
            self._data = copy.deepcopy(DEFAULT_STORE_SCHEMA)
            self._save()

    def _save(self) -> None:
        """Write self._data to JSON, creating a .bak backup first."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            bak_path = str(self._path) + ".bak"
            with open(self._path, "r") as src:
                backup_content = src.read()
            with open(bak_path, "w") as dst:
                dst.write(backup_content)

        with open(self._path, "w") as fh:
            json.dump(self._data, fh, indent=2, sort_keys=True)

    def _migrate(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """Apply migrations until data version matches CURRENT_VERSION."""
        if from_version == CURRENT_VERSION:
            return data

        # Version 1.0.0 — default schema already in DEFAULT_STORE_SCHEMA
        # Future migrations can be added here as needed.
        data["version"] = CURRENT_VERSION
        return data
