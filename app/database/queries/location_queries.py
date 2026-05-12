GET_LOCATION_BY_DISTRICT_COLLECTION = """
    SELECT location_id, location_key, location_name,
        district, province,
        ST_X(coordinates::geometry) AS longitude,
        ST_Y(coordinates::geometry) AS latitude,
        elevation_m, population, population_density,
        flood_risk_zone, seismic_zone, heat_risk_zone,
        infrastructure_quality, drainage_quality, building_stock,
        is_active
    FROM pakistan_locations
    WHERE district ILIKE $1
      AND LOWER(province::TEXT) = LOWER($2)
      AND is_active = TRUE
    LIMIT 1;
"""

GET_INFRASTRUCTURE_WITHIN_RADIUS_COLLECTION = """
    SELECT asset_name, asset_type, capacity, capacity_unit,
        is_critical, serves_population, vulnerability_level,
        is_flood_resistant, is_seismic_resistant,
        ST_Distance(
            coordinates,
            ST_MakePoint($1, $2)::geography
        ) / 1000 AS distance_km
    FROM pakistan_infrastructure
    WHERE ST_DWithin(
        coordinates,
        ST_MakePoint($1, $2)::geography,
        $3
    )
    AND is_active = TRUE
    ORDER BY is_critical DESC, distance_km ASC;
"""
