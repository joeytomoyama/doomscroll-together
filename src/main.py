import asyncio, ssl, random, re, subprocess, time
import contextlib
from threading import Thread

from db.database import init_db, Chatter, Link, Vote
from src import store
from obs.writer import write_chatter, write_chatter_up, write_chatter_down, write_link_up, write_link_down
from receiver_server.receiver import app

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import time

# ====== CONFIG ======
CHANNEL = "doomscrolltogether"  # <-- no leading '#'

# ====================

HOST = "irc.chat.twitch.tv"
PORT = 6697  # TLS


def valid_like_count(url: str, platform: str) -> bool:
    """
    Returns True if the video passes the like threshold
    (anti self-promo filter), False otherwise.

    platform: "youtube", "tiktok", or "instagram"
    """

    MIN_LIKES = 5000
    MIN_AGE_HOURS = 6  # optional but recommended

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        # "runtime": ["node"],
    }

    # Instagram benefits greatly from cookies
    if platform == "instagram":
        ydl_opts["cookiesfrombrowser"] = ("firefox",) # type: ignore

    try:
        with YoutubeDL(ydl_opts) as ydl: # type: ignore
            info = ydl.extract_info(url, download=False)
    except DownloadError:
        return False

    likes = info.get("like_count")
    timestamp = info.get("timestamp")

    print(f"[CHECK] {platform.capitalize()} video has {likes} likes and timestamp {timestamp}.")

    # Missing or invalid like count → fail
    if not isinstance(likes, int):
        return False

    if likes < MIN_LIKES:
        return False

    # Optional age gate (strongly recommended)
    if timestamp:
        age_hours = (time.time() - timestamp) / 3600
        if age_hours < MIN_AGE_HOURS:
            return False

    return True


def is_valid_doom_url(url: str) -> bool:
    # Normalize URL: Remove "https://", "http://", and "www."
    url = url.lower().strip()
    url = re.sub(r'^(https?://)?(www\.)?', '', url)  # Remove https:// or www.

    # Define regex patterns for YouTube Shorts, Instagram Reels, and TikTok

    # YouTube can use either "youtube.com/shorts/..." or "youtu.be/..."
    youtube_pattern = r'^(youtube\.com/shorts/[\w-]+|youtu\.be/[\w-]+)$'

    # Instagram Reels URL pattern
    instagram_pattern = r'^instagram\.com/reel/[\w-]+$'

    # TikTok video URL pattern (with or without @username)
    tiktok_pattern = r'^tiktok\.com/@[\w-]+/video/\d+$'

    # Match against each pattern
    if re.match(youtube_pattern, url):
        print("[VALID] YouTube Shorts URL detected.")
        return valid_like_count(url, "youtube") # add proper short form content and like count check
    elif re.match(instagram_pattern, url):
        print("[VALID] Instagram Reels URL detected.")
        return valid_like_count(url, "instagram")
    elif re.match(tiktok_pattern, url):
        print("[VALID] TikTok URL detected.")
        return valid_like_count(url, "tiktok")
    
    print("[INVALID] URL is not a valid Doomscroll source.")
    return False

def get_twitch_value(raw, key):
    try:
        tag_section = raw.split(' ', 1)[0]
        for tag in tag_section.lstrip('@').split(';'):
            if tag.startswith(key + "="):
                return tag.split("=", 1)[1]
    except IndexError:
        pass
    return None

def get_twitch_msg(raw):
    try:
        return raw.split("PRIVMSG", 1)[1].split(":", 1)[1]
    except IndexError:
        return ""

def handle_vote_or_link(text: str):
    username = get_twitch_value(text, "display-name") or "unknown_user"
    user_id = get_twitch_value(text, "user-id") or ""
    msg = get_twitch_msg(text).strip()

    # get chatter from db
    chatter = Chatter.get_or_create(username=username, defaults={'user_id': user_id})[0]
    print(f"[CHATTER] {chatter.username} (W:{chatter.w_count} L:{chatter.l_count})")

    # check if vote
    if msg.lower() == "w" or msg.lower() == "l":
        if not store.ACTIVE:
            print(f"[VOTE] Ignored vote from {chatter.username} because not ACTIVE.")
            return
        
        is_upvote = msg.lower() == "w"
        vote, created = Vote.get_or_create(chatter=chatter, defaults={'is_upvote': is_upvote})
        # update chatter's w_count or l_count
        if created:
            if is_upvote:
                chatter.w_count += 1
                print(f"[VOTE] {chatter.username} voted W (total W: {chatter.w_count})")
                write_chatter_up(chatter.w_count)
            else:
                chatter.l_count += 1
                print(f"[VOTE] {chatter.username} voted L (total L: {chatter.l_count})")
                write_chatter_down(chatter.l_count)
            chatter.save()
        
    if is_valid_doom_url(msg):
        Link.create(url=msg, posted_by=chatter)


async def irc_reader(channel: str):
    ctx = ssl.create_default_context()
    reader, writer = await asyncio.open_connection(HOST, PORT, ssl=ctx)

    anon_suffix = random.randint(10000, 99999)
    nick = f"justinfan{anon_suffix}"

    # Request Twitch capabilities (tags/commands help, but not required to just read).
    def send(cmd: str):
        writer.write((cmd + "\r\n").encode("utf-8"))

    # Anonymous pattern: send PASS with any random string (or blank), and a 'justinfan' nick.
    send(f"PASS justinfan{random.randint(1, 10**8)}")
    send(f"NICK {nick}")
    send("CAP REQ :twitch.tv/tags twitch.tv/commands")
    send(f"JOIN #{channel}")
    await writer.drain()
    print(f"[IRC] Connected as {nick}. Joined #{channel}")

    try:
        while True:
            line = await reader.readline()
            if not line:
                print("[IRC] Disconnected (EOF). Reconnecting in 3s...")
                await asyncio.sleep(3)
                return await irc_reader(channel)

            text = line.decode("utf-8", errors="ignore").strip()
            if text.startswith("PING"):
                # Keepalive
                pong = text.replace("PING", "PONG", 1)
                send(pong)
                await writer.drain()
                continue

            # PRIVMSG format: :user!user@user.tmi.twitch.tv PRIVMSG #channel :message...
            if "PRIVMSG" in text:
                handle_vote_or_link(text)
    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()

def main():
    print("[START] Watching links in chat. Press Ctrl+C to stop.")
    try:
        init_db()
        
        # Start Flask server in a separate thread
        flask_thread = Thread(target=lambda: app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False))
        flask_thread.daemon = True
        flask_thread.start()
        print("[FLASK] Receiver server started on http://127.0.0.1:5000")
        
        # Start IRC reader (blocking)
        asyncio.run(irc_reader(CHANNEL.lower()))
        # print(valid_like_count("https://www.instagram.com/reels/DSM51Z8Afsl/", "instagram"))
        # print(valid_like_count("https://www.tiktok.com/@gemmagottardi/video/7563995786871082262", "tiktok"))
        # print(valid_like_count("https://www.youtube.com/shorts/520JzVVudaI", "youtube"))
    except KeyboardInterrupt:
        print("\n[STOP] Bye.")

if __name__ == "__main__":
    main()
