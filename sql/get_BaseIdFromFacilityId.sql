-- Accesses the public Map API to convert facility IDs to base IDs.
SELECT (
    "id"
)
FROM
    "PS2Map"."Public"
WHERE
    "facility_id" = $1
;
