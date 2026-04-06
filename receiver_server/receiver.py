from datetime import datetime
import random
import time

from flask import Flask, request # global flask installation

from src import robot
from src import store
from db.database import Chatter, Link, Vote
from obs.writer import write_chatter, write_chatter_up, write_chatter_down, write_link_up, write_link_down

app = Flask(__name__)

def print_links():
    print("[LINKS] Current links in database including opened, validated, and all:")
    for link in Link.select():
        print(f"  - {link.url} (posted by {link.posted_by.username if link.posted_by else 'unknown'}, opened_at={datetime.fromtimestamp(link.opened_at) if link.opened_at else 'not opened'}, validated={link.validated})")

def get_link():
    now = time.time()
    cutoff = now - 60

    # random link posted in last 60 seconds (recency bias)
    recent_links = list(Link.select().where(
        (Link.posted_at >= cutoff) & 
        (Link.opened_at.is_null(True))
        # TODO: add validated flag
    ))

    if recent_links:
        print(f"[LINK] Choosing from recent links.")
        link = random.choice(recent_links)
    else:
        # return the most recent unopened link if no recent links
        print(f"[LINK] No recent links, choosing most recent unopened link.")
        link = (
            Link.select()
            .where(Link.opened_at.is_null(True))
            .order_by(Link.posted_at.desc())
            .first()
        )
    
    if link:
        link.opened_at = now
        link.save()
        print_links()
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