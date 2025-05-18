--  1. VIEWS

-- A. Recently added 10 games
DROP VIEW IF EXISTS Recent_Games;
CREATE VIEW Recent_Games AS
SELECT * FROM BOARD_GAMES
ORDER BY updated_at DESC
LIMIT 10;

-- B. List of users for admin
DROP VIEW IF EXISTS Admin_UserList;
CREATE VIEW Admin_UserList AS
SELECT user_id, username, is_admin, is_blocked
FROM Users;

-- C. List of games for admin to manage
DROP VIEW IF EXISTS Admin_BoardGames;
CREATE VIEW Admin_BoardGames AS
SELECT game_id, name, year_published, min_players, max_players, average_rating
FROM BOARD_GAMES;

-- D. List of games owned and number of owners
DROP VIEW IF EXISTS Games_Owned_Count;
CREATE VIEW Games_Owned_Count AS
SELECT bg.name, COUNT(go.user_id) AS owners_count
FROM BOARD_GAMES bg
JOIN GameOwned go ON bg.game_id = go.game_id
GROUP BY bg.game_id;

-- E. Events and number of participants
DROP VIEW IF EXISTS Event_Participation;
CREATE VIEW Event_Participation AS
SELECT e.name, e.event_time, COUNT(p.user_id) AS participants
FROM EVENTS e
LEFT JOIN ParticipateTo p ON e.event_id = p.event_id
GROUP BY e.event_id;

-- F. Games and their genres
DROP VIEW IF EXISTS Game_Genres;
CREATE VIEW Game_Genres AS
SELECT bg.name AS game, g.name AS genre
FROM BOARD_GAMES bg
JOIN IsOfGenre ig ON bg.game_id = ig.game_id
JOIN GENRES g ON ig.genre_id = g.genre_id;

-- G. Genres and number of games in each
DROP VIEW IF EXISTS Genre_Game_Count;
CREATE VIEW Genre_Game_Count AS
SELECT g.name AS genre, COUNT(ig.game_id) AS total_games
FROM GENRES g
LEFT JOIN IsOfGenre ig ON g.genre_id = ig.genre_id
GROUP BY g.genre_id;


-- 2. INDEXES (to optimize performance)

CREATE INDEX idx_user_username ON Users(username);
CREATE INDEX idx_game_name ON BOARD_GAMES(name);
CREATE INDEX idx_rating_game_user ON Rating(game_id, user_id);
CREATE INDEX idx_event_time ON EVENTS(event_time);


-- 3. TRIGGERS

-- A. Update average_rating when new rating added
DROP TRIGGER IF EXISTS update_rating_avg;

CREATE TRIGGER update_rating_avg AFTER INSERT ON Rating
FOR EACH ROW
BEGIN
  UPDATE BOARD_GAMES
  SET average_rating = (
    SELECT AVG(Stars)
    FROM Rating
    WHERE game_id = NEW.game_id
  )
  WHERE game_id = NEW.game_id;
END;



-- B. Update nb_participant when someone joins event
DROP TRIGGER IF EXISTS update_nb_participant;


CREATE TRIGGER update_nb_participant AFTER INSERT ON ParticipateTo
FOR EACH ROW
BEGIN
  UPDATE EVENTS
  SET nb_participant = nb_participant + 1
  WHERE event_id = NEW.event_id;
END;



-- C. Update updated_at on game modification
DROP TRIGGER IF EXISTS set_updated_at;


CREATE TRIGGER set_updated_at BEFORE UPDATE ON BOARD_GAMES
FOR EACH ROW
BEGIN
  SET NEW.updated_at = NOW();
END;



-- D. Check max participants before adding to event
DROP TRIGGER IF EXISTS check_max_participants;


CREATE TRIGGER check_max_participants BEFORE INSERT ON ParticipateTo
FOR EACH ROW
BEGIN
  DECLARE current_nb INT;
  DECLARE max_nb INT;
  SELECT nb_participant, max_participants INTO current_nb, max_nb
  FROM EVENTS WHERE event_id = NEW.event_id;

  IF current_nb >= max_nb THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Max participants reached for this event';
  END IF;
END;


-- E. Check venue capacity not exceeded by event
DROP TRIGGER IF EXISTS check_venue_capacity;


CREATE TRIGGER check_venue_capacity BEFORE INSERT ON EVENTS
FOR EACH ROW
BEGIN
  DECLARE max_venue INT;
  SELECT max_capacity INTO max_venue
  FROM VENUE WHERE venue_id = NEW.venue_id;

  IF NEW.max_participants > max_venue THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Max participants exceeds venue capacity';
  END IF;
END;



-- 4. STORED PROCEDURES & FUNCTIONS

-- A. Search for a game (by filters)
DROP PROCEDURE IF EXISTS SearchGame;

CREATE PROCEDURE SearchGame(
  IN y YEAR, IN g VARCHAR(50),
  IN minP INT, IN maxP INT,
  IN minT INT, IN maxT INT, IN age INT
)
BEGIN
  SELECT DISTINCT bg.*
  FROM BOARD_GAMES bg
  JOIN IsOfGenre ig ON bg.game_id = ig.game_id
  JOIN GENRES ge ON ig.genre_id = ge.genre_id
  WHERE (y IS NULL OR bg.year_published = y)
    AND (g IS NULL OR ge.name = g)
    AND bg.min_players >= minP
    AND bg.max_players <= maxP
    AND bg.min_playtime >= minT
    AND bg.max_playtime <= maxT
    AND bg.min_age <= age;
END;



-- B. Games in a user’s wishlist
DROP FUNCTION IF EXISTS GetWishlist;

CREATE FUNCTION GetWishlist(userID INT)
RETURNS TEXT
DETERMINISTIC
BEGIN
  DECLARE result TEXT DEFAULT '';
  SELECT GROUP_CONCAT(bg.name SEPARATOR ', ')
  INTO result
  FROM WishList wl
  JOIN BOARD_GAMES bg ON wl.game_id = bg.game_id
  WHERE wl.user_id = userID;
  RETURN result;
END;



-- C. Users for a given event
DROP PROCEDURE IF EXISTS GetEventUsers;

CREATE PROCEDURE GetEventUsers(IN eventID INT)
BEGIN
  SELECT u.username
  FROM Users u
  JOIN ParticipateTo pt ON pt.user_id = u.user_id
  WHERE pt.event_id = eventID;
END;



-- D. Ratings for a game
DROP PROCEDURE IF EXISTS GetRatingsForGame;

CREATE PROCEDURE GetRatingsForGame(IN gameID INT)
BEGIN
  SELECT u.username, r.Stars, r.comment
  FROM Rating r
  JOIN Users u ON r.user_id = u.user_id
  WHERE r.game_id = gameID;
END;



-- E. Blocked/unblocked users
DROP PROCEDURE IF EXISTS GetUsersByBlockStatus;

CREATE PROCEDURE GetUsersByBlockStatus(IN blockStatus BOOLEAN)
BEGIN
  SELECT * FROM Users WHERE is_blocked = blockStatus;
END;



-- F. Modify event info
DROP PROCEDURE IF EXISTS UpdateEvent;

CREATE PROCEDURE UpdateEvent(
  IN e_id INT, IN new_name VARCHAR(50), IN new_desc VARCHAR(255),
  IN new_max INT, IN new_time DATETIME, IN new_vid INT
)
BEGIN
  UPDATE EVENTS
  SET name = new_name,
      description = new_desc,
      max_participants = new_max,
      event_time = new_time,
      venue_id = new_vid
  WHERE event_id = e_id;
END;


-- G. Games owned by a user
DROP PROCEDURE IF EXISTS GetOwnedGames;

CREATE PROCEDURE GetOwnedGames(IN userID INT)
BEGIN
  SELECT bg.name
  FROM OwnedGames og
  JOIN BOARD_GAMES bg ON og.game_id = bg.game_id
  WHERE og.user_id = userID;
END;




