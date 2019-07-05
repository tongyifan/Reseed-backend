import pymysql
from flaskext.mysql import MySQL


class Database(MySQL):
    def exec(self, sql: str, cursor: object = pymysql.cursors.DictCursor):
        db = self.get_db()
        cursor = db.cursor(cursor)
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
