"""Конфигурация рекрутингового бота и HR-панели.

Секреты читаются из переменных окружения (файл .env).
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    """Загрузить переменные из .env файла (без внешних зависимостей)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / ".env")

# Путь к БД можно переопределить (в Docker БД лежит на volume)
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "candidates.db")))

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

HR_PANEL_HOST = os.getenv("HR_PANEL_HOST", "0.0.0.0")
HR_PANEL_PORT = int(os.getenv("HR_PANEL_PORT", "5050"))
HR_PANEL_SECRET_KEY = os.getenv("HR_PANEL_SECRET_KEY", "change-me-in-production")
HR_PANEL_PASSWORD = os.getenv("HR_PANEL_PASSWORD", "admin")

MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID", "0"))

# --- AI-скоринг кандидатов ---
# Любой OpenAI-совместимый API: Ollama (локально), OpenRouter, GigaChat-адаптер и т.д.
AI_ENABLED = os.getenv("AI_ENABLED", "1") == "1"
# AI-формулировка вопросов в диалоге. Использует отдельную быструю модель
# без reasoning-режима (ответ за ~1 сек). Скоринг работает на основной модели.
AI_DIALOGUE_ENABLED = os.getenv("AI_DIALOGUE_ENABLED", "0") == "1"
AI_DIALOGUE_MODEL = os.getenv("AI_DIALOGUE_MODEL", "qwen2.5:3b-instruct")
AI_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")
AI_MODEL = os.getenv("AI_MODEL", "qwen3-vl:8b")
AI_API_KEY = os.getenv("AI_API_KEY", "ollama")  # для Ollama значение не важно
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "120"))

LOG_FILE = BASE_DIR / "bot.log"

# Название компании: используется в приветствии, текстах бота и AI-промптах —
# при клонировании бота под клиента меняется в одном месте
COMPANY_NAME = os.getenv("COMPANY_NAME", "Mindl")

COMPANY_WELCOME = (
    "╔══════════════════════╗\n"
    f"║    {'  '.join(COMPANY_NAME.upper()):^18}║\n"
    "╚══════════════════════╝\n\n"
    f"Привет! Я — рекрутинговый бот компании *{COMPANY_NAME}*.\n\n"
    f"{COMPANY_NAME} — IT-компания, которая создаёт умные продукты "
    "для бизнеса: от автоматизации процессов до AI-решений.\n\n"
    "Мы постоянно растём и ищем талантливых людей в команду 🚀\n\n"
    "Выберите вакансию, которая вас интересует:"
)

POSITIONS = [
    {
        "id": "devops",
        "title": "DevOps Engineer",
        "description": "Инфраструктура, CI/CD, облака",
        "emoji": "⚙️",
    },
    {
        "id": "frontend",
        "title": "Frontend Developer",
        "description": "React, TypeScript, UI/UX",
        "emoji": "🎨",
    },
    {
        "id": "backend",
        "title": "Backend Developer",
        "description": "Python/Go, API, базы данных",
        "emoji": "🔧",
    },
]

# Общие вопросы (для всех специальностей)
QUESTIONS_COMMON = [
    {"key": "full_name",       "text": "Как вас зовут? (ФИО)"},
    {"key": "email_or_phone",  "text": "Ваш email или телефон для связи?"},
    {"key": "experience_years","text": "Какой у вас опыт в разработке? (например: 3 года, 6 месяцев, 1.5)"},
]

# Вопросы под каждую специальность
QUESTIONS_BY_POSITION = {
    "devops": [
        {"key": "tools",    "text": "Какие инструменты используете? (Docker, K8s, Ansible, Terraform...)"},
        {"key": "clouds",   "text": "С какими облачными платформами работали? (AWS, GCP, Azure, Yandex Cloud)"},
        {"key": "ci_cd",    "text": "Какие CI/CD системы знаете? (GitLab CI, GitHub Actions, Jenkins...)"},
    ],
    "frontend": [
        {"key": "frameworks",   "text": "Какие фреймворки используете? (React, Vue, Angular...)"},
        {"key": "typescript",   "text": "Знаете TypeScript? Опишите уровень владения."},
        {"key": "tools_fe",     "text": "Какие инструменты используете? (Webpack, Vite, Figma, Storybook...)"},
    ],
    "backend": [
        {"key": "languages",    "text": "Основные языки программирования? (Python, Go, Java...)"},
        {"key": "databases",    "text": "С какими базами данных работали? (PostgreSQL, Redis, MongoDB...)"},
        {"key": "arch",         "text": "Есть опыт с микросервисами / очередями? (Kafka, RabbitMQ, gRPC)"},
    ],
}

STATUS_OPTIONS = ["Работаю", "Ищу работу", "Фрилансер"]

QUESTION_START_DATE = "Укажите предполагаемую дату начала работы:"

START_DATE_OPTIONS = [
    "Готов приступить немедленно",
    "В течение 1–2 рабочих дней",
    "В течение одной рабочей недели",
    "Через две недели",
    "Через месяц",
    "Готов обсудить сроки с менеджером",
]
