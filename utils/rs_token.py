import base64
import hmac
import time

from utils import db
from env import TOKEN_EXPIRED_TIME


def generate_token(username, expire=TOKEN_EXPIRED_TIME):
    key = db.get_user(username)[0]['passhash']
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
        user = db.get_user(username)
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
