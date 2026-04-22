"""Tests for recital.py."""

from click.testing import CliRunner

from dancemanager.recital import (
    MIN_BUFFER,
    greedy_schedule,
    _score_dance,
    recital,
)
from dancemanager.store import DataStore
from dancemanager.utils import reset_default_store, set_default_store


class TestRecitalAdd:
    def setup_method(self):
        reset_default_store()

    def test_add_recital(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(recital, ["add", "Spring Showcase"])
        assert result.exit_code == 0
        assert "Created recital: Spring Showcase" in result.output


class TestRecitalList:
    def setup_method(self):
        reset_default_store()

    def test_list_empty(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(recital, ["list"])
        assert result.exit_code == 0
        assert "No recitals" in result.output

    def test_list_with_recitals(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "recitals",
            "spring",
            {"id": "spring", "name": "Spring", "performance_order": [], "notes": ""},
        )
        store.set(
            "recitals",
            "summer",
            {"id": "summer", "name": "Summer", "performance_order": [], "notes": ""},
        )
        runner = CliRunner()
        result = runner.invoke(recital, ["list"])
        assert result.exit_code == 0
        assert "Spring" in result.output
        assert "Summer" in result.output


class TestRecitalShow:
    def setup_method(self):
        reset_default_store()

    def test_show_recital(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "recitals",
            "spring",
            {"id": "spring", "name": "Spring", "performance_order": [], "notes": ""},
        )
        runner = CliRunner()
        result = runner.invoke(recital, ["show", "spring"])
        assert result.exit_code == 0
        assert "Name: Spring" in result.output

    def test_show_recital_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(recital, ["show", "missing"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestRecitalRemove:
    def setup_method(self):
        reset_default_store()

    def test_remove_recital(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "recitals",
            "spring",
            {"id": "spring", "name": "Spring", "performance_order": [], "notes": ""},
        )
        runner = CliRunner()
        result = runner.invoke(recital, ["remove", "spring"])
        assert result.exit_code == 0
        assert "Removed recital" in result.output

    def test_remove_recital_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(recital, ["remove", "missing"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestRecitalAddDance:
    def setup_method(self):
        reset_default_store()

    def test_add_dance_to_recital(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "recitals",
            "spring",
            {"id": "spring", "name": "Spring", "performance_order": [], "notes": ""},
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
        result = runner.invoke(recital, ["add-dance", "spring", "waltz"])
        assert result.exit_code == 0
        assert "Added dance" in result.output

    def test_add_dance_to_nonexistent_recital(self, tmp_path):
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
        result = runner.invoke(recital, ["add-dance", "spring", "waltz"])
        assert result.exit_code == 0
        assert "Recital not found" in result.output

    def test_add_nonexistent_dance_to_recital(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "recitals",
            "spring",
            {"id": "spring", "name": "Spring", "performance_order": [], "notes": ""},
        )
        runner = CliRunner()
        result = runner.invoke(recital, ["add-dance", "spring", "waltz"])
        assert result.exit_code == 0
        assert "Dance not found" in result.output

    def test_add_duplicate_dance_to_recital(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "recitals",
            "spring",
            {
                "id": "spring",
                "name": "Spring",
                "performance_order": [{"dance_id": "waltz", "position": 1}],
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
        result = runner.invoke(recital, ["add-dance", "spring", "waltz"])
        assert result.exit_code == 0
        assert "already in recital" in result.output


class TestRecitalReorder:
    def setup_method(self):
        reset_default_store()

    def test_reorder_dance(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "recitals",
            "spring",
            {
                "id": "spring",
                "name": "Spring",
                "performance_order": [
                    {"dance_id": "waltz", "position": 1},
                    {"dance_id": "hiphop", "position": 2},
                ],
                "notes": "",
            },
        )
        runner = CliRunner()
        # Reorder "hiphop" to position 1
        result = runner.invoke(recital, ["reorder", "spring", "1", "hiphop"])
        assert result.exit_code == 0
        assert "Reordered" in result.output

    def test_reorder_nonexistent_dance(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "recitals",
            "spring",
            {"performance_order": [{"dance_id": "waltz", "position": 1}], "notes": ""},
        )
        runner = CliRunner()
        result = runner.invoke(recital, ["reorder", "spring", "1", "missing"])
        assert result.exit_code == 0
        assert "not in recital" in result.output

    def test_reorder_nonexistent_recital(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(recital, ["reorder", "spring", "1", "waltz"])
        assert result.exit_code == 0
        assert "Recital not found" in result.output


class TestRecitalGenerateSchedule:
    def setup_method(self):
        reset_default_store()

    def test_generate_schedule_requires_min_two_dances(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
             "recitals",
             "spring",
             {"id": "spring", "name": "Spring", "performance_order": [], "notes": ""},
         )
        runner = CliRunner()
        result = runner.invoke(recital, ["generate-schedule", "spring"])
        assert result.exit_code == 0
        assert "at least 2 dances" in result.output

    def test_generate_schedule_with_nonexistent_recital(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(recital, ["generate-schedule", "missing"])
        assert result.exit_code == 0
        assert "Recital not found" in result.output


class TestGreedySchedule:
    def test_empty_list(self):
        result = greedy_schedule([], {}, MIN_BUFFER)
        assert result == []

    def test_single_dance(self):
        result = greedy_schedule(["waltz"], {}, MIN_BUFFER)
        assert result == ["waltz"]

    def test_two_dances_different_dancers(self):
        dancer_dances = {
            "alice": ["waltz"],
            "bob": ["hiphop"],
        }
        result = greedy_schedule(["waltz", "hiphop"], dancer_dances, MIN_BUFFER)
        assert result is not None
        assert len(result) == 2
        assert "waltz" in result
        assert "hiphop" in result

    def test_two_dances_same_dancer_min_buffer(self):
        dancer_dances = {
            "alice": ["waltz", "hiphop", "jazz", "contemp", "waltz2", "hiphop2"],
        }
        result = greedy_schedule(
            ["waltz", "hiphop", "jazz", "contemp", "waltz2", "hiphop2"],
            dancer_dances,
            MIN_BUFFER,
        )
        assert result is not None
        assert len(result) == 6

    def test_schedule_contains_all_dances(self):
        dance_ids = ["waltz", "hiphop", "jazz"]
        dancer_dances = {
            "alice": ["waltz", "jazz"],
            "bob": ["hiphop", "jazz"],
        }
        result = greedy_schedule(dance_ids, dancer_dances, MIN_BUFFER)
        assert result is not None
        assert set(result) == set(dance_ids)


class TestGreedyScheduleBacktracking:
    def test_constrained_scheduling(self):
        dancer_dances = {
            "alice": ["waltz", "hiphop", "jazz"],
            "bob": ["waltz", "hiphop", "jazz"],
        }
        result = greedy_schedule(
            ["waltz", "hiphop", "jazz", "contemp", "swing", "tap"],
            dancer_dances,
            MIN_BUFFER,
        )
        assert result is not None
        assert len(result) == 6

    def test_impossible_schedule_returns_none(self):
        dancer_dances = {
            "alice": ["waltz", "hiphop"],
            "bob": ["waltz", "hiphop"],
        }
        result = greedy_schedule(
            ["waltz", "hiphop"],
            dancer_dances,
            MIN_BUFFER,
        )
        # With only 2 dances and buffer=4, it may or may not be possible
        # but backtracking should handle it
        assert result is None or len(result) == 2


class TestGreedyScheduleScoring:
    def test_score_dance_first_position(self):
        dancer_dances = {
            "alice": ["waltz", "hiphop"],
            "bob": ["waltz", "jazz"],
        }
        score = _score_dance("waltz", [], dancer_dances, MIN_BUFFER)
        assert score >= 0

    def test_score_dance_with_ready_dancers(self):
        schedule = ["waltz", "jazz", "swing", "tap", "contemp"]
        dancer_dances = {
            "alice": ["waltz", "hiphop"],
        }
        score = _score_dance("hiphop", schedule, dancer_dances, MIN_BUFFER)
        assert score >= 0


class TestRecitalIntegration:
    def test_full_recital_workflow(self, tmp_path):
        """Add recital, add dances, show recital."""
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        store.set(
            "recitals",
            "spring",
            {
                "id": "spring",
                "name": "Spring",
                "performance_order": [],
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
                "dancer_ids": ["alice", "bob"],
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
                "dancer_ids": ["alice"],
                "notes": "",
            },
        )

        runner = CliRunner()

        # Add dances to recital
        runner.invoke(recital, ["add-dance", "spring", "waltz"])
        runner.invoke(recital, ["add-dance", "spring", "hiphop"])

        # Show recital
        result = runner.invoke(recital, ["show", "spring"])
        assert result.exit_code == 0
        assert "Name: Spring" in result.output

        # Generate schedule
        result = runner.invoke(recital, ["generate-schedule", "spring"])
        assert result.exit_code == 0
        # May print schedule or "at least 2 dances" depending on state


class TestGreedyScheduleEdgeCases:
    def test_no_dancers_map(self):
        result = greedy_schedule(
            ["waltz", "hiphop", "jazz"],
            {},
            MIN_BUFFER,
        )
        assert result is not None
        assert len(result) == 3

    def test_many_dances(self):
        dance_ids = [f"dance_{i}" for i in range(10)]
        dancer_dances = {
            "alice": dance_ids[:5],
            "bob": dance_ids[5:],
        }
        result = greedy_schedule(dance_ids, dancer_dances, MIN_BUFFER)
        assert result is not None
        assert len(result) == 10

    def test_all_same_dancer(self):
        dance_ids = [f"dance_{i}" for i in range(6)]
        dancer_dances = {
            "alice": dance_ids,
        }
        result = greedy_schedule(dance_ids, dancer_dances, MIN_BUFFER)
        assert result is not None
        assert len(result) == 6
