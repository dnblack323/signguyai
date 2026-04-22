"""Phase 5 Business Assistant personalization — backend smoke tests."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
EMAIL = "signguypa@gmail.com"
PASSWORD = "Billnel323"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# ---- Preferences (mode switcher) ----
def test_preferences_get_default(client):
    r = client.get(f"{BASE_URL}/api/ai/assistant/preferences", timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "mode" in body


@pytest.mark.parametrize("mode", ["quick", "guided", "power"])
def test_preferences_put_each_mode(client, mode):
    r = client.put(f"{BASE_URL}/api/ai/assistant/preferences", json={"mode": mode}, timeout=20)
    assert r.status_code == 200, r.text
    r2 = client.get(f"{BASE_URL}/api/ai/assistant/preferences", timeout=20)
    assert r2.json().get("mode") == mode


def test_preferences_invalid_mode(client):
    r = client.put(f"{BASE_URL}/api/ai/assistant/preferences", json={"mode": "zen"}, timeout=20)
    assert r.status_code == 400


# ---- Saved commands CRUD ----
def test_saved_commands_crud(client):
    # create
    r = client.post(f"{BASE_URL}/api/ai/assistant/saved-commands",
                    json={"label": "TEST_cmd", "command": "show overdue invoices", "pinned": True}, timeout=20)
    assert r.status_code == 200, r.text
    cmd = r.json()
    cid = cmd["id"]
    assert cmd["label"] == "TEST_cmd"
    assert cmd["command"] == "show overdue invoices"
    # list
    r = client.get(f"{BASE_URL}/api/ai/assistant/saved-commands", timeout=20)
    assert r.status_code == 200
    items = r.json().get("items", [])
    assert any(x["id"] == cid for x in items)
    # update
    r = client.put(f"{BASE_URL}/api/ai/assistant/saved-commands/{cid}",
                   json={"label": "TEST_cmd_renamed"}, timeout=20)
    assert r.status_code == 200
    # record run
    r = client.post(f"{BASE_URL}/api/ai/assistant/saved-commands/{cid}/record-run", timeout=20)
    assert r.status_code == 200
    # delete
    r = client.delete(f"{BASE_URL}/api/ai/assistant/saved-commands/{cid}", timeout=20)
    assert r.status_code == 200


def test_saved_commands_empty_rejected(client):
    r = client.post(f"{BASE_URL}/api/ai/assistant/saved-commands",
                    json={"command": "   "}, timeout=20)
    assert r.status_code == 400


# ---- Routines CRUD ----
def test_routines_crud(client):
    r = client.post(f"{BASE_URL}/api/ai/assistant/routines",
                    json={"name": "TEST_morning", "commands": ["show overdue invoices", "list upcoming orders"]},
                    timeout=20)
    assert r.status_code == 200, r.text
    rt = r.json()
    rid = rt["id"]
    assert rt["name"] == "TEST_morning"
    assert len(rt["commands"]) == 2
    # list
    r = client.get(f"{BASE_URL}/api/ai/assistant/routines", timeout=20)
    assert r.status_code == 200
    assert any(x["id"] == rid for x in r.json().get("items", []))
    # update
    r = client.put(f"{BASE_URL}/api/ai/assistant/routines/{rid}",
                   json={"name": "TEST_morning2"}, timeout=20)
    assert r.status_code == 200
    # record-run
    r = client.post(f"{BASE_URL}/api/ai/assistant/routines/{rid}/record-run", timeout=20)
    assert r.status_code == 200
    # delete
    r = client.delete(f"{BASE_URL}/api/ai/assistant/routines/{rid}", timeout=20)
    assert r.status_code == 200


def test_routines_validation(client):
    # empty commands
    r = client.post(f"{BASE_URL}/api/ai/assistant/routines",
                    json={"name": "TEST_x", "commands": []}, timeout=20)
    assert r.status_code == 400
    # 9 commands (over limit)
    r = client.post(f"{BASE_URL}/api/ai/assistant/routines",
                    json={"name": "TEST_x", "commands": [f"cmd {i}" for i in range(9)]}, timeout=20)
    assert r.status_code == 400


# ---- Smart defaults ----
def test_smart_default_last_order_customer(client):
    r = client.get(f"{BASE_URL}/api/ai/assistant/smart-defaults/last-order-customer", timeout=20)
    assert r.status_code == 200
    body = r.json()
    assert "customer_name" in body
    assert "customer_id" in body
    assert "last_used_at" in body


# ---- Next-step suggestions ----
def test_next_steps_create_order(client):
    r = client.post(f"{BASE_URL}/api/ai/assistant/next-step-suggestions",
                    json={"action_type": "create_order", "result": {"order_id": "abc-123"}}, timeout=20)
    assert r.status_code == 200
    suggs = r.json().get("suggestions", [])
    assert len(suggs) >= 1
    labels = [s["label"] for s in suggs]
    assert any("invoice" in l.lower() for l in labels)
    # dynamic route
    view = next((s for s in suggs if "View" in s["label"]), None)
    if view:
        assert "abc-123" in view["target"]


def test_next_steps_unknown_action(client):
    r = client.post(f"{BASE_URL}/api/ai/assistant/next-step-suggestions",
                    json={"action_type": "totally_unknown", "result": {}}, timeout=20)
    assert r.status_code == 200
    assert r.json().get("suggestions") == []


# ---- Bulk overdue reminders ----
def test_bulk_overdue_preview(client):
    r = client.get(f"{BASE_URL}/api/ai/assistant/bulk/overdue-reminders/preview", timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "count" in body
    assert "sample" in body
    assert isinstance(body["sample"], list)


def test_bulk_overdue_send_empty_is_graceful(client):
    # Send with explicit empty list  -> should return sent=0 message
    r = client.post(f"{BASE_URL}/api/ai/assistant/bulk/overdue-reminders/send",
                    json={"invoice_ids": ["__nonexistent__"], "note": "TEST note"}, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "sent" in body


# ---- Auth required ----
def test_preferences_requires_auth():
    r = requests.get(f"{BASE_URL}/api/ai/assistant/preferences", timeout=20)
    assert r.status_code in (401, 403)
