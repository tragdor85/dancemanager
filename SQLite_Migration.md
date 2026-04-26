# SQLite Migration Plan

## Executive Summary

Migrate from JSON file storage to SQLite database for improved query performance, data integrity, and scalability.

---

## Session Progress

### Completed
- Analyzed `SQLite_Migration.md` target schema, data models, and planned API surface
- Reviewed active persistence layer (`dancemanager/store.py`) and alternative implementation (`store_sqlite.py`)
- Examined `tests/test_store.py` — imports from `dancemanager.store` but contains assertions expecting `.json` file paths/extensions
- Inspected migration scripts `migrations/001_initial_schema.py` and `migrations/002_populate_data.py` for schema definition and data population logic
- Checked git log confirming recent dance manager implementation commits

### In Progress
- Mapping discrepancies between test expectations (JSON file I/O, specific method signatures) and SQLite implementation details in `store.py`
- Identifying required updates to the migration plan to address test failures and alignment gaps

### Blocked
- None

---

## Current Architecture

### Data Store: `data/store.json`
- Single flat JSON file
- Nested collections: `dancers`, `teams`, `classes`, `instructors`, `dances`, `recitals`, `schedules`, `studios`
- Simple key-value access pattern
- No query capabilities, no indexing, no concurrent access

### Data Models

```python
Dancer = {
    "id": str,
    "name": str,
    "team_id": str | None,
    "class_ids": [str, ...],
    "notes": str
}

Team = {
    "id": str,
    "name": str,
    "dancer_ids": [str, ...],
    "notes": str
}

Class = {
    "id": str,
    "name": str,
    "team_ids": [str, ...],
    "dancer_ids": [str, ...],
    "instructor_id": str | None,
    "notes": str
}

Instructor = {
    "id": str,
    "name": str,
    "class_ids": [str, ...],
    "dance_ids": [str, ...],
    "notes": str
}

Dance = {
    "id": str,
    "name": str,
    "song_name": str,
    "instructor_id": str | None,
    "dancer_ids": [str, ...],
    "notes": str
}

Recital = {
    "id": str,
    "name": str,
    "performance_order": [
        {"dance_id": str, "position": int}
    ],
    "notes": str
}
```

---

## Target Architecture

### Data Store: `data/store.db`
- SQLite database with normalized tables
- Foreign key relationships
- Indexes for common queries
- Transaction support
- Concurrent access safety

### Database Schema

```sql
-- Dancers table
CREATE TABLE dancers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team_id TEXT,
    notes TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Teams table
CREATE TABLE teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT
);

-- Classes table
CREATE TABLE classes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    instructor_id TEXT,
    notes TEXT,
    FOREIGN KEY (instructor_id) REFERENCES instructors(id)
);

-- Instructors table
CREATE TABLE instructors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT
);

-- Dances table
CREATE TABLE dances (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    song_name TEXT NOT NULL,
    instructor_id TEXT,
    notes TEXT,
    FOREIGN KEY (instructor_id) REFERENCES instructors(id)
);

-- Recitals table
CREATE TABLE recitals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT
);

-- Dance assignments (many-to-many: dances <-> dancers)
CREATE TABLE dance_assignments (
    dance_id TEXT NOT NULL,
    dancer_id TEXT NOT NULL,
    PRIMARY KEY (dance_id, dancer_id),
    FOREIGN KEY (dance_id) REFERENCES dances(id),
    FOREIGN KEY (dancer_id) REFERENCES dancers(id)
);

-- Class assignments (many-to-many: classes <-> teams)
CREATE TABLE class_team_assignments (
    class_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    PRIMARY KEY (class_id, team_id),
    FOREIGN KEY (class_id) REFERENCES classes(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Class assignments (many-to-many: classes <-> dancers)
CREATE TABLE class_dancer_assignments (
    class_id TEXT NOT NULL,
    dancer_id TEXT NOT NULL,
    PRIMARY KEY (class_id, dancer_id),
    FOREIGN KEY (class_id) REFERENCES classes(id),
    FOREIGN KEY (dancer_id) REFERENCES dancers(id)
);

-- Recital performance order
CREATE TABLE recital_dances (
    recital_id TEXT NOT NULL,
    dance_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (recital_id, dance_id, position),
    FOREIGN KEY (recital_id) REFERENCES recitals(id),
    FOREIGN KEY (dance_id) REFERENCES dances(id)
);

-- Schedules table (future)
CREATE TABLE schedules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT
);

-- Studios table (future)
CREATE TABLE studios (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT
);

-- Indexes for performance
CREATE INDEX idx_dancers_team_id ON dancers(team_id);
CREATE INDEX idx_teams_dancer_ids ON teams(id);
CREATE INDEX idx_classes_instructor_id ON classes(instructor_id);
CREATE INDEX idx_dances_instructor_id ON dances(instructor_id);
CREATE INDEX idx_recital_dances_recital_id ON recital_dances(recital_id);
CREATE INDEX idx_class_team_assignments_class_id ON class_team_assignments(class_id);
CREATE INDEX idx_class_dancer_assignments_class_id ON class_dancer_assignments(class_id);
```

---

## Migration Strategy

### Phase 1: Preparation

1. **Create migration module** (`store.py` → `store_sqlite.py`)
   - New SQLite-based store implementation
   - Parallel to existing JSON store
   - No breaking changes to API

2. **Define migration schema**
   - Create migration scripts in `migrations/` directory
   - Version tracking table for schema evolution

3. **Set up test fixtures**
   - Export current JSON data to CSV
   - Create test database with sample data

### Phase 2: Schema Migration

1. **Create tables** (in order of foreign key dependencies):
   - `instructors` (no dependencies)
   - `dancers` (references teams)
   - `teams` (no dependencies)
   - `classes` (references instructors)
   - `dances` (references instructors)
   - `recitals` (no dependencies)
   - Join tables (many-to-many relationships)

2. **Migrate data** from JSON to SQLite:
   - Read entire JSON file
   - Insert records into new tables
   - Create join table entries
   - Verify data integrity

3. **Update version tracking**:
   - Record current schema version
   - Create migration history

### Phase 3: Application Migration

1. **Update store access layer**:
   - Replace `store.get()` with SQL queries
   - Replace `store.set()` with SQL inserts/updates
   - Maintain same API surface

2. **Migrate module-by-module**:
   - `dancers.py` → use SQL queries
   - `teams.py` → use SQL queries
   - `classes.py` → use SQL queries
   - `instructors.py` → use SQL queries
   - `dances.py` → use SQL queries
   - `recital.py` → use SQL queries

3. **Update relationship handling**:
   - `class_ids` arrays → JOIN queries
   - `dancer_ids` arrays → JOIN queries
   - `team_ids` arrays → JOIN queries

### Phase 4: Optimization

1. **Add indexes** for common queries:
   - Search by name
   - Filter by team/class
   - Performance-critical lookups

2. **Optimize queries**:
   - Use EXPLAIN to identify slow queries
   - Add composite indexes where needed
   - Consider query caching

3. **Add constraints**:
   - NOT NULL constraints
   - UNIQUE constraints
   - CHECK constraints for validation

### Phase 5: Validation & Rollback

1. **Verify data integrity**:
   - Compare record counts
   - Verify relationships intact
   - Test all CRUD operations

2. **Test concurrent access**:
   - Multiple simultaneous operations
   - Transaction isolation
   - Lock behavior

3. **Prepare rollback plan**:
   - Keep JSON store as backup
   - Document migration steps
   - Test rollback procedure

---

## Implementation Steps

### Step 1: Create SQLite Store Module

```python
# store_sqlite.py
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()
    
    def execute(self, sql: str, params: tuple = ()) -> None:
        self.conn.execute(sql, params)
        self.conn.commit()
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict]:
        cursor = self.conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    # ... CRUD operations ...
```

### Step 2: Create Migration Scripts

```python
# migrations/001_initial_schema.py
def migrate_up():
    create_tables()
    
def migrate_down():
    drop_tables()
```

### Step 3: Update Data Access

```python
# Before (JSON)
dancer = store.get("dancers", dancer_id)

# After (SQLite)
dancer = store.query("SELECT * FROM dancers WHERE id = ?", (dancer_id,))
```

### Step 4: Handle Relationships

```python
# Before (JSON)
dancer = store.get("dancers", dancer_id)
teams = [store.get("teams", tid) for tid in dancer["team_ids"]]

# After (SQLite)
dancer = store.query("SELECT * FROM dancers WHERE id = ?", (dancer_id,))
teams = store.query(
    "SELECT * FROM teams WHERE id IN (SELECT team_id FROM dancers WHERE id = ?)",
    (dancer_id,)
)
```

### Step 5: Add Query Capabilities

```python
# Search by name
results = store.query(
    "SELECT * FROM dancers WHERE name LIKE ?",
    (f"%search_term%",)
)

# Filter by team
results = store.query(
    "SELECT * FROM dancers WHERE team_id = ?",
    (team_id,)
)

# Complex queries
results = store.query("""
    SELECT d.name, t.name as team_name
    FROM dancers d
    JOIN teams t ON d.team_id = t.id
    WHERE d.name LIKE ?
""", (search_term,))
```

---

## Benefits of SQLite Migration

### Performance
- **Query speed**: O(log n) vs O(n) for lookups
- **Indexing**: Fast searches on common fields
- **No file locking**: SQLite handles concurrency

### Data Integrity
- **Foreign keys**: Referential integrity
- **Transactions**: Atomic operations
- **Constraints**: Validation at database level

### Scalability
- **100k+ records**: SQLite handles well
- **Concurrent reads**: Multiple readers supported
- **Backup**: Simple file copy

### Developer Experience
- **SQL queries**: Expressive data manipulation
- **Debugging**: `.dump` for inspection
- **Migrations**: Version-controlled schema

---

## Trade-offs

### Advantages
- ✅ Query capabilities (filter, search, aggregate)
- ✅ Indexing for performance
- ✅ Transaction support
- ✅ Foreign key constraints
- ✅ Concurrent access safety
- ✅ Better for growing datasets

### Disadvantages
- ❌ More complex setup
- ❌ Migration effort required
- ❌ Less portable than JSON
- ❌ Requires schema management
- ❌ No automatic backups (manual required)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss during migration | Low | High | Keep JSON backup, test rollback |
| Breaking changes to API | Low | High | Maintain API compatibility |
| Performance regression | Low | Medium | Benchmark before/after |
| Complex queries needed | Medium | Medium | Design schema for queries |

---

## Rollback Plan

If migration fails or causes issues:

1. **Keep JSON store active** as primary
2. **Use SQLite read-only** for testing
3. **Revert changes** to `store.py`
4. **Restore from backup** if needed

---

## Success Criteria

- [ ] All CRUD operations work correctly
- [ ] Query performance improved (measurable)
- [ ] No data loss during migration
- [ ] All tests pass
- [ ] Foreign key constraints enforced
- [ ] Indexes improve query speed
- [ ] Concurrent access works correctly

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|-------------|
| Preparation | 1 day | None |
| Schema Migration | 2 days | Preparation |
| Application Migration | 3 days | Schema Migration |
| Optimization | 1 day | Application Migration |
| Validation | 1 day | All previous phases |
| **Total** | **8 days** | - |

---

## Decision Matrix

| Metric | JSON | SQLite | Winner |
|--------|------|--------|---------|
| Setup complexity | None | Medium | JSON |
| Query performance | O(n) | O(log n) | SQLite |
| Data integrity | Manual | Automatic | SQLite |
| Scalability | <1k records | 100k+ records | SQLite |
| Concurrent access | No | Yes | SQLite |
| Backup strategy | Simple | Manual | JSON |
| Migration effort | N/A | High | JSON |

**Recommendation**: Migrate to SQLite when dataset grows beyond ~500 records or query performance becomes a bottleneck.
