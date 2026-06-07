"""
Phase 4 backend regression — Store-type Questionnaire Coverage + Customer/Order Sync.

Tests:
 A1 — 4 webstore templates exposed by GET /api/questionnaires/templates
 A2 — Template dispatched correctly by store_type (event, fundraiser, business, creator)
 A3 — Submitting a Business questionnaire via /public/{id}/submit persists and shows up
       under /api/questionnaires/{id}/responses
 B1 — Owner email upserts into /api/customers tagged 'webstore_owner'
 B2 — Same owner_email across two stores -> single customer row
 B3 — Phone-only fallback dedupe across two stores
 B4 — POST /api/webstore-owners/{id}/invite/quick still upserts customer with tag
       (even if SendGrid fails)
 C1 — GET /api/orders?source=webstore and ?webstore_id=<id> filter hooks
 C2 — GET /api/orders (no filter) returns full list (regression)
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://ops-command-center-77.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"

TS = str(int(time.time()))


@pytest.fixture(scope="module")
def token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"Auth failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


def _create_store(client, name, store_type, owner_email=None, owner_phone=None):
    body = {
        "name": name,
        "store_type": store_type,
        "owner_name": f"Owner {name}",
    }
    if owner_email is not None:
        body["owner_email"] = owner_email
    if owner_phone is not None:
        body["owner_phone"] = owner_phone
    r = client.post(f"{BASE_URL}/api/webstores/v2", json=body, timeout=30)
    assert r.status_code in (200, 201), f"Webstore create failed: {r.status_code} {r.text}"
    return r.json()


# --------------------------------------------------------------------- A1
def test_A1_templates_exposed(client):
    r = client.get(f"{BASE_URL}/api/questionnaires/templates", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    # endpoint returns dict {key: template} or list — handle both
    if isinstance(data, dict):
        keys = set(data.keys())
    else:
        keys = {t.get("key") or t.get("id") or t.get("template_key") for t in data}
    for required in (
        "event_web_store_setup",
        "fundraiser_web_store_setup",
        "team_school_web_store_setup",
        "business_web_store_setup",
    ):
        assert required in keys, f"missing template: {required}; got {keys}"


# --------------------------------------------------------------------- A2
@pytest.mark.parametrize(
    "store_type,expected_label",
    [
        ("event", "Event Store Setup"),
        ("fundraiser", "Fundraiser Store Setup"),
        ("business", "Business Store Setup"),
        ("creator", "Team / School Store Setup"),
    ],
)
def test_A2_template_dispatch_by_store_type(client, store_type, expected_label):
    name = f"P4-A2-{store_type}-{TS}"
    ws = _create_store(
        client, name, store_type,
        owner_email=f"p4a2-{store_type}-{TS}@example.com",
    )
    wid = ws.get("id") or ws.get("_id")
    assert wid

    r = client.post(f"{BASE_URL}/api/webstores/v2/{wid}/questionnaire/send", json={}, timeout=30)
    assert r.status_code in (200, 201), f"send failed: {r.status_code} {r.text}"
    body = r.json()
    qid = body.get("questionnaire_id") or body.get("id")
    assert qid, f"no questionnaire_id in response: {body}"

    g = client.get(f"{BASE_URL}/api/questionnaires/{qid}", timeout=30)
    assert g.status_code == 200, g.text
    qdoc = g.json()
    qname = qdoc.get("name") or qdoc.get("title") or ""
    assert qname.startswith(expected_label), f"Expected '{expected_label} — ...' got '{qname}'"
    assert name in qname, f"Store name '{name}' not in questionnaire name '{qname}'"


# --------------------------------------------------------------------- A3
def test_A3_business_questionnaire_submission(client):
    name = f"P4-A3-business-{TS}"
    ws = _create_store(
        client, name, "business",
        owner_email=f"p4a3-{TS}@example.com",
    )
    wid = ws["id"]

    r = client.post(f"{BASE_URL}/api/webstores/v2/{wid}/questionnaire/send", json={}, timeout=30)
    assert r.status_code in (200, 201), r.text
    qid = r.json().get("questionnaire_id") or r.json().get("id")
    assert qid

    pub = requests.get(f"{BASE_URL}/api/questionnaires/public/{qid}", timeout=30)
    assert pub.status_code == 200, pub.text
    qdoc = pub.json()

    answers = {}
    sections = qdoc.get("sections") or []
    questions = []
    if sections:
        for s in sections:
            questions.extend(s.get("questions") or [])
    questions.extend(qdoc.get("questions") or [])

    for q in questions:
        if not q.get("required"):
            continue
        qid_inner = q.get("id") or q.get("key")
        qtype = (q.get("type") or "text").lower()
        label = (q.get("label") or q.get("question") or "").lower()
        opts = q.get("options") or []
        opt_vals = [o.get("value") if isinstance(o, dict) else o for o in opts]

        if qtype == "email":
            ans = "b@example.com"
        elif qtype == "phone":
            ans = "5551234567"
        elif qtype == "date":
            ans = "2026-12-01"
        elif qtype == "signature":
            ans = "data:image/png;base64,iVBORw0KGgo="
        elif qtype == "select":
            ans = opt_vals[0] if opt_vals else "yes"
        elif qtype == "checkbox":
            if "agree" in label or "consent" in label or "acknowledg" in label:
                ans = ["agree"]
            else:
                ans = [opt_vals[0]] if opt_vals else ["yes"]
        elif qtype == "number":
            ans = 1
        else:
            ans = "Test value"
        answers[qid_inner] = ans

    sub = requests.post(
        f"{BASE_URL}/api/questionnaires/public/{qid}/submit",
        json={"questionnaire_id": qid, "answers": answers, "webstore_id": wid},
        timeout=30,
    )
    assert sub.status_code == 200, f"submit failed: {sub.status_code} {sub.text}"
    sb = sub.json()
    rid = sb.get("response_id") or sb.get("id")
    assert rid, f"no response_id in {sb}"

    resp_list = client.get(f"{BASE_URL}/api/questionnaires/{qid}/responses", timeout=30)
    assert resp_list.status_code == 200, resp_list.text
    rl = resp_list.json()
    items = rl if isinstance(rl, list) else (rl.get("responses") or rl.get("items") or [])
    assert items, f"no responses for {qid}"
    assert any((it.get("webstore_id") == wid) for it in items), \
        f"response missing webstore_id={wid}: {[it.get('webstore_id') for it in items]}"


# --------------------------------------------------------------------- B1
def _find_customer(client, email=None, phone=None):
    r = client.get(f"{BASE_URL}/api/customers", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    items = data if isinstance(data, list) else (data.get("customers") or data.get("items") or [])
    matches = []
    norm_phone = "".join(ch for ch in (phone or "") if ch.isdigit())
    for c in items:
        if email and (c.get("email") or "").lower() == email.lower():
            matches.append(c)
        elif phone and "".join(ch for ch in (c.get("phone") or "") if ch.isdigit()) == norm_phone:
            matches.append(c)
    return matches


def test_B1_owner_customer_sync_on_create(client):
    email = f"p4b1-{TS}@example.com"
    name = f"P4-B1-{TS}"
    _create_store(client, name, "business", owner_email=email)
    matches = _find_customer(client, email=email)
    assert len(matches) >= 1, f"customer with {email} not found"
    tags = matches[0].get("tags") or []
    assert "webstore_owner" in tags, f"tags={tags}"


# --------------------------------------------------------------------- B2
def test_B2_email_dedupe(client):
    email = f"p4b2-{TS}@example.com"
    _create_store(client, f"P4-B2a-{TS}", "business", owner_email=email)
    _create_store(client, f"P4-B2b-{TS}", "business", owner_email=email)
    matches = _find_customer(client, email=email)
    assert len(matches) == 1, f"expected 1 customer, got {len(matches)}"
    tags = matches[0].get("tags") or []
    assert "webstore_owner" in tags


# --------------------------------------------------------------------- B3
def test_B3_phone_fallback_dedupe(client):
    # unique phone — append last 4 of timestamp
    suffix = TS[-4:]
    raw = f"555123{suffix}"
    fmt = f"(555) 123-{suffix}"
    _create_store(client, f"P4-B3a-{TS}", "business", owner_email=None, owner_phone=raw)
    _create_store(client, f"P4-B3b-{TS}", "business", owner_email=None, owner_phone=fmt)
    matches = _find_customer(client, phone=raw)
    assert len(matches) == 1, f"expected 1 customer for phone {raw}, got {len(matches)}"


# --------------------------------------------------------------------- B4
def test_B4_invite_path_tags_customer(client):
    lst = client.get(f"{BASE_URL}/api/webstores/v2", timeout=30)
    assert lst.status_code == 200, lst.text
    data = lst.json()
    stores = data if isinstance(data, list) else (data.get("webstores") or data.get("items") or [])
    assert stores, "no webstores available"
    sid = stores[0].get("id") or stores[0].get("_id")
    invite_email = f"p4inv-{TS}@example.com"
    r = client.post(
        f"{BASE_URL}/api/webstore-owners/{sid}/invite/quick",
        json={"email": invite_email, "name": "Invite P4"},
        timeout=60,
    )
    # SendGrid may fail — that's OK; side effect must still happen
    # Acceptable: 200/201 success or 500/502 if mail backend down
    assert r.status_code in (200, 201, 202, 400, 500, 502, 503), \
        f"unexpected status {r.status_code}: {r.text}"
    # small wait so DB upsert settles
    time.sleep(1)
    matches = _find_customer(client, email=invite_email)
    assert len(matches) >= 1, f"invite customer {invite_email} not created"
    tags = matches[0].get("tags") or []
    assert "webstore_owner" in tags, f"missing webstore_owner tag, got {tags}"


# --------------------------------------------------------------------- C1
def test_C1_orders_filter_source_webstore(client):
    r = client.get(f"{BASE_URL}/api/orders?source=webstore", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    items = data if isinstance(data, list) else (data.get("orders") or data.get("items") or [])
    # Each item must have either source=webstore or is_webstore_order=true
    if items:
        for o in items[:20]:
            assert (o.get("source") == "webstore") or o.get("is_webstore_order") is True, \
                f"Order {o.get('id') or o.get('order_number')} matched filter but has source={o.get('source')} is_webstore_order={o.get('is_webstore_order')}"


def test_C1b_orders_filter_webstore_id(client):
    # Use the known legacy webstore_id from problem statement if present
    known_wid = "22b7956b-32f3-4794-aa25-3206dd1965f3"
    r = client.get(f"{BASE_URL}/api/orders?webstore_id={known_wid}", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    items = data if isinstance(data, list) else (data.get("orders") or data.get("items") or [])
    for o in items[:20]:
        assert o.get("webstore_id") == known_wid, \
            f"Order {o.get('id')} has webstore_id={o.get('webstore_id')}, not {known_wid}"


# --------------------------------------------------------------------- C2
def test_C2_orders_default_no_filter(client):
    r = client.get(f"{BASE_URL}/api/orders", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    items = data if isinstance(data, list) else (data.get("orders") or data.get("items") or [])
    assert isinstance(items, list)
    # Default list should be at least as big as the webstore-filtered one
    rw = client.get(f"{BASE_URL}/api/orders?source=webstore", timeout=30).json()
    ws_items = rw if isinstance(rw, list) else (rw.get("orders") or rw.get("items") or [])
    assert len(items) >= len(ws_items), \
        f"default list ({len(items)}) shorter than webstore-only ({len(ws_items)})"
