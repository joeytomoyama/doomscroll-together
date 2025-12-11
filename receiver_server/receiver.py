import subprocess
from datetime import datetime
import random

from flask import Flask, request # global flask installation

from chat_link_opener import BROWSER_CMD
import store
from db.database import Chatter, Link

app = Flask(__name__)

@app.post("/sample")
async def sample():
    global last_value
    data = request.get_json(force=True, silent=True) or {}
    value = data.get("value")

    if value != "loop":
        return {"status": "ignored"}

    store.CURRENT_CHATTER = None
    link = get_link()
    if not link:
        return {"status": "no_link"}
    
    await open_in_firefox(link.url)

    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"[{timestamp}] Received value from browser:", value)

    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

def get_link():
    recent_links = Link.select().where(Link.posted_at >= datetime.now().timestamp() - 10) # last 10 seconds
    # if recent_links is not empty, return random one
    if recent_links:
        return random.choice(recent_links)
    return recent_links.order_by(Link.posted_at.desc()).first()  # return the most recent link if no recent links
    

async def open_in_firefox(url: str):
    try:
        subprocess.Popen(BROWSER_CMD + [url])
        print(f"[OPEN] {url}")
    except FileNotFoundError:
        print("[ERROR] Firefox command not found. Adjust BROWSER_CMD.")
    except Exception as e:
        print(f"[ERROR] Failed to open URL: {e}")