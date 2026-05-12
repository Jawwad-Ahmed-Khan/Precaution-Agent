import math


def calculate_displaced(
    affected_population: int,
    disaster_kind: str,
    flood_risk_zone: str | None = None,
    magnitude: float | None = None,
    estimated_displaced_from_report: int | None = None
) -> dict:
    """
    Computes displacement numbers based on disaster type and severity.
    Returns exact numbers for displaced persons and shelter seekers.
    """
    source = "calculated"
    ratio = 0.30  # Default ratio

    if estimated_displaced_from_report is not None and estimated_displaced_from_report > 0:
        displaced = estimated_displaced_from_report
        source = "risk_report"
        # Back-calculate ratio for metadata if needed, otherwise use a placeholder
        ratio = displaced / affected_population if affected_population > 0 else 0
    else:
        kind = disaster_kind.lower()
        if "flood" in kind:
            zone = str(flood_risk_zone).lower() if flood_risk_zone else ""
            if "zone_5" in zone or "critical" in zone:
                ratio = 0.70
            elif "zone_4" in zone or "very_high" in zone:
                ratio = 0.50
            elif "zone_3" in zone or "high" in zone:
                ratio = 0.30
            else:
                ratio = 0.40
        elif "earthquake" in kind:
            mag = magnitude if magnitude is not None else 0.0
            if mag >= 6.0:
                ratio = 0.40
            elif mag >= 5.0:
                ratio = 0.20
            else:
                ratio = 0.15
        elif "heatwave" in kind:
            ratio = 0.05
        elif "cyclone" in kind:
            ratio = 0.60
        elif "landslide" in kind:
            ratio = 0.50
        elif "heavy_rain" in kind:
            ratio = 0.25
        elif "cold_wave" in kind:
            ratio = 0.20
        elif "drought" in kind:
            ratio = 0.10
        else:
            ratio = 0.30

        displaced = int(affected_population * ratio)

    # 40% typically go to relatives in Pakistan context
    formal_shelter_seekers = int(displaced * 0.60)
    go_to_relatives = displaced - formal_shelter_seekers

    return {
        "displaced": displaced,
        "formal_shelter_seekers": formal_shelter_seekers,
        "go_to_relatives": go_to_relatives,
        "displacement_ratio_used": round(ratio, 2),
        "source": source
    }
