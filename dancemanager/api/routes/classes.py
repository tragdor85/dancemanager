"""Class CRUD API endpoints."""

from fastapi import APIRouter, HTTPException

from dancemanager.store import get_store
from dancemanager.api import schemas

router = APIRouter()


@router.get("/api/classes/", response_model=list)
def api_classes_list():
    """List all classes."""
    store = get_store()
    classes = store.get_collection("classes")
    return list(classes.values())


@router.get("/api/classes/{class_id}", response_model=schemas.ClassResponse)
def api_class_detail(class_id: str):
    """Show details for a single class."""
    store = get_store()
    cls = store.get("classes", class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    return cls


@router.post("/api/classes/", response_model=schemas.ClassResponse)
def api_class_create(cls: schemas.ClassCreate):
    """Create a new class."""
    store = get_store()
    class_id = schemas.make_class_id(cls.name)
    if class_id in store.get_collection("classes"):
        raise HTTPException(status_code=400, detail="Class already exists")
    cls_dict = cls.model_dump()
    store.set("classes", class_id, cls_dict)
    return store.get("classes", class_id)


@router.put("/api/classes/{class_id}", response_model=schemas.ClassResponse)
def api_class_update(class_id: str, cls: schemas.ClassUpdate):
    """Update an existing class."""
    store = get_store()
    existing = store.get("classes", class_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Class not found")
    update_data = cls.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            existing[key] = value
    store.set("classes", class_id, existing)
    return existing


@router.delete("/api/classes/{class_id}", status_code=204)
def api_class_delete(class_id: str):
    """Remove a class."""
    store = get_store()
    if not store.get("classes", class_id):
        raise HTTPException(status_code=404, detail="Class not found")
    store.delete("classes", class_id)
    return None


@router.post("/api/classes/{class_id}/teams/add")
def api_class_add_team(class_id: str, team_id: str):
    """Assign a team to a class."""
    store = get_store()
    cls = store.get("classes", class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    team = store.get("teams", team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team_id not in cls.get("team_ids", []):
        cls["team_ids"].append(team_id)
        store.set("classes", class_id, cls)
    return {"message": f"Team {team_id} added to class {class_id}"}


@router.post("/api/classes/{class_id}/dancers/add")
def api_class_add_dancer(class_id: str, dancer_id: str):
    """Add a dancer to a class."""
    store = get_store()
    cls = store.get("classes", class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    dancer = store.get("dancers", dancer_id)
    if not dancer:
        raise HTTPException(status_code=404, detail="Dancer not found")
    if dancer_id not in cls.get("dancer_ids", []):
        cls["dancer_ids"].append(dancer_id)
        store.set("classes", class_id, cls)
    return {"message": f"Dancer {dancer_id} added to class {class_id}"}


@router.post("/api/classes/{class_id}/dancers/remove")
def api_class_remove_dancer(class_id: str, dancer_id: str):
    """Remove a dancer from a class."""
    store = get_store()
    cls = store.get("classes", class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if dancer_id in cls.get("dancer_ids", []):
        cls["dancer_ids"].remove(dancer_id)
        store.set("classes", class_id, cls)
    return {"message": f"Dancer {dancer_id} removed from class {class_id}"}


@router.post("/api/classes/{class_id}/instructor/assign")
def api_class_assign_instructor(class_id: str, instructor_id: str):
    """Assign an instructor to a class."""
    store = get_store()
    cls = store.get("classes", class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    instructor = store.get("instructors", instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    cls["instructor_id"] = instructor_id
    store.set("classes", class_id, cls)
    return {"message": f"Instructor {instructor_id} assigned to class {class_id}"}
