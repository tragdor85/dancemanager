"""Migration - add team_ids column to dances table."""


def migrate_up(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE dances ADD COLUMN team_ids TEXT")
    except Exception:
        pass  # column may already exist from prior run
    cursor.execute("UPDATE dances SET team_ids = '[]' WHERE team_ids IS NULL")
    conn.commit()


def migrate_down(conn):
    """Reset team_ids to NULL (SQLite doesn't support DROP COLUMN easily)."""
    cursor = conn.cursor()
    cursor.execute("UPDATE dances SET team_ids = NULL")
    conn.commit()
