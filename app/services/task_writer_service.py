import uuid as uuid_module
from app.database.main_db_connection import get_main_pool, acquire_healthy_connection
from app.database.queries.task_queries import (
    INSERT_TASK,
    INSERT_TASK_STATUS_HISTORY
)
from app.database.queries.disaster_event_queries import (
    GET_DISASTER_EVENT_BY_ID,
    UPDATE_DISASTER_EVENT_AFTER_ANALYSIS
)
from app.models.output_models import PrecautionPlan
from app.core.logger import setup_logger
from app.core.exceptions import TaskWriteError

logger = setup_logger(__name__)

# Mapping from LLM-generated values to actual DB enum values
# DB risk_level: ['low', 'medium', 'high', 'critical']
_RISK_LEVEL_MAP = {
    "low": "low",
    "medium": "medium",
    "moderate": "medium",
    "high": "high",
    "extreme": "critical",
    "critical": "critical",
    "very_high": "critical",
}

# DB task_type: ['ambulance', 'boat', 'medical', 'food', 'evacuation', 'shelter']
_TASK_TYPE_MAP = {
    "ambulance": "ambulance",
    "ambulance_dispatch": "ambulance",
    "boat": "boat",
    "rescue_boat": "boat",
    "boat_rescue": "boat",
    "medical": "medical",
    "medical_supply": "medical",
    "field_hospital": "medical",
    "health": "medical",
    "disease_prevention": "medical",
    "food": "food",
    "food_supply": "food",
    "food_water": "food",
    "water": "food",
    "nutrition": "food",
    "evacuation": "evacuation",
    "search_and_rescue": "evacuation",
    "search_rescue": "evacuation",
    "life_safety": "evacuation",
    "rescue": "evacuation",
    "shelter": "shelter",
    "tent": "shelter",
    "housing": "shelter",
    "blanket": "shelter",
    # Catch-all categories mapped to closest match
    "equipment": "evacuation",
    "communication": "evacuation",
    "infrastructure": "evacuation",
    "logistics": "evacuation",
    "vulnerable_population": "shelter",
    "protection": "shelter",
    "recovery": "shelter",
    "general": "evacuation",
}

# DB task_priority: ['low', 'medium', 'high', 'critical']
_PRIORITY_MAP = {
    "low": "low",
    "medium": "medium",
    "moderate": "medium",
    "high": "high",
    "critical": "critical",
    "urgent": "critical",
    "extreme": "critical",
    "very_high": "critical",
    "p1": "critical",
    "p2": "high",
    "p3": "medium",
    "p4": "low",
}


def _normalize_risk_level(risk_level: str) -> str:
    """Maps LLM risk_level to DB enum value."""
    return _RISK_LEVEL_MAP.get(risk_level.lower().strip(), "high")


def _normalize_task_type(task_type: str) -> str:
    """Maps LLM task_type_for_db to DB enum value."""
    key = task_type.lower().strip().replace(" ", "_").replace("-", "_")
    return _TASK_TYPE_MAP.get(key, "evacuation")


def _normalize_priority(priority: str) -> str:
    """Maps LLM priority_level_for_db to DB enum value."""
    return _PRIORITY_MAP.get(priority.lower().strip(), "medium")


async def write_tasks_to_database(
    plan: PrecautionPlan,
    longitude: float,
    latitude: float,
) -> list[str]:
    """
    Writes all prioritized actions as individual tasks in the database.
    Updates the parent disaster event with the precaution summary.
    Normalizes all enum values before inserting.
    Uses acquire_healthy_connection to handle stale PgBouncer connections.
    """
    pool = get_main_pool()
    task_ids = []

    # Convert string event_id to UUID for asyncpg
    event_uuid = uuid_module.UUID(plan.disaster_event_id)

    conn = None
    try:
        conn = await acquire_healthy_connection(pool)
        async with conn.transaction():
            # 1. Create each task from the plan's actions
            for action in plan.prioritized_actions:
                task_id_row = await conn.fetchrow(
                    INSERT_TASK,
                    event_uuid,                                     # $1 (uuid)
                    action.action_title,                            # $2
                    action.action_detail,                           # $3
                    _normalize_task_type(action.task_type_for_db),  # $4 (task_type enum)
                    action.quantity_required,                        # $5
                    _normalize_priority(action.priority_level_for_db),  # $6 (task_priority enum)
                    longitude,                                      # $7
                    latitude,                                       # $8
                    plan.district,                                  # $9
                    action.estimated_duration_hours                  # $10
                )
                
                if not task_id_row:
                    raise TaskWriteError(f"Failed to retrieve task_id for action: {action.action_title}")
                
                task_id_uuid = task_id_row["task_id"]
                task_ids.append(str(task_id_uuid))

                await conn.execute(
                    INSERT_TASK_STATUS_HISTORY,
                    task_id_uuid  # $1 (uuid)
                )

            # 2. Update the parent disaster event record
            await conn.execute(
                UPDATE_DISASTER_EVENT_AFTER_ANALYSIS,
                event_uuid,                                     # $1 (uuid)
                plan.precautions_summary_array,                  # $2
                plan.estimated_damage_pkr,                       # $3
                _normalize_risk_level(plan.risk_level),          # $4 (risk_level enum)
                plan.estimated_population_affected               # $5
            )

        logger.info(f"Successfully created {len(task_ids)} tasks for event {plan.disaster_event_id}")
        return task_ids

    except TaskWriteError:
        raise
    except Exception as e:
        logger.error(f"Error while writing tasks to database: {str(e)}")
        raise TaskWriteError(f"Database transaction failed: {str(e)}")
    finally:
        if conn:
            await pool.release(conn)


async def verify_event_exists(disaster_event_id: str) -> bool:
    """
    Checks if the specified disaster event exists in the main database.
    Uses acquire_healthy_connection to avoid stale connection errors.
    """
    pool = get_main_pool()
    conn = None
    try:
        event_uuid = uuid_module.UUID(disaster_event_id)
        conn = await acquire_healthy_connection(pool)
        row = await conn.fetchrow(GET_DISASTER_EVENT_BY_ID, event_uuid)
        exists = row is not None
        logger.info(f"Disaster event verification for {disaster_event_id}: {'Found' if exists else 'Not Found'}")
        return exists
    except ValueError:
        logger.error(f"Invalid UUID format for disaster_event_id: {disaster_event_id}")
        return False
    except Exception as e:
        logger.error(f"Error verifying event exists: {str(e)}")
        return False
    finally:
        if conn:
            await pool.release(conn)
