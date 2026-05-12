"""
This module defines the ClimaSync Precaution Definer Agent.
The agent uses 5 specialized tools to gather data, perform calculations, 
and search the web to produce a structured PrecautionPlan.
"""

from agents import (
    Agent, WebSearchTool, AgentOutputSchema, 
    ModelSettings, ModelRetrySettings, retry_policies
)
from app.agent.system_prompt import PRECAUTION_DEFINER_SYSTEM_PROMPT
from app.agent.tools.ngo_resource_tool import get_available_ngo_resources
from app.agent.tools.location_context_tool import get_location_and_infrastructure
from app.agent.tools.resource_calculator_tool import calculate_resource_requirements
from app.agent.tools.existing_tasks_tool import get_existing_tasks_for_event
from app.models.output_models import PrecautionPlan
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)


def create_precaution_agent() -> Agent:
    """
    Initializes the Precaution Definer Agent with its tools, 
    system prompt, and structured output type.
    
    Uses AgentOutputSchema with strict_json_schema=False because PrecautionPlan
    contains Optional fields and complex Enum types that cannot be auto-converted
    to strict JSON schema.
    
    Includes ModelRetrySettings with network_error and HTTP status retry policies
    to handle transient OpenAI API connection failures during multi-turn execution.
    """
    logger.info(f"Creating Precaution Definer Agent using model: {settings.openai_model}")
    
    # Configure retry policy for transient connection errors
    retry_config = ModelRetrySettings(
        max_retries=3,
        backoff={
            "initial_delay": 1.0,
            "max_delay": 10.0,
            "multiplier": 2.0,
            "jitter": True,
        },
        policy=retry_policies.any(
            retry_policies.network_error(),
            retry_policies.http_status([408, 429, 500, 502, 503, 504]),
            retry_policies.retry_after(),
        ),
    )

    agent = Agent(
        name="ClimaSync Precaution Definer Agent",
        model=settings.openai_model,
        instructions=PRECAUTION_DEFINER_SYSTEM_PROMPT,
        model_settings=ModelSettings(
            max_tokens=16384,
            retry=retry_config,
        ),
        tools=[
            get_available_ngo_resources,
            get_location_and_infrastructure,
            calculate_resource_requirements,
            get_existing_tasks_for_event,
            WebSearchTool(),
        ],
        output_type=AgentOutputSchema(PrecautionPlan, strict_json_schema=False),
    )
    
    return agent


# Module-level singleton instance for use throughout the application
precaution_agent = create_precaution_agent()
