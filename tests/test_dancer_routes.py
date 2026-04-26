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
        assert 'href="/dancers/alice-smith/edit" class="btn btn-primary">Edit Dancer' in resp.text

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
