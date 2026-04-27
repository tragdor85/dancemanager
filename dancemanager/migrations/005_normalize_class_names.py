"""Migration - normalize all existing class names to title case."""


def migrate_up(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM classes")
    for row in cursor.fetchall():
        class_id, old_name = row
        new_name = old_name.title()
        if new_name != old_name:
            cursor.execute(
                "UPDATE classes SET name = ? WHERE id = ?",
                (new_name, class_id),
            )
    conn.commit()


def migrate_down(conn):
    """Cannot reverse title case losslessly."""
    pass
