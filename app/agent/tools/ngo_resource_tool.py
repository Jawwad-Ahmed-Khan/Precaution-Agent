import json
from agents import function_tool
from app.database.main_db_connection import get_main_pool, acquire_healthy_connection
from app.database.queries.ngo_queries import (
    GET_ELIGIBLE_NGOS_FOR_DISTRICT,
    GET_NGO_SPECIALIZATIONS_FOR_NGOS,
    GET_NGO_OPERATIONAL_AREAS_FOR_NGOS,
    GET_NGO_RESOURCE_TOTALS
)
from app.core.logger import setup_logger

logger = setup_logger(__name__)


async def get_available_ngo_resources_logic(
    province: str,
    district: str,
    disaster_kind: str,
) -> dict:
    """Core logic for retrieving NGO resources."""
    pool = get_main_pool()
    conn = await acquire_healthy_connection(pool)
    try:
        # 1. Get eligible NGOs
        ngo_rows = await conn.fetch(GET_ELIGIBLE_NGOS_FOR_DISTRICT, province, district)
        
        if not ngo_rows:
            return {
                "found": False,
                "message": f"No verified NGOs found operating in {district}, {province}."
            }

        eligible_ngos = [dict(row) for row in ngo_rows]
        ngo_ids = [ngo["ngo_id"] for ngo in eligible_ngos]

        # 2. Get specializations
        spec_rows = await conn.fetch(GET_NGO_SPECIALIZATIONS_FOR_NGOS, ngo_ids)
        specs_map = {row["ngo_id"]: row["specializations"] for row in spec_rows}

        # 3. Get operational areas
        area_rows = await conn.fetch(GET_NGO_OPERATIONAL_AREAS_FOR_NGOS, ngo_ids)
        areas_map = {row["ngo_id"]: {"districts": row["districts"], "provinces": row["provinces"]} for row in area_rows}

        # 4. Get aggregate totals
        totals_row = await conn.fetchrow(GET_NGO_RESOURCE_TOTALS, ngo_ids)
        resource_totals = dict(totals_row) if totals_row else {}

        # 5. Enrich NGO data and identify specialists
        disaster_kind_lower = disaster_kind.lower()
        specialists = []
        
        for ngo in eligible_ngos:
            ngo_id = ngo["ngo_id"]
            ngo["specializations"] = specs_map.get(ngo_id, [])
            ngo["operational_areas"] = areas_map.get(ngo_id, {"districts": [], "provinces": []})
            
            if any(disaster_kind_lower in s.lower() for s in ngo["specializations"]):
                specialists.append(ngo["org_name"])

        return {
            "found": True,
            "eligible_ngos": eligible_ngos,
            "resource_totals": resource_totals,
            "disaster_kind_specialists": specialists,
            "count": len(eligible_ngos)
        }
    finally:
        await pool.release(conn)


@function_tool
async def get_available_ngo_resources(
    province: str,
    district: str,
    disaster_kind: str,
) -> str:
    """
    Finds all verified NGOs that can operate in the affected district. 
    Returns their complete resource inventory including rescue boats, 
    ambulances, doctors, paramedics, volunteers, shelter capacity, 
    and food packets. Also returns aggregate totals for gap analysis. 
    Call this in STEP 4 of workflow.
    """
    try:
        res = await get_available_ngo_resources_logic(province, district, disaster_kind)
        return json.dumps(res, default=str)
    except Exception as e:
        logger.error(f"Error in get_available_ngo_resources: {str(e)}")
        return json.dumps({"error": str(e)})
