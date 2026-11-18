"""Pytest fixtures: isolated SQLite DB, TestClient, role-authenticated clients."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Environment must be configured BEFORE app imports (settings are cached).
_TMP = tempfile.mkdtemp(prefix="hp_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test_healthpulse.db"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DOCUMENT_STORAGE_DIR"] = f"{_TMP}/documents"
os.environ["REDIS_URL"] = ""

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.user import User  # noqa: E402

TEST_PASSWORD = "TestPass!2026"
ROLE_EMAILS = {
    "CITIZEN": "citizen@test.demo",
    "PATIENT": "patient@test.demo",
    "CLINICIAN": "clinician@test.demo",
    "MUNICIPAL_ADMIN": "municipal@test.demo",
    "HEALTH_ADMIN": "health@test.demo",
    "SUPER_ADMIN": "super@test.demo",
}


@pytest.fixture(scope="session")
def app_client():
    """Fresh app + DB for the whole test session."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    for role, email in ROLE_EMAILS.items():
        if not db.query(User).filter(User.email == email).first():
            db.add(User(email=email, full_name=f"Test {role}",
                        role=role, password_hash=hash_password(TEST_PASSWORD)))
    db.commit()
    db.close()
    with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
        yield client


@pytest.fixture(scope="session")
def tokens(app_client) -> dict[str, str]:
    out = {}
    for role, email in ROLE_EMAILS.items():
        r = app_client.post("/api/v1/auth/login", json={"email": email,
                                                        "password": TEST_PASSWORD})
        assert r.status_code == 200, f"login failed for {role}: {r.text}"
        out[role] = r.json()["access_token"]
    return out


def auth(role: str, tokens: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens[role]}"}


@pytest.fixture(scope="session")
def citizen_headers(tokens):
    return auth("CITIZEN", tokens)


@pytest.fixture(scope="session")
def patient_headers(tokens):
    return auth("PATIENT", tokens)


@pytest.fixture(scope="session")
def clinician_headers(tokens):
    return auth("CLINICIAN", tokens)


@pytest.fixture(scope="session")
def municipal_headers(tokens):
    return auth("MUNICIPAL_ADMIN", tokens)


@pytest.fixture(scope="session")
def health_headers(tokens):
    return auth("HEALTH_ADMIN", tokens)


@pytest.fixture(scope="session")
def super_headers(tokens):
    return auth("SUPER_ADMIN", tokens)
