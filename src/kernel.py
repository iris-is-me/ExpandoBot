import os
import asyncio

from dotenv import load_dotenv

from .client.client import Bot

async def initialise():
    """
    Initialise the bot

    This is an async function. Run using `asyncio.run`
    """
    token = _load_token()

    bot = Bot()
    await bot.start(token)

def _load_token():
    load_dotenv()

    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set DISCORD_BOT_TOKEN in .env or the process environment before starting the bot.")
    
    return token

def main():
    asyncio.run(initialise())