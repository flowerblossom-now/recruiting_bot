"""Фоновый AI-скоринг кандидата и уведомление менеджера.

Обе операции выполняются после сохранения анкеты и не должны ронять
основной поток: любая ошибка логируется и гасится.
"""

from __future__ import annotations

import logging

from aiogram import Bot

from ai_scoring import score_candidate
from config import MANAGER_CHAT_ID, POSITIONS
from database import update_ai_score

logger = logging.getLogger(__name__)


async def run_ai_scoring(bot: Bot, candidate_id: int, candidate: dict) -> None:
    """Оценить кандидата и уведомить менеджера вместе с оценкой.

    Если скоринг не удался, уведомление всё равно уходит — без оценки.
    """
    score, summary = None, None
    try:
        result = await score_candidate(candidate)
        if result:
            score, summary = result
            update_ai_score(candidate_id, score, summary)
        else:
            logger.warning("AI-скоринг не дал результата для id=%s", candidate_id)
    except Exception:
        logger.exception("Ошибка фонового AI-скоринга id=%s", candidate_id)

    await notify_manager(bot, candidate_id, candidate, score, summary)


async def notify_manager(
    bot: Bot,
    candidate_id: int,
    candidate: dict,
    score: int | None = None,
    summary: str | None = None,
) -> None:
    """Уведомить менеджера о новой анкете. Ошибки не ломают основной поток."""
    if not MANAGER_CHAT_ID:
        return

    position = next(
        (p for p in POSITIONS if p["id"] == candidate.get("position")), None
    )
    position_text = (
        f"{position['emoji']} {position['title']}" if position
        else candidate.get("position", "?")
    )
    username = candidate.get("telegram_username")
    contact_tg = f"@{username}" if username else f"tg id: {candidate['telegram_id']}"

    text = (
        f"🆕 Новая анкета #{candidate_id}\n\n"
        f"👤 {candidate['full_name']} ({contact_tg})\n"
        f"💼 {position_text}\n"
        f"📊 Опыт: {candidate['experience_years']} лет\n"
        f"📞 {candidate['email_or_phone']}\n"
        f"🕐 Готовность: {candidate['start_date']}\n"
    )
    if score is not None:
        text += f"\n🤖 AI-оценка: {score}/10\n{summary}"

    try:
        await bot.send_message(chat_id=MANAGER_CHAT_ID, text=text)
    except Exception:
        logger.exception("Не удалось уведомить менеджера (chat_id=%s)", MANAGER_CHAT_ID)
