"""Migration - add location, capacity, schedule columns to studios table."""


def migrate_up(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE studios ADD COLUMN location TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE studios ADD COLUMN capacity INTEGER DEFAULT 20")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE studios ADD COLUMN schedule TEXT DEFAULT '[]'")
    except Exception:
        pass
    conn.commit()


def migrate_down(conn):
    """Reset new columns to NULL."""
    cursor = conn.cursor()
    cursor.execute("UPDATE studios SET location = NULL, capacity = 20, schedule = '[]'")
    conn.commit()
