"""Tests for detail pages and create endpoints.

Covers: GET /{entity}/{id} detail views, POST /{entity} creation with validation.
"""

from tests.web_helpers import make_test_client, seed_data

# ──────────────────────────────────────────────────────────────────────
# 3. Detail pages (GET /dancers/{id}, etc.)
# ──────────────────────────────────────────────────────────────────────


class TestDetailPages:
    """Tests for all detail endpoints."""

    def test_dancer_detail_200(self):
        store = seed_data.__self__ if hasattr(seed_data, "__self__") else None
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers/alice")
        assert resp.status_code == 200

    def test_dancer_detail_shows_name(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers/alice")
        assert "Alice Smith" in resp.text

    def test_dancer_detail_404(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers/nonexistent")
        assert resp.status_code == 404

    def test_team_detail_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams/red")
        assert resp.status_code == 200

    def test_team_detail_shows_dancers(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams/red")
        assert "Alice Smith" in resp.text

    def test_team_detail_404(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams/nonexistent")
        assert resp.status_code == 404

    def test_class_detail_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes/ballet")
        assert resp.status_code == 200

    def test_class_detail_shows_dancers(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes/ballet")
        assert "Alice Smith" in resp.text

    def test_class_detail_404(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes/nonexistent")
        assert resp.status_code == 404

    def test_instructor_detail_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors/jane")
        assert resp.status_code == 200

    def test_instructor_detail_shows_name(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors/jane")
        assert "Jane Doe" in resp.text

    def test_instructor_detail_404(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors/nonexistent")
        assert resp.status_code == 404

    def test_dance_detail_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances/waltz")
        assert resp.status_code == 200

    def test_dance_detail_shows_name(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances/waltz")
        assert "Waltz" in resp.text

    def test_dance_detail_404(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances/nonexistent")
        assert resp.status_code == 404

    def test_recital_detail_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring")
        assert resp.status_code == 200

    def test_recital_detail_404(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/dancers", data={"class_ids": "", "team_id": ""})
        assert resp.status_code == 400

    # -- Team creation --
    def test_create_team_success(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/teams", data={"name": "Blue Team", "dancer_ids": ""})
        assert resp.status_code == 303

    def test_create_team_stores_data(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/teams", data={"name": "", "dancer_ids": ""})
        assert resp.status_code == 400

    def test_create_team_assigns_dancers(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.post("/recitals", data={"name": "", "performance_order": ""})
        assert resp.status_code == 400
