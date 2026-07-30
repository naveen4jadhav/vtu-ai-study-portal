"""
Integration tests for the authentication API.

Requires a reachable PostgreSQL instance matching the configured
`DATABASE_URL` (see `tests/conftest.py`).
"""
from fastapi.testclient import TestClient

AUTH_PREFIX = "/api/v1/auth"


def _valid_registration_payload(**overrides) -> dict:
    payload = {
        "full_name": "Naveen Kumar",
        "email": "naveen.kumar@example.com",
        "phone": "+919876543210",
        "username": "naveen_k",
        "password": "StrongP@ss1",
        "password_confirm": "StrongP@ss1",
    }
    payload.update(overrides)
    return payload


class TestRegister:
    def test_register_creates_user_with_student_role(self, client: TestClient) -> None:
        response = client.post(f"{AUTH_PREFIX}/register", json=_valid_registration_payload())
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "naveen.kumar@example.com"
        assert body["username"] == "naveen_k"
        assert body["role"] == "STUDENT"
        assert "hashed_password" not in body

    def test_register_rejects_privilege_escalation_attempt(self, client: TestClient) -> None:
        payload = _valid_registration_payload(role="SUPER_ADMIN")
        response = client.post(f"{AUTH_PREFIX}/register", json=payload)
        assert response.status_code == 201
        assert response.json()["role"] == "STUDENT"

    def test_register_rejects_duplicate_email(self, client: TestClient) -> None:
        client.post(f"{AUTH_PREFIX}/register", json=_valid_registration_payload())
        response = client.post(
            f"{AUTH_PREFIX}/register",
            json=_valid_registration_payload(username="different_user"),
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "duplicate_email"

    def test_register_rejects_duplicate_username(self, client: TestClient) -> None:
        client.post(f"{AUTH_PREFIX}/register", json=_valid_registration_payload())
        response = client.post(
            f"{AUTH_PREFIX}/register",
            json=_valid_registration_payload(email="another@example.com"),
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "duplicate_username"

    def test_register_rejects_weak_password(self, client: TestClient) -> None:
        payload = _valid_registration_payload(password="weak", password_confirm="weak")
        response = client.post(f"{AUTH_PREFIX}/register", json=payload)
        assert response.status_code == 422

    def test_register_rejects_mismatched_passwords(self, client: TestClient) -> None:
        payload = _valid_registration_payload(password_confirm="Different1@Pass")
        response = client.post(f"{AUTH_PREFIX}/register", json=payload)
        assert response.status_code == 422


class TestLogin:
    def _register(self, client: TestClient) -> None:
        client.post(f"{AUTH_PREFIX}/register", json=_valid_registration_payload())

    def test_login_succeeds_with_username(self, client: TestClient) -> None:
        self._register(client)
        response = client.post(
            f"{AUTH_PREFIX}/login", json={"login": "naveen_k", "password": "StrongP@ss1"}
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_succeeds_with_email(self, client: TestClient) -> None:
        self._register(client)
        response = client.post(
            f"{AUTH_PREFIX}/login",
            json={"login": "naveen.kumar@example.com", "password": "StrongP@ss1"},
        )
        assert response.status_code == 200

    def test_login_fails_with_wrong_password(self, client: TestClient) -> None:
        self._register(client)
        response = client.post(
            f"{AUTH_PREFIX}/login", json={"login": "naveen_k", "password": "WrongPass1!"}
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "invalid_credentials"

    def test_login_fails_for_unknown_user(self, client: TestClient) -> None:
        response = client.post(
            f"{AUTH_PREFIX}/login", json={"login": "ghost", "password": "StrongP@ss1"}
        )
        assert response.status_code == 401


class TestMe:
    def _register_and_login(self, client: TestClient) -> str:
        client.post(f"{AUTH_PREFIX}/register", json=_valid_registration_payload())
        response = client.post(
            f"{AUTH_PREFIX}/login", json={"login": "naveen_k", "password": "StrongP@ss1"}
        )
        return response.json()["access_token"]

    def test_me_returns_current_user(self, client: TestClient) -> None:
        access_token = self._register_and_login(client)
        response = client.get(
            f"{AUTH_PREFIX}/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "naveen_k"

    def test_me_rejects_missing_token(self, client: TestClient) -> None:
        response = client.get(f"{AUTH_PREFIX}/me")
        assert response.status_code in (401, 403)

    def test_me_rejects_invalid_token(self, client: TestClient) -> None:
        response = client.get(
            f"{AUTH_PREFIX}/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == 401


class TestRefresh:
    def _register_and_login(self, client: TestClient) -> dict:
        client.post(f"{AUTH_PREFIX}/register", json=_valid_registration_payload())
        response = client.post(
            f"{AUTH_PREFIX}/login", json={"login": "naveen_k", "password": "StrongP@ss1"}
        )
        return response.json()

    def test_refresh_issues_new_token_pair(self, client: TestClient) -> None:
        tokens = self._register_and_login(client)
        response = client.post(
            f"{AUTH_PREFIX}/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert response.status_code == 200
        new_tokens = response.json()
        assert new_tokens["access_token"] != tokens["access_token"]
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

    def test_refresh_rejects_reused_refresh_token(self, client: TestClient) -> None:
        tokens = self._register_and_login(client)
        client.post(f"{AUTH_PREFIX}/refresh", json={"refresh_token": tokens["refresh_token"]})
        second_attempt = client.post(
            f"{AUTH_PREFIX}/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert second_attempt.status_code == 401

    def test_refresh_rejects_access_token(self, client: TestClient) -> None:
        tokens = self._register_and_login(client)
        response = client.post(
            f"{AUTH_PREFIX}/refresh", json={"refresh_token": tokens["access_token"]}
        )
        assert response.status_code == 401


class TestLogout:
    def _register_and_login(self, client: TestClient) -> dict:
        client.post(f"{AUTH_PREFIX}/register", json=_valid_registration_payload())
        response = client.post(
            f"{AUTH_PREFIX}/login", json={"login": "naveen_k", "password": "StrongP@ss1"}
        )
        return response.json()

    def test_logout_revokes_access_token(self, client: TestClient) -> None:
        tokens = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        logout_response = client.post(f"{AUTH_PREFIX}/logout", headers=headers)
        assert logout_response.status_code == 200

        me_response = client.get(f"{AUTH_PREFIX}/me", headers=headers)
        assert me_response.status_code == 401

    def test_logout_revokes_supplied_refresh_token(self, client: TestClient) -> None:
        tokens = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        client.post(
            f"{AUTH_PREFIX}/logout",
            headers=headers,
            json={"refresh_token": tokens["refresh_token"]},
        )

        refresh_response = client.post(
            f"{AUTH_PREFIX}/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == 401


class TestChangePassword:
    def _register_and_login(self, client: TestClient) -> dict:
        client.post(f"{AUTH_PREFIX}/register", json=_valid_registration_payload())
        response = client.post(
            f"{AUTH_PREFIX}/login", json={"login": "naveen_k", "password": "StrongP@ss1"}
        )
        return response.json()

    def test_change_password_succeeds(self, client: TestClient) -> None:
        tokens = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = client.post(
            f"{AUTH_PREFIX}/change-password",
            headers=headers,
            json={
                "current_password": "StrongP@ss1",
                "new_password": "EvenStronger2#",
                "new_password_confirm": "EvenStronger2#",
            },
        )
        assert response.status_code == 200

        login_response = client.post(
            f"{AUTH_PREFIX}/login",
            json={"login": "naveen_k", "password": "EvenStronger2#"},
        )
        assert login_response.status_code == 200

    def test_change_password_rejects_wrong_current_password(
        self, client: TestClient
    ) -> None:
        tokens = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = client.post(
            f"{AUTH_PREFIX}/change-password",
            headers=headers,
            json={
                "current_password": "WrongCurrent1!",
                "new_password": "EvenStronger2#",
                "new_password_confirm": "EvenStronger2#",
            },
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_password"

    def test_change_password_rejects_mismatched_confirmation(
        self, client: TestClient
    ) -> None:
        tokens = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        response = client.post(
            f"{AUTH_PREFIX}/change-password",
            headers=headers,
            json={
                "current_password": "StrongP@ss1",
                "new_password": "EvenStronger2#",
                "new_password_confirm": "Different3$",
            },
        )
        assert response.status_code == 422
