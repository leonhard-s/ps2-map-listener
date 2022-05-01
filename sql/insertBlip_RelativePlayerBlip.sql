-- Store a RelativePlayerBlip in the database
INSERT INTO "event"."RelativePlayerBlip" (
    "timestamp",
    "server_id",
    "continent_id",
    "player_a_id",
    "player_b_id"
)
VALUES (
    $1, $2, $3, $4, $5
);