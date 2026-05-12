import math


def calculate_medical(
    affected_population: int,
    risk_level: str,
    disaster_kind: str
) -> dict:
    """
    Computes medical personnel and infrastructure requirements.
    """
    level = risk_level.lower()
    if level in ["extreme", "critical"]:
        ratio = 500
    elif level == "high":
        ratio = 1000
    elif level == "medium":
        ratio = 2000
    else:  # low
        ratio = 5000
        
    doctors_needed = max(2, math.ceil(affected_population / ratio))
    paramedics_needed = doctors_needed * 2
    nurses_needed = doctors_needed * 3
    
    ambulances_needed = max(2, math.ceil(affected_population / 10000))
    field_hospitals_needed = max(1, math.ceil(affected_population / 50000))
    medicine_kits_needed = math.ceil(affected_population / 50)
    blood_units_needed = doctors_needed * 10
    
    if "heatwave" in disaster_kind.lower():
        iv_fluid_bags = doctors_needed * 50
    else:
        iv_fluid_bags = doctors_needed * 20
        
    return {
        "doctors_needed": doctors_needed,
        "paramedics_needed": paramedics_needed,
        "nurses_needed": nurses_needed,
        "ambulances_needed": ambulances_needed,
        "field_hospitals_needed": field_hospitals_needed,
        "medicine_kits_needed": medicine_kits_needed,
        "blood_units_needed": blood_units_needed,
        "iv_fluid_bags": iv_fluid_bags
    }
