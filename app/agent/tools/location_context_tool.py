import json
from agents import function_tool
from app.database.collection_db_connection import get_collection_pool, acquire_healthy_collection_connection
from app.database.queries.location_queries import (
    GET_LOCATION_BY_DISTRICT_COLLECTION,
    GET_INFRASTRUCTURE_WITHIN_RADIUS_COLLECTION
)
from app.core.logger import setup_logger

logger = setup_logger(__name__)


async def get_location_and_infrastructure_logic(
    district: str,
    province: str,
    longitude: float,
    latitude: float,
) -> dict:
    """Core logic for location and infrastructure retrieval."""
    pool = get_collection_pool()
    conn = await acquire_healthy_collection_connection(pool)
    try:
        # 1. Get location context
        location_row = await conn.fetchrow(GET_LOCATION_BY_DISTRICT_COLLECTION, district, province)
        location_data = dict(location_row) if location_row else {"message": "Location details not found in collection DB"}

        # 2. Get infrastructure within 30km
        infra_rows = await conn.fetch(GET_INFRASTRUCTURE_WITHIN_RADIUS_COLLECTION, longitude, latitude, 30000)
        
        # 3. Categorize infrastructure
        infra_summary = {
            "hospitals_count": 0,
            "hospital_beds_total": 0,
            "basic_health_units_count": 0,
            "schools_count": 0,
            "bridges_count": 0,
            "dams_count": 0,
            "barrages_count": 0,
            "evacuation_centers_count": 0,
            "total_evacuation_capacity": 0,
            "power_stations_count": 0,
            "water_treatment_count": 0,
            "critical_assets_count": 0,
            "assets_list": []
        }

        for row in infra_rows:
            asset = dict(row)
            asset_type = asset["asset_type"].lower()
            
            if asset["is_critical"]:
                infra_summary["critical_assets_count"] += 1
            
            if "hospital" in asset_type:
                infra_summary["hospitals_count"] += 1
                infra_summary["hospital_beds_total"] += asset.get("capacity") or 0
            elif "health" in asset_type or "bhu" in asset_type:
                infra_summary["basic_health_units_count"] += 1
            elif "school" in asset_type or "college" in asset_type or "university" in asset_type:
                infra_summary["schools_count"] += 1
            elif "bridge" in asset_type:
                infra_summary["bridges_count"] += 1
            elif "dam" in asset_type:
                infra_summary["dams_count"] += 1
            elif "barrage" in asset_type:
                infra_summary["barrages_count"] += 1
            elif "evacuation" in asset_type or "shelter" in asset_type:
                infra_summary["evacuation_centers_count"] += 1
                infra_summary["total_evacuation_capacity"] += asset.get("capacity") or 0
            elif "power" in asset_type or "grid" in asset_type:
                infra_summary["power_stations_count"] += 1
            elif "water" in asset_type or "treatment" in asset_type:
                infra_summary["water_treatment_count"] += 1
            
            if len(infra_summary["assets_list"]) < 20:
                infra_summary["assets_list"].append({
                    "name": asset["asset_name"],
                    "type": asset["asset_type"],
                    "distance_km": round(asset["distance_km"], 2),
                    "is_critical": asset["is_critical"]
                })

        return {
            "location_context": location_data,
            "infrastructure_summary": infra_summary
        }
    finally:
        await pool.release(conn)


@function_tool
async def get_location_and_infrastructure(
    district: str,
    province: str,
    longitude: float,
    latitude: float,
) -> str:
    """
    Reads the collection database to get location vulnerability context 
    and infrastructure inventory. Returns population, terrain type, 
    drainage quality, building stock, and counts of hospitals, schools, 
    bridges, dams, evacuation centers within 30km of the disaster coordinates. 
    Call this STEP 3.
    """
    try:
        res = await get_location_and_infrastructure_logic(district, province, longitude, latitude)
        return json.dumps(res, default=str)
    except Exception as e:
        logger.error(f"Error in get_location_and_infrastructure: {str(e)}")
        return json.dumps({
            "error": "Collection Database currently unavailable",
            "details": str(e),
            "note": "Agent should make assumptions based on general district knowledge."
        })
