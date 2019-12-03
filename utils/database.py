import pymysql
from flaskext.mysql import MySQL


class Database(MySQL):
    def exec(self, sql: str, args=None, cursor: object = pymysql.cursors.DictCursor):
        db = self.get_db()
        cursor = db.cursor(cursor)
        cursor.execute(sql, args)
        data = cursor.fetchall()
        return data

    def get_sites_info(self):
        return self.exec("SELECT `site`, `base_url` FROM `sites` WHERE `show` = 1")

    def select_torrent(self, name):
        return self.exec("SELECT `id`, `name`, `files`, `length` FROM `torrents` WHERE `name` = %s",
                         (str(name),))

    def check_torrent_valid(self, sid, site):
        return self.exec("SELECT COUNT(*) AS c FROM `torrent_records` WHERE `sid` = %s AND `site` = %s",
                         (sid, site))[0]['c']

    def record_upload_data(self, uid, hash, result, ip):
        self.exec("INSERT INTO `historys` (`uid`, `hash`, `result`, `ip`) VALUES(%s, %s, %s, %s)",
                  (uid, hash, result, ip))

    def get_result_cache(self, hash):
        cache = self.exec('''SELECT `result` FROM `historys` WHERE `hash` = %s 
                                AND TIMESTAMPDIFF(HOUR, `time`, NOW()) < 24 ORDER BY `time` DESC''', (hash,))
        return cache[0]['result'] if cache else None

    def signup(self, username, passhash, site, user_id):
        col = 'tjupt_id'
        if site == 'ourbits':
            col = 'ourbits_id'

        self.exec("INSERT INTO `users` (`username`, `passhash`, `{}`) VALUES (%s, %s, %s)".format(col),
                  (str(username), passhash, str(user_id)))

    def get_user(self, username='', uid=0):
        if username:
            user = self.exec("SELECT * FROM `users` WHERE `username` = %s LIMIT 1", (str(username),))
        elif uid:
            user = self.exec("SELECT * FROM `users` WHERE `id` = %s LIMIT 1", (str(uid),))
        else:
            user = None
        return user[0] if user else None

    def check_site_id_registered(self, site, user_id):
        if site == 'ourbits':
            return self.check_obid_registered(user_id)
        return self.check_tjuid_registered(user_id)

    def check_obid_registered(self, user_id):
        return self.exec("SELECT COUNT(*) as `a` FROM `users` WHERE `ourbits_id` = %s", (str(user_id),))[0]['a'] == 0

    def check_tjuid_registered(self, user_id):
        return self.exec("SELECT COUNT(*) as `a` FROM `users` WHERE `tjupt_id` = %s", (str(user_id),))[0]['a'] == 0

    def ban_user(self, uid):
        self.exec("UPDATE `users` SET enable = 0 WHERE `id` = %s", uid)

    def find_torrents_by_id(self, tid):
        return self.exec("SELECT site, sid FROM torrent_records WHERE tid = %s", (tid,))
