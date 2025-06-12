# /ProjectGenesis/init_db.py

import sqlite3

# データベースに接続（ファイルが存在しない場合は新規作成される）
connection = sqlite3.connect('genesis.db')

# schema.sqlファイルを開き、その中のSQL文を実行してテーブルを作成
with open('schema.sql', 'r', encoding='utf-8') as f:
    connection.executescript(f.read())

# 接続を閉じる
connection.close()

print("データベースのテーブルが作成されました。（初期データなし）")