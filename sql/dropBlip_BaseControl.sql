-- Update a BaseControl blip in the database
DELETE FROM "Blip"."BaseControl"
WHERE
    "timestamp" = %s
AND
    "server_id" = %s
AND
    "base_id" = %s
;