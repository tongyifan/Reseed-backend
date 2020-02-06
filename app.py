from flask import jsonify

from views import create_app, socketio

app = create_app(debug=True)


@app.route('/')
def hello_world():
    return 'Hello World! This is the backend API of Reseed (https://reseed.tongyifan.me). ' \
           'If you want to use it for development, please contact with me by telegram - ' \
           '<a href="https://t.me/tongyifan">@tongyifan</a>'


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'success': False, 'msg': "Rate limit exceeded: %s" % e.description}), 429


if __name__ == '__main__':
    socketio.run(app)
