import math


def analyze_gaps(
    requirements: dict,
    available: dict
) -> list[dict]:
    """
    Compares resource requirements against available NGO resources.
    Returns a list of gap analyses with severity levels and suggestions.
    """
    gap_reports = []
    
    for resource_key, required in requirements.items():
        if required == 0:
            continue
            
        available_qty = available.get(resource_key, 0)
        gap = max(0, required - available_qty)
        gap_pct = (gap / required) * 100 if required > 0 else 0
        
        if gap_pct >= 80:
            severity = "CRITICAL"
            suggestion = (
                f"URGENT: Contact NDMA, Pakistan Army, and international organizations immediately. "
                f"Gap of {gap} {resource_key.replace('_', ' ')} cannot be met by NGOs alone."
            )
        elif gap_pct >= 40:
            severity = "SIGNIFICANT"
            suggestion = "Contact regional NGOs outside current area. Consider government warehouses."
        elif gap_pct >= 20:
            severity = "MODERATE"
            suggestion = "Coordinate with nearby district NGOs. Gap manageable with extra effort."
        elif gap_pct > 0:
            severity = "MANAGEABLE"
            suggestion = "Available resources nearly sufficient. Monitor consumption."
        else:
            severity = "COVERED"
            suggestion = "Sufficient resources available from NGOs."
            
        gap_reports.append({
            "resource_name": resource_key,
            "required_quantity": required,
            "available_from_ngos": available_qty,
            "gap_quantity": gap,
            "gap_percentage": round(gap_pct, 2),
            "gap_severity": severity,
            "procurement_suggestion": suggestion
        })
        
    return gap_reports


def count_critical_gaps(gaps: list[dict]) -> int:
    """Counts how many resources have a CRITICAL gap severity."""
    return sum(1 for g in gaps if g["gap_severity"] == "CRITICAL")
