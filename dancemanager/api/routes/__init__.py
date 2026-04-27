"""API routes initialization."""

from dancemanager.api.routes.dancers import router as dancers_router
from dancemanager.api.routes.teams import router as teams_router
from dancemanager.api.routes.classes import router as classes_router
from dancemanager.api.routes.instructors import router as instructors_router
from dancemanager.api.routes.dances import router as dances_router
from dancemanager.api.routes.recitals import router as recitals_router
from dancemanager.api.routes.import_export import router as import_export_router
from dancemanager.api.routes.studios import router as studios_router
