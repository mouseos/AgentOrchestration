import importlib.util
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def load_auth_middleware():
    module_path = Path(__file__).parents[1] / "src" / "api" / "middleware.py"
    spec = importlib.util.spec_from_file_location("api_middleware", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.AuthMiddleware


AuthMiddleware = load_auth_middleware()


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware)

    @app.api_route("/api/v2/protected", methods=["GET", "OPTIONS"])
    async def protected_route():
        return {"ok": True}

    return app


class TestAuthMiddleware:
    def test_options_preflight_reaches_handler_without_auth(self):
        client = TestClient(create_test_app())

        response = client.options("/api/v2/protected")

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_real_api_request_without_auth_is_rejected(self):
        client = TestClient(create_test_app())

        response = client.get("/api/v2/protected")

        assert response.status_code == 401
        assert response.text == "Unauthorized"

    def test_real_api_request_with_bearer_auth_reaches_handler(self):
        client = TestClient(create_test_app())

        response = client.get(
            "/api/v2/protected",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}
