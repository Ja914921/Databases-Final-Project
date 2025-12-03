
DROP DATABASE IF EXISTS gamesearch_db;

CREATE DATABASE gamesearch_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE gamesearch_db;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;


DROP TABLE IF EXISTS app_audit_log;
DROP TABLE IF EXISTS app_review_vote;
DROP TABLE IF EXISTS app_game_review;
DROP TABLE IF EXISTS app_favorite_item;
DROP TABLE IF EXISTS app_favorite_list;
DROP TABLE IF EXISTS app_search_result;
DROP TABLE IF EXISTS app_search;
DROP TABLE IF EXISTS app_session;
DROP TABLE IF EXISTS app_user_settings;
DROP TABLE IF EXISTS app_user_role;
DROP TABLE IF EXISTS app_role;
DROP TABLE IF EXISTS app_user;

DROP TABLE IF EXISTS app_game_tag;
DROP TABLE IF EXISTS app_tag;
DROP TABLE IF EXISTS app_genre;
DROP TABLE IF EXISTS app_platform;
DROP TABLE IF EXISTS app_game_link;

DROP TABLE IF EXISTS bg_sales_record;
DROP TABLE IF EXISTS bg_sales_game;
DROP TABLE IF EXISTS bg_meta_game;
DROP TABLE IF EXISTS bg_esrb_game;


CREATE TABLE bg_esrb_game (
  esrb_game_id   INT NOT NULL,
  title          VARCHAR(250) DEFAULT NULL,
  esrb           VARCHAR(60)  DEFAULT NULL,
  developer      VARCHAR(200) DEFAULT NULL,
  publisher      VARCHAR(200) DEFAULT NULL,
  release_date   VARCHAR(60)  DEFAULT NULL,
  source         VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (esrb_game_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE bg_meta_game (
  meta_game_id   INT NOT NULL,
  title          VARCHAR(250) DEFAULT NULL,
  platform       VARCHAR(100) DEFAULT NULL,
  meta_score     INT          DEFAULT NULL,
  user_score     DECIMAL(3, 1) DEFAULT NULL,
  release_date   VARCHAR(60)  DEFAULT NULL,
  developer      VARCHAR(200) DEFAULT NULL,
  publisher      VARCHAR(200) DEFAULT NULL,
  genre          VARCHAR(120) DEFAULT NULL,
  source         VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (meta_game_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE bg_sales_game (
  sales_game_id  INT NOT NULL,
  title          VARCHAR(250) DEFAULT NULL,
  platform       VARCHAR(100) DEFAULT NULL,
  genre          VARCHAR(120) DEFAULT NULL,
  publisher      VARCHAR(200) DEFAULT NULL,
  developer      VARCHAR(200) DEFAULT NULL,
  release_year   INT          DEFAULT NULL,
  source         VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (sales_game_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE bg_sales_record (
  sales_id       INT NOT NULL,
  sales_game_id  INT NOT NULL,
  region         VARCHAR(60) NOT NULL,
  sales_millions DECIMAL(10, 3) DEFAULT NULL,
  source         VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (sales_id),
  KEY idx_sales_game_id (sales_game_id),
  CONSTRAINT fk_sales_record_game
    FOREIGN KEY (sales_game_id)
    REFERENCES bg_sales_game (sales_game_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- Users
CREATE TABLE app_user (
  user_id       INT NOT NULL AUTO_INCREMENT,
  username      VARCHAR(50)  NOT NULL,
  email         VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active     TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_user_username (username),
  UNIQUE KEY uq_user_email (email)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Roles
CREATE TABLE app_role (
  role_id    INT NOT NULL AUTO_INCREMENT,
  role_name  VARCHAR(50) NOT NULL,
  PRIMARY KEY (role_id),
  UNIQUE KEY uq_role_name (role_name)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- User <-> Role 
CREATE TABLE app_user_role (
  user_id  INT NOT NULL,
  role_id  INT NOT NULL,
  PRIMARY KEY (user_id, role_id),
  CONSTRAINT fk_user_role_user
    FOREIGN KEY (user_id)
    REFERENCES app_user (user_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_user_role_role
    FOREIGN KEY (role_id)
    REFERENCES app_role (role_id)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Sessions
CREATE TABLE app_session (
  session_id   INT NOT NULL AUTO_INCREMENT,
  user_id      INT NOT NULL,
  token        VARCHAR(255) NOT NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at   DATETIME NOT NULL,
  revoked_at   DATETIME DEFAULT NULL,
  PRIMARY KEY (session_id),
  UNIQUE KEY uq_session_token (token),
  KEY idx_session_user (user_id),
  CONSTRAINT fk_session_user
    FOREIGN KEY (user_id)
    REFERENCES app_user (user_id)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- User settings
CREATE TABLE app_user_settings (
  user_id           INT NOT NULL,
  preferred_platform VARCHAR(100) DEFAULT NULL,
  preferred_genre    VARCHAR(120) DEFAULT NULL,
  show_mature        TINYINT(1) NOT NULL DEFAULT 1,
  created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_settings_user
    FOREIGN KEY (user_id)
    REFERENCES app_user (user_id)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Audit log 
CREATE TABLE app_audit_log (
  audit_id     INT NOT NULL AUTO_INCREMENT,
  user_id      INT DEFAULT NULL,
  action_type  VARCHAR(20) NOT NULL,
  entity_type  VARCHAR(50) NOT NULL,
  entity_id    VARCHAR(64) DEFAULT NULL,
  action_time  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  details      TEXT DEFAULT NULL,
  PRIMARY KEY (audit_id),
  KEY idx_audit_user (user_id),
  KEY idx_audit_time (action_time),
  CONSTRAINT fk_audit_user
    FOREIGN KEY (user_id)
    REFERENCES app_user (user_id)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Search 
CREATE TABLE app_search (
  search_id     INT NOT NULL AUTO_INCREMENT,
  user_id       INT DEFAULT NULL,
  query_text    VARCHAR(255) NOT NULL,
  platform      VARCHAR(100) DEFAULT NULL,
  genre         VARCHAR(120) DEFAULT NULL,
  esrb          VARCHAR(60)  DEFAULT NULL,
  min_meta      INT DEFAULT NULL,
  search_time   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (search_id),
  KEY idx_search_user (user_id),
  KEY idx_search_time (search_time),
  CONSTRAINT fk_search_user
    FOREIGN KEY (user_id)
    REFERENCES app_user (user_id)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Search results 
CREATE TABLE app_search_result (
  search_result_id INT NOT NULL AUTO_INCREMENT,
  search_id        INT NOT NULL,
  meta_game_id     INT DEFAULT NULL,
  sales_game_id    INT DEFAULT NULL,
  esrb_game_id     INT DEFAULT NULL,
  clicked          TINYINT(1) NOT NULL DEFAULT 0,
  rank_order       INT DEFAULT NULL,
  PRIMARY KEY (search_result_id),
  KEY idx_sr_search (search_id),
  KEY idx_sr_meta (meta_game_id),
  KEY idx_sr_sales (sales_game_id),
  KEY idx_sr_esrb (esrb_game_id),
  CONSTRAINT fk_sr_search
    FOREIGN KEY (search_id)
    REFERENCES app_search (search_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_sr_meta
    FOREIGN KEY (meta_game_id)
    REFERENCES bg_meta_game (meta_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_sr_sales
    FOREIGN KEY (sales_game_id)
    REFERENCES bg_sales_game (sales_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_sr_esrb
    FOREIGN KEY (esrb_game_id)
    REFERENCES bg_esrb_game (esrb_game_id)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Favorite list 
CREATE TABLE app_favorite_list (
  favorite_list_id INT NOT NULL AUTO_INCREMENT,
  user_id          INT NOT NULL,
  list_name        VARCHAR(100) NOT NULL,
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (favorite_list_id),
  KEY idx_fav_list_user (user_id),
  UNIQUE KEY uq_user_listname (user_id, list_name),
  CONSTRAINT fk_fav_list_user
    FOREIGN KEY (user_id)
    REFERENCES app_user (user_id)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Favorite item 
CREATE TABLE app_favorite_item (
  favorite_item_id INT NOT NULL AUTO_INCREMENT,
  favorite_list_id INT NOT NULL,
  meta_game_id     INT DEFAULT NULL,
  sales_game_id    INT DEFAULT NULL,
  esrb_game_id     INT DEFAULT NULL,
  notes            VARCHAR(255) DEFAULT NULL,
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (favorite_item_id),
  KEY idx_fav_item_list (favorite_list_id),
  KEY idx_fav_item_meta (meta_game_id),
  KEY idx_fav_item_sales (sales_game_id),
  KEY idx_fav_item_esrb (esrb_game_id),
  CONSTRAINT fk_fav_item_list
    FOREIGN KEY (favorite_list_id)
    REFERENCES app_favorite_list (favorite_list_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_fav_item_meta
    FOREIGN KEY (meta_game_id)
    REFERENCES bg_meta_game (meta_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_fav_item_sales
    FOREIGN KEY (sales_game_id)
    REFERENCES bg_sales_game (sales_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_fav_item_esrb
    FOREIGN KEY (esrb_game_id)
    REFERENCES bg_esrb_game (esrb_game_id)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Reviews
CREATE TABLE app_game_review (
  review_id     INT NOT NULL AUTO_INCREMENT,
  user_id       INT NOT NULL,
  meta_game_id  INT DEFAULT NULL,
  sales_game_id INT DEFAULT NULL,
  esrb_game_id  INT DEFAULT NULL,
  rating        INT NOT NULL,
  review_text   TEXT DEFAULT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                         ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (review_id),
  KEY idx_review_user (user_id),
  KEY idx_review_meta (meta_game_id),
  KEY idx_review_sales (sales_game_id),
  KEY idx_review_esrb (esrb_game_id),
  CONSTRAINT ck_review_rating CHECK (rating BETWEEN 1 AND 10),
  CONSTRAINT fk_review_user
    FOREIGN KEY (user_id)
    REFERENCES app_user (user_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_review_meta
    FOREIGN KEY (meta_game_id)
    REFERENCES bg_meta_game (meta_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_review_sales
    FOREIGN KEY (sales_game_id)
    REFERENCES bg_sales_game (sales_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_review_esrb
    FOREIGN KEY (esrb_game_id)
    REFERENCES bg_esrb_game (esrb_game_id)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

--  Like/Dislike
CREATE TABLE app_review_vote (
  review_id   INT NOT NULL,
  user_id     INT NOT NULL,
  vote_value  TINYINT NOT NULL,
  voted_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (review_id, user_id),
  CONSTRAINT ck_vote_value CHECK (vote_value IN (-1, 1)),
  CONSTRAINT fk_vote_review
    FOREIGN KEY (review_id)
    REFERENCES app_game_review (review_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_vote_user
    FOREIGN KEY (user_id)
    REFERENCES app_user (user_id)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Tag master
CREATE TABLE app_tag (
  tag_id    INT NOT NULL AUTO_INCREMENT,
  tag_name  VARCHAR(80) NOT NULL,
  PRIMARY KEY (tag_id),
  UNIQUE KEY uq_tag_name (tag_name)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Game <-> Tag 
CREATE TABLE app_game_tag (
  game_tag_id  INT NOT NULL AUTO_INCREMENT,
  meta_game_id INT DEFAULT NULL,
  sales_game_id INT DEFAULT NULL,
  esrb_game_id INT DEFAULT NULL,
  tag_id       INT NOT NULL,
  PRIMARY KEY (game_tag_id),
  KEY idx_gt_meta (meta_game_id),
  KEY idx_gt_sales (sales_game_id),
  KEY idx_gt_esrb (esrb_game_id),
  KEY idx_gt_tag (tag_id),
  CONSTRAINT fk_gt_tag
    FOREIGN KEY (tag_id)
    REFERENCES app_tag (tag_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_gt_meta
    FOREIGN KEY (meta_game_id)
    REFERENCES bg_meta_game (meta_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_gt_sales
    FOREIGN KEY (sales_game_id)
    REFERENCES bg_sales_game (sales_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_gt_esrb
    FOREIGN KEY (esrb_game_id)
    REFERENCES bg_esrb_game (esrb_game_id)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- Game link 
CREATE TABLE app_game_link (
  game_link_id  INT NOT NULL AUTO_INCREMENT,
  normalized_title VARCHAR(250) NOT NULL,
  meta_game_id   INT DEFAULT NULL,
  sales_game_id  INT DEFAULT NULL,
  esrb_game_id   INT DEFAULT NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (game_link_id),
  UNIQUE KEY uq_norm_title (normalized_title),
  KEY idx_link_meta (meta_game_id),
  KEY idx_link_sales (sales_game_id),
  KEY idx_link_esrb (esrb_game_id),
  CONSTRAINT fk_link_meta
    FOREIGN KEY (meta_game_id)
    REFERENCES bg_meta_game (meta_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_link_sales
    FOREIGN KEY (sales_game_id)
    REFERENCES bg_sales_game (sales_game_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_link_esrb
    FOREIGN KEY (esrb_game_id)
    REFERENCES bg_esrb_game (esrb_game_id)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- A saved filter preset per user 
CREATE TABLE app_filter_preset (
  preset_id    INT NOT NULL AUTO_INCREMENT,
  user_id      INT NOT NULL,
  preset_name  VARCHAR(80) NOT NULL,
  platform     VARCHAR(100) DEFAULT NULL,
  genre        VARCHAR(120) DEFAULT NULL,
  esrb         VARCHAR(60)  DEFAULT NULL,
  min_meta     INT DEFAULT NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (preset_id),
  UNIQUE KEY uq_user_preset (user_id, preset_name),
  CONSTRAINT fk_preset_user
    FOREIGN KEY (user_id)
    REFERENCES app_user (user_id)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Re-enable checks
-- ============================================================

SET UNIQUE_CHECKS = 1;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- CSV LOADS (4 dataset csv files)
-- ============================================================

-- IMPORTANT:
-- 1) You must start mysql with --local-infile=1 (you already are doing this)
-- 2) Using NULLIF(...) avoids “Incorrect integer/decimal value: ''” warnings

LOAD DATA LOCAL INFILE 'bg_esrb_game.csv'
INTO TABLE bg_esrb_game
FIELDS TERMINATED BY ','
  ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(esrb_game_id, title, esrb, developer, publisher, release_date, source);

LOAD DATA LOCAL INFILE 'bg_meta_game.csv'
INTO TABLE bg_meta_game
FIELDS TERMINATED BY ','
  ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
  @meta_game_id,
  @title,
  @platform,
  @meta_score,
  @user_score,
  @release_date,
  @developer,
  @publisher,
  @genre,
  @source
)
SET
  meta_game_id = NULLIF(@meta_game_id, ''),
  title        = NULLIF(@title, ''),
  platform     = NULLIF(@platform, ''),
  meta_score   = NULLIF(@meta_score, ''),
  user_score   = NULLIF(@user_score, ''),
  release_date = NULLIF(@release_date, ''),
  developer    = NULLIF(@developer, ''),
  publisher    = NULLIF(@publisher, ''),
  genre        = NULLIF(@genre, ''),
  source       = NULLIF(@source, '');

LOAD DATA LOCAL INFILE 'bg_sales_game.csv'
INTO TABLE bg_sales_game
FIELDS TERMINATED BY ','
  ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
  @sales_game_id,
  @title,
  @platform,
  @genre,
  @publisher,
  @developer,
  @release_year,
  @source
)
SET
  sales_game_id = NULLIF(@sales_game_id, ''),
  title         = NULLIF(@title, ''),
  platform      = NULLIF(@platform, ''),
  genre         = NULLIF(@genre, ''),
  publisher     = NULLIF(@publisher, ''),
  developer     = NULLIF(@developer, ''),
  release_year  = NULLIF(@release_year, ''),
  source        = NULLIF(@source, '');

LOAD DATA LOCAL INFILE 'bg_sales_record.csv'
INTO TABLE bg_sales_record
FIELDS TERMINATED BY ','
  ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
  @sales_id,
  @sales_game_id,
  @region,
  @sales_millions,
  @source
)
SET
  sales_id       = NULLIF(@sales_id, ''),
  sales_game_id  = NULLIF(@sales_game_id, ''),
  region         = NULLIF(@region, ''),
  sales_millions = NULLIF(@sales_millions, ''),
  source         = NULLIF(@source, '');

-- ============================================================
-- Optional: seed roles so GUI has something to show
-- ============================================================

INSERT INTO app_role (role_name) VALUES
  ('admin'),
  ('user')
ON DUPLICATE KEY UPDATE role_name = role_name;