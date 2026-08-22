import asyncio
import contextlib
import logging
import signal
from types import FrameType

from ..core.client import Bot


logger = logging.getLogger(__name__)

async def run_bot(bot: Bot, token: str) -> None:
    shutdown_event = asyncio.Event()
    _register_shutdown_signals(shutdown_event)

    bot_task = asyncio.create_task(bot.start(token), name="discord-bot")
    shutdown_task = asyncio.create_task(shutdown_event.wait(), name="shutdown-signal")
    
    try:
        done, _pending = await asyncio.wait(
            {bot_task, shutdown_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        if shutdown_task in done:
            logger.info("Shutdown requested; closing bot")
            await _close_bot(bot)
            logger.info(
                "Bot close completed; is_closed=%s; task_done=%s",
                bot.is_closed(),
                bot_task.done(),
            )
            await _await_bot_task_shutdown(bot_task)
            return

        shutdown_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await shutdown_task

        await bot_task
    finally:
        if not bot.is_closed():
            await _close_bot(bot)


def _register_shutdown_signals(shutdown_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()

    def request_shutdown(signum: int) -> None:
        signal_name = signal.Signals(signum).name
        if shutdown_event.is_set():
            logger.info("Received %s; shutdown already in progress", signal_name)
            return

        logger.info("Received %s; requesting graceful shutdown", signal_name)
        shutdown_event.set()

    def make_signal_handler(signum: int):
        def handle_shutdown_signal(_signum: int, _frame: FrameType | None) -> None:
            loop.call_soon_threadsafe(request_shutdown, signum)

        return handle_shutdown_signal

    for sig_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue

        try:
            loop.add_signal_handler(sig, request_shutdown, sig)
        except NotImplementedError:
            signal.signal(sig, make_signal_handler(sig))


async def _close_bot(bot: Bot) -> None:
    try:
        await bot.close()
    except RuntimeError as exc:
        if _is_session_closed_error(exc):
            logger.debug("Ignored session-closed error during bot shutdown")
            return
        raise


async def _await_bot_task_shutdown(bot_task: asyncio.Task) -> None:
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    except RuntimeError as exc:
        if _is_session_closed_error(exc):
            logger.debug("Ignored session-closed error while bot task stopped")
            return
        raise


def _is_session_closed_error(exc: RuntimeError) -> bool:
    return str(exc) == "Session is closed"
