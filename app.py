import sqlite3
import time
import json
import os
import secrets
import psycopg2
from psycopg2.extras import DictCursor
from functools import wraps
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# --- Flaskアプリの初期設定 ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a-super-secret-key-that-no-one-can-guess')

# --- 定数データ定義 ---
TECHNOLOGIES = { 'fire': {'name': '火の発見', 'cost': 10, 'time': 5, 'req': [], 'field': '化学'}, 'stone_tools': {'name': '石器', 'cost': 20, 'time': 10, 'req': [], 'field': '物理学'}, 'agriculture': {'name': '農耕', 'cost': 50, 'time': 20, 'req': ['stone_tools'], 'field': '生物学'}, 'writing': {'name': '文字', 'cost': 80, 'time': 30, 'req': ['agriculture'], 'field': '社会学'}, 'calculus': {'name': '微積分学', 'cost': 500, 'time': 60, 'req': ['writing'], 'field': '物理学'}, 'optics': {'name': '光学', 'cost': 400, 'time': 50, 'req': ['writing'], 'field': '物理学'}, 'astronomy': {'name': '天文学', 'cost': 1000, 'time': 120, 'req': ['calculus', 'optics'], 'field': '物理学'}, }
FACILITIES = { 'lab': {'name': '基礎研究所', 'base_cost': 100, 'effect_target': 'rp', 'effect_value': 0.5}, 'library': {'name': '図書館', 'base_cost': 500, 'effect_target': 'rp', 'effect_value': 2}, 'market': {'name': '市場', 'base_cost': 80, 'effect_target': 'money', 'effect_value': 1}, }
CIVILIZATION_LEVELS = { 0: {'name': '石器時代', 'rp_threshold': 0}, 1: {'name': '古代文明', 'rp_threshold': 150}, 2: {'name': '中世・ルネサンス期', 'rp_threshold': 1000}, }
PERMANENT_UPGRADES = {
    'rp_bonus': {'id': 'rp_bonus', 'name': '基礎研究ブースト', 'description_template': '次に転生した時、RPの基礎生産量が永続的に +{effect:.2f}/s される。', 'base_cost': 10, 'cost_increase_factor': 1.8, 'effect_per_level': 0.1, 'target_column': 'perm_bonus_rp_level'},
    'money_bonus': {'id': 'money_bonus', 'name': '基礎資金ブースト', 'description_template': '次に転生した時、資金の基礎生産量が永続的に +{effect:.2f}/s される。', 'base_cost': 15, 'cost_increase_factor': 2.0, 'effect_per_level': 0.05, 'target_column': 'perm_bonus_money_level'}
}
IS_PRODUCTION = 'DATABASE_URL' in os.environ

# --- データベース接続ヘルパー ---
def get_db_connection():
    if IS_PRODUCTION:
        return psycopg2.connect(os.environ.get('DATABASE_URL'))
    else:
        return sqlite3.connect('genesis.db')

def get_cursor(conn):
    if IS_PRODUCTION:
        return conn.cursor(cursor_factory=DictCursor)
    else:
        conn.row_factory = sqlite3.Row
        return conn.cursor()

def get_sql_placeholder():
    return "%s" if IS_PRODUCTION else "?"

# --- ログイン必須デコレータ ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ユーザー認証ルート ---
@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if request.method == 'POST':
        conn = None
        try:
            username, password = request.form['username'], request.form['password']
            conn = get_db_connection(); cur = get_cursor(conn); ph = get_sql_placeholder()
            error = None
            if not username: error = 'ユーザー名は必須です。'
            elif not password: error = 'パスワードは必須です。'
            else:
                cur.execute(f'SELECT id FROM users WHERE username = {ph}', (username,))
                if cur.fetchone(): error = f"ユーザー名 '{username}' は既に登録されています。"

            if error is None:
                sql_insert_user = f'INSERT INTO users (username, password) VALUES ({ph}, {ph}){" RETURNING id" if IS_PRODUCTION else ""}'
                cur.execute(sql_insert_user, (username, generate_password_hash(password)))
                new_user_id = cur.fetchone()['id'] if IS_PRODUCTION else cur.lastrowid
                initial_facilities = json.dumps({k: 0 for k in FACILITIES})
                sql_insert_player = f'''INSERT INTO players (user_id, last_update_time, research_points, money, total_rp_earned, 
                                       rp_per_second, money_per_second, civilization_level, unlocked_technologies, 
                                       researching_tech, facility_levels, evolution_points, genesis_shifts,
                                       perm_bonus_rp_level, perm_bonus_money_level, run_start_time)
                       VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})'''
                cur.execute(sql_insert_player, (new_user_id, time.time(), 10.0, 50.0, 0.0, 1.0, 0.5, 0, '[]', None, initial_facilities, 0, 0, 0, 0, time.time()))
                conn.commit(); flash('登録が完了しました。ログインしてください。'); return redirect(url_for('login'))
            flash(error)
        except Exception as e:
            print(f"Signup Error: {e}")
            flash('登録中にエラーが発生しました。', 'error')
        finally:
            if conn: conn.close()
    return render_template('signup.html')


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        conn = None
        try:
            username, password = request.form['username'], request.form['password']
            conn = get_db_connection(); cur = get_cursor(conn); ph = get_sql_placeholder()
            cur.execute(f'SELECT * FROM users WHERE username = {ph}', (username,)); user = cur.fetchone()
            error = None
            if user is None: error = 'ユーザー名が違います。'
            elif not check_password_hash(user['password'], password): error = 'パスワードが違います。'
            if error is None:
                session.clear(); session['user_id'], session['username'] = user['id'], user['username']
                return redirect(url_for('index'))
            flash(error)
        except Exception as e:
            print(f"Login Error: {e}")
            flash('ログイン中にエラーが発生しました。', 'error')
        finally:
            if conn: conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/forgot_password', methods=('GET', 'POST'))
def forgot_password():
    if request.method == 'POST':
        conn = None
        try:
            username = request.form['username']
            conn = get_db_connection(); cur = get_cursor(conn); ph = get_sql_placeholder()
            cur.execute(f'SELECT * FROM users WHERE username = {ph}', (username,))
            user = cur.fetchone()
            if user:
                token = secrets.token_urlsafe(32); expiry = time.time() + 3600 
                sql_update_token = f'UPDATE users SET reset_token = {ph}, reset_token_expiry = {ph} WHERE id = {ph}'
                cur.execute(sql_update_token, (token, expiry, user['id']))
                conn.commit()
                reset_link = url_for('reset_password', token=token, _external=True)
                print("--- パスワード再設定リンクが発行されました ---"); print(reset_link); print("-----------------------------------------")
            flash('入力されたユーザー名が存在する場合、パスワード再設定の手順が発行されます。', 'info')
        except Exception as e:
            print(f"Forgot Password Error: {e}")
            flash('リクエスト処理中にエラーが発生しました。', 'error')
        finally:
            if conn: conn.close()
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=('GET', 'POST'))
def reset_password(token):
    conn = None
    try:
        conn = get_db_connection(); cur = get_cursor(conn); ph = get_sql_placeholder()
        cur.execute(f'SELECT * FROM users WHERE reset_token = {ph} AND reset_token_expiry > {ph}', (token, time.time()))
        user = cur.fetchone()
        if not user:
            flash('この再設定リンクは無効か、有効期限が切れています。', 'error')
            return redirect(url_for('forgot_password'))
        
        if request.method == 'POST':
            password, password_confirm = request.form['password'], request.form['password_confirm']
            if not password or password != password_confirm:
                flash('パスワードが一致しません。', 'error'); return redirect(url_for('reset_password', token=token))
            hashed_password = generate_password_hash(password)
            sql_update_password = f'UPDATE users SET password = {ph}, reset_token = NULL, reset_token_expiry = NULL WHERE id = {ph}'
            cur.execute(sql_update_password, (hashed_password, user['id']))
            conn.commit()
            flash('パスワードが正常に更新されました。新しいパスワードでログインしてください。', 'success'); return redirect(url_for('login'))
    except Exception as e:
        print(f"Reset Password Error: {e}")
        flash('パスワードの更新中にエラーが発生しました。', 'error')
        return redirect(url_for('forgot_password'))
    finally:
        if conn: conn.close()
        
    return render_template('reset_password.html')


# (以降のゲームAPIとロジックは前回のバグ修正版と同じです)
# ... (変更なし) ...

# --- ゲーム本体とAPIのルート ---
@app.route('/')
@login_required
def index(): return render_template('index.html')

@app.route('/api/gamestate')
@login_required
def get_gamestate():
    player_data, log = update_player_state(session['user_id'])
    if not player_data: return jsonify({'error': 'プレイヤーデータが見つかりません。'}), 404
    current_civ_level = player_data['civilization_level']
    threshold = CIVILIZATION_LEVELS.get(current_civ_level + 1, {}).get('rp_threshold', float('inf'))
    if player_data['total_rp_earned'] >= threshold:
        next_level = current_civ_level + 1
        log.append(f"【文明進化】人類は『{CIVILIZATION_LEVELS[current_civ_level]['name']}』から『{CIVILIZATION_LEVELS[next_level]['name']}』へ進歩しました！")
        player_data['civilization_level'] = next_level
        conn = get_db_connection(); cur = get_cursor(conn); ph = get_sql_placeholder()
        cur.execute(f'UPDATE players SET civilization_level = {ph} WHERE user_id = {ph}', (next_level, session['user_id'])); conn.commit(); cur.close(); conn.close()
    return jsonify(format_data_for_frontend(player_data, log))

@app.route('/api/action', methods=['POST'])
@login_required
def perform_action():
    user_id = session['user_id']; _, _ = update_player_state(user_id)
    conn = None
    try:
        conn = get_db_connection(); cur = get_cursor(conn); ph = get_sql_placeholder()
        cur.execute(f'SELECT * FROM players WHERE user_id = {ph}', (user_id,)); player = cur.fetchone()
        data, action, item_id = request.json, request.json.get('action'), request.json.get('id')
        if not action or not item_id: return jsonify({'success': False, 'message': '無効なリクエストです。'}), 400
        if action == 'start_research':
            tech = TECHNOLOGIES.get(item_id)
            if not tech or player['research_points'] < tech['cost'] or (player['researching_tech'] is not None): return jsonify({'success': False, 'message': '研究を開始できません。'})
            new_rp, new_researching = player['research_points'] - tech['cost'], json.dumps((item_id, time.time(), tech['time']))
            cur.execute(f'UPDATE players SET research_points = {ph}, researching_tech = {ph} WHERE user_id = {ph}', (new_rp, new_researching, user_id))
        elif action == 'upgrade_facility':
            facility, levels = FACILITIES.get(item_id), json.loads(player['facility_levels'])
            if not facility: return jsonify({'success': False, 'message': '存在しない施設です。'})
            cost = facility['base_cost'] * (1.5 ** levels.get(item_id, 0))
            if player['money'] < cost: return jsonify({'success': False, 'message': '資金が不足しています。'})
            levels[item_id] = levels.get(item_id, 0) + 1
            new_money = player['money'] - cost
            new_rp_rate = player['rp_per_second'] + (facility['effect_value'] if facility['effect_target'] == 'rp' else 0)
            new_money_rate = player['money_per_second'] + (facility['effect_value'] if facility['effect_target'] == 'money' else 0)
            cur.execute(f'UPDATE players SET money={ph}, facility_levels={ph}, rp_per_second={ph}, money_per_second={ph} WHERE user_id={ph}',
                        (new_money, json.dumps(levels), new_rp_rate, new_money_rate, user_id))
        else: return jsonify({'success': False, 'message': '未知のアクションです。'}), 400
        conn.commit()
        return jsonify({'success': True})
    except Exception as e: return jsonify({'success': False, 'message': f'サーバーエラー: {e}'}), 500
    finally:
        if conn: cur.close(); conn.close()

@app.route('/api/genesis_shift', methods=['POST'])
@login_required
def genesis_shift():
    user_id = session['user_id']; conn = None
    try:
        conn = get_db_connection(); cur = get_cursor(conn); ph = get_sql_placeholder()
        cur.execute(f'SELECT * FROM players WHERE user_id = {ph}', (user_id,)); player = cur.fetchone()
        if 'astronomy' not in json.loads(player['unlocked_technologies']): return jsonify({'success': False, 'message': '転生の条件を満たしていません。'})
        ep_gain = int(player['total_rp_earned'] ** 0.5 / 100)
        base_rp = 1.0 
        base_money = 0.5
        cur.execute(f'''
            UPDATE players SET last_update_time={ph}, research_points=10.0, money=50.0, total_rp_earned=0.0,
                rp_per_second={ph}, money_per_second={ph}, civilization_level=0, unlocked_technologies='[]', 
                researching_tech=null, facility_levels={ph}, evolution_points={ph}, genesis_shifts={ph}, run_start_time={ph}
            WHERE user_id={ph}''',
            (time.time(), base_rp, base_money, json.dumps({k: 0 for k in FACILITIES}), player['evolution_points'] + ep_gain, player['genesis_shifts'] + 1, time.time(), user_id))
        conn.commit(); return jsonify({'success': True, 'message': f'ジェネシス・シフト発動！ {ep_gain} EPを獲得しました！'})
    finally:
        if conn: cur.close(); conn.close()

@app.route('/api/purchase_permanent_upgrade', methods=['POST'])
@login_required
def purchase_permanent_upgrade():
    user_id, upgrade_id = session['user_id'], request.json.get('upgrade_id')
    upgrade_info = PERMANENT_UPGRADES.get(upgrade_id)
    if not upgrade_info: return jsonify({'success': False, 'message': '無効なアップグレードです。'}), 400
    conn = None
    try:
        conn = get_db_connection(); cur = get_cursor(conn); ph = get_sql_placeholder()
        cur.execute(f'SELECT * FROM players WHERE user_id = {ph}', (user_id,)); player = cur.fetchone()
        target_column, current_level = upgrade_info['target_column'], player[upgrade_info['target_column']]
        cost = int(upgrade_info['base_cost'] * (upgrade_info['cost_increase_factor'] ** current_level))
        if player['evolution_points'] < cost: return jsonify({'success': False, 'message': 'EPが不足しています。'})
        cur.execute(f'UPDATE players SET evolution_points = {ph}, {target_column} = {ph} WHERE user_id = {ph}',
                     (player['evolution_points'] - cost, current_level + 1, user_id))
        conn.commit(); return jsonify({'success': True})
    finally:
        if conn: cur.close(); conn.close()

# --- ゲームロジック関数 ---
def format_data_for_frontend(player_data, log=[]):
    player_dict, unlocked = dict(player_data), json.loads(player_data['unlocked_technologies'])
    researching = json.loads(player_dict['researching_tech']) if player_dict['researching_tech'] else None
    facilities = json.loads(player_dict['facility_levels'])
    dashboard_stats = {'time_elapsed_this_run': time.time() - player_dict.get('run_start_time', time.time()), 'total_rp_this_run': player_dict['total_rp_earned'], 'unlocked_tech_count': len(unlocked), 'total_tech_count': len(TECHNOLOGIES), 'total_facility_levels': sum(facilities.values())}
    perm_upgrades_info = []
    for up_id, up_data in PERMANENT_UPGRADES.items():
        level = player_dict[up_data['target_column']]; cost = int(up_data['base_cost'] * (up_data['cost_increase_factor'] ** level))
        effect = (level + 1) * up_data['effect_per_level']
        perm_upgrades_info.append({'id': up_id, 'name': up_data['name'], 'level': level, 'description': up_data['description_template'].format(effect=effect), 'cost': cost})
    perm_rp_bonus, perm_money_bonus = player_dict['perm_bonus_rp_level'] * PERMANENT_UPGRADES['rp_bonus']['effect_per_level'], player_dict['perm_bonus_money_level'] * PERMANENT_UPGRADES['money_bonus']['effect_per_level']
    return {'research_points': player_dict['research_points'], 'money': player_dict['money'], 'rp_per_second': player_dict['rp_per_second'] + perm_rp_bonus, 'money_per_second': player_dict['money_per_second'] + perm_money_bonus, 'unlocked_technologies': unlocked, 'researching_tech': researching, 'available_technologies': [{'id': tid, **tech} for tid, tech in TECHNOLOGIES.items() if tid not in unlocked and (not researching or tid != researching[0]) and all(req in unlocked for req in tech['req'])], 'facilities': [{'id': fid, 'level': facilities.get(fid, 0), 'cost': fac['base_cost'] * (1.5 ** facilities.get(fid, 0)), **fac} for fid, fac in FACILITIES.items()], 'civilization': CIVILIZATION_LEVELS[player_dict['civilization_level']], 'evolution_points': player_dict['evolution_points'], 'genesis_shifts': player_dict['genesis_shifts'], 'permanent_upgrades': perm_upgrades_info, 'dashboard_stats': dashboard_stats, 'log': log}

def update_player_state(user_id):
    conn = None; log = []
    try:
        conn = get_db_connection(); cur = get_cursor(conn); ph = get_sql_placeholder()
        cur.execute(f'SELECT * FROM players WHERE user_id = {ph}', (user_id,)); player = cur.fetchone()
        if not player: return None, []
        player_data = dict(player)
        now, last_update = time.time(), player_data['last_update_time']
        elapsed = now - last_update if last_update > 0 else 0
        perm_rp_bonus, perm_money_bonus = player_data['perm_bonus_rp_level'] * PERMANENT_UPGRADES['rp_bonus']['effect_per_level'], player_data['perm_bonus_money_level'] * PERMANENT_UPGRADES['money_bonus']['effect_per_level']
        player_data['research_points'] += (player_data['rp_per_second'] + perm_rp_bonus) * elapsed; player_data['total_rp_earned'] += (player_data['rp_per_second'] + perm_rp_bonus) * elapsed
        player_data['money'] += (player_data['money_per_second'] + perm_money_bonus) * elapsed
        researching = json.loads(player_data['researching_tech']) if player_data['researching_tech'] else None
        if researching and now - researching[1] >= researching[2]:
            log.append(f"【研究完了】{TECHNOLOGIES[researching[0]]['name']}を解放しました！")
            unlocked = json.loads(player_data['unlocked_technologies'])
            if researching[0] not in unlocked: unlocked.append(researching[0])
            player_data['unlocked_technologies'], player_data['researching_tech'] = json.dumps(unlocked), None
        player_data['last_update_time'] = now
        cur.execute(f'UPDATE players SET last_update_time={ph}, research_points={ph}, money={ph}, total_rp_earned={ph}, researching_tech={ph}, unlocked_technologies={ph} WHERE user_id={ph}',
                     (now, player_data['research_points'], player_data['money'], player_data['total_rp_earned'], player_data['researching_tech'], player_data['unlocked_technologies'], user_id))
        conn.commit(); return player_data, log
    finally:
        if conn: cur.close(); conn.close()

if __name__ == '__main__':
    app.run(debug=True)
