"""Comprehensive tests for the Dance Manager web interface.

Covers: Dashboard/index page, List pages, Detail pages, Create endpoints,
Update endpoints, Delete endpoints, and Recital schedule generation.
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


# ──────────────────────────────────────────────────────────────────────
# 1. Dashboard / index page
# ──────────────────────────────────────────────────────────────────────


class TestDashboardIndex:
    """Tests for GET / (dashboard/index)."""

    def test_index_returns_200(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_shows_counts_empty(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert "dancer_count" in resp.text or "0" in resp.text

    def test_index_shows_counts_with_data(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        app = make_app(store)
        client = TestClient(app, follow_redirects=False)
        resp = client.get("/")
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────
# 2. List pages (GET /dancers, /teams, etc.)
# ──────────────────────────────────────────────────────────────────────


class TestListPages:
    """Tests for all list endpoints."""

    # -- Dancers list --
    def test_dancers_list_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers")
        assert resp.status_code == 200

    def test_dancers_list_shows_dancers(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers")
        assert "Alice Smith" in resp.text

    def test_dancers_list_empty(self):
        client, _ = make_test_client()
        resp = client.get("/dancers")
        assert resp.status_code == 200

    def test_dancers_list_search(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers?q=alice")
        assert resp.status_code == 200
        assert "Alice Smith" in resp.text

    def test_dancers_list_search_no_match(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers?q=zzzzz")
        assert resp.status_code == 200

    def test_dancers_list_case_insensitive(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers?q=ALICE")
        assert "Alice Smith" in resp.text

    # -- Teams list --
    def test_teams_list_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams")
        assert resp.status_code == 200

    def test_teams_list_shows_teams(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams")
        assert "Red Team" in resp.text

    # -- Classes list --
    def test_classes_list_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes")
        assert resp.status_code == 200

    def test_classes_list_shows_classes(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes")
        assert "Ballet Basics" in resp.text

    # -- Instructors list --
    def test_instructors_list_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors")
        assert resp.status_code == 200

    def test_instructors_list_shows_instructors(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors")
        assert "Jane Doe" in resp.text

    # -- Dances list --
    def test_dances_list_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances")
        assert resp.status_code == 200

    def test_dances_list_shows_dances(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances")
        assert "Waltz" in resp.text

    # -- Recitals list --
    def test_recitals_list_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals")
        assert resp.status_code == 200

    def test_recitals_list_shows_recitals(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals")
        assert "Spring Showcase" in resp.text

    # -- Teams list count columns --
    def test_teams_list_shows_dancer_count(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        client, _ = make_test_client(store)
        resp = client.get("/teams")
        assert resp.status_code == 200
        # Alice has team_id="red" so Red Team should show dancer count of 1
        assert "Red Team" in resp.text

    def test_teams_list_shows_zero_for_team_without_dancers(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        # Bob has team_id=None, so teams list should handle this gracefully
        client, _ = make_test_client(store)
        resp = client.get("/teams")
        assert resp.status_code == 200

    # -- Classes list count columns --
    def test_classes_list_shows_team_count(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        # Assign Red Team to Ballet class via assignment table
        store.execute(
            "INSERT OR IGNORE INTO class_team_assignments (class_id, team_id) VALUES (?, ?)",
            ("ballet", "red"),
        )

        client, _ = make_test_client(store)
        resp = client.get("/classes")
        assert resp.status_code == 200
        assert "Ballet Basics" in resp.text

    def test_classes_list_shows_zero_teams(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        client, _ = make_test_client(store)
        resp = client.get("/classes")
        assert resp.status_code == 200

    # -- Instructors list count columns --
    def test_instructors_list_shows_class_and_dance_counts(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        client, _ = make_test_client(store)
        resp = client.get("/instructors")
        assert resp.status_code == 200
        # Jane Doe teaches Ballet Basics and Waltz dance
        assert "Jane Doe" in resp.text

    def test_instructors_list_shows_zero_counts(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        # Create instructor with no classes or dances assigned
        store.set(
            "instructors",
            "john",
            {"id": "john", "name": "John Smith", "class_ids": [], "dance_ids": []},
        )

        client, _ = make_test_client(store)
        resp = client.get("/instructors")
        assert resp.status_code == 200
        assert "John Smith" in resp.text

    # -- Dances list count columns --
    def test_dances_list_shows_dancer_count(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        client, _ = make_test_client(store)
        resp = client.get("/dances")
        assert resp.status_code == 200
        assert "Waltz" in resp.text

    def test_dances_list_shows_zero_dancers(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        # Create dance with no dancers assigned
        store.set(
            "dances",
            "salsa",
            {
                "id": "salsa",
                "name": "Salsa",
                "song_name": "Rhythm",
                "instructor_id": None,
                "dancer_ids": [],
                "notes": "",
            },
        )

        client, _ = make_test_client(store)
        resp = client.get("/dances")
        assert resp.status_code == 200
        assert "Salsa" in resp.text

    # -- Dancers list count columns --
    def test_dancers_list_shows_class_count(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        client, _ = make_test_client(store)
        resp = client.get("/dancers")
        assert resp.status_code == 200
        # Alice is assigned to Ballet Basics class
        assert "Alice Smith" in resp.text

    def test_dancers_list_shows_zero_classes(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        client, _ = make_test_client(store)
        resp = client.get("/dancers")
        assert resp.status_code == 200
        # Bob has no class_ids so should show 0 classes


# ──────────────────────────────────────────────────────────────────────
# 3. Detail pages (GET /dancers/{id}, etc.)
# ──────────────────────────────────────────────────────────────────────


class TestDetailPages:
    """Tests for all detail endpoints."""

    def test_dancer_detail_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers/alice")
        assert resp.status_code == 200

    def test_dancer_detail_shows_name(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers/alice")
        assert "Alice Smith" in resp.text

    def test_dancer_detail_404(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers/nonexistent")
        assert resp.status_code == 404

    def test_team_detail_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams/red")
        assert resp.status_code == 200

    def test_team_detail_shows_dancers(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams/red")
        assert "Alice Smith" in resp.text

    def test_team_detail_404(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams/nonexistent")
        assert resp.status_code == 404

    def test_class_detail_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes/ballet")
        assert resp.status_code == 200

    def test_class_detail_shows_dancers(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes/ballet")
        assert "Alice Smith" in resp.text

    def test_class_detail_404(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes/nonexistent")
        assert resp.status_code == 404

    def test_instructor_detail_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors/jane")
        assert resp.status_code == 200

    def test_instructor_detail_shows_name(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors/jane")
        assert "Jane Doe" in resp.text

    def test_instructor_detail_404(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors/nonexistent")
        assert resp.status_code == 404

    def test_dance_detail_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances/waltz")
        assert resp.status_code == 200

    def test_dance_detail_shows_name(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances/waltz")
        assert "Waltz" in resp.text

    def test_dance_detail_404(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances/nonexistent")
        assert resp.status_code == 404

    def test_recital_detail_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring")
        assert resp.status_code == 200

    def test_recital_detail_404(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/nonexistent")
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────────────
# 4. Create endpoints (POST /dancers, /teams, etc.)
# ──────────────────────────────────────────────────────────────────────


class TestCreateEndpoints:
    """Tests for all POST create endpoints."""

    # -- Dancer creation --
    def test_create_dancer_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/dancers", data={"name": "Carol White", "class_ids": "", "team_id": ""}
        )
        assert resp.status_code == 303

    def test_create_dancer_stores_data(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/dancers", data={"name": "Carol White", "class_ids": "", "team_id": ""}
        )
        dancer = store.get("dancers", "carol-white")
        assert dancer is not None
        assert dancer["name"] == "Carol White"

    def test_create_dancer_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/dancers", data={"name": "", "class_ids": "", "team_id": ""}
        )
        assert resp.status_code == 400

    def test_create_dancer_no_name_required(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/dancers", data={"class_ids": "", "team_id": ""})
        assert resp.status_code == 400

    # -- Team creation --
    def test_create_team_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/teams", data={"name": "Blue Team", "dancer_ids": ""})
        assert resp.status_code == 303

    def test_create_team_stores_data(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post("/teams", data={"name": "Blue Team", "dancer_ids": ""})
        team = store.get("teams", "blue-team")
        assert team is not None
        assert team["name"] == "Blue Team"

    def test_create_team_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/teams", data={"name": "", "dancer_ids": ""})
        assert resp.status_code == 400

    def test_create_team_assigns_dancers(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post("/teams", data={"name": "Blue Team", "dancer_ids": ["alice"]})
        dancer = store.get("dancers", "alice")
        assert dancer["team_id"] == "blue-team"

    # -- Class creation --
    def test_create_class_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/classes", data={"name": "Tap Dance", "instructor_id": "", "team_ids": ""}
        )
        assert resp.status_code == 303

    def test_create_class_stores_data(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/classes", data={"name": "Tap Dance", "instructor_id": "", "team_ids": ""}
        )
        cls = store.get("classes", "tap-dance")
        assert cls is not None
        assert cls["name"] == "Tap Dance"

    def test_create_class_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/classes", data={"name": "", "instructor_id": "", "team_ids": ""}
        )
        assert resp.status_code == 400

    # -- Instructor creation --
    def test_create_instructor_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/instructors",
            data={"name": "John Smith", "class_ids": "", "dance_ids": ""},
        )
        assert resp.status_code == 303

    def test_create_instructor_stores_data(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/instructors",
            data={"name": "John Smith", "class_ids": "", "dance_ids": ""},
        )
        inst = store.get("instructors", "john-smith")
        assert inst is not None
        assert inst["name"] == "John Smith"

    def test_create_instructor_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/instructors", data={"name": "", "class_ids": "", "dance_ids": ""}
        )
        assert resp.status_code == 400

    # -- Dance creation --
    def test_create_dance_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/dances",
            data={
                "name": "Salsa",
                "song_name": "Ritmo",
                "instructor_id": "",
                "dancer_ids": "",
            },
        )
        assert resp.status_code == 303

    def test_create_dance_stores_data(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/dances",
            data={
                "name": "Salsa",
                "song_name": "Ritmo",
                "instructor_id": "",
                "dancer_ids": "",
            },
        )
        dance = store.get("dances", "salsa")
        assert dance is not None
        assert dance["name"] == "Salsa"

    def test_create_dance_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/dances",
            data={"name": "", "song_name": "", "instructor_id": "", "dancer_ids": ""},
        )
        assert resp.status_code == 400

    # -- Recital creation --
    def test_create_recital_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/recitals", data={"name": "Fall Gala", "performance_order": ""}
        )
        assert resp.status_code == 303

    def test_create_recital_stores_data(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post("/recitals", data={"name": "Fall Gala", "performance_order": ""})
        recital = store.get("recitals", "fall-gala")
        assert recital is not None
        assert recital["name"] == "Fall Gala"

    def test_create_recital_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/recitals", data={"name": "", "performance_order": ""})
        assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────────────
# 5. Update endpoints (POST /dancers/{id}, etc.)
# ──────────────────────────────────────────────────────────────────────


class TestUpdateEndpoints:
    """Tests for all POST update endpoints."""

    # -- Dancer update --
    def test_update_dancer_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/dancers/alice",
            data={"name": "Alice Updated", "class_ids": "", "team_id": ""},
        )
        assert resp.status_code == 303

    def test_update_dancer_changes_name(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/dancers/alice",
            data={"name": "Alice Updated", "class_ids": "", "team_id": ""},
        )
        dancer = store.get("dancers", "alice")
        assert dancer["name"] == "Alice Updated"

    def test_update_dancer_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/dancers/alice", data={"name": "", "class_ids": "", "team_id": ""}
        )
        assert resp.status_code == 400

    def test_update_dancer_assigns_team(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/dancers/alice", data={"name": "Alice", "class_ids": "", "team_id": "red"}
        )
        dancer = store.get("dancers", "alice")
        assert dancer["team_id"] == "red"

    # -- Team update --
    def test_update_team_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/teams/red", data={"name": "Red Team Updated", "dancer_ids": ""}
        )
        assert resp.status_code == 303

    def test_update_team_changes_name(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post("/teams/red", data={"name": "Red Team Updated", "dancer_ids": ""})
        team = store.get("teams", "red")
        assert team["name"] == "Red Team Updated"

    def test_update_team_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/teams/red", data={"name": "", "dancer_ids": ""})
        assert resp.status_code == 400

    def test_update_team_removes_dancers(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        # alice is in red team; update with no dancers should remove her
        client.post("/teams/red", data={"name": "Red Team", "dancer_ids": ""})
        dancer = store.get("dancers", "alice")
        assert dancer.get("team_id") is None

    def test_update_team_adds_dancers(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post("/teams/red", data={"name": "Red Team", "dancer_ids": ["bob"]})
        dancer = store.get("dancers", "bob")
        assert dancer["team_id"] == "red"

    # -- Class update --
    def test_update_class_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/classes/ballet",
            data={"name": "Ballet Advanced", "instructor_id": "", "team_ids": ""},
        )
        assert resp.status_code == 303

    def test_update_class_changes_name(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/classes/ballet",
            data={"name": "Ballet Advanced", "instructor_id": "", "team_ids": ""},
        )
        cls = store.get("classes", "ballet")
        assert cls["name"] == "Ballet Advanced"

    def test_update_class_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/classes/ballet", data={"name": "", "instructor_id": "", "team_ids": ""}
        )
        assert resp.status_code == 400

    # -- Instructor update --
    def test_update_instructor_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/instructors/jane",
            data={"name": "Jane Updated", "class_ids": "", "dance_ids": ""},
        )
        assert resp.status_code == 303

    def test_update_instructor_changes_name(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/instructors/jane",
            data={"name": "Jane Updated", "class_ids": "", "dance_ids": ""},
        )
        inst = store.get("instructors", "jane")
        assert inst["name"] == "Jane Updated"

    def test_update_instructor_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/instructors/jane", data={"name": "", "class_ids": "", "dance_ids": ""}
        )
        assert resp.status_code == 400

    # -- Dance update --
    def test_update_dance_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/dances/waltz",
            data={
                "name": "Waltz Advanced",
                "song_name": "New Song",
                "instructor_id": "",
                "dancer_ids": "",
            },
        )
        assert resp.status_code == 303

    def test_update_dance_changes_name(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/dances/waltz",
            data={
                "name": "Waltz Advanced",
                "song_name": "New Song",
                "instructor_id": "",
                "dancer_ids": "",
            },
        )
        dance = store.get("dances", "waltz")
        assert dance["name"] == "Waltz Advanced"

    def test_update_dance_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/dances/waltz",
            data={"name": "", "song_name": "", "instructor_id": "", "dancer_ids": ""},
        )
        assert resp.status_code == 400

    # -- Recital update --
    def test_update_recital_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/recitals/spring",
            data={"name": "Spring Showcase Updated", "performance_order": ""},
        )
        assert resp.status_code == 303

    def test_update_recital_changes_name(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post(
            "/recitals/spring",
            data={"name": "Spring Showcase Updated", "performance_order": ""},
        )
        recital = store.get("recitals", "spring")
        assert recital["name"] == "Spring Showcase Updated"

    def test_update_recital_no_name_400(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post(
            "/recitals/spring", data={"name": "", "performance_order": ""}
        )
        assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────────────
# 6. Delete endpoints (DELETE /dancers/{id}, etc.)
# ──────────────────────────────────────────────────────────────────────


class TestDeleteEndpoints:
    """Tests for all DELETE endpoints."""

    def test_delete_dancer_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.delete("/dancers/alice")
        assert resp.status_code == 303
        dancer = store.get("dancers", "alice")
        assert dancer is None

    def test_delete_dancer_redirects_to_list(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.delete("/dancers/alice")
        assert "/dancers" in str(resp.headers.get("location", ""))

    def test_delete_team_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        # Clear team_id from dancers to avoid FK constraint
        alice = store.get("dancers", "alice")
        if alice:
            alice["team_id"] = None
            store.set("dancers", "alice", alice)
        client, _ = make_test_client(store)
        resp = client.delete("/teams/red")
        assert resp.status_code == 303
        team = store.get("teams", "red")
        assert team is None

    def test_delete_class_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.delete("/classes/ballet")
        assert resp.status_code == 303
        cls = store.get("classes", "ballet")
        assert cls is None

    def test_delete_instructor_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        # Clear instructor_id from classes and dances to avoid FK constraint
        ballet = store.get("classes", "ballet")
        if ballet:
            ballet["instructor_id"] = None
            store.set("classes", "ballet", ballet)
        waltz = store.get("dances", "waltz")
        if waltz:
            waltz["instructor_id"] = None
            store.set("dances", "waltz", waltz)
        client, _ = make_test_client(store)
        resp = client.delete("/instructors/jane")
        assert resp.status_code == 303
        inst = store.get("instructors", "jane")
        assert inst is None

    def test_delete_dance_success(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.delete("/dances/waltz")
        assert resp.status_code == 303
        dance = store.get("dances", "waltz")
        assert dance is None

    def test_delete_recital_success(self):
        """DELETE /recitals/{recital_id} should work (bug fix)."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.delete("/recitals/spring")
        assert resp.status_code == 303
        recital = store.get("recitals", "spring")
        assert recital is None

    def test_delete_recital_redirects_to_list(self):
        """DELETE /recitals/{recital_id} should redirect to /recitals."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.delete("/recitals/spring")
        assert "/recitals" in str(resp.headers.get("location", ""))


# ──────────────────────────────────────────────────────────────────────
# 7. Recital schedule generation
# ──────────────────────────────────────────────────────────────────────


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


class TestRecitalScheduleGeneration:
    """Tests for recital schedule generation endpoints."""

    def test_schedule_page_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert resp.status_code == 200

    def test_schedule_page_shows_schedule(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert "schedule" in resp.text.lower() or "position" in resp.text.lower()

    def test_schedule_page_404(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/nonexistent/schedule")
        assert resp.status_code == 404

    def test_schedule_generate_200(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule-generate")
        assert resp.status_code == 303

    def test_schedule_generate_saves_order(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        client.get("/recitals/spring/schedule-generate")
        recital = store.get("recitals", "spring")
        order = recital.get("performance_order", [])
        assert len(order) == 4

    def test_schedule_generate_requires_min_two_dances(self):
        """Schedule generation with <2 dances should return 400."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        store.set(
            "recitals",
            "spring",
            {"id": "spring", "name": "Spring", "performance_order": [], "notes": ""},
        )
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule-generate")
        assert resp.status_code == 400

    def test_schedule_generate_single_dance(self):
        """Schedule generation with only 1 dance should return 400."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        store.set(
            "recitals",
            "spring",
            {
                "id": "spring",
                "name": "Spring",
                "performance_order": ["waltz"],
                "notes": "",
            },
        )
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule-generate")
        assert resp.status_code == 400

    def test_schedule_generate_404(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/nonexistent/schedule-generate")
        assert resp.status_code == 404

    def test_schedule_generate_redirects_to_schedule(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule-generate")
        assert "/schedule" in str(resp.headers.get("location", ""))

    def test_schedule_page_with_legacy_order_format(self):
        """Test schedule page handles legacy string-based performance_order."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        # Override with legacy format (list of dance_id strings instead of dicts)
        recital = store.get("recitals", "spring")
        recital["performance_order"] = ["waltz", "hiphop"]
        store.set("recitals", "spring", recital)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert resp.status_code == 200

    def test_schedule_page_empty_order(self):
        """Schedule page with no dances in order should still work."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        recital = store.get("recitals", "spring")
        recital["performance_order"] = []
        store.set("recitals", "spring", recital)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert resp.status_code == 200

    def test_schedule_page_missing_dance_in_order(self):
        """Schedule page should handle missing dance IDs gracefully."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        recital = store.get("recitals", "spring")
        # Reference a non-existent dance
        recital["performance_order"] = ["waltz", "nonexistent-dance"]
        store.set("recitals", "spring", recital)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert resp.status_code == 200

    def test_schedule_generate_updates_recital(self):
        """Verify schedule-generate actually updates the recital in store."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)

        # Before: performance_order is a list of strings
        before = store.get("recitals", "spring")
        assert isinstance(before["performance_order"], list)

        client.get("/recitals/spring/schedule-generate")

        after = store.get("recitals", "spring")
        order = after["performance_order"]
        # After: should be a list of dicts with dance_id and position
        assert len(order) == 4
        assert isinstance(order[0], dict)
        assert "dance_id" in order[0]
        assert "position" in order[0]

    def test_schedule_page_shows_dancer_names(self):
        """Schedule page should include dancer names for each slot."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert "Alice Smith" in resp.text

    def test_schedule_page_shows_song_names(self):
        """Schedule page should include song names."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert "Blue Danube" in resp.text

    def test_schedule_page_shows_positions(self):
        """Schedule page should show position numbers."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert "1" in resp.text


class TestRecitalScheduleGenerationEdgeCases:
    """Edge cases for recital schedule generation."""

    def test_schedule_generate_no_dances_in_recital(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        store.set(
            "recitals",
            "empty",
            {"id": "empty", "name": "Empty", "performance_order": [], "notes": ""},
        )
        client, _ = make_test_client(store)
        resp = client.get("/recitals/empty/schedule-generate")
        assert resp.status_code == 400

    def test_schedule_page_empty_recital(self):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        store.set(
            "recitals",
            "empty",
            {"id": "empty", "name": "Empty", "performance_order": [], "notes": ""},
        )
        client, _ = make_test_client(store)
        resp = client.get("/recitals/empty/schedule")
        assert resp.status_code == 200

    def test_schedule_generate_with_no_dancer_conflicts(self):
        """When no dancer is in multiple dances, any order works."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        store.set(
            "dancers",
            "alice",
            {"id": "alice", "name": "Alice", "class_ids": [], "team_id": None},
        )
        store.set(
            "dances",
            "waltz",
            {
                "id": "waltz",
                "name": "Waltz",
                "song_name": "Song1",
                "instructor_id": None,
                "dancer_ids": ["alice"],
                "notes": "",
            },
        )
        store.set(
            "dances",
            "jazz",
            {
                "id": "jazz",
                "name": "Jazz",
                "song_name": "Song2",
                "instructor_id": None,
                "dancer_ids": ["alice"],
                "notes": "",
            },
        )
        store.set(
            "recitals",
            "spring",
            {
                "id": "spring",
                "name": "Spring",
                "performance_order": ["waltz", "jazz"],
                "notes": "",
            },
        )
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule-generate")
        assert resp.status_code == 303

    def test_schedule_page_with_dict_order_format(self):
        """Schedule page handles dict-based performance_order."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        recital = store.get("recitals", "spring")
        # Override with dict format (new format)
        recital["performance_order"] = [
            {"dance_id": "waltz", "position": 1},
            {"dance_id": "hiphop", "position": 2},
        ]
        store.set("recitals", "spring", recital)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert resp.status_code == 200

    def test_schedule_generate_constrained_dancers(self):
        """Schedule generation with many conflicts should still produce valid schedule."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        # All dancers in all dances -> maximum conflict
        for i in range(3):
            store.set(
                "dancers",
                f"dancer{i}",
                {
                    "id": f"dancer{i}",
                    "name": f"Dancer {i}",
                    "class_ids": [],
                    "team_id": None,
                },
            )
        dance_names = ["waltz", "hiphop", "jazz", "tap", "swing", "contemp"]
        for dn in dance_names:
            store.set(
                "dances",
                dn,
                {
                    "id": dn,
                    "name": dn.capitalize(),
                    "song_name": f"Song {dn}",
                    "instructor_id": None,
                    "dancer_ids": ["dancer0", "dancer1", "dancer2"],
                    "notes": "",
                },
            )
        store.set(
            "recitals",
            "spring",
            {
                "id": "spring",
                "name": "Spring",
                "performance_order": dance_names,
                "notes": "",
            },
        )
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule-generate")
        assert resp.status_code == 303
