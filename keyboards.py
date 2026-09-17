"""Клавиатуры бота."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import POSITIONS, START_DATE_OPTIONS, STATUS_OPTIONS

BTN_APPLY = "📋 Оставить заявку"


def main_keyboard() -> ReplyKeyboardMarkup:
    """Постоянная клавиатура с кнопкой подачи заявки."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_APPLY)]],
        resize_keyboard=True,
        input_field_placeholder="Нажмите кнопку ниже или введите /start",
    )


def positions_keyboard() -> InlineKeyboardMarkup:
    """Список вакансий: одна кнопка на вакансию."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{pos['emoji']}  {pos['title']} — {pos['description']}",
                callback_data=f"pos_{pos['id']}",
            )]
            for pos in POSITIONS
        ]
    )


def status_keyboard() -> InlineKeyboardMarkup:
    """Варианты текущего статуса кандидата."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"status_{opt}")]
            for opt in STATUS_OPTIONS
        ]
    )


def start_date_keyboard() -> InlineKeyboardMarkup:
    """Варианты готовности выйти на работу."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"date_{i}")]
            for i, opt in enumerate(START_DATE_OPTIONS)
        ]
    )
