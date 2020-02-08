import functools
import hashlib
import json
from itertools import chain

from flask import Blueprint, current_app, request, jsonify
from flask_login import current_user, login_required
from flask_socketio import disconnect, emit

from utils import compare_torrents
from . import limiter, socketio, mysql, redis

reseed = Blueprint('reseed', __name__)


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)

    return wrapped


@reseed.route('/upload_json', methods=['POST'])
@login_required
@limiter.limit('10/day;5/hour')
def upload_file():
    file = request.files['file']
    sites = request.form['sites']
    sites = sites.split(',')
    try:
        t_json = json.loads((file.read().decode('utf-8')))
    except json.decoder.JSONDecodeError:
        return jsonify({'success': False, 'msg': "Format JSON error!"}), 500
    file_hash = hashlib.md5(json.dumps(t_json['result']).encode('utf-8')).hexdigest()
    cache = mysql.get_result_cache(file_hash)
    if cache is not None:
        result = json.loads(cache)
    else:
        result = []
        for name, files in t_json['result'].items():
            result.append(compare_torrents(name, files))
        mysql.record_upload_data(current_user.id, file_hash, json.dumps(result), request.remote_addr)

    for torrent in result:
        for t in chain(torrent['cmp_warning'], torrent['cmp_success']):
            torrents = filter(lambda k: k['site'] in sites, find_torrents_by_id(t['id']))
            t['sites'] = ",".join(["{}-{}".format(t['site'], t['sid']) for t in torrents])
        torrent['cmp_success'] = list(filter(lambda k: k['sites'] != '', torrent['cmp_success']))
        torrent['cmp_warning'] = list(filter(lambda k: k['sites'] != '', torrent['cmp_warning']))
    return jsonify({'success': True, 'base_dir': t_json['base_dir'], 'result': result})


@socketio.on('file')
@authenticated_only
def find_torrents_by_file_socket(files: dict):
    def send_result(torrent):
        for t in chain(torrent['cmp_warning'], torrent['cmp_success']):
            torrents = find_torrents_by_id(t['id'])
            t['sites'] = ",".join(["{}-{}".format(t['site'], t['sid']) for t in torrents])
        torrent['cmp_success'] = list(filter(lambda k: k['sites'] != '', torrent['cmp_success']))
        torrent['cmp_warning'] = list(filter(lambda k: k['sites'] != '', torrent['cmp_warning']))
        emit('reseed result', torrent, json=True)

    file_hash = hashlib.md5(json.dumps(files).encode('utf-8')).hexdigest()
    cache = mysql.get_result_cache(file_hash)
    if cache is not None:
        result = json.loads(cache)
        for torrent in result:
            send_result(torrent)
    else:
        result = []
        for name, file in files.items():
            torrent = compare_torrents(name, file)
            result.append(torrent)
            send_result(torrent)
        mysql.record_upload_data(current_user.id, file_hash, json.dumps(result),
                                 socketio.server.environ[request.sid]['X-Real-IP'])


@socketio.on('tid')
@authenticated_only
def find_torrents_by_id_socket(tid):
    emit('reseed result', find_torrents_by_id(tid), json=True)


def find_torrents_by_id(tid):
    cache = redis.get(tid)
    if cache:
        result = json.loads(str(cache, encoding='utf-8'))
    else:
        result = mysql.find_torrents_by_id(tid)
        redis.set(tid, json.dumps(result), current_app.config.get('REDIS_TTL', 2 * 24 * 60 * 60))
    return result


@socketio.on('hash')
@authenticated_only
def find_torrents_by_hash_socket(hex_info_hash):
    emit('reseed result', find_torrents_by_hash(hex_info_hash), json=True)


def find_torrents_by_hash(hex_info_hash):
    cache = redis.get('torrent_hash_{}'.format(hex_info_hash))
    if cache:
        tid = cache
    else:
        tid = mysql.find_tid_by_hash(hex_info_hash)
        redis.set('torrent_hash_{}'.format(hex_info_hash), tid,
                  current_app.config.get('REDIS_TTL', 2 * 24 * 60 * 60))
    return find_torrents_by_id(tid)


@reseed.route('/sites_info')
@login_required
def sites_info():
    sites = mysql.get_sites_info()
    result = list()
    for site in sites:
        result.append({'name': site['site'], 'base_url': site['base_url'], '_enable': False, 'passkey': ""})
    return jsonify(result)
