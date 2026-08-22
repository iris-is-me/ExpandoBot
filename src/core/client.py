import discord
import datetime
import logging

class Bot(discord.Bot):
    def __init__(self, description=None, *args, **options):
        self.logger = logging.getLogger(__name__)
        self.shutting_down = False
        super().__init__(description, *args, **options)
    
    async def on_connect(self):
        await super().on_connect()
        self.logger.info("Logged in as %s", self.user)
        self.connect_time = datetime.datetime.now(datetime.timezone.utc)
    
    async def close(self):
        self.close_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger.info(f"Client shutting down")
        return await super().close()
    
    async def on_ready(self):
        self.ready_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger.info(f"Client ready")
