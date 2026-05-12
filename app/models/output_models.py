from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class PlanMode(str, Enum):
    REACTIVE = "REACTIVE"
    PROACTIVE = "PROACTIVE"


class ActionTimeline(str, Enum):
    IMMEDIATE = "0-6 hours"
    SHORT_TERM = "6-24 hours"
    MEDIUM_TERM = "24-72 hours"
    RECOVERY = "72+ hours"


class ActionCategory(str, Enum):
    LIFE_SAFETY = "LIFE_SAFETY"
    MEDICAL = "MEDICAL"
    SHELTER = "SHELTER"
    FOOD_WATER = "FOOD_WATER"
    EQUIPMENT = "EQUIPMENT"
    COMMUNICATION = "COMMUNICATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    VULNERABLE_POPULATION = "VULNERABLE_POPULATION"
    DISEASE_PREVENTION = "DISEASE_PREVENTION"
    RECOVERY = "RECOVERY"


class GapSeverity(str, Enum):
    COVERED = "COVERED"
    MANAGEABLE = "MANAGEABLE"
    MODERATE = "MODERATE"
    SIGNIFICANT = "SIGNIFICANT"
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    HIGH = "HIGH"
    LOW = "LOW"


class ResourceRequirements(BaseModel):
    """Computed exact quantities for every resource type."""
    # Shelter
    tents_needed: int = 0
    blankets_needed: int = 0
    persons_needing_formal_shelter: int = 0
    schools_usable_as_shelter: int = 0
    school_shelter_capacity: int = 0
    
    # Medical
    doctors_needed: int = 0
    paramedics_needed: int = 0
    nurses_needed: int = 0
    ambulances_needed: int = 0
    field_hospitals_needed: int = 0
    medicine_kits_needed: int = 0
    blood_units_needed: int = 0
    iv_fluid_bags: int = 0
    
    # Food and Water
    food_packets_per_day: int = 0
    clean_water_liters_per_day: int = 0
    water_tankers_per_day: int = 0
    water_purification_tablets: int = 0
    ors_sachets: int = 0
    community_kitchens: int = 0
    
    # Flood specific (0 if not flood)
    rescue_boats_needed: int = 0
    life_jackets_total: int = 0
    water_pumps_needed: int = 0
    
    # Earthquake specific (0 if not earthquake)
    search_rescue_teams: int = 0
    heavy_machinery_cranes: int = 0
    search_dogs: int = 0
    body_bags: int = 0
    thermal_cameras: int = 0
    
    # Heatwave specific (0 if not heatwave)
    cooling_centers_needed: int = 0
    water_distribution_points: int = 0
    ice_packs_per_day: int = 0
    shade_structures: int = 0
    
    # General equipment
    generators_needed: int = 0
    satellite_phones: int = 0
    temporary_toilets: int = 0
    mosquito_nets: int = 0


class ResourceGap(BaseModel):
    """Gap analysis for a single resource type."""
    resource_name: str
    required_quantity: int = 0
    available_from_ngos: int = 0
    gap_quantity: int = 0
    gap_percentage: float = 0.0
    gap_severity: str = "MODERATE"  # Use str to accept any LLM value
    procurement_suggestion: str = ""


# Mapping for common LLM-generated time_window variations
_TIMELINE_ALIASES = {
    "0-6 hours": ActionTimeline.IMMEDIATE,
    "0-6h": ActionTimeline.IMMEDIATE,
    "immediate": ActionTimeline.IMMEDIATE,
    "IMMEDIATE": ActionTimeline.IMMEDIATE,
    "6-24 hours": ActionTimeline.SHORT_TERM,
    "6-24h": ActionTimeline.SHORT_TERM,
    "short_term": ActionTimeline.SHORT_TERM,
    "SHORT_TERM": ActionTimeline.SHORT_TERM,
    "24-72 hours": ActionTimeline.MEDIUM_TERM,
    "24-72h": ActionTimeline.MEDIUM_TERM,
    "medium_term": ActionTimeline.MEDIUM_TERM,
    "MEDIUM_TERM": ActionTimeline.MEDIUM_TERM,
    "72+ hours": ActionTimeline.RECOVERY,
    "72+h": ActionTimeline.RECOVERY,
    "recovery": ActionTimeline.RECOVERY,
    "RECOVERY": ActionTimeline.RECOVERY,
}

# Mapping for common LLM-generated category variations
_CATEGORY_ALIASES = {
    "LIFE_SAFETY": ActionCategory.LIFE_SAFETY,
    "SEARCH_AND_RESCUE": ActionCategory.LIFE_SAFETY,
    "SEARCH_RESCUE": ActionCategory.LIFE_SAFETY,
    "RESCUE": ActionCategory.LIFE_SAFETY,
    "EVACUATION": ActionCategory.LIFE_SAFETY,
    "MEDICAL": ActionCategory.MEDICAL,
    "HEALTH": ActionCategory.MEDICAL,
    "HEALTHCARE": ActionCategory.MEDICAL,
    "SHELTER": ActionCategory.SHELTER,
    "HOUSING": ActionCategory.SHELTER,
    "FOOD_WATER": ActionCategory.FOOD_WATER,
    "FOOD": ActionCategory.FOOD_WATER,
    "WATER": ActionCategory.FOOD_WATER,
    "NUTRITION": ActionCategory.FOOD_WATER,
    "EQUIPMENT": ActionCategory.EQUIPMENT,
    "LOGISTICS": ActionCategory.EQUIPMENT,
    "SUPPLIES": ActionCategory.EQUIPMENT,
    "COMMUNICATION": ActionCategory.COMMUNICATION,
    "COORDINATION": ActionCategory.COMMUNICATION,
    "INFRASTRUCTURE": ActionCategory.INFRASTRUCTURE,
    "TRANSPORT": ActionCategory.INFRASTRUCTURE,
    "VULNERABLE_POPULATION": ActionCategory.VULNERABLE_POPULATION,
    "VULNERABLE": ActionCategory.VULNERABLE_POPULATION,
    "PROTECTION": ActionCategory.VULNERABLE_POPULATION,
    "DISEASE_PREVENTION": ActionCategory.DISEASE_PREVENTION,
    "WASH": ActionCategory.DISEASE_PREVENTION,
    "HYGIENE": ActionCategory.DISEASE_PREVENTION,
    "SANITATION": ActionCategory.DISEASE_PREVENTION,
    "RECOVERY": ActionCategory.RECOVERY,
    "EARLY_RECOVERY": ActionCategory.RECOVERY,
}


class PrioritizedAction(BaseModel):
    """One action item in the precaution plan. Maps to a task record."""
    priority: int
    category: str = "LIFE_SAFETY"  # Use str to accept any LLM value
    action_title: str
    action_detail: str
    task_type_for_db: str = "general"
    quantity_required: int = 0
    quantity_unit: str = "units"
    priority_level_for_db: str = "medium"
    time_window: str = "0-6 hours"  # Use str to accept any LLM value
    estimated_duration_hours: int = 24
    responsible_ngo_suggestion: Optional[str] = None
    prerequisites: list[str] = []
    is_time_critical: bool = False
    estimated_people_helped: int = 0
    is_compound_specific: bool = False

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v):
        if isinstance(v, str):
            # 1. Try exact alias lookup
            key = v.upper().replace(" ", "_").replace("/", "_").replace("-", "_")
            mapped = _CATEGORY_ALIASES.get(key)
            if mapped:
                return mapped.value
            # 2. Keyword fallback for freeform text like "Rescue/Boats"
            lower = v.lower()
            if any(k in lower for k in ("rescue", "boat", "evacuat", "life_safety", "search")):
                return ActionCategory.LIFE_SAFETY.value
            if any(k in lower for k in ("medical", "doctor", "hospital", "health", "ambulance")):
                return ActionCategory.MEDICAL.value
            if any(k in lower for k in ("shelter", "tent", "blanket", "housing")):
                return ActionCategory.SHELTER.value
            if any(k in lower for k in ("food", "water", "nutrition", "ration")):
                return ActionCategory.FOOD_WATER.value
            if any(k in lower for k in ("equipment", "generator", "pump", "logistic")):
                return ActionCategory.EQUIPMENT.value
            if any(k in lower for k in ("communicat", "coordinat", "phone")):
                return ActionCategory.COMMUNICATION.value
            if any(k in lower for k in ("disease", "hygiene", "sanitat", "wash", "mosquito")):
                return ActionCategory.DISEASE_PREVENTION.value
            if any(k in lower for k in ("vulnerab", "child", "elder", "disabl", "protect")):
                return ActionCategory.VULNERABLE_POPULATION.value
            if any(k in lower for k in ("infra", "bridge", "road", "transport")):
                return ActionCategory.INFRASTRUCTURE.value
            if any(k in lower for k in ("recover", "rehab", "restor")):
                return ActionCategory.RECOVERY.value
        return v

    @field_validator("time_window", mode="before")
    @classmethod
    def normalize_time_window(cls, v):
        if isinstance(v, str):
            mapped = _TIMELINE_ALIASES.get(v)
            if mapped:
                return mapped.value
        return v


class NGOSuggestion(BaseModel):
    """A suggested NGO assignment for a category of tasks."""
    ngo_id: str = ""
    ngo_name: str
    base_district: str = ""
    base_province: str = ""
    rating: float = 0.0
    specializations: list[str] = []
    suggested_task_categories: list[str] = []
    deployment_hours_estimate: int = 0
    available_resources_summary: dict[str, Any] = {}
    reason_for_suggestion: str = ""


class TimelineBreakdown(BaseModel):
    """Breakdown of task priorities by time window."""
    immediate_0_to_6h: list[int] = []
    short_term_6_to_24h: list[int] = []
    medium_term_24_to_72h: list[int] = []
    recovery_72h_plus: list[int] = []


class CompoundDisasterInfo(BaseModel):
    """Information about detected compound disasters."""
    has_compound_disaster: bool = False
    compound_disasters: list[str] = []
    compound_interaction_description: str = ""
    additional_precautions_count: int = 0


class PrecautionPlan(BaseModel):
    """The complete deliverable of the Precaution Definer Agent."""
    # Identification
    plan_id: str = ""
    disaster_event_id: str
    breach_id: str = ""
    assessment_id: str = ""
    disaster_kind: str
    location_name: str = ""
    district: str
    province: str = ""
    plan_mode: str = "REACTIVE"  # Use str instead of PlanMode enum
    risk_level: str = "EXTREME"
    composite_risk_score: float = 0.0
    plan_generated_at: str = ""
    agent_version: str = "precaution_definer_v1.0"
    
    # Situation
    situation_summary: str = ""
    hours_until_peak: Optional[float] = None
    estimated_population_affected: int = 0
    estimated_displaced_persons: int = 0
    
    # Computed requirements
    resource_requirements: ResourceRequirements = ResourceRequirements()
    
    # NGO availability totals
    eligible_ngos_found: int = 0
    ngo_total_rescue_boats_available: int = 0
    ngo_total_doctors_available: int = 0
    ngo_total_ambulances_available: int = 0
    ngo_total_volunteers_available: int = 0
    ngo_total_shelter_capacity_available: int = 0
    ngo_total_food_packets_available: int = 0
    
    # Gap analysis
    resource_gaps: list[ResourceGap] = []
    critical_gaps_count: int = 0
    critical_gaps_summary: str = ""
    
    # Main deliverable
    prioritized_actions: list[PrioritizedAction] = []
    total_actions_count: int = 0
    
    @model_validator(mode="after")
    def compute_total_actions(self) -> "PrecautionPlan":
        if self.total_actions_count == 0 and self.prioritized_actions:
            self.total_actions_count = len(self.prioritized_actions)
        return self
    
    # Timeline
    timeline_breakdown: TimelineBreakdown = TimelineBreakdown()
    
    # NGO suggestions
    suggested_ngo_assignments: list[NGOSuggestion] = []
    
    # Compound disaster
    compound_disaster_info: CompoundDisasterInfo = CompoundDisasterInfo()
    
    # Summary for disaster_events.precautions column
    precautions_summary_array: list[str] = []
    
    # Estimated damage
    estimated_damage_pkr: Optional[int] = None
    
    # Web search findings
    road_access_status: str = ""
    logistics_challenges: list[str] = []
    current_ngo_operations_found: str = ""
    
    # Data quality
    plan_confidence: str = "MEDIUM"
    data_gaps: list[str] = []
    assumptions_made: list[str] = []
    
    # DB write results (filled after writing tasks)
    tasks_created_in_db: int = 0
    task_ids_created: list[str] = []
