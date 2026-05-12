import json
from agents import function_tool
from app.agent.calculators.displacement_calculator import calculate_displaced
from app.agent.calculators.shelter_calculator import calculate_shelter
from app.agent.calculators.medical_calculator import calculate_medical
from app.agent.calculators.equipment_calculator import calculate_equipment
from app.agent.calculators.food_water_calculator import calculate_food_water
from app.core.logger import setup_logger

logger = setup_logger(__name__)


def calculate_resource_requirements_logic(
    affected_population: int,
    estimated_displaced: int,
    risk_level: str,
    disaster_kind: str,
    terrain_type: str,
    schools_count: int,
    hospitals_count: int,
    hospital_beds: int,
    dams_count: int = 0,
    flood_risk_zone: str | None = None,
    magnitude: float | None = None,
) -> dict:
    """Core logic for calculating resource requirements."""
    # 1. Displacement
    displaced_res = calculate_displaced(
        affected_population=affected_population,
        disaster_kind=disaster_kind,
        flood_risk_zone=flood_risk_zone,
        magnitude=magnitude,
        estimated_displaced_from_report=estimated_displaced
    )

    # 2. Medical
    medical_res = calculate_medical(
        affected_population=affected_population,
        risk_level=risk_level,
        disaster_kind=disaster_kind
    )

    # 3. Shelter
    shelter_res = calculate_shelter(
        formal_shelter_seekers=displaced_res["formal_shelter_seekers"],
        schools_count=schools_count
    )

    # 4. Equipment
    equipment_res = calculate_equipment(
        affected_population=affected_population,
        displaced=displaced_res["displaced"],
        disaster_kind=disaster_kind,
        terrain_type=terrain_type,
        field_hospitals=medical_res["field_hospitals_needed"],
        dams_count=dams_count
    )

    # 5. Food & Water
    food_water_res = calculate_food_water(
        displaced=displaced_res["displaced"],
        affected_population=affected_population,
        disaster_kind=disaster_kind
    )

    return {
        "displacement": displaced_res,
        "shelter": shelter_res,
        "medical": medical_res,
        "equipment": equipment_res,
        "food_water": food_water_res
    }


@function_tool
async def calculate_resource_requirements(
    affected_population: int,
    estimated_displaced: int,
    risk_level: str,
    disaster_kind: str,
    terrain_type: str,
    schools_count: int,
    hospitals_count: int,
    hospital_beds: int,
    dams_count: int = 0,
    flood_risk_zone: str | None = None,
    magnitude: float | None = None,
) -> str:
    """
    Pure calculation tool. Computes exact quantities for every resource type 
    using Pakistan-specific formulas. Call this STEP 5 of workflow.
    """
    try:
        res = calculate_resource_requirements_logic(
            affected_population, estimated_displaced, risk_level, 
            disaster_kind, terrain_type, schools_count, 
            hospitals_count, hospital_beds, dams_count, 
            flood_risk_zone, magnitude
        )
        return json.dumps(res, default=str)
    except Exception as e:
        logger.error(f"Error in calculate_resource_requirements: {str(e)}")
        return json.dumps({"error": str(e)})
