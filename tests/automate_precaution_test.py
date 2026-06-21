import httpx
import json
import uuid
import time
import sys
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
BASE_URL = "http://localhost:8003"
# Priority: Environment variable > Hardcoded fallback
API_KEY = os.getenv("INTERNAL_API_KEY", "2b666f707fff4410b814123ddc392665")

# --- AREA CONFIGURATION (Larkana) ---
TEST_DISTRICT = "larkana"
TEST_PROVINCE = "sindh"
TEST_CITY = "Larkana City"
LATITUDE = 27.5589
LONGITUDE = 68.2020

# --- DISASTER TYPE (Switch between 'flood' or 'heatwave') ---
DISASTER_KIND = "flood" # Set to "heatwave" for heatwave test

TEST_EVENT_ID = str(uuid.uuid4())
TEST_NGO_ID = str(uuid.uuid4())

# --- PAYLOAD ---
PAYLOAD = {
    "disaster_event_id": TEST_EVENT_ID,
    "risk_assessment": {
        "assessment_id": f"auto-test-{TEST_EVENT_ID[:8]}",
        "breach_id": f"breach-{TEST_EVENT_ID[:8]}",
        "disaster_kind": DISASTER_KIND,
        "location_name": TEST_CITY,
        "district": TEST_DISTRICT,
        "province": TEST_PROVINCE,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "is_forecast_breach": False,
        "composite_risk_score": 88.5 if DISASTER_KIND == "flood" else 92.0,
        "risk_level": "EXTREME" if DISASTER_KIND == "flood" else "CRITICAL",
        "situation_trajectory": "Rapidly Worsening",
        "terrain_assessment": {
            "terrain_type": "riverine_plain" if DISASTER_KIND == "flood" else "urban"
        },
        "exposure": {
            "population_breakdown": {
                "total_population": 600000,
                "estimated_directly_affected": 450000
            },
            "infrastructure_at_risk": {
                "hospitals_count": 4,
                "schools_count": 35,
                "bridges_count": 3 if DISASTER_KIND == "flood" else 0
            }
        },
        "impact_estimates": {
            "estimated_population_affected": 450000,
            "estimated_displaced_persons": 280000 if DISASTER_KIND == "flood" else 0
        },
        "hours_until_peak": 8.5
    }
}

def seed_database():
    """Uses MCP SQL Execution to seed the database with test data."""
    print(f"\n[1/4] Seeding database for {TEST_DISTRICT} ({DISASTER_KIND})...")
    
    # NGO Resources adapted based on disaster kind
    boats = 10 if DISASTER_KIND == "flood" else 0
    cooling_centers = 0 if DISASTER_KIND == "flood" else 20
    
    sql = f"""
    -- Cleanup potential old test data
    DELETE FROM ngo_operational_areas WHERE ngo_id = '{TEST_NGO_ID}';
    DELETE FROM ngo_resources WHERE ngo_id = '{TEST_NGO_ID}';
    DELETE FROM ngo_profiles WHERE ngo_id = '{TEST_NGO_ID}';
    DELETE FROM tasks WHERE event_id = '{TEST_EVENT_ID}';
    DELETE FROM disaster_events WHERE event_id = '{TEST_EVENT_ID}';

    -- Insert Test NGO
    INSERT INTO ngo_profiles (
        ngo_id, org_name, org_email, registration_number, base_district, base_province, 
        verification_status, rating, is_active, service_radius_km
    ) VALUES (
        '{TEST_NGO_ID}', 'Larkana Relief Corps {TEST_NGO_ID[:4]}', 'larkana-relief@example.com', 'REG-LRK-99', 
        '{TEST_DISTRICT}', '{TEST_PROVINCE}', 'verified', 4.9, true, 150
    );

    -- Insert NGO Resources
    INSERT INTO ngo_resources (
        ngo_id, ambulances, rescue_boats, trucks, doctors, paramedics, 
        volunteers_available, food_packets_capacity, shelter_capacity
    ) VALUES (
        '{TEST_NGO_ID}', 15, {boats}, 8, 25, 50, 250, 15000, 8000
    );

    -- Insert NGO Operational Area
    INSERT INTO ngo_operational_areas (
        ngo_id, district, province, is_active
    ) VALUES (
        '{TEST_NGO_ID}', '{TEST_DISTRICT}', '{TEST_PROVINCE}', true
    );

    -- Insert Disaster Event
    INSERT INTO disaster_events (
        event_id, event_type, title, district, province, 
        location, affected_population, risk_level, event_status
    ) VALUES (
        '{TEST_EVENT_ID}', '{DISASTER_KIND}', 'Larkana {DISASTER_KIND.capitalize()} Emergency', 
        '{TEST_DISTRICT}', '{TEST_PROVINCE}',
        ST_SetSRID(ST_Point({LONGITUDE}, {LATITUDE}), 4326), 450000, 
        '{"extreme" if DISASTER_KIND == "flood" else "critical"}', 'active'
    );
    """
    
    print(f"  NGO ID: {TEST_NGO_ID}")
    print(f"  Event ID: {TEST_EVENT_ID}")
    print(f"  Area: {TEST_CITY}, {TEST_PROVINCE}")
    return sql

def run_agent():
    print(f"\n[2/4] Triggering Precaution Agent API for {DISASTER_KIND} in Larkana...")
    start_time = time.time()
    
    with httpx.Client(timeout=300) as client:
        try:
            response = client.post(
                f"{BASE_URL}/api/v1/precaution",
                json=PAYLOAD,
                headers={"X-API-Key": API_KEY}
            )
            response.raise_for_status()
            elapsed = time.time() - start_time
            print(f"  Success! Status 200 in {elapsed:.2f}s")
            return response.json()
        except Exception as e:
            print(f"  FAILED: {str(e)}")
            if hasattr(e, 'response'):
                print(f"  Details: {e.response.text}")
            sys.exit(1)

def verify_results(plan):
    print(f"\n[3/4] Verifying Larkana {DISASTER_KIND.capitalize()} Plan...")
    
    # 1. Check API Response Structure
    print(f"  Checking JSON structure...")
    assert plan["disaster_kind"] == DISASTER_KIND, f"Disaster kind mismatch: {plan['disaster_kind']}"
    assert plan["district"].lower() == TEST_DISTRICT, f"District mismatch: {plan['district']}"
    assert len(plan["prioritized_actions"]) >= 20, "Insufficient actions generated"
    
    # 2. Check Resource Calculations based on disaster type
    print(f"  Checking specific requirements...")
    reqs = plan["resource_requirements"]
    
    if DISASTER_KIND == "flood":
        assert reqs["rescue_boats_needed"] > 0, "Boats calculation failed for flood"
        assert reqs["tents_needed"] > 0, "Tents calculation failed for flood"
    elif DISASTER_KIND == "heatwave":
        assert reqs["cooling_centers_needed"] > 0, "Cooling centers calculation failed for heatwave"
        assert reqs["iv_fluid_bags"] > 0, "Medical IV fluid calculation failed for heatwave"
    
    print("  Larkana verification successful!")

def check_db_persistence():
    """SQL to verify if tasks were actually written to the DB."""
    print(f"\n[4/4] Generating SQL for database verification...")
    
    sql = f"""
    -- Check tasks created for Larkana
    SELECT task_label, task_type, required_quantity, priority 
    FROM tasks 
    WHERE event_id = '{TEST_EVENT_ID}'
    ORDER BY priority DESC;

    -- Check if disaster_events was updated
    SELECT precautions, analyzed_at 
    FROM disaster_events 
    WHERE event_id = '{TEST_EVENT_ID}';
    """
    return sql

if __name__ == "__main__":
    print("="*60)
    print(f"LARKANA {DISASTER_KIND.upper()} AUTOMATED TEST")
    print("="*60)
    
    # 1. Generate SQL for Seeding
    seed_sql = seed_database()
    
    # Save seed SQL to a file for easy execution
    with open("seed_larkana.sql", "w") as f:
        f.write(seed_sql)
    print(f"\n  Seed SQL saved to: seed_larkana.sql")
    
    print("\nNext Steps:")
    print(f"1. Run the SQL in 'seed_larkana.sql' in Supabase.")
    print("2. Ensure the Precaution Agent is running.")
    print("3. Uncomment 'run_agent()' in this script and run it.")
    
    # To run automatically, uncomment these:
    # response_plan = run_agent()
    # verify_results(response_plan)
    # verify_sql = check_db_persistence()
    # print(verify_sql)
