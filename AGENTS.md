# Dance Manager — Agent Instructions

## Project type
Python CLI + FastAPI web app for managing a dance studio (classes, teams, dancers, instructors, dances, recitals). No external database — SQLite with JSON-serialized list fields.

## Run commands
```bash
pip3.11 install -r requirements.txt   # or: python3 install_packages.py
python -m pytest tests/                # run all tests
python -m pytest tests/test_recital.py -v  # single test file
python -m dancemanager --help          # CLI help
```

Dev deps: `black` (format), `flake8` (lint), `pytest` (tests).

```bash
black .                          # format all Python files
flake8 dancemanager/ tests/      # lint check
```

## Architecture (what an agent needs to know)

**Entry points:**
- CLI: `dancemanager/__main__.py` → `cli.py` (`click.group()`) → subcommand modules in `dancemanager/*.py`
- Web: `python -m dancemanager serve` launches FastAPI via uvicorn on port 8000
- API routes live in `dancemanager/api/routes/`, web templates in `dancemanager/web/`

**Data layer:**
- `store.py` — SQLite persistence (`DataStore` class). All list fields (e.g. `dancer_ids`) are JSON-serialized strings in the DB.
- `models.py` — `DEFAULT_STORE_SCHEMA` dict defines collection names; ID generators (`make_dancer_id`, etc.) produce deterministic slugs from names (NOT UUIDs despite what IMPLEMENTATION.md says).
- Store singleton: `get_store()` / `set_default_store(store)` / `reset_default_store()` in `utils.py`. Tests inject a temp store via `set_default_store()`.

**Key modules:**
| Module | Purpose |
|--------|---------|
| `dancers.py` | Dancer CRUD (belongs to one team, multiple classes) |
| `teams.py` | Team CRUD → assigned to classes |
| `classes.py` | Class CRUD → has teams + individual dancers + instructor |
| `instructors.py` | Instructor CRUD → leads classes and dances |
| `dances.py` | Dance CRUD → mix of class members + individuals |
| `recital.py` | Recital management + greedy scheduling algorithm (4-dance buffer between a dancer's performances) |
| `utils.py` | CSV import/export, CLI helpers, store injection for tests |

**Data relationships:** Dancer→Team(1:1), Dancer→Classes(many), Team→Classes(many), Instructor→Classes/Dances(many), Dance→Dancers(many), Recital→Dances(many with position order).

## Testing quirks
- Tests use `setup_method` + `reset_default_store()` / `set_default_store(store)` pattern to isolate each test.
- CLI tests invoke commands via `CliRunner().invoke(cli_cmd, args)`.
- Store path is always passed as a temp file: `DataStore(path=str(tmp_path / "store.json"))`.
- No fixtures directory exists; all test data is created inline.

## Gotchas
- **IDs are deterministic slugs**, not UUIDs. `make_dancer_id("Alice Smith")` → `"alice-smith"`. Two modules with the same name collide.
- **Store uses SQLite, not JSON.** IMPLEMENTATION.md describes a JSON store — ignore it; the real code is in `store.py` (SQLite).
- **List fields are JSON strings** in the DB. Reading/writing them requires `json.loads()`/`json.dumps()`. The `DataStore.get()` method handles deserialization automatically.
- **Migrations:** On first init, if `data/store.json` exists it auto-migrates to SQLite. After that, only `.db` is used.
- **`data/` directory is gitignored.** Don't expect store files in the repo.

## Files that explain the system (read these first)
1. `IMPLEMENTATION.md` — high-level plan (outdated on data layer details but good for CLI commands and architecture overview)
2. `requirements.md` — feature requirements
3. `dancemanager/store.py` — actual persistence layer (authoritative over IMPLEMENTATION.md)
4. `dancemanager/cli.py` — CLI command registration
5. `tests/test_recital.py` — comprehensive test patterns for CLI + store injection

## Code style
- 4-space indentation, no tabs (enforced by global rules).
- Type hints on all function signatures.
- Functions should be small (aim for ~10 lines or less per function body).
- `snake_case` functions/variables, `PascalCase` classes.
