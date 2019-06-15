from redis import Redis

from utils.database import Database

db = Database("")
r = Redis(db=1)
