import asyncio, ssl, random, re, subprocess, time

from db.database import init_db, Chatter, Link
import store

# ====== CONFIG ======
CHANNEL = "doomscrolltogether"  # <-- no leading '#'

# Command to open a tab in Firefox.
# Linux: ["firefox", "--new-tab"]; Windows: r"C:\Program Files\Mozilla Firefox\firefox.exe", "-new-tab"
# macOS: ["open", "-a", "Firefox"]  (macOS doesn't need --new-tab; 'open' asks Firefox to open the URL)
BROWSER_CMD = ["firefox", "--new-tab"]
# ====================

HOST = "irc.chat.twitch.tv"
PORT = 6697  # TLS

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
        return True # add proper short form content and like count check
    elif re.match(instagram_pattern, url):
        return True
    elif re.match(tiktok_pattern, url):
        return True
    
    return False

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
                try:
                    msg = text.split("PRIVMSG", 1)[1].split(":", 1)[1]
                except Exception:
                    continue

                print(f"[MSG] {msg}")
                valid = is_valid_doom_url(msg)
                if not valid:
                    continue

                # await open_in_firefox(msg)
                # store.WAITLIST.add(msg)
                user = text.split("!", 1)[0][1:]  # Extract username
                # if user doesn't exist in db, create them
                user, _created = Chatter.get_or_create(username=user)
                # store.CURRENT_CHATTER = user
                Link.create(url=msg, posted_by=user)
    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()

def main():
    print("[START] Watching links in chat. Press Ctrl+C to stop.")
    try:
        init_db()
        asyncio.run(irc_reader(CHANNEL.lower()))
    except KeyboardInterrupt:
        print("\n[STOP] Bye.")

if __name__ == "__main__":
    import contextlib
    main()
