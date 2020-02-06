import base64
import hmac
import time

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_login import LoginManager, current_user
from flask_redis import FlaskRedis
from flask_socketio import SocketIO

from models.user import User
from utils import Database

socketio = SocketIO(cors_allowed_origins='*')
limiter = Limiter(key_func=lambda: current_user.id)
login_manager = LoginManager()
mysql = Database(autocommit=True)
redis = FlaskRedis()
cors = CORS()


def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py')
    app.debug = debug

    from .reseed import reseed
    from .plugin import plugin
    from .user import us
    app.register_blueprint(us)
    app.register_blueprint(reseed)
    app.register_blueprint(plugin)

    # fixme: edit CORS
    cors.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*')
    limiter.init_app(app)
    login_manager.init_app(app)
    mysql.init_app(app)
    redis.init_app(app)

    return app


@login_manager.request_loader
def load_user_from_request(request):
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

    token = request.headers.get('Authorization')
    if token:
        token = token.replace('Bearar ', '', 1)
        return verify_token(token)
    else:
        return None
