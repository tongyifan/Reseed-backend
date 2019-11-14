import base64
import hashlib
import hmac
import json
import time
from itertools import chain

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_login import LoginManager, login_required, current_user
from flask_redis import FlaskRedis
import bcrypt

from model.user import User
from utils.database import Database

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

mysql = Database(app=app, autocommit=True)
redis = FlaskRedis(app=app)
REDIS_TTL = app.config.get('REDIS_TTL', 2 * 24 * 60 * 60)

import utils

CORS(app)

limiter = Limiter(app)

login_manager = LoginManager(app)


@login_manager.request_loader
def load_user_from_request(request):
    token = request.headers.get('Authorization')
    if token:
        token = token.replace('Bearar ', '', 1)
        return verify_token(token)
    else:
        return None


def verify_token(token):
    try:
        token_str = base64.urlsafe_b64decode(token).decode('utf-8')
        token_list = token_str.split(':')
        if len(token_list) != 3:
            return False
        username = token_list[0]
        user = mysql.get_user(username)
        if not user or not user['enable']:
            return False
        key = user['passhash']
        ts_str = token_list[1]
        if float(ts_str) < time.time():
            # token expired
            return False
        known_sha1_tsstr = token_list[2]
        sha1 = hmac.new(key.encode("utf-8"), ts_str.encode('utf-8'), 'sha1')
        calc_sha1_tsstr = sha1.hexdigest()
        return User(user) if calc_sha1_tsstr == known_sha1_tsstr else None
    except Exception:
        return None


@app.route('/')
def hello_world():
    return 'Hello World! This is the backend API of Reseed (https://reseed.tongyifan.me). ' \
           'If you want to use it for development, please contact with me by telegram - ' \
           '<a href="https://t.me/tongyifan">@tongyifan</a>'


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'success': False, 'msg': "Rate limit exceeded: %s" % e.description}), 429


@app.route('/upload_json', methods=['POST'])
@login_required
@limiter.limit('10/day;5/hour', key_func=lambda: current_user.id)
def upload_file():
    file = request.files['file']
    sites = request.form['sites']
    sites = sites.split(',')
    try:
        t_json = json.loads((file.read().decode('utf-8')))
    except json.decoder.JSONDecodeError:
        return jsonify({'success': False, 'msg': "Format JSON error!"}), 500
    file_hash = hashlib.md5(json.dumps(t_json['result']).encode('utf-8')).hexdigest()
    cache = mysql.get_result_cache(file_hash)
    if cache is not None:
        result = json.loads(cache)
    else:
        result = utils.search_torrent(t_json['result'], sites)
        mysql.record_upload_data(current_user.id, file_hash, json.dumps(result), request.remote_addr)

    for torrent in result:
        for t in chain(torrent['cmp_warning'], torrent['cmp_success']):
            t['sites'] = format_sites(t['sites'], sites)
        torrent['cmp_success'] = list(filter(lambda k: k['sites'] != '', torrent['cmp_success']))
        torrent['cmp_warning'] = list(filter(lambda k: k['sites'] != '', torrent['cmp_warning']))
    return jsonify({'success': True, 'base_dir': t_json['base_dir'], 'result': result})


def format_sites(result, sites):
    formatted_result = list()
    for r in result.split(','):
        sid = r.split('-')[-1]
        site = r.replace('-' + sid, '')
        if site in sites and mysql.check_torrent_valid(sid, site):
            formatted_result.append(r)
    return ','.join(formatted_result)


@app.route('/sites_info')
@login_required
def sites_info():
    sites = mysql.get_sites_info()
    result = list()
    for site in sites:
        result.append({'name': site['site'], 'base_url': site['base_url'], '_enable': False, 'passkey': ""})
    return jsonify(result)


@app.route('/signup', methods=['POST'])
def sign_up():
    username = request.form['username']
    password = request.form['password']

    site = request.form.get('site', 'tjupt')
    user_id = request.form['id']
    user_passkey = request.form['passkey']

    # Check site id in our database
    if not mysql.check_site_id_registered(site, user_id):
        return jsonify({'success': False, 'msg': 'This ID has been used in Site: {}.'.format(site)}), 403

    # check if user is valid in site
    msg = check_id_passkey(site, user_id, user_passkey)
    if msg:
        return jsonify({'success': False, 'msg': msg}), 403

    # Create user if their name is not dupe
    if not mysql.get_user(username):
        salt = bcrypt.gensalt()
        passhash = bcrypt.hashpw(password.encode('utf-8'), salt)

        mysql.signup(username, passhash.decode('utf-8'), site, user_id)
        return jsonify({'success': True, 'msg': 'Registration success!'}), 201
    else:
        return jsonify({'success': False, 'msg': 'Username existed!'}), 403


@app.route('/login', methods=['POST'])
def log_in():
    username = request.form['username']
    password = request.form['password']

    user = mysql.get_user(username)
    if user:
        if not user['enable']:
            return jsonify({'success': False, 'msg': 'User has been banned! Please contact administrator.'}), 403

        # 如果用户的TJUPT账户被封禁，则将Reseed账户同时封禁
        if user['tjupt_id']:
            user_active = check_id_tjupt(user['tjupt_id'])
            if not user_active:
                mysql.ban_user(user['id'])
                return jsonify({'success': False, 'msg': 'User has been banned! Please contact administrator.'}), 403

        if bcrypt.checkpw(password.encode('utf-8'), user['passhash'].encode('utf-8')):
            return jsonify({'success': True, 'msg': 'Success~', 'token': User(user).get_auth_token()})
        else:
            return jsonify({'success': False, 'msg': 'Invalid username or password!'}), 403
    else:
        return jsonify({'success': False, 'msg': 'Invalid username or password!'}), 403


def check_id_passkey(site, user_id, user_passkey):
    if site == 'ourbits':
        return check_id_passkey_ourbits(user_id, user_passkey)
    return check_id_passkey_tjupt(user_id, user_passkey)  # Fallback


def check_id_tjupt(tjupt_id):
    api_type = 'verify_id_status'
    sign = hashlib.md5(
        (app.config.get('TJUPT_TOKEN') + api_type + str(tjupt_id) + app.config.get('TJUPT_SECRET')).encode(
            'utf-8')).hexdigest()
    try:
        resp = requests.get('https://tjupt.org/api_username.php', params={
            'token': app.config.get('TJUPT_TOKEN'),
            'id': tjupt_id,
            'type': api_type,
            'sign': sign
        }, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return True if data['status'] == 0 else False
        else:
            return True
    except requests.RequestException:
        return True


def check_id_passkey_tjupt(tjupt_id, tjupt_passkey):
    api_type = 'verify_id_passkey'
    sign = hashlib.md5(
        (app.config.get('TJUPT_TOKEN') + api_type + tjupt_id + tjupt_passkey + app.config.get('TJUPT_SECRET')).encode(
            'utf-8')).hexdigest()
    try:
        resp = requests.get('https://tjupt.org/api_username.php', params={
            'token': app.config.get('TJUPT_TOKEN'),
            'id': tjupt_id,
            'passkey': tjupt_passkey,
            'type': api_type,
            'sign': sign
        }, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data['status'] == 0:
                return ''
            else:
                return 'Auth failed! Please check your ID and passkey.'
        else:
            return 'Network error! Please try it later...'
    except requests.RequestException:
        return 'Network error! Please try it later...'


# 这里调用了Reseed专用接口，具体请与 @Rhilip 联系
def check_id_passkey_ourbits(ob_id, ob_passkey):
    verity = hashlib.md5(
        ('{}{}{}{}'.format(app.config.get('OURBITS_TOKEN'), ob_id, ob_passkey,
                           app.config.get('OURBITS_SECRET'))).encode('utf-8')
    ).hexdigest()
    try:
        resp = requests.get('https://www.ourbits.club/api_reseed.php', params={
            'token': app.config.get('OURBITS_TOKEN'),
            'id': ob_id,
            'verity': verity
        }, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data['success']:  # 接口只返回 {'success' : <Boolean>} ，验证通过就True
                return ''
            else:
                return 'Auth failed! Please check your ID and passkey.'
        else:
            return 'Network error! Please try it later...'
    except requests.RequestException:
        return 'Network error! Please try it later...'


if __name__ == '__main__':
    app.run(host="0.0.0.0")
