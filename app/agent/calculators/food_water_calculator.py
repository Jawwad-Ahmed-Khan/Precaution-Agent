import math


def calculate_food_water(
    displaced: int,
    affected_population: int,
    disaster_kind: str,
    water_liters_per_person: float = 15.0,
    tanker_capacity: int = 10000
) -> dict:
    """
    Computes food and water requirements.
    """
    household_size = 6.5
    
    clean_water_liters_per_day = int(displaced * water_liters_per_person)
    water_tankers_per_day = math.ceil(clean_water_liters_per_day / tanker_capacity)
    
    # 3 meal-equivalent packets per person per day
    food_packets_per_day = displaced * 3
    
    # 10-day initial supply for emergency treatment
    water_purification_tablets = displaced * 10
    
    # Oral Rehydration Salts — critical for flood/cholera
    ors_sachets = displaced * 5
    
    # 1 cooking set per 10 households for community kitchens
    cooking_fuel_sets = math.ceil(displaced / (household_size * 10))
    
    community_kitchens = max(1, math.ceil(displaced / 5000))
    
    return {
        "clean_water_liters_per_day": clean_water_liters_per_day,
        "water_tankers_per_day": water_tankers_per_day,
        "food_packets_per_day": food_packets_per_day,
        "water_purification_tablets": water_purification_tablets,
        "ors_sachets": ors_sachets,
        "cooking_fuel_sets": cooking_fuel_sets,
        "community_kitchens": community_kitchens,
        "days_supply_initial": 7
    }
