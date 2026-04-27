"""Dance CRUD API endpoints."""

from fastapi import APIRouter, HTTPException

from dancemanager.store import get_store
from dancemanager.api import schemas

router = APIRouter()


@router.get("/api/dances/", response_model=list)
def api_dances_list():
    """List all dances."""
    store = get_store()
    dances = store.get_collection("dances")
    return list(dances.values())


@router.get("/api/dances/{dance_id}", response_model=schemas.DanceResponse)
def api_dance_detail(dance_id: str):
    """Show details for a single dance."""
    store = get_store()
    dance = store.get("dances", dance_id)
    if not dance:
        raise HTTPException(status_code=404, detail="Dance not found")
    return dance


@router.post("/api/dances/", response_model=schemas.DanceResponse)
def api_dance_create(dance: schemas.DanceCreate):
    """Create a new dance."""
    store = get_store()
    dance_id = schemas.make_dance_id(dance.name)
    if dance_id in store.get_collection("dances"):
        raise HTTPException(status_code=400, detail="Dance already exists")
    dance_dict = dance.model_dump()
    store.set("dances", dance_id, dance_dict)
    return store.get("dances", dance_id)


@router.put("/api/dances/{dance_id}", response_model=schemas.DanceResponse)
def api_dance_update(dance_id: str, dance: schemas.DanceUpdate):
    """Update an existing dance."""
    store = get_store()
    existing = store.get("dances", dance_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Dance not found")
    update_data = dance.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            existing[key] = value
    store.set("dances", dance_id, existing)
    return existing


@router.delete("/api/dances/{dance_id}", status_code=204)
def api_dance_delete(dance_id: str):
    """Remove a dance."""
    store = get_store()
    if not store.get("dances", dance_id):
        raise HTTPException(status_code=404, detail="Dance not found")
    store.delete("dances", dance_id)
    return None


@router.post("/api/dances/{dance_id}/dancers/add")
def api_dance_add_dancer(dance_id: str, dancer_id: str):
    """Add a dancer to a dance."""
    store = get_store()
    dance = store.get("dances", dance_id)
    if not dance:
        raise HTTPException(status_code=404, detail="Dance not found")
    dancer = store.get("dancers", dancer_id)
    if not dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")
    if dancer_id not in dance.get("dancer_ids", []):
        dance["dancer_ids"].append(dancer_id)
        store.set("dances", dance_id, dance)
    return {"message": f"Dancer {dancer_id} added to dance {dance_id}"}


@router.post("/api/dances/{dance_id}/dancers/remove")
def api_dance_remove_dancer(dance_id: str, dancer_id: str):
    """Remove a dancer from a dance."""
    store = get_store()
    dance = store.get("dances", dance_id)
    if not dance:
        raise HTTPException(status_code=404, detail="Dance not found")
    if dancer_id in dance.get("dancer_ids", []):
        dance["dancer_ids"].remove(dancer_id)
        store.set("dances", dance_id, dance)
    return {"message": f"Dancer {dancer_id} removed from dance {dance_id}"}


@router.post("/api/dances/{dance_id}/teams/add")
def api_dance_add_team(dance_id: str, team_id: str):
    """Add a team to a dance."""
    store = get_store()
    dance = store.get("dances", dance_id)
    if not dance:
        raise HTTPException(status_code=404, detail="Dance not found")
    team = store.get("teams", team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    current_team_ids = list(dance.get("team_ids", []))
    if team_id not in current_team_ids:
        current_team_ids.append(team_id)
        dance["team_ids"] = current_team_ids
        store.set("dances", dance_id, dance)
    return {"message": f"Team {team_id} added to dance {dance_id}"}


@router.post("/api/dances/{dance_id}/teams/remove")
def api_dance_remove_team(dance_id: str, team_id: str):
    """Remove a team from a dance."""
    store = get_store()
    dance = store.get("dances", dance_id)
    if not dance:
        raise HTTPException(status_code=404, detail="Dance not found")
    current_team_ids = list(dance.get("team_ids", []))
    if team_id in current_team_ids:
        current_team_ids.remove(team_id)
        dance["team_ids"] = current_team_ids
        store.set("dances", dance_id, dance)
    return {"message": f"Team {team_id} removed from dance {dance_id}"}
