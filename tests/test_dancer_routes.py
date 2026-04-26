"""Tests for dancer list page, detail page, and edit functionality.

These tests ensure the Detail and Edit buttons on the dancer list page work correctly,
including proper routing to detail/edit pages and form rendering.
"""

import tempfile
import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

from dancemanager.store import DataStore
import dancemanager.web.main as main


def make_app(store):
    """Create a FastAPI app with the given store for testing."""
    app = FastAPI()
    app.dependency_overrides[main.store_dependency] = lambda: store
    app.include_router(main.router)
    return app


def make_test_client(store=None):
    """Create a TestClient that does not follow redirects by default."""
    if store is None:
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
    app = make_app(store)
    return TestClient(app, follow_redirects=False), store


def seed_dancers(store):
    """Populate the store with dancer test data."""
    store.set(
        "dancers",
        "alice-smith",
        {"id": "alice-smith", "name": "Alice Smith", "class_ids": [], "team_id": None},
    )
    store.set(
        "dancers",
        "bob-jones",
        {"id": "bob-jones", "name": "Bob Jones", "class_ids": [], "team_id": None},
    )


class TestDancerListPage:
    """Tests for the dancer list page and its action buttons."""

    def test_dancer_list_page_loads(self):
        """Test that the dancer list page loads successfully."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers")
        assert resp.status_code == 200
        assert "Dancers" in resp.text
        assert 'href="/dancers/alice-smith"' in resp.text
        assert 'href="/dancers/bob-jones"' in resp.text

    def test_dancer_list_shows_detail_link(self):
        """Test that the dancer list page shows Detail links for each dancer."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers")
        assert resp.status_code == 200
        # Check that Detail links exist for each dancer
        assert 'href="/dancers/alice-smith">Detail' in resp.text
        assert 'href="/dancers/bob-jones">Detail' in resp.text

    def test_dancer_list_shows_edit_link(self):
        """Test that the dancer list page shows Edit links for each dancer."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers")
        assert resp.status_code == 200
        # Check that Edit links exist for each dancer
        assert 'href="/dancers/alice-smith/edit">Edit' in resp.text
        assert 'href="/dancers/bob-jones/edit">Edit' in resp.text

    def test_dancer_list_name_clickable(self):
        """Test that the dancer name is a clickable link to detail page."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers")
        assert resp.status_code == 200
        # Check that dancer names are links to detail pages
        assert '<a href="/dancers/alice-smith">Alice Smith</a>' in resp.text
        assert '<a href="/dancers/bob-jones">Bob Jones</a>' in resp.text


class TestDancerDetailPage:
    """Tests for the dancer detail page accessed via Detail button."""

    def test_detail_page_loads(self):
        """Test that clicking Detail navigates to the detail page."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers/alice-smith")
        assert resp.status_code == 200
        assert "Alice Smith" in resp.text
        assert 'href="/dancers/alice-smith/edit"' in resp.text

    def test_detail_page_has_edit_button(self):
        """Test that the detail page has an Edit Dancer button."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers/alice-smith")
        assert resp.status_code == 200
        assert (
            'href="/dancers/alice-smith/edit" class="btn btn-primary">Edit Dancer'
            in resp.text
        )

    def test_detail_page_has_delete_button(self):
        """Test that the detail page has a Delete button with JavaScript handler."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers/alice-smith")
        assert resp.status_code == 200
        assert 'onclick="deleteDancer(' in resp.text
        assert "Delete" in resp.text
        # Verify the confirmDelete function is defined
        assert "function deleteDancer(id)" in resp.text

    def test_detail_page_404_for_unknown_dancer(self):
        """Test that detail page returns 404 for non-existent dancer."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers/nonexistent-dancer")
        assert resp.status_code == 404


class TestDancerEditPage:
    """Tests for the dancer edit page accessed via Edit button."""

    def test_edit_page_loads(self):
        """Test that clicking Edit navigates to the edit form."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers/alice-smith/edit")
        assert resp.status_code == 200
        assert 'name="name"' in resp.text
        assert 'value="Alice Smith"' in resp.text

    def test_edit_page_has_form_fields(self):
        """Test that the edit form has all required fields."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers/alice-smith/edit")
        assert resp.status_code == 200
        assert 'name="name"' in resp.text
        assert 'name="class_ids"' in resp.text
        assert 'name="team_id"' in resp.text

    def test_edit_page_404_for_unknown_dancer(self):
        """Test that edit page returns 404 for non-existent dancer."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers/nonexistent-dancer/edit")
        assert resp.status_code == 404


class TestDancerDelete:
    """Tests for the dancer delete functionality."""

    def test_delete_dancer(self):
        """Test that DELETE request removes a dancer and redirects."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        # Verify dancer exists before delete
        resp = client.get("/dancers/alice-smith")
        assert resp.status_code == 200

        # Delete the dancer
        resp = client.delete("/dancers/alice-smith")
        assert resp.status_code == 303
        assert resp.headers.get("location") == "/dancers"

        # Verify dancer is gone
        resp = client.get("/dancers/bob-jones")
        assert resp.status_code == 200
        resp = client.get("/dancers/alice-smith")
        assert resp.status_code == 404


class TestDancerListEditDetailFlow:
    """Integration tests for the full list -> detail/edit flow."""

    def test_full_flow_list_to_detail(self):
        """Test the complete flow: list page -> click name -> detail page."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        # Step 1: Get list page
        resp = client.get("/dancers")
        assert resp.status_code == 200
        assert "Alice Smith" in resp.text

        # Step 2: Click on dancer name (navigate to detail)
        resp = client.get("/dancers/alice-smith")
        assert resp.status_code == 200
        assert "Alice Smith" in resp.text
        assert "Dancer Detail" in resp.text

    def test_full_flow_list_to_edit(self):
        """Test the complete flow: list page -> click Edit -> edit form."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        # Step 1: Get list page
        resp = client.get("/dancers")
        assert resp.status_code == 200

        # Step 2: Click Edit link (navigate to edit form)
        resp = client.get("/dancers/alice-smith/edit")
        assert resp.status_code == 200
        assert 'value="Alice Smith"' in resp.text
        assert "Edit" in resp.text or "form" in resp.text.lower()

    def test_full_flow_detail_to_edit(self):
        """Test the complete flow: detail page -> click Edit Dancer button -> edit form."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        # Step 1: Get detail page
        resp = client.get("/dancers/alice-smith")
        assert resp.status_code == 200

        # Step 2: Click Edit Dancer button (navigate to edit form)
        resp = client.get("/dancers/alice-smith/edit")
        assert resp.status_code == 200
        assert 'value="Alice Smith"' in resp.text

    def test_detail_page_has_back_to_list_link(self):
        """Test that detail page has a Back to List link."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers/alice-smith")
        assert resp.status_code == 200
        assert 'href="/dancers"' in resp.text


class TestClassCountOnDancersList:
    """Tests ensuring the Classes column on the dancers list page shows accurate counts."""

    def _create_class(self, store, name):
        from dancemanager.models import make_class_id

        class_id = make_class_id(name)
        store.set(
            "classes",
            class_id,
            {
                "id": class_id,
                "name": name,
                "instructor_id": None,
                "team_ids": [],
                "dancer_ids": [],
            },
        )
        return class_id

    def _create_team(self, store, name):
        from dancemanager.models import make_team_id

        team_id = make_team_id(name)
        store.set(
            "teams",
            team_id,
            {"id": team_id, "name": name, "dancer_ids": []},
        )
        return team_id

    def test_class_count_zero_when_no_classes(self):
        """Dancer with no classes assigned shows count 0."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_dancers(store)
        client, _ = make_test_client(store)

        resp = client.get("/dancers")
        assert resp.status_code == 200
        # Both dancers have empty class_ids, so count should be 0
        assert ">0<" in resp.text or ">0</td>" in resp.text

    def test_class_count_one_single_assignment(self):
        """Dancer assigned to one class shows correct count."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        client, _ = make_test_client(store)

        # Create a class and assign dancer to it via web form
        self._create_class(store, "Ballet 101")
        resp = client.post(
            "/dancers",
            data={
                "name": "Carol White",
                "class_ids": "test-class-ballet-101",
                "team_id": "",
            },
        )
        assert resp.status_code == 303

        # Check list page shows count of 1
        resp = client.get("/dancers")
        assert resp.status_code == 200
        assert "Carol White" in resp.text
        assert ">1<" in resp.text or ">1</td>" in resp.text

    def test_class_count_multiple_assignments(self):
        """Dancer assigned to multiple classes shows accurate count."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        client, _ = make_test_client(store)

        class1_id = self._create_class(store, "Ballet 101")
        class2_id = self._create_class(store, "Jazz 201")
        class3_id = self._create_class(store, "Tap 302")

        # Assign dancer to all three classes via web form (only last one sticks due to single select)
        store.set(
            "dancers",
            "carol-white",
            {
                "id": "carol-white",
                "name": "Carol White",
                "class_ids": [class1_id, class2_id, class3_id],
                "team_id": None,
            },
        )

        resp = client.get("/dancers")
        assert resp.status_code == 200
        assert "Carol White" in resp.text
        assert ">3<" in resp.text or ">3</td>" in resp.text

    def test_class_update_syncs_dancer_class_ids_via_teams(self):
        """Adding a team to a class updates those dancers' class_ids."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        client, _ = make_test_client(store)

        # Create team with dancer
        team_id = self._create_team(store, "Red Team")
        store.set(
            "dancers",
            "alice-smith",
            {
                "id": "alice-smith",
                "name": "Alice Smith",
                "class_ids": [],
                "team_id": team_id,
            },
        )

        # Create class and assign the team to it
        class_id = self._create_class(store, "Advanced Ballet")
        resp = client.post(
            "/classes",
            data={"name": "Advanced Ballet", "instructor_id": "", "team_ids": team_id},
        )
        assert resp.status_code == 303

        # Verify dancer's class_ids was updated
        alice = store.get("dancers", "alice-smith")
        assert alice is not None
        assert class_id in alice.get("class_ids", [])

        # Verify list page shows correct count
        resp = client.get("/dancers")
        assert resp.status_code == 200
        assert ">1<" in resp.text or ">1</td>" in resp.text

    def test_dancer_update_removes_old_class_reference(self):
        """Removing a class from dancer updates both sides."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        client, _ = make_test_client(store)

        class_id = self._create_class(store, "Ballet 101")
        store.set(
            "dancers",
            "alice-smith",
            {
                "id": "alice-smith",
                "name": "Alice Smith",
                "class_ids": [class_id],
                "team_id": None,
            },
        )

        # Update dancer to remove the class
        resp = client.post(
            "/dancers/alice-smith",
            data={"name": "Alice Smith", "class_ids": "", "team_id": ""},
        )
        assert resp.status_code == 303

        alice = store.get("dancers", "alice-smith")
        assert alice is not None
        assert class_id not in alice.get("class_ids", [])

    def test_cli_style_dancer_has_valid_class_ids(self):
        """Dancer without class_ids field renders count 0 (not crash)."""
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        client, _ = make_test_client(store)

        # Simulate CLI-created dancer with no class_ids field at all
        store.set(
            "dancers",
            "bob-jones",
            {"id": "bob-jones", "name": "Bob Jones", "team_id": None},
        )

        resp = client.get("/dancers")
        assert resp.status_code == 200
        assert "Bob Jones" in resp.text
