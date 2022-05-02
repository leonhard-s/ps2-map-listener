-- Accesses the public Map API to convert facility IDs to base IDs.
SELECT (
    "id"
)
FROM
    "API"."Base"
WHERE
    "facility_id" = $1
;
