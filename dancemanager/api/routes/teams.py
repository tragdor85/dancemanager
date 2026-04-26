"""Team CRUD API endpoints."""

from fastapi import APIRouter, HTTPException

from dancemanager.store import get_store
from dancemanager.api import schemas

router = APIRouter()


@router.get("/api/teams/", response_model=list)
def api_teams_list():
    """List all teams."""
    store = get_store()
    teams = store.get_collection("teams")
    return list(teams.values())


@router.get("/api/teams/{team_id}", response_model=schemas.TeamResponse)
def api_team_detail(team_id: str):
    """Show details for a single team."""
    store = get_store()
    team = store.get("teams", team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("/api/teams/", response_model=schemas.TeamResponse)
def api_team_create(team: schemas.TeamCreate):
    """Create a new team."""
    store = get_store()
    team_id = schemas.make_team_id(team.name)
    if team_id in store.get_collection("teams"):
        raise HTTPException(status_code=400, detail="Team already exists")
    team_dict = team.model_dump()
    store.set("teams", team_id, team_dict)
    return store.get("teams", team_id)


@router.put("/api/teams/{team_id}", response_model=schemas.TeamResponse)
def api_team_update(team_id: str, team: schemas.TeamUpdate):
    """Update an existing team."""
    store = get_store()
    existing = store.get("teams", team_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Team not found")
    update_data = team.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            existing[key] = value
    store.set("teams", team_id, existing)
    return existing


@router.delete("/api/teams/{team_id}", status_code=204)
def api_team_delete(team_id: str):
    """Remove a team."""
    store = get_store()
    if not store.get("teams", team_id):
        raise HTTPException(status_code=404, detail="Team not found")
    store.delete("teams", team_id)
    return None


@router.post("/api/teams/{team_id}/dancers/add")
def api_team_add_dancer(team_id: str, dancer_id: str):
    """Add a dancer to a team."""
    store = get_store()
    team = store.get("teams", team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    dancer = store.get("dancers", dancer_id)
    if not dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")
    if dancer_id not in team.get("dancer_ids", []):
        team["dancer_ids"].append(dancer_id)
        store.set("teams", team_id, team)
    return {"message": f"Dancer {dancer_id} added to team {team_id}"}


@router.post("/api/teams/{team_id}/dancers/remove")
def api_team_remove_dancer(team_id: str, dancer_id: str):
    """Remove a dancer from a team."""
    store = get_store()
    team = store.get("teams", team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if dancer_id in team.get("dancer_ids", []):
        team["dancer_ids"].remove(dancer_id)
        store.set("teams", team_id, team)
    return {"message": f"Dancer {dancer_id} removed from team {team_id}"}
