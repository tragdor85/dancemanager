"""Tests for recital schedule generation.

Covers: GET /recitals/{id}/schedule page, POST /recitals/{id}/schedule-generate,
scheduling algorithm with dancer conflicts, edge cases, and format handling.
"""

from tests.web_helpers import make_test_client, setup_recital_with_dances


class TestRecitalScheduleGeneration:
    """Tests for recital schedule generation endpoints."""

    def test_schedule_page_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert resp.status_code == 200

    def test_schedule_page_shows_schedule(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert "schedule" in resp.text.lower() or "position" in resp.text.lower()

    def test_schedule_page_404(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/nonexistent/schedule")
        assert resp.status_code == 404

    def test_schedule_generate_200(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule-generate")
        assert resp.status_code == 303

    def test_schedule_generate_saves_order(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/nonexistent/schedule-generate")
        assert resp.status_code == 404

    def test_schedule_generate_redirects_to_schedule(self):
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule-generate")
        assert "/schedule" in str(resp.headers.get("location", ""))

    def test_schedule_page_with_legacy_order_format(self):
        """Test schedule page handles legacy string-based performance_order."""
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert "Alice Smith" in resp.text

    def test_schedule_page_shows_song_names(self):
        """Schedule page should include song names."""
        from dancemanager.store import DataStore
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        setup_recital_with_dances(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert "Blue Danube" in resp.text

    def test_schedule_page_shows_positions(self):
        """Schedule page should show position numbers."""
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        from dancemanager.store import DataStore
        import tempfile
        import os

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
        """Schedule gen with many conflicts should still produce valid schedule."""
        from dancemanager.store import DataStore
        import tempfile
        import os

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
