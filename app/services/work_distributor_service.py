import httpx
from app.core.config import settings
from app.models.output_models import PrecautionPlan
from app.core.logger import setup_logger

logger = setup_logger(__name__)


async def forward_to_work_distributor(plan: PrecautionPlan) -> bool:
    """
    Forwards the generated PrecautionPlan to the Work Distributor Agent.
    Failure to forward does not fail the main request, but is logged for attention.
    """
    if not settings.work_distributor_base_url:
        logger.warning("Work Distributor Agent URL not configured. Skipping distribution.")
        return False

    url = f"{settings.work_distributor_base_url.rstrip('/')}/api/v1/distribute"
    headers = {
        "X-API-Key": settings.work_distributor_api_key,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=plan.model_dump(mode="json"),
                headers=headers
            )

            if response.status_code in [200, 201]:
                logger.info(f"PrecautionPlan {plan.plan_id} forwarded successfully to Work Distributor.")
                return True
            else:
                logger.warning(
                    f"Work Distributor returned error {response.status_code}: {response.text}"
                )
                return False

    except httpx.RequestError as e:
        logger.warning(f"Work Distributor Agent not reachable: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during distribution handoff: {str(e)}")
        return False
