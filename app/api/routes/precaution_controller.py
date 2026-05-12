import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from agents import Runner

from app.models.input_models import PrecautionTriggerPayload
from app.models.output_models import PrecautionPlan
from app.agent.precaution_agent import precaution_agent
from app.services.task_writer_service import write_tasks_to_database, verify_event_exists
from app.services.work_distributor_service import forward_to_work_distributor
from app.core.config import settings
from app.core.exceptions import (
    http_unauthorized, 
    http_agent_error, 
    http_event_not_found, 
    http_task_write_error,
    http_invalid_input,
    AgentExecutionError,
    TaskWriteError
)
from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Precaution"])


async def verify_api_key(x_api_key: str = Header(None)) -> None:
    """Dependency to verify the internal API key."""
    if x_api_key != settings.internal_api_key:
        logger.warning("Unauthorized access attempt with invalid API key.")
        raise http_unauthorized()


@router.post("/precaution", response_model=PrecautionPlan)
async def generate_precaution_plan(
    payload: PrecautionTriggerPayload,
    api_key: None = Depends(verify_api_key)
):
    """
    Main endpoint to trigger the AI-powered precaution planning workflow.
    Validates the event, runs the agent, persists tasks, and notifies downstream.
    """
    plan_id = str(uuid.uuid4())
    risk = payload.risk_assessment
    event_id = payload.disaster_event_id
    
    # Validate disaster_event_id is a proper UUID
    try:
        uuid.UUID(event_id)
    except ValueError:
        raise http_invalid_input(f"disaster_event_id '{event_id}' is not a valid UUID")

    logger.info(
        f"Precaution planning triggered for event {event_id}, "
        f"disaster={risk.get('disaster_kind', 'unknown')}"
    )

    # 1. Verify event exists in Main DB
    if not await verify_event_exists(event_id):
        raise http_event_not_found(event_id)

    # 2. Extract coordinates and location data
    longitude = risk.get("longitude", 0.0)
    latitude = risk.get("latitude", 0.0)

    # 3. Build comprehensive agent input
    agent_input = _build_agent_input(payload, plan_id)

    try:
        # 4. Run the AI Agent
        # Network retry logic is handled by ModelRetrySettings in precaution_agent.py
        logger.info("Starting agent execution...")
        result = await Runner.run(
            precaution_agent,
            input=agent_input,
            max_turns=settings.openai_max_turns
        )
        
        # 5. Extract structured output
        plan: PrecautionPlan = result.final_output
        plan.plan_id = plan_id

        # 6. Write generated tasks to database (atomic transaction)
        task_ids = await write_tasks_to_database(plan, longitude, latitude)
        plan.tasks_created_in_db = len(task_ids)
        plan.task_ids_created = task_ids

        # 7. Forward plan to Work Distributor Agent (async handoff)
        await forward_to_work_distributor(plan)

        logger.info(
            f"Precaution Plan {plan_id} complete. Risk={plan.risk_level}, "
            f"Tasks Created={plan.tasks_created_in_db}, NGOs Suggested={len(plan.suggested_ngo_assignments)}"
        )
        
        return plan

    except AgentExecutionError as e:
        logger.error(f"Agent Execution Failure for event {event_id}: {str(e)}")
        raise http_agent_error(str(e))
    except TaskWriteError as e:
        logger.error(f"Database Task Write Failure for event {event_id}: {str(e)}")
        raise http_task_write_error(str(e))
    except Exception as e:
        logger.error(f"Unexpected system error during planning for event {event_id}: {str(e)}")
        raise http_agent_error(f"Internal System Error: {str(e)}")


def _build_agent_input(payload: PrecautionTriggerPayload, plan_id: str) -> str:
    """
    Formats the raw risk assessment and context into a clear instruction for the agent.
    Includes the full risk assessment JSON so the agent has access to all fields
    including breach_id, assessment_id, secondary_disasters_possible, etc.
    """
    risk = payload.risk_assessment
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Serialize the full risk assessment for the agent
    full_risk_json = json.dumps(risk, indent=2, default=str)
    
    return f"""
PRECAUTION PLANNING REQUEST
Plan ID: {plan_id}
Disaster Event ID: {payload.disaster_event_id}
Request Timestamp: {now_utc}

RISK ASSESSMENT SUMMARY:
- Disaster Kind: {risk.get('disaster_kind')}
- Risk Level: {risk.get('risk_level')}
- Composite Risk Score: {risk.get('composite_risk_score')}
- Location: {risk.get('district')}, {risk.get('province')}
- Coordinates: Lat {risk.get('latitude')}, Long {risk.get('longitude')}
- Affected Population: {risk.get('estimated_population_affected')}
- Estimated Displaced: {risk.get('estimated_displaced_persons')}
- Is Forecast Breach: {risk.get('is_forecast_breach')}
- Hours Until Peak: {risk.get('hours_until_peak')}
- Terrain: {risk.get('terrain_assessment')}
- Infrastructure at Risk: {risk.get('infrastructure_at_risk')}
- Situation Trajectory: {risk.get('situation_trajectory')}
- Escalation Risk: {risk.get('escalation_risk')}

COMPLETE RISK ASSESSMENT DATA:
{full_risk_json}

INSTRUCTIONS:
1. Follow your mandatory 13-step workflow strictly.
2. Use disaster_event_id={payload.disaster_event_id} in your output.
3. Operation Mode: {'PROACTIVE' if risk.get('is_forecast_breach') else 'REACTIVE'}
4. Generate a minimum of 30 quantified, prioritized actions.
5. Produce your final response as a complete PrecautionPlan JSON.
"""
