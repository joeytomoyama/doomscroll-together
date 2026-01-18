from datetime import datetime
import random

from flask import Flask, request # global flask installation

from src import robot
from src import store
from db.database import Chatter, Link, Vote
from obs.writer import write_chatter, write_chatter_up, write_chatter_down, write_link_up, write_link_down

app = Flask(__name__)

def get_link():
    # random link posted in last 10 seconds (recency bias)
    recent_links = Link.select().where(Link.posted_at >= datetime.now().timestamp() - 10)

    if recent_links:
        print(f"[LINK] Choosing from recent links.")
        return random.choice(recent_links)
    else:
        # return the most recent link if no recent links
        print(f"[LINK] No recent links, choosing most recent link.")
        return recent_links.order_by(Link.posted_at.desc()).first()
    
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