-- Store a RelativePlayerBlip in the database
INSERT INTO "EventBuffer"."RelativePlayerBlip" (
    "timestamp",
    "server_id",
    "continent_id",
    "player_a_id",
    "player_b_id"
)
VALUES (
    %s, %s, %s, %s, %s
);