"""T-212, T-213: POST /api/ai/insight 실제 연결 및 스트리밍 엔드포인트 테스트."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.main import app

VALID_KEY = "test-internal-key"


@pytest.fixture()
def client():
    return TestClient(app)


# ── T-212: /api/ai/insight RAG 체인 연결 ────────────────────────────


class TestInsightWithRagChain:
    """POST /api/ai/insight가 실제 RAG 체인과 연결되어 동작하는지 테스트."""

    @patch("app.api.router.get_retriever")
    @patch("app.api.router.build_rag_chain")
    @patch("app.api.router.invoke_with_fallback")
    def test_returns_200_with_insight(
        self, mock_invoke, mock_build_chain, mock_get_retriever, client
    ):
        """정상 요청 시 200과 insight를 반환한다."""
        mock_retriever = MagicMock()
        mock_get_retriever.return_value = mock_retriever

        mock_chain = MagicMock()
        mock_build_chain.return_value = mock_chain

        mock_invoke.return_value = "삼성전자 주가 전망은 긍정적입니다."

        mock_retriever.invoke.return_value = [
            Document(
                page_content="뉴스 본문",
                metadata={"source": "https://example.com/news/1"},
            ),
        ]

        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "A", "query": "삼성전자 전망"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["insight"] == "삼성전자 주가 전망은 긍정적입니다."

    @patch("app.api.router.get_retriever")
    @patch("app.api.router.build_rag_chain")
    @patch("app.api.router.invoke_with_fallback")
    def test_response_contains_sources(
        self, mock_invoke, mock_build_chain, mock_get_retriever, client
    ):
        """응답에 sources 필드가 포함된다."""
        mock_retriever = MagicMock()
        mock_get_retriever.return_value = mock_retriever

        mock_chain = MagicMock()
        mock_build_chain.return_value = mock_chain

        mock_invoke.return_value = "인사이트 내용"

        mock_retriever.invoke.return_value = [
            Document(page_content="뉴스1", metadata={"source": "https://a.com"}),
            Document(page_content="뉴스2", metadata={"source": "https://b.com"}),
        ]

        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "B", "query": "테슬라 분석"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        data = resp.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) >= 1

    @patch("app.api.router.get_retriever")
    @patch("app.api.router.build_rag_chain")
    @patch("app.api.router.invoke_with_fallback")
    def test_sources_are_unique(self, mock_invoke, mock_build_chain, mock_get_retriever, client):
        """sources에 중복 URL이 없다."""
        mock_retriever = MagicMock()
        mock_get_retriever.return_value = mock_retriever

        mock_chain = MagicMock()
        mock_build_chain.return_value = mock_chain

        mock_invoke.return_value = "인사이트"

        mock_retriever.invoke.return_value = [
            Document(page_content="뉴스1", metadata={"source": "https://a.com"}),
            Document(page_content="뉴스2", metadata={"source": "https://a.com"}),
            Document(page_content="뉴스3", metadata={"source": "https://b.com"}),
        ]

        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "A", "query": "test"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        data = resp.json()
        assert len(data["sources"]) == len(set(data["sources"]))

    @patch("app.api.router.get_retriever")
    @patch("app.api.router.build_rag_chain")
    @patch("app.api.router.invoke_with_fallback")
    def test_segment_a_c_uses_kor_market(
        self, mock_invoke, mock_build_chain, mock_get_retriever, client
    ):
        """세그먼트 A, C는 KOR 시장을 사용한다."""
        mock_retriever = MagicMock()
        mock_get_retriever.return_value = mock_retriever
        mock_build_chain.return_value = MagicMock()
        mock_invoke.return_value = "인사이트"
        mock_retriever.invoke.return_value = []

        for segment in ["A", "C"]:
            client.post(
                "/api/ai/insight",
                json={"user_segment": segment, "query": "test"},
                headers={"X-Internal-Key": VALID_KEY},
            )
            call_kwargs = mock_get_retriever.call_args[1]
            assert call_kwargs["market"] == "KOR", f"Segment {segment} should use KOR market"

    @patch("app.api.router.get_retriever")
    @patch("app.api.router.build_rag_chain")
    @patch("app.api.router.invoke_with_fallback")
    def test_segment_b_uses_us_market(
        self, mock_invoke, mock_build_chain, mock_get_retriever, client
    ):
        """세그먼트 B는 US 시장을 사용한다."""
        mock_retriever = MagicMock()
        mock_get_retriever.return_value = mock_retriever
        mock_build_chain.return_value = MagicMock()
        mock_invoke.return_value = "인사이트"
        mock_retriever.invoke.return_value = []

        client.post(
            "/api/ai/insight",
            json={"user_segment": "B", "query": "test"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        call_kwargs = mock_get_retriever.call_args[1]
        assert call_kwargs["market"] == "US"

    @patch("app.api.router.get_retriever")
    @patch("app.api.router.build_rag_chain")
    @patch("app.api.router.invoke_with_fallback")
    def test_fallback_when_no_docs(self, mock_invoke, mock_build_chain, mock_get_retriever, client):
        """검색 결과 없으면 폴백 메시지를 반환한다."""
        mock_retriever = MagicMock()
        mock_get_retriever.return_value = mock_retriever
        mock_build_chain.return_value = MagicMock()

        fallback_msg = "현재 관련 금융 데이터가 없습니다. 잠시 후 다시 시도해주세요."
        mock_invoke.return_value = fallback_msg
        mock_retriever.invoke.return_value = []

        resp = client.post(
            "/api/ai/insight",
            json={"user_segment": "A", "query": "test"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        data = resp.json()
        assert data["insight"] == fallback_msg
        assert data["sources"] == []


# ── T-213 / T-225: /api/ai/insight/stream 스트리밍 엔드포인트 ──────
# 내부 구현이 AgentExecutor로 교체되었으므로 agent 모듈을 mock 한다.


class TestInsightStream:
    """POST /api/ai/insight/stream 스트리밍 엔드포인트 테스트."""

    @patch("app.api.router.astream_agent")
    @patch("app.api.router.create_agent_executor")
    def test_stream_returns_200(self, mock_create_executor, mock_astream, client):
        """스트리밍 엔드포인트가 200을 반환한다."""
        mock_create_executor.return_value = MagicMock()

        async def mock_gen(executor, query):
            for token in ["안녕", "하세요"]:
                yield token

        mock_astream.side_effect = mock_gen

        resp = client.post(
            "/api/ai/insight/stream",
            json={"user_segment": "A", "query": "test"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert resp.status_code == 200

    @patch("app.api.router.astream_agent")
    @patch("app.api.router.create_agent_executor")
    def test_stream_content_type_is_event_stream(self, mock_create_executor, mock_astream, client):
        """스트리밍 응답의 content-type이 text/event-stream이다."""
        mock_create_executor.return_value = MagicMock()

        async def mock_gen(executor, query):
            yield "토큰1"

        mock_astream.side_effect = mock_gen

        resp = client.post(
            "/api/ai/insight/stream",
            json={"user_segment": "A", "query": "test"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        assert "text/event-stream" in resp.headers.get("content-type", "")

    @patch("app.api.router.astream_agent")
    @patch("app.api.router.create_agent_executor")
    def test_stream_contains_tokens(self, mock_create_executor, mock_astream, client):
        """스트리밍 응답에 토큰이 포함된다."""
        mock_create_executor.return_value = MagicMock()

        async def mock_gen(executor, query):
            for token in ["삼성", "전자", " 전망"]:
                yield token

        mock_astream.side_effect = mock_gen

        resp = client.post(
            "/api/ai/insight/stream",
            json={"user_segment": "A", "query": "test"},
            headers={"X-Internal-Key": VALID_KEY},
        )
        body = resp.text
        assert "삼성" in body
        assert "전자" in body

    def test_stream_no_auth_returns_401(self, client):
        """스트리밍 엔드포인트도 인증이 필요하다."""
        resp = client.post(
            "/api/ai/insight/stream",
            json={"user_segment": "A", "query": "test"},
        )
        assert resp.status_code == 401
