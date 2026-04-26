# Dance Manager - UI Implementation Plan

## Overview

Add a web-based user interface to the existing Dance Manager CLI application. The UI will use **FastAPI** as the backend framework (replacing/supplementing the CLI entry point) with **HTMX** for dynamic page interactions, keeping the frontend simple and server-rendered. The existing JSON store and all business logic remain unchanged — the UI is a new presentation layer on top of the same data.

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend framework | **FastAPI** | Already noted as easy swap target in `requirements.txt`, supports async, auto-docs |
| Frontend approach | **Server-rendered templates (Jinja2) + HTMX** | Minimal JS, reuses existing server logic, simple deployment |
| Styling | **Pico.css** (CDN) | Zero-config, semantic, accessible, no build step |
| Static files | Local `static/` directory | Optional for future assets (logo, CSS overrides) |
| API | RESTful JSON API (in addition to HTML routes) | Enables future mobile/API consumers, same store underneath |
| Session | Stateless (no server-side sessions) | Store is JSON file; no auth needed for this use case |

---

## Project Structure (New)

```
dancemanager/
├── pyproject.toml
├── requirements.txt
├── README.md
├── data/
│     └── store.json
├── dancemanager/
│     ├── __init__.py
│     ├── __main__.py               # CLI entry point (unchanged)
│     ├── cli.py                     # CLI commands (unchanged)
│     ├── store.py                   # JSON persistence (unchanged)
│     ├── models.py                  # Core models (unchanged)
│     ├── dancers.py                 # Dancer CRUD (unchanged)
│     ├── classes.py                 # Class CRUD (unchanged)
│     ├── teams.py                   # Team CRUD (unchanged)
│     ├── instructors.py             # Instructor CRUD (unchanged)
│     ├── dances.py                  # Dance CRUD (unchanged)
│     ├── recital.py                 # Recital engine (unchanged)
│     ├── utils.py                   # CSV helpers (unchanged)
│     ├── api/                       # NEW: API layer
│     │     ├── __init__.py           # FastAPI app factory
│     │     ├── schemas.py            # Pydantic schemas for request/response models
│     │     └── routes/
│     │         ├── __init__.py
│     │         ├── dancers.py       # Dancer CRUD API
│     │         ├── teams.py         # Team CRUD API
│     │         ├── classes.py       # Class CRUD API
│     │         ├── instructors.py   # Instructor CRUD API
│     │         ├── dances.py        # Dance CRUD API
│     │         ├── recitals.py      # Recital CRUD + scheduling API
│     │         └── import_export.py # CSV import/export API
│     └── web/                       # NEW: Web UI
│           ├── __init__.py
│           ├── main.py               # HTML route handlers (views)
│           └── templates/
│               ├── base.html         # Base layout with Pico.css
│               ├── index.html        # Dashboard / home page
│               ├── components/
│               │   └── table.html    # Reusable table snippet (HTMX)
│               ├── dancers/
│               │   ├── list.html
│               │   ├── detail.html
│               │   └── form.html
│               ├── teams/
│               │   ├── list.html
│               │   ├── detail.html
│               │   └── form.html
│               ├── classes/
│               │   ├── list.html
│               │   ├── detail.html
│               │   └── form.html
│               ├── instructors/
│               │   ├── list.html
│               │   ├── detail.html
│               │   └── form.html
│               ├── dances/
│               │   ├── list.html
│               │   ├── detail.html
│               │   └── form.html
│               ├── recitals/
│               │   ├── list.html
│               │   ├── detail.html
│               │   └── form.html
│               ├── static/
│               │   └── style.css     # Optional overrides
│               └── auth.py           # Simple password guard (optional)
└── tests/
    └── test_api/                    # NEW: API integration tests
        ├── conftest.py
        ├── test_dancers_api.py
        ├── test_teams_api.py
        ├── test_classes_api.py
        ├── test_instructors_api.py
        ├── test_dances_api.py
        └── test_recitals_api.py
```

---

## Dependencies (Additions)

Add these to `requirements.txt` (keep existing deps):

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework, API + HTML routing |
| `uvicorn` | ASGI server to run the app |
| `jinja2` | HTML template engine |
| `python-multipart` | Form data parsing |
| `pydantic` | Request/response validation (FastAPI ships with it, but explicit) |

---

## Phase 1: Web Server Foundation

### 1.1 FastAPI Application Factory (`dancemanager/api/__init__.py`)

Create a `create_app()` function that:
- Initializes FastAPI with metadata (name, version from `__init__.py`)
- Mounts static files from `dancemanager/web/static/`
- Mounts HTML routes from `dancemanager/web/main.py`
- Mounts API routes from `dancemanager/api/routes/`
- Configures middleware (CORS not needed, simple request logging)

### 1.2 CLI-to-Web Bridge

Add a new CLI command to `cli.py` or `__main__.py`:
- `dancemanager serve` — launches the uvicorn server (runs on `localhost:8000` by default)
- Accept `--port` and `--host` options
- Should not conflict with existing CLI commands

### 1.3 HTML Base Template (`web/templates/base.html`)

- Uses Pico.css via CDN link
- Defines page structure: header with dance studio name, navigation sidebar, main content area
- Navigation items: Dashboard, Dancers, Teams, Classes, Instructors, Dances, Recitals
- HTMX loaded from CDN in `<head>`
- Responsive layout (sidebar collapses on mobile)

### 1.4 Dashboard Page (`web/templates/index.html`)

- Overview of all collections (counts of dancers, teams, classes, etc.)
- Quick actions: Add dancer, Add class, Create recital
- Recent activity summary
- Quick links to each management section

---

## Phase 2: Pydantic Schemas

### 2.1 API Schemas (`dancemanager/api/schemas.py`)

Define Pydantic models mirroring the JSON store structures:

```python
# Dancer
class DancerCreate(BaseModel):
    name: str
    team_id: str | None = None
    notes: str = ""

class DancerUpdate(BaseModel):
    name: str | None = None
    team_id: str | None = None
    notes: str | None = None

class DancerResponse(BaseModel):
    id: str
    name: str
    team_id: str | None
    class_ids: list[str]
    notes: str

# Team
class TeamCreate(BaseModel):
    name: str
    dancer_ids: list[str] = []

# Class
class ClassCreate(BaseModel):
    name: str
    instructor_id: str | None = None

# Dance
class DanceCreate(BaseModel):
    name: str
    song_name: str
    instructor_id: str | None = None

# Instructor
class InstructorCreate(BaseModel):
    name: str

# Recital
class RecitalCreate(BaseModel):
    name: str

class DanceSlot(BaseModel):
    dance_id: str
    position: int
```

---

## Phase 3: API Routes

Implement RESTful JSON API endpoints for every CRUD operation. Each route follows the pattern:
- `GET /api/<collection>/` — list all items
- `GET /api/<collection>/{id}/` — show single item
- `POST /api/<collection>/` — create
- `PUT /api/<collection>/{id}/` — update
- `DELETE /api/<collection>/{id}/` — remove
- `POST /api/<collection>/{id}/dancer/add` — add dancer to collection
- `POST /api/<collection>/{id}/dancer/remove` — remove dancer

### 3.1 Dancers API (`dancemanager/api/routes/dancers.py`)

Endpoints:
- `GET /api/dancers/` — list all dancers (JSON)
- `GET /api/dancers/search?q=...` — search dancers by name
- `POST /api/dancers/` — create dancer
- `GET /api/dancers/{id}/` — show dancer details
- `PUT /api/dancers/{id}/` — update dancer
- `DELETE /api/dancers/{id}/` — remove dancer
- `POST /api/dancers/{id}/assign-team` — assign dancer to team

### 3.2 Teams API (`dancemanager/api/routes/teams.py`)

Endpoints:
- `GET /api/teams/` — list all teams
- `POST /api/teams/` — create team
- `GET /api/teams/{id}/` — show team
- `DELETE /api/teams/{id}/` — remove team
- `POST /api/teams/{id}/dancers/add` — add dancer to team
- `POST /api/teams/{id}/dancers/remove` — remove dancer from team

### 3.3 Classes API (`dancemanager/api/routes/classes.py`)

Endpoints:
- `GET /api/classes/` — list all classes
- `POST /api/classes/` — create class
- `GET /api/classes/{id}/` — show class (with member counts)
- `DELETE /api/classes/{id}/` — remove class
- `POST /api/classes/{id}/teams/add` — assign team to class
- `POST /api/classes/{id}/dancers/add` — add dancer to class
- `POST /api/classes/{id}/dancers/remove` — remove dancer from class
- `POST /api/classes/{id}/instructor/assign` — assign instructor

### 3.4 Instructors API (`dancemanager/api/routes/instructors.py`)

Endpoints:
- `GET /api/instructors/` — list all instructors
- `POST /api/instructors/` — create instructor
- `GET /api/instructors/{id}/` — show instructor
- `DELETE /api/instructors/{id}/` — remove instructor
- `POST /api/instructors/{id}/classes/assign` — assign to class
- `POST /api/instructors/{id}/dances/assign` — assign to dance

### 3.5 Dances API (`dancemanager/api/routes/dances.py`)

Endpoints:
- `GET /api/dances/` — list all dances
- `POST /api/dances/` — create dance
- `GET /api/dances/{id}/` — show dance (with performer details)
- `DELETE /api/dances/{id}/` — remove dance
- `POST /api/dances/{id}/dancers/add` — add dancer
- `POST /api/dances/{id}/dancers/remove` — remove dancer

### 3.6 Recitals API (`dancemanager/api/routes/recitals.py`)

Endpoints:
- `GET /api/recitals/` — list all recitals
- `POST /api/recitals/` — create recital
- `GET /api/recitals/{id}/` — show recital
- `DELETE /api/recitals/{id}/` — remove recital
- `POST /api/recitals/{id}/dances/add` — add dance to recital
- `POST /api/recitals/{id}/dances/remove` — remove dance from recital
- `POST /api/recitals/{id}/reorder` — reorder dance positions
- `POST /api/recitals/{id}/generate-schedule` — auto-generate schedule (calls `greedy_schedule`)
- `GET /api/recitals/{id}/schedule` — display generated schedule with validation

### 3.7 Import/Export API (`dancemanager/api/routes/import_export.py`)

Endpoints:
- `POST /api/import/classes` — upload class CSV
- `POST /api/import/teams` — upload team CSV
- `GET /api/export/dancers` — download dancers CSV
- `GET /api/export/teams` — download teams CSV
- `GET /api/export/classes` — download classes CSV
- `GET /api/export/dances` — download dances CSV
- `GET /api/export/recital/{id}` — download recital CSV

---

## Phase 4: HTML Routes (Web UI Views)

### 4.1 Route Design Pattern

Each resource gets standard CRUD views:
- **List page** — table with sort, filter, search, add button
- **Detail page** — full information, edit/delete buttons
- **Form page** — create/edit form with HTMX-powered fields

HTMX attributes enable partial page updates:
- `hx-post` for create actions
- `hx-put` for edit actions
- `hx-delete` for remove actions
- `hx-swap="outerHTML"` for in-place updates
- `hx-target="#table-container"` for table refresh

### 4.2 Dancers Views

**`web/templates/dancers/list.html`**
- Search bar at top (filter by name)
- Table: Name, Team, Classes, Actions
- "Add Dancer" button
- Row links to detail page
- HTMX-powered: add dancer inline, remove with confirm dialog

**`web/templates/dancers/detail.html`**
- Dancer name, team assignment (with link to edit)
- Classes list (clickable links to class pages)
- Notes field (editable inline via HTMX)
- Actions: edit, remove

**`web/templates/dancers/form.html`**
- Form for add/edit: name, team (dropdown of existing teams), notes
- Submit via HTMX, redirect to detail page on success

### 4.3 Teams Views

**`web/templates/teams/list.html`**
- Table: Name, Dancers (count), Actions
- "Add Team" button

**`web/templates/teams/detail.html`**
- Team name, dancer list (clickable links)
- Add dancer to team (inline form with HTMX)
- Remove dancer (HTMX delete)

**`web/templates/teams/form.html`**
- Form for add/edit: name, dancer multi-select

### 4.4 Classes Views

**`web/templates/classes/list.html`**
- Table: Name, Teams, Dancers (count), Instructor, Actions
- "Add Class" button

**`web/templates/classes/detail.html`**
- Class name, team assignments (clickable links)
- Dancer list (individual members)
- Instructor assignment (dropdown)
- Actions: edit, remove

**`web/templates/classes/form.html`**
- Form: name, instructor (dropdown), team assignment, dancer add

### 4.5 Instructors Views

**`web/templates/instructors/list.html`**
- Table: Name, Classes, Dances

**`web/templates/instructors/detail.html`**
- Instructor name, class list, dance list
- Assign class / assign dance (inline forms)

**`web/templates/instructors/form.html`**
- Simple form: name

### 4.6 Dances Views

**`web/templates/dances/list.html`**
- Table: Name, Song, Instructor, Dancers (count)

**`web/templates/dances/detail.html`**
- Dance name, song name, instructor
- Dancer list (add/remove inline)
- Link to recitals this dance appears in

**`web/templates/dances/form.html`**
- Form: name, song name, instructor (dropdown)

### 4.7 Recitals Views

**`web/templates/recitals/list.html`**
- Table: Name, Dance Count, Actions
- "Create Recital" button

**`web/templates/recitals/detail.html`**
- Recital name, performance order table
- Add dance to recital (dropdown search + HTMX add)
- Remove dance (HTMX delete)
- Reorder dances (drag-and-drop with HTMX reordering)
- "Generate Schedule" button

**`web/templates/recitals/schedule.html`**
- Full performance schedule view
- Table: Position, Dance, Song, Performers, Buffer Notes
- Validation report section
- Print-friendly layout
- Download as CSV

---

## Phase 5: UI Polish & UX

### 5.1 Shared Components

**`web/templates/components/table.html`**
- Reusable HTMX table component
- Accepts headers and rows as parameters
- Built-in sort-by-column
- Responsive on mobile

### 5.2 Navigation & Layout

- Consistent sidebar across all pages
- Active page highlighted
- Mobile-responsive (sidebar becomes collapsible hamburger menu)
- Breadcrumbs on detail pages

### 5.3 Confirmations & Feedback

- HTMX confirm dialogs for destructive actions (remove)
- Toast-style success/error messages after actions
- Loading indicators for scheduling operations

### 5.4 Search & Filter

- Search bars on all list pages (client-side filtering via HTMX `hx-trigger` on `input`)
- Filter by team/class on dancer list
- Filter by instructor on dance list

### 5.5 Empty States

- Friendly empty states for all collections (e.g., "No dancers yet. Import from CSV or add one.")
- Links to import or add action from empty states

---

## Phase 6: Integration with Existing Code

### 6.1 Reuse Existing Modules

The web layer **does not duplicate** any business logic:
- All CRUD operations call the existing module functions (`dancemanager.dancers.py`, `dancemanager.teams.py`, etc.)
- The store is shared — `get_store()` works identically
- The scheduling algorithm in `recital.py` is reused directly

### 6.2 API Wrapper Pattern

Create thin wrapper functions in `api/routes/` that:
- Call into `dancemanager.<module>` for data operations
- Return JSON responses (Pydantic models) or rendered templates (HTML)
- Handle errors consistently (404, 400, 500)

### 6.3 Dual Entry Points

- `python -m dancemanager` — CLI (unchanged)
- `dancemanager serve` — web server (new)
- Both share the same `data/store.json`

---

## Implementation Order

| Step | Component | Description |
|------|-----------|-------------|
| 1 | `requirements.txt` update + `pyproject.toml` | Add FastAPI, uvicorn, Jinja2, python-multipart |
| 2 | `dancemanager/api/__init__.py` | FastAPI app factory with static file mounting |
| 3 | `dancemanager/api/schemas.py` | Pydantic models for all resources |
| 4 | `dancemanager/web/templates/base.html` | Base layout with Pico.css + HTMX |
| 5 | `dancemanager/web/main.py` — index route | Dashboard with collection counts |
| 6 | `dancemanager/api/routes/dancers.py` | Dancer CRUD API endpoints |
| 7 | `dancemanager/web/templates/dancers/` | Dancer list, detail, form views |
| 8 | `dancemanager/api/routes/teams.py` | Team CRUD API endpoints |
| 9 | `dancemanager/web/templates/teams/` | Team list, detail, form views |
| 10 | `dancemanager/api/routes/classes.py` | Class CRUD API endpoints |
| 11 | `dancemanager/web/templates/classes/` | Class list, detail, form views |
| 12 | `dancemanager/api/routes/instructors.py` | Instructor CRUD API endpoints |
| 13 | `dancemanager/web/templates/instructors/` | Instructor list, detail, form views |
| 14 | `dancemanager/api/routes/dances.py` | Dance CRUD API endpoints |
| 15 | `dancemanager/web/templates/dances/` | Dance list, detail, form views |
| 16 | `dancemanager/api/routes/recitals.py` | Recital CRUD + scheduling endpoints |
| 17 | `dancemanager/web/templates/recitals/` | Recital list, detail, schedule views |
| 18 | `dancemanager/api/routes/import_export.py` | CSV import/export endpoints |
| 19 | `dancemanager/cli.py` / `__main__.py` | Add `serve` command for web server |
| 20 | `tests/test_api/` | API integration tests for all endpoints |
| 21 | UI polish | Navigation, empty states, confirmations, mobile responsiveness |
| 22 | End-to-end testing | Full workflow: import → manage → schedule recital (via web) |

---

## Testing Strategy

- **API tests** in `tests/test_api/` using `FastAPI.testclient`
  - CRUD for each resource (positive + negative cases)
  - Schedule generation tests (reuse `greedy_schedule` logic)
  - Import/export tests (valid + malformed CSV)
- **Template rendering tests** — ensure pages render without errors
- **Integration tests** — full workflow via web:
  1. Create dancers via web UI
  2. Create classes, assign dancers
  3. Create dances, add dancers
  4. Create recital, add dances
  5. Generate schedule
  6. Export as CSV
- Target: **90%+ test coverage** on web layer (same as CLI)

---

## Key HTMX Patterns

| Pattern | HTMX Syntax |
|---------|-------------|
| Create item inline | `<form hx-post="/api/dancers/" hx-target="#message">` |
| Refresh list after add | `<form hx-post="..." hx-target="#dancers-table" hx-swap="outerHTML">` |
| Delete with confirm | `<button hx-delete="/api/dancers/{id}/" hx-confirm="Remove this dancer?">` |
| Search filter | `<input hx-get="/api/dancers/" hx-trigger="input changed delay:300ms" hx-target="#dancers-table">` |
| Loading indicator | `<span hx-indicator="htmx-indicator"></span>` |
| Reorder recital dances | `<select hx-post="/api/recitals/{id}/reorder" hx-target="#schedule" hx-swap="outerHTML">` |

---

## Data Flow (Web)

```
Browser ──HTMX──► FastAPI Routes ──► Existing Modules (dancers.py, etc.)
    ▲                     │                         │
     │                    ▼                        ▼
     │              JSON API Response          JSON Store (store.json)
     │                     │                         ▲
     └────────────────── HTMX Swap ────────────────┘
```

The web UI is a **thin layer** on top of existing code. The store, models, and business logic are reused verbatim.

---

## Current Implementation Status

### ✅ Completed

#### Phase 1: Web Server Foundation
- [x] `dancemanager/api/__init__.py` - FastAPI application factory
- [x] `dancemanager/api/schemas.py` - Pydantic models for all resources
- [x] `dancemanager/web/main.py` - HTML route handlers for all CRUD views
- [x] `dancemanager/web/templates/base.html` - Base layout with Pico.css + HTMX
- [x] `dancemanager/web/templates/dancers/` - List, detail, form views
- [x] `dancemanager/web/templates/teams/` - List, detail, form views
- [x] `dancemanager/web/templates/classes/` - List, detail, form views
- [x] `dancemanager/web/templates/instructors/` - List, detail, form views
- [x] `dancemanager/web/templates/dances/` - List, detail, form views
- [x] `dancemanager/web/templates/recitals/` - List, detail, form views

#### Phase 3: API Routes (All Endpoints)
- [x] `dancemanager/api/routes/dancers.py` - Full CRUD API
- [x] `dancemanager/api/routes/teams.py` - Full CRUD API
- [x] `dancemanager/api/routes/classes.py` - Full CRUD API
- [x] `dancemanager/api/routes/instructors.py` - Full CRUD API
- [x] `dancemanager/api/routes/dances.py` - Full CRUD API
- [x] `dancemanager/api/routes/recitals.py` - Full CRUD + scheduling API
- [x] `dancemanager/api/routes/import_export.py` - CSV import/export API

#### Phase 6: Integration
- [x] `dancemanager/api/__init__.py` properly mounts all routes
- [x] All API routes properly integrated with existing store modules

---

### ✅ Completed

#### Phase 2: Dependencies
- [x] Updated `requirements.txt` with FastAPI, uvicorn, jinja2, python-multipart
- [x] All dependencies installed and working

#### Phase 4: HTML Routes (All Views)
- [x] `web/templates/recitals/form.html` - Create form with HTMX-powered fields
- [x] `web/templates/recitals/schedule.html` - Full performance schedule view with:
  - Position, Dance, Song, Performers, Buffer Notes columns
  - Validation report section
  - Print-friendly layout using @media print
  - Download as CSV functionality
  - HTMX loading indicator for scheduling operations

#### Phase 5: UI Polish
- [x] Shared components table (`web/templates/components/table.html`) - Reusable HTMX table with sort functionality
- [x] Mobile responsive improvements - Sidebar becomes collapsible hamburger menu
- [x] HTMX confirm dialogs - Added to all destructive actions across all resource pages
- [x] Loading indicators - Added for scheduling operations
- [x] Search/filter functionality - All list pages have search with HTMX `hx-trigger="input changed delay:300ms"`
- [x] Custom styling (`web/templates/static/style.css`) - Custom overrides including enhanced tables, loading spinners, toast notifications

### 🚧 In Progress

#### Phase 6: CLI Integration
- [ ] Add `serve` command to CLI (already exists in cli.py)

#### Phase 4: HTML Routes
- [ ] `web/templates/recitals/form.html` - Missing recital create form
- [ ] `web/templates/recitals/schedule.html` - Missing schedule view

#### Phase 5: UI Polish
- [ ] Shared components table
- [ ] Mobile responsive improvements
- [ ] HTMX confirm dialogs
- [ ] Loading indicators

#### Phase 6: CLI Integration
- [ ] Add `serve` command to CLI

---

## Notes

- **No database migration** needed — still JSON file-based
- **No auth** — the app is local-use only, no login required
- **No file upload UI** — CSV import is done via the API directly (can add a simple file upload form later)
- **Responsive design** — Pico.css handles most of this; minimal custom CSS needed
- **Print layout** — recital schedule page uses a `@media print` stylesheet for printing the performance order
- **All existing CLI commands continue to work** — store is shared, so CLI and web can coexist
