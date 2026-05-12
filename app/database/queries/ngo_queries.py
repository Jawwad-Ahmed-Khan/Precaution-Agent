GET_ELIGIBLE_NGOS_FOR_DISTRICT = """
    SELECT 
        np.ngo_id, np.org_name, np.base_district, np.base_province, 
        np.service_radius_km, np.verification_status, np.rating, np.deleted_at,
        nr.ambulances, nr.rescue_boats, nr.trucks, nr.four_wheel_vehicles,
        nr.cranes, nr.doctors, nr.paramedics, nr.rescue_divers, 
        nr.volunteers_available, nr.food_packets_capacity, nr.shelter_capacity
    FROM ngo_profiles np
    JOIN ngo_resources nr ON nr.ngo_id = np.ngo_id
    WHERE np.verification_status = 'verified'
      AND np.deleted_at IS NULL
      AND (
        EXISTS (
          SELECT 1 FROM ngo_operational_areas noa
          WHERE noa.ngo_id = np.ngo_id
            AND noa.is_active = TRUE
            AND LOWER(noa.province) = LOWER($1)
            AND LOWER(noa.district) = LOWER($2)
        )
        OR (
          LOWER(np.base_province) = LOWER($1)
          AND np.service_radius_km >= 30
        )
      )
    ORDER BY np.rating DESC;
"""

GET_NGO_SPECIALIZATIONS_FOR_NGOS = """
    SELECT ngo_id, ARRAY_AGG(specialization) AS specializations
    FROM ngo_specializations
    WHERE ngo_id = ANY($1::uuid[])
    GROUP BY ngo_id;
"""

GET_NGO_OPERATIONAL_AREAS_FOR_NGOS = """
    SELECT ngo_id, 
        ARRAY_AGG(district) AS districts,
        ARRAY_AGG(province) AS provinces
    FROM ngo_operational_areas
    WHERE ngo_id = ANY($1::uuid[])
      AND is_active = TRUE
    GROUP BY ngo_id;
"""

GET_NGO_RESOURCE_TOTALS = """
    SELECT 
        SUM(nr.rescue_boats) AS total_rescue_boats,
        SUM(nr.ambulances) AS total_ambulances,
        SUM(nr.doctors) AS total_doctors,
        SUM(nr.paramedics) AS total_paramedics,
        SUM(nr.volunteers_available) AS total_volunteers,
        SUM(nr.shelter_capacity) AS total_shelter_capacity,
        SUM(nr.food_packets_capacity) AS total_food_packets,
        SUM(nr.trucks) AS total_trucks,
        SUM(nr.cranes) AS total_cranes,
        COUNT(np.ngo_id) AS eligible_ngo_count
    FROM ngo_profiles np
    JOIN ngo_resources nr ON nr.ngo_id = np.ngo_id
    WHERE np.ngo_id = ANY($1::uuid[])
      AND np.verification_status = 'verified'
      AND np.deleted_at IS NULL;
"""
