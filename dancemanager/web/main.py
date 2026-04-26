"""Web application for Dance Manager."""

from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dancemanager.store import DataStore, get_store
from dancemanager.models import (
    make_dancer_id,
    make_team_id,
    make_class_id,
    make_instructor_id,
    make_dance_id,
    make_recital_id,
)
from dancemanager.recital import greedy_schedule

app = FastAPI()
router = APIRouter()


def store_dependency():
    return get_store()


_templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


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

    dancer_data = {
        "id": dancer_id,
        "name": name,
        "class_ids": class_ids_list if class_ids_list else [],
        "team_id": team_id,
    }

    store.set("dancers", dancer_id, dancer_data)
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
    teams = [{"id": tid, **t} for tid, t in teams_coll.items()]
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
    classes = [{"id": cid, **c} for cid, c in classes_coll.items()]
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
    team_ids = form.get("team_ids", "")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    team_ids_list = [t.strip() for t in team_ids.split(",") if t.strip()]

    class_id = make_class_id(name)
    class_data = {
        "id": class_id,
        "name": name,
        "instructor_id": instructor_id if instructor_id else None,
        "team_ids": team_ids_list if team_ids_list else [],
        "dancer_ids": [],
    }

    store.set("classes", class_id, class_data)
    return RedirectResponse(url="/classes", status_code=303)


@router.post("/classes/{class_id}")
async def class_update(
    request: Request, class_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    instructor_id = form.get("instructor_id")
    team_ids = form.get("team_ids", "")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    team_ids_list = [t.strip() for t in team_ids.split(",") if t.strip()]

    class_data = {
        "id": class_id,
        "name": name,
        "instructor_id": instructor_id if instructor_id else None,
        "team_ids": team_ids_list if team_ids_list else [],
        "dancer_ids": [],
    }

    store.set("classes", class_id, class_data)
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
    instructors = [{"id": iid, **i} for iid, i in instructors_coll.items()]
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
    class_ids = form.get("class_ids", "")
    dance_ids = form.get("dance_ids", "")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    class_ids_list = [c.strip() for c in class_ids.split(",") if c.strip()]
    dance_ids_list = [d.strip() for d in dance_ids.split(",") if d.strip()]

    instructor_id = make_instructor_id(name)
    instructor_data = {
        "id": instructor_id,
        "name": name,
        "class_ids": class_ids_list if class_ids_list else [],
        "dance_ids": dance_ids_list if dance_ids_list else [],
    }

    store.set("instructors", instructor_id, instructor_data)
    return RedirectResponse(url="/instructors", status_code=303)


@router.post("/instructors/{instructor_id}")
async def instructor_update(
    request: Request, instructor_id: str, store: DataStore = Depends(store_dependency)
):
    form = await request.form()
    name = form.get("name")
    class_ids = form.get("class_ids", "")
    dance_ids = form.get("dance_ids", "")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    class_ids_list = [c.strip() for c in class_ids.split(",") if c.strip()]
    dance_ids_list = [d.strip() for d in dance_ids.split(",") if d.strip()]

    instructor_data = {
        "id": instructor_id,
        "name": name,
        "class_ids": class_ids_list if class_ids_list else [],
        "dance_ids": dance_ids_list if dance_ids_list else [],
    }

    store.set("instructors", instructor_id, instructor_data)
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
    return templates.TemplateResponse(
        request,
        "dances/list.html",
        {"request": request, "page": "dances", "dances": dances},
    )


@router.get("/dances/new")
async def dance_new(request: Request, store: DataStore = Depends(store_dependency)):
    instructors = list(store.get_collection("instructors").values())
    dancers = list(store.get_collection("dancers").values())
    return templates.TemplateResponse(
        request,
        "dances/form.html",
        {
            "request": request,
            "page": "dances",
            "instructors": instructors,
            "dancers": dancers,
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

    dancers = list(store.get_collection("dancers").values())
    dance_dancers = [d for d in dancers if dance_id in d.get("dancer_ids", [])]

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
    return templates.TemplateResponse(
        request,
        "dances/form.html",
        {
            "request": request,
            "page": "dances",
            "instructors": instructors,
            "dancers": dancers,
            "dance": dance,
        },
    )


@router.post("/dances")
async def dance_create(request: Request, store: DataStore = Depends(store_dependency)):
    form = await request.form()
    name = form.get("name")
    song_name = form.get("song_name")
    instructor_id = form.get("instructor_id")
    dancer_ids = form.get("dancer_ids", "")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    dancer_ids_list = [d.strip() for d in dancer_ids.split(",") if d.strip()]

    dance_id = make_dance_id(name)
    dance_data = {
        "id": dance_id,
        "name": name,
        "song_name": song_name,
        "instructor_id": instructor_id if instructor_id else None,
        "dancer_ids": dancer_ids_list if dancer_ids_list else [],
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
    dancer_ids = form.get("dancer_ids", "")
    notes = form.get("notes", "")

    if not name:
        return HTMLResponse("Name is required", status_code=400)

    dancer_ids_list = [d.strip() for d in dancer_ids.split(",") if d.strip()]

    dance_data = {
        "id": dance_id,
        "name": name,
        "song_name": song_name,
        "instructor_id": instructor_id if instructor_id else None,
        "dancer_ids": dancer_ids_list if dancer_ids_list else [],
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
        {"request": request, "page": "recitals", "recital": recital},
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
        if isinstance(order, list) and len(order) > 0 and isinstance(order[0], dict) and "dance_id" in order[0]
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
        if isinstance(order, list) and len(order) > 0 and isinstance(order[0], dict) and "dance_id" in order[0]
        else ([s for s in order]) if isinstance(order, list) and len(order) > 0 else []
    )

    if len(dance_ids) < 2:
        return HTMLResponse(
            '<div class="toast error">Need at least 2 dances to generate a schedule.</div>',
            status_code=400,
        )

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
    return templates.TemplateResponse(
        request,
        "recitals/form.html",
        {"request": request, "page": "recitals", "recital": recital},
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

    performance_order_list = [
        p.strip() for p in performance_order.split(",") if p.strip()
    ]

    recital_id = make_recital_id(name)
    recital_data = {
        "id": recital_id,
        "name": name,
        "performance_order": performance_order_list if performance_order_list else [],
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

    performance_order_list = [
        p.strip() for p in performance_order.split(",") if p.strip()
    ]

    recital_data = {
        "id": recital_id,
        "name": name,
        "performance_order": performance_order_list if performance_order_list else [],
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


app.include_router(router)
