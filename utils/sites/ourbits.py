import hashlib

import requests
from flask import current_app


def check_id_passkey_ourbits(ob_id, ob_passkey):
    verity = hashlib.md5(('{}{}{}{}'.format(current_app.config.get('OURBITS_TOKEN'), ob_id, ob_passkey,
                                            current_app.config.get('OURBITS_SECRET'))).encode('utf-8')).hexdigest()
    try:
        # 这里调用了Reseed专用接口，具体请与 @Rhilip 联系
        resp = requests.get('https://www.ourbits.club/api_reseed.php', params={
            'token': current_app.config.get('OURBITS_TOKEN'),
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
