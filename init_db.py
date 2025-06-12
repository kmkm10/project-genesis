import os
import sqlite3
import psycopg2 # PostgreSQL用ライブラリ

# --- テーブル作成用のSQL文 ---
# usersテーブル
SQL_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id {auto_increment_syntax},
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
"""
# playersテーブル
SQL_CREATE_PLAYERS_TABLE = """
CREATE TABLE IF NOT EXISTS players (
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
"""

# --- メイン処理 ---
def initialize_database():
    is_production = 'DATABASE_URL' in os.environ
    
    # 本番環境(PostgreSQL)かローカル(SQLite)かで接続方法とSQL構文を切り替える
    if is_production:
        print("本番環境(PostgreSQL)のデータベースを初期化します...")
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        # PostgreSQLではidを自動で増やすためにSERIAL PRIMARY KEYを使う
        auto_increment_syntax = "SERIAL PRIMARY KEY"
    else:
        print("ローカル環境(SQLite)のデータベースを初期化します...")
        if os.path.exists('genesis.db'):
            os.remove('genesis.db')
            print("既存の 'genesis.db' を削除しました。")
        conn = sqlite3.connect('genesis.db')
        # SQLiteではINTEGER PRIMARY KEY AUTOINCREMENTを使う
        auto_increment_syntax = "INTEGER PRIMARY KEY AUTOINCREMENT"

    # カーソルを取得
    cur = conn.cursor()
    
    # テーブルを作成
    print("users テーブルを作成中...")
    cur.execute(SQL_CREATE_USERS_TABLE.format(auto_increment_syntax=auto_increment_syntax))
    print("players テーブルを作成中...")
    cur.execute(SQL_CREATE_PLAYERS_TABLE.format(auto_increment_syntax=auto_increment_syntax))

    # 変更を確定して接続を閉じる
    conn.commit()
    cur.close()
    conn.close()
    
    print("データベースの初期化が完了しました。")

if __name__ == '__main__':
    initialize_database()
