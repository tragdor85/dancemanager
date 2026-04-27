"""Studio CRUD and reservation API endpoints."""

import json

from fastapi import APIRouter, HTTPException

from dancemanager.api import schemas
from dancemanager.studios import (
    cancel_reservation,
    find_conflicts,
    get_studio_schedule,
    reserve_slot,
)
from dancemanager.store import get_store

router = APIRouter()


@router.get("/api/studios/", response_model=list)
def api_studios_list():
    """List all studios."""
    store = get_store()
    return list(store.get_collection("studios").values())


@router.get("/api/studios/{studio_id}", response_model=schemas.StudioResponse)
def api_studio_detail(studio_id: str):
    """Show details for a single studio."""
    store = get_store()
    studio = store.get("studios", studio_id)
    if not studio:
        raise HTTPException(status_code=404, detail="Studio not found")
    return studio


@router.post("/api/studios/", response_model=schemas.StudioResponse)
def api_studio_create(studio: schemas.StudioCreate):
    """Create a new studio."""
    store = get_store()
    studio_id = schemas.make_studio_id(studio.name)
    if studio_id in store.get_collection("studios"):
        raise HTTPException(status_code=400, detail="Studio already exists")

    extra_fields: dict = {}
    if studio.equipment:
        extra_fields["equipment"] = studio.equipment

    store.execute(
        "INSERT OR REPLACE INTO studios "
        "(id, name, location, capacity, schedule, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (
            studio_id,
            studio.name,
            studio.location or "",
            studio.capacity,
            "[]",
            "",
        ),
    )

    if extra_fields:
        store.execute(
            "UPDATE studios SET extra = ? WHERE id = ?",
            (json.dumps(extra_fields), studio_id),
        )

    store.save()
    return store.get("studios", studio_id)


@router.put("/api/studios/{studio_id}", response_model=schemas.StudioResponse)
def api_studio_update(studio_id: str, studio: schemas.StudioUpdate):
    """Update an existing studio."""
    store = get_store()
    existing = store.get("studios", studio_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Studio not found")

    update_data = studio.model_dump(exclude_unset=True)

    # Handle equipment separately (stored in extra column)
    equipment = update_data.pop("equipment", None)

    for key, value in update_data.items():
        if value is not None:
            existing[key] = value

    store.set("studios", studio_id, existing)

    if equipment is not None:
        extra = existing.get("extra") or {}
        if isinstance(extra, str):
            try:
                extra = json.loads(extra)
            except (json.JSONDecodeError, TypeError):
                extra = {}
        extra["equipment"] = equipment
        store.execute(
            "UPDATE studios SET extra = ? WHERE id = ?",
            (json.dumps(extra), studio_id),
        )

    return store.get("studios", studio_id)


@router.delete("/api/studios/{studio_id}", status_code=204)
def api_studio_delete(studio_id: str):
    """Remove a studio."""
    store = get_store()
    if not store.get("studios", studio_id):
        raise HTTPException(status_code=404, detail="Studio not found")
    store.delete("studios", studio_id)
    return None


@router.post("/api/studios/{studio_id}/reserve")
def api_studio_reserve(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str,
    reservation_type: str,
    reservation_id: str,
):
    """Reserve a time slot in a studio."""
    store = get_store()
    if not store.get("studios", studio_id):
        raise HTTPException(status_code=404, detail="Studio not found")

    success = reserve_slot(
        studio_id=studio_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        reservation_type=reservation_type,
        reservation_id=reservation_id,
    )

    if not success:
        conflicts = find_conflicts(studio_id, date, start_time, end_time)
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Time slot conflict",
                "conflicts": conflicts,
            },
        )

    return {"message": f"Reservation created for {date} {start_time}-{end_time}"}


@router.delete("/api/studios/{studio_id}/reservations")
def api_studio_cancel_reservation(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str,
    reservation_id: str = None,
):
    """Cancel a reservation."""
    store = get_store()
    if not store.get("studios", studio_id):
        raise HTTPException(status_code=404, detail="Studio not found")

    success = cancel_reservation(
        studio_id=studio_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        reservation_id=reservation_id or "",
    )

    if not success:
        raise HTTPException(status_code=404, detail="Reservation not found")

    return {"message": f"Reservation cancelled for {date} {start_time}-{end_time}"}


@router.get("/api/studios/{studio_id}/schedule")
def api_studio_schedule(studio_id: str):
    """Get the full schedule for a studio."""
    store = get_store()
    if not store.get("studios", studio_id):
        raise HTTPException(status_code=404, detail="Studio not found")

    return get_studio_schedule(studio_id)


@router.get("/api/studios/{studio_id}/conflicts")
def api_studio_check_conflicts(
    studio_id: str,
    date: str,
    start_time: str,
    end_time: str,
):
    """Check for scheduling conflicts."""
    store = get_store()
    if not store.get("studios", studio_id):
        raise HTTPException(status_code=404, detail="Studio not found")

    conflicts = find_conflicts(studio_id, date, start_time, end_time)
    return {"has_conflicts": len(conflicts) > 0, "conflicts": conflicts}
