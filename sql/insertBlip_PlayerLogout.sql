-- Store a PlayerLogout blip in the database
INSERT INTO "Blip"."PlayerLogout" (
    "timestamp", 
    "player_id"
)
VALUES (
    $1, $2
);