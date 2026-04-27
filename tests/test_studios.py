"""Tests for studio management."""

from click.testing import CliRunner

from dancemanager.studios import (
    add_studio,
    find_conflicts,
    get_available_slots,
    get_studio,
    get_studio_schedule,
    is_slot_conflicted,
    reserve_slot,
    studio,
)
from dancemanager.store import DataStore
from dancemanager.utils import reset_default_store, set_default_store


class TestStudioAdd:
    def setup_method(self):
        reset_default_store()

    def test_add_studio(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(studio, ["add", "Studio 1", "--location", "Room A"])
        assert result.exit_code == 0
        assert "Created studio: Studio 1" in result.output
        assert "studio-studio-1" in result.output

    def test_add_studio_with_capacity(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(
            studio, ["add", "Studio 2", "--location", "Room B", "--capacity", "30"]
        )
        assert result.exit_code == 0
        assert "Created studio: Studio 2" in result.output

    def test_add_studio_duplicate(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        runner.invoke(studio, ["add", "Studio 1"])
        result = runner.invoke(studio, ["add", "Studio 1"])
        assert result.exit_code == 0
        assert "already exists" in result.output


class TestStudioList:
    def setup_method(self):
        reset_default_store()

    def test_list_empty(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(studio, ["list"])
        assert result.exit_code == 0
        assert "No studios found" in result.output

    def test_list_with_studios(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Studio A", "Room 1")
        add_studio("Studio B", "Room 2")
        runner = CliRunner()
        result = runner.invoke(studio, ["list"])
        assert result.exit_code == 0
        assert "Studio A" in result.output
        assert "Studio B" in result.output


class TestStudioShow:
    def setup_method(self):
        reset_default_store()

    def test_show_studio(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Main Studio", "Room 101")
        runner = CliRunner()
        result = runner.invoke(studio, ["show", "studio-main-studio"])
        assert result.exit_code == 0
        assert "Name: Main Studio" in result.output
        assert "Location: Room 101" in result.output

    def test_show_studio_not_found(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(studio, ["show", "nonexistent"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestStudioRemove:
    def setup_method(self):
        reset_default_store()

    def test_remove_studio(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        result = runner.invoke(studio, ["remove", "studio-test-studio"])
        assert result.exit_code == 0
        assert "Removed studio" in result.output

    def test_remove_nonexistent(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(studio, ["remove", "nonexistent"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestStudioReserve:
    def setup_method(self):
        reset_default_store()

    def test_reserve_slot_success(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        result = runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )
        assert result.exit_code == 0
        assert "Reservation successful" in result.output

    def test_reserve_conflict(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )
        result = runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "jazz-201",
            ],
        )
        assert result.exit_code == 0
        assert "already reserved" in result.output

    def test_reserve_overlapping(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )
        # Overlapping time should fail
        result = runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "19:00",
                "--end-time",
                "20:00",
                "--reservation-type",
                "class",
                "--reservation-id",
                "jazz-201",
            ],
        )
        assert result.exit_code == 0
        assert "already reserved" in result.output

    def test_reserve_different_date(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )
        # Same time, different date should succeed
        result = runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-16",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "jazz-201",
            ],
        )
        assert result.exit_code == 0
        assert "Reservation successful" in result.output

    def test_reserve_individual(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Practice Room", "Room 3")
        runner = CliRunner()
        result = runner.invoke(
            studio,
            [
                "reserve",
                "studio-practice-room",
                "--date",
                "2024-07-01",
                "--start-time",
                "16:00",
                "--end-time",
                "17:00",
                "--reservation-type",
                "individual",
                "--reservation-id",
                "alice-smith",
            ],
        )
        assert result.exit_code == 0
        assert "Reservation successful" in result.output

    def test_reserve_nonexistent_studio(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        runner = CliRunner()
        result = runner.invoke(
            studio,
            [
                "reserve",
                "nonexistent-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )
        assert result.exit_code == 0
        assert "not found" in result.output


class TestStudioCancel:
    def setup_method(self):
        reset_default_store()

    def test_cancel_reservation(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )
        result = runner.invoke(
            studio,
            [
                "cancel",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-id",
                "ballet-101",
            ],
        )
        assert result.exit_code == 0
        assert "Reservation cancelled" in result.output

    def test_cancel_nonexistent(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        result = runner.invoke(
            studio,
            [
                "cancel",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-id",
                "ballet-101",
            ],
        )
        assert result.exit_code == 0
        assert "not found" in result.output


class TestStudioSchedule:
    def setup_method(self):
        reset_default_store()

    def test_schedule_empty(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        result = runner.invoke(studio, ["schedule", "studio-test-studio"])
        assert result.exit_code == 0
        assert "No scheduled reservations" in result.output

    def test_schedule_with_reservations(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "20:00",
                "--end-time",
                "21:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "jazz-201",
            ],
        )
        result = runner.invoke(studio, ["schedule", "studio-test-studio"])
        assert result.exit_code == 0
        assert "Schedule for Test Studio" in result.output
        assert "2024-06-15" in result.output


class TestConflictDetection:
    def setup_method(self):
        reset_default_store()

    def test_no_conflict_different_times(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        assert (
            is_slot_conflicted("studio-test-studio", "2024-06-15", "18:00", "19:30")
            is False
        )

    def test_conflict_same_time(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        reserve_slot(
            "studio-test-studio",
            "2024-06-15",
            "18:00",
            "19:30",
            "class",
            "ballet-101",
        )
        assert (
            is_slot_conflicted("studio-test-studio", "2024-06-15", "18:00", "19:30")
            is True
        )

    def test_find_conflicts(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        reserve_slot(
            "studio-test-studio",
            "2024-06-15",
            "18:00",
            "19:30",
            "class",
            "ballet-101",
        )
        conflicts = find_conflicts("studio-test-studio", "2024-06-15", "18:00", "19:30")
        assert len(conflicts) == 1
        assert conflicts[0]["reserved_by"] == "ballet-101"

    def test_get_available_slots(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        assert (
            get_available_slots("studio-test-studio", "2024-06-15", "18:00", "19:30")
            is True
        )

        reserve_slot(
            "studio-test-studio",
            "2024-06-15",
            "18:00",
            "19:30",
            "class",
            "ballet-101",
        )
        assert (
            get_available_slots("studio-test-studio", "2024-06-15", "18:00", "19:30")
            is False
        )


class TestStudioScheduleFunction:
    def setup_method(self):
        reset_default_store()

    def test_get_studio_schedule_sorted(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-20",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "jazz-201",
            ],
        )

        schedule = get_studio_schedule("studio-test-studio")
        assert len(schedule) == 2
        # Should be sorted by date
        assert schedule[0]["date"] == "2024-06-15"
        assert schedule[1]["date"] == "2024-06-20"


class TestStudioRemoveWithReservations:
    def setup_method(self):
        reset_default_store()

    def test_remove_studio_clears_reservations(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Test Studio", "Room 1")
        runner = CliRunner()
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-test-studio",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )
        result = runner.invoke(studio, ["remove", "studio-test-studio"])
        assert result.exit_code == 0

        # Verify studio is gone
        studio_data = get_studio("studio-test-studio")
        assert studio_data is None


class TestMultipleStudios:
    def setup_method(self):
        reset_default_store()

    def test_independent_schedules(self, tmp_path):
        store = DataStore(path=str(tmp_path / "store.json"))
        set_default_store(store)
        add_studio("Studio A", "Room 1")
        add_studio("Studio B", "Room 2")
        runner = CliRunner()

        # Book same time in both studios - should succeed independently
        runner.invoke(
            studio,
            [
                "reserve",
                "studio-studio-a",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "ballet-101",
            ],
        )

        result = runner.invoke(
            studio,
            [
                "reserve",
                "studio-studio-b",
                "--date",
                "2024-06-15",
                "--start-time",
                "18:00",
                "--end-time",
                "19:30",
                "--reservation-type",
                "class",
                "--reservation-id",
                "jazz-201",
            ],
        )
        assert result.exit_code == 0
        assert "Reservation successful" in result.output
