import asyncio

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
        self._bot_config = None

        self.bot = None
        self.plugin_manager = None   # Currently does nothing to the project
        self.config = None   # Currently does nothing to the project
        self.database = None   # Currently does nothing to the project

    async def initialise_kernel(self):

        self._load_configuration()
        self._initialise_database()
        await self._initialise_bot()
        self._initialise_plugin_manager()

    async def _initialise_bot(self):
        self._bot_config = load_config()

        self._run_prerun_scripts()

        self.bot = Bot()
        await run_bot(self.bot, self._bot_config)

    def _load_configuration(self):
        self.config = ConfigManager()

    def _initialise_plugin_manager(self):
        self.plugin_manager = PluginManager(
            bot=self.bot,
            config=self.config,
            database=self.database,
            builtin_plugins_dir=Path("builtin_plugins"),
            user_plugins_dir=Path("plugins"),
        )

    def _initialise_database(self):
        self.database = SQLiteDatabase(self.config.paths.database_file)

    def _run_prerun_scripts(self):
        prerun()