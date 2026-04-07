"""An example of connecting to a conduit and subscribing to EventSub when a User Authorizes the application.

This bot can be restarted as many times without needing to subscribe or worry about tokens:
- Tokens are stored in '.tio.tokens.json' by default
- Subscriptions last 72 hours after the bot is disconnected and refresh when the bot starts.

Consider reading through the documentation for AutoBot for more in depth explanations.
"""

import os, time, re, logging, asyncio, random
from typing import TYPE_CHECKING
from threading import Thread

import twitchio
from twitchio import eventsub
from twitchio.ext import commands
import asqlite
from dotenv import load_dotenv
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from db.database import init_db, Chatter, Link, Vote
from src import store
from obs.writer import write_chatter, write_chatter_up, write_chatter_down, write_link_up, write_link_down
from receiver_server.receiver import app

load_dotenv()


if TYPE_CHECKING:
    import sqlite3


LOGGER: logging.Logger = logging.getLogger("Bot")

# Consider using a .env or another form of Configuration file!
CLIENT_ID = os.getenv("CLIENT_ID")  # The CLIENT ID from the Twitch Dev Console
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  # The CLIENT SECRET from the Twitch Dev Console
BOT_ID = os.getenv("BOT_ID")  # The Account ID of the bot user...
OWNER_ID = os.getenv("OWNER_ID")  # Your personal User ID..

class Bot(commands.AutoBot):
    def __init__(self, *, token_database: asqlite.Pool, subs: list[eventsub.SubscriptionPayload]) -> None:
        self.token_database = token_database

        if CLIENT_ID is None or CLIENT_SECRET is None or BOT_ID is None or OWNER_ID is None:
            raise ValueError("CLIENT_ID, CLIENT_SECRET, BOT_ID, and OWNER_ID must be set in the environment variables.")

        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="!",
            subscriptions=subs,
            force_subscribe=True,
        )

    async def setup_hook(self) -> None:
        # Add our component which contains our commands...
        await self.add_component(LinkProcessor(self))

    async def event_oauth_authorized(self, payload: twitchio.authentication.UserTokenPayload) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # We usually don't want subscribe to events on the bots channel...
            return

        # A list of subscriptions we would like to make to the newly authorized channel...
        subs: list[eventsub.SubscriptionPayload] = [
            eventsub.ChatMessageSubscription(broadcaster_user_id=payload.user_id, user_id=self.bot_id),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            LOGGER.warning("Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id)

    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Added token to the database for user: %s", resp.user_id)
        return resp

    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.bot_id)


class LinkProcessor(commands.Component):
    # An example of a Component with some simple commands and listeners
    # You can use Components within modules for a more organized codebase and hot-reloading.

    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"

    def __init__(self, bot: Bot) -> None:
        # Passing args is not required...
        # We pass bot here as an example...
        self.bot = bot

    def is_valid_url(self, url: str) -> str | None:
        # Normalize URL: Remove "https://", "http://", and "www."
        url = url.strip()
        url = re.sub(r'^(https?://)?(www\.)?', '', url)  # Remove https:// or www.

        # Define regex patterns for YouTube Shorts, Instagram Reels, and TikTok

        # YouTube can use either "youtube.com/shorts/..." or "youtu.be/..."
        youtube_pattern = r'^(youtube\.com/shorts/|youtu\.be/).+'

        # Instagram Reels URL pattern
        # Accept both /reel/ and /reels/ forms
        instagram_pattern = r'^instagram\.com/reels?/.+'

        # TikTok video URL pattern (with or without @username)
        tiktok_pattern = r'^tiktok\.com/@[\w-]+/video/.+'

        # Match against each pattern
        if re.match(youtube_pattern, url):
            print("[VALID] YouTube Shorts URL detected.")
            # return valid_like_count(url, "youtube") # add proper short form content and like count check
            return self.YOUTUBE
        elif re.match(instagram_pattern, url):
            print("[VALID] Instagram Reels URL detected.")
            # return valid_like_count(url, "instagram")
            return self.INSTAGRAM
        elif re.match(tiktok_pattern, url):
            print("[VALID] TikTok URL detected.")
            # return valid_like_count(url, "tiktok")
            return self.TIKTOK
        
        print("[INVALID] URL is not a valid Doomscroll source.")
        return None

    def is_valid_like_count(self, url: str, platform: str) -> bool:
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
        if platform == self.INSTAGRAM:
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

    def is_link_played_recently(self, url: str) -> bool:
        RECENCY_THRESHOLD = 60 * 60 * 2 # 2 hour

        recent_links = Link.select().where(
            (Link.url == url) &
            (Link.opened_at.is_null(False)) &
            (Link.posted_at >= time.time() - RECENCY_THRESHOLD)
        )

        return recent_links.exists()

    # An example of listening to an event
    # We use a listener in our Component to display the messages received.
    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        print(f"[{payload.broadcaster.name}] - {payload.chatter.name}: {payload.text}")


    @commands.command()
    async def hi(self, ctx: commands.Context) -> None:
        """Command that replies to the invoker with Hi <name>!

        !hi
        """
        await ctx.reply(f"Hi {ctx.chatter}!")

    @commands.command()
    async def link(self, ctx: commands.Context, *, message: str) -> None:
        """Command processes and saves a doom link

        !link
        """

        # check type of ctx.payload if it is a message
        if not isinstance(ctx.payload, twitchio.ChatMessage):
            print("[ERROR] Received !link command with non-ChatMessage payload.")
            return
        
        platform = self.is_valid_url(message)
        if not platform:
            await ctx.reply("Sorry, that doesn't look like a valid Shorts, Reels, or TikTok URL.")
            return

        if not self.is_valid_like_count(message, platform):
            await ctx.reply("Sorry, video must exist and have at least 5000 likes.")
            return

        # if self.is_link_played_recently(message):
        #     await ctx.reply("Sorry, that link or a duplicate has been played recently. Please try again later.")
        #     return

        chatter = Chatter.get_or_create(user_id=ctx.chatter.id, defaults={"username": ctx.chatter.name})[0]
        Link.create(url=message, posted_by=chatter)

        print("chatter", ctx.chatter.name)
        print("chatter id", ctx.chatter.id)
        print("message", message)
        
        await ctx.reply(f"Successfully added {platform.capitalize()} link!")

    @commands.command()
    async def w(self, ctx: commands.Context) -> None:
        """Command that replies to the invoker with Hi <name>!

        !w
        """
        # detect W

    @commands.command()
    async def l(self, ctx: commands.Context) -> None:
        """Command that replies to the invoker with Hi <name>!

        !l
        """
        # detect L


async def setup_database(db: asqlite.Pool) -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:
    # Create our token table, if it doesn't exist..
    # You should add the created files to .gitignore or potentially store them somewhere safer
    # This is just for example purposes...

    query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
    async with db.acquire() as connection:
        await connection.execute(query)

        # Fetch any existing tokens...
        rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        tokens: list[tuple[str, str]] = []
        subs: list[eventsub.SubscriptionPayload] = []

        for row in rows:
            tokens.append((row["token"], row["refresh"]))

            if row["user_id"] == BOT_ID:
                continue

            subs.extend([eventsub.ChatMessageSubscription(broadcaster_user_id=row["user_id"], user_id=BOT_ID)])

    return tokens, subs


# Our main entry point for our Bot
# Best to setup_logging here, before anything starts
def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb:
            tokens, subs = await setup_database(tdb)

            async with Bot(token_database=tdb, subs=subs) as bot:
                for pair in tokens:
                    await bot.add_token(*pair)

                await bot.start(load_tokens=False)

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt")


if __name__ == "__main__":
    main()


    # EXAMPLE COMMANDS
    # @commands.command()
    # async def say(self, ctx: commands.Context, *, message: str) -> None:
    #     """Command which repeats what the invoker sends.

    #     !say <message>
    #     """
    #     await ctx.send(message)

    # @commands.command()
    # async def add(self, ctx: commands.Context, left: int, right: int) -> None:
    #     """Command which adds to integers together.

    #     !add <number> <number>
    #     """
    #     await ctx.reply(f"{left} + {right} = {left + right}")

    # @commands.command()
    # async def choice(self, ctx: commands.Context, *choices: str) -> None:
    #     """Command which takes in an arbitrary amount of choices and randomly chooses one.

    #     !choice <choice_1> <choice_2> <choice_3> ...
    #     """
    #     await ctx.reply(f"You provided {len(choices)} choices, I choose: {random.choice(choices)}")

    # @commands.command(aliases=["thanks", "thank"])
    # async def give(self, ctx: commands.Context, user: twitchio.User, amount: int, *, message: str | None = None) -> None:
    #     """A more advanced example of a command which has makes use of the powerful argument parsing, argument converters and
    #     aliases.

    #     The first argument will be attempted to be converted to a User.
    #     The second argument will be converted to an integer if possible.
    #     The third argument is optional and will consume the reast of the message.

    #     !give <@user|user_name> <number> [message]
    #     !thank <@user|user_name> <number> [message]
    #     !thanks <@user|user_name> <number> [message]
    #     """
    #     msg = f"with message: {message}" if message else ""
    #     await ctx.send(f"{ctx.chatter.mention} gave {amount} thanks to {user.mention} {msg}")

    # @commands.group(invoke_fallback=True)
    # async def socials(self, ctx: commands.Context) -> None:
    #     """Group command for our social links.

    #     !socials
    #     """
    #     await ctx.send("discord.gg/..., youtube.com/..., twitch.tv/...")

    # @socials.command(name="discord")
    # async def socials_discord(self, ctx: commands.Context) -> None:
    #     """Sub command of socials that sends only our discord invite.

    #     !socials discord
    #     """
    #     await ctx.send("discord.gg/...")