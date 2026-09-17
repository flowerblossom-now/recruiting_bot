"""Анкета кандидата: выбор вакансии, общие вопросы, вопросы по специальности."""

from __future__ import annotations

import asyncio
import json
import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from ai_dialogue import humanize_question, is_shallow, make_followup
from config import (
    AI_DIALOGUE_ENABLED,
    AI_ENABLED,
    COMPANY_NAME,
    POSITIONS,
    QUESTION_START_DATE,
    QUESTIONS_BY_POSITION,
    QUESTIONS_COMMON,
    START_DATE_OPTIONS,
)
from database import save_candidate
from keyboards import main_keyboard, start_date_keyboard, status_keyboard
from services.notifications import notify_manager, run_ai_scoring
from states import CandidateForm
from validators import validate_contact, validate_experience, validate_name

application_router = Router(name="application")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Выбор вакансии
# ---------------------------------------------------------------------------

@application_router.callback_query(
    CandidateForm.choosing_position, F.data.startswith("pos_")
)
async def position_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора вакансии, старт анкеты."""
    position_id = callback.data.removeprefix("pos_")
    position = next((p for p in POSITIONS if p["id"] == position_id), None)

    if not position:
        await callback.answer("Вакансия не найдена", show_alert=True)
        return

    await state.update_data(
        position=position_id,
        specialty_questions=QUESTIONS_BY_POSITION.get(position_id, []),
        specialty_index=0,
        specialty_answers={},
        dialogue_history=[],
        awaiting_followup=False,
        pending_followup_q="",
    )

    await callback.message.answer(
        f"✅ Вы выбрали: *{position['emoji']} {position['title']}*\n\n"
        f"Давайте заполним анкету.\n\n"
        f"📝 {QUESTIONS_COMMON[0]['text']}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(CandidateForm.full_name)
    await callback.answer()


# ---------------------------------------------------------------------------
# Общие вопросы
# ---------------------------------------------------------------------------

@application_router.message(CandidateForm.full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    """Сохранить ФИО, спросить контакт."""
    is_valid, result = validate_name(message.text)
    if not is_valid:
        await message.answer(result)
        return
    await state.update_data(full_name=result)
    await message.answer(f"📝 {QUESTIONS_COMMON[1]['text']}")
    await state.set_state(CandidateForm.email_or_phone)


@application_router.message(CandidateForm.email_or_phone)
async def process_contact(message: Message, state: FSMContext) -> None:
    """Сохранить контакт, спросить опыт."""
    is_valid, result = validate_contact(message.text)
    if not is_valid:
        await message.answer(result)
        return
    await state.update_data(email_or_phone=result)
    await message.answer(f"📝 {QUESTIONS_COMMON[2]['text']}")
    await state.set_state(CandidateForm.experience_years)


@application_router.message(CandidateForm.experience_years)
async def process_experience(message: Message, state: FSMContext) -> None:
    """Сохранить опыт, перейти к вопросам по специальности."""
    is_valid, years = validate_experience(message.text)
    if not is_valid:
        await message.answer(
            "Не удалось распознать. Укажите опыт, например: "
            "«3 года», «6 месяцев», «1.5» или «нет опыта»:"
        )
        return
    await state.update_data(experience_years=years)
    await ask_specialty_question(message, state)


# ---------------------------------------------------------------------------
# Вопросы по специальности (динамический цикл)
# ---------------------------------------------------------------------------

def _position_title(data: dict) -> str:
    """Название вакансии из данных FSM."""
    position = next(
        (p for p in POSITIONS if p["id"] == data.get("position")), None
    )
    return position["title"] if position else "IT-специалист"


async def ask_specialty_question(message: Message, state: FSMContext) -> None:
    """Задать текущий вопрос по специальности или перейти к статусу."""
    data = await state.get_data()
    questions = data.get("specialty_questions", [])
    index = data.get("specialty_index", 0)

    if index >= len(questions):
        # Все вопросы по специальности пройдены → спрашиваем статус
        await message.answer("📝 Ваш текущий статус?", reply_markup=status_keyboard())
        await state.set_state(CandidateForm.status)
        return

    q = questions[index]
    text = q["text"]
    if AI_DIALOGUE_ENABLED:
        # Показываем «печатает...» пока LLM формулирует вопрос
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        text = await humanize_question(
            q["text"],
            _position_title(data),
            data.get("dialogue_history", []),
        )
    await message.answer(f"📝 {text}")
    await state.set_state(CandidateForm.specialty_q)


@application_router.message(CandidateForm.specialty_q)
async def process_specialty_answer(message: Message, state: FSMContext) -> None:
    """Сохранить ответ, при коротком ответе — задать уточняющий вопрос."""
    data = await state.get_data()
    questions = data.get("specialty_questions", [])
    index = data.get("specialty_index", 0)
    answers = data.get("specialty_answers", {})
    history = data.get("dialogue_history", [])
    answer = message.text.strip()

    if index >= len(questions):
        await state.update_data(specialty_index=index + 1)
        await ask_specialty_question(message, state)
        return

    key = questions[index]["key"]
    base_question = questions[index]["text"]

    # Это ответ на уточняющий вопрос — дописываем к основному ответу
    if data.get("awaiting_followup"):
        answers[key] = f"{answers.get(key, '')} (уточнение: {answer})"
        history.append((data.get("pending_followup_q", "уточнение"), answer))
        await state.update_data(
            specialty_answers=answers,
            dialogue_history=history,
            awaiting_followup=False,
            pending_followup_q="",
            specialty_index=index + 1,
        )
        await ask_specialty_question(message, state)
        return

    # Обычный ответ
    answers[key] = answer
    history.append((base_question, answer))

    # Короткий ответ → один уточняющий вопрос (максимум один на вопрос)
    if AI_DIALOGUE_ENABLED and is_shallow(answer):
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        followup = await make_followup(base_question, answer)
        if followup:
            await state.update_data(
                specialty_answers=answers,
                dialogue_history=history,
                awaiting_followup=True,
                pending_followup_q=followup,
            )
            await message.answer(f"📝 {followup}")
            return

    await state.update_data(
        specialty_answers=answers,
        dialogue_history=history,
        specialty_index=index + 1,
    )
    await ask_specialty_question(message, state)


# ---------------------------------------------------------------------------
# Статус и дата выхода
# ---------------------------------------------------------------------------

@application_router.callback_query(
    CandidateForm.status, F.data.startswith("status_")
)
async def process_status(callback: CallbackQuery, state: FSMContext) -> None:
    """Сохранить статус, показать варианты даты старта."""
    status_value = callback.data.removeprefix("status_")
    await state.update_data(status=status_value)

    await callback.message.answer(
        f"📝 {QUESTION_START_DATE}",
        reply_markup=start_date_keyboard(),
    )
    await state.set_state(CandidateForm.start_date)
    await callback.answer()


@application_router.callback_query(
    CandidateForm.start_date, F.data.startswith("date_")
)
async def process_start_date(callback: CallbackQuery, state: FSMContext) -> None:
    """Сохранить выбранную дату старта и записать кандидата в БД."""
    idx = int(callback.data.removeprefix("date_"))
    start_date = (
        START_DATE_OPTIONS[idx] if 0 <= idx < len(START_DATE_OPTIONS)
        else START_DATE_OPTIONS[-1]
    )
    await state.update_data(start_date=start_date)
    data = await state.get_data()

    specialty_answers = data.get("specialty_answers", {})
    programming_languages = (
        ", ".join(specialty_answers.values()) if specialty_answers else ""
    )

    candidate = {
        "telegram_id": callback.from_user.id,
        "telegram_username": callback.from_user.username or "",
        "full_name": data["full_name"],
        "email_or_phone": data["email_or_phone"],
        "experience_years": data["experience_years"],
        "programming_languages": programming_languages,
        "specialty_answers": json.dumps(specialty_answers, ensure_ascii=False),
        "status": data["status"],
        "start_date": start_date,
        "position": data.get("position", "backend"),
    }

    try:
        candidate_id = save_candidate(candidate)
        if AI_ENABLED:
            # Уведомление менеджеру уйдёт после скоринга — вместе с оценкой
            asyncio.create_task(run_ai_scoring(callback.bot, candidate_id, candidate))
        else:
            asyncio.create_task(notify_manager(callback.bot, candidate_id, candidate))
        await callback.message.answer(
            "✅ *Спасибо! Ваша анкета принята.*\n\n"
            f"Номер анкеты: `{candidate_id}`\n"
            f"Команда *{COMPANY_NAME}* свяжется с вами в ближайшее время.\n\n"
            "Чтобы обновить анкету — нажмите кнопку ниже.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_keyboard(),
        )
        logger.info(
            "Анкета сохранена: id=%s, tg_id=%s, name=%s, position=%s",
            candidate_id, callback.from_user.id, data["full_name"],
            data.get("position"),
        )
    except Exception:
        logger.exception("Ошибка сохранения анкеты")
        await callback.message.answer(
            "❌ Произошла ошибка при сохранении. Попробуйте позже или напишите /start"
        )

    await state.clear()
