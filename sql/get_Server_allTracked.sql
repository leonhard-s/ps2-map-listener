-- Retrieve all servers for which tracking is enabled
SELECT
    "id"
FROM
    "API_static"."Server"
WHERE
    "tracking_enabled" = true
;