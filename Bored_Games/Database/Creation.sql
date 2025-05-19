DROP DATABASE Bored_Games;
CREATE DATABASE IF NOT EXISTS Bored_Games;

USE Bored_Games;

CREATE TABLE IF NOT EXISTS BOARD_GAMES(
   game_id INT AUTO_INCREMENT,
   name VARCHAR(64) NOT NULL,
   image VARCHAR(255),
   description VARCHAR(1000),
   year_published INT,
   min_players SMALLINT NOT NULL,
   max_players SMALLINT NOT NULL,
   min_playtime INT,
   max_playtime INT,
   min_age INT,
   publisher VARCHAR(50) NOT NULL,
   updated_at DATETIME NOT NULL,
   average_rating DECIMAL(15,2) NOT NULL,
   PRIMARY KEY(game_id)
);

CREATE TABLE IF NOT EXISTS GENRES(
   genre_id INT AUTO_INCREMENT,
   name VARCHAR(50) NOT NULL,
   PRIMARY KEY(genre_id)
);

CREATE TABLE IF NOT EXISTS Users(
   user_id INT AUTO_INCREMENT,
   is_admin boolean NOT NULL,
   username VARCHAR(50) NOT NULL,
   password VARCHAR(255) NOT NULL,
   is_blocked boolean NOT NULL,
   PRIMARY KEY(user_id),
   UNIQUE (username)
);

CREATE TABLE IF NOT EXISTS VENUE(
   venue_id INT AUTO_INCREMENT,
   address VARCHAR(100) NOT NULL,
   name VARCHAR(50) NOT NULL,
   max_capacity INT NOT NULL,
   PRIMARY KEY(venue_id)
);

CREATE TABLE IF NOT EXISTS EVENTS(
   event_id INT AUTO_INCREMENT,
   name VARCHAR(50) NOT NULL,
   description VARCHAR(255) NOT NULL,
   max_participants INT NOT NULL,
   nb_participant INT NOT NULL,
   event_time DATETIME NOT NULL,
   venue_id INT NOT NULL,
   PRIMARY KEY(event_id),
   FOREIGN KEY(venue_id) REFERENCES VENUE(venue_id)
);

CREATE TABLE IF NOT EXISTS IsOfGenre(
   game_id INT,
   genre_id INT,
   PRIMARY KEY(game_id, genre_id),
   FOREIGN KEY(game_id) REFERENCES BOARD_GAMES(game_id),
   FOREIGN KEY(genre_id) REFERENCES GENRES(genre_id)
);

CREATE TABLE IF NOT EXISTS WishList(
   game_id INT,
   user_id INT,
   PRIMARY KEY(game_id, user_id),
   FOREIGN KEY(game_id) REFERENCES BOARD_GAMES(game_id),
   FOREIGN KEY(user_id) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS GameOwned(
   game_id INT,
   user_id INT,
   since DATE,
   PRIMARY KEY(game_id, user_id),
   FOREIGN KEY(game_id) REFERENCES BOARD_GAMES(game_id),
   FOREIGN KEY(user_id) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS Rating(
   user_id INT,
   Stars TINYINT CHECK(Stars BETWEEN 1 AND 5),
   comment VARCHAR(2000),
   game_id INT NOT NULL,
   PRIMARY KEY(user_id, game_id),
   FOREIGN KEY(user_id) REFERENCES Users(user_id),
   FOREIGN KEY(game_id) REFERENCES BOARD_GAMES(game_id)
);

CREATE TABLE IF NOT EXISTS ParticipateTo(
   event_id INT,
   user_id INT,
   PRIMARY KEY(event_id, user_id),
   FOREIGN KEY(event_id) REFERENCES EVENTS(event_id),
   FOREIGN KEY(user_id) REFERENCES Users(user_id)
);
