-- Store a PlayerBlip in the database
INSERT INTO "EventBuffer"."PlayerBlip" (
    "timestamp",
    "server_id",
    "continent_id",
    "player_id",
    "base_id"
)
VALUES (
    %s, %s, %s, %s, %s
);