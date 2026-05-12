from pydantic import BaseModel, Field, model_validator
from typing import Any


class PrecautionTriggerPayload(BaseModel):
    """
    Schema for the incoming trigger from the ClimaSync backend.
    Includes the disaster event link and the full risk assessment report.
    """
    disaster_event_id: str = Field(
        ...,
        description="UUID of disaster_events record in main DB. All tasks created will be linked to this event_id."
    )
    
    risk_assessment: dict[str, Any] = Field(
        ...,
        description="""Complete RiskAssessmentReport JSON from Risk Analysis Agent. 
        Contains risk_level, composite_risk_score, disaster_kind, district, province, 
        latitude, longitude, estimated_population_affected, estimated_displaced_persons, 
        is_forecast_breach, forecast_horizon_h, hours_until_peak, terrain_assessment, 
        infrastructure_at_risk, impact_estimates, situation_trajectory, escalation_risk."""
    )

    @model_validator(mode="after")
    def validate_payload(self) -> "PrecautionTriggerPayload":
        # Check disaster_event_id
        if not self.disaster_event_id or not self.disaster_event_id.strip():
            raise ValueError("disaster_event_id cannot be an empty string")

        # Check required keys in risk_assessment
        required_keys = [
            "disaster_kind", 
            "district", 
            "province", 
            "risk_level", 
            "is_forecast_breach"
        ]
        missing_keys = [key for key in required_keys if key not in self.risk_assessment]

        if missing_keys:
            raise ValueError(
                f"risk_assessment is missing required keys: {', '.join(missing_keys)}"
            )

        return self
