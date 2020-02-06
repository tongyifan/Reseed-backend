import requests
from flask import current_app


def check_id_passkey_hdchina(hdchina_username, hdchina_userkey):
    try:
        resp = requests.post('https://api.hdchina.org/v1/3rd/reseed/checkUserToken', data={
            'userKey': hdchina_userkey
        }, headers={'Authorization': "Bearer {}".format(current_app.config.get('HDCHINA_APIKEY'))}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data['status'] == 'success':
                if str.lower(hdchina_username) == str.lower(data['data']['username']):
                    return ''
                return 'Auth failed! Username mismatch, please contact administrator.'
            else:
                return 'Auth failed! Please check your ID and passkey.'
        else:
            return 'Network error! Please try it later...'
    except requests.RequestException:
        return 'Network error! Please try it later...'
