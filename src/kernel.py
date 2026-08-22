import asyncio

from .setup.config import load_config
from .setup.lifecycle import run_bot
from .setup.prerun import prerun

from .core.client import Bot

async def initialise():
    """
    Initialise the bot

    This is an async function. Run using `asyncio.run`
    """

    config = load_config()

    prerun()

    bot = Bot()
    await run_bot(bot, config.token)


def main():
    asyncio.run(initialise())
