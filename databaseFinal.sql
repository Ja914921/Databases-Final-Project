DROP DATABASE IF EXISTS gamesearch_db;
CREATE DATABASE gamesearch_db CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE gamesearch_db;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;

DROP TABLE IF EXISTS `bg_sales_record`;
DROP TABLE IF EXISTS `bg_sales_game`;
DROP TABLE IF EXISTS `bg_meta_game`;
DROP TABLE IF EXISTS `bg_esrb_game`;

CREATE TABLE `bg_esrb_game` (
  `esrb_game_id` int NOT NULL,
  `title` varchar(250) DEFAULT NULL,
  `esrb` varchar(60) DEFAULT NULL,
  `developer` varchar(200) DEFAULT NULL,
  `publisher` varchar(200) DEFAULT NULL,
  `release_date` varchar(60) DEFAULT NULL,
  `source` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`esrb_game_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `bg_meta_game` (
  `meta_game_id` int NOT NULL,
  `title` varchar(250) DEFAULT NULL,
  `platform` varchar(100) DEFAULT NULL,
  `meta_score` int DEFAULT NULL,
  `user_score` decimal(3,1) DEFAULT NULL,
  `release_date` varchar(60) DEFAULT NULL,
  `developer` varchar(200) DEFAULT NULL,
  `publisher` varchar(200) DEFAULT NULL,
  `genre` varchar(120) DEFAULT NULL,
  `source` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`meta_game_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `bg_sales_game` (
  `sales_game_id` int NOT NULL,
  `title` varchar(250) DEFAULT NULL,
  `platform` varchar(100) DEFAULT NULL,
  `genre` varchar(120) DEFAULT NULL,
  `publisher` varchar(200) DEFAULT NULL,
  `developer` varchar(200) DEFAULT NULL,
  `release_year` int DEFAULT NULL,
  `source` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`sales_game_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `bg_sales_record` (
  `sales_id` int NOT NULL,
  `sales_game_id` int NOT NULL,
  `region` varchar(60) NOT NULL,
  `sales_millions` decimal(10,3) DEFAULT NULL,
  `source` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`sales_id`),
  KEY `idx_sales_game_id` (`sales_game_id`),
  CONSTRAINT `fk_sales_record_game`
    FOREIGN KEY (`sales_game_id`) REFERENCES `bg_sales_game` (`sales_game_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET UNIQUE_CHECKS = 1;

LOAD DATA LOCAL INFILE 'bg_esrb_game.csv'
INTO TABLE bg_esrb_game
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(esrb_game_id, title, esrb, developer, publisher, release_date, source);

LOAD DATA LOCAL INFILE 'bg_meta_game.csv'
INTO TABLE bg_meta_game
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(@meta_game_id, @title, @platform, @meta_score, @user_score, @release_date, @developer, @publisher, @genre, @source)
SET
  meta_game_id = NULLIF(@meta_game_id,''),
  title        = NULLIF(@title,''),
  platform     = NULLIF(@platform,''),
  meta_score   = NULLIF(@meta_score,''),
  user_score   = NULLIF(@user_score,''),
  release_date = NULLIF(@release_date,''),
  developer    = NULLIF(@developer,''),
  publisher    = NULLIF(@publisher,''),
  genre        = NULLIF(@genre,''),
  source       = NULLIF(@source,'');

LOAD DATA LOCAL INFILE 'bg_sales_game.csv'
INTO TABLE bg_sales_game
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(@sales_game_id, @title, @platform, @genre, @publisher, @developer, @release_year, @source)
SET
  sales_game_id = NULLIF(@sales_game_id,''),
  title         = NULLIF(@title,''),
  platform      = NULLIF(@platform,''),
  genre         = NULLIF(@genre,''),
  publisher     = NULLIF(@publisher,''),
  developer     = NULLIF(@developer,''),
  release_year  = NULLIF(@release_year,''),
  source        = NULLIF(@source,'');

LOAD DATA LOCAL INFILE 'bg_sales_record.csv'
INTO TABLE bg_sales_record
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(@sales_id, @sales_game_id, @region, @sales_millions, @source)
SET
  sales_id       = NULLIF(@sales_id,''),
  sales_game_id  = NULLIF(@sales_game_id,''),
  region         = NULLIF(@region,''),
  sales_millions = NULLIF(@sales_millions,''),
  source         = NULLIF(@source,'');

SET FOREIGN_KEY_CHECKS = 1;