-- Store a PlayerLogout blip in the database
INSERT INTO "event"."PlayerLogout" (
    "timestamp", 
    "player_id"
)
VALUES (
    $1, $2
);