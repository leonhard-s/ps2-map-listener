-- Store a PlayerLogout blip in the database
INSERT INTO "EventBuffer"."PlayerLogout" (
    "timestamp",
    "player_id"
)
VALUES (
    %s, %s
);