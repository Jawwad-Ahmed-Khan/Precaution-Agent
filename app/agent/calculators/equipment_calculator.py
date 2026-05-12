import math


def calculate_equipment(
    affected_population: int,
    displaced: int,
    disaster_kind: str,
    terrain_type: str,
    field_hospitals: int,
    dams_count: int = 0
) -> dict:
    """
    Computes equipment requirements based on disaster type and terrain.
    """
    # Initialize all values to 0
    results = {
        "generators_needed": 0,
        "satellite_phones": 0,
        "temporary_toilets": 0,
        "mosquito_nets": 0,
        "rescue_boats_needed": 0,
        "life_jackets_total": 0,
        "water_pumps_needed": 0,
        "search_rescue_teams": 0,
        "heavy_machinery_cranes": 0,
        "search_dogs": 0,
        "thermal_cameras": 0,
        "body_bags": 0,
        "cooling_centers_needed": 0,
        "water_distribution_points": 0,
        "iv_fluid_bags": 0, # Note: this is also in medical but sometimes counted as equipment
        "ice_packs_per_day": 0,
        "shade_structures": 0
    }

    # All disasters
    results["generators_needed"] = field_hospitals * 2 + 3
    results["satellite_phones"] = max(5, field_hospitals * 2)
    results["temporary_toilets"] = max(10, math.ceil(displaced / 20))
    results["mosquito_nets"] = math.ceil(displaced * 1.2)
    
    kind = disaster_kind.lower()
    
    if "flood" in kind:
        results["rescue_boats_needed"] = max(5, math.ceil(affected_population / 5000))
        life_jackets = math.ceil(results["rescue_boats_needed"] * 8 * 1.25)
        child_life_jackets = math.ceil(displaced * 0.20 * 0.50)
        results["life_jackets_total"] = life_jackets + child_life_jackets
        results["water_pumps_needed"] = max(3, math.ceil(affected_population / 25000))
        
    if "earthquake" in kind:
        results["search_rescue_teams"] = max(2, math.ceil(affected_population / 20000))
        results["heavy_machinery_cranes"] = max(1, math.ceil(affected_population / 30000))
        results["search_dogs"] = results["search_rescue_teams"] * 2
        results["thermal_cameras"] = results["search_rescue_teams"]
        results["body_bags"] = max(50, math.ceil(affected_population * 0.001) * 2)
        
    if "heatwave" in kind:
        results["cooling_centers_needed"] = max(3, math.ceil(affected_population / 10000))
        results["water_distribution_points"] = max(5, math.ceil(affected_population / 5000))
        results["ice_packs_per_day"] = math.ceil(affected_population * 0.30)
        results["shade_structures"] = math.ceil(affected_population * 0.30 / 100)
        
    # Mountain terrain modifier
    terrain = terrain_type.lower()
    if "mountain" in terrain or "highland" in terrain:
        results["satellite_phones"] *= 2
        
    return results
