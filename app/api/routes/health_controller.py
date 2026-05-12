import time
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.core.logger import setup_logger
from app.database.main_db_connection import get_main_pool
from app.database.collection_db_connection import get_collection_pool

logger = setup_logger(__name__)
router = APIRouter(tags=["Health"])

# Track service start time
_start_time = time.time()


@router.get("/health")
async def health_check():
    """
    Performs health checks on the service and its database connections.
    """
    main_db_connected = False
    collection_db_connected = False
    main_db_error = None
    collection_db_error = None

    # 1. Check Main Database
    try:
        pool = get_main_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        main_db_connected = True
    except Exception as e:
        main_db_error = str(e)
        logger.error(f"Health Check: Main DB Connection Failed: {main_db_error}")

    # 2. Check Collection Database
    try:
        pool = get_collection_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        collection_db_connected = True
    except Exception as e:
        collection_db_error = str(e)
        logger.error(f"Health Check: Collection DB Connection Failed: {collection_db_error}")

    status = "healthy" if main_db_connected and collection_db_connected else "degraded"
    
    return {
        "status": status,
        "service": settings.service_name,
        "environment": settings.app_env,
        "uptime_seconds": round(time.time() - _start_time, 2),
        "main_database_connected": main_db_connected,
        "collection_database_connected": collection_db_connected,
        "main_database_error": main_db_error,
        "collection_database_error": collection_db_error,
        "model": settings.openai_model,
        "agent_ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
