import json

import app


def search_torrent(dir_tree, sites):
    matched_torrents = []
    for name, files in dir_tree.items():
        matched_torrents.append(compare_torrents(name, files, sites))
    return matched_torrents


def compare_torrents(name, files, sites):
    torrents = app.redis.get(name)
    if not torrents:
        torrents = app.mysql.select_torrent(name)
        app.redis.set(name, json.dumps(torrents))
    else:
        torrents = json.loads(str(torrents, encoding='utf-8'))

    cmp_success = []
    cmp_warning = []
    for t in torrents:
        success_count = failure_count = 0
        torrent_files = eval(t['files'])
        result_site = format_sites(t['sites_existed'], sites)
        if not result_site:
            continue
        if len(torrent_files):
            if type(files) is int:
                continue

            keys = list(files.keys())
            for key in keys:
                files[key.replace('\\', '/')] = files.pop(key)  # 对于Windows，将\\更改为/，以适配数据库

            for k, v in torrent_files.items():
                if v * 0.95 < files.get(k, -1) < v * 1.05:
                    success_count += 1
                else:
                    failure_count += 1
            if failure_count:
                if success_count > failure_count:
                    cmp_warning.append({'id': t['id'], 'sites': result_site})
            else:
                cmp_success.append({'id': t['id'], 'sites': result_site})
        else:
            if type(files) is not int:
                continue
            if t['length'] * 0.95 < files < t['length'] * 1.05:
                cmp_success.append({'id': t['id'], 'sites': result_site})
    return {'name': name, 'cmp_success': cmp_success, 'cmp_warning': cmp_warning}


def format_sites(result, sites):
    formatted_result = list()
    for r in result.split(','):
        sid = r.split('-')[-1]
        site = r.replace('-' + sid, '')
        if site in sites and app.mysql.check_torrent_valid(sid, site):
            formatted_result.append(r)
    return ','.join(formatted_result)
