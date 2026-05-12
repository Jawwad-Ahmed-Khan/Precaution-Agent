# Precaution Definer Agent — Complete Production Design

---

## SECTION 1: FULL SYSTEM UNDERSTANDING

Before designing, let me map exactly what exists:

```
┌──────────────────────────────────────────────────────────────────┐
│              WHAT WE NOW KNOW FROM THE DATABASE                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  OPERATIONAL DATABASE (Main ClimaSync DB) HAS:                  │
│                                                                  │
│  NGO DATA:                                                       │
│  ├── ngo_profiles (org_name, base_district, base_province,      │
│  │   service_radius_km, verification_status, rating)            │
│  ├── ngo_resources (ambulances, rescue_boats, trucks,           │
│  │   doctors, paramedics, rescue_divers, volunteers,            │
│  │   food_packets_capacity, shelter_capacity, cranes)           │
│  ├── ngo_specializations (flood, earthquake, medical, etc)      │
│  └── ngo_operational_areas (province, district, is_active)      │
│                                                                  │
│  DISASTER DATA:                                                  │
│  ├── alerts (alert_type, severity_score, location, district)    │
│  ├── disaster_events (event_type, affected_population,          │
│  │   risk_level, precautions[], estimated_damage_pkr,          │
│  │   analyzed_at, location, district, province)                │
│  └── disaster_sources (raw provenance data)                     │
│                                                                  │
│  TASK DATA:                                                      │
│  ├── tasks (task_label, task_type, required_quantity,           │
│  │   priority, status, assigned_ngo_id, created_by_type,       │
│  │   estimated_duration_hours, approved_at)                    │
│  └── task_status_history (audit trail)                          │
│                                                                  │
│  SOCIAL DATA:                                                    │
│  ├── social_posts (content, status, created_by_type)            │
│  └── social_post_platforms (per platform tracking)              │
│                                                                  │
│  OTHER:                                                          │
│  ├── users, admin_profiles                                      │
│  ├── notifications                                              │
│  └── audit_logs                                                 │
│                                                                  │
│  COLLECTION DATABASE HAS:                                        │
│  ├── pakistan_locations (population, terrain data)              │
│  ├── pakistan_infrastructure (hospitals, schools, bridges)      │
│  ├── weather_hourly_window (current weather)                    │
│  ├── seismic_events (earthquake data)                           │
│  └── flood_gauge_current/forecasts (river data)                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## SECTION 2: AGENT POSITION IN PIPELINE

```
┌──────────────────────────────────────────────────────────────────┐
│                  COMPLETE PIPELINE FLOW                          │
└──────────────────────────────────────────────────────────────────┘

Collection Service → detects breach
        ↓
Admin Portal → admin reviews breach → triggers Risk Agent
        ↓
Risk Analysis Agent (Port 8002)
  → reads collection DB
  → web searches
  → produces RiskAssessmentReport {
      composite_risk_score: 82.5,
      risk_level: "EXTREME",
      disaster_kind: "flood",
      district: "sukkur",
      province: "sindh",
      estimated_population_affected: 750000,
      estimated_displaced_persons: 525000,
      hours_until_peak: 8.2,
      is_forecast_breach: false,
      terrain_assessment: {...},
      infrastructure_at_risk: {...},
      situation_trajectory: "Rapidly Worsening",
      impact_estimates: {...}
    }
        ↓
        ↓ risk report sent to
        ↓
┌────────────────────────────────────────────────┐
│     PRECAUTION DEFINER AGENT (Port 8003)       │
│                                                │
│  READS:  Main DB → NGO resources and areas     │
│  READS:  Collection DB → location/infra data   │
│  READS:  Main DB → existing tasks (avoid dupe) │
│  READS:  Main DB → active disaster_events      │
│  WRITES: Main DB → tasks table (created_by_type='ai')    │
│  WRITES: Main DB → disaster_events.precautions │
│  USES:   Web search for logistics and context  │
│  OUTPUT: PrecautionPlan JSON                   │
└────────────────────────────────────────────────┘
        ↓
        ↓ sends PrecautionPlan to
        ↓
Work Distributor Agent (Port 8004)
  ├── Task Allocator Agent → assigns tasks to NGOs
  │   → updates tasks.assigned_ngo_id
  │   → sends notifications to NGOs
  └── Social Media Agent → posts public alerts
      → creates social_posts records
      → creates social_post_platforms records
```

---

## SECTION 3: TWO OPERATION MODES

```
┌──────────────────────────────────────────────────────────────────┐
│                    TWO OPERATION MODES                           │
├──────────────────────────┬───────────────────────────────────────┤
│  REACTIVE MODE           │  PROACTIVE MODE                       │
├──────────────────────────┼───────────────────────────────────────┤
│  TRIGGER:                │  TRIGGER:                             │
│  is_forecast_breach=FALSE│  is_forecast_breach=TRUE              │
│                          │                                       │
│  MEANING:                │  MEANING:                             │
│  Disaster IS HAPPENING   │  Disaster IS COMING                   │
│  RIGHT NOW               │  hours or days ahead                  │
│                          │                                       │
│  EXAMPLES:               │  EXAMPLES:                            │
│  Earthquake M6.2 struck  │  River gauge at 85% danger            │
│  Flood is active now     │  level, rising rapidly,               │
│  Heatwave ongoing        │  forecast shows 80% extreme           │
│  People need help NOW    │  probability in 36 hours              │
│                          │                                       │
│  PRECAUTIONS:            │  PRECAUTIONS:                         │
│  RESCUE focused          │  PREVENTION focused                   │
│  Deploy immediately      │  Pre-position resources               │
│  Search and rescue       │  Evacuate NOW before peak             │
│  Medical triage          │  Warn communities                     │
│  Emergency shelter       │  Sandbag embankments                  │
│  Body recovery prep      │  Stock medicines in advance           │
│                          │                                       │
│  TASKS CREATED WITH:     │  TASKS CREATED WITH:                  │
│  priority = critical     │  priority = high                      │
│  status = unallocated    │  status = unallocated                 │
│  timeline: 0-6h first    │  timeline: hours before peak          │
└──────────────────────────┴───────────────────────────────────────┘
```

---

## SECTION 4: WHAT AGENT WRITES TO DATABASE

```
┌──────────────────────────────────────────────────────────────────┐
│              AGENT DATABASE WRITES (VERY IMPORTANT)              │
└──────────────────────────────────────────────────────────────────┘

WRITE 1: disaster_events table UPDATE
  Fields updated:
    precautions = ARRAY of precaution strings
    estimated_damage_pkr = computed damage estimate
    analyzed_at = now()
    risk_level = from risk report (low/medium/high/critical)
    affected_population = from risk report
  
  This connects the precaution plan to the disaster event.

WRITE 2: tasks table INSERT (multiple rows)
  For each action in the prioritized list:
  INSERT INTO tasks:
    event_id = disaster_event UUID
    task_label = action_title (e.g. "Deploy rescue boats")
    description = action_detail (full instruction)
    task_type = mapped from category
                (ambulance/boat/medical/food/evacuation/shelter)
    required_quantity = exact number computed by agent
    priority = critical/high/medium/low based on timeline
    target_location = disaster coordinates
    target_location_name = district name
    status = 'unallocated' (ready for task allocator)
    created_by_type = 'ai'
    estimated_duration_hours = from action timeline
    
  The Task Allocator Agent will later:
    - Find the right NGO for each task
    - Set assigned_ngo_id
    - Change status to 'pending_acceptance'
    - Send notification to NGO

WRITE 3: task_status_history INSERT
  For each task created:
    old_status = NULL
    new_status = 'unallocated'
    change_reason = 'Created by Precaution Definer Agent'
```

---

## SECTION 5: NGO MATCHING LOGIC

```
┌──────────────────────────────────────────────────────────────────┐
│              HOW AGENT MATCHES NGOs TO TASKS                     │
└──────────────────────────────────────────────────────────────────┘

STEP 1: Find eligible NGOs for disaster area
  Query ngo_operational_areas:
    WHERE province = disaster_province
    AND district = disaster_district
    AND is_active = TRUE
  
  Also query by service_radius_km:
    NGOs whose base_location is within their 
    service_radius_km of disaster location

STEP 2: Filter by verification status
  Only verified NGOs:
    WHERE verification_status = 'verified'

STEP 3: Check specialization match
  For flood disaster:
    Prefer NGOs with specialization = 'flood' or 'rescue'
  For earthquake:
    Prefer NGOs with specialization = 'earthquake' or 
    'search_and_rescue'
  For heatwave:
    Prefer NGOs with specialization = 'medical' or 
    'healthcare'

STEP 4: Check available resources
  From ngo_resources table:
    Task type = 'boat' → check rescue_boats > 0
    Task type = 'ambulance' → check ambulances > 0
    Task type = 'medical' → check doctors > 0 or paramedics > 0
    Task type = 'food' → check food_packets_capacity > 0
    Task type = 'shelter' → check shelter_capacity > 0
    Task type = 'evacuation' → check trucks or 
                               four_wheel_vehicles > 0

STEP 5: Rank by rating
  ORDER BY ngo_profiles.rating DESC

STEP 6: Suggest (not assign — Task Allocator assigns)
  PrecautionPlan includes suggested_ngo_assignments:
    Which NGO is best for which task category
    Based on specialization + resources + location
```

---

## SECTION 6: QUANTITY CALCULATION ENGINE

```
┌──────────────────────────────────────────────────────────────────┐
│              EXACT QUANTITY CALCULATION FORMULAS                 │
│         (These become the tool: calculate_requirements)         │
└──────────────────────────────────────────────────────────────────┘

INPUT VARIABLES:
  affected_population (from risk report)
  risk_level: LOW/MEDIUM/HIGH/EXTREME
  disaster_kind: flood/earthquake/heatwave/etc
  estimated_displaced (from risk report)
  terrain_type (from risk report)
  infrastructure_at_risk (hospitals, schools, from risk report)
  hours_until_peak (from risk report, None if reactive)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DISPLACEMENT CALCULATION (used by all formulas below):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use estimated_displaced from risk report if available.
If not:
  flood + zone_5 → displaced = population × 0.70
  flood + zone_4 → displaced = population × 0.50
  flood + zone_3 → displaced = population × 0.30
  earthquake M6+ shallow → displaced = population × 0.40
  earthquake M5-6 → displaced = population × 0.20
  heatwave → displaced = 0 (need shelter not displacement)
  heatwave medical need → population × 0.05

formal_shelter_seekers = displaced × 0.60
  (40% go to relatives' homes in Pakistan context)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHELTER CALCULATIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pakistan average household size = 6.5 persons

schools_available_as_shelter = 
  infrastructure_at_risk.schools_count × 0.70
  (30% assumed damaged or inaccessible)

school_shelter_capacity = 
  schools_available_as_shelter × 200 persons each

persons_needing_tents = 
  MAX(0, formal_shelter_seekers - school_shelter_capacity)

tents_needed = CEIL(persons_needing_tents / 6.5)

blankets_needed = tents_needed × 6.5 × 2
  (2 per person — floor and cover)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEDICAL CALCULATIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Risk level doctor ratio:
  EXTREME → 1 doctor per 500 affected
  HIGH → 1 doctor per 1,000 affected
  MEDIUM → 1 doctor per 2,000 affected
  LOW → 1 doctor per 5,000 affected

doctors_needed = CEIL(affected_population / ratio)

paramedics_needed = doctors_needed × 2
  (always 2 paramedics per doctor minimum)

nurses_needed = doctors_needed × 3

ambulances_needed = CEIL(affected_population / 10,000)
  minimum 2 always

field_hospitals_needed = CEIL(affected_population / 50,000)
  minimum 1 always

medicine_kits_needed = CEIL(affected_population / 50)

blood_units_needed = doctors_needed × 10
  (reserve supply)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD AND WATER CALCULATIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

clean_water_liters_per_day = displaced × 15 liters
  (WHO emergency standard)

water_tankers_per_day = CEIL(clean_water_liters_per_day / 10,000)
  (10,000 liter tanker capacity)

food_packets_per_day = displaced × 3
  (3 meals equivalent per day per person)

water_purification_tablets = displaced × 10
  (10-day initial supply)

ors_sachets = displaced × 5
  (especially for flood — cholera prevention)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLOOD-SPECIFIC EQUIPMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rescue_boats_needed = CEIL(affected_population / 5,000)
  minimum 5

life_jackets_needed = rescue_boats_needed × 8 × 1.25
  (8 per boat + 25% reserve)

life_jackets_for_children = CEIL(displaced × 0.20 × 0.50)
  (20% children, 50% need child-size jackets)

total_life_jackets = life_jackets_needed + 
                     life_jackets_for_children

water_pumps_needed = CEIL(affected_population / 25,000)

generators_needed = field_hospitals_needed × 2 +
                    relief_camps_count × 1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EARTHQUAKE-SPECIFIC EQUIPMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

search_rescue_teams = CEIL(affected_population / 20,000)
  each team = 8 trained persons

heavy_machinery_cranes = CEIL(affected_population / 30,000)
  for rubble removal

search_dogs = search_rescue_teams × 2

body_bags = estimated_deaths × 2
  (uncertainty buffer, never understock)

thermal_cameras = search_rescue_teams
  (for detecting survivors under rubble)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEATWAVE-SPECIFIC:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cooling_centers_needed = CEIL(affected_population / 10,000)

water_distribution_points = CEIL(affected_population / 5,000)

iv_fluid_bags = doctors_needed × 50
  (critical for heat stroke treatment)

ice_packs_per_day = CEIL(affected_population × 0.30)
  (30% outdoor workers and vulnerable)

shade_structures = CEIL(affected_population × 0.30 / 100)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NGO RESOURCE GAP ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each resource type, compare needed vs available:

  available = SUM of all eligible NGO resources
  gap = MAX(0, needed - available)
  gap_pct = (gap / needed) × 100

  gap_severity:
    gap_pct > 80% → CRITICAL
    gap_pct 40-80% → SIGNIFICANT
    gap_pct 20-40% → MODERATE
    gap_pct < 20% → MANAGEABLE
    gap_pct = 0 → COVERED
```

---

## SECTION 7: PRIORITIZED ACTION LIST STRUCTURE

```
┌──────────────────────────────────────────────────────────────────┐
│         COMPLETE PRIORITY ORDER AND ACTION CATEGORIES            │
└──────────────────────────────────────────────────────────────────┘

PRIORITY 1-5: LIFE SAFETY (ALWAYS FIRST — NON NEGOTIABLE)
  P1: Rescue operations (boats/teams) deploy immediately
  P2: Evacuate persons in immediate danger zones
  P3: Search and rescue for trapped/missing persons
  P4: Establish emergency medical triage
  P5: Issue emergency alerts to all downstream communities

PRIORITY 6-10: MEDICAL RESPONSE
  P6: Deploy ambulances to disaster zone
  P7: Establish field hospitals at safe distance
  P8: Deploy doctors and paramedics to triage points
  P9: Stock emergency medicines and IV fluids
  P10: Set up blood collection point

PRIORITY 11-15: SHELTER AND BASIC NEEDS
  P11: Open schools and public buildings as emergency shelter
  P12: Deploy relief tents for displaced families
  P13: Distribute blankets and basic household items
  P14: Establish relief camp with basic sanitation
  P15: Provide emergency cooking facilities at camps

PRIORITY 16-20: FOOD AND WATER
  P16: Deploy water tankers for clean drinking water
  P17: Distribute food packets (3 meals per person)
  P18: Set up community kitchens
  P19: Distribute water purification tablets
  P20: Establish food distribution schedule

PRIORITY 21-25: EQUIPMENT AND LOGISTICS
  P21: Deploy generators at field hospitals
  P22: Establish command and coordination center
  P23: Open emergency supply corridor roads
  P24: Deploy satellite communication equipment
  P25: Position cranes for rubble/debris clearing

PRIORITY 26-30: VULNERABLE POPULATION
  P26: Identify and register elderly, disabled, pregnant women
  P27: Provide dedicated transport for mobility-impaired
  P28: Set up child-friendly spaces in relief camps
  P29: Assign dedicated medical staff for vulnerable groups
  P30: Register missing persons and families

PRIORITY 31-35: DISEASE PREVENTION
  P31: Distribute ORS sachets (cholera prevention)
  P32: Test water quality at all distribution points
  P33: Distribute mosquito nets (flood disease prevention)
  P34: Set up temporary toilets (1 per 20 persons)
  P35: Deploy disease surveillance team

PRIORITY 36-40: RECOVERY PLANNING
  P36: Begin damage assessment documentation
  P37: Register all displaced persons for compensation
  P38: Psychosocial support teams deploy
  P39: Livestock rescue and veterinary support
  P40: Agricultural damage assessment for crop insurance
```

---

## SECTION 8: TASK TYPE MAPPING

```
┌──────────────────────────────────────────────────────────────────┐
│     MAPPING ACTIONS TO tasks.task_type ENUM VALUES               │
│     (enum: ambulance, boat, medical, food, evacuation, shelter)  │
└──────────────────────────────────────────────────────────────────┘

action_category → task_type:

LIFE_SAFETY rescue by boat → 'boat'
LIFE_SAFETY rescue by vehicle → 'evacuation'
MEDICAL triage/doctors/hospital → 'medical'
MEDICAL ambulances → 'ambulance'
SHELTER tents/camp → 'shelter'
FOOD food packets/water/kitchen → 'food'
EVACUATION moving people → 'evacuation'
EQUIPMENT/OTHER → 'medical' (closest match) or 'evacuation'

NOTE: The current task_type enum has 6 values.
If additional task types are needed in future,
the enum can be extended.
```

---

## SECTION 9: COMPLETE FILE STRUCTURE

```
precaution_definer_agent/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── exceptions.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── main_db_connection.py
│   │   │   ← connects to MAIN operational DB
│   │   │   ← READ: NGOs, tasks, disaster_events
│   │   │   ← WRITE: tasks, disaster_events.precautions
│   │   │
│   │   ├── collection_db_connection.py
│   │   │   ← connects to COLLECTION DB
│   │   │   ← READ ONLY: pakistan_locations, infrastructure
│   │   │
│   │   └── queries/
│   │       ├── __init__.py
│   │       ├── ngo_queries.py
│   │       │   ← read ngo_profiles, ngo_resources,
│   │       │     ngo_specializations, ngo_operational_areas
│   │       │
│   │       ├── disaster_event_queries.py
│   │       │   ← read/write disaster_events
│   │       │   ← read alerts
│   │       │
│   │       ├── task_queries.py
│   │       │   ← write tasks table
│   │       │   ← write task_status_history
│   │       │   ← read existing tasks for dedup
│   │       │
│   │       └── location_queries.py
│   │           ← read pakistan_locations (collection DB)
│   │           ← read pakistan_infrastructure (collection DB)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── input_models.py
│   │   │   ← receives RiskAssessmentReport from risk agent
│   │   │
│   │   └── output_models.py
│   │       ← produces PrecautionPlan
│   │       ← produces TaskCreationResult
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── precaution_agent.py
│   │   │   ← Agent definition with 5 tools
│   │   │
│   │   ├── system_prompt.py
│   │   │   ← complete detailed system prompt
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── ngo_resource_tool.py
│   │   │   │   ← get_available_ngo_resources()
│   │   │   │   ← reads ngo_profiles + ngo_resources +
│   │   │   │     ngo_operational_areas + ngo_specializations
│   │   │   │
│   │   │   ├── location_context_tool.py
│   │   │   │   ← get_location_and_infrastructure()
│   │   │   │   ← reads collection DB pakistan_locations
│   │   │   │   ← reads collection DB pakistan_infrastructure
│   │   │   │
│   │   │   ├── resource_calculator_tool.py
│   │   │   │   ← calculate_resource_requirements()
│   │   │   │   ← pure calculation, no DB needed
│   │   │   │   ← uses all formulas from Section 6
│   │   │   │
│   │   │   ├── existing_tasks_tool.py
│   │   │   │   ← get_existing_tasks_for_event()
│   │   │   │   ← reads tasks table for this event
│   │   │   │   ← prevents duplicate task creation
│   │   │   │
│   │   │   └── web_search_tool.py
│   │   │       ← WebSearchTool() from OpenAI Agents SDK
│   │   │
│   │   └── calculators/
│   │       ├── __init__.py
│   │       ├── displacement_calculator.py
│   │       ├── shelter_calculator.py
│   │       ├── medical_calculator.py
│   │       ├── equipment_calculator.py
│   │       ├── food_water_calculator.py
│   │       └── gap_analyzer.py
│   │           ← compares needed vs NGO available
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_writer_service.py
│   │   │   ← writes approved tasks to tasks table
│   │   │   ← writes task_status_history
│   │   │   ← updates disaster_events.precautions
│   │   │
│   │   └── work_distributor_service.py
│   │       ← forwards PrecautionPlan to Work Distributor
│   │       ← POST to port 8004
│   │
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           ├── precaution_controller.py
│           └── health_controller.py
│
├── tests/
│   ├── __init__.py
│   ├── test_calculators.py
│   ├── test_tools.py
│   └── test_agent.py
│
├── .env
├── .env.example
└── pyproject.toml
```

---

## SECTION 10: ENVIRONMENT VARIABLES

```env
# ── OpenAI ─────────────────────────────────────────────
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TURNS=30

# ── Main Operational Database (READ + WRITE) ────────────
# NGOs, tasks, disaster_events, social_posts
MAIN_DB_HOST=your-main-supabase.supabase.co
MAIN_DB_PORT=5432
MAIN_DB_NAME=postgres
MAIN_DB_USER=postgres
MAIN_DB_PASSWORD=your-main-db-password
MAIN_DB_POOL_MIN=2
MAIN_DB_POOL_MAX=10

# ── Collection Database (READ ONLY) ────────────────────
# pakistan_locations, pakistan_infrastructure, weather
COLLECTION_DB_HOST=your-collection-supabase.supabase.co
COLLECTION_DB_PORT=5432
COLLECTION_DB_NAME=postgres
COLLECTION_DB_USER=postgres
COLLECTION_DB_PASSWORD=your-collection-db-password
COLLECTION_DB_POOL_MIN=2
COLLECTION_DB_POOL_MAX=5

# ── Service ─────────────────────────────────────────────
APP_PORT=8003
APP_ENV=production
LOG_LEVEL=INFO
SERVICE_NAME=climasync-precaution-definer-agent

# ── Security ────────────────────────────────────────────
INTERNAL_API_KEY=your-internal-api-key

# ── Downstream: Work Distributor Agent ──────────────────
WORK_DISTRIBUTOR_BASE_URL=http://localhost:8004
WORK_DISTRIBUTOR_API_KEY=your-work-distributor-key

# ── Pakistan Constants ──────────────────────────────────
PAKISTAN_AVG_HOUSEHOLD_SIZE=6.5
FORMAL_SHELTER_RATIO=0.60
WHO_WATER_LITERS_PER_PERSON=15
TANKER_CAPACITY_LITERS=10000
```

---

## SECTION 11: COMPLETE INPUT MODEL

```python
# app/models/input_models.py
# ─────────────────────────────────────────────────────────────────
# This agent receives the complete RiskAssessmentReport
# from the Risk Analysis Agent plus the disaster_event_id
# to link tasks to the correct event in the operational DB.
# ─────────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class PrecautionTriggerPayload(BaseModel):
    """
    What the main ClimaSync backend sends to trigger
    the Precaution Definer Agent.

    Contains:
    1. disaster_event_id: UUID from main DB disaster_events
       table. Tasks will be linked to this event.

    2. risk_assessment: The complete RiskAssessmentReport
       JSON produced by the Risk Analysis Agent.
       Contains all scores, population data, terrain,
       infrastructure, and web search findings.
    """

    disaster_event_id: str = Field(
        ...,
        description=(
            "UUID of the disaster_events record in the "
            "main ClimaSync operational database. "
            "All tasks created will have this event_id."
        )
    )

    risk_assessment: dict = Field(
        ...,
        description=(
            "Complete RiskAssessmentReport JSON from the "
            "Risk Analysis Agent. Contains risk_level, "
            "composite_risk_score, disaster_kind, "
            "estimated_population_affected, "
            "estimated_displaced_persons, "
            "infrastructure_at_risk, terrain_assessment, "
            "impact_estimates, situation_trajectory, "
            "is_forecast_breach, hours_until_peak, "
            "and all five dimension scores."
        )
    )
```

---

## SECTION 12: COMPLETE OUTPUT MODEL

```python
# app/models/output_models.py

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


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


# ── SUB MODELS ────────────────────────────────────────────────────

class ResourceRequirements(BaseModel):
    """Computed exact quantities for every resource type."""

    # Shelter
    tents_needed: int
    blankets_needed: int
    persons_needing_formal_shelter: int
    schools_usable_as_shelter: int
    school_shelter_capacity: int

    # Medical
    doctors_needed: int
    paramedics_needed: int
    nurses_needed: int
    ambulances_needed: int
    field_hospitals_needed: int
    medicine_kits_needed: int
    blood_units_needed: int

    # Food and Water
    food_packets_per_day: int
    clean_water_liters_per_day: int
    water_tankers_per_day: int
    water_purification_tablets: int
    ors_sachets: int

    # Flood specific
    rescue_boats_needed: int = 0
    life_jackets_total: int = 0
    water_pumps_needed: int = 0

    # Earthquake specific
    search_rescue_teams: int = 0
    heavy_machinery_cranes: int = 0
    search_dogs: int = 0
    body_bags: int = 0
    thermal_cameras: int = 0

    # Heatwave specific
    cooling_centers_needed: int = 0
    water_distribution_points: int = 0
    iv_fluid_bags: int = 0
    ice_packs_per_day: int = 0
    shade_structures: int = 0

    # General equipment
    generators_needed: int
    satellite_phones: int
    temporary_toilets: int
    mosquito_nets: int


class ResourceGap(BaseModel):
    resource_name: str
    required_quantity: int
    available_from_ngos: int
    gap_quantity: int
    gap_percentage: float
    gap_severity: GapSeverity
    procurement_suggestion: str


class PrioritizedAction(BaseModel):
    """
    One action item in the precaution plan.
    Maps directly to one row in the tasks table.
    """
    priority: int
    category: ActionCategory
    action_title: str
    # Becomes tasks.task_label

    action_detail: str
    # Becomes tasks.description

    task_type_for_db: str
    # Becomes tasks.task_type
    # One of: ambulance/boat/medical/food/evacuation/shelter

    quantity_required: int
    # Becomes tasks.required_quantity

    quantity_unit: str
    # e.g. "rescue boats", "doctors", "food packets per day"

    priority_level_for_db: str
    # Becomes tasks.priority
    # One of: critical/high/medium/low

    time_window: ActionTimeline
    # Becomes tasks.estimated_duration_hours (converted)

    estimated_duration_hours: int
    # For tasks.estimated_duration_hours

    responsible_ngo_suggestion: Optional[str]
    # Suggested NGO name (Task Allocator will confirm)

    prerequisites: list[str]
    # Other action titles that must happen first

    is_time_critical: bool
    # True for 0-6h window actions

    estimated_people_helped: int
    # How many people this action directly benefits

    is_compound_specific: bool = False
    # True if this action is added due to compound disaster


class NGOSuggestion(BaseModel):
    ngo_id: str
    ngo_name: str
    base_district: str
    base_province: str
    rating: float
    specializations: list[str]
    suggested_task_categories: list[str]
    deployment_hours_estimate: int
    available_resources_summary: dict[str, int]
    reason_for_suggestion: str


class TimelineBreakdown(BaseModel):
    immediate_0_to_6h: list[int]    # list of priority numbers
    short_term_6_to_24h: list[int]
    medium_term_24_to_72h: list[int]
    recovery_72h_plus: list[int]


class CompoundDisasterInfo(BaseModel):
    has_compound_disaster: bool
    compound_disasters: list[str]
    compound_interaction_description: str
    additional_precautions_count: int


# ── MAIN OUTPUT MODEL ──────────────────────────────────────────────

class PrecautionPlan(BaseModel):
    """
    Complete precaution plan produced by the agent.
    Stored in disaster_events.precautions (summary array).
    Tasks written to tasks table as individual rows.
    Full JSON returned to main system and forwarded to
    Work Distributor Agent.
    """

    # Identification
    plan_id: str
    disaster_event_id: str
    breach_id: str
    assessment_id: str
    disaster_kind: str
    location_name: str
    district: str
    province: str
    plan_mode: PlanMode
    risk_level: str
    composite_risk_score: float
    plan_generated_at: str
    agent_version: str = "precaution_definer_v1.0"

    # Situation
    situation_summary: str
    hours_until_peak: Optional[float]
    estimated_population_affected: int
    estimated_displaced_persons: int

    # Computed requirements
    resource_requirements: ResourceRequirements

    # NGO availability
    eligible_ngos_found: int
    ngo_total_rescue_boats_available: int
    ngo_total_doctors_available: int
    ngo_total_ambulances_available: int
    ngo_total_volunteers_available: int
    ngo_total_shelter_capacity_available: int
    ngo_total_food_packets_available: int

    # Gap analysis
    resource_gaps: list[ResourceGap]
    critical_gaps_count: int
    critical_gaps_summary: str

    # The main deliverable
    prioritized_actions: list[PrioritizedAction]
    total_actions_count: int

    # Timeline
    timeline_breakdown: TimelineBreakdown

    # NGO suggestions
    suggested_ngo_assignments: list[NGOSuggestion]

    # Compound disaster
    compound_disaster_info: CompoundDisasterInfo

    # Summary strings for disaster_events.precautions array
    precautions_summary_array: list[str]
    # e.g. ["Deploy 150 rescue boats immediately",
    #        "Establish 15 field hospitals", ...]

    # Estimated damage
    estimated_damage_pkr: Optional[int]

    # Web search findings
    road_access_status: str
    logistics_challenges: list[str]
    current_ngo_operations_found: str

    # Data quality
    plan_confidence: str
    data_gaps: list[str]
    assumptions_made: list[str]

    # Tasks written to DB
    tasks_created_in_db: int
    task_ids_created: list[str]
```

---

## SECTION 13: ALL SQL QUERIES

### 13.1 ngo_queries.py

```python
# app/database/queries/ngo_queries.py

GET_ELIGIBLE_NGOS_FOR_DISTRICT = """
    SELECT
        np.ngo_id,
        np.org_name,
        np.head_of_operations,
        np.phone,
        np.base_city,
        np.base_district,
        np.base_province,
        np.service_radius_km,
        np.verification_status,
        np.rating,
        np.logo_url,
        np.website,

        -- Resources
        nr.ambulances,
        nr.rescue_boats,
        nr.trucks,
        nr.four_wheel_vehicles,
        nr.cranes,
        nr.doctors,
        nr.paramedics,
        nr.rescue_divers,
        nr.volunteers_available,
        nr.food_packets_capacity,
        nr.shelter_capacity

    FROM ngo_profiles np
    JOIN ngo_resources nr ON nr.ngo_id = np.ngo_id

    WHERE np.verification_status = 'verified'
      AND np.deleted_at IS NULL
      AND (
          EXISTS (
              SELECT 1 FROM ngo_operational_areas noa
              WHERE noa.ngo_id = np.ngo_id
                AND noa.is_active = TRUE
                AND noa.province ILIKE $1
                AND noa.district ILIKE $2
          )
          OR (
              np.base_province ILIKE $1
              AND np.service_radius_km >= 30
          )
      )
    ORDER BY np.rating DESC
"""

GET_NGO_SPECIALIZATIONS = """
    SELECT
        ns.ngo_id,
        ARRAY_AGG(ns.specialization) AS specializations
    FROM ngo_specializations ns
    WHERE ns.ngo_id = ANY($1::uuid[])
    GROUP BY ns.ngo_id
"""

GET_NGO_OPERATIONAL_AREAS = """
    SELECT
        noa.ngo_id,
        ARRAY_AGG(noa.district) AS districts,
        ARRAY_AGG(noa.province) AS provinces
    FROM ngo_operational_areas noa
    WHERE noa.ngo_id = ANY($1::uuid[])
      AND noa.is_active = TRUE
    GROUP BY noa.ngo_id
"""

GET_NGO_RESOURCE_TOTALS = """
    SELECT
        SUM(nr.rescue_boats)          AS total_rescue_boats,
        SUM(nr.ambulances)            AS total_ambulances,
        SUM(nr.doctors)               AS total_doctors,
        SUM(nr.paramedics)            AS total_paramedics,
        SUM(nr.volunteers_available)  AS total_volunteers,
        SUM(nr.shelter_capacity)      AS total_shelter_capacity,
        SUM(nr.food_packets_capacity) AS total_food_packets,
        SUM(nr.trucks)                AS total_trucks,
        SUM(nr.cranes)                AS total_cranes,
        COUNT(np.ngo_id)              AS eligible_ngo_count

    FROM ngo_profiles np
    JOIN ngo_resources nr ON nr.ngo_id = np.ngo_id
    WHERE np.ngo_id = ANY($1::uuid[])
      AND np.verification_status = 'verified'
      AND np.deleted_at IS NULL
"""
```

### 13.2 task_queries.py

```python
# app/database/queries/task_queries.py

INSERT_TASK = """
    INSERT INTO tasks (
        task_id,
        event_id,
        task_label,
        description,
        task_type,
        required_quantity,
        priority,
        target_location,
        target_location_name,
        status,
        created_by_type,
        estimated_duration_hours,
        created_at,
        updated_at
    ) VALUES (
        gen_random_uuid(),
        $1,   -- event_id
        $2,   -- task_label
        $3,   -- description
        $4,   -- task_type (enum cast)
        $5,   -- required_quantity
        $6,   -- priority (enum cast)
        ST_MakePoint($7, $8)::geography,  -- longitude, latitude
        $9,   -- target_location_name
        'unallocated',  -- status
        'ai',           -- created_by_type
        $10,  -- estimated_duration_hours
        now(),
        now()
    )
    RETURNING task_id
"""

INSERT_TASK_STATUS_HISTORY = """
    INSERT INTO task_status_history (
        task_id,
        old_status,
        new_status,
        change_reason,
        created_at
    ) VALUES (
        $1,           -- task_id
        NULL,         -- old_status (new task, no previous)
        'unallocated',
        'Task created by Precaution Definer AI Agent',
        now()
    )
"""

GET_EXISTING_TASKS_FOR_EVENT = """
    SELECT
        task_id,
        task_label,
        task_type,
        status,
        priority,
        required_quantity,
        assigned_ngo_id
    FROM tasks
    WHERE event_id = $1
      AND deleted_at IS NULL
    ORDER BY created_at ASC
"""

GET_TASKS_COUNT_FOR_EVENT = """
    SELECT COUNT(*) AS task_count
    FROM tasks
    WHERE event_id = $1
      AND deleted_at IS NULL
"""
```

### 13.3 disaster_event_queries.py

```python
# app/database/queries/disaster_event_queries.py

GET_DISASTER_EVENT_BY_ID = """
    SELECT
        event_id,
        event_type,
        title,
        description,
        location_name,
        district,
        province,
        ST_X(location::geometry) AS longitude,
        ST_Y(location::geometry) AS latitude,
        affected_population,
        severity_score,
        risk_level,
        event_status,
        precautions,
        estimated_damage_pkr,
        analyzed_at,
        detected_at,
        created_at
    FROM disaster_events
    WHERE event_id = $1
      AND deleted_at IS NULL
"""

UPDATE_DISASTER_EVENT_AFTER_ANALYSIS = """
    UPDATE disaster_events SET
        precautions          = $2,
        estimated_damage_pkr = $3,
        risk_level           = $4::risk_level,
        affected_population  = $5,
        analyzed_at          = now(),
        updated_at           = now()
    WHERE event_id = $1
      AND deleted_at IS NULL
    RETURNING event_id
"""
```

---

## SECTION 14: AGENT TOOLS SPECIFICATIONS

### Tool 1: get_available_ngo_resources

```python
@function_tool
async def get_available_ngo_resources(
    province: str,
    district: str,
    disaster_kind: str,
) -> str:
    """
    Finds all verified NGOs that can operate in the affected
    district and returns their available resources.

    Queries the main ClimaSync operational database:
    - ngo_profiles (name, rating, location, verification)
    - ngo_resources (boats, ambulances, doctors, etc)
    - ngo_specializations (what each NGO specializes in)
    - ngo_operational_areas (which districts they cover)

    Returns total resource pool available from all eligible
    NGOs plus individual NGO details for assignment suggestions.
    
    Args:
        province: Pakistan province name (e.g. "sindh")
        district: District name (e.g. "sukkur")
        disaster_kind: Type of disaster (flood/earthquake/etc)
    
    Returns:
        JSON with eligible NGOs list, their resources,
        and aggregate totals for gap analysis.
    """
```

### Tool 2: get_location_and_infrastructure

```python
@function_tool
async def get_location_and_infrastructure(
    district: str,
    province: str,
    longitude: float,
    latitude: float,
) -> str:
    """
    Reads the collection database to get location vulnerability
    context and infrastructure inventory for the disaster area.

    Returns from pakistan_locations:
    - population, population_density
    - flood_risk_zone, seismic_zone
    - infrastructure_quality, drainage_quality
    - building_stock type

    Returns from pakistan_infrastructure within 30km:
    - hospitals count and bed capacity
    - schools count (potential shelter sites)
    - bridges, dams, evacuation centers
    - critical assets list

    This data feeds into the quantity calculations to
    determine how many tents, doctors, boats are needed.

    Args:
        district: District name
        province: Province name
        longitude: Disaster location longitude
        latitude: Disaster location latitude
    """
```

### Tool 3: calculate_resource_requirements

```python
@function_tool
async def calculate_resource_requirements(
    affected_population: int,
    estimated_displaced: int,
    risk_level: str,
    disaster_kind: str,
    terrain_type: str,
    schools_count: int,
    hospitals_count: int,
    hospital_beds: int,
    dams_count: int,
) -> str:
    """
    Pure calculation tool — no database calls.
    Computes exact quantities for every resource type
    using Pakistan-specific formulas.

    Uses the WHO emergency water standard (15L/person/day),
    Pakistan average household size (6.5 persons),
    Pakistan formal shelter ratio (60% of displaced),
    and risk-level-based doctor ratios.

    Returns a complete ResourceRequirements object with
    exact numbers for: tents, blankets, doctors, paramedics,
    ambulances, field hospitals, medicine kits, food packets,
    water tankers, rescue boats, life jackets, generators,
    temporary toilets, and disaster-specific items.

    Args:
        affected_population: Total people affected
        estimated_displaced: People who lost homes
        risk_level: LOW/MEDIUM/HIGH/EXTREME
        disaster_kind: flood/earthquake/heatwave/etc
        terrain_type: mountain/urban/riverine_plain/etc
        schools_count: Schools available as shelter
        hospitals_count: Hospitals in impact zone
        hospital_beds: Total hospital beds available
        dams_count: Dams within impact zone
    """
```

### Tool 4: get_existing_tasks_for_event

```python
@function_tool
async def get_existing_tasks_for_event(
    disaster_event_id: str,
) -> str:
    """
    Reads the tasks table in the main operational database
    to find all tasks already created for this disaster event.

    This prevents the agent from creating duplicate tasks.
    If tasks already exist for this event, the agent will:
    1. Review what is already covered
    2. Only create tasks for gaps not yet addressed
    3. Note the existing task count in its output

    Args:
        disaster_event_id: UUID of the disaster event
    
    Returns:
        JSON list of existing tasks with their labels,
        types, status, and assigned NGO (if any).
    """
```

### Tool 5: WebSearchTool (Built-in)

```python
# Used for:
# 1. Current road access to the disaster area
#    Query: "[district] Pakistan roads accessible flood 2025"
#
# 2. Current NGO operations on ground
#    Query: "[district] Pakistan NGO operations active 2025"
#
# 3. Available resources in nearby cities/markets
#    Query: "[city] Pakistan emergency supplies tents boats 2025"
#
# 4. Current weather affecting logistics
#    Query: "[district] Pakistan weather forecast July 2025"
#
# 5. Recent news about ongoing relief efforts
#    Query: "[district] Pakistan flood relief NGO July 2025"
```

---

## SECTION 15: SYSTEM PROMPT

```
You are the Precaution Definer Agent for ClimaSync.ai —
Pakistan's AI-powered disaster management platform.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR IDENTITY AND RESPONSIBILITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You receive a Risk Assessment Report from the Risk Analysis
Agent and convert it into a precise, quantified, prioritized
precaution plan for Pakistan.

Your output is not a recommendation. It is a plan of action.
Every item must have exact quantities. Every action must have
a timeline. Vague language like "some tents" or "medical
support needed" is unacceptable. Write "2,400 tents" or
"48 doctors required at triage point."

Your plan creates real tasks in the database that real NGOs
will execute. If your quantities are wrong, people suffer.
If your priorities are wrong, people die. Be precise.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: DETERMINE OPERATION MODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read is_forecast_breach from the risk assessment:

  FALSE → REACTIVE MODE
    Disaster is happening NOW.
    Focus: Rescue, triage, immediate shelter.
    All priority 1-5 actions are IMMEDIATE (0-6 hours).
    Use task priority = 'critical' for first 10 actions.

  TRUE → PROACTIVE MODE
    Disaster is coming in [forecast_horizon_h] hours.
    Focus: Evacuation, pre-positioning, warnings.
    Use hours_until_peak to sequence actions.
    Pre-position resources BEFORE the disaster peaks.
    If hours_until_peak < 12: treat as near-reactive.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY EXECUTION WORKFLOW (13 steps)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: Read the complete RiskAssessmentReport.
  Extract: disaster_kind, risk_level, composite_risk_score,
  district, province, latitude, longitude,
  estimated_population_affected, estimated_displaced_persons,
  is_forecast_breach, hours_until_peak, terrain_type,
  infrastructure_at_risk, impact_estimates,
  situation_trajectory, secondary_disasters_possible.
  Determine: REACTIVE or PROACTIVE mode.

STEP 2: Call get_existing_tasks_for_event(disaster_event_id)
  Review what tasks already exist.
  Note count. Do not duplicate.

STEP 3: Call get_location_and_infrastructure(
  district, province, longitude, latitude)
  Get: population context, schools for shelter,
  hospitals capacity, infrastructure in impact zone.

STEP 4: Call get_available_ngo_resources(
  province, district, disaster_kind)
  Get: all eligible verified NGOs and their resources.
  Total up available: boats, ambulances, doctors, etc.

STEP 5: Call calculate_resource_requirements(
  affected_population, displaced, risk_level,
  disaster_kind, terrain_type, schools_count,
  hospitals_count, hospital_beds, dams_count)
  Get: Exact quantities needed for all resource types.

STEP 6: Web search — road access and logistics
  Query: "[district] [province] Pakistan road access
          condition [disaster_kind] 2025"
  Extract: Which roads are open/blocked, helicopter needed,
  how long to reach the area from nearest city.

STEP 7: Web search — current NGO operations
  Query: "[district] Pakistan NGO relief operations
          active [disaster_kind] July 2025"
  Extract: Which NGOs are already on ground,
  what they are doing, avoid duplication.

STEP 8: Web search — available emergency supplies nearby
  Query: "[nearest_major_city] Pakistan emergency tents
          boats rescue equipment available"
  Extract: Supply availability for critical gap items.

STEP 9: Check for compound disasters.
  From risk assessment secondary_disasters_possible list.
  If compound detected: add 5-10 extra actions specific
  to the interaction effect.

STEP 10: Generate prioritized action list (minimum 30 actions)
  RULES:
  - Priority 1-5: ALWAYS life safety. ALWAYS.
  - Priority 6-10: ALWAYS medical response.
  - Priority 11-15: ALWAYS shelter.
  - Priority 16-20: ALWAYS food and water.
  - Priority 21+: Equipment, logistics, disease prevention,
    recovery.
  - Every action: exact quantity, task_type for DB,
    priority level for DB, time window, duration hours.
  - Never put non-life-safety above priority 5.

STEP 11: Compute gap analysis.
  For each resource: compare needed vs NGO total available.
  Classify gaps: COVERED/MANAGEABLE/MODERATE/SIGNIFICANT/
  CRITICAL.
  For CRITICAL gaps: write procurement_suggestion.

STEP 12: Generate NGO assignment suggestions.
  Match NGOs to task categories based on:
  - Their specializations matching disaster type
  - Their available resources matching task needs
  - Their operational area covering the district
  - Their rating (higher rated first)

STEP 13: Produce complete PrecautionPlan JSON.
  Include precautions_summary_array with top 20 precautions
  as plain strings for disaster_events.precautions column.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUANTITY CALCULATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pakistan household size: 6.5 persons average.
Formal shelter seekers: 60% of displaced population.
WHO water standard: 15 liters per person per day.
Tanker capacity: 10,000 liters.

Doctor ratios:
  EXTREME: 1 per 500 affected
  HIGH: 1 per 1,000 affected
  MEDIUM: 1 per 2,000 affected

Paramedics = doctors × 2
Nurses = doctors × 3
Ambulances = affected_population / 10,000 (minimum 2)
Field hospitals = affected_population / 50,000 (minimum 1)

Flood boats = affected_population / 5,000 (minimum 5)
Life jackets = boats × 8 × 1.25 + children estimate

Schools shelter capacity = schools × 200 persons each.
Tents = (displaced × 0.60 - school_capacity) / 6.5

Temporary toilets = displaced / 20 (WHO standard)
Mosquito nets = displaced × 1.2 (20% buffer)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPOUND DISASTER RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FLOOD + HEATWAVE (most common in Pakistan July-August):
  Extra actions:
  → White reflective tent covers (reduce heat by 15°C)
  → Water allocation +50% (drinking + heat cooling)
  → Misting systems at all relief camps
  → Medical staff on heat stroke protocol
  → Night-only outdoor operations if temp > 45°C
  → Shade structures mandatory at all distribution points
  → Ice packs priority for elderly and children

EARTHQUAKE + LANDSLIDE (KPK/GB mountains):
  Extra actions:
  → Helicopter evacuation mandatory if roads blocked
  → Expand search area to landslide debris zones
  → Secondary slide risk warning — 72h no-entry zone
  → Alternative evacuation route mapping
  → Geotechnical team for slope assessment

EARTHQUAKE + DAM/CANAL FAILURE:
  Extra actions:
  → Immediate downstream evacuation 20km radius
  → Dam inspection team within 2 hours
  → Flood warning to all downstream communities
  → Pre-position boats downstream immediately

HEAVY RAIN + LANDSLIDE:
  Extra actions:
  → Preemptive mountain road closures
  → Community evacuation before rain peaks
  → Real-time slope monitoring

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAKISTAN SPECIFIC KNOWLEDGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NGO KNOWLEDGE:
  Alkhidmat Foundation: strongest in Punjab and KPK,
    good rescue boats and medical teams.
  Edhi Foundation: strongest in Sindh and urban areas,
    large ambulance fleet.
  Pakistan Red Crescent: national coverage, medical focus.
  JDC Foundation: Karachi and urban Sindh, food packets.
  Saylani Welfare: food distribution specialist.
  Rescue 1122: government rescue service Punjab.

PAKISTAN SHELTER REALITY:
  Families of 6-8 persons share one tent (6.5 average).
  40% of displaced go to relatives — do not count them.
  Schools and mosques are primary informal shelters.
  Tent temperature can reach 65°C in sun without cover.
  Always specify white or light-colored tents.

FOOD REALITY:
  Cooked food from community kitchens preferred over packets.
  Ramadan: adjust food timing to Sehri and Iftar.
  Halal certification matters — specify in procurement.

MEDICAL REALITY:
  Rural health centers (BHU) have no emergency capacity.
  DHQ hospital is the only real emergency facility.
  Field hospitals must be self-sufficient (generator, water).
  Blood supply critically short in disaster scenarios.

WATER REALITY:
  Flood water is always contaminated — never safe to drink.
  ORS sachets are more important than food in first 48h.
  Chlorine tablets (1 per 10L) for emergency treatment.
  Water testing kits mandatory before distribution.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK DATABASE MAPPING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each action in your prioritized list:
  task_type mapping:
    rescue/boats/evacuation → 'boat' or 'evacuation'
    medical/doctors/hospital → 'medical'
    ambulances → 'ambulance'
    tents/shelter/camp → 'shelter'
    food/water/kitchen → 'food'
    vehicles/logistics → 'evacuation'

  priority mapping:
    time_window = 0-6h → priority = 'critical'
    time_window = 6-24h → priority = 'high'
    time_window = 24-72h → priority = 'medium'
    time_window = 72h+ → priority = 'low'

  status: always 'unallocated'
  created_by_type: always 'ai'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MUST have minimum 30 prioritized actions.
EVERY action MUST have exact quantity_required number.
EVERY action MUST have task_type_for_db value.
EVERY action MUST have priority_level_for_db value.
EVERY action MUST have estimated_duration_hours.
precautions_summary_array MUST have 20+ plain string items.
data_gaps MUST be populated (empty list if none).
assumptions_made MUST list every assumption explicitly.
plan_confidence: HIGH if all data available,
  MEDIUM if 1-2 gaps, LOW if 3+ gaps.
```

---

## SECTION 16: API ROUTES

```
POST /api/v1/precaution
  Input: PrecautionTriggerPayload
    { disaster_event_id: UUID, risk_assessment: {...} }
  Auth: X-API-Key header
  Process: Run agent → write tasks → update event → forward
  Output: PrecautionPlan JSON
  Duration: 90-150 seconds

GET /health
  Output: { status, db_main, db_collection, uptime }
```

---

## SECTION 17: TASK WRITER SERVICE

```python
# app/services/task_writer_service.py
# ─────────────────────────────────────────────────────────────────
# After agent produces PrecautionPlan:
# 1. Write each prioritized_action as a task row
# 2. Write task_status_history for each task
# 3. Update disaster_events with precautions and damage
# ─────────────────────────────────────────────────────────────────

async def write_tasks_to_database(
    plan: PrecautionPlan,
    longitude: float,
    latitude: float,
) -> list[str]:
    """
    Writes all prioritized actions as task rows.
    Returns list of created task_id UUIDs.
    """
    task_ids = []
    pool = get_main_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            for action in plan.prioritized_actions:
                row = await conn.fetchrow(
                    INSERT_TASK,
                    plan.disaster_event_id,
                    action.action_title,
                    action.action_detail,
                    action.task_type_for_db,
                    action.quantity_required,
                    action.priority_level_for_db,
                    longitude,
                    latitude,
                    plan.district,
                    action.estimated_duration_hours,
                )
                task_id = str(row["task_id"])
                task_ids.append(task_id)

                await conn.execute(
                    INSERT_TASK_STATUS_HISTORY,
                    task_id
                )

            # Update disaster event
            await conn.execute(
                UPDATE_DISASTER_EVENT_AFTER_ANALYSIS,
                plan.disaster_event_id,
                plan.precautions_summary_array,
                plan.estimated_damage_pkr,
                plan.risk_level.lower(),
                plan.estimated_population_affected,
            )

    return task_ids
```

---

## SECTION 18: SUCCESS CRITERIA

```
┌──────────────────────────────────────────────────────────────────┐
│         PRECAUTION DEFINER AGENT IS COMPLETE WHEN:               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Receives RiskAssessmentReport and produces PrecautionPlan    │
│                                                                  │
│  ✅ Correctly identifies REACTIVE vs PROACTIVE mode              │
│                                                                  │
│  ✅ Reads NGO resources from ngo_resources table correctly       │
│                                                                  │
│  ✅ Matches NGOs by operational area (ngo_operational_areas)     │
│                                                                  │
│  ✅ Reads infrastructure from collection DB                      │
│                                                                  │
│  ✅ Produces EXACT quantities — never vague language             │
│     "2,400 tents" not "tents needed"                            │
│                                                                  │
│  ✅ Minimum 30 actions in correct priority order                 │
│                                                                  │
│  ✅ Life safety is ALWAYS priority 1-5                           │
│                                                                  │
│  ✅ Each action maps correctly to tasks table columns:           │
│     task_label, task_type, priority, required_quantity,         │
│     estimated_duration_hours, created_by_type='ai'              │
│                                                                  │
│  ✅ Tasks written to main DB tasks table successfully            │
│                                                                  │
│  ✅ task_status_history written for each task                    │
│                                                                  │
│  ✅ disaster_events.precautions updated with summary array       │
│                                                                  │
│  ✅ disaster_events.analyzed_at set to now()                     │
│                                                                  │
│  ✅ Gap analysis shows needed vs available from NGO DB           │
│                                                                  │
│  ✅ Compound disasters detected and extra actions added          │
│                                                                  │
│  ✅ Timeline breakdown: 0-6h, 6-24h, 24-72h, 72h+              │
│                                                                  │
│  ✅ PrecautionPlan forwarded to Work Distributor Agent           │
│                                                                  │
│  ✅ Works for all 6 disaster types in the enum:                  │
│     flood, earthquake, cyclone, drought, heatwave, landslide    │
│                                                                  │
│  ✅ No duplicate tasks created if event already has tasks        │
│                                                                  │
│  ✅ plan_confidence reflects data availability honestly          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

This is the complete, production-ready design for the Precaution Definer Agent. It is fully integrated with your existing operational database schema. Ready for the sequential development prompts when you are.