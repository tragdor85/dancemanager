"""Tests for dances.py."""

from click.testing import CliRunner

from dancemanager.dances import dances
from dancemanager.store import DataStore
from dancemanager.utils import reset_default_store, set_default_store


class TestDancesAdd:
    def setup_method(self):
        reset_default_store()

    def test_add_dance(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(dances, ["add", "Waltz", "Moonlight Waltz"])
        assert result.exit_code == 0
        assert "Created dance: Waltz" in result.output

    def test_add_dance_with_song(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        runner.invoke(dances, ["add", "Waltz", "Moonlight Waltz"])
        dance = store.get("dances", "waltz")
        assert dance is not None
        assert dance["song_name"] == "Moonlight Waltz"

    def test_add_dance_duplicate(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        runner.invoke(dances, ["add", "Waltz", "Moon"])
        result = runner.invoke(dances, ["add", "Waltz", "Moon"])
        assert result.exit_code == 0
        assert "already exists" in result.output


class TestDancesList:
    def setup_method(self):
        reset_default_store()

    def test_list_empty(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(dances, ["list"])
        assert result.exit_code == 0
        assert "No dances" in result.output

    def test_list_with_dances(self, tmp_path):
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
        store.set(
               "dances",
               "hiphop",
               {
                   "id": "hiphop",
                   "name": "Hip Hop",
                   "song_name": "Beat",
                   "instructor_id": None,
                   "dancer_ids": [],
                   "notes": "",
               },
           )
        runner = CliRunner()
        result = runner.invoke(dances, ["list"])
        assert result.exit_code == 0
        assert "Waltz" in result.output
        assert "Hip Hop" in result.output


class TestDancesShow:
    def setup_method(self):
        reset_default_store()

    def test_show_dance(self, tmp_path):
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
        result = runner.invoke(dances, ["show", "waltz"])
        assert result.exit_code == 0
        assert "Name: Waltz" in result.output

    def test_show_dance_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(dances, ["show", "missing"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestDancesRemove:
    def setup_method(self):
        reset_default_store()

    def test_remove_dance(self, tmp_path):
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
        result = runner.invoke(dances, ["remove", "waltz"])
        assert result.exit_code == 0
        assert "Removed dance" in result.output

    def test_remove_dance_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(dances, ["remove", "missing"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestDancesDancerAdd:
    def setup_method(self):
        reset_default_store()

    def test_add_dancer_to_dance(self, tmp_path):
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
        result = runner.invoke(dances, ["dancer-add", "waltz", "alice"])
        assert result.exit_code == 0
        assert "Added dancer" in result.output

    def test_add_dancer_to_nonexistent_dance(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(dances, ["dancer-add", "waltz", "alice"])
        assert result.exit_code == 0
        assert "Dance not found" in result.output


class TestDancesDancerRemove:
    def setup_method(self):
        reset_default_store()

    def test_remove_dancer_from_dance(self, tmp_path):
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
                   "dancer_ids": ["alice"],
                   "notes": "",
               },
           )
        runner = CliRunner()
        result = runner.invoke(dances, ["dancer-remove", "waltz", "alice"])
        assert result.exit_code == 0
        assert "Removed dancer" in result.output


class TestDancesExport:
    def setup_method(self):
        reset_default_store()

    def test_export_creates_file(self, tmp_path):
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
        filepath = str(tmp_path / "export.csv")
        result = runner.invoke(dances, ["export", "--filepath", filepath])
        assert result.exit_code == 0
        assert "Exported dances" in result.output
        assert tmp_path.joinpath("export.csv").exists()
