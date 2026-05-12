GET_DISASTER_EVENT_BY_ID = """
    SELECT event_id, event_type, title, description,
        location_name, district, province,
        ST_X(location::geometry) AS longitude,
        ST_Y(location::geometry) AS latitude,
        affected_population, severity_score, risk_level,
        event_status, precautions, estimated_damage_pkr,
        analyzed_at, detected_at, created_at
    FROM disaster_events
    WHERE event_id = $1 AND deleted_at IS NULL;
"""

UPDATE_DISASTER_EVENT_AFTER_ANALYSIS = """
    UPDATE disaster_events SET
        precautions = $2,
        estimated_damage_pkr = $3,
        risk_level = $4::risk_level,
        affected_population = $5,
        analyzed_at = now(),
        updated_at = now()
    WHERE event_id = $1 AND deleted_at IS NULL
    RETURNING event_id;
"""
