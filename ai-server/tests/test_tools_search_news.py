"""T-220: search_news_tool 테스트 -- ChromaDB RAG 검색 래핑."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import MagicMock, patch

from langchain_core.documents import Document


class TestSearchNews:
    """search_news 함수 단위 테스트."""

    @patch("app.agent.tools.get_retriever")
    def test_returns_formatted_chunks(self, mock_get_retriever):
        """관련 뉴스 청크를 포맷팅하여 반환한다."""
        from app.agent.tools import search_news

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            Document(page_content="삼성전자 실적 호조", metadata={"source": "a.com"}),
            Document(page_content="반도체 수출 증가", metadata={"source": "b.com"}),
        ]
        mock_get_retriever.return_value = mock_retriever

        result = search_news("삼성전자", market="KOR")

        assert "삼성전자 실적 호조" in result
        assert "반도체 수출 증가" in result

    @patch("app.agent.tools.get_retriever")
    def test_returns_fallback_when_no_results(self, mock_get_retriever):
        """검색 결과가 없으면 폴백 메시지를 반환한다."""
        from app.agent.tools import search_news

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_get_retriever.return_value = mock_retriever

        result = search_news("존재하지않는종목")

        assert "관련 뉴스를 찾을 수 없습니다" in result

    @patch("app.agent.tools.get_retriever")
    def test_kor_market_filter(self, mock_get_retriever):
        """market='KOR'이 retriever에 전달된다."""
        from app.agent.tools import search_news

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_get_retriever.return_value = mock_retriever

        search_news("테스트", market="KOR")

        mock_get_retriever.assert_called_once()
        call_kwargs = mock_get_retriever.call_args[1]
        assert call_kwargs["market"] == "KOR"

    @patch("app.agent.tools.get_retriever")
    def test_us_market_filter(self, mock_get_retriever):
        """market='US'가 retriever에 전달된다."""
        from app.agent.tools import search_news

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []
        mock_get_retriever.return_value = mock_retriever

        search_news("AAPL", market="US")

        call_kwargs = mock_get_retriever.call_args[1]
        assert call_kwargs["market"] == "US"

    @patch("app.agent.tools.get_retriever")
    def test_includes_source_metadata(self, mock_get_retriever):
        """결과에 출처 정보가 포함된다."""
        from app.agent.tools import search_news

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            Document(page_content="뉴스 본문", metadata={"source": "https://example.com/news"}),
        ]
        mock_get_retriever.return_value = mock_retriever

        result = search_news("테스트")

        assert "example.com" in result

    @patch("app.agent.tools.get_retriever")
    def test_handles_retriever_exception_gracefully(self, mock_get_retriever):
        """retriever 오류 시 에러 메시지를 반환한다."""
        from app.agent.tools import search_news

        mock_retriever = MagicMock()
        mock_retriever.invoke.side_effect = Exception("ChromaDB connection failed")
        mock_get_retriever.return_value = mock_retriever

        result = search_news("테스트")

        assert "오류" in result or "실패" in result
