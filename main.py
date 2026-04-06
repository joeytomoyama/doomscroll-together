import asyncio
import twitchio

from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

async def main() -> None:
    if CLIENT_ID is None or CLIENT_SECRET is None:
        print("Error: CLIENT_ID and CLIENT_SECRET must be set in the environment.")
        return
    
    async with twitchio.Client(client_id=CLIENT_ID, client_secret=CLIENT_SECRET) as client:
        await client.login()
        user = await client.fetch_users(logins=["doomscrolltogether", "torpedobear"])
        for u in user:
            print(f"User: {u.name} - ID: {u.id}")

if __name__ == "__main__":
    asyncio.run(main())