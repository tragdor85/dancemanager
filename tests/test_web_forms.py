"""Tests for web forms in main.py."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from dancemanager.store import DataStore
import tempfile
import os

# Import directly from main.py to avoid circular imports
import dancemanager.web.main as main


def create_app_with_store(store):
    """Create a FastAPI app with the given store for testing."""
    app = FastAPI()
    app.dependency_overrides[main.store_dependency] = lambda: store
    app.include_router(main.router)
    return app


class TestDancerForm:
    """Tests for the dancer form."""

    def test_dancer_new_form_exists(self):
        """Test that the new dancer form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/dancers/new")
        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "dancer" in response.text.lower()

    def test_dancer_new_form_has_required_fields(self):
        """Test that the new dancer form has all required fields."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/dancers/new")
        assert response.status_code == 200
        assert 'name="name"' in response.text
        assert 'name="class_ids"' in response.text
        assert 'name="team_id"' in response.text

    def test_dancer_edit_form_exists(self):
        """Test that the edit dancer form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/dancers/d1/edit")
        assert response.status_code == 200
        assert "form" in response.text.lower()


class TestTeamForm:
    """Tests for the team form."""

    def test_team_new_form_exists(self):
        """Test that the new team form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/teams/new")
        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "team" in response.text.lower()

    def test_team_new_form_has_required_fields(self):
        """Test that the new team form has all required fields."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/teams/new")
        assert response.status_code == 200
        assert 'name="name"' in response.text
        assert 'name="dancer_ids"' in response.text

    def test_team_edit_form_exists(self):
        """Test that the edit team form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/teams/t1/edit")
        assert response.status_code == 200
        assert "form" in response.text.lower()


class TestClassForm:
    """Tests for the class form."""

    def test_class_new_form_exists(self):
        """Test that the new class form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/classes/new")
        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "class" in response.text.lower()

    def test_class_new_form_has_required_fields(self):
        """Test that the new class form has all required fields."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/classes/new")
        assert response.status_code == 200
        assert 'name="name"' in response.text
        assert 'name="instructor_id"' in response.text
        assert 'name="team_ids"' in response.text

    def test_class_edit_form_exists(self):
        """Test that the edit class form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/classes/c1/edit")
        assert response.status_code == 200
        assert "form" in response.text.lower()

    def test_class_edit_form_uses_team_dropdown(self):
        """Edit class form uses a select dropdown for teams, not a text input."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": []}
            )
            store.set(
                "teams", "t2", {"id": "t2", "name": "Team Beta", "dancer_ids": []}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": ["t1"],
                    "dancer_ids": [],
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/classes/c1/edit")
        assert response.status_code == 200
        # Should use a select element, not an input text field
        assert '<select id="team_ids"' in response.text
        assert 'name="team_ids" multiple' in response.text
        # Pre-selected team should have selected attribute
        assert 'value="t1"' in response.text
        assert "selected" in response.text

    def test_class_create_with_teams(self):
        """Creating a class with teams saves them correctly."""
        tmp_dir = tempfile.mkdtemp()
        store = DataStore(path=os.path.join(tmp_dir, "store.json"))
        store.set("teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": []})
        store.set("teams", "t2", {"id": "t2", "name": "Team Beta", "dancer_ids": []})

        app = create_app_with_store(store)
        client = TestClient(app, follow_redirects=False)
        resp = client.post(
            "/classes",
            data={"name": "New Class", "instructor_id": "", "team_ids": ["t1", "t2"]},
        )
        assert resp.status_code == 303

        new_class = store.get("classes", "new-class")
        assert new_class is not None
        assert set(new_class["team_ids"]) == {"t1", "t2"}

    def test_class_update_with_teams(self):
        """Updating a class with teams saves them correctly."""
        tmp_dir = tempfile.mkdtemp()
        store = DataStore(path=os.path.join(tmp_dir, "store.json"))
        store.set("teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": []})
        store.set("teams", "t2", {"id": "t2", "name": "Team Beta", "dancer_ids": []})
        store.set(
            "classes",
            "c1",
            {
                "id": "c1",
                "name": "Old Name",
                "instructor_id": None,
                "team_ids": ["t1"],
                "dancer_ids": [],
            },
        )

        app = create_app_with_store(store)
        client = TestClient(app, follow_redirects=False)
        resp = client.post(
            "/classes/c1",
            data={"name": "Updated Name", "instructor_id": "", "team_ids": ["t2"]},
        )
        assert resp.status_code == 303

        updated_class = store.get("classes", "c1")
        assert updated_class is not None
        assert updated_class["name"] == "Updated Name"
        assert set(updated_class["team_ids"]) == {"t2"}


class TestInstructorForm:
    """Tests for the instructor form."""

    def test_instructor_new_form_exists(self):
        """Test that the new instructor form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/instructors/new")
        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "instructor" in response.text.lower()

    def test_instructor_new_form_has_required_fields(self):
        """Test that the new instructor form has all required fields."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/instructors/new")
        assert response.status_code == 200
        assert 'name="name"' in response.text
        assert 'name="class_ids"' in response.text
        assert 'name="dance_ids"' in response.text

    def test_instructor_edit_form_exists(self):
        """Test that the edit instructor form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/instructors/i1/edit")
        assert response.status_code == 200
        assert "form" in response.text.lower()


class TestInstructorFormMultiSelect:
    """Tests for instructor form multi-select dropdowns."""

    def _setup_store(self):
        tmp_dir = tempfile.mkdtemp()
        store = DataStore(path=os.path.join(tmp_dir, "store.json"))
        store.set(
            "classes",
            "c1",
            {
                "id": "c1",
                "name": "Ballet Class",
                "instructor_id": None,
                "team_ids": [],
                "dancer_ids": [],
            },
        )
        store.set(
            "classes",
            "c2",
            {
                "id": "c2",
                "name": "Jazz Class",
                "instructor_id": None,
                "team_ids": [],
                "dancer_ids": [],
            },
        )
        store.set(
            "dances",
            "dance1",
            {
                "id": "dance1",
                "name": "Dance One",
                "song_name": "Song A",
                "instructor_id": None,
                "dancer_ids": [],
                "notes": "",
            },
        )
        store.set(
            "dances",
            "dance2",
            {
                "id": "dance2",
                "name": "Dance Two",
                "song_name": "Song B",
                "instructor_id": None,
                "dancer_ids": [],
                "notes": "",
            },
        )
        return store

    def test_instructor_new_form_uses_multi_selects(self):
        """New instructor form uses select dropdowns for classes and dances."""
        store = self._setup_store()
        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/instructors/new")
        assert response.status_code == 200
        assert '<select id="class_ids" name="class_ids" multiple>' in response.text
        assert '<select id="dance_ids" name="dance_ids" multiple>' in response.text
        assert 'value="c1"' in response.text
        assert 'value="dance1"' in response.text

    def test_instructor_edit_form_preselects_classes(self):
        """Edit form pre-selects the classes assigned to the instructor."""
        store = self._setup_store()
        store.set(
            "instructors",
            "i1",
            {
                "id": "i1",
                "name": "Jane Instructor",
                "class_ids": ["c1"],
                "dance_ids": [],
            },
        )
        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/instructors/i1/edit")
        assert response.status_code == 200
        assert '<select id="class_ids" name="class_ids" multiple>' in response.text
        assert "selected" in response.text
        assert 'value="c1"' in response.text

    def test_instructor_edit_form_preselects_dances(self):
        """Edit form pre-selects the dances assigned to the instructor."""
        store = self._setup_store()
        store.set(
            "instructors",
            "i1",
            {
                "id": "i1",
                "name": "Jane Instructor",
                "class_ids": [],
                "dance_ids": ["dance2"],
            },
        )
        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/instructors/i1/edit")
        assert response.status_code == 200
        assert '<select id="dance_ids" name="dance_ids" multiple>' in response.text
        assert "selected" in response.text
        assert 'value="dance2"' in response.text

    def test_instructor_create_with_multi_select(self):
        """Creating an instructor with multi-select saves selections correctly."""
        store = self._setup_store()
        app = create_app_with_store(store)
        client = TestClient(app, follow_redirects=False)
        resp = client.post(
            "/instructors",
            data={
                "name": "New Instructor",
                "class_ids": ["c1", "c2"],
                "dance_ids": ["dance1"],
            },
        )
        assert resp.status_code == 303
        new_instructor = store.get("instructors", "new-instructor")
        assert new_instructor is not None
        assert set(new_instructor["class_ids"]) == {"c1", "c2"}
        assert set(new_instructor["dance_ids"]) == {"dance1"}
        class_c1 = store.get("classes", "c1")
        assert class_c1["instructor_id"] == "new-instructor"
        class_c2 = store.get("classes", "c2")
        assert class_c2["instructor_id"] == "new-instructor"
        dance_dance1 = store.get("dances", "dance1")
        assert dance_dance1["instructor_id"] == "new-instructor"

    def test_instructor_update_with_multi_select(self):
        """Updating an instructor with multi-select replaces selections."""
        store = self._setup_store()
        store.set(
            "instructors",
            "i1",
            {
                "id": "i1",
                "name": "Jane Instructor",
                "class_ids": [],
                "dance_ids": [],
            },
        )
        store.set(
            "classes",
            "c1",
            {
                "id": "c1",
                "name": "Ballet Class",
                "instructor_id": "i1",
                "team_ids": [],
                "dancer_ids": [],
            },
        )
        app = create_app_with_store(store)
        client = TestClient(app, follow_redirects=False)
        resp = client.post(
            "/instructors/i1",
            data={
                "name": "Jane Instructor",
                "class_ids": ["c2"],
                "dance_ids": ["dance1", "dance2"],
            },
        )
        assert resp.status_code == 303
        updated = store.get("instructors", "i1")
        assert set(updated["class_ids"]) == {"c2"}
        assert set(updated["dance_ids"]) == {"dance1", "dance2"}
        class_c2 = store.get("classes", "c2")
        assert class_c2["instructor_id"] == "i1"
        class_c1 = store.get("classes", "c1")
        assert class_c1.get("instructor_id") is None
        dance_dance1 = store.get("dances", "dance1")
        assert dance_dance1["instructor_id"] == "i1"

    def test_instructor_create_with_no_selections(self):
        """Creating an instructor with no classes or dances saves empty lists."""
        store = self._setup_store()
        app = create_app_with_store(store)
        client = TestClient(app, follow_redirects=False)
        resp = client.post(
            "/instructors",
            data={
                "name": "Solo Instructor",
                "class_ids": [],
                "dance_ids": [],
            },
        )
        assert resp.status_code == 303
        new_instructor = store.get("instructors", "solo-instructor")
        assert new_instructor is not None
        assert new_instructor["class_ids"] == []
        assert new_instructor["dance_ids"] == []


class TestDanceForm:
    """Tests for the dance form."""

    def test_dance_new_form_exists(self):
        """Test that the new dance form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/dances/new")
        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "dance" in response.text.lower()

    def test_dance_new_form_has_required_fields(self):
        """Test that the new dance form has all required fields."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/dances/new")
        assert response.status_code == 200
        assert 'name="name"' in response.text
        assert 'name="song_name"' in response.text
        assert 'name="instructor_id"' in response.text
        assert 'name="dancer_ids"' in response.text

    def test_dance_edit_form_exists(self):
        """Test that the edit dance form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/dances/dance1/edit")
        assert response.status_code == 200
        assert "form" in response.text.lower()


class TestRecitalForm:
    """Tests for the recital form."""

    def test_recital_new_form_exists(self):
        """Test that the new recital form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/recitals/new")
        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "recital" in response.text.lower()

    def test_recital_new_form_has_required_fields(self):
        """Test that the new recital form has all required fields."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/recitals/new")
        assert response.status_code == 200
        assert 'name="name"' in response.text
        assert 'name="performance_order"' in response.text

    def test_recital_edit_form_exists(self):
        """Test that the edit recital form page is accessible."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = DataStore(path=os.path.join(tmp_dir, "store.json"))
            store.set(
                "dancers",
                "d1",
                {"id": "d1", "name": "Alice", "class_ids": [], "team_id": None},
            )
            store.set(
                "dancers",
                "d2",
                {"id": "d2", "name": "Bob", "class_ids": [], "team_id": None},
            )
            store.set(
                "teams", "t1", {"id": "t1", "name": "Team Alpha", "dancer_ids": ["d1"]}
            )
            store.set(
                "classes",
                "c1",
                {
                    "id": "c1",
                    "name": "Ballet Class",
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": ["d1", "d2"],
                },
            )
            store.set(
                "instructors",
                "i1",
                {
                    "id": "i1",
                    "name": "Jane Instructor",
                    "class_ids": ["c1"],
                    "dance_ids": [],
                },
            )
            store.set(
                "dances",
                "dance1",
                {
                    "id": "dance1",
                    "name": "Dance One",
                    "song_name": "Song A",
                    "instructor_id": None,
                    "dancer_ids": ["d1"],
                    "notes": "",
                },
            )
            store.set(
                "dances",
                "dance2",
                {
                    "id": "dance2",
                    "name": "Dance Two",
                    "song_name": "Song B",
                    "instructor_id": None,
                    "dancer_ids": ["d2"],
                    "notes": "",
                },
            )
            store.set(
                "recitals",
                "r1",
                {
                    "id": "r1",
                    "name": "Spring Recital",
                    "performance_order": [],
                    "notes": "",
                },
            )

        app = create_app_with_store(store)
        client = TestClient(app)
        response = client.get("/recitals/r1/edit")
        assert response.status_code == 200
        assert "form" in response.text.lower()
