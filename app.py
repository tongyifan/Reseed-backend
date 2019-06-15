import hashlib
import json

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import bcrypt

from utils import db
from utils.rs_token import generate_token, verify_token
from utils.torrent_compare import search_torrent
from env import TJUPT_SECRET, TJUPT_TOKEN

app = Flask(__name__)
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
        sites = db.get_sites_info()
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

    tjupt_id = request.form['id']
    tjupt_passkey = request.form['passkey']
    if not db.check_tjuid_registered(tjupt_id):
        return jsonify({'success': False, 'msg': 'This ID has been used.'}), 403
    msg = check_id_passkey(tjupt_id, tjupt_passkey)
    if msg:
        return jsonify({'success': False, 'msg': msg}), 403

    if not db.get_user(username):
        salt = bcrypt.gensalt()
        passhash = bcrypt.hashpw(password.encode('utf-8'), salt)

        db.signup(username, passhash.decode('utf-8'), tjupt_id)
        return jsonify({'success': True, 'msg': 'Registration success!'}), 201
    else:
        return jsonify({'success': False, 'msg': 'Username existed!'}), 403


@app.route('/login', methods=['POST'])
def log_in():
    username = request.form['username']
    password = request.form['password']

    user = db.get_user(username)
    if user:
        if bcrypt.checkpw(password.encode('utf-8'), user[0]['passhash'].encode('utf-8')):
            token = generate_token(user[0]['username'])
            return jsonify({'success': True, 'msg': 'Success~', 'token': token})
        else:
            return jsonify({'success': False, 'msg': 'Invalid username or password!'}), 401
    else:
        return jsonify({'success': False, 'msg': 'Invalid username or password!'}), 401


def check_id_passkey(tjupt_id, tjupt_passkey):
    api_type = 'verify_id_passkey'
    sign = hashlib.md5((TJUPT_TOKEN + api_type + tjupt_id + tjupt_passkey + TJUPT_SECRET).encode('utf-8')).hexdigest()
    try:
        resp = requests.get('https://tjupt.org/api_username.php', params={
            'token': TJUPT_TOKEN,
            'id': tjupt_id,
            'passkey': tjupt_passkey,
            'type': api_type,
            'sign': sign
        }, timeout=30)
        if resp.status_code == 200:
            data = json.loads(resp.text)
            if data['status'] == 0:
                return ''
            else:
                return 'Auth failed! Please check your ID and passkey.'
        else:
            return 'Network error! Please try it later...'
    except requests.RequestException:
        return 'Network error! Please try it later...'


if __name__ == '__main__':
    app.run(host="0.0.0.0")
