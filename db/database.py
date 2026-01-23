from peewee import Model, SqliteDatabase, CharField, FloatField, ForeignKeyField, BooleanField, IntegerField
import os
import time

# SQLite database connection - store in the db/ directory
db_path = os.path.join(os.path.dirname(__file__), 'doomscroll.db')
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db

class Chatter(BaseModel):
    username = CharField(unique=True)
    user_id = CharField(null=True)
    w_count = IntegerField(default=0)
    l_count = IntegerField(default=0)

class Link(BaseModel):
    url = CharField()
    posted_by = ForeignKeyField(Chatter, backref='links', null=True)
    posted_at = FloatField(default=time.time)
    opened_at = FloatField(null=True, default=None)

class Vote(BaseModel):
    # link = ForeignKeyField(Link, backref='votes')
    chatter = ForeignKeyField(Chatter, backref='votes')
    is_upvote = BooleanField()

# Initialize database and create tables
def init_db():
    db.connect()
    db.create_tables([Chatter, Link, Vote], safe=True)
    print("[DB] Database initialized")

if __name__ == "__main__":
    init_db()
