import os
import sys
import socket
import asyncio
import logging
import aiohttp

from pathlib import Path

from .setup.config import load_config
from .setup.lifecycle import run_bot
from .setup.prerun import prerun

from .core.client import Bot
from .core.config import ConfigManager
from .core.plugin_manager import PluginManager
from .core.sqlite import SQLiteDatabase

INTERNET_CHECK_HOST = "discord.com"
INTERNET_CHECK_PORT = 443
INTERNET_CHECK_TIMEOUT = 5

def main():
    kernel = Kernel()
    asyncio.run(kernel.initialise_kernel())

class Kernel:
    def __init__(self) -> None:
        self.logger: logging.Logger = logging.getLogger(__name__)

        self._bot_config = None

        self.bot = None
        self.plugin_manager = None
        self.config = None
        self.database = None

    # Kernel

    async def initialise_kernel(self):
        self.logger.info("Initialising kernel...")

        self._load_configuration()
        self._initialise_database()
        await self._initialise_bot()
        await self._initialise_plugin_manager()

        await self.bot._wait_until_bot_starts()

        await self.database.connect()
        await self.plugin_manager.start_plugins()

        self.logger.debug("Client is now running alongside plugins, databases, and config")

        await self._wait_until_bot_stops()

        await self.plugin_manager.end_plugins()
        await self.database.close()

    # Bot

    async def _initialise_bot(self):
        self._bot_config = load_config()

        self._run_prerun_scripts()
        await self._ensure_internet_connection()

        self.logger.info("Initialising bot...")
        self.bot = Bot(
            config = self.config,
            database = self.database,
        )
        self.logger.info("Running bot...")

        self._bot_wrapper = asyncio.create_task(run_bot(self.bot, self._bot_config), name="run-bot-wrapper")


    async def _wait_until_bot_stops(self):
        while True:
            await asyncio.sleep(5)
            if self.bot.is_closed(): # or self._bot_wrapper.done():
                return

    # Config

    def _load_configuration(self):
        
        self.logger.info("Initialising configuration...")
        self.config = ConfigManager()

        self.logger.info("Ensuring config files exists...")
        self.config.ensure_files()


    # Plugins

    async def _initialise_plugin_manager(self):
        self.logger.info("Initialising plugin manager...")
        self.plugin_manager = PluginManager(
            bot=self.bot,
            config=self.config,
            database=self.database,
            builtin_plugins_dir=Path("builtin_plugins"),
            user_plugins_dir=Path("plugins"),
        )
        self.logger.info("Plugin manager initialised")

    # Database

    def _initialise_database(self):
        self.logger.info("Initialising database...")
        self.database = SQLiteDatabase(self.config.paths.database_file)
        self.logger.info("Database initialised")

    # Preruns

    def _run_prerun_scripts(self):
        self.logger.info("Prerunning scripts...")
        prerun()

    async def _ensure_internet_connection(self):
        self.logger.info("Checking internet connection...")

        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(INTERNET_CHECK_HOST, INTERNET_CHECK_PORT),
                timeout=INTERNET_CHECK_TIMEOUT,
            )
        except (OSError, TimeoutError) as exc:
            self.logger.error(
                "You must be connected to the internet to run a Discord bot"
            )
            raise SystemExit(1) from exc

        writer.close()
        await writer.wait_closed()
