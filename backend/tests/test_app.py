
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Allow tests to import backend/app.py
BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, BACKEND_DIR)

# app.py calls initialize_database() during import.
# Mock that call so tests do not require a running MySQL server.
with patch("mysql.connector.connect"), patch(
    "mysql.connector.connect"
):
    import app as backend_app

app = backend_app.app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_status_success(client):
    with patch.object(
        backend_app, "get_active_cursor"
    ) as mock_db:
        conn = MagicMock()
        cursor = MagicMock()
        mock_db.return_value = (conn, cursor)

        response = client.get("/api/status")

        assert response.status_code == 200
        assert response.get_json()["status"] == "success"
        cursor.close.assert_called_once()
        conn.close.assert_called_once()


def test_status_database_error(client):
    with patch.object(
        backend_app,
        "get_active_cursor",
        side_effect=backend_app.mysql.connector.Error(
            "Database unavailable"
        ),
    ):
        response = client.get("/api/status")

        assert response.status_code == 500
        assert response.get_json()["status"] == "error"


def test_signup_missing_data(client):
    response = client.post("/api/signup", json={})

    assert response.status_code == 400
    assert response.get_json()["message"] == (
        "No signup data received."
    )


def test_login_missing_credentials(client):
    response = client.post("/api/login", json={})

    assert response.status_code == 400
    assert response.get_json()["message"] == (
        "No login data received."
    )


def test_appointment_missing_data(client):
    response = client.post("/api/book-appointment", json={})

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


def test_login_invalid_credentials(client):
    with patch.object(
        backend_app, "authenticate_user", return_value=None
    ):
        response = client.post(
            "/api/login",
            json={
                "email": "test@example.com",
                "password": "wrong-password",
            },
        )

    assert response.status_code == 401
    assert response.get_json()["message"] == (
        "Invalid email or password."
    )
