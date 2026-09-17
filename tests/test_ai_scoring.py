"""Тесты AI-скоринга: разбор ответа модели и устойчивость к отказу провайдера."""

import json

import pytest

import ai_scoring
from ai_scoring import _build_prompt, _parse_response, score_candidate


class TestParseResponse:
    def test_parses_clean_json(self):
        assert _parse_response('{"score": 7, "summary": "Крепкий middle."}') == (
            7,
            "Крепкий middle.",
        )

    def test_extracts_json_from_surrounding_prose(self):
        """Модели любят добавлять пояснения вокруг JSON — они не должны мешать."""
        raw = 'Вот моя оценка:\n{"score": 4, "summary": "Опыт по касательной."}\nГотово.'
        assert _parse_response(raw) == (4, "Опыт по касательной.")

    def test_extracts_json_from_markdown_fence(self):
        raw = '```json\n{"score": 9, "summary": "Брать в приоритет."}\n```'
        assert _parse_response(raw) == (9, "Брать в приоритет.")

    def test_accepts_multiline_summary(self):
        raw = '{"score": 5, "summary": "Первая строка.\\nВторая строка."}'
        score, summary = _parse_response(raw)
        assert score == 5
        assert "Вторая строка." in summary

    def test_strips_summary_whitespace(self):
        assert _parse_response('{"score": 6, "summary": "  Средне.  "}')[1] == "Средне."

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "Модель отказалась отвечать",
            "{не json}",
            '{"score": 11, "summary": "вне шкалы"}',
            '{"score": 0, "summary": "вне шкалы"}',
            '{"score": 5}',
            '{"summary": "нет балла"}',
            '{"score": 5, "summary": ""}',
            '{"score": "высокий", "summary": "балл не число"}',
            '{"score": null, "summary": "null"}',
        ],
    )
    def test_rejects_malformed(self, raw):
        assert _parse_response(raw) is None

    def test_accepts_score_at_both_bounds(self):
        assert _parse_response('{"score": 1, "summary": "низ шкалы"}')[0] == 1
        assert _parse_response('{"score": 10, "summary": "верх шкалы"}')[0] == 10


class TestBuildPrompt:
    def test_includes_experience_and_status(self):
        prompt = _build_prompt(
            {
                "position": "backend",
                "experience_years": 3,
                "specialty_answers": {"Стек": "Python, asyncio"},
                "status": "в поиске",
                "start_date": "через 2 недели",
            }
        )
        assert "3" in prompt
        assert "Python, asyncio" in prompt
        assert "в поиске" in prompt
        assert "через 2 недели" in prompt

    def test_accepts_answers_as_json_string(self):
        """Из БД ответы приходят строкой JSON, а не словарём."""
        prompt = _build_prompt(
            {"specialty_answers": json.dumps({"Опыт с Docker": "да, в проде"})}
        )
        assert "Опыт с Docker" in prompt
        assert "да, в проде" in prompt

    def test_survives_malformed_answers_string(self):
        """Битая строка не должна ронять сборку промпта."""
        prompt = _build_prompt({"specialty_answers": "не json вовсе"})
        assert "не json вовсе" in prompt

    def test_survives_empty_candidate(self):
        assert _build_prompt({})


@pytest.mark.asyncio
class TestScoreCandidateResilience:
    async def test_returns_none_when_provider_unreachable(self, monkeypatch):
        """Отказ AI-провайдера возвращает None, а не исключение наверх."""

        def explode(*args, **kwargs):
            raise OSError("provider is down")

        monkeypatch.setattr(ai_scoring.aiohttp, "ClientSession", explode)
        assert await score_candidate({"position": "backend"}) is None

    async def test_returns_none_on_unparsable_model_output(self, monkeypatch):
        """Модель ответила мусором — считаем это отсутствием оценки."""

        class FakeResponse:
            status = 200

            async def json(self):
                return {"choices": [{"message": {"content": "я не понял вопрос"}}]}

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

        class FakeSession:
            def __init__(self, *args, **kwargs):
                pass

            def post(self, *args, **kwargs):
                return FakeResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

        monkeypatch.setattr(ai_scoring.aiohttp, "ClientSession", FakeSession)
        assert await score_candidate({"position": "backend"}) is None
