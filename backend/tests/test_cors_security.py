import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_cors_preflight_options(client):
    """Verify that OPTIONS preflight requests return 200 with CORS headers."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type,X-Merchant-ID",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_dynamic_port_regex(client):
    """Verify that any port on localhost or 127.0.0.1 is accepted by origin regex."""
    for origin in ["http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:4173"]:
        response = client.get(
            "/api/v1/health",
            headers={"Origin": origin},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin
        assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_headers_on_error_response(client):
    """Verify that error responses still carry CORS headers."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@recoverx.io", "password": "wrongpassword"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 401
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_production_origin(client):
    """Verify that production Vercel frontend is accepted and returns CORS headers."""
    for origin in ["https://recover-x-sage.vercel.app", "https://recover-x-preview-123.vercel.app"]:
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type,X-Merchant-ID",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin
        assert response.headers.get("access-control-allow-credentials") == "true"
