# Dance Manager - Implementation Plan

## Overview

A Python CLI application for managing a dance studio's classes, teams, dancers, instructors, dances, and recital scheduling. Built on a JSON data store with an extensible architecture ready for future UI and scheduling features.

---

## Project Structure

```
dancemanager/
├── pyproject.toml
├── requirements.txt
├── README.md
├── data/
│   └── store.json              # Single JSON data store
├── dancemanager/
│   ├── __init__.py
│   ├── __main__.py              # Entry point: python -m dancemanager
│   ├── cli.py                    # CLI with click framework
│   ├── store.py                 # JSON data persistence layer
│   ├── models.py                # Core data models / schemas
│   ├── dancers.py               # Dancer CRUD
│   ├── classes.py               # Dance class management
│   ├── teams.py                 # Team management
│   ├── dances.py                # Dance management
│   ├── instructors.py           # Instructor management
│   ├── recital.py               # Recital scheduling engine
│   └── utils.py                 # CSV import/export helpers
```

---

## Phase 1: Foundation

### 1.1 Project Setup

- `pyproject.toml` with Python 3.11+, project metadata, dependencies
- `requirements.txt` listing: `click` (CLI framework, more powerful than argparse), `pytest` (testing)
- `dancemanager/__main__.py` entry point wired to `click.group()`
- Initialize git repo with `git@github.com:tragdor85/dancemanager.git`

### 1.2 Data Store (`store.py`)

Single JSON file (`data/store.json`) as the data store. Simple key-value structure:

```json
{
    "version": "1.0.0",
    "dancers": { ... },
    "teams": { ... },
    "classes": { ... },
    "instructors": { ... },
    "dances": { ... },
    "recitals": { ... },
    "schedules": { ... },
    "studios": { ... }
}
```

- `version` — Schema version string. All migrations check and update this.
- `load()` — reads JSON into dict, checks version compatibility
- `save()` — writes dict back to JSON, creates `.bak` backup of previous file first
- `get(collection, key)` / `set(collection, key, value)` — typed getters/setters
- `migrate(target_version)` — Applies schema migrations when version changes
- All IDs are strings (UUIDs or auto-incrementing). All lists/dicts are deep-copied on read/write to avoid mutation issues.
- **Backup**: On every `save()`, the previous `store.json` is copied to `store.json.bak` before writing. Prevents data loss on crashes or bad migrations.

### 1.3 Data Models (`models.py`)

Core schema definitions. These are the single source of truth for data structure:

**Dancer**
```python
{
    "id": str,
    "name": str,
    "team_id": str | None,        # Optional: assigned to one team
    "class_ids": [str, ...],      # Classes this dancer is in
    "notes": str                  # Flexible notes field
}
```

**Team**
```python
{
    "id": str,
    "name": str,
    "dancer_ids": [str, ...],     # Dancers on this team
    "notes": str
}
```

**Class**
```python
{
    "id": str,
    "name": str,
    "team_ids": [str, ...],       # Teams assigned to this class
    "dancer_ids": [str, ...],     # Individual dancers in this class
    "instructor_id": str | None,  # Lead instructor
    "notes": str
}
```

**Instructor**
```python
{
    "id": str,
    "name": str,
    "class_ids": [str, ...],      # Classes this instructor leads
    "dance_ids": [str, ...],      # Dances this instructor leads
    "notes": str
}
```

**Dance**
```python
{
    "id": str,
    "name": str,                  # Dance name/title
    "song_name": str,
    "instructor_id": str | None,  # Optional instructor for this dance
    "dancer_ids": [str, ...],     # Mix of class members and individuals
    "notes": str
}
```

**Recital**
```python
{
    "id": str,
    "name": str,
    "performance_order": [        # Ordered list of dance slots
        {
            "dance_id": str,
            "position": int       # Position in performance order
        },
        ...
    ],
    "notes": str
}
```

**Extensibility placeholder** (empty dict, ready for future use):
```python
{
    "schedules": { ... },         # Future: class/studio/time schedules
    "studios": { ... }            # Future: studio definitions
}
```

---

## Phase 2: Core CRUD Operations

### 2.1 CSV Import/Export (`utils.py`)

Shared helpers for all modules. Loaded early in development since everything depends on it.

- `csv_import_classes(filepath)` — Parse class CSV: column header = class name, each row = student. Creates classes and dancers in one pass.
- `csv_import_teams(filepath)` — Parse team CSV: column header = team name, each row = dancer. Creates teams and dancers in one pass.
- `csv_export_dancers(filepath)` — Export dancer data as CSV
- `csv_export_teams(filepath)` — Export team data as CSV
- `csv_export_classes(filepath)` — Export class data as CSV
- `csv_export_dances(filepath)` — Export dance data as CSV
- `csv_export_recital(filepath, recital_id)` — Export recital schedule as CSV

**Import validation rules:**
- Skip blank rows
- Deduplicate dancers by name (warn on duplicates)
- Handle duplicate class/team names (merge into existing or warn)
- Report malformed rows (non-string values, empty headers)
- Return import summary (created, skipped, errors)

### 2.2 Dancers (`dancers.py`)

Commands:
- `dancer add <name> [--team <team_name>]` — Add dancer, optionally assign to team
- `dancer list` — List all dancers
- `dancer show <dancer_id>` — Show dancer details (team, classes)
- `dancer remove <dancer_id>` — Remove dancer (also removes from related classes/dances)
- `dancer export` — Export dancers to CSV

### 2.3 Teams (`teams.py`)

Commands:
- `team add <name> [--dancer <dancer_name>...]` — Create team with optional dancers
- `team list` — List all teams
- `team show <team_id>` — Show team details
- `team remove <team_id>` — Remove team
- `team assign <team_id> <class_name>` — Assign team to a class
- `team dancer add <team_id> <dancer_id>` — Add dancer to team
- `team dancer remove <team_id> <dancer_id>` — Remove dancer from team
- `team export` — Export teams to CSV

### 2.4 Classes (`classes.py`)

Commands:
- `class add <name> [--instructor <instructor_name>]` — Create class
- `class list` — List all classes
- `class show <class_id>` — Show class details (members, teams, instructor)
- `class remove <class_id>` — Remove class
- `class team add <class_id> <team_id>` — Assign team to class
- `class dancer add <class_id> <dancer_id>` — Add individual dancer to class
- `class dancer remove <class_id> <dancer_id>` — Remove dancer from class
- `class instructor assign <class_id> <instructor_id>` — Assign instructor to class
- `class export` — Export classes to CSV

### 2.5 Dances (`dances.py`)

Commands:
- `dance add <name> <song_name> [--instructor <instructor_name>]` — Create dance with song
- `dance list` — List all dances
- `dance show <dance_id>` — Show dance details (dancers, song, instructor)
- `dance remove <dance_id>` — Remove dance
- `dance dancer add <dance_id> <dancer_id>` — Add dancer to dance
- `dance dancer remove <dance_id> <dancer_id>` — Remove dancer from dance
- `dance export` — Export dances to CSV

Dances support a flexible mix of dancers from classes and individuals.

### 2.6 Instructors (`instructors.py`)

Commands:
- `instructor add <name>` — Add instructor
- `instructor list` — List all instructors
- `instructor show <instructor_id>` — Show instructor details
- `instructor remove <instructor_id>` — Remove instructor
- `instructor assign-class <instructor_id> <class_id>` — Assign instructor to class
- `instructor assign-dance <instructor_id> <dance_id>` — Assign instructor to dance

---

## Phase 3: Recital Scheduling Engine

### 3.1 Recital Management (`recital.py`)

Commands:
- `recital add <name>` — Create a new recital
- `recital list` — List all recitals
- `recital show <recital_id>` — Show recital details
- `recital remove <recital_id>` — Remove a recital
- `recital add-dance <recital_id> <dance_id>` — Add dance to recital
- `recital reorder <recital_id> <position> <dance_id>` — Reorder dance in schedule
- `recital generate-schedule <recital_id>` — Auto-generate optimal performance order

### 3.2 Schedule Generator

The core scheduling algorithm:

1. **Input**: A list of dances with their assigned dancers (from the recital)
2. **Build dancer availability map**: For each dancer, find all dances they perform in
3. **Graph constraint problem**:
   - Each dance is a node
   - Constraint: Between any two consecutive performances by the same dancer, there must be at least 4 other dances
4. **Greedy scheduling algorithm**:
   - Start with an empty schedule
   - For each position, score each remaining dance by how many dancers are "ready" (4+ dances since last performance)
   - Pick the dance that allows the most dancers to be ready
   - Repeat until all dances scheduled
5. **Backtracking fallback**: If greedy fails, backtrack and try alternative orderings
6. **Output**: Ordered list of dances with position numbers

**Output format** (text):
```
Recital: Spring Showcase

Position  Dance Name       Song                  Performers
1         Waltz Dreams     Moonlight Waltz       Alice, Bob, Carol
2         Hip Hop Flash    Beat Drop             Alice, David
3         Ballet Grace     Swan Lake             Bob, Carol
4         Jazz Power       Counting Sheep        Alice, Eve
5         Contemporary     River Flows           Bob, Frank
6         Hip Hop Flash    Beat Drop             Alice, David    (Alice: 4th dance since 1st)
```

7. **Validation report**: After generating, print a validation showing each dancer's performance times with "4 dance buffer" check passing/failing

---

## Phase 4: Extensibility & Polish

### 4.1 Flexible Data Structures

- The JSON store uses a flat collection pattern (dancers, teams, classes, etc.) making it trivial to add new collections like `schedules` and `studios`
- `store.py` already has generic `get_collection()` / `set_collection()` methods for new data types
- Models in `models.py` are simple dicts — no ORM lock-in, easy to extend

### 4.2 Future-Ready Stubs

- Empty `schedules` and `studios` collections in the data store
- `cli.py` has a `@cli.group()` pattern making it easy to add new subcommand groups
- `store.py` provides `get_all(collection)` and `iterate(collection)` for future query-heavy features

### 4.3 CLI Polish

- All commands return human-readable text output (formatted tables for lists)
- CSV export for all data (mirrors import format)
- Error handling with clear messages (e.g., "Dancer not found", "Dance conflict: insufficient buffer for recital schedule")
- Help text (`--help`) on all subcommands
- ID display in all list outputs for easy reference

---

## Data Flow Diagram

```
CSV Import ──► Store ──► CRUD Operations ──► Recital Engine ──► Schedule Output
                        ▲
                        │
              Dancer ↔ Team ↔ Class ↔ Dance
                        │
                 Instructor
```

Key relationships:
- **Dancer** → belongs to one **Team** (optional)
- **Dancer** → belongs to multiple **Classes**
- **Team** → assigned to multiple **Classes**
- **Instructor** → leads multiple **Classes** and **Dances**
- **Dance** → includes **Class** members + **Individual** dancers
- **Recital** → orders **Dances** with scheduling constraints

---

## Implementation Order

| Step | Component | Description |
|------|-----------|-------------|
| 1 | `pyproject.toml` + repo setup | Project scaffold, dependencies, git init |
| 2 | `store.py` + `models.py` | JSON persistence layer and data model schemas |
| 3 | `utils.py` | CSV import/export helpers (depends on store + models) |
| 4 | `cli.py` | Click CLI group with subcommand registration |
| 5 | `dancers.py` | Dancer CRUD (foundation for everything else) |
| 6 | `teams.py` | Team CRUD, team↔class assignment |
| 7 | `classes.py` | Class CRUD, team/dancer/instructor assignment |
| 8 | `instructors.py` | Instructor CRUD, assign to classes/dances |
| 9 | `dances.py` | Dance CRUD, dancer assignment |
| 10 | `recital.py` | Recital management + scheduling engine |
| 11 | `store.py` v2.0 | Add backup on save, `version` field, migration logic |
| 12 | Integration testing | End-to-end recital scheduling test |

---

## Testing Strategy

- Minimum **90% test coverage** enforced via `pytest-cov` — all code must meet or exceed this threshold to prevent breaking changes during development
- **Test-Driven Development (TDD)** is the preferred workflow: write failing tests first, then implement the code to make them pass
- `tests/` directory with `pytest`
- `pytest-cov` for coverage reporting
- Unit tests for `store.py` (load/save consistency)
- Unit tests for `recital.py` (schedule generator edge cases)
- Integration tests for full recital workflow (import → assign → schedule)
- Test fixtures in `tests/fixtures/` with sample CSV data

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_store.py
├── test_dancers.py
├── test_teams.py
├── test_classes.py
├── test_instructors.py
├── test_dances.py
├── test_recital.py          # Schedule generator tests
└── fixtures/
    ├── classes.csv
    ├── teams.csv
    └── dancers.csv
```

---

## Dependencies

Minimal. Only external deps:

| Package | Purpose |
|---------|---------|
| `click` | CLI framework (easy to later swap for FastAPI/Flask) |
| `pytest` | Testing framework |
| `pytest-cov` | Coverage reporting (enforces 90% minimum) |

No database, no web framework. Pure Python with JSON storage.

---

## Notes

- **IDs**: Auto-generated using `uuid.uuid4()` for simplicity and collision safety
- **Deep copy**: All reads from the JSON store return deep copies to prevent in-memory mutation leaking to the file
- **Validation**: On `save()`, basic schema validation runs to catch corruption early
- **Extensibility**: The flat collection model means adding `schedules` (class/studio/time) or `studios` is a one-line change to the store init and a new module

---

## Coding Standards

- Follow **Uncle Bob's Clean Code** principles to keep code readable and self-documenting:
     - **Functions should be small** — aim for 4-8 lines per function. If a function exceeds one screen, it likely needs to be broken up
     - **Functions should do one thing** — a function's name should describe exactly what it does; if explaining the function requires an "and", it does more than one thing
     - **Use meaningful names** — variable names should reveal intent (`num_dancers` not `n`), function names should be verbs (`find_available_dancers` not `get`)
     - **Format code for readability** — horizontal spacing around operators, vertical spacing around concepts, consistent indentation (4 spaces)
     - **Use the standard naming conventions** — `snake_case` for functions and variables, `PascalCase` for classes, `_private` for internal members
     - **Comments should explain *why*, not *what*** — the code itself should be clear enough that comments are only needed for context, not restating the obvious
     - **Handle errors early** — use guard clauses and early returns to keep nesting shallow
- All Python files formatted with `black`, linted with `ruff` and `flake8`
- All Python files indented with 4 spaces consistently across every file — no tabs, no mixed indentation
- Type hints on all function signatures for clarity and static analysis
