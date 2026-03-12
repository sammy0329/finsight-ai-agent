"""T-225: FastAPI 엔드포인트 수정 -- AgentExecutor SSE 스트리밍 테스트."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

VALID_KEY = "test-internal-key"


@pytest.fixture()
def client():
    return TestClient(app)


class TestInsightStreamWithAgent:
    """POST /api/ai/insight/stream이 AgentExecutor를 사용하는지 테스트."""

    @patch("app.api.router.astream_agent")
    @patch("app.api.router.create_agent_executor")
    def test_stream_returns_200(self, mock_create_executor, mock_astream, client):
        """스트리밍 엔드포인트가 200을 반환한다."""
        mock_executor = MagicMock()
        mock_create_executor.return_value = mock_executor

        async def mock_gen(executor, query):
            yield "응답"

        mock_astream.side_effect = mock_gen

        resp = client.post(
            "/api/ai/insight/stream",
            json={"user_segment": "A", "query": "삼성전자 전망"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert resp.status_code == 200

    @patch("app.api.router.astream_agent")
    @patch("app.api.router.create_agent_executor")
    def test_stream_content_type(self, mock_create_executor, mock_astream, client):
        """응답 content-type이 text/event-stream이다."""
        mock_executor = MagicMock()
        mock_create_executor.return_value = mock_executor

        async def mock_gen(executor, query):
            yield "토큰"

        mock_astream.side_effect = mock_gen

        resp = client.post(
            "/api/ai/insight/stream",
            json={"user_segment": "B", "query": "테슬라"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert "text/event-stream" in resp.headers.get("content-type", "")

    @patch("app.api.router.astream_agent")
    @patch("app.api.router.create_agent_executor")
    def test_stream_contains_tokens(self, mock_create_executor, mock_astream, client):
        """스트리밍 응답에 토큰이 포함된다."""
        mock_executor = MagicMock()
        mock_create_executor.return_value = mock_executor

        async def mock_gen(executor, query):
            for t in ["삼성", "전자", " 분석"]:
                yield t

        mock_astream.side_effect = mock_gen

        resp = client.post(
            "/api/ai/insight/stream",
            json={"user_segment": "A", "query": "삼성전자"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert "삼성" in resp.text
        assert "전자" in resp.text

    def test_stream_no_auth_returns_401(self, client):
        """인증 없이 요청하면 401을 반환한다."""
        resp = client.post(
            "/api/ai/insight/stream",
            json={"user_segment": "A", "query": "test"},
        )
        assert resp.status_code == 401

    @patch("app.api.router.astream_agent")
    @patch("app.api.router.create_agent_executor")
    def test_each_segment_creates_executor(self, mock_create_executor, mock_astream, client):
        """각 세그먼트별로 AgentExecutor가 생성된다."""
        mock_executor = MagicMock()
        mock_create_executor.return_value = mock_executor

        async def mock_gen(executor, query):
            yield "응답"

        mock_astream.side_effect = mock_gen

        for segment in ["A", "B", "C"]:
            client.post(
                "/api/ai/insight/stream",
                json={"user_segment": segment, "query": "테스트"},
                headers={"X-Internal-Key": VALID_KEY},
            )

        assert mock_create_executor.call_count == 3
        segments_called = [
            call.kwargs.get("segment") or call.args[0]
            for call in mock_create_executor.call_args_list
        ]
        # 각 세그먼트가 다 호출되었는지 확인 (순서는 무관)
        assert set(segments_called) == {"A", "B", "C"}
