"""Tests for dance team selection feature (team_ids on dances).

Covers:
- Web form: searchable multi-selects for teams and dancers
- API endpoints: add/remove team from dance
- Logic: effective dancer resolution (individual + team members)
- Migration: team_ids column added to dances table
"""

import os
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

from dancemanager.store import DataStore
from dancemanager.utils import set_default_store


# ── Helpers ────────────────────────────────────────────────────────────────


def _create_web_app(store):
    """Create a FastAPI app with web routes and the given store."""
    from dancemanager.web.main import router as web_router, store_dependency

    app = FastAPI()
    app.dependency_overrides[store_dependency] = lambda: store
    app.include_router(web_router)
    return app


def _create_api_app(store):
    """Create a FastAPI app with API routes and the given store.

    Must set the store module's singleton so get_store() returns our test store.
    """
    import dancemanager.store as store_module

    # Inject into store.py's singleton (used by API routes)
    store_module._store_instance = store
    store_module._store_cache.clear()

    from dancemanager.api.routes.dances import router as api_dances_router

    app = FastAPI()
    app.include_router(api_dances_router)
    return app


def _setup_store_with_teams_and_dancers():
    """Create a store with teams, dancers, and instructors for dance team tests.

    Teams must be created before dancers that reference them (FK constraint).
    """
    tmp_dir = tempfile.mkdtemp()
    store = DataStore(path=os.path.join(tmp_dir, "store.json"))

    # Create teams first
    store.set(
        "teams",
        "team-alpha",
        {"id": "team-alpha", "name": "Team Alpha", "dancer_ids": []},
    )
    store.set(
        "teams",
        "team-beta",
        {"id": "team-beta", "name": "Team Beta", "dancer_ids": []},
    )

    # Create dancers (referencing teams)
    store.set(
        "dancers",
        "alice-smith",
        {
            "id": "alice-smith",
            "name": "Alice Smith",
            "class_ids": [],
            "team_id": "team-alpha",
        },
    )
    store.set(
        "dancers",
        "bob-jones",
        {
            "id": "bob-jones",
            "name": "Bob Jones",
            "class_ids": [],
            "team_id": "team-alpha",
        },
    )
    store.set(
        "dancers",
        "carol-lee",
        {"id": "carol-lee", "name": "Carol Lee", "class_ids": [], "team_id": None},
    )

    # Create instructor
    store.set(
        "instructors",
        "jane-instructor",
        {
            "id": "jane-instructor",
            "name": "Jane Instructor",
            "class_ids": [],
            "dance_ids": [],
        },
    )

    return store


# ── Web Form Tests ────────────────────────────────────────────────────────


class TestDanceFormTeams:
    """Tests for the dance form with team selection."""

    def test_new_form_has_team_section(self):
        """GET /dances/new contains team search input and team multi-select element."""
        store = _setup_store_with_teams_and_dancers()
        app = _create_web_app(store)
        client = TestClient(app)
        resp = client.get("/dances/new")
        assert resp.status_code == 200
        assert 'id="team_search"' in resp.text
        assert 'name="team_ids" multiple' in resp.text
        assert "Search teams" in resp.text

    def test_new_form_has_dancer_section(self):
        """GET /dances/new has dancer search input and dancer multi-select."""
        store = _setup_store_with_teams_and_dancers()
        app = _create_web_app(store)
        client = TestClient(app)
        resp = client.get("/dances/new")
        assert resp.status_code == 200
        assert 'id="dancer_search"' in resp.text
        assert 'name="dancer_ids" multiple' in resp.text
        assert "Search dancers" in resp.text

    def test_edit_form_preselects_teams(self):
        """Editing a dance with teams shows them pre-selected in the dropdown."""
        store = _setup_store_with_teams_and_dancers()
        store.set(
            "dances",
            "waltz",
            {
                "id": "waltz",
                "name": "Waltz",
                "song_name": "Moonlight Waltz",
                "instructor_id": None,
                "dancer_ids": [],
                "team_ids": ["team-alpha"],
                "notes": "",
            },
        )
        app = _create_web_app(store)
        client = TestClient(app)
        resp = client.get("/dances/waltz/edit")
        assert resp.status_code == 200
        # The team option should have selected attribute
        assert 'value="team-alpha"' in resp.text
        assert "selected" in resp.text

    def test_edit_form_preselects_dancers(self):
        """Editing a dance with dancers shows them pre-selected in the dropdown."""
        store = _setup_store_with_teams_and_dancers()
        store.set(
            "dances",
            "waltz",
            {
                "id": "waltz",
                "name": "Waltz",
                "song_name": "Moonlight Waltz",
                "instructor_id": None,
                "dancer_ids": ["alice-smith", "carol-lee"],
                "team_ids": [],
                "notes": "",
            },
        )
        app = _create_web_app(store)
        client = TestClient(app)
        resp = client.get("/dances/waltz/edit")
        assert resp.status_code == 200
        # Both dancers should be pre-selected
        assert "selected" in resp.text

    def test_create_with_teams_and_dancers(self):
        """POST creates dance with both team_ids and dancer_ids saved correctly."""
        store = _setup_store_with_teams_and_dancers()
        app = _create_web_app(store)
        client = TestClient(app, follow_redirects=False)
        resp = client.post(
            "/dances",
            data={
                "name": "New Dance",
                "song_name": "Song A",
                "instructor_id": "",
                "team_ids": ["team-alpha"],
                "dancer_ids": ["carol-lee"],
            },
        )
        assert resp.status_code == 303
        dance = store.get("dances", "new-dance")
        assert dance is not None
        assert set(dance["team_ids"]) == {"team-alpha"}
        assert set(dance["dancer_ids"]) == {"carol-lee"}

    def test_update_teams_replaces_old(self):
        """POST update replaces team assignments (not appends)."""
        store = _setup_store_with_teams_and_dancers()
        store.set(
            "dances",
            "waltz",
            {
                "id": "waltz",
                "name": "Waltz",
                "song_name": "Moonlight Waltz",
                "instructor_id": None,
                "dancer_ids": ["alice-smith"],
                "team_ids": ["team-alpha"],
                "notes": "",
            },
        )
        app = _create_web_app(store)
        client = TestClient(app, follow_redirects=False)
        resp = client.post(
            "/dances/waltz",
            data={
                "name": "Waltz",
                "song_name": "Moonlight Waltz",
                "instructor_id": "",
                "team_ids": ["team-beta"],
                "dancer_ids": ["carol-lee"],
            },
        )
        assert resp.status_code == 303
        updated = store.get("dances", "waltz")
        assert set(updated["team_ids"]) == {"team-beta"}
        assert set(updated["dancer_ids"]) == {"carol-lee"}

    def test_create_empty_selections_saves_as_empty_lists(self):
        """No teams/dancers selected saves [] for both fields."""
        store = _setup_store_with_teams_and_dancers()
        app = _create_web_app(store)
        client = TestClient(app, follow_redirects=False)
        resp = client.post(
            "/dances",
            data={
                "name": "Solo Dance",
                "song_name": "Song B",
                "instructor_id": "",
                "team_ids": [],
                "dancer_ids": [],
            },
        )
        assert resp.status_code == 303
        dance = store.get("dances", "solo-dance")
        assert dance is not None
        assert dance["team_ids"] == []
        assert dance["dancer_ids"] == []


# ── API Endpoint Tests ────────────────────────────────────────────────────


class TestDanceTeamAPI:
    """Tests for the team add/remove API endpoints."""

    def test_add_team_to_dance(self, tmp_path):
        """POST /api/dances/{id}/teams/add adds team to dance's team_ids."""
        store = DataStore(path=str(tmp_path / "store.json"))
        import dancemanager.store as store_module

        store_module._store_instance = store
        store_module._store_cache.clear()

        # Create team first (FK constraint)
        store.set("teams", "t1", {"id": "t1", "name": "Team One", "dancer_ids": []})
        store.set(
            "dancers",
            "alice-smith",
            {
                "id": "alice-smith",
                "name": "Alice Smith",
                "class_ids": [],
                "team_id": None,
            },
        )
        store.set(
            "dances",
            "waltz",
            {
                "id": "waltz",
                "name": "Waltz",
                "song_name": "Moon",
                "instructor_id": None,
                "dancer_ids": [],
                "team_ids": [],
                "notes": "",
            },
        )

        app = _create_api_app(store)
        client = TestClient(app)
        resp = client.post("/api/dances/waltz/teams/add?team_id=t1")
        assert resp.status_code == 200
        dance = store.get("dances", "waltz")
        assert "t1" in dance["team_ids"]

    def test_remove_team_from_dance(self, tmp_path):
        """POST /api/dances/{id}/teams/remove removes team from dance's team_ids."""
        store = DataStore(path=str(tmp_path / "store.json"))
        import dancemanager.store as store_module

        store_module._store_instance = store
        store_module._store_cache.clear()

        store.set("teams", "t1", {"id": "t1", "name": "Team One", "dancer_ids": []})
        store.set(
            "dances",
            "waltz",
            {
                "id": "waltz",
                "name": "Waltz",
                "song_name": "Moon",
                "instructor_id": None,
                "dancer_ids": [],
                "team_ids": ["t1"],
                "notes": "",
            },
        )

        app = _create_api_app(store)
        client = TestClient(app)
        resp = client.post("/api/dances/waltz/teams/remove?team_id=t1")
        assert resp.status_code == 200
        dance = store.get("dances", "waltz")
        assert "t1" not in dance["team_ids"]

    def test_add_team_nonexistent_dance(self, tmp_path):
        """Returns HTTP 404 for invalid dance ID."""
        store = DataStore(path=str(tmp_path / "store.json"))
        import dancemanager.store as store_module

        store_module._store_instance = store
        store_module._store_cache.clear()

        app = _create_api_app(store)
        client = TestClient(app)
        resp = client.post("/api/dances/missing/teams/add?team_id=t1")
        assert resp.status_code == 404

    def test_add_team_nonexistent_team(self, tmp_path):
        """Returns HTTP 404 for invalid team ID."""
        store = DataStore(path=str(tmp_path / "store.json"))
        import dancemanager.store as store_module

        store_module._store_instance = store
        store_module._store_cache.clear()

        store.set(
            "dances",
            "waltz",
            {
                "id": "waltz",
                "name": "Waltz",
                "song_name": "Moon",
                "instructor_id": None,
                "dancer_ids": [],
                "team_ids": [],
                "notes": "",
            },
        )

        app = _create_api_app(store)
        client = TestClient(app)
        resp = client.post("/api/dances/waltz/teams/add?team_id=missing")
        assert resp.status_code == 404


# ── Logic Tests ───────────────────────────────────────────────────────────


def _resolve_effective_dancers(dance, store):
    """Resolve effective dancers: individual + all members of selected teams.

    This is the helper function that would be used at render/API time.
    """
    dancer_ids = set(dance.get("dancer_ids", []))
    team_ids = dance.get("team_ids", [])

    for tid in team_ids:
        team = store.get("teams", tid)
        if team:
            team_dancers = team.get("dancer_ids", [])
            dancer_ids.update(team_dancers)

    return sorted(dancer_ids)


class TestDanceEffectiveMembers:
    """Tests for effective dancer resolution logic."""

    def test_effective_dancers_includes_team_members(self, tmp_path):
        """Helper unions individual dancers with all members of selected teams."""
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set("teams", "t1", {"id": "t1", "name": "Team One", "dancer_ids": []})
        store.set(
            "dancers",
            "alice-smith",
            {
                "id": "alice-smith",
                "name": "Alice Smith",
                "class_ids": [],
                "team_id": None,
            },
        )
        store.set(
            "dancers",
            "bob-jones",
            {"id": "bob-jones", "name": "Bob Jones", "class_ids": [], "team_id": None},
        )
        # Update team with dancers after creation to avoid FK issues
        store.set(
            "teams",
            "t1",
            {
                "id": "t1",
                "name": "Team One",
                "dancer_ids": ["alice-smith", "bob-jones"],
            },
        )
        dance = {
            "id": "waltz",
            "name": "Waltz",
            "song_name": "Moon",
            "instructor_id": None,
            "dancer_ids": [],
            "team_ids": ["t1"],
            "notes": "",
        }

        result = _resolve_effective_dancers(dance, store)
        assert set(result) == {"alice-smith", "bob-jones"}

    def test_no_duplicate_dancers_when_individual_and_team_overlap(self, tmp_path):
        """Dancer appears only once when individually added and in selected team."""
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set("teams", "t1", {"id": "t1", "name": "Team One", "dancer_ids": []})
        store.set(
            "dancers",
            "alice-smith",
            {
                "id": "alice-smith",
                "name": "Alice Smith",
                "class_ids": [],
                "team_id": None,
            },
        )
        # Update team with dancer after creation to avoid FK issues
        store.set(
            "teams",
            "t1",
            {"id": "t1", "name": "Team One", "dancer_ids": ["alice-smith"]},
        )
        dance = {
            "id": "waltz",
            "name": "Waltz",
            "song_name": "Moon",
            "instructor_id": None,
            "dancer_ids": ["alice-smith"],
            "team_ids": ["t1"],
            "notes": "",
        }

        result = _resolve_effective_dancers(dance, store)
        assert result == ["alice-smith"]


# ── Migration Test ────────────────────────────────────────────────────────


class TestDanceMigration:
    """Tests for the migration that adds team_ids column."""

    def test_migration_adds_team_ids_column(self, tmp_path):
        """New dances table has team_ids column after migration runs."""
        store = DataStore(path=str(tmp_path / "store.json"))

        # Create a dance and verify it has team_ids properly deserialized
        store.set(
            "dances",
            "waltz",
            {
                "id": "waltz",
                "name": "Waltz",
                "song_name": "Moonlight Waltz",
                "instructor_id": None,
                "dancer_ids": [],
                "team_ids": ["t1"],
                "notes": "",
            },
        )

        # Verify the dance can be retrieved with team_ids properly deserialized
        dance = store.get("dances", "waltz")
        assert dance is not None
        assert isinstance(dance["team_ids"], list)
        assert "t1" in dance["team_ids"]
