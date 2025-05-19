--  1. VIEWS

-- User info
CREATE OR REPLACE VIEW user_info AS
SELECT user_id, username, is_admin
FROM Users;

-- Recently updated/added 10 games
CREATE OR REPLACE VIEW Recent_Games AS
SELECT game_id, name, image
FROM BOARD_GAMES
ORDER BY updated_at DESC
LIMIT 10;

-- Upcoming Events with Venue Info
CREATE OR REPLACE VIEW Upcoming_Events AS
SELECT E.event_id, E.name AS event_name, E.description, E.event_time,
       V.name AS venue_name, E.max_participants
FROM EVENTS E
JOIN VENUE V ON E.venue_id = V.venue_id
WHERE E.event_time >= NOW()
ORDER BY E.event_time;

CREATE OR REPLACE VIEW event_details_view AS
SELECT 
    E.event_id,
    E.name,
    E.description,
    E.event_time,
    E.max_participants,
    E.nb_participant,
    V.name AS venue_name,
    V.address AS venue_address,
    V.max_capacity AS venue_capacity
FROM EVENTS E
JOIN VENUE V ON E.venue_id = V.venue_id;


-- Game Details
CREATE OR REPLACE VIEW Game_Details AS
SELECT 
    game_id,
    name,
    description,
    image,
    year_published,
    min_players,
    max_players,
    min_playtime,
    max_playtime,
    min_age,
    publisher,
    average_rating
FROM BOARD_GAMES;



-- Game Genres
CREATE OR REPLACE VIEW Game_Genres AS
SELECT IG.game_id, G.name AS genre
FROM IsOfGenre IG
JOIN GENRES G ON IG.genre_id = G.genre_id;

-- Ratings with Usernames
CREATE OR REPLACE VIEW Game_Ratings AS
SELECT R.game_id, R.user_id, U.username, R.Stars, R.comment
FROM Rating R
JOIN Users U ON R.user_id = U.user_id;

CREATE OR REPLACE VIEW game_ratings_view AS
SELECT
    R.game_id,
    R.user_id, 
    U.username,
    R.Stars AS stars,
    R.comment
FROM Rating R
JOIN Users U ON R.user_id = U.user_id;


-- Searchable Game Data View
CREATE OR REPLACE VIEW Game_SearchView AS
SELECT BG.game_id, BG.name, BG.year_published, BG.publisher,
       BG.min_age, BG.average_rating, BG.image, G.name AS genre
FROM BOARD_GAMES BG
LEFT JOIN IsOfGenre IG ON BG.game_id = IG.game_id
LEFT JOIN GENRES G ON IG.genre_id = G.genre_id;

-- List of users for admin
DROP VIEW IF EXISTS Admin_UserList;
CREATE VIEW Admin_UserList AS
SELECT user_id, username, is_admin, is_blocked
FROM Users;

-- List of games for admin to manage
DROP VIEW IF EXISTS Admin_BoardGames;
CREATE VIEW Admin_BoardGames AS
SELECT game_id, name, year_published, min_players, max_players, average_rating
FROM BOARD_GAMES;

-- List of games owned and number of owners
DROP VIEW IF EXISTS Games_Owned_Count;
CREATE VIEW Games_Owned_Count AS
SELECT bg.name, COUNT(go.user_id) AS owners_count
FROM BOARD_GAMES bg
JOIN GameOwned go ON bg.game_id = go.game_id
GROUP BY bg.game_id;

-- 2. INDEXES (to optimize performance)

CREATE INDEX idx_user_username ON Users(username);
CREATE INDEX idx_game_name ON BOARD_GAMES(name);
CREATE INDEX idx_rating_game_user ON Rating(game_id, user_id);
CREATE INDEX idx_event_time ON EVENTS(event_time);


-- 3. TRIGGERS

-- Update average_rating when new rating added
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



-- Update nb_participant when someone joins event
DROP TRIGGER IF EXISTS update_nb_participant;


CREATE TRIGGER update_nb_participant AFTER INSERT ON ParticipateTo
FOR EACH ROW
BEGIN
  UPDATE EVENTS
  SET nb_participant = nb_participant + 1
  WHERE event_id = NEW.event_id;
END;



-- Update updated_at on game modification
DROP TRIGGER IF EXISTS set_updated_at;


CREATE TRIGGER set_updated_at BEFORE UPDATE ON BOARD_GAMES
FOR EACH ROW
BEGIN
  SET NEW.updated_at = NOW();
END;



-- Check max participants before adding to event
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


-- Check venue capacity not exceeded by event
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

-- Get User Role
DROP PROCEDURE IF EXISTS GetUserRole;

CREATE FUNCTION GetUserRole(uid INT) RETURNS VARCHAR(10)
DETERMINISTIC
BEGIN
  DECLARE role VARCHAR(10);
  SELECT IF(is_admin, 'admin', 'user') INTO role
  FROM Users WHERE user_id = uid;
  RETURN role;
END;

-- Search for a game (by filters)
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



-- Games in a user’s wishlist
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



-- Users for a given event
DROP PROCEDURE IF EXISTS GetEventUsers;

CREATE PROCEDURE GetEventUsers(IN eventID INT)
BEGIN
  SELECT u.username
  FROM Users u
  JOIN ParticipateTo pt ON pt.user_id = u.user_id
  WHERE pt.event_id = eventID;
END;



-- Ratings for a game
DROP PROCEDURE IF EXISTS GetRatingsForGame;

CREATE PROCEDURE GetRatingsForGame(IN gameID INT)
BEGIN
  SELECT u.username, r.Stars, r.comment
  FROM Rating r
  JOIN Users u ON r.user_id = u.user_id
  WHERE r.game_id = gameID;
END;



-- Blocked/unblocked users
DROP PROCEDURE IF EXISTS GetUsersByBlockStatus;

CREATE PROCEDURE GetUsersByBlockStatus(IN blockStatus BOOLEAN)
BEGIN
  SELECT * FROM Users WHERE is_blocked = blockStatus;
END;



-- Modify event info
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


-- Games owned by a user
DROP PROCEDURE IF EXISTS GetOwnedGames;

CREATE PROCEDURE GetOwnedGames(IN userID INT)
BEGIN
  SELECT bg.name
  FROM OwnedGames og
  JOIN BOARD_GAMES bg ON og.game_id = bg.game_id
  WHERE og.user_id = userID;
END;




