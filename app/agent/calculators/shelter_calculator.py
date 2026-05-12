import math


def calculate_shelter(
    formal_shelter_seekers: int,
    schools_count: int,
    household_size: float = 6.5,
    school_usability_ratio: float = 0.70
) -> dict:
    """
    Computes tent and blanket requirements based on available school capacity.
    Applies a 70% usability factor (30% assumed damaged or inaccessible).
    """
    # 70% of schools assumed usable as emergency shelter
    schools_usable = int(schools_count * school_usability_ratio)
    
    # 200 persons per school as emergency shelter
    school_shelter_capacity = schools_usable * 200
    
    persons_needing_tents = max(0, formal_shelter_seekers - school_shelter_capacity)
    
    tents_needed = math.ceil(persons_needing_tents / household_size)
    
    # 2 blankets per person (floor and cover)
    blankets_needed = int(tents_needed * household_size * 2)
    
    return {
        "tents_needed": tents_needed,
        "blankets_needed": blankets_needed,
        "persons_needing_tents": persons_needing_tents,
        "school_shelter_capacity": school_shelter_capacity,
        "schools_usable_as_shelter": schools_usable,
        "formal_shelter_seekers": formal_shelter_seekers
    }
