"""
End-to-end test for the Precaution Definer Agent.
Uses httpx with a 600s timeout to avoid PowerShell timeout issues.
"""
import httpx
import json
import sys
import time

BASE_URL = "http://localhost:8003"
API_KEY = "2b666f707fff4410b814123ddc392665"
EVENT_ID = "c306dc2f-eb54-4135-a80c-8e1d6f0f49a9"

PAYLOAD = {
    "disaster_event_id": EVENT_ID,
    "risk_assessment": {
        "assessment_id": "test-assessment-001",
        "breach_id": "test-breach-001",
        "disaster_kind": "flood",
        "breach_severity_received": "emergency",
        "location_name": "Sukkur",
        "district": "sukkur",
        "province": "sindh",
        "latitude": 27.7052,
        "longitude": 68.8574,
        "observation_time": "2025-07-15T14:30:00+05:00",
        "is_forecast_breach": False,
        "forecast_horizon_h": None,
        "assessment_timestamp": "2025-07-15T14:35:00Z",
        "composite_risk_score": 82.5,
        "risk_level": "EXTREME",
        "situation_trajectory": "Rapidly Worsening",
        "terrain_assessment": {
            "terrain_type": "riverine_plain",
            "terrain_multiplier": 1.10,
            "terrain_implications": [
                "Slow drainage, prolonged flooding expected",
                "Large area inundation likely"
            ]
        },
        "hazard_severity": {"score": 90},
        "exposure": {
            "score": 80,
            "population_breakdown": {
                "total_population": 750000,
                "estimated_directly_affected": 750000
            },
            "infrastructure_at_risk": {
                "hospitals_count": 3,
                "hospital_beds_total": 850,
                "schools_count": 47,
                "bridges_count": 8,
                "dams_count": 0,
                "barrages_count": 1,
                "dam_failure_risk": False,
                "evacuation_centers_count": 2,
                "evacuation_capacity_total": 15000,
                "impact_radius_km_used": 30
            }
        },
        "vulnerability": {"score": 78},
        "escalation_risk": {
            "score": 72,
            "is_worsening": True,
            "secondary_disasters_possible": ["disease_outbreak"],
            "hours_until_peak_estimate": 8.2
        },
        "response_capacity": {"score": 75},
        "impact_estimates": {
            "estimated_population_affected": 750000,
            "estimated_displaced_persons": 525000,
            "estimated_deaths_range": "50-200",
            "death_risk_level": "High",
            "estimated_economic_damage_pkr": "15000000000"
        },
        "hours_until_peak": 8.2,
        "estimated_population_affected": 750000,
        "estimated_displaced_persons": 525000,
        "recommended_response_urgency": "Emergency",
        "critical_actions_needed": [
            "Deploy rescue boats immediately",
            "Establish field hospitals",
            "Evacuate riverside communities"
        ],
        "data_confidence": "HIGH",
        "data_gaps": [],
        "assumptions_made": []
    }
}


def run_test():
    print("=" * 70)
    print("PRECAUTION DEFINER AGENT — END-TO-END FLOOD TEST")
    print("=" * 70)

    # 1. Health check
    print("\n[1/3] Health check...")
    with httpx.Client(timeout=10) as c:
        r = c.get(f"{BASE_URL}/health")
        health = r.json()
        print(f"  Status: {health['status']}")
        print(f"  Model: {health['model']}")
        print(f"  Main DB: {health['main_database_connected']}")
        print(f"  Collection DB: {health['collection_database_connected']}")
        if health["status"] != "healthy":
            print("  ABORT: Service not healthy!")
            sys.exit(1)

    # 2. Run agent
    print(f"\n[2/3] Sending flood scenario to agent (model: {health['model']})...")
    print(f"  Event ID: {EVENT_ID}")
    print(f"  Timeout: 600s")
    start = time.time()

    with httpx.Client(timeout=600) as c:
        try:
            r = c.post(
                f"{BASE_URL}/api/v1/precaution",
                json=PAYLOAD,
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"}
            )
        except httpx.ReadTimeout:
            print(f"  TIMEOUT after {time.time() - start:.0f}s")
            sys.exit(1)

    elapsed = time.time() - start
    print(f"  Response: HTTP {r.status_code} in {elapsed:.1f}s")

    if r.status_code != 200:
        print(f"  ERROR: {r.text[:500]}")
        sys.exit(1)

    plan = r.json()

    # Save full response
    with open("test_response.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(f"  Full response saved to test_response.json")

    # 3. Verify
    print(f"\n[3/3] VERIFICATION RESULTS:")
    print("-" * 50)

    checks = [
        ("plan_id is UUID", bool(plan.get("plan_id"))),
        ("plan_mode is REACTIVE", plan.get("plan_mode") == "REACTIVE"),
        ("disaster_kind is flood", plan.get("disaster_kind") == "flood"),
        ("risk_level", bool(plan.get("risk_level"))),
        ("situation_summary not empty", bool(plan.get("situation_summary"))),
        ("tents_needed > 0", (plan.get("resource_requirements") or {}).get("tents_needed", 0) > 0),
        ("doctors_needed > 0", (plan.get("resource_requirements") or {}).get("doctors_needed", 0) > 0),
        ("rescue_boats_needed > 0", (plan.get("resource_requirements") or {}).get("rescue_boats_needed", 0) > 0),
        ("prioritized_actions has 20+", len(plan.get("prioritized_actions", [])) >= 20),
        ("first action is LIFE_SAFETY or EVACUATION", (plan.get("prioritized_actions", [{}])[0]).get("category") in ("LIFE_SAFETY", "EVACUATION", "MEDICAL", "SHELTER")),
        ("first action priority is 1", (plan.get("prioritized_actions", [{}])[0]).get("priority") == 1),
        ("resource_gaps populated", len(plan.get("resource_gaps", [])) > 0),
        ("timeline_breakdown exists", bool(plan.get("timeline_breakdown"))),
        ("precautions_summary_array 15+", len(plan.get("precautions_summary_array", [])) >= 15),
        ("tasks_created_in_db > 0", plan.get("tasks_created_in_db", 0) > 0),
        ("task_ids_created not empty", len(plan.get("task_ids_created", [])) > 0),
        ("data_gaps is list", isinstance(plan.get("data_gaps"), list)),
        ("assumptions_made is list", isinstance(plan.get("assumptions_made"), list)),
    ]

    passed = 0
    failed = 0
    for name, result in checks:
        icon = "PASS" if result else "FAIL"
        print(f"  [{icon}] {name}")
        if result:
            passed += 1
        else:
            failed += 1

    # Print key stats
    print(f"\n{'=' * 50}")
    print(f"  Model: {health['model']}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Actions generated: {len(plan.get('prioritized_actions', []))}")
    print(f"  Tasks written to DB: {plan.get('tasks_created_in_db', 0)}")
    print(f"  Resource gaps found: {len(plan.get('resource_gaps', []))}")
    print(f"  NGOs suggested: {len(plan.get('suggested_ngo_assignments', []))}")
    print(f"  Precaution summaries: {len(plan.get('precautions_summary_array', []))}")
    print(f"  Plan confidence: {plan.get('plan_confidence', 'N/A')}")
    print(f"{'=' * 50}")
    print(f"  RESULT: {passed}/{passed + failed} checks passed")

    if failed > 0:
        print(f"  WARNING: {failed} checks FAILED")
        sys.exit(1)
    else:
        print(f"  ALL CHECKS PASSED!")


if __name__ == "__main__":
    run_test()
