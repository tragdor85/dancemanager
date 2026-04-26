"""Tests for update and delete endpoints.

Covers: POST /{entity}/{id} updates with validation, DELETE /{entity}/{id} removal.
"""

from tests.web_helpers import make_test_client, seed_data

# ──────────────────────────────────────────────────────────────────────
# 5. Update endpoints (POST /dancers/{id}, etc.)
# ──────────────────────────────────────────────────────────────────────


class TestUpdateEndpoints:
    """Tests for all POST update endpoints."""

    # -- Dancer update --
    def test_update_dancer_success(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        client.post("/teams/red", data={"name": "Red Team Updated", "dancer_ids": ""})
        team = store.get("teams", "red")
        assert team["name"] == "Red Team Updated"

    def test_update_team_no_name_400(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/teams/red", data={"name": "", "dancer_ids": ""})
        assert resp.status_code == 400

    def test_update_team_removes_dancers(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.delete("/dancers/alice")
        assert "/dancers" in str(resp.headers.get("location", ""))

    def test_delete_team_success(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.delete("/recitals/spring")
        assert "/recitals" in str(resp.headers.get("location", ""))
