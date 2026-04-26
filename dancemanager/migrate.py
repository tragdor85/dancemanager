"""Migration runner - discovers and executes numbered migration scripts."""

import importlib.util
from pathlib import Path


def run_migrations(conn):
    """Run all pending migrations from the migrations directory.

    Migrations are Python files named like 001_xxx.py, 002_yyy.py etc.
    Each must define migrate_up(conn) and optionally migrate_down(conn).
    """
    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        return

    migration_files = sorted(
        f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"
    )

    cursor = conn.cursor()
    # Track which migrations have been applied via a metadata table
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS _migrations (
            name TEXT PRIMARY KEY,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    )

    for migration_file in migration_files:
        module_name = migration_file.stem  # e.g. "001_initial_schema"

        # Check if already applied
        cursor.execute(
            "SELECT COUNT(*) FROM _migrations WHERE name = ?", (module_name,)
        )
        if cursor.fetchone()[0] > 0:
            continue

        spec = importlib.util.spec_from_file_location(module_name, migration_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Run the migration
        module.migrate_up(conn)

        # Mark as applied
        cursor.execute("INSERT INTO _migrations (name) VALUES (?)", (module_name,))
        conn.commit()
