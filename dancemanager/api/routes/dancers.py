"""Dancer CRUD API endpoints."""

from fastapi import APIRouter, HTTPException, Query

from dancemanager.store import get_store
from dancemanager.api import schemas

router = APIRouter()


@router.get("/api/dancers/", response_model=list)
def api_dancers_list():
    """List all dancers."""
    store = get_store()
    dancers = store.get_collection("dancers")
    return list(dancers.values())


@router.get("/api/dancers/search", response_model=list)
def api_dancers_search(q: str = Query(...)):
    """Search dancers by name."""
    store = get_store()
    dancers = store.get_collection("dancers")
    return [d for d in dancers.values() if q.lower() in d.get("name", "").lower()]


@router.get("/api/dancers/{dancer_id}", response_model=schemas.DancerResponse)
def api_dancer_detail(dancer_id: str):
    """Show details for a single dancer."""
    store = get_store()
    dancer = store.get("dancers", dancer_id)
    if not dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")
    return dancer


@router.post("/api/dancers/", response_model=schemas.DancerResponse)
def api_dancer_create(dancer: schemas.DancerCreate):
    """Create a new dancer."""
    store = get_store()
    dancer_id = schemas.make_dancer_id(dancer.name)
    if dancer_id in store.get_collection("dancers"):
        raise HTTPException(status_code=400, detail="Dancer already exists")
    dancer_dict = dancer.model_dump()
    store.set("dancers", dancer_id, dancer_dict)
    return store.get("dancers", dancer_id)


@router.put("/api/dancers/{dancer_id}", response_model=schemas.DancerResponse)
def api_dancer_update(dancer_id: str, dancer: schemas.DancerUpdate):
    """Update an existing dancer."""
    store = get_store()
    existing = store.get("dancers", dancer_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Dancer not found")
    update_data = dancer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            existing[key] = value
    store.set("dancers", dancer_id, existing)
    return existing


@router.delete("/api/dancers/{dancer_id}", status_code=204)
def api_dancer_delete(dancer_id: str):
    """Remove a dancer."""
    store = get_store()
    if not store.get("dancers", dancer_id):
        raise HTTPException(status_code=404, detail="Dancer not found")
    store.delete("dancers", dancer_id)
    return None


@router.post("/api/dancers/{dancer_id}/assign-team")
def api_dancer_assign_team(dancer_id: str, team_id: str):
    """Assign a dancer to a team."""
    store = get_store()
    dancer = store.get("dancers", dancer_id)
    if not dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")
    team = store.get("teams", team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    dancer["team_id"] = team_id
    if dancer_id not in team.get("dancer_ids", []):
        team["dancer_ids"].append(dancer_id)
        store.set("teams", team_id, team)
    store.set("dancers", dancer_id, dancer)
    return {"message": f"Dancer {dancer_id} assigned to team {team_id}"}
