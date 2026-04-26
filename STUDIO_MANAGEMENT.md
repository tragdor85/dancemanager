# Studio Management - Implementation Plan

## Overview

Add comprehensive studio management to Dance Manager, enabling:
- Multiple studios (Studio 1, Studio 2, Studio 3, etc.)
- Per-studio scheduling with date/time slots
- Class reservations (recurring)
- Individual dancer/instructor reservations (one-time)
- Conflict detection to prevent double-booking

---

## Data Model

### Studio Schema

```python
{
    "id": str,                          # e.g., "studio-1"
    "name": str,                        # e.g., "Studio 1"
    "location": str,                    # e.g., "123 Main St, Room A"
    "capacity": int,                    # Max concurrent dancers
    "equipment": [str, ...],            # ["mirrors", "barre", "sound_system"]
    "schedule": [                        # List of time slots
        {
            "date": str,                # "2024-01-15"
            "start_time": str,          # "18:00"
            "end_time": str,            # "19:30"
            "duration_minutes": int,    # 90
            "reserved_by": str | None, # Class ID or dancer/instructor ID
            "reservation_type": str     # "class" | "individual"
        },
        ...
    ],
    "notes": str
}
```

---

## Architecture

### 1. Store Integration

Add `studios` collection to `DEFAULT_STORE_SCHEMA` in `dancemanager/models.py`:

```python
DEFAULT_STORE_SCHEMA = {
    "version": "1.0.0",
    "dancers": {},
    "teams": {},
    "classes": {},
    "instructors": {},
    "dances": {},
    "recitals": {},
    "schedules": {},
    "studios": {},  # NEW
}
```

---

### 2. Studio Module (`dancemanager/studios.py`)

#### Core Functions

```python
def add_studio(name: str, location: str, capacity: int = 20) -> str:
    """Create a new studio."""
    studio_id = f"studio-{name.lower().replace(' ', '-')}"
    studio = {
        "id": studio_id,
        "name": name,
        "location": location,
        "capacity": capacity,
        "schedule": [],
        "notes": ""
    }
    store.set("studios", studio_id, studio)
    return studio_id


def get_studio(id: str) -> dict | None:
    """Retrieve a studio by ID."""
    return store.get("studios", id)


def list_studios() -> list:
    """List all studios."""
    return store.get_all("studios")


def remove_studio(id: str) -> bool:
    """Delete a studio."""
    return store.delete("studios", id)


def reserve_slot(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str,
    reservation_type: str,  # "class" | "individual"
    reservation_id: str     # Class ID or dancer/instructor ID
) -> bool:
    """
    Reserve a time slot in a studio.
    
    Returns True if reservation successful, False if conflict.
    """
    studio = store.get("studios", studio_id)
    if not studio:
        return False
    
    # Check for conflicts
    if is_slot_conflicted(studio_id, date, start_time, end_time):
        return False
    
    # Add reservation
    slot = {
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": int(end_time.replace(":", 0)) - int(start_time.replace(":", 0)),
        "reserved_by": reservation_id,
        "reservation_type": reservation_type
    }
    
    studio["schedule"].append(slot)
    store.set("studios", studio_id, studio)
    return True


def cancel_reservation(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str,
    reservation_id: str
) -> bool:
    """Cancel a reservation."""
    studio = store.get("studios", studio_id)
    if not studio:
        return False
    
    studio["schedule"] = [
        slot for slot in studio["schedule"]
        if not (
            slot["date"] == date and
            slot["start_time"] == start_time and
            slot["end_time"] == end_time and
            slot["reserved_by"] == reservation_id
        )
    ]
    store.set("studios", studio_id, studio)
    return True


def is_slot_conflicted(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str
) -> bool:
    """
    Check if a time slot is already reserved.
    
    Returns True if conflict exists (slot is booked).
    """
    studio = store.get("studios", studio_id)
    if not studio:
        return True  # Studio doesn't exist = conflict
    
    for slot in studio.get("schedule", []):
        if (
            slot["date"] == date and
            slot["start_time"] == start_time and
            slot["end_time"] == end_time
        ):
            return True
    
    return False


def get_available_slots(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str
) -> bool:
    """Check if a slot is available for booking."""
    return not is_slot_conflicted(studio_id, date, start_time, end_time)


def get_studio_schedule(studio_id: str) -> list:
    """Get all scheduled slots for a studio."""
    studio = store.get("studios", studio_id)
    if not studio:
        return []
    return studio.get("schedule", [])
```

---

### 3. CLI Commands (`dancemanager/cli.py`)

```python
@cli.group()
def studio():
    """Manage dance studios."""
    pass


@studio.command()
@click.option('--name', required=True)
@click.option('--location', required=True)
@click.option('--capacity', default=20)
def add(name, location, capacity):
    """Add a new studio."""
    studio_id = studios.add_studio(name, location, capacity)
    print(f"Studio '{name}' added with ID: {studio_id}")


@studio.command()
@click.option('--name', required=True)
def list(name):
    """List all studios."""
    studios_list = studios.list_studios()
    # Format and display...


@studio.command()
@click.option('--id', required=True)
def show(id):
    """Show studio details including schedule."""
    studio = studios.get_studio(id)
    schedule = studios.get_studio_schedule(id)
    # Display studio info + schedule


@studio.command()
@click.option('--id', required=True)
def remove(id):
    """Remove a studio."""
    studios.remove_studio(id)
    print(f"Studio '{id}' removed")


@studio.command()
@click.option('--id', required=True)
@click.option('--date', required=True)
@click.option('--start-time', required=True)
@click.option('--end-time', required=True)
@click.option('--reservation-type', required=True, type=click.Choice(['class', 'individual']))
@click.option('--reservation-id', required=True)
def reserve(id, date, start_time, end_time, reservation_type, reservation_id):
    """
    Reserve a time slot.
    
    - reservation_type: 'class' for recurring class reservations,
                        'individual' for one-time dancer/instructor bookings
    - reservation_id: Class ID for classes, dancer/instructor ID for individuals
    """
    success = studios.reserve_slot(
        studio_id=id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        reservation_type=reservation_type,
        reservation_id=reservation_id
    )
    if success:
        print(f"Reservation successful for {reservation_type}")
    else:
        print("Error: Time slot already reserved or studio not found")


@studio.command()
@click.option('--id', required=True)
@click.option('--date', required=True)
@click.option('--start-time', required=True)
@click.option('--end-time', required=True)
@click.option('--reservation-id', required=True)
def cancel(id, date, start_time, end_time, reservation_id):
    """Cancel a reservation."""
    success = studios.cancel_reservation(
        studio_id=id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        reservation_id=reservation_id
    )
    if success:
        print("Reservation cancelled")
    else:
        print("Error: Reservation not found")


@studio.command()
@click.option('--id', required=True)
def schedule(id):
    """Show full studio schedule."""
    schedule = studios.get_studio_schedule(id)
    # Display formatted schedule
```

---

### 4. Integration with Classes (`dancemanager/classes.py`)

```python
def add_class(
    name: str,
    instructor_id: str | None = None,
    team_ids: list[str] | None = None,
    dancer_ids: list[str] | None = None,
    studio_id: str | None = None,
    schedule: list[dict] | None = None
) -> str:
    """
    Add a class with optional studio reservation.
    
    If schedule is provided, attempts to reserve recurring slots.
    """
    class_id = make_class_id(name)
    
    class_data = {
        "id": class_id,
        "name": name,
        "instructor_id": instructor_id,
        "team_ids": team_ids or [],
        "dancer_ids": dancer_ids or [],
        "notes": ""
    }
    
    if studio_id:
        if schedule:
            for slot in schedule:
                if not studios.reserve_slot(
                    studio_id=studio_id,
                    date=slot["date"],
                    start_time=slot["start_time"],
                    end_time=slot["end_time"],
                    reservation_type="class",
                    reservation_id=class_id
                ):
                    raise ValueError(f"Cannot reserve slot {slot} - conflict detected")
        class_data["studio_id"] = studio_id
    
    store.set("classes", class_id, class_data)
    return class_id
```

---

### 5. Integration with Dancers/Instructors (`dancemanager/dancers.py`, `dancemanager/instructors.py`)

```python
# In dancers.py
def add_dancer(name: str, team_id: str | None = None) -> str:
    dancer_id = make_dancer_id(name)
    dancer = {
        "id": dancer_id,
        "name": name,
        "team_id": team_id,
        "class_ids": [],
        "notes": ""
    }
    store.set("dancers", dancer_id, dancer)
    return dancer_id


# In instructors.py
def add_instructor(name: str) -> str:
    instructor_id = make_instructor_id(name)
    instructor = {
        "id": instructor_id,
        "name": name,
        "class_ids": [],
        "dance_ids": [],
        "notes": ""
    }
    store.set("instructors", instructor_id, instructor)
    return instructor_id
```

---

### 6. Conflict Detection Logic

```python
def find_conflicts(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str
) -> list:
    """
    Find all conflicting reservations for a time slot.
    
    Returns list of reservation details if conflicts exist.
    """
    studio = store.get("studios", studio_id)
    if not studio:
        return []
    
    conflicts = []
    for slot in studio.get("schedule", []):
        if (
            slot["date"] == date and
            slot["start_time"] == start_time and
            slot["end_time"] == end_time
        ):
            conflicts.append({
                "date": slot["date"],
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
                "reserved_by": slot["reserved_by"],
                "reservation_type": slot["reservation_type"]
            })
    
    return conflicts


def can_book_slot(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str,
    reservation_type: str,
    reservation_id: str
) -> tuple[bool, list]:
    """
    Check if a slot can be booked.
    
    Returns (is_available, conflict_details)
    """
    conflicts = find_conflicts(studio_id, date, start_time, end_time)
    is_available = len(conflicts) == 0
    return is_available, conflicts
```

---

## Implementation Steps

### Phase 1: Data Model Updates

1. Update `DEFAULT_STORE_SCHEMA` in `dancemanager/models.py`
2. Add `studios` collection initialization

### Phase 2: Core Studio Module

3. Create `dancemanager/studios.py`
4. Implement CRUD operations (add, get, list, remove)
5. Implement `reserve_slot()` with conflict detection
6. Implement `cancel_reservation()`
7. Implement `get_studio_schedule()`

### Phase 3: CLI Integration

8. Add `studio` group to `cli.py`
9. Implement `studio add` command
10. Implement `studio list` command
11. Implement `studio show` command
12. Implement `studio remove` command
13. Implement `studio reserve` command
14. Implement `studio cancel` command
15. Implement `studio schedule` command

### Phase 4: Class Integration

16. Update `classes.py` to accept `studio_id` parameter
17. Update `classes add` to support recurring reservations
18. Add validation to prevent double-booking classes

### Phase 5: Dancer/Instructor Integration

19. Update `dancers.py` to support studio reservations
20. Update `instructors.py` to support studio reservations
21. Add `studio reserve --reservation-type individual` for dancers/instructors

### Phase 6: Testing

22. Write unit tests for studio operations
23. Write integration tests for class-studio reservations
24. Write conflict detection tests
25. Verify no double-booking scenarios

### Phase 7: Polish

26. Add formatted output for studio schedules
27. Add helpful error messages
28. Add `--help` documentation for all commands
29. Add CSV export for studio data

---

## Key Design Decisions

### 1. Reservation Types

- **Class reservations**: Recurring date/time slots (e.g., "Mon 18:00-19:30")
- **Individual reservations**: One-time slots for dancers/instructors (e.g., "Jan 15 18:00-19:30")

### 2. Conflict Detection

- Exact match on date + start_time + end_time
- Prevents double-booking of the same time slot
- Allows multiple classes at different times in same studio

### 3. Studio Capacity

- Optional field for tracking concurrent dancer limits
- Can be enforced in future if needed
- Currently informational

### 4. Schedule Structure

- Each studio has its own independent schedule
- No global schedule conflicts between studios
- Studios can operate simultaneously at different times

---

## Example Usage

```bash
# Add Studio 1
studio add --name "Studio 1" --location "123 Main St" --capacity 25

# Add Studio 2
studio add --name "Studio 2" --location "456 Oak Ave" --capacity 30

# Reserve a recurring class slot in Studio 1
studio reserve \
  --id studio-1 \
  --date 2024-01-15 \
  --start-time 18:00 \
  --end-time 19:30 \
  --reservation-type class \
  --reservation-id class-ballet-101

# Reserve a one-time slot for an individual dancer
studio reserve \
  --id studio-1 \
  --date 2024-01-15 \
  --start-time 19:30 \
  --end-time 20:30 \
  --reservation-type individual \
  --reservation-id dancer-jane-doe

# Try to book a conflicting slot (will fail)
studio reserve \
  --id studio-1 \
  --date 2024-01-15 \
  --start-time 18:00 \
  --end-time 19:30 \
  --reservation-type class \
  --reservation-id class-jazz-201

# View studio schedule
studio schedule --id studio-1

# Cancel a reservation
studio cancel \
  --id studio-1 \
  --date 2024-01-15 \
  --start-time 18:00 \
  --end-time 19:30 \
  --reservation-id class-ballet-101
```

---

## Future Enhancements

1. **Studio availability calendar**: Visual calendar view
2. **Bulk reservations**: Import multiple class slots at once
3. **Studio capacity enforcement**: Hard limit on concurrent dancers
4. **Equipment booking**: Reserve specific equipment alongside studio
5. **Waitlist**: Queue for fully booked slots
6. **Notifications**: Email reminders for upcoming reservations
7. **API endpoints**: RESTful API for web integration

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `dancemanager/models.py` | Modify | Add `studios` to schema |
| `dancemanager/studios.py` | Create | Core studio logic |
| `dancemanager/cli.py` | Modify | Add studio commands |
| `dancemanager/classes.py` | Modify | Add studio integration |
| `dancemanager/dancers.py` | Modify | Add studio reservation support |
| `dancemanager/instructors.py` | Modify | Add studio reservation support |
| `tests/test_studios.py` | Create | Unit tests |
| `dancemanager/web/main.py` | Modify | Add studio routes |
| `dancemanager/web/templates/studios/list.html` | Create | Studio list template |
| `dancemanager/web/templates/studios/form.html` | Create | Studio form template |
| `dancemanager/web/templates/studios/detail.html` | Create | Studio detail template |
| `dancemanager/web/templates/studios/schedule.html` | Create | Studio schedule template |
| `dancemanager/web/templates/studios/reserve.html` | Create | Studio reservation form template |

---

## Testing Checklist

- [ ] Studio CRUD operations work correctly
- [ ] Class reservations create recurring slots
- [ ] Individual reservations work for dancers/instructors
- [ ] Conflict detection prevents double-booking
- [ ] Canceling reservations frees up slots
- [ ] Multiple studios can operate simultaneously
- [ ] Schedule display is clear and readable
- [ ] Error messages are helpful
- [ ] Help text documents all commands
