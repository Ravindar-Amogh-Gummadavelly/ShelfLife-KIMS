from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.households import router as households_router
from app.database import MongoDatabase


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
