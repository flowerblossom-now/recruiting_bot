"""Точка входа Telegram рекрутингового бота на aiogram 3.

Обработчики живут в пакете `handlers`, фоновые задачи — в `services`.
Здесь остаётся только запуск: логирование, инициализация БД и polling.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, COMPANY_NAME, LOG_FILE
from database import init_db
from handlers import build_router

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Настроить логирование в консоль и файл."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    with contextlib.suppress(OSError):
        handlers.append(logging.FileHandler(str(LOG_FILE), encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


async def main() -> None:
    """Запуск бота."""
    setup_logging()
    init_db()

    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Укажите токен бота в файле .env (BOT_TOKEN=...)")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build_router())

    logger.info("Бот %s запущен", COMPANY_NAME)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
