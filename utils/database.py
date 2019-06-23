from threading import Lock

import pymysql

from env import DB_USER, DB_PASS, DB_NAME


class Database:
    _commit_lock = Lock()

    def __init__(self, site):
        self.db = pymysql.connect(user=DB_USER, password=DB_PASS, db=DB_NAME,
                                  charset='utf8mb4', autocommit=True)
        self.site = site

    def exec(self, sql: str, cursor: object = pymysql.cursors.DictCursor):
        with self._commit_lock:
            self.db.ping(reconnect=True)
            cursor = self.db.cursor(cursor)
            cursor.execute(sql)
            data = cursor.fetchall()
        return data

    def get_sites_info(self):
        return self.exec("SELECT `site`, `base_url` FROM `sites` WHERE `show` = 1")

    def select_torrent(self, name):
        return self.exec("SELECT * FROM `torrents` WHERE `name` = '{}'".format(pymysql.escape_string(str(name))))

    def check_torrent_valid(self, sid, site):
        return self.exec(
            "SELECT COUNT(*) AS c FROM `torrent_records` WHERE `sid` = '{}' AND `site` = '{}'".format(
                sid, site))[0]['c']

    def hit(self, tid):
        self.exec("INSERT INTO `historys` (`tid`) VALUES('{}')".format(tid))

    def signup(self, username, passhash, tjupt_id):
        self.exec("INSERT INTO `users` (`username`, `passhash`, `tjupt_id`) VALUES ('{}', '{}', '{}')".format(
            pymysql.escape_string(str(username)), pymysql.escape_string(passhash),
            pymysql.escape_string(str(tjupt_id))))

    def get_user(self, username):
        return self.exec("SELECT * FROM `users` WHERE `username` = '{}'".format(pymysql.escape_string(str(username))))

    def check_tjuid_registered(self, tjupt_id):
        return self.exec("SELECT COUNT(*) as `a` FROM `users` WHERE `tjupt_id` = '{}'".format(
            pymysql.escape_string(str(tjupt_id))))[0]['a'] == 0
