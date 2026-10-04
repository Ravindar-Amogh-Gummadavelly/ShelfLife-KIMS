from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.households import router as households_router
from app.api.inventory import router as inventory_router
from app.database import MongoDatabase

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    application.state.database = None
    application.state.database_lock = Lock()
    try:
        yield
    finally:
        database: MongoDatabase | None = application.state.database
        if database is not None:
            database.close()
            application.state.database = None


app = FastAPI(title="ShelfLife API", lifespan=lifespan)
app.include_router(health_router, prefix="/api")
app.include_router(households_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")

FRONTEND_ASSETS = FRONTEND_DIST / "assets"
if FRONTEND_ASSETS.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_ASSETS),
        name="frontend-assets",
    )


@app.get("/", include_in_schema=False, response_class=FileResponse)
def serve_frontend() -> FileResponse:
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Frontend build is not available",
        )
    return FileResponse(index_file)
