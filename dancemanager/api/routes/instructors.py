"""Instructor CRUD API endpoints."""

from fastapi import APIRouter, HTTPException

from dancemanager.store import get_store
from dancemanager.api import schemas

router = APIRouter()


@router.get("/api/instructors/", response_model=list)
def api_instructors_list():
    """List all instructors."""
    store = get_store()
    instructors = store.get_collection("instructors")
    return list(instructors.values())


@router.get(
    "/api/instructors/{instructor_id}", response_model=schemas.InstructorResponse
)
def api_instructor_detail(instructor_id: str):
    """Show details for a single instructor."""
    store = get_store()
    instructor = store.get("instructors", instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return instructor


@router.post("/api/instructors/", response_model=schemas.InstructorResponse)
def api_instructor_create(instructor: schemas.InstructorCreate):
    """Create a new instructor."""
    store = get_store()
    instructor_id = schemas.make_instructor_id(instructor.name)
    if instructor_id in store.get_collection("instructors"):
        raise HTTPException(status_code=400, detail="Instructor already exists")
    instructor_dict = instructor.model_dump()
    store.set("instructors", instructor_id, instructor_dict)
    return store.get("instructors", instructor_id)


@router.put(
    "/api/instructors/{instructor_id}", response_model=schemas.InstructorResponse
)
def api_instructor_update(instructor_id: str, instructor: schemas.InstructorUpdate):
    """Update an existing instructor."""
    store = get_store()
    existing = store.get("instructors", instructor_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Instructor not found")
    update_data = instructor.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            existing[key] = value
    store.set("instructors", instructor_id, existing)
    return existing


@router.delete("/api/instructors/{instructor_id}", status_code=204)
def api_instructor_delete(instructor_id: str):
    """Remove an instructor."""
    store = get_store()
    if not store.get("instructors", instructor_id):
        raise HTTPException(status_code=404, detail="Instructor not found")
    store.delete("instructors", instructor_id)
    return None


@router.post("/api/instructors/{instructor_id}/classes/assign")
def api_instructor_assign_class(instructor_id: str, class_id: str):
    """Assign a class to an instructor."""
    store = get_store()
    instructor = store.get("instructors", instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    cls = store.get("classes", class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    cls["instructor_id"] = instructor_id
    store.set("classes", class_id, cls)
    return {"message": f"Class {class_id} assigned to instructor {instructor_id}"}


@router.post("/api/instructors/{instructor_id}/dances/assign")
def api_instructor_assign_dance(instructor_id: str, dance_id: str):
    """Assign a dance to an instructor."""
    store = get_store()
    instructor = store.get("instructors", instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    dance = store.get("dances", dance_id)
    if not dance:
        raise HTTPException(status_code=404, detail="Dance not found")
    dance["instructor_id"] = instructor_id
    store.set("dances", dance_id, dance)
    return {"message": f"Dance {dance_id} assigned to instructor {instructor_id}"}
