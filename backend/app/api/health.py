from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import PyMongoError

from app.database import MongoDatabase, get_database

router = APIRouter()


@router.get("/health")
async def get_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def get_database_health(
    database: MongoDatabase = Depends(get_database),
) -> dict[str, str]:
    try:
        database.ping()
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        ) from None

    return {"status": "ok"}
