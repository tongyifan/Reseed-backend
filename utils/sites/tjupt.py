import hashlib

import requests
from flask import current_app


def check_id_tjupt(tjupt_id):
    api_type = 'verify_id_status'
    sign = hashlib.md5((current_app.config.get('TJUPT_TOKEN') + api_type + str(tjupt_id) +
                        current_app.config.get('TJUPT_SECRET')).encode('utf-8')).hexdigest()
    try:
        resp = requests.get('https://tjupt.org/api_username.php', params={
            'token': current_app.config.get('TJUPT_TOKEN'),
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
    sign = hashlib.md5((current_app.config.get('TJUPT_TOKEN') + api_type + tjupt_id + tjupt_passkey +
                        current_app.config.get('TJUPT_SECRET')).encode('utf-8')).hexdigest()
    try:
        resp = requests.get('https://tjupt.org/api_username.php', params={
            'token': current_app.config.get('TJUPT_TOKEN'),
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
