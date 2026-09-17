import asyncio
import logging

from pathlib import Path

from .setup.config import load_config
from .setup.lifecycle import run_bot
from .setup.prerun import prerun

from .core.client import Bot
from .core.config import ConfigManager
from .core.plugin_manager import PluginManager
from .core.sqlite import SQLiteDatabase

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

    async def initialise_kernel(self):
        self.logger.info("Initialising kernel...")

        self._load_configuration()
        self._initialise_database()
        self._initialise_plugin_manager()
        await self._initialise_bot()

        self.logger.info("Kernel finished initialising")

    async def _initialise_bot(self):
        self._bot_config = load_config()

        self._run_prerun_scripts()

        self.logger.info("Initialising bot...")
        self.bot = Bot(
            config = self.config,
            database = self.database,
            plugin_manager = self.plugin_manager
        )
        self.logger.info("Running bot...")
        await run_bot(self.bot, self._bot_config)

    def _load_configuration(self):
        
        self.logger.info("Initialising configuration...")
        self.config = ConfigManager()

        self.logger.info("Ensuring config files exists...")
        self.config.ensure_files()

    def _initialise_plugin_manager(self):
        self.logger.info("Initialising plugin manager...")
        self.plugin_manager = PluginManager(
            bot=self.bot,
            config=self.config,
            database=self.database,
            builtin_plugins_dir=Path("builtin_plugins"),
            user_plugins_dir=Path("plugins"),
        )

    def _initialise_database(self):
        self.logger.info("Initialising database...")
        self.database = SQLiteDatabase(self.config.paths.database_file)

    def _run_prerun_scripts(self):
        self.logger.info("Prerunning scripts...")
        prerun()