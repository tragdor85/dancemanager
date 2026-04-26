"""Tests for instructors.py."""

from click.testing import CliRunner

from dancemanager.instructors import instructors
from dancemanager.store import DataStore
from dancemanager.utils import reset_default_store, set_default_store


class TestInstructorsAdd:
    def setup_method(self):
        reset_default_store()

    def test_add_instructor(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(instructors, ["add", "Charlie"])
        assert result.exit_code == 0
        assert "Added instructor: Charlie" in result.output

    def test_add_instructor_duplicate(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        runner.invoke(instructors, ["add", "Charlie"])
        result = runner.invoke(instructors, ["add", "Charlie"])
        assert result.exit_code == 0
        assert "already exists" in result.output


class TestInstructorsList:
    def setup_method(self):
        reset_default_store()

    def test_list_empty(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(instructors, ["list"])
        assert result.exit_code == 0
        assert "No instructors" in result.output

    def test_list_with_instructors(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "instructors",
            "charlie",
            {
                "id": "charlie",
                "name": "Charlie",
                "class_ids": [],
                "dance_ids": [],
                "notes": "",
            },
        )
        store.set(
            "instructors",
            "diana",
            {
                "id": "diana",
                "name": "Diana",
                "class_ids": [],
                "dance_ids": [],
                "notes": "",
            },
        )
        runner = CliRunner()
        result = runner.invoke(instructors, ["list"])
        assert result.exit_code == 0
        assert "Charlie" in result.output
        assert "Diana" in result.output


class TestInstructorsShow:
    def setup_method(self):
        reset_default_store()

    def test_show_instructor(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "instructors",
            "charlie",
            {
                "id": "charlie",
                "name": "Charlie",
                "class_ids": ["ballet"],
                "dance_ids": [],
                "notes": "",
            },
        )
        runner = CliRunner()
        result = runner.invoke(instructors, ["show", "charlie"])
        assert result.exit_code == 0
        assert "Name: Charlie" in result.output

    def test_show_instructor_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(instructors, ["show", "missing"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestInstructorsRemove:
    def setup_method(self):
        reset_default_store()

    def test_remove_instructor(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "instructors",
            "charlie",
            {
                "id": "charlie",
                "name": "Charlie",
                "class_ids": [],
                "dance_ids": [],
                "notes": "",
            },
        )
        runner = CliRunner()
        result = runner.invoke(instructors, ["remove", "charlie"])
        assert result.exit_code == 0
        assert "Removed instructor" in result.output

    def test_remove_instructor_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(instructors, ["remove", "missing"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestInstructorsAssignClass:
    def setup_method(self):
        reset_default_store()

    def test_assign_instructor_to_class(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "instructors",
            "charlie",
            {
                "id": "charlie",
                "name": "Charlie",
                "class_ids": [],
                "dance_ids": [],
                "notes": "",
            },
        )
        store.set(
            "classes",
            "ballet",
            {
                "id": "ballet",
                "name": "Ballet",
                "team_ids": [],
                "dancer_ids": [],
                "instructor_id": None,
                "notes": "",
            },
        )
        runner = CliRunner()
        result = runner.invoke(instructors, ["assign-class", "charlie", "ballet"])
        assert result.exit_code == 0
        assert "Assigned instructor" in result.output

    def test_assign_instructor_class_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "instructors",
            "charlie",
            {
                "id": "charlie",
                "name": "Charlie",
                "class_ids": [],
                "dance_ids": [],
                "notes": "",
            },
        )
        runner = CliRunner()
        result = runner.invoke(instructors, ["assign-class", "charlie", "ballet"])
        assert result.exit_code == 0
        assert "Class not found" in result.output

    def test_assign_instructor_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "classes",
            "ballet",
            {
                "id": "ballet",
                "name": "Ballet",
                "team_ids": [],
                "dancer_ids": [],
                "instructor_id": None,
                "notes": "",
            },
        )
        runner = CliRunner()
        result = runner.invoke(instructors, ["assign-class", "charlie", "ballet"])
        assert result.exit_code == 0
        assert "Instructor not found" in result.output


class TestInstructorsAssignDance:
    def setup_method(self):
        reset_default_store()

    def test_assign_instructor_to_dance(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "instructors",
            "charlie",
            {
                "id": "charlie",
                "name": "Charlie",
                "class_ids": [],
                "dance_ids": [],
                "notes": "",
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
                "notes": "",
            },
        )
        runner = CliRunner()
        result = runner.invoke(instructors, ["assign-dance", "charlie", "waltz"])
        assert result.exit_code == 0
        assert "Assigned instructor" in result.output

    def test_assign_instructor_dance_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "instructors",
            "charlie",
            {
                "id": "charlie",
                "name": "Charlie",
                "class_ids": [],
                "dance_ids": [],
                "notes": "",
            },
        )
        runner = CliRunner()
        result = runner.invoke(instructors, ["assign-dance", "charlie", "waltz"])
        assert result.exit_code == 0
        assert "Dance not found" in result.output

    def test_assign_instructor_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "dances",
            "waltz",
            {
                "id": "waltz",
                "name": "Waltz",
                "song_name": "Moon",
                "instructor_id": None,
                "dancer_ids": [],
                "notes": "",
            },
        )
        runner = CliRunner()
        result = runner.invoke(instructors, ["assign-dance", "charlie", "waltz"])
        assert result.exit_code == 0
        assert "Instructor not found" in result.output
