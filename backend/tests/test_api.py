def register_user(client, email="test@example.com", password="password123"):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def test_health_and_metrics(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "running"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "wefindbest_http_requests_total" in metrics.text


def test_register_login_and_api_key_chat(client):
    auth = register_user(client)
    assert auth["api_key"].startswith("wfb_")
    assert auth["refresh_token"]
    assert auth["email_verification_token"]

    login = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    assert login.json()["api_key"] == auth["api_key"]

    missing_key = client.post("/v1/chat", json={"input": "hello"})
    assert missing_key.status_code == 401

    chat = client.post(
        "/v1/chat",
        headers={"x-api-key": auth["api_key"]},
        json={"input": "hello", "model": "mock"},
    )
    assert chat.status_code == 200
    assert "Mock AI response" in chat.json()["response"]
    assert chat.json()["provider"] == "mock"
    assert chat.json()["prompt_tokens"] > 0
    assert chat.json()["completion_tokens"] > 0
    assert chat.json()["estimated_cost_usd"] == 0

    fallback = client.post(
        "/v1/chat",
        headers={"x-api-key": auth["api_key"]},
        json={
            "input": "fallback hello",
            "model": "gpt-4o-mini",
            "fallback_models": ["mock"],
        },
    )
    assert fallback.status_code == 200
    assert fallback.json()["provider"] == "mock"
    assert fallback.json()["fallback_used"] is True


def test_refresh_verify_reset_and_sessions(client):
    auth = register_user(client, email="flow@example.com")

    refresh = client.post("/auth/refresh", json={"refresh_token": auth["refresh_token"]})
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]

    verify = client.post("/auth/verify-email", json={"token": auth["email_verification_token"]})
    assert verify.status_code == 200

    reset_request = client.post("/auth/password-reset/request", json={"email": "flow@example.com"})
    assert reset_request.status_code == 200
    reset_token = reset_request.json()["reset_token"]
    assert reset_token

    reset_confirm = client.post(
        "/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "newpassword123"},
    )
    assert reset_confirm.status_code == 200

    login = client.post("/auth/login", json={"email": "flow@example.com", "password": "newpassword123"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    sessions = client.get("/auth/sessions", headers=headers)
    assert sessions.status_code == 200
    assert len(sessions.json()) >= 1

    history = client.get("/auth/login-history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) >= 1


def test_api_key_rotation_and_organizations(client):
    auth = register_user(client, email="keys@example.com", password="password123")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    created = client.post("/auth/api-keys", headers=headers, json={"name": "secondary"})
    assert created.status_code == 200
    created_key = created.json()
    assert created_key["key"].startswith("wfb_")

    rotated = client.post(
        f"/auth/api-keys/{created_key['id']}/rotate",
        headers=headers,
        json={"name": "secondary-rotated"},
    )
    assert rotated.status_code == 200
    assert rotated.json()["key"].startswith("wfb_")

    org = client.post("/auth/organizations", headers=headers, json={"name": "Acme", "slug": "acme"})
    assert org.status_code == 200

    member_user = register_user(client, email="member@example.com", password="password123")
    add_member = client.post(
        f"/auth/organizations/{org.json()['id']}/members",
        headers=headers,
        json={"email": "member@example.com", "role": "member"},
    )
    assert add_member.status_code == 200

    member_headers = {"Authorization": f"Bearer {member_user['access_token']}"}
    member_orgs = client.get("/auth/organizations", headers=member_headers)
    assert member_orgs.status_code == 200
    assert member_orgs.json()[0]["slug"] == "acme"

    audit = client.get("/auth/audit-logs", headers=headers)
    assert audit.status_code == 200
    assert len(audit.json()) >= 1

    provider_health = client.get("/v1/providers/health", headers=headers)
    assert provider_health.status_code == 200
    providers = {item["provider"]: item for item in provider_health.json()}
    assert providers["mock"]["healthy"] is True
    assert "openai" in providers


def test_stream_chat(client):
    auth = register_user(client, email="stream@example.com")

    response = client.post(
        "/v1/chat/stream",
        headers={"x-api-key": auth["api_key"]},
        json={"input": "stream this", "model": "mock"},
    )

    assert response.status_code == 200
    assert '"token"' in response.text
    assert '"done": true' in response.text
    assert '"provider": "mock"' in response.text


def test_subscription_billing_usage_invoices_and_coupons(client):
    auth = register_user(client, email="billing@example.com")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    plans = client.get("/billing/plans")
    assert plans.status_code == 200
    plan_slugs = {plan["slug"] for plan in plans.json()}
    assert {"free", "starter", "pro", "business", "enterprise"}.issubset(plan_slugs)

    coupon = client.post(
        "/billing/coupons",
        headers=headers,
        json={"code": "SAVE20", "percent_off": 20, "max_redemptions": 3},
    )
    assert coupon.status_code == 200

    subscription = client.post(
        "/billing/subscribe",
        headers=headers,
        json={"plan_slug": "pro", "coupon_code": "SAVE20"},
    )
    assert subscription.status_code == 200
    assert subscription.json()["plan"]["slug"] == "pro"

    invoices = client.get("/billing/invoices", headers=headers)
    assert invoices.status_code == 200
    assert invoices.json()[0]["discount_usd"] > 0

    payments = client.get("/billing/payments", headers=headers)
    assert payments.status_code == 200
    assert payments.json()[0]["provider"] == "mock"

    before_usage = client.get("/billing/usage", headers=headers)
    assert before_usage.status_code == 200

    chat = client.post(
        "/v1/chat",
        headers={"x-api-key": auth["api_key"]},
        json={"input": "billing usage", "model": "mock"},
    )
    assert chat.status_code == 200

    after_usage = client.get("/billing/usage", headers=headers)
    assert after_usage.status_code == 200
    assert after_usage.json()["requests_used"] == before_usage.json()["requests_used"] + 1
    assert after_usage.json()["tokens_used"] >= before_usage.json()["tokens_used"]


def test_observability_request_provider_activity_and_alerts(client):
    auth = register_user(client, email="observe@example.com")
    bearer_headers = {"Authorization": f"Bearer {auth['access_token']}"}

    chat = client.post(
        "/v1/chat",
        headers={"x-api-key": auth["api_key"]},
        json={"input": "observe this", "model": "mock"},
    )
    assert chat.status_code == 200
    assert chat.json()["provider_latency_ms"] >= 0

    summary = client.get("/observability/summary", headers=bearer_headers)
    assert summary.status_code == 200
    assert summary.json()["request_count"] >= 1
    assert summary.json()["total_tokens"] > 0

    requests = client.get("/observability/requests", headers=bearer_headers)
    assert requests.status_code == 200
    assert any(item["path"] == "/v1/chat" for item in requests.json())

    providers = client.get("/observability/providers", headers=bearer_headers)
    assert providers.status_code == 200
    assert providers.json()[0]["provider"] == "mock"

    provider_latency = client.get("/observability/providers/latency", headers=bearer_headers)
    assert provider_latency.status_code == 200
    assert provider_latency.json()[0]["provider"] == "mock"

    activity = client.get("/observability/activity", headers=bearer_headers)
    assert activity.status_code == 200
    assert any(item["action"] == "chat.completed" for item in activity.json())

    health = client.get("/observability/system-health", headers=bearer_headers)
    assert health.status_code == 200
    assert health.json()["database"] == "ok"

    created_alert = client.post(
        "/observability/alerts",
        headers=bearer_headers,
        json={
            "severity": "warning",
            "title": "Latency threshold crossed",
            "message": "p95 exceeded configured target",
            "source": "api",
        },
    )
    assert created_alert.status_code == 200

    ack = client.post(f"/observability/alerts/{created_alert.json()['id']}/ack", headers=bearer_headers)
    assert ack.status_code == 200
    assert ack.json()["status"] == "acknowledged"

    resolved = client.post(f"/observability/alerts/{created_alert.json()['id']}/resolve", headers=bearer_headers)
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


def test_validation_errors(client):
    short_password = client.post(
        "/auth/register",
        json={"email": "bad@example.com", "password": "short"},
    )
    assert short_password.status_code == 422

    auth = register_user(client, email="validation@example.com")
    empty_chat = client.post(
        "/v1/chat",
        headers={"x-api-key": auth["api_key"]},
        json={"input": ""},
    )
    assert empty_chat.status_code == 422
