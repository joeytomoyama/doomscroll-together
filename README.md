# doomscroll-together
doomscroll together

## Setup & Running

**Install dependencies:**
```bash
uv sync
```

**Activate virtual environment (optional):**
```bash
source .venv/bin/activate
```

**Start the main app:**
```bash
python3 -m src.main
# or with uv:
uv run python3 -m src.main

# dev mode (extra debugging behavior)
python3 -m src.main --dev
```

**Start the receiver Flask server:**
```bash
python3 -m receiver_server.receiver
# or with uv:
uv run python3 -m receiver_server.receiver
```

## Quick Reference

**Peewee (SQLite) basics**
- Connect: create `db = SqliteDatabase("my.db")`; set `class Meta: database = db` in your models.
- Create tables: `db.connect(); db.create_tables([User, Item])`.
- Insert: `User.create(name="alice")` or `u = User(name="bob"); u.save()`.
- Query: `User.select()`; filter with `User.select().where(User.name == "alice")`.
- Get one: `User.get(User.id == 1)` or safer `User.get_or_none(...)`.
- Update: `user.name = "new"; user.save()` or bulk `User.update(name="new").where(User.id == 1).execute()`.
- Delete: `user.delete_instance()` or `User.delete().where(...).execute()`.
- Relations: `Item.create(user=u, title="foo")`; backref `u.items`.
- Ordering/limit: `.order_by(User.created_at.desc()).limit(10)`.
- Transactions: `with db.atomic(): ...`.

**SQLite CLI cheatsheet (db/doomscroll.db)**
```bash
sqlite3 db/doomscroll.db
# inside sqlite:
.tables
.schema chatter
.headers on
.mode column
SELECT * FROM chatter LIMIT 5;
.quit

# one-off query from shell
sqlite3 db/doomscroll.db "SELECT * FROM chatter LIMIT 5;"
```