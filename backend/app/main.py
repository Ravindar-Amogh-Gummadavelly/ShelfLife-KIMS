from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI

from app.database import MongoDatabase
from app.api.health import router as health_router


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
