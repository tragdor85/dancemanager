"""Tests for base template structure, logo, and navigation.

Covers: Logo presence/position on all pages, navigation menu items,
template inheritance, and block definitions in base.html.
"""

from pathlib import Path

from tests.web_helpers import make_test_client, seed_data

# ──────────────────────────────────────────────────────────────────────
# 8. Base template and logo
# ──────────────────────────────────────────────────────────────────────


class TestBaseTemplateAndLogo:
    """Tests for the base.html template with logo above navigation."""

    def test_index_has_logo_image(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert resp.status_code == 200
        assert 'src="/static/images/gta-logo.png"' in resp.text

    def test_index_logo_has_alt_text(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert 'alt="GTA Dance Manager Logo"' in resp.text

    def test_index_logo_appears_before_nav(self):
        client, _ = make_test_client()
        resp = client.get("/")
        logo_pos = resp.text.find('src="/static/images/gta-logo.png"')
        nav_pos = resp.text.find("<nav>")
        assert logo_pos < nav_pos, "Logo should appear before the navigation menu"

    def test_index_has_navigation(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert "<nav>" in resp.text
        assert 'href="/dancers"' in resp.text
        assert 'href="/teams"' in resp.text
        assert 'href="/classes"' in resp.text
        assert 'href="/instructors"' in resp.text
        assert 'href="/dances"' in resp.text
        assert 'href="/recitals"' in resp.text

    def test_dancers_list_has_logo(self):
        tmp_dir = seed_data.__globals__.get("tempfile") or __import__("tempfile")
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers")
        assert resp.status_code == 200
        assert 'src="/static/images/gta-logo.png"' in resp.text

    def test_dancers_list_logo_before_nav(self):
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers")
        logo_pos = resp.text.find('src="/static/images/gta-logo.png"')
        nav_pos = resp.text.find("<nav>")
        assert logo_pos < nav_pos

    def test_teams_list_has_logo(self):
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/teams")
        assert resp.status_code == 200
        assert 'src="/static/images/gta-logo.png"' in resp.text

    def test_classes_list_has_logo(self):
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/classes")
        assert resp.status_code == 200
        assert 'src="/static/images/gta-logo.png"' in resp.text

    def test_instructors_list_has_logo(self):
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/instructors")
        assert resp.status_code == 200
        assert 'src="/static/images/gta-logo.png"' in resp.text

    def test_dances_list_has_logo(self):
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dances")
        assert resp.status_code == 200
        assert 'src="/static/images/gta-logo.png"' in resp.text

    def test_recitals_list_has_logo(self):
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals")
        assert resp.status_code == 200
        assert 'src="/static/images/gta-logo.png"' in resp.text

    def test_detail_pages_have_logo(self):
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        for url in [
            "/dancers/alice",
            "/teams/red",
            "/classes/ballet",
            "/instructors/jane",
            "/dances/waltz",
        ]:
            resp = client.get(url)
            assert resp.status_code == 200
            assert (
                'src="/static/images/gta-logo.png"' in resp.text
            ), f"Logo missing on {url}"

    def test_form_pages_have_logo(self):
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        for url in [
            "/dancers/new",
            "/teams/new",
            "/classes/new",
            "/instructors/new",
            "/dances/new",
        ]:
            resp = client.get(url)
            assert resp.status_code == 200
            assert (
                'src="/static/images/gta-logo.png"' in resp.text
            ), f"Logo missing on {url}"

    def test_recital_schedule_has_logo(self):
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/recitals/spring/schedule")
        assert resp.status_code == 200
        assert 'src="/static/images/gta-logo.png"' in resp.text

    def test_base_template_has_extra_css_block(self):
        base_path = (
            Path(__file__).parent.parent
            / "dancemanager"
            / "web"
            / "templates"
            / "base.html"
        )
        source = base_path.read_text()
        assert "{% block extra_css %}" in source

    def test_base_template_has_extra_js_block(self):
        base_path = (
            Path(__file__).parent.parent
            / "dancemanager"
            / "web"
            / "templates"
            / "base.html"
        )
        source = base_path.read_text()
        assert "{% block extra_js %}" in source

    def test_base_template_has_content_block(self):
        base_path = (
            Path(__file__).parent.parent
            / "dancemanager"
            / "web"
            / "templates"
            / "base.html"
        )
        source = base_path.read_text()
        assert "{% block content %}" in source

    def test_index_extends_base(self):
        index_path = (
            Path(__file__).parent.parent
            / "dancemanager"
            / "web"
            / "templates"
            / "index.html"
        )
        source = index_path.read_text()
        assert '{% extends "base.html" %}' in source

    def test_dancers_list_extends_base(self):
        list_path = (
            Path(__file__).parent.parent
            / "dancemanager"
            / "web"
            / "templates"
            / "dancers"
            / "list.html"
        )
        source = list_path.read_text()
        assert '{% extends "base.html" %}' in source

    def test_nav_is_in_base_not_repeated(self):
        """The nav should only appear once per page (in base.html)."""
        import tempfile
        from dancemanager.store import DataStore
        import os

        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, "test_store.json")
        store = DataStore(path=path)
        seed_data(store)
        client, _ = make_test_client(store)
        resp = client.get("/dancers")
        nav_count = resp.text.count("<nav>")
        assert nav_count == 1, f"Expected 1 <nav> tag, found {nav_count}"

    def test_logo_container_has_correct_classes(self):
        client, _ = make_test_client()
        resp = client.get("/")
        assert 'class="logo-container"' in resp.text
