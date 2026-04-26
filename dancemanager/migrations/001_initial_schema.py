"""Initial schema migration - create all tables with proper foreign key relationships."""


def migrate_up(conn):
    """Create all tables in dependency order."""
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # 1. Instructors (no dependencies)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS instructors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            notes TEXT
        )
    """
    )

    # 2. Teams (no dependencies)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS teams (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            notes TEXT
        )
    """
    )

    # 3. Dancers (references teams)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dancers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            team_id TEXT,
            notes TEXT,
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    """
    )

    # 4. Classes (references instructors)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS classes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            instructor_id TEXT,
            notes TEXT,
            FOREIGN KEY (instructor_id) REFERENCES instructors(id)
        )
    """
    )

    # 5. Dances (references instructors)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dances (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            song_name TEXT NOT NULL,
            instructor_id TEXT,
            notes TEXT,
            FOREIGN KEY (instructor_id) REFERENCES instructors(id)
        )
    """
    )

    # 6. Recitals (no dependencies)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recitals (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            notes TEXT
        )
    """
    )

    # 7. Join tables (many-to-many relationships)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dance_assignments (
            dance_id TEXT NOT NULL,
            dancer_id TEXT NOT NULL,
            PRIMARY KEY (dance_id, dancer_id),
            FOREIGN KEY (dance_id) REFERENCES dances(id),
            FOREIGN KEY (dancer_id) REFERENCES dancers(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS class_team_assignments (
            class_id TEXT NOT NULL,
            team_id TEXT NOT NULL,
            PRIMARY KEY (class_id, team_id),
            FOREIGN KEY (class_id) REFERENCES classes(id),
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS class_dancer_assignments (
            class_id TEXT NOT NULL,
            dancer_id TEXT NOT NULL,
            PRIMARY KEY (class_id, dancer_id),
            FOREIGN KEY (class_id) REFERENCES classes(id),
            FOREIGN KEY (dancer_id) REFERENCES dancers(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recital_dances (
            recital_id TEXT NOT NULL,
            dance_id TEXT NOT NULL,
            position INTEGER NOT NULL,
            PRIMARY KEY (recital_id, dance_id, position),
            FOREIGN KEY (recital_id) REFERENCES recitals(id),
            FOREIGN KEY (dance_id) REFERENCES dances(id)
        )
    """
    )

    # 8. Future tables (schedules, studios)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schedules (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            notes TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS studios (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            notes TEXT
        )
    """
    )

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dancers_team_id ON dancers(team_id)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_classes_instructor_id ON classes(instructor_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_dances_instructor_id ON dances(instructor_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_recital_dances_recital_id ON recital_dances(recital_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_class_team_assignments_class_id ON class_team_assignments(class_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_class_dancer_assignments_class_id ON class_dancer_assignments(class_id)"
    )

    conn.commit()


def migrate_down(conn):
    """Drop all tables in reverse dependency order."""
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = OFF")

    # Drop join tables first
    cursor.execute("DROP TABLE IF EXISTS recital_dances")
    cursor.execute("DROP TABLE IF EXISTS class_dancer_assignments")
    cursor.execute("DROP TABLE IF EXISTS class_team_assignments")
    cursor.execute("DROP TABLE IF EXISTS dance_assignments")

    # Then drop main tables
    cursor.execute("DROP TABLE IF EXISTS schedules")
    cursor.execute("DROP TABLE IF EXISTS studios")
    cursor.execute("DROP TABLE IF EXISTS recitals")
    cursor.execute("DROP TABLE IF EXISTS dances")
    cursor.execute("DROP TABLE IF EXISTS classes")
    cursor.execute("DROP TABLE IF EXISTS dancers")
    cursor.execute("DROP TABLE IF EXISTS teams")
    cursor.execute("DROP TABLE IF EXISTS instructors")

    conn.commit()
