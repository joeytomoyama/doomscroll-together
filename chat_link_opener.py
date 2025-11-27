import asyncio, ssl, random, re, subprocess, time
from urllib.parse import urlparse

# ====== CONFIG ======
CHANNEL = "doomscrolltogether"  # <-- no leading '#'
OPEN_INTERVAL_SECONDS = 10   # minimum gap between openings
DUPLICATE_TTL_SECONDS = 600  # don't reopen the same URL within 10 minutes
ALLOWED_DOMAINS = {
    "youtube.com", "youtu.be",
    "tiktok.com", "vm.tiktok.com",
    "instagram.com"
}
# Command to open a tab in Firefox.
# Linux: ["firefox", "--new-tab"]; Windows: r"C:\Program Files\Mozilla Firefox\firefox.exe", "-new-tab"
# macOS: ["open", "-a", "Firefox"]  (macOS doesn't need --new-tab; 'open' asks Firefox to open the URL)
BROWSER_CMD = ["firefox", "--new-tab"]
# ====================

HOST = "irc.chat.twitch.tv"
PORT = 6697  # TLS

URL_RE = re.compile(r'(https?://\S+)', re.IGNORECASE)

def host_allowed(u: str) -> bool:
    try:
        p = urlparse(u)
        if p.scheme not in ("http", "https"):
            return False
        host = (p.netloc or "").lower()
        return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)
    except Exception:
        return False

def safe_first_url(msg: str):
    m = URL_RE.search(msg)
    if not m:
        return None
    url = m.group(1)
    return url if host_allowed(url) else None

async def open_in_firefox(url: str):
    try:
        subprocess.Popen(BROWSER_CMD + [url])
        print(f"[OPEN] {url}")
    except FileNotFoundError:
        print("[ERROR] Firefox command not found. Adjust BROWSER_CMD.")
    except Exception as e:
        print(f"[ERROR] Failed to open URL: {e}")

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

    last_open_ts = 0.0
    recent_urls = {}  # url -> last_seen_ts

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
                url = safe_first_url(msg)
                if not url:
                    continue

                now = time.time()
                # duplicate suppression
                last_seen = recent_urls.get(url, 0)
                if now - last_seen < DUPLICATE_TTL_SECONDS:
                    continue
                recent_urls[url] = now

                # rate limiting open behavior
                if now - last_open_ts < OPEN_INTERVAL_SECONDS:
                    # defer a bit to respect interval
                    await asyncio.sleep(OPEN_INTERVAL_SECONDS - (now - last_open_ts))
                await open_in_firefox(url)
                last_open_ts = time.time()
    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()

def main():
    print("[START] Watching links in chat. Press Ctrl+C to stop.")
    try:
        asyncio.run(irc_reader(CHANNEL.lower()))
    except KeyboardInterrupt:
        print("\n[STOP] Bye.")

if __name__ == "__main__":
    import contextlib
    main()
