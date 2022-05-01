-- Store a PlayerBlip in the database
INSERT INTO "event"."PlayerBlip" (
    "timestamp",
    "server_id",
    "continent_id",
    "player_id",
    "base_id"
)
VALUES (
    $1, $2, $3, $4, $5
);