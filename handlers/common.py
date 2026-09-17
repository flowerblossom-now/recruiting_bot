"""Команды бота и ответ на сообщения вне анкеты.

Роутеры разделены намеренно: `commands_router` подключается до анкеты,
чтобы /start, /cancel и /help работали в любом состоянии, а `fallback_router` —
после неё, как перехватчик всего остального.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import COMPANY_NAME, COMPANY_WELCOME
from database import get_candidate_by_telegram_id
from keyboards import BTN_APPLY, main_keyboard, positions_keyboard
from states import CandidateForm

commands_router = Router(name="commands")
fallback_router = Router(name="fallback")


@commands_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Приветствие, показ reply-клавиатуры."""
    await state.clear()

    existing = get_candidate_by_telegram_id(message.from_user.id)
    extra = ""
    if existing:
        extra = "\n⚠️ Вы уже заполняли анкету. Новая отправка обновит данные.\n"

    await message.answer(
        COMPANY_WELCOME + extra,
        reply_markup=main_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )


async def show_positions(message: Message, state: FSMContext) -> None:
    """Показать список вакансий с inline-кнопками."""
    await message.answer("Выберите вакансию:", reply_markup=positions_keyboard())
    await state.set_state(CandidateForm.choosing_position)


@commands_router.message(F.text == BTN_APPLY)
async def btn_apply(message: Message, state: FSMContext) -> None:
    """Обработка нажатия кнопки «Оставить заявку»."""
    await state.clear()
    await show_positions(message, state)


@commands_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Отменить заполнение анкеты."""
    if await state.get_state() is None:
        await message.answer("Нечего отменять.", reply_markup=main_keyboard())
        return
    await state.clear()
    await message.answer("❌ Заполнение отменено.", reply_markup=main_keyboard())


@commands_router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Показать список команд."""
    await message.answer(
        "📋 *Команды:*\n\n"
        "/start — начать заполнение анкеты\n"
        "/cancel — отменить заполнение\n"
        "/help — эта справка",
        parse_mode=ParseMode.MARKDOWN,
    )


@fallback_router.message(StateFilter(None))
async def fallback(message: Message) -> None:
    """Ответ на сообщения вне анкеты."""
    await message.answer(
        f"Я — рекрутинговый бот *{COMPANY_NAME}*.\n"
        "Нажмите кнопку ниже, чтобы откликнуться на вакансию.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(),
    )
