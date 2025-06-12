DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS players;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    -- ▼▼▼【ここを追記】▼▼▼
    run_start_time REAL NOT NULL DEFAULT 0 -- 現在の周回の開始時刻
    -- ▲▲▲【ここまで追記】▲▲▲
    ,
    FOREIGN KEY (user_id) REFERENCES users (id)
);