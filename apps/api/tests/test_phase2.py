"""Phase 2-4 smoke tests. Require running postgres + seeded DB."""
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


def _launches(client, token):
    return client.get("/launches", headers=_auth(token)).json()


def test_integrations_available_includes_new_connectors(client, admin_token):
    r = client.get("/integrations/available", headers=_auth(admin_token))
    assert r.status_code == 200
    kinds = {row["kind"] for row in r.json()}
    assert {"clinicaltrials_gov", "dailymed", "who_gho", "cms_open_payments"}.issubset(kinds)


def test_scenarios_clone_and_list(client, admin_token):
    launches = _launches(client, admin_token)
    l001 = next(ln for ln in launches if ln["launch_code"] == "L-001")
    # Initial list filtered to this launch
    r0 = client.get(f"/scenarios?launch_id={l001['id']}", headers=_auth(admin_token))
    assert r0.status_code == 200
    initial_count = len(r0.json())

    r = client.post(
        "/scenarios",
        headers=_auth(admin_token),
        json={"name": "Aggressive Y1 ramp", "base_launch_id": l001["id"]},
    )
    assert r.status_code == 200
    sid = r.json()["id"]

    r2 = client.get(f"/scenarios?launch_id={l001['id']}", headers=_auth(admin_token))
    assert r2.status_code == 200
    assert len(r2.json()) == initial_count + 1
    assert any(s["id"] == sid for s in r2.json())


def test_irp_simulate(client, admin_token):
    launches = _launches(client, admin_token)
    l002 = next(ln for ln in launches if ln["launch_code"] == "L-002")
    r = client.post(
        "/irp/simulate",
        headers=_auth(admin_token),
        json={"source_launch_id": l002["id"], "new_net_price": 100000.0, "ccy": "EUR"},
    )
    assert r.status_code == 200
    impacts = r.json()
    # Seeded dependencies (L-004, L-005) + reference_pricing_link to L-005
    assert len(impacts) >= 1
    assert any("target_launch_code" in i for i in impacts)


def test_sensitivity_returns_three_scenarios(client, admin_token):
    launches = _launches(client, admin_token)
    l001 = next(ln for ln in launches if ln["launch_code"] == "L-001")
    r = client.get(f"/launches/{l001['id']}/sensitivity", headers=_auth(admin_token))
    assert r.status_code == 200
    body = r.json()
    assert len(body["scenarios"]) == 3
    labels = {s["scenario"] for s in body["scenarios"]}
    assert labels == {"low", "base", "high"}
    for s in body["scenarios"]:
        assert s["total_revenue"] >= 0
        assert len(s["years"]) == 3


def test_assistant_summarize_risks_offline(client, admin_token):
    launches = _launches(client, admin_token)
    l001 = next(ln for ln in launches if ln["launch_code"] == "L-001")
    r = client.post(
        "/assistant/summarize-risks",
        headers=_auth(admin_token),
        json={"launch_id": l001["id"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert "summary" in body
    assert len(body["summary"]) > 20


def test_stage_gate_approve_flow(client, admin_token):
    launches = _launches(client, admin_token)
    l001 = next(ln for ln in launches if ln["launch_code"] == "L-001")
    gates = client.get(f"/launches/{l001['id']}/gates", headers=_auth(admin_token)).json()
    assert len(gates) >= 2
    # Find one that is still pending
    pending = next((g for g in gates if g["status"] == "pending"), None)
    if pending is None:
        pytest.skip("All gates already decided")
    r = client.post(
        f"/gates/{pending['id']}/approve",
        headers=_auth(admin_token),
        json={"note": "All risks accepted at steering."},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


def test_variance_alerts_seeded(client, admin_token):
    launches = _launches(client, admin_token)
    l004 = next(ln for ln in launches if ln["launch_code"] == "L-004")
    r = client.get(f"/launches/{l004['id']}/variance-alerts", headers=_auth(admin_token))
    assert r.status_code == 200
    alerts = r.json()
    # 3 periods x 2 metrics = 6 alerts at 80% (-20%) which exceeds 10% threshold
    assert len(alerts) >= 3
    assert any(abs(a["variance_pct"]) >= 10.0 for a in alerts)


def test_prd_comments(client, admin_token):
    launches = _launches(client, admin_token)
    l001 = next(ln for ln in launches if ln["launch_code"] == "L-001")
    prd = client.get(f"/launches/{l001['id']}/prd", headers=_auth(admin_token)).json()
    r = client.get(f"/prds/{prd['id']}/comments", headers=_auth(admin_token))
    assert r.status_code == 200
    assert any(c["section"] == "executive_summary" for c in r.json())


def test_users_list_admin_only(client, admin_token):
    r = client.get("/users", headers=_auth(admin_token))
    assert r.status_code == 200
    emails = {u["email"] for u in r.json()}
    assert "admin@demo.example" in emails
