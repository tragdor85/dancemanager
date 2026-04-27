"""Web application for Dance Manager."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dancemanager.store import DataStore, get_store
from dancemanager.models import (
    make_dancer_id,
    make_team_id,
    make_class_id,
    make_instructor_id,
    make_dance_id,
    make_recital_id,
    make_studio_id,
)
from dancemanager.recital import greedy_schedule
from dancemanager.studios import (
    get_studio_schedule,
    reserve_slot as _reserve_slot,
    cancel_reservation as _cancel_reservation,
    title,
)


def _format_time_12h(time_str: str) -> str:
    """Convert HH:MM military time to standard 12-hour format (e.g. '2:30 p.m.' )."""
    if not time_str or ":" not in time_str:
        return time_str or ""
    parts = time_str.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    period = "a.m." if hour < 12 else "p.m."
    display_hour = hour % 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour}:{minute:02d} {period}"


app = FastAPI()
router = APIRouter()

# Serve static files (logos, images, etc.) from the resources directory
_RESOURCES_DIR = Path(__file__).resolve().parent.parent.parent / "resources"
if _RESOURCES_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_RESOURCES_DIR)), name="static")


def store_dependency():
    return get_store()


_templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))
templates.env.globals["isinstance"] = isinstance


# ── Dashboard ──────────────────────────────────────────────────────────


@router.get("/")
async def index(request: Request, store: DataStore = Depends(store_dependency)):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "page": "index",
            "dancer_count": len(store.get_collection("dancers")),
            "team_count": len(store.get_collection("teams")),
            "class_count": len(store.get_collection("classes")),
            "instructor_count": len(store.get_collection("instructors")),
            "dance_count": len(store.get_collection("dances")),
            "recital_count": len(store.get_collection("recitals")),
            "studio_count": len(store.get_collection("studios")),
        },
    )


# ── Dancers ─────────────────────────────────────────────────────────────


@router.get("/dancers")
async def dancers(
    request: Request, q: str = None, store: DataStore = Depends(store_dependency)
):
    dancers_coll = store.get_collection("dancers")
    all_dancers = list(dancers_coll.values())
    teams = store.get_collection("teams")

    if q:
        all_dancers = [d for d in all_dancers if q.lower() in d.get("name", "").lower()]

    team_map = {tid: t["name"] for tid, t in teams.items()}
    for d in all_dancers:
        d["team_name"] = team_map.get(d.get("team_id"), "")
        class_ids = d.get("class_ids") or []
        if not isinstance(class_ids, list):
            class_ids = []
        d["class_count"] = len(class_ids)

    return templates.TemplateResponse(
        request,
        "dancers/list.html",
        {"request": request, "page": "dancers", "dancers": all_dancers, "query": q},
    )


@router.get("/dancers/new")
async def dancer_new(request: Request, store: DataStore = Depends(store_dependency)):
    teams = list(store.get_collection("teams").values())
    classes = list(store.get_collection("classes").values())
    return templates.TemplateResponse(
        request,
        "dancers/form.html",
        {
            "request": request,
            "page": "dancers",
            "teams": teams,
            "classes": classes,
            "dancer": None,
        },
    )


@router.get("/dancers/{dancer_id}")
async def dancer_detail(
    request: Request, dancer_id: str, store: DataStore = Depends(store_dependency)
):
    dancer = store.get("dancers", dancer_id)
    if not dancer:
        return HTMLResponse("Dancer not found", status_code=404)

    teams = store.get_collection("teams")
    team_map = {tid: t["name"] for tid, t in teams.items()}
    dancer["team_name"] = team_map.get(dancer.get("team_id"), "")

    classes = store.get_collection("classes")
    class_map = {cid: c["name"] for cid, c in classes.items()}

    dancer_classes = []
    for cid in dancer.get("class_ids", []):
        if cid in class_map:
            dancer_classes.append({"id": cid, "name": class_map[cid]})
    dancer["classes"] = dancer_classes

    return templates.TemplateResponse(
        request,
        "dancers/detail.html",
        {"request": request, "page": "dancers", "dancer": dancer},
    )


@router.get("/dancers/{dancer_id}/edit")
async def dancer_edit(
    request: Request, dancer_id: str, store: DataStore = Depends(store_dependency)
):
    dancer = store.get("dancers", dancer_id)
    if not dancer:
        return HTMLResponse("Dancer not found", status_code=404)

    teams = list(store.get_collection("teams").values())
    classes = list(store.get_collection("classes").values())
    return templates.TemplateResponse(
        request,
        "dancers/form.html",
        {
            "request": request,
            "page": "dancers",
            "teams": teams,
            "classes": classes,
            "dancer": dancer,
        },
    )


@router.post("/dancers")
async def dancer_create(request: Request, store: DataStore = Depends(store_dependency)):
    form = await request.form()
    name = form.get("name")
    class_id = form.get("class_ids")
    team_id = form.get("team_id")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    class_ids_list = [class_id] if class_id else []
    if not team_id:
        team_id = None

    dancer_id = make_dancer_id(name)
    dancer_data = {
        "id": dancer_id,
        "name": name,
        "class_ids": class_ids_list if class_ids_list else [],
        "team_id": team_id,
    }

    store.set("dancers", dancer_id, dancer_data)

    # Sync: add this dancer to each class's dancer_ids
    for cid in class_ids_list:
        cls = store.get("classes", cid)
        if cls:
            dancer_ids = list(cls.get("dancer_ids", []))
            if dancer_id not in dancer_ids:
                dancer_ids.append(dancer_id)
                cls["dancer_ids"] = dancer_ids
                store.set("classes", cid, cls)

    return RedirectResponse(url="/dancers", status_code=303)


@router.post("/dancers/{dancer_id}")
async def dancer_update(
    request: Request, dancer_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    class_id = form.get("class_ids")
    team_id = form.get("team_id")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    class_ids_list = [class_id] if class_id else []
    if not team_id:
        team_id = None

    # Remove this dancer from old classes' dancer_ids
    existing_dancer = store.get("dancers", dancer_id)
    if existing_dancer:
        for cid in existing_dancer.get("class_ids", []):
            cls = store.get("classes", cid)
            if cls:
                dancer_ids = list(cls.get("dancer_ids", []))
                if dancer_id in dancer_ids:
                    dancer_ids.remove(dancer_id)
                    cls["dancer_ids"] = dancer_ids
                    store.set("classes", cid, cls)

    dancer_data = {
        "id": dancer_id,
        "name": name,
        "class_ids": class_ids_list if class_ids_list else [],
        "team_id": team_id,
    }

    store.set("dancers", dancer_id, dancer_data)

    # Sync: add this dancer to new classes' dancer_ids
    for cid in class_ids_list:
        cls = store.get("classes", cid)
        if cls:
            dancer_ids = list(cls.get("dancer_ids", []))
            if dancer_id not in dancer_ids:
                dancer_ids.append(dancer_id)
                cls["dancer_ids"] = dancer_ids
                store.set("classes", cid, cls)

    return RedirectResponse(url="/dancers", status_code=303)


@router.delete("/dancers/{dancer_id}")
async def dancer_delete(
    request: Request, dancer_id: str, store: DataStore = Depends(store_dependency)
):
    store.delete("dancers", dancer_id)
    return RedirectResponse(url="/dancers", status_code=303)


# ── Teams ───────────────────────────────────────────────────────────────


@router.get("/teams")
async def teams_list(request: Request, store: DataStore = Depends(store_dependency)):
    teams_coll = store.get_collection("teams")
    dancers = list(store.get_collection("dancers").values())
    teams = [{"id": tid, **t} for tid, t in teams_coll.items()]
    for team in teams:
        dancer_ids = [d["id"] for d in dancers if d.get("team_id") == team["id"]]
        team["dancer_count"] = len(dancer_ids)
    return templates.TemplateResponse(
        request,
        "teams/list.html",
        {"request": request, "page": "teams", "teams": teams},
    )


@router.get("/teams/new")
async def team_new(request: Request, store: DataStore = Depends(store_dependency)):
    dancers = list(store.get_collection("dancers").values())
    return templates.TemplateResponse(
        request,
        "teams/form.html",
        {"request": request, "page": "teams", "dancers": dancers, "team": None},
    )


@router.get("/teams/{team_id}")
async def team_detail(
    request: Request, team_id: str, store: DataStore = Depends(store_dependency)
):
    team = store.get("teams", team_id)
    if not team:
        return HTMLResponse("Team not found", status_code=404)

    dancers = list(store.get_collection("dancers").values())
    team_dancers = [d for d in dancers if d.get("team_id") == team_id]

    return templates.TemplateResponse(
        request,
        "teams/detail.html",
        {"request": request, "page": "teams", "team": team, "dancers": team_dancers},
    )


@router.get("/teams/{team_id}/edit")
async def team_edit(
    request: Request, team_id: str, store: DataStore = Depends(store_dependency)
):
    team = store.get("teams", team_id)
    if not team:
        return HTMLResponse("Team not found", status_code=404)

    dancers = list(store.get_collection("dancers").values())
    return templates.TemplateResponse(
        request,
        "teams/form.html",
        {"request": request, "page": "teams", "dancers": dancers, "team": team},
    )


@router.post("/teams")
async def team_create(request: Request, store: DataStore = Depends(store_dependency)):
    form = await request.form()
    name = form.get("name")
    dancer_ids_list = form.getlist("dancer_ids")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    team_id = make_team_id(name)
    team_data = {
        "id": team_id,
        "name": name,
        "dancer_ids": dancer_ids_list,
    }

    store.set("teams", team_id, team_data)

    for did in dancer_ids_list:
        dancer = store.get("dancers", did)
        if dancer:
            dancer["team_id"] = team_id
            store.set("dancers", did, dancer)

    return RedirectResponse(url="/teams", status_code=303)


@router.post("/teams/{team_id}")
async def team_update(
    request: Request, team_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    dancer_ids_list = form.getlist("dancer_ids")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    team_data = {
        "id": team_id,
        "name": name,
        "dancer_ids": dancer_ids_list,
    }

    store.set("teams", team_id, team_data)

    dancers_coll = store.get_collection("dancers")
    for did in dancer_ids_list:
        if did in dancers_coll:
            dancer = store.get("dancers", did)
            if dancer:
                dancer["team_id"] = team_id
                store.set("dancers", did, dancer)
    for did in dancers_coll:
        d = store.get("dancers", did)
        if d and d.get("team_id") == team_id and did not in dancer_ids_list:
            d["team_id"] = None
            store.set("dancers", did, d)

    return RedirectResponse(url="/teams", status_code=303)


@router.delete("/teams/{team_id}")
async def team_delete(
    request: Request, team_id: str, store: DataStore = Depends(store_dependency)
):
    store.delete("teams", team_id)
    return RedirectResponse(url="/teams", status_code=303)


# ── Classes ─────────────────────────────────────────────────────────────


@router.get("/classes")
async def classes_list(request: Request, store: DataStore = Depends(store_dependency)):
    classes_coll = store.get_collection("classes")
    teams_coll = store.get_collection("teams")
    dancers = list(store.get_collection("dancers").values())
    classes = [{"id": cid, **c} for cid, c in classes_coll.items()]

    team_dancer_map = {}
    for t in teams_coll.values():
        tid = t["id"] if isinstance(t, dict) else t
        if isinstance(t, dict):
            tid = t.get("id")
        team_dancers = [d["id"] for d in dancers if d.get("team_id") == tid]
        team_dancer_map[tid] = len(team_dancers)

    for cls in classes:
        class_id = cls["id"]
        result = store.query(
            "SELECT COUNT(DISTINCT team_id) as cnt "
            "FROM class_team_assignments WHERE class_id = ?",
            (class_id,),
        )
        cls["team_count"] = result[0]["cnt"] if result else 0

    return templates.TemplateResponse(
        request,
        "classes/list.html",
        {"request": request, "page": "classes", "classes": classes},
    )


@router.get("/classes/new")
async def class_new(request: Request, store: DataStore = Depends(store_dependency)):
    instructors = list(store.get_collection("instructors").values())
    teams = list(store.get_collection("teams").values())
    return templates.TemplateResponse(
        request,
        "classes/form.html",
        {
            "request": request,
            "page": "classes",
            "instructors": instructors,
            "teams": teams,
            "class": None,
        },
    )


@router.get("/classes/{class_id}")
async def class_detail(
    request: Request, class_id: str, store: DataStore = Depends(store_dependency)
):
    class_obj = store.get("classes", class_id)
    if not class_obj:
        return HTMLResponse("Class not found", status_code=404)

    dancers = list(store.get_collection("dancers").values())
    class_dancers = [
        d for d in dancers if d.get("class_ids") and class_id in d.get("class_ids", [])
    ]

    return templates.TemplateResponse(
        request,
        "classes/detail.html",
        {
            "request": request,
            "page": "classes",
            "class": class_obj,
            "dancers": class_dancers,
        },
    )


@router.get("/classes/{class_id}/edit")
async def class_edit(
    request: Request, class_id: str, store: DataStore = Depends(store_dependency)
):
    class_obj = store.get("classes", class_id)
    if not class_obj:
        return HTMLResponse("Class not found", status_code=404)

    instructors = list(store.get_collection("instructors").values())
    teams = list(store.get_collection("teams").values())
    return templates.TemplateResponse(
        request,
        "classes/form.html",
        {
            "request": request,
            "page": "classes",
            "instructors": instructors,
            "teams": teams,
            "class": class_obj,
        },
    )


@router.post("/classes")
async def class_create(request: Request, store: DataStore = Depends(store_dependency)):
    form = await request.form()
    name = form.get("name")
    instructor_id = form.get("instructor_id")
    team_ids = form.getlist("team_ids")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    class_id = make_class_id(name)
    class_data = {
        "id": class_id,
        "name": name,
        "instructor_id": instructor_id if instructor_id else None,
        "team_ids": team_ids if team_ids else [],
        "dancer_ids": [],
    }

    store.set("classes", class_id, class_data)

    # Sync: add this class to all dancers in assigned teams
    for tid in team_ids:
        for did, dancer in store.get_collection("dancers").items():
            if dancer.get("team_id") == tid:
                class_ids = list(dancer.get("class_ids", []))
                if class_id not in class_ids:
                    class_ids.append(class_id)
                    dancer["class_ids"] = class_ids
                    store.set("dancers", did, dancer)

    # Sync: add this class to directly assigned dancers
    for did in class_data.get("dancer_ids", []):
        dancer = store.get("dancers", did)
        if dancer:
            class_ids = list(dancer.get("class_ids", []))
            if class_id not in class_ids:
                class_ids.append(class_id)
                dancer["class_ids"] = class_ids
                store.set("dancers", did, dancer)

    return RedirectResponse(url="/classes", status_code=303)


@router.post("/classes/{class_id}")
async def class_update(
    request: Request, class_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    instructor_id = form.get("instructor_id")
    team_ids = form.getlist("team_ids")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    # Remove this class from old teams' dancers' class_ids
    existing_class = store.get("classes", class_id)
    if existing_class:
        old_team_ids = existing_class.get("team_ids", [])
        for tid in old_team_ids:
            for did, dancer in store.get_collection("dancers").items():
                if dancer.get("team_id") == tid and class_id in dancer.get(
                    "class_ids", []
                ):
                    class_ids = list(dancer.get("class_ids", []))
                    class_ids.remove(class_id)
                    dancer["class_ids"] = class_ids
                    store.set("dancers", did, dancer)

    class_data = {
        "id": class_id,
        "name": name,
        "instructor_id": instructor_id if instructor_id else None,
        "team_ids": team_ids if team_ids else [],
        "dancer_ids": [],
    }

    store.set("classes", class_id, class_data)

    # Sync: add this class to all dancers in assigned teams
    for tid in team_ids:
        for did, dancer in store.get_collection("dancers").items():
            if dancer.get("team_id") == tid:
                class_ids = list(dancer.get("class_ids", []))
                if class_id not in class_ids:
                    class_ids.append(class_id)
                    dancer["class_ids"] = class_ids
                    store.set("dancers", did, dancer)

    # Sync: add this class to directly assigned dancers
    for did in class_data.get("dancer_ids", []):
        dancer = store.get("dancers", did)
        if dancer:
            class_ids = list(dancer.get("class_ids", []))
            if class_id not in class_ids:
                class_ids.append(class_id)
                dancer["class_ids"] = class_ids
                store.set("dancers", did, dancer)

    return RedirectResponse(url="/classes", status_code=303)


@router.delete("/classes/{class_id}")
async def class_delete(
    request: Request, class_id: str, store: DataStore = Depends(store_dependency)
):
    store.delete("classes", class_id)
    return RedirectResponse(url="/classes", status_code=303)


# ── Instructors ─────────────────────────────────────────────────────────


@router.get("/instructors")
async def instructors_list(
    request: Request, store: DataStore = Depends(store_dependency)
):
    instructors_coll = store.get_collection("instructors")
    classes = list(store.get_collection("classes").values())
    dances = list(store.get_collection("dances").values())
    instructors = [{"id": iid, **i} for iid, i in instructors_coll.items()]

    for instructor in instructors:
        inst_id = instructor["id"]
        class_count = len([c for c in classes if c.get("instructor_id") == inst_id])
        dance_count = len([d for d in dances if d.get("instructor_id") == inst_id])
        instructor["class_count"] = class_count
        instructor["dance_count"] = dance_count

    return templates.TemplateResponse(
        request,
        "instructors/list.html",
        {"request": request, "page": "instructors", "instructors": instructors},
    )


@router.get("/instructors/new")
async def instructor_new(
    request: Request, store: DataStore = Depends(store_dependency)
):
    classes = list(store.get_collection("classes").values())
    dances = list(store.get_collection("dances").values())
    return templates.TemplateResponse(
        request,
        "instructors/form.html",
        {
            "request": request,
            "page": "instructors",
            "classes": classes,
            "dances": dances,
            "instructor": None,
        },
    )


@router.get("/instructors/{instructor_id}")
async def instructor_detail(
    request: Request, instructor_id: str, store: DataStore = Depends(store_dependency)
):
    instructor = store.get("instructors", instructor_id)
    if not instructor:
        return HTMLResponse("Instructor not found", status_code=404)

    classes = list(store.get_collection("classes").values())
    instructor_classes = [c for c in classes if c.get("instructor_id") == instructor_id]

    dances = list(store.get_collection("dances").values())
    instructor_dances = [d for d in dances if d.get("instructor_id") == instructor_id]

    return templates.TemplateResponse(
        request,
        "instructors/detail.html",
        {
            "request": request,
            "page": "instructors",
            "instructor": instructor,
            "classes": instructor_classes,
            "dances": instructor_dances,
        },
    )


@router.get("/instructors/{instructor_id}/edit")
async def instructor_edit(
    request: Request, instructor_id: str, store: DataStore = Depends(store_dependency)
):
    instructor = store.get("instructors", instructor_id)
    if not instructor:
        return HTMLResponse("Instructor not found", status_code=404)

    classes = list(store.get_collection("classes").values())
    dances = list(store.get_collection("dances").values())
    return templates.TemplateResponse(
        request,
        "instructors/form.html",
        {
            "request": request,
            "page": "instructors",
            "classes": classes,
            "dances": dances,
            "instructor": instructor,
        },
    )


@router.post("/instructors")
async def instructor_create(
    request: Request, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    class_ids_list = form.getlist("class_ids")
    dance_ids_list = form.getlist("dance_ids")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    instructor_id = make_instructor_id(name)
    instructor_data = {
        "id": instructor_id,
        "name": name,
        "class_ids": class_ids_list if class_ids_list else [],
        "dance_ids": dance_ids_list if dance_ids_list else [],
    }

    store.set("instructors", instructor_id, instructor_data)

    classes_coll = store.get_collection("classes")
    for cid in class_ids_list:
        if cid in classes_coll:
            cls = store.get("classes", cid)
            if cls:
                cls["instructor_id"] = instructor_id
                store.set("classes", cid, cls)
    for cid in classes_coll:
        c = store.get("classes", cid)
        if c and c.get("instructor_id") == instructor_id and cid not in class_ids_list:
            c["instructor_id"] = None
            store.set("classes", cid, c)

    dances_coll = store.get_collection("dances")
    for did in dance_ids_list:
        if did in dances_coll:
            dance = store.get("dances", did)
            if dance:
                dance["instructor_id"] = instructor_id
                store.set("dances", did, dance)
    for did in dances_coll:
        d = store.get("dances", did)
        if d and d.get("instructor_id") == instructor_id and did not in dance_ids_list:
            d["instructor_id"] = None
            store.set("dances", did, d)

    return RedirectResponse(url="/instructors", status_code=303)


@router.post("/instructors/{instructor_id}")
async def instructor_update(
    request: Request, instructor_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    class_ids_list = form.getlist("class_ids")
    dance_ids_list = form.getlist("dance_ids")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    instructor_data = {
        "id": instructor_id,
        "name": name,
        "class_ids": class_ids_list if class_ids_list else [],
        "dance_ids": dance_ids_list if dance_ids_list else [],
    }

    store.set("instructors", instructor_id, instructor_data)

    classes_coll = store.get_collection("classes")
    for cid in class_ids_list:
        if cid in classes_coll:
            cls = store.get("classes", cid)
            if cls:
                cls["instructor_id"] = instructor_id
                store.set("classes", cid, cls)
    for cid in classes_coll:
        c = store.get("classes", cid)
        if c and c.get("instructor_id") == instructor_id and cid not in class_ids_list:
            c["instructor_id"] = None
            store.set("classes", cid, c)

    dances_coll = store.get_collection("dances")
    for did in dance_ids_list:
        if did in dances_coll:
            dance = store.get("dances", did)
            if dance:
                dance["instructor_id"] = instructor_id
                store.set("dances", did, dance)
    for did in dances_coll:
        d = store.get("dances", did)
        if d and d.get("instructor_id") == instructor_id and did not in dance_ids_list:
            d["instructor_id"] = None
            store.set("dances", did, d)

    return RedirectResponse(url="/instructors", status_code=303)


@router.delete("/instructors/{instructor_id}")
async def instructor_delete(
    request: Request, instructor_id: str, store: DataStore = Depends(store_dependency)
):
    store.delete("instructors", instructor_id)
    return RedirectResponse(url="/instructors", status_code=303)


# ── Dances ──────────────────────────────────────────────────────────────


@router.get("/dances")
async def dances_list(request: Request, store: DataStore = Depends(store_dependency)):
    dances_coll = store.get_collection("dances")
    dances = [{"id": did, **d} for did, d in dances_coll.items()]

    for dance in dances:
        dance_id = dance["id"]
        result = store.query(
            "SELECT COUNT(DISTINCT dancer_id) as cnt "
            "FROM dance_assignments WHERE dance_id = ?",
            (dance_id,),
        )
        dance["dancer_count"] = result[0]["cnt"] if result else 0

    return templates.TemplateResponse(
        request,
        "dances/list.html",
        {"request": request, "page": "dances", "dances": dances},
    )


@router.get("/dances/new")
async def dance_new(request: Request, store: DataStore = Depends(store_dependency)):
    instructors = list(store.get_collection("instructors").values())
    dancers = list(store.get_collection("dancers").values())
    teams = list(store.get_collection("teams").values())
    return templates.TemplateResponse(
        request,
        "dances/form.html",
        {
            "request": request,
            "page": "dances",
            "instructors": instructors,
            "dancers": dancers,
            "teams": teams,
            "dance": None,
        },
    )


@router.get("/dances/{dance_id}")
async def dance_detail(
    request: Request, dance_id: str, store: DataStore = Depends(store_dependency)
):
    dance = store.get("dances", dance_id)
    if not dance:
        return HTMLResponse("Dance not found", status_code=404)

    dancers_coll = store.get_collection("dancers")
    all_dancers = list(dancers_coll.values())

    result = store.query(
        "SELECT dancer_id FROM dance_assignments WHERE dance_id = ?", (dance_id,)
    )
    assigned_ids = {row["dancer_id"] for row in result} if result else set()
    dance_dancers = [d for d in all_dancers if d["id"] in assigned_ids]

    return templates.TemplateResponse(
        request,
        "dances/detail.html",
        {
            "request": request,
            "page": "dances",
            "dance": dance,
            "dancers": dance_dancers,
        },
    )


@router.get("/dances/{dance_id}/edit")
async def dance_edit(
    request: Request, dance_id: str, store: DataStore = Depends(store_dependency)
):
    dance = store.get("dances", dance_id)
    if not dance:
        return HTMLResponse("Dance not found", status_code=404)

    instructors = list(store.get_collection("instructors").values())
    dancers = list(store.get_collection("dancers").values())
    teams = list(store.get_collection("teams").values())
    return templates.TemplateResponse(
        request,
        "dances/form.html",
        {
            "request": request,
            "page": "dances",
            "instructors": instructors,
            "dancers": dancers,
            "teams": teams,
            "dance": dance,
        },
    )


@router.post("/dances")
async def dance_create(request: Request, store: DataStore = Depends(store_dependency)):
    form = await request.form()
    name = form.get("name")
    song_name = form.get("song_name")
    instructor_id = form.get("instructor_id")
    dancer_ids_list = form.getlist("dancer_ids")
    team_ids_list = form.getlist("team_ids")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    dance_id = make_dance_id(name)
    dance_data = {
        "id": dance_id,
        "name": name,
        "song_name": song_name,
        "instructor_id": instructor_id if instructor_id else None,
        "dancer_ids": dancer_ids_list,
        "team_ids": team_ids_list,
        "notes": "",
    }

    store.set("dances", dance_id, dance_data)
    return RedirectResponse(url="/dances", status_code=303)


@router.post("/dances/{dance_id}")
async def dance_update(
    request: Request, dance_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    song_name = form.get("song_name")
    instructor_id = form.get("instructor_id")
    dancer_ids_list = form.getlist("dancer_ids")
    team_ids_list = form.getlist("team_ids")
    notes = form.get("notes", "")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    dance_data = {
        "id": dance_id,
        "name": name,
        "song_name": song_name,
        "instructor_id": instructor_id if instructor_id else None,
        "dancer_ids": dancer_ids_list,
        "team_ids": team_ids_list,
        "notes": notes,
    }

    store.set("dances", dance_id, dance_data)
    return RedirectResponse(url="/dances", status_code=303)


@router.delete("/dances/{dance_id}")
async def dance_delete(
    request: Request, dance_id: str, store: DataStore = Depends(store_dependency)
):
    store.delete("dances", dance_id)
    return RedirectResponse(url="/dances", status_code=303)


# ── Recitals ────────────────────────────────────────────────────────────


@router.get("/recitals")
async def recitals_list(request: Request, store: DataStore = Depends(store_dependency)):
    recitals_coll = store.get_collection("recitals")
    recitals = [{"id": rid, **r} for rid, r in recitals_coll.items()]
    return templates.TemplateResponse(
        request,
        "recitals/list.html",
        {"request": request, "page": "recitals", "recitals": recitals},
    )


@router.get("/recitals/new")
async def recital_new(request: Request, store: DataStore = Depends(store_dependency)):
    dances = list(store.get_collection("dances").values())
    return templates.TemplateResponse(
        request,
        "recitals/form.html",
        {"request": request, "page": "recitals", "dances": dances, "recital": None},
    )


@router.get("/recitals/{recital_id}")
async def recital_detail(
    request: Request, recital_id: str, store: DataStore = Depends(store_dependency)
):
    recital = store.get("recitals", recital_id)
    if not recital:
        return HTMLResponse("Recital not found", status_code=404)

    return templates.TemplateResponse(
        request,
        "recitals/detail.html",
        {
            "request": request,
            "page": "recitals",
            "recital": recital,
            "recital_id": recital_id,
        },
    )


@router.get("/recitals/{recital_id}/schedule")
async def recital_schedule(
    request: Request, recital_id: str, store: DataStore = Depends(store_dependency)
):
    recital = store.get("recitals", recital_id)
    if not recital:
        return HTMLResponse("Recital not found", status_code=404)

    dances_coll = store.get_collection("dances")
    order = recital.get("performance_order", [])
    dance_ids = (
        [s["dance_id"] for s in order]
        if isinstance(order, list)
        and len(order) > 0
        and isinstance(order[0], dict)
        and "dance_id" in order[0]
        else ([s for s in order]) if isinstance(order, list) and len(order) > 0 else []
    )

    schedule = None
    errors = []

    if len(dance_ids) >= 2:
        dancer_dances = {}
        for did in dance_ids:
            dance = dances_coll.get(did)
            if dance:
                for dancer_id in dance.get("dancer_ids", []):
                    if dancer_id not in dancer_dances:
                        dancer_dances[dancer_id] = []
                    dancer_dances[dancer_id].append(did)

        result = greedy_schedule(dance_ids, dancer_dances, 4)
        if result:
            schedule = []
            for i, did in enumerate(result):
                dance = dances_coll.get(did)
                if dance:
                    dancers = []
                    for dancer_id in dance.get("dancer_ids", []):
                        d = store.get("dancers", dancer_id)
                        if d:
                            dancers.append(
                                {"id": dancer_id, "name": d.get("name", dancer_id)}
                            )
                    slot_entry = {
                        "position": i + 1,
                        "dance_id": did,
                        "dance_name": dance.get("name", ""),
                        "song_name": dance.get("song_name", ""),
                        "dancers": dancers,
                        "buffer_notes": "",
                    }
                    schedule.append(slot_entry)

        else:
            errors.append("Could not generate a valid schedule.")

    return templates.TemplateResponse(
        request,
        "recitals/schedule.html",
        {
            "request": request,
            "page": "recitals",
            "recital": recital,
            "schedule": schedule,
            "errors": errors,
        },
    )


@router.get("/recitals/{recital_id}/schedule-generate")
async def recital_schedule_generate(
    request: Request, recital_id: str, store: DataStore = Depends(store_dependency)
):
    recital = store.get("recitals", recital_id)
    if not recital:
        return HTMLResponse("Recital not found", status_code=404)

    dances_coll = store.get_collection("dances")
    order = recital.get("performance_order", [])
    dance_ids = (
        [s["dance_id"] for s in order]
        if isinstance(order, list)
        and len(order) > 0
        and isinstance(order[0], dict)
        and "dance_id" in order[0]
        else ([s for s in order]) if isinstance(order, list) and len(order) > 0 else []
    )

    if len(dance_ids) < 2:
        msg = (
            '<div class="toast error">'
            "Need at least 2 dances to generate a schedule.</div>"
        )
        return HTMLResponse(msg, status_code=400)

    dancer_dances = {}
    for did in dance_ids:
        dance = dances_coll.get(did)
        if dance:
            for dancer_id in dance.get("dancer_ids", []):
                if dancer_id not in dancer_dances:
                    dancer_dances[dancer_id] = []
                dancer_dances[dancer_id].append(did)

    result = greedy_schedule(dance_ids, dancer_dances, 4)
    if result is None:
        return HTMLResponse(
            '<div class="toast error">Could not generate a valid schedule.</div>',
            status_code=500,
        )

    recital["performance_order"] = [
        {"dance_id": did, "position": i + 1} for i, did in enumerate(result)
    ]
    store.set("recitals", recital_id, recital)

    return RedirectResponse(
        url=f"/recitals/{recital_id}/schedule",
        status_code=303,
    )


@router.get("/recitals/{recital_id}/edit")
async def recital_edit(
    request: Request, recital_id: str, store: DataStore = Depends(store_dependency)
):
    recital = store.get("recitals", recital_id)
    if not recital:
        return HTMLResponse("Recital not found", status_code=404)
    dances = list(store.get_collection("dances").values())
    return templates.TemplateResponse(
        request,
        "recitals/form.html",
        {"request": request, "page": "recitals", "recital": recital, "dances": dances},
    )


@router.post("/recitals")
async def recital_create(
    request: Request, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    performance_order = form.get("performance_order", "")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    try:
        dance_ids = json.loads(performance_order) if performance_order else []
    except (json.JSONDecodeError, TypeError):
        dance_ids = [p.strip() for p in performance_order.split(",") if p.strip()]

    recital_id = make_recital_id(name)
    recital_data = {
        "id": recital_id,
        "name": name,
        "performance_order": [
            {"dance_id": did, "position": i + 1} for i, did in enumerate(dance_ids)
        ],
        "notes": "",
    }

    store.set("recitals", recital_id, recital_data)
    return RedirectResponse(url="/recitals", status_code=303)


@router.post("/recitals/{recital_id}")
async def recital_update(
    request: Request, recital_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    performance_order = form.get("performance_order", "")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    try:
        dance_ids = json.loads(performance_order) if performance_order else []
    except (json.JSONDecodeError, TypeError):
        dance_ids = [p.strip() for p in performance_order.split(",") if p.strip()]

    recital_data = {
        "id": recital_id,
        "name": name,
        "performance_order": [
            {"dance_id": did, "position": i + 1} for i, did in enumerate(dance_ids)
        ],
        "notes": "",
    }

    store.set("recitals", recital_id, recital_data)
    return RedirectResponse(url="/recitals", status_code=303)


@router.delete("/recitals/{recital_id}")
async def recital_delete(
    request: Request, recital_id: str, store: DataStore = Depends(store_dependency)
):
    store.delete("recitals", recital_id)
    return RedirectResponse(url="/recitals", status_code=303)


# ── Studios ─────────────────────────────────────────────────────────────


@router.get("/studios")
async def studios_list(
    request: Request, q: str = None, store: DataStore = Depends(store_dependency)
):
    studios_coll = store.get_collection("studios")
    studios = [{"id": sid, **s} for sid, s in studios_coll.items()]

    # Extract equipment from extra column and count reservations
    import json as _json

    for studio in studios:
        extra = studio.get("extra") or {}
        if isinstance(extra, str):
            try:
                extra = _json.loads(extra)
            except (json.JSONDecodeError, TypeError):
                extra = {}
        studio["equipment"] = extra.get("equipment", [])

        schedule = studio.get("schedule", [])
        if not isinstance(schedule, list):
            try:
                schedule = _json.loads(schedule)
            except (json.JSONDecodeError, TypeError):
                schedule = []
        studio["reservation_count"] = len(schedule)

    # Filter by search query
    if q:
        studios = [s for s in studios if q.lower() in s.get("name", "").lower()]

    return templates.TemplateResponse(
        request,
        "studios/list.html",
        {"request": request, "page": "studios", "studios": studios, "query": q},
    )


@router.get("/studios/new")
async def studio_new(request: Request, store: DataStore = Depends(store_dependency)):
    classes = list(store.get_collection("classes").values())
    return templates.TemplateResponse(
        request,
        "studios/form.html",
        {"request": request, "page": "studios", "classes": classes, "studio": None},
    )


@router.get("/studios/{studio_id}")
async def studio_detail(
    request: Request, studio_id: str, store: DataStore = Depends(store_dependency)
):
    studio = store.get("studios", studio_id)
    if not studio:
        return HTMLResponse("Studio not found", status_code=404)

    import json as _json

    # Extract equipment from extra column
    extra = studio.get("extra") or {}
    if isinstance(extra, str):
        try:
            extra = _json.loads(extra)
        except (json.JSONDecodeError, TypeError):
            extra = {}
    studio["equipment"] = extra.get("equipment", [])

    # Get schedule with resolved names
    schedule = get_studio_schedule(studio_id)
    classes_coll = store.get_collection("classes")
    dancers_coll = store.get_collection("dancers")
    instructors_coll = store.get_collection("instructors")

    for slot in schedule:
        reserved_by = slot.get("reserved_by", "")
        res_type = slot.get("reservation_type", "")
        if reserved_by and res_type == "class":
            cls = classes_coll.get(reserved_by)
            if cls:
                slot["resolved_name"] = cls.get("name", reserved_by)
        elif reserved_by and res_type == "individual":
            dancer = dancers_coll.get(reserved_by)
            if dancer:
                slot["resolved_name"] = dancer.get("name", reserved_by)
            else:
                instructor = instructors_coll.get(reserved_by)
                if instructor:
                    slot["resolved_name"] = instructor.get("name", reserved_by)
                else:
                    slot["resolved_name"] = reserved_by
        else:
            slot["resolved_name"] = reserved_by or "Unknown"

        start_time = slot.get("start_time", "")
        end_time = slot.get("end_time", "")
        if start_time and ":" in start_time:
            slot["formatted_start_time"] = _format_time_12h(start_time)
        else:
            slot["formatted_start_time"] = start_time or ""
        if end_time and ":" in end_time:
            slot["formatted_end_time"] = _format_time_12h(end_time)
        else:
            slot["formatted_end_time"] = end_time or ""

    return templates.TemplateResponse(
        request,
        "studios/detail.html",
        {
            "request": request,
            "page": "studios",
            "studio": studio,
            "schedule": schedule,
        },
    )


@router.get("/studios/{studio_id}/edit")
async def studio_edit(
    request: Request, studio_id: str, store: DataStore = Depends(store_dependency)
):
    studio = store.get("studios", studio_id)
    if not studio:
        return HTMLResponse("Studio not found", status_code=404)

    classes = list(store.get_collection("classes").values())
    return templates.TemplateResponse(
        request,
        "studios/form.html",
        {
            "request": request,
            "page": "studios",
            "classes": classes,
            "studio": studio,
        },
    )


@router.post("/studios")
async def studio_create(request: Request, store: DataStore = Depends(store_dependency)):
    form = await request.form()
    name = form.get("name")
    location = form.get("location", "") or ""
    capacity_str = form.get("capacity", "20")

    try:
        capacity = int(capacity_str) if capacity_str else 20
    except (ValueError, TypeError):
        capacity = 20

    equipment_str = form.get("equipment", "")
    equipment = (
        [e.strip() for e in equipment_str.split(",") if e.strip()]
        if equipment_str
        else []
    )

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    studio_id = make_studio_id(name)
    extra_fields = {}
    if equipment:
        extra_fields["equipment"] = equipment

    store.execute(
        "INSERT OR REPLACE INTO studios "
        "(id, name, location, capacity, schedule, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (studio_id, title(name), location, capacity, "[]", ""),
    )

    if extra_fields:
        import json as _json

        store.execute(
            "UPDATE studios SET extra = ? WHERE id = ?",
            (_json.dumps(extra_fields), studio_id),
        )

    store.save()
    return RedirectResponse(url="/studios", status_code=303)


@router.post("/studios/{studio_id}")
async def studio_update(
    request: Request, studio_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    location = form.get("location", "") or ""
    capacity_str = form.get("capacity", "20")

    try:
        capacity = int(capacity_str) if capacity_str else 20
    except (ValueError, TypeError):
        capacity = 20

    equipment_str = form.get("equipment", "")
    equipment = (
        [e.strip() for e in equipment_str.split(",") if e.strip()]
        if equipment_str
        else []
    )

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    studio_data = {
        "id": studio_id,
        "name": title(name),
        "location": location,
        "capacity": capacity,
    }

    store.set("studios", studio_id, studio_data)

    # Update equipment in extra column
    import json as _json

    extra = studio_data.get("extra") or {}
    if isinstance(extra, str):
        try:
            extra = _json.loads(extra)
        except (json.JSONDecodeError, TypeError):
            extra = {}
    extra["equipment"] = equipment
    store.execute(
        "UPDATE studios SET extra = ? WHERE id = ?",
        (_json.dumps(extra), studio_id),
    )

    return RedirectResponse(url="/studios", status_code=303)


@router.delete("/studios/{studio_id}")
async def studio_delete(
    request: Request, studio_id: str, store: DataStore = Depends(store_dependency)
):
    store.delete("studios", studio_id)
    return RedirectResponse(url="/studios", status_code=303)


@router.post("/studios/{studio_id}/reserve")
async def studio_reserve(
    request: Request, studio_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    date = form.get("date", "")
    start_time = form.get("start_time", "")
    end_time = form.get("end_time", "")
    reservation_type = form.get("reservation_type", "individual")
    reservation_id = form.get("reservation_id", "")

    if not all([date, start_time, end_time]):
        return RedirectResponse(url=f"/studios/{studio_id}", status_code=303)

    success = _reserve_slot(
        studio_id=studio_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        reservation_type=reservation_type,
        reservation_id=reservation_id,
    )

    if not success:
        return RedirectResponse(url=f"/studios/{studio_id}", status_code=303)

    return RedirectResponse(url=f"/studios/{studio_id}", status_code=303)


@router.post("/studios/{studio_id}/cancel")
async def studio_cancel_reservation(
    request: Request, studio_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    date = form.get("date", "")
    start_time = form.get("start_time", "")
    end_time = form.get("end_time", "")
    reservation_id = form.get("reservation_id", "")

    _cancel_reservation(
        studio_id=studio_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        reservation_id=reservation_id,
    )

    return RedirectResponse(url=f"/studios/{studio_id}", status_code=303)


app.include_router(router)
