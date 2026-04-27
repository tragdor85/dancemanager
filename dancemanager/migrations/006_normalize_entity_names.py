"""Migration - normalize dancer, instructor, dance, and recital names to title case."""


def migrate_up(conn):
    cursor = conn.cursor()

    # Normalize dancers
    cursor.execute("SELECT id, name FROM dancers")
    for row in cursor.fetchall():
        dancer_id, old_name = row
        new_name = old_name.title()
        if new_name != old_name:
            cursor.execute(
                "UPDATE dancers SET name = ? WHERE id = ?",
                (new_name, dancer_id),
            )

    # Normalize instructors
    cursor.execute("SELECT id, name FROM instructors")
    for row in cursor.fetchall():
        inst_id, old_name = row
        new_name = old_name.title()
        if new_name != old_name:
            cursor.execute(
                "UPDATE instructors SET name = ? WHERE id = ?",
                (new_name, inst_id),
            )

    # Normalize dances
    cursor.execute("SELECT id, name FROM dances")
    for row in cursor.fetchall():
        dance_id, old_name = row
        new_name = old_name.title()
        if new_name != old_name:
            cursor.execute(
                "UPDATE dances SET name = ? WHERE id = ?",
                (new_name, dance_id),
            )

    # Normalize recitals
    cursor.execute("SELECT id, name FROM recitals")
    for row in cursor.fetchall():
        recital_id, old_name = row
        new_name = old_name.title()
        if new_name != old_name:
            cursor.execute(
                "UPDATE recitals SET name = ? WHERE id = ?",
                (new_name, recital_id),
            )

    conn.commit()


def migrate_down(conn):
    """Cannot reverse title case losslessly."""
    pass
