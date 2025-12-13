from datetime import datetime
import random

from flask import Flask, request # global flask installation

import robot
import store
from db.database import Chatter, Link, Vote

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

@app.post("/sample")
def sample():
    data = request.get_json(force=True, silent=True) or {}
    value = data.get("value")

    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"[{timestamp}] Received value from browser:", value)

    if value != "loop":
        return {"status": "ignored"}

    store.CURRENT_CHATTER = None
    link = get_link()
    if not link:
        print("[SAMPLE] No links available to open.")
        return {"status": "no_link"}
    
    robot.open_in_firefox(link.url)
    store.CURRENT_CHATTER = link.posted_by if link.posted_by else ""
    reset_votes()

    return {"status": "ok"}

@app.post("/progress")
def progress():
    data = request.get_json(force=True, silent=True) or {}
    currentTime = data.get("currentTime")
    duration = data.get("duration")

    # if currentTime is None or duration is None:
    #     return {"status": "ignored"}
    
    # print(f"[PROGRESS] {currentTime} / {duration}")

    # if duration - currentTime <= 5.0:
    #     reset_votes()
    #     print("[VOTES] Votes reset for next link.")

    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)