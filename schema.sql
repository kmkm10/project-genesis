-- テーブルが存在すれば削除する命令を追加して、安全に再実行できるようにする
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id {auto_increment_syntax},
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    reset_token TEXT,
    reset_token_expiry REAL
);

CREATE TABLE players (
    id {auto_increment_syntax},
    user_id INTEGER NOT NULL,
    last_update_time REAL NOT NULL,
    research_points REAL NOT NULL,
    money REAL NOT NULL,
    total_rp_earned REAL NOT NULL,
    rp_per_second REAL NOT NULL,
    money_per_second REAL NOT NULL,
    civilization_level INTEGER NOT NULL,
    unlocked_technologies TEXT NOT NULL,
    researching_tech TEXT,
    facility_levels TEXT NOT NULL,
    evolution_points REAL NOT NULL DEFAULT 0,
    genesis_shifts INTEGER NOT NULL DEFAULT 0,
    perm_bonus_rp_level INTEGER NOT NULL DEFAULT 0,
    perm_bonus_money_level INTEGER NOT NULL DEFAULT 0,
    run_start_time REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
