"""Smoke tests. Require a running postgres (docker compose up postgres) and a seeded DB."""
import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://launchiq:launchiq@localhost:5432/launchiq",
)

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def admin_token(client):
    r = client.post("/auth/login", json={"email": "admin@demo.example", "password": "demo123"})
    if r.status_code != 200:
        pytest.skip("DB not seeded; run `python -m app.seed`")
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_healthz(client):
    assert client.get("/healthz").status_code == 200


def test_me(client, admin_token):
    r = client.get("/auth/me", headers=_auth(admin_token))
    assert r.status_code == 200
    assert r.json()["email"] == "admin@demo.example"


def test_launches_list(client, admin_token):
    r = client.get("/launches", headers=_auth(admin_token))
    assert r.status_code == 200
    codes = {ln["launch_code"] for ln in r.json()}
    assert {"L-001", "L-002", "L-003", "L-004", "L-005"}.issubset(codes)


def test_portfolio_overview(client, admin_token):
    r = client.get("/portfolio/overview", headers=_auth(admin_token))
    assert r.status_code == 200
    body = r.json()
    assert body["total_launches"] >= 5
    assert body["peak_revenue"] > 0


def test_matrix(client, admin_token):
    r = client.get("/portfolio/matrix", headers=_auth(admin_token))
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 2
    assert all("cells" in row for row in rows)


def test_downstream_dependency_walk(client, admin_token):
    launches = client.get("/launches", headers=_auth(admin_token)).json()
    deu = next(ln for ln in launches if ln["launch_code"] == "L-002")
    r = client.get(f"/launches/{deu['id']}/downstream", headers=_auth(admin_token))
    assert r.status_code == 200
    rows = r.json()
    # Germany seeds 2 dependencies (L-004, L-005)
    assert len(rows) >= 2


def test_prd_versioning(client, admin_token):
    launches = client.get("/launches", headers=_auth(admin_token)).json()
    lid = launches[0]["id"]
    r = client.get(f"/launches/{lid}/prd", headers=_auth(admin_token))
    assert r.status_code == 200
    v0 = r.json()["current_version"]
    payload = r.json()["payload"]
    payload.setdefault("executive_summary", {})["launch_vision"] = "Updated vision text"
    r2 = client.put(
        f"/launches/{lid}/prd",
        headers=_auth(admin_token),
        json={"payload": payload, "change_reason": "Re-aligning to global brand book"},
    )
    assert r2.status_code == 200
    assert r2.json()["current_version"] == v0 + 1
