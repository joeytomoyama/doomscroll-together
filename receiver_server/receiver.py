from datetime import datetime
import random
import time

from peewee import fn

from flask import Flask, request # global flask installation

from src import robot
from src import store
from db.database import Chatter, Link, Vote, db
from obs.writer import write_chatter, write_chatter_up, write_chatter_down, write_link_up, write_link_down

app = Flask(__name__)

def get_link():
    now = time.time()
    cutoff = now - 10

    # Wrap selection and update in a single transaction to avoid races
    with db.atomic():
        # Prefer an unopened link from the last 10 seconds, picked at random in DB
        link = (
            Link.select()
            .where((Link.posted_at >= cutoff) & (Link.opened_at.is_null(True)))
            .order_by(fn.Random())
            .limit(1)
            .first()
        )

        if not link:
            # Fallback: most recent unopened link
            link = (
                Link.select()
                .where(Link.opened_at.is_null(True))
                .order_by(Link.posted_at.desc())
                .first()
            )

        if link:
            link.opened_at = now
            link.save()
            return link
    
def reset_votes():
    # drop whole Vote table
    Vote.delete().execute()

@app.post("/loop")
def loop():
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"[{timestamp}] Received loop from browser")

    store.CURRENT_CHATTER = None
    link = get_link()
    if not link:
        print("[SAMPLE] No links available to open.")
        return {"status": "no_link"}
    
    # robot.open_in_firefox(link.url)
    robot.openURLLikeHuman(link.url)
    username = link.posted_by.username if link.posted_by else "unknown_user"
    print(f"[SAMPLE] Opening link: {link.url} posted by {username}")
    write_chatter(username)
    store.CURRENT_CHATTER = username
    store.CURRENT_LINK = link
    reset_votes()

    return {"status": "ok"}