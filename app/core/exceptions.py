from fastapi import HTTPException, status


class PrecautionAgentError(Exception):
    """Base class for all exceptions in the Precaution Definer Agent."""
    def __init__(self, message: str = "An unexpected error occurred in the Precaution Agent"):
        self.message = message
        super().__init__(self.message)


class MainDatabaseError(PrecautionAgentError):
    """Errors related to the Main Operational Database."""
    pass


class CollectionDatabaseError(PrecautionAgentError):
    """Errors related to the Collection Database."""
    pass


class NGODataNotFoundError(PrecautionAgentError):
    """Raised when no eligible NGOs are found for a disaster area."""
    pass


class DisasterEventNotFoundError(PrecautionAgentError):
    """Raised when the specified disaster event does not exist in the database."""
    pass


class AgentExecutionError(PrecautionAgentError):
    """Errors during the AI agent's decision making or tool execution process."""
    pass


class TaskWriteError(PrecautionAgentError):
    """Errors while writing tasks or status history to the database."""
    pass


class InvalidRiskReportError(PrecautionAgentError):
    """Raised when the input RiskAssessmentReport is malformed or missing critical data."""
    pass


class WorkDistributorError(PrecautionAgentError):
    """Errors while communicating with the Work Distributor Agent."""
    pass


# --- FastAPI HTTPException Factory Functions ---

def http_unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this resource"
    )


def http_event_not_found(event_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Disaster event with ID {event_id} not found"
    )


def http_agent_error(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Agent Execution Failure: {detail}"
    )


def http_task_write_error(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to write tasks to database: {detail}"
    )


def http_invalid_input(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Invalid Risk Assessment Input: {detail}"
    )
