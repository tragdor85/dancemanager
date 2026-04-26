"""Shared helper functions for web interface tests.

Provides make_app, make_test_client, seed_data, and setup_recital_with_dances
utilities used across all web interface test modules.
"""

import tempfile
import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

from dancemanager.store import DataStore
import dancemanager.web.main as main


def make_app(store):
    """Create a FastAPI app with the given store for testing."""
    app = FastAPI()
    app.dependency_overrides[main.store_dependency] = lambda: store
    app.include_router(main.router)
    return app


def make_test_client(store=None):
    """Create a TestClient that does not follow redirects by default.

    If no store is provided, creates a fresh one with a unique temp path.
    Returns (client, store) tuple.
    """
    if store is None:
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
    app = make_app(store)
    return TestClient(app, follow_redirects=False), store


def seed_data(store):
    """Populate the store with standard test data.

    Order matters: create referenced entities (teams, classes, instructors)
    before records that reference them via foreign keys.
    """
    # Create referenced entities first
    store.set("teams", "red", {"id": "red", "name": "Red Team", "dancer_ids": []})
    store.set(
        "classes",
        "ballet",
        {
            "id": "ballet",
            "name": "Ballet Basics",
            "instructor_id": None,
            "team_ids": [],
            "dancer_ids": [],
        },
    )
    store.set(
        "instructors",
        "jane",
        {"id": "jane", "name": "Jane Doe", "class_ids": [], "dance_ids": []},
    )

    # Now create records that reference them
    store.set(
        "dancers",
        "alice",
        {
            "id": "alice",
            "name": "Alice Smith",
            "class_ids": ["ballet"],
            "team_id": "red",
        },
    )
    store.set(
        "dancers",
        "bob",
        {"id": "bob", "name": "Bob Jones", "class_ids": [], "team_id": None},
    )

    # Update class to reference instructor after it exists
    cls = store.get("classes", "ballet")
    cls["instructor_id"] = "jane"
    store.set("classes", "ballet", cls)

    store.set(
        "dances",
        "waltz",
        {
            "id": "waltz",
            "name": "Waltz",
            "song_name": "Blue Danube",
            "instructor_id": "jane",
            "dancer_ids": ["alice"],
            "notes": "",
        },
    )
    store.set(
        "dances",
        "hiphop",
        {
            "id": "hiphop",
            "name": "Hip Hop",
            "song_name": "Beat Drop",
            "instructor_id": None,
            "dancer_ids": ["bob"],
            "notes": "",
        },
    )
    store.set(
        "recitals",
        "spring",
        {
            "id": "spring",
            "name": "Spring Showcase",
            "performance_order": [],
            "notes": "",
        },
    )


def setup_recital_with_dances(store):
    """Create a recital with two dances sharing a dancer (conflict)."""
    # Two dancers, each in both dances -> scheduling conflict
    store.set(
        "dancers",
        "alice",
        {"id": "alice", "name": "Alice Smith", "class_ids": [], "team_id": None},
    )
    store.set(
        "dancers",
        "bob",
        {"id": "bob", "name": "Bob Jones", "class_ids": [], "team_id": None},
    )
    # Dance 1: both alice and bob
    store.set(
        "dances",
        "waltz",
        {
            "id": "waltz",
            "name": "Waltz",
            "song_name": "Blue Danube",
            "instructor_id": None,
            "dancer_ids": ["alice", "bob"],
            "notes": "",
        },
    )
    # Dance 2: both alice and bob (conflict)
    store.set(
        "dances",
        "hiphop",
        {
            "id": "hiphop",
            "name": "Hip Hop",
            "song_name": "Beat Drop",
            "instructor_id": None,
            "dancer_ids": ["alice", "bob"],
            "notes": "",
        },
    )
    # Dance 3: only alice (buffer)
    store.set(
        "dances",
        "jazz",
        {
            "id": "jazz",
            "name": "Jazz",
            "song_name": "Swing Time",
            "instructor_id": None,
            "dancer_ids": ["alice"],
            "notes": "",
        },
    )
    # Dance 4: only bob (buffer)
    store.set(
        "dances",
        "tap",
        {
            "id": "tap",
            "name": "Tap",
            "song_name": "Rhythm",
            "instructor_id": None,
            "dancer_ids": ["bob"],
            "notes": "",
        },
    )
    # Recital with all 4 dances in performance_order as dance IDs (legacy format)
    store.set(
        "recitals",
        "spring",
        {
            "id": "spring",
            "name": "Spring Showcase",
            "performance_order": ["waltz", "hiphop", "jazz", "tap"],
            "notes": "",
        },
    )
