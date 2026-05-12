import json
import uuid as uuid_module
from agents import function_tool
from app.database.main_db_connection import get_main_pool, acquire_healthy_connection
from app.database.queries.task_queries import (
    GET_EXISTING_TASKS_FOR_EVENT,
    GET_TASK_COUNT_FOR_EVENT
)
from app.core.logger import setup_logger

logger = setup_logger(__name__)


async def get_existing_tasks_for_event_logic(
    disaster_event_id: str,
) -> dict:
    """Core logic for retrieving existing tasks."""
    pool = get_main_pool()

    # Convert string to UUID for asyncpg
    event_uuid = uuid_module.UUID(disaster_event_id)

    conn = await acquire_healthy_connection(pool)
    try:
        # 1. Get task count
        count_row = await conn.fetchrow(GET_TASK_COUNT_FOR_EVENT, event_uuid)
        count = count_row["task_count"] if count_row else 0

        # 2. Get detailed tasks
        task_rows = await conn.fetch(GET_EXISTING_TASKS_FOR_EVENT, event_uuid)
        existing_tasks = [dict(row) for row in task_rows]
        
        # 3. Identify covered types
        covered_types = list(set(task["task_type"] for task in existing_tasks))

        return {
            "existing_task_count": count,
            "existing_tasks": existing_tasks,
            "covered_task_types": covered_types,
            "message": "No existing tasks. Create all." if count == 0 else f"{count} tasks exist. Only create gaps not already covered."
        }
    finally:
        await pool.release(conn)


@function_tool
async def get_existing_tasks_for_event(
  disaster_event_id: str,
) -> str:
    """
    Reads the tasks table to find all tasks already created for this 
    disaster event. Call this STEP 2 of workflow.
    """
    try:
        res = await get_existing_tasks_for_event_logic(disaster_event_id)
        return json.dumps(res, default=str)
    except Exception as e:
        logger.error(f"Error in get_existing_tasks_for_event: {str(e)}")
        return json.dumps({"error": str(e)})
