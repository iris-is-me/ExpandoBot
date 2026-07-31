import discord
import datetime
import logging

class Bot(discord.Bot):
    def __init__(self, description=None, *args, **options):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        super().__init__(description, *args, **options)
    
    async def on_connect(self):
        await super().on_connect()
        self.logger.info(f"Logged in as {self.user}")
        self.connect_time = datetime.datetime.now(datetime.timezone.utc)
    
    async def close(self):
        self.close_time = datetime.datetime.now(datetime.timezone.utc)
        return await super().close()
    
    async def on_ready(self):
        self.ready_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger.info(f"Client ready")
