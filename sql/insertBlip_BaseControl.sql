-- Store a BaseControl blip in the database
INSERT INTO "Blip"."BaseControl" (
    "timestamp",
    "server_id",
    "continent_id",
    "base_id",
    "old_faction_id",
    "new_faction_id"
)
VALUES (
    $1, $2, $3, $4, $5, $6
);