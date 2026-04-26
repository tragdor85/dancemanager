"""CSV import/export API endpoints."""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response

from dancemanager.store import get_store
from dancemanager.api import schemas

router = APIRouter()


@router.post("/api/import/classes")
def api_import_classes(csv_file: UploadFile = File(...)):
    """Import classes from CSV."""
    store = get_store()
    content = csv_file.file.read()
    lines = content.decode("utf-8").strip().split("\n")
    headers = lines[0].split(",")
    data = [line.split(",") for line in lines[1:]]
    imported_count = 0
    for row in data:
        name = row[0].strip()
        if name not in store.get_collection("classes"):
            class_id = schemas.make_class_id(name)
            store.set(
                "classes",
                class_id,
                {
                    "id": class_id,
                    "name": name,
                    "instructor_id": None,
                    "team_ids": [],
                    "dancer_ids": [],
                    "notes": "",
                },
            )
            imported_count += 1
    return {"message": f"Imported {imported_count} classes", "count": imported_count}


@router.post("/api/import/teams")
def api_import_teams(csv_file: UploadFile = File(...)):
    """Import teams from CSV."""
    store = get_store()
    content = csv_file.file.read()
    lines = content.decode("utf-8").strip().split("\n")
    headers = lines[0].split(",")
    data = [line.split(",") for line in lines[1:]]
    imported_count = 0
    for row in data:
        name = row[0].strip()
        if name not in store.get_collection("teams"):
            team_id = schemas.make_team_id(name)
            store.set(
                "teams",
                team_id,
                {"id": team_id, "name": name, "dancer_ids": [], "notes": ""},
            )
            imported_count += 1
    return {"message": f"Imported {imported_count} teams", "count": imported_count}


@router.get("/api/export/dancers")
def api_export_dancers():
    """Export dancers as CSV."""
    store = get_store()
    lines = ["id,name,team_id,class_ids,notes"]
    for dancer in store.get_collection("dancers").values():
        lines.append(
            f"{dancer.get('id', '')},{dancer.get('name', '')},{dancer.get('team_id', '') or ''},{','.join(dancer.get('class_ids', [])) or ''},{dancer.get('notes', '')}"
        )
    content = "\n".join(lines).encode("utf-8")
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dancers.csv"},
    )


@router.get("/api/export/teams")
def api_export_teams():
    """Export teams as CSV."""
    store = get_store()
    lines = ["id,name,dancer_ids,notes"]
    for team in store.get_collection("teams").values():
        lines.append(
            f"{team.get('id', '')},{team.get('name', '')},{','.join(team.get('dancer_ids', [])) or ''},{team.get('notes', '')}"
        )
    content = "\n".join(lines).encode("utf-8")
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=teams.csv"},
    )


@router.get("/api/export/classes")
def api_export_classes():
    """Export classes as CSV."""
    store = get_store()
    lines = ["id,name,instructor_id,team_ids,dancer_ids,notes"]
    for cls in store.get_collection("classes").values():
        lines.append(
            f"{cls.get('id', '')},{cls.get('name', '')},{cls.get('instructor_id', '') or ''},{','.join(cls.get('team_ids', [])) or ''},{','.join(cls.get('dancer_ids', [])) or ''},{cls.get('notes', '')}"
        )
    content = "\n".join(lines).encode("utf-8")
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=classes.csv"},
    )


@router.get("/api/export/dances")
def api_export_dances():
    """Export dances as CSV."""
    store = get_store()
    lines = ["id,name,song_name,instructor_id,dancer_ids"]
    for dance in store.get_collection("dances").values():
        lines.append(
            f"{dance.get('id', '')},{dance.get('name', '')},{dance.get('song_name', '')},{dance.get('instructor_id', '') or ''},{','.join(dance.get('dancer_ids', [])) or ''}"
        )
    content = "\n".join(lines).encode("utf-8")
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dances.csv"},
    )


@router.get("/api/export/recital/{recital_id}")
def api_export_recital_csv(recital_id: str):
    """Export recital schedule as CSV."""
    store = get_store()
    recital = store.get("recitals", recital_id)
    if not recital:
        raise HTTPException(status_code=404, detail="Recital not found")
    dances_coll = store.get_collection("dances")
    order = recital.get("performance_order", [])
    lines = ["position,dance_name,song_name,performers"]
    for slot in sorted(order, key=lambda x: x["position"]):
        dance = dances_coll.get(slot["dance_id"])
        if dance:
            performers = ", ".join(dance.get("dancer_ids", []))
            lines.append(
                f"{slot['position']},{dance.get('name', '')},{dance.get('song_name', '')},{performers}"
            )
    content = "\n".join(lines).encode("utf-8")
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={recital_id}_schedule.csv"
        },
    )
