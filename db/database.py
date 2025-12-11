from peewee import Model, SqliteDatabase, CharField, DateTimeField, ForeignKeyField, BooleanField
import os
import datetime

# SQLite database connection - store in the db/ directory
db_path = os.path.join(os.path.dirname(__file__), 'doomscroll.db')
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db

class Chatter(BaseModel):
    username = CharField(unique=True)
    w_count = CharField(default='0')
    l_count = CharField(default='0')
    is_banned = BooleanField(default=False)

class Link(BaseModel):
    url = CharField()
    posted_by = ForeignKeyField(Chatter, backref='links', null=True)
    posted_at = DateTimeField(default=datetime.datetime.now)
    opened_at = DateTimeField(null=True, default=None)

# Initialize database and create tables
def init_db():
    db.connect()
    db.create_tables([Chatter, Link], safe=True)
    print("[DB] Database initialized")

if __name__ == "__main__":
    init_db()
