import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class BotConfig:
    token: str


def load_config() -> BotConfig:
    load_dotenv()

    return BotConfig(
        token=os.environ["DISCORD_BOT_TOKEN"],
    )
