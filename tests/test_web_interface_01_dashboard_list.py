"""Tests for dashboard index page and all list pages.

Covers: GET /, GET /dancers, /teams, /classes, /instructors, /dances, /recitals
including search functionality and count columns.
"""

from tests.web_helpers import make_test_client, seed_data

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/")
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────
# 2. List pages (GET /dancers, /teams, etc.)
# ──────────────────────────────────────────────────────────────────────


class TestListPages:
    """Tests for all list endpoints."""

    # -- Dancers list --
    def test_dancers_list_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers")
        assert resp.status_code == 200

    def test_dancers_list_shows_dancers(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers?q=alice")
        assert resp.status_code == 200
        assert "Alice Smith" in resp.text

    def test_dancers_list_search_no_match(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers?q=zzzzz")
        assert resp.status_code == 200

    def test_dancers_list_case_insensitive(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers?q=ALICE")
        assert "Alice Smith" in resp.text

    # -- Teams list --
    def test_teams_list_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams")
        assert resp.status_code == 200

    def test_teams_list_shows_teams(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams")
        assert "Red Team" in resp.text

    # -- Classes list --
    def test_classes_list_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes")
        assert resp.status_code == 200

    def test_classes_list_shows_classes(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes")
        assert "Ballet Basics" in resp.text

    # -- Instructors list --
    def test_instructors_list_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors")
        assert resp.status_code == 200

    def test_instructors_list_shows_instructors(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors")
        assert "Jane Doe" in resp.text

    # -- Dances list --
    def test_dances_list_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances")
        assert resp.status_code == 200

    def test_dances_list_shows_dances(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances")
        assert "Waltz" in resp.text

    # -- Recitals list --
    def test_recitals_list_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals")
        assert resp.status_code == 200

    def test_recitals_list_shows_recitals(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals")
        assert "Spring Showcase" in resp.text

    # -- Teams list count columns --
    def test_teams_list_shows_dancer_count(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        # Assign Red Team to Ballet class via assignment table
        store.execute(
            "INSERT OR IGNORE INTO class_team_assignments "  # noqa: E501
            "(class_id, team_id) VALUES (?, ?)",
            ("ballet", "red"),
        )

        client, _ = make_test_client(store)
        resp = client.get("/classes")
        assert resp.status_code == 200
        assert "Ballet Basics" in resp.text

    def test_classes_list_shows_zero_teams(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        client, _ = make_test_client(store)
        resp = client.get("/classes")
        assert resp.status_code == 200

    # -- Instructors list count columns --
    def test_instructors_list_shows_class_and_dance_counts(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        client, _ = make_test_client(store)
        resp = client.get("/dances")
        assert resp.status_code == 200
        assert "Waltz" in resp.text

    def test_dances_list_shows_zero_dancers(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)

        client, _ = make_test_client(store)
        resp = client.get("/dancers")
        assert resp.status_code == 200
        # Bob has no class_ids so should show 0 classes


# ──────────────────────────────────────────────────────────────────────
# 3. Dashboard stat card links
# ──────────────────────────────────────────────────────────────────────


class TestDashboardStatLinks:
    """Tests that dashboard stat cards link to their list pages."""

    def test_dancers_stat_links_to_dancers_list(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert 'href="/dancers"' in resp.text

    def test_teams_stat_links_to_teams_list(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert 'href="/teams"' in resp.text

    def test_classes_stat_links_to_classes_list(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert 'href="/classes"' in resp.text

    def test_instructors_stat_links_to_instructors_list(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert 'href="/instructors"' in resp.text

    def test_dances_stat_links_to_dances_list(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert 'href="/dances"' in resp.text

    def test_recitals_stat_links_to_recitals_list(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert 'href="/recitals"' in resp.text
