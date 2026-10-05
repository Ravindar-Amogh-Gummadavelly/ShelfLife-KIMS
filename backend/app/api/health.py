import logging

from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import PyMongoError

from app.database import MongoDatabase, get_database

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def get_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def get_database_health(
    database: MongoDatabase = Depends(get_database),
) -> dict[str, str]:
    try:
        database.ping()
    except PyMongoError as error:
        logger.warning(
            "MongoDB health ping failed (%s)",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        ) from None

    return {"status": "ok"}
