"""Состояния FSM анкеты кандидата."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class CandidateForm(StatesGroup):
    """Состояния анкеты кандидата."""

    choosing_position = State()
    full_name = State()
    email_or_phone = State()
    experience_years = State()
    specialty_q = State()   # динамические вопросы по специальности
    status = State()
    start_date = State()
