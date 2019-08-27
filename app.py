import base64
import hashlib
import hmac
import json
import time

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_redis import FlaskRedis
import bcrypt

from utils.database import Database

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

mysql = Database(app=app, autocommit=True)
redis = FlaskRedis(app=app)

from utils.torrent_compare import search_torrent

CORS(app)


@app.route('/')
def hello_world():
    return 'Hello World! This is the backend API of Reseed (https://reseed.tongyifan.me). ' \
           'If you want to use it for development, please contact with me by telegram - ' \
           '<a href="https://t.me/tongyifan">@tongyifan</a>'


@app.route('/upload_json', methods=['POST'])
def upload_file():
    if verify_token(request.args['token']):
        file = request.files['file']
        sites = request.form['sites']
        sites = sites.split(',')
        try:
            t_json = json.loads((file.read().decode('utf-8')))
        except json.decoder.JSONDecodeError:
            return jsonify({'success': False, 'msg': "Format JSON error!"}), 500
        result = search_torrent(t_json['result'], sites)
        return jsonify({'success': True, 'base_dir': t_json['base_dir'], 'result': result})
    else:
        return jsonify({'success': True, 'msg': 'Invalid token!'}), 401


@app.route('/sites_info')
def sites_info():
    if verify_token(request.args['token']):
        sites = mysql.get_sites_info()
        result = list()
        for site in sites:
            result.append({'name': site['site'], 'base_url': site['base_url'], '_enable': False, 'passkey': ""})
        return jsonify(result)
    else:
        return jsonify({'success': False, 'msg': 'Invalid token!'}), 401


@app.route('/signup', methods=['POST'])
def sign_up():
    username = request.form['username']
    password = request.form['password']

    site = request.form['site'] or 'tjupt'
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
        if bcrypt.checkpw(password.encode('utf-8'), user[0]['passhash'].encode('utf-8')):
            token = generate_token(user[0]['username'])
            return jsonify({'success': True, 'msg': 'Success~', 'token': token})
        else:
            return jsonify({'success': False, 'msg': 'Invalid username or password!'}), 401
    else:
        return jsonify({'success': False, 'msg': 'Invalid username or password!'}), 401


def check_id_passkey(site, user_id, user_passkey):
    if site == 'ourbits':
        return check_id_passkey_ourbits(user_id, user_passkey)
    return check_id_passkey_tjupt(user_id, user_passkey)  # Fallback


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


def generate_token(username, expire=app.config.get('TOKEN_EXPIRED_TIME')):
    key = mysql.get_user(username)[0]['passhash']
    ts_str = str(time.time() + expire)
    ts_byte = ts_str.encode("utf-8")
    sha1_tshexstr = hmac.new(key.encode("utf-8"), ts_byte, 'sha1').hexdigest()
    token = username + ':' + ts_str + ':' + sha1_tshexstr
    b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))
    return b64_token.decode("utf-8")


def verify_token(token):
    try:
        token_str = base64.urlsafe_b64decode(token).decode('utf-8')
        token_list = token_str.split(':')
        if len(token_list) != 3:
            return False
        username = token_list[0]
        user = mysql.get_user(username)
        if not user:
            return False
        key = user[0]['passhash']
        ts_str = token_list[1]
        if float(ts_str) < time.time():
            # token expired
            return False
        known_sha1_tsstr = token_list[2]
        sha1 = hmac.new(key.encode("utf-8"), ts_str.encode('utf-8'), 'sha1')
        calc_sha1_tsstr = sha1.hexdigest()
        return calc_sha1_tsstr == known_sha1_tsstr
    except Exception:
        return False


if __name__ == '__main__':
    app.run(host="0.0.0.0")
