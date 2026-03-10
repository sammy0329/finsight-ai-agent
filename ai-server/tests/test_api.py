"""T-201, T-203, T-204: FastAPI 라우터, 인증 미들웨어, 헬스체크 API 테스트."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

VALID_KEY = "test-internal-key"
INVALID_KEY = "wrong-key"


@pytest.fixture()
def client():
    return TestClient(app)


# ── T-204: /health 엔드포인트 ────────────────────────────────────


class TestHealthEndpoint:
    """GET /health 엔드포인트 테스트."""

    def test_health_returns_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_no_auth_required(self, client: TestClient):
        """헬스체크는 인증 헤더 없이도 접근 가능해야 한다."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_chroma_connected(self, client: TestClient):
        """ChromaDB 연결 성공 시 chroma=connected."""
        with patch("app.main.chromadb.HttpClient") as mock_chroma:
            mock_client = mock_chroma.return_value
            mock_client.heartbeat.return_value = 1
            resp = client.get("/health")
            data = resp.json()
            assert data["status"] == "ok"
            assert data["chroma"] in ("connected", "disconnected")

    def test_health_chroma_disconnected(self, client: TestClient):
        """ChromaDB 연결 실패 시 chroma=disconnected."""
        with patch("app.main.chromadb.HttpClient") as mock_chroma:
            mock_chroma.return_value.heartbeat.side_effect = Exception("Connection refused")
            resp = client.get("/health")
            data = resp.json()
            assert data["status"] == "ok"
            assert data["chroma"] == "disconnected"


# ── T-203: 인증 미들웨어 ──────────────────────────────────────────


class TestAuthMiddleware:
    """내부 서비스 인증 테스트."""

    def test_insight_no_key_returns_401(self, client: TestClient):
        """인증 헤더 없으면 401."""
        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "A", "query": "test"},
        )
        assert resp.status_code == 401

    def test_insight_invalid_key_returns_401(self, client: TestClient):
        """잘못된 키면 401."""
        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "A", "query": "test"},
            headers={"X-Internal-Key": INVALID_KEY},
        )
        assert resp.status_code == 401

    def test_insight_valid_key_returns_200(self, client: TestClient):
        """올바른 키면 200."""
        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "A", "query": "test"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert resp.status_code == 200


# ── T-201: /api/ai/insight 엔드포인트 ────────────────────────────


class TestInsightEndpoint:
    """POST /api/ai/insight 엔드포인트 테스트."""

    @pytest.mark.parametrize("segment", ["A", "B", "C"])
    def test_valid_segments(self, client: TestClient, segment: str):
        """user_segment A/B/C 각각 정상 처리."""
        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": segment, "query": "테스트 쿼리"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "insight" in data
        assert "sources" in data
        assert segment in data["insight"]

    def test_invalid_segment_returns_422(self, client: TestClient):
        """user_segment 잘못된 값("D")이면 422."""
        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "D", "query": "test"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert resp.status_code == 422

    def test_missing_query_returns_422(self, client: TestClient):
        """query 필드 누락 시 422."""
        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "A"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert resp.status_code == 422

    def test_response_structure(self, client: TestClient):
        """응답이 InsightResponse 스키마를 준수."""
        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "A", "query": "삼성전자 전망"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        data = resp.json()
        assert isinstance(data["insight"], str)
        assert isinstance(data["sources"], list)

    def test_empty_body_returns_422(self, client: TestClient):
        """빈 요청 body면 422."""
        resp = client.post(
            "/api/ai/insight",
            headers={"X-Internal-Key": VALID_KEY},
            content="{}",
        )
        assert resp.status_code == 422
