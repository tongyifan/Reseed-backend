import bcrypt
from flask import Blueprint, request, jsonify

from models.user import User
from utils import check_id_tjupt, check_id_passkey_tjupt, check_id_passkey_ourbits, check_id_passkey_hdchina
from . import mysql

us = Blueprint('user', __name__)


@us.route('/signup', methods=['POST'])
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


@us.route('/login', methods=['POST'])
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
    elif site == 'hdchina':
        return check_id_passkey_hdchina(user_id, user_passkey)
    elif site == 'tjupt':
        return check_id_passkey_tjupt(user_id, user_passkey)
    else:
        return 'Auth failed! Unknown site.'
