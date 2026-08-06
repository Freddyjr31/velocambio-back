from typing import Annotated

from fastapi  import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from core.database import get_db
from core.logger import logger
from core.config import VERSION
from core.rate_limit import limiter

router = APIRouter(
    tags=["Health"],
)

@router.get("/health", status_code=status.HTTP_200_OK)
@limiter.exempt
async def health_check(db: Annotated[Session, Depends(get_db)]):
    
    try:
        db.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        db_status = "disconnected"
    
    return {
        "status": "OK" if db_status == "connected" else "ERROR",
        "database": db_status,
        "version": VERSION
    }
