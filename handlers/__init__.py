"""Сборка роутеров бота.

Порядок подключения значим: команды перехватываются раньше анкеты,
fallback — последним.
"""

from __future__ import annotations

from aiogram import Router

from handlers.application import application_router
from handlers.common import commands_router, fallback_router


def build_router() -> Router:
    """Собрать корневой роутер бота."""
    root = Router(name="root")
    root.include_router(commands_router)
    root.include_router(application_router)
    root.include_router(fallback_router)
    return root
