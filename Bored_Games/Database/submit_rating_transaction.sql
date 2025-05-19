START TRANSACTION;

INSERT INTO Rating (user_id, game_id, Stars, comment)
VALUES ({user_id}, {game_id}, {stars}, {comment})
ON DUPLICATE KEY UPDATE 
    Stars = VALUES(Stars), 
    comment = VALUES(comment);

UPDATE BOARD_GAMES
SET average_rating = (
    SELECT ROUND(AVG(Stars), 2)
    FROM Rating
    WHERE game_id = {game_id}
)
WHERE game_id = {game_id};

COMMIT;


