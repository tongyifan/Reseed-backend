import base64
import hmac
import time

from flask_login import UserMixin

from instance.config import REMEMBER_COOKIE_DURATION


class User(UserMixin):
    def __init__(self, user):
        self.user = user
        self.id = user['id']

    def is_active(self):
        return self.user['enable']

    def get_auth_token(self):
        key = self.user['passhash']
        ts_str = str(time.time() + REMEMBER_COOKIE_DURATION)
        ts_byte = ts_str.encode("utf-8")
        sha1_tshexstr = hmac.new(key.encode("utf-8"), ts_byte, 'sha1').hexdigest()
        token = self.user['username'] + ':' + ts_str + ':' + sha1_tshexstr
        b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))
        return b64_token.decode("utf-8")
