-- Accesses the public Map API to convert facility IDs to base IDs.
SELECT (
    "id"
)
FROM
    "API_static"."Base"
WHERE
    "facility_id" = %s
;
