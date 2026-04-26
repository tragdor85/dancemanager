"""Recital CRUD and scheduling API endpoints."""

from fastapi import APIRouter, HTTPException

from dancemanager.store import get_store
from dancemanager.api import schemas
from dancemanager.recital import greedy_schedule

router = APIRouter()


@router.get("/api/recitals/", response_model=list)
def api_recitals_list():
    """List all recitals."""
    store = get_store()
    recitals = store.get_collection("recitals")
    return list(recitals.values())


@router.get("/api/recitals/{recital_id}", response_model=schemas.RecitalResponse)
def api_recital_detail(recital_id: str):
    """Show details for a single recital."""
    store = get_store()
    recital = store.get("recitals", recital_id)
    if not recital:
        raise HTTPException(status_code=404, detail="Recital not found")
    return recital


@router.post("/api/recitals/", response_model=schemas.RecitalResponse)
def api_recital_create(recital: schemas.RecitalCreate):
    """Create a new recital."""
    store = get_store()
    recital_id = schemas.make_recital_id(recital.name)
    if recital_id in store.get_collection("recitals"):
        raise HTTPException(status_code=400, detail="Recital already exists")
    recital_dict = recital.model_dump()
    store.set("recitals", recital_id, recital_dict)
    return store.get("recitals", recital_id)


@router.put("/api/recitals/{recital_id}", response_model=schemas.RecitalResponse)
def api_recital_update(recital_id: str, recital: schemas.RecitalUpdate):
    """Update an existing recital."""
    store = get_store()
    existing = store.get("recitals", recital_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Recital not found")
    update_data = recital.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            existing[key] = value
    store.set("recitals", recital_id, existing)
    return existing


@router.delete("/api/recitals/{recital_id}", status_code=204)
def api_recital_delete(recital_id: str):
    """Remove a recital."""
    store = get_store()
    if not store.get("recitals", recital_id):
        raise HTTPException(status_code=404, detail="Recital not found")
    store.delete("recitals", recital_id)
    return None


@router.post("/api/recitals/{recital_id}/dances/add")
def api_recital_add_dance(recital_id: str, dance_id: str):
    """Add a dance to a recital."""
    store = get_store()
    recital = store.get("recitals", recital_id)
    if not recital:
        raise HTTPException(status_code=404, detail="Recital not found")
    dance = store.get("dances", dance_id)
    if not dance:
        raise HTTPException(status_code=404, detail="Dance not found")
    order = recital.get("performance_order", [])
    for slot in order:
        if slot["dance_id"] == dance_id:
            return {"message": "Dance already in recital", "dance_id": dance_id}
    position = len(order) + 1
    order.append({"dance_id": dance_id, "position": position})
    recital["performance_order"] = order
    store.set("recitals", recital_id, recital)
    return {
        "message": "Dance added to recital",
        "dance_id": dance_id,
        "position": position,
    }


@router.post("/api/recitals/{recital_id}/dances/remove")
def api_recital_remove_dance(recital_id: str, dance_id: str):
    """Remove a dance from a recital."""
    store = get_store()
    recital = store.get("recitals", recital_id)
    if not recital:
        raise HTTPException(status_code=404, detail="Recital not found")
    order = recital.get("performance_order", [])
    updated = [s for s in order if s["dance_id"] != dance_id]
    for i, slot in enumerate(updated):
        slot["position"] = i + 1
    recital["performance_order"] = updated
    store.set("recitals", recital_id, recital)
    return {"message": "Dance removed from recital", "dance_id": dance_id}


@router.post("/api/recitals/{recital_id}/reorder")
def api_recital_reorder_dances(recital_id: str, body: list[schemas.DanceSlot]):
    """Reorder dances in a recital."""
    store = get_store()
    recital = store.get("recitals", recital_id)
    if not recital:
        raise HTTPException(status_code=404, detail="Recital not found")
    slots = sorted(body, key=lambda d: d.position)
    order = [{"dance_id": d.dance_id, "position": d.position} for d in slots]
    recital["performance_order"] = order
    store.set("recitals", recital_id, recital)
    return {"message": "Dances reordered", "positions": [s["dance_id"] for s in order]}


@router.post("/api/recitals/{recital_id}/generate-schedule")
def api_recital_generate_schedule(recital_id: str):
    """Auto-generate a schedule for the recital."""
    store = get_store()
    recital = store.get("recitals", recital_id)
    if not recital:
        raise HTTPException(status_code=404, detail="Recital not found")
    dances_coll = store.get_collection("dances")
    order = recital.get("performance_order", [])
    dance_ids = [s["dance_id"] for s in order]

    if len(dance_ids) < 2:
        raise HTTPException(
            status_code=400, detail="Need at least 2 dances to generate a schedule"
        )

    dancer_dances = {}
    for did in dance_ids:
        dance = dances_coll.get(did)
        if dance is None:
            continue
        for dancer_id in dance.get("dancer_ids", []):
            if dancer_id not in dancer_dances:
                dancer_dances[dancer_id] = []
            dancer_dances[dancer_id].append(did)

    result = greedy_schedule(dance_ids, dancer_dances, 4)
    if result is None:
        return {"error": "Could not generate a valid schedule", "schedule": []}

    recital["performance_order"] = [
        {"dance_id": did, "position": i + 1} for i, did in enumerate(result)
    ]
    store.set("recitals", recital_id, recital)

    schedule = []
    for i, did in enumerate(result):
        dance = dances_coll.get(did)
        if dance:
            dancers = []
            for dancer_id in dance.get("dancer_ids", []):
                d = store.get("dancers", dancer_id)
                if d:
                    dancers.append({"id": dancer_id, "name": d.get("name", dancer_id)})
            schedule.append(
                {
                    "position": i + 1,
                    "dance_id": did,
                    "dance_name": dance.get("name", ""),
                    "song_name": dance.get("song_name", ""),
                    "dancers": dancers,
                }
            )
    return {"schedule": schedule}


@router.get("/api/recitals/{recital_id}/schedule")
def api_recital_get_schedule(recital_id: str):
    """Get the schedule for a recital."""
    store = get_store()
    recital = store.get("recitals", recital_id)
    if not recital:
        raise HTTPException(status_code=404, detail="Recital not found")
    dances_coll = store.get_collection("dances")
    order = recital.get("performance_order", [])

    schedule = []
    for slot in sorted(order, key=lambda x: x["position"]):
        dance = dances_coll.get(slot["dance_id"])
        if dance:
            dancers = []
            for dancer_id in dance.get("dancer_ids", []):
                d = store.get("dancers", dancer_id)
                if d:
                    dancers.append({"id": dancer_id, "name": d.get("name", dancer_id)})
            schedule.append(
                {
                    "position": slot["position"],
                    "dance_id": slot["dance_id"],
                    "dance_name": dance.get("name", ""),
                    "song_name": dance.get("song_name", ""),
                    "dancers": dancers,
                }
            )
    return {"recital_id": recital_id, "schedule": schedule}
