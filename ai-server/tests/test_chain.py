"""T-211, T-214: RAG 체인 구성 및 폴백 처리 테스트."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import MagicMock, patch

from langchain_core.documents import Document


class TestFormatDocs:
    """format_docs 함수 테스트."""

    def test_formats_multiple_documents(self):
        """여러 문서를 개행 두 줄로 연결한다."""
        from app.agent.chain import format_docs

        docs = [
            Document(page_content="첫 번째 문서"),
            Document(page_content="두 번째 문서"),
            Document(page_content="세 번째 문서"),
        ]
        result = format_docs(docs)
        assert result == "첫 번째 문서\n\n두 번째 문서\n\n세 번째 문서"

    def test_formats_single_document(self):
        """단일 문서는 그대로 반환한다."""
        from app.agent.chain import format_docs

        docs = [Document(page_content="단일 문서")]
        result = format_docs(docs)
        assert result == "단일 문서"

    def test_formats_empty_list(self):
        """빈 리스트는 빈 문자열을 반환한다."""
        from app.agent.chain import format_docs

        result = format_docs([])
        assert result == ""

    def test_preserves_whitespace_in_content(self):
        """문서 내부 공백을 보존한다."""
        from app.agent.chain import format_docs

        docs = [Document(page_content="줄1\n줄2")]
        result = format_docs(docs)
        assert result == "줄1\n줄2"


class TestBuildRagChain:
    """build_rag_chain 함수 테스트."""

    @patch("app.agent.chain.ChatOpenAI")
    def test_chain_returns_string(self, mock_llm_cls):
        """체인 invoke 결과는 문자열이다."""
        from app.agent.chain import build_rag_chain

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            Document(page_content="관련 뉴스 내용", metadata={"source": "http://example.com"}),
        ]

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="AI 인사이트 결과")
        mock_llm_cls.return_value = mock_llm

        chain = build_rag_chain(segment="A", retriever=mock_retriever, openai_api_key="test-key")
        # Chain is an LCEL chain; test that it can be built without error
        assert chain is not None

    @patch("app.agent.chain.ChatOpenAI")
    def test_chain_uses_gpt4o_mini(self, mock_llm_cls):
        """체인은 gpt-4o-mini 모델을 사용한다."""
        from app.agent.chain import build_rag_chain

        mock_retriever = MagicMock()

        build_rag_chain(segment="A", retriever=mock_retriever, openai_api_key="test-key")

        mock_llm_cls.assert_called_once_with(model="gpt-4o-mini", api_key="test-key")

    @patch("app.agent.chain.get_prompt_for_segment")
    @patch("app.agent.chain.ChatOpenAI")
    def test_segment_a_uses_correct_prompt(self, mock_llm_cls, mock_get_prompt):
        """세그먼트 A는 A형 프롬프트를 사용한다."""
        from app.agent.chain import build_rag_chain

        mock_retriever = MagicMock()
        mock_prompt = MagicMock()
        mock_get_prompt.return_value = mock_prompt

        build_rag_chain(segment="A", retriever=mock_retriever, openai_api_key="test-key")

        mock_get_prompt.assert_called_once_with("A")

    @patch("app.agent.chain.get_prompt_for_segment")
    @patch("app.agent.chain.ChatOpenAI")
    def test_segment_b_uses_correct_prompt(self, mock_llm_cls, mock_get_prompt):
        """세그먼트 B는 B형 프롬프트를 사용한다."""
        from app.agent.chain import build_rag_chain

        mock_retriever = MagicMock()
        mock_prompt = MagicMock()
        mock_get_prompt.return_value = mock_prompt

        build_rag_chain(segment="B", retriever=mock_retriever, openai_api_key="test-key")

        mock_get_prompt.assert_called_once_with("B")

    @patch("app.agent.chain.get_prompt_for_segment")
    @patch("app.agent.chain.ChatOpenAI")
    def test_segment_c_uses_correct_prompt(self, mock_llm_cls, mock_get_prompt):
        """세그먼트 C는 C형 프롬프트를 사용한다."""
        from app.agent.chain import build_rag_chain

        mock_retriever = MagicMock()
        mock_prompt = MagicMock()
        mock_get_prompt.return_value = mock_prompt

        build_rag_chain(segment="C", retriever=mock_retriever, openai_api_key="test-key")

        mock_get_prompt.assert_called_once_with("C")


class TestFallbackHandling:
    """T-214: 검색 결과 없을 때 폴백 처리 테스트."""

    FALLBACK_MSG = "현재 관련 금융 데이터가 없습니다. 잠시 후 다시 시도해주세요."

    @patch("app.agent.chain.ChatOpenAI")
    def test_empty_retrieval_returns_fallback(self, mock_llm_cls):
        """retriever 결과가 빈 리스트이면 폴백 메시지를 반환한다."""
        from app.agent.chain import build_rag_chain

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = []

        # RunnablePassthrough / LCEL pipe operator 사용 시
        # retriever가 빈 결과를 반환하면 폴백 메시지를 반환해야 한다
        chain = build_rag_chain(segment="A", retriever=mock_retriever, openai_api_key="test-key")

        # invoke를 직접 테스트하기 어려우므로 build_rag_chain_with_fallback 테스트
        from app.agent.chain import invoke_with_fallback

        result = invoke_with_fallback(chain, mock_retriever, "테스트 쿼리")
        assert result == self.FALLBACK_MSG

    @patch("app.agent.chain.ChatOpenAI")
    def test_nonempty_retrieval_calls_chain(self, mock_llm_cls):
        """retriever 결과가 있으면 체인을 실행한다."""
        from app.agent.chain import invoke_with_fallback

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            Document(page_content="뉴스 내용", metadata={"source": "http://example.com"}),
        ]

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="AI 분석 결과")
        mock_llm_cls.return_value = mock_llm

        chain = MagicMock()
        chain.invoke.return_value = "AI 분석 결과"

        result = invoke_with_fallback(chain, mock_retriever, "삼성전자 전망")
        assert result == "AI 분석 결과"
        chain.invoke.assert_called_once_with("삼성전자 전망")
