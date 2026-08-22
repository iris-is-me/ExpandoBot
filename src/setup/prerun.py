# src/setup/prerun.py
import logging
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class PrerunContext:
    env: Mapping[str, str]


Check = Callable[[PrerunContext], None]


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def check_discord_token(ctx: PrerunContext) -> None:
    if not ctx.env.get("DISCORD_BOT_TOKEN"):
        raise RuntimeError(
            "Set DISCORD_BOT_TOKEN in .env or the process environment before starting the bot."
        )


CHECKS: tuple[Check, ...] = (
    check_discord_token,
)


def run_prerun_checks(ctx: PrerunContext) -> None:
    logger = logging.getLogger(__name__)

    for check in CHECKS:
        logger.debug("Running prerun check: %s", check.__name__)
        check(ctx)


def prerun() -> None:
    setup_logging()
    run_prerun_checks(PrerunContext(env=os.environ))
