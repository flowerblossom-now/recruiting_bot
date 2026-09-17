"""Тесты валидаторов пользовательского ввода."""

import pytest

from validators import (
    normalize_phone,
    validate_contact,
    validate_email,
    validate_experience,
    validate_name,
    validate_phone,
)


class TestNormalizePhone:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("+79991234567", "+79991234567"),
            ("89991234567", "+79991234567"),
            ("79991234567", "+79991234567"),
            ("9991234567", "+79991234567"),
            ("+7 (999) 123-45-67", "+79991234567"),
            ("8 999 123 45 67", "+79991234567"),
        ],
    )
    def test_accepts_common_formats(self, raw, expected):
        assert normalize_phone(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "123",
            "+7499123456",          # 10 цифр, но начинается не с 9
            "74991234567",          # городской, второй знак не 9
            "999123456789999",      # слишком длинный
            "не телефон",
        ],
    )
    def test_rejects_invalid(self, raw):
        assert normalize_phone(raw) is None

    def test_mobile_prefix_is_required(self):
        """Второй знак обязан быть 9 — городские номера не принимаются."""
        assert normalize_phone("84991234567") is None


class TestValidatePhone:
    def test_returns_normalized_on_success(self):
        ok, value = validate_phone("8 (999) 123-45-67")
        assert ok is True
        assert value == "+79991234567"

    def test_returns_hint_on_failure(self):
        ok, message = validate_phone("12345")
        assert ok is False
        assert "+79991234567" in message


class TestValidateEmail:
    @pytest.mark.parametrize(
        "value", ["a@b.co", "egor.chaly@example.com", "user+tag@mail.ru"]
    )
    def test_accepts_valid(self, value):
        assert validate_email(value) is True

    @pytest.mark.parametrize(
        "value", ["", "no-at-sign", "a@b", "a b@c.com", "@example.com", "a@@b.com"]
    )
    def test_rejects_invalid(self, value):
        assert validate_email(value) is False


class TestValidateContact:
    def test_phone_is_normalized(self):
        ok, value = validate_contact("  8 999 123 45 67 ")
        assert (ok, value) == (True, "+79991234567")

    def test_email_passes_through_trimmed(self):
        ok, value = validate_contact("  user@example.com  ")
        assert (ok, value) == (True, "user@example.com")

    def test_too_short_is_rejected(self):
        ok, message = validate_contact("ab")
        assert ok is False
        assert "email" in message.lower()

    def test_digits_but_not_a_phone_gets_phone_specific_hint(self):
        """Если в строке есть цифры — подсказка должна быть про формат номера."""
        ok, message = validate_contact("тел 12345")
        assert ok is False
        assert "+79991234567" in message

    def test_plain_garbage_gets_generic_hint(self):
        ok, message = validate_contact("абракадабра")
        assert ok is False
        assert "+79991234567" not in message


class TestValidateName:
    def test_trims_whitespace(self):
        assert validate_name("  Егор Чалый  ") == (True, "Егор Чалый")

    @pytest.mark.parametrize("value", ["", " ", "я"])
    def test_rejects_too_short(self, value):
        ok, _ = validate_name(value)
        assert ok is False


class TestValidateExperience:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("5", 5.0),
            ("0.5", 0.5),
            ("1,5", 1.5),
            ("3 года", 3.0),
            ("1 год", 1.0),
            ("5 лет", 5.0),
            ("2.5 г", 2.5),
            ("6 месяцев", 0.5),
            ("3 мес", 0.25),
            ("1 год 6 месяцев", 1.5),
            ("полгода", 0.5),
            ("пол года", 0.5),
            ("полтора года", 1.5),
            ("год", 1.0),
            ("нет опыта", 0),
            ("без опыта", 0),
        ],
    )
    def test_parses_known_forms(self, text, expected):
        ok, years = validate_experience(text)
        assert ok is True
        assert years == pytest.approx(expected, abs=0.01)

    def test_month_without_number(self):
        ok, years = validate_experience("месяц")
        assert ok is True
        assert years == pytest.approx(1 / 12, abs=0.01)

    @pytest.mark.parametrize("text", ["", "неизвестно", "давно"])
    def test_rejects_unparsable(self, text):
        ok, years = validate_experience(text)
        assert (ok, years) == (False, 0)

    def test_rejects_out_of_range(self):
        """Больше 50 лет опыта — явная ошибка ввода."""
        ok, _ = validate_experience("99 лет")
        assert ok is False

    def test_case_insensitive(self):
        assert validate_experience("ПОЛТОРА ГОДА")[1] == pytest.approx(1.5)
