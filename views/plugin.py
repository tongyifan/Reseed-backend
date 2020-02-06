import time

import requests
from flask import Blueprint, current_app, jsonify
from flask_login import login_required

from views import redis

plugin = Blueprint('plugin', __name__)


@plugin.route('/hdchina_token')
@login_required
def get_hdchina_token():
    token = redis.get('_hdchina_token')
    if token:
        return jsonify({'success': True, 'token': str(token, encoding='utf-8')})
    else:
        result = refresh_hdchina_token().json()
        if result['success']:
            token = redis.get('_hdchina_token')
            return jsonify({'success': True, 'token': str(token, encoding='utf-8')})
        else:
            return jsonify(result), 500


@plugin.route('/refresh_hdchina_token')
def refresh_hdchina_token():
    token = redis.get('_hdchina_token')
    if token:
        return jsonify({'success': True})
    try:
        resp = requests.get('https://api.hdchina.org/v1/3rd/reseed/requestToken',
                            headers={'Authorization': "Bearer {}".format(current_app.config.get('HDCHINA_APIKEY'))},
                            timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data['status'] == 'success':
                token = data['data']['token']
                redis.set('_hdchina_token', token, int(data['data']['expire']) - int(time.time()) - 10)
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'msg': 'Reseed auth failed! Please report to @tongyifan'})
        else:
            return jsonify({'success': False, 'msg': 'Network error! Please try it later...'})
    except requests.RequestException:
        return jsonify({'success': False, 'msg': 'Network error! Please try it later...'})
