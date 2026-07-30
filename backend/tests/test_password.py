"""Unit tests for the password service and password policy validation."""
import pytest

from app.services.password_service import password_service


class TestPasswordHashing:
    def test_hash_produces_different_value_than_plaintext(self) -> None:
        hashed = password_service.hash("StrongP@ss1")
        assert hashed != "StrongP@ss1"
        assert hashed.startswith("$2b$")

    def test_verify_succeeds_for_correct_password(self) -> None:
        hashed = password_service.hash("StrongP@ss1")
        assert password_service.verify("StrongP@ss1", hashed) is True

    def test_verify_fails_for_incorrect_password(self) -> None:
        hashed = password_service.hash("StrongP@ss1")
        assert password_service.verify("WrongPassword1!", hashed) is False

    def test_hashing_is_salted(self) -> None:
        first = password_service.hash("StrongP@ss1")
        second = password_service.hash("StrongP@ss1")
        assert first != second


class TestPasswordPolicy:
    def test_accepts_strong_password(self) -> None:
        password_service.enforce_policy("StrongP@ss1")

    @pytest.mark.parametrize(
        "weak_password",
        [
            "short1!",  # too short
            "alllowercase1!",  # no uppercase
            "ALLUPPERCASE1!",  # no lowercase
            "NoDigitsHere!",  # no digit
            "NoSpecialChar1",  # no special character
        ],
    )
    def test_rejects_weak_passwords(self, weak_password: str) -> None:
        with pytest.raises(ValueError):
            password_service.enforce_policy(weak_password)
