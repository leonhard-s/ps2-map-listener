-- Store a BaseControl blip in the database
INSERT INTO "EventBuffer"."BaseControl" (
    "timestamp",
    "server_id",
    "continent_id",
    "base_id",
    "old_faction_id",
    "new_faction_id"
)
VALUES (
    %s, %s, %s, %s, %s, %s
);