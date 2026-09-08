import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class BotConfig:
    token: str
    debug: bool


def load_config() -> BotConfig:
    load_dotenv()

    return BotConfig(
        token=os.environ["DISCORD_BOT_TOKEN"],
        debug=False
    )
