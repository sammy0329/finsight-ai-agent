"""T-210: ChromaDB Retriever 설정 테스트."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import MagicMock, patch


class TestGetRetriever:
    """get_retriever 함수 테스트."""

    @patch("app.agent.retriever.Chroma")
    @patch("app.agent.retriever.OpenAIEmbeddings")
    def test_returns_retriever_object(self, mock_embeddings_cls, mock_chroma_cls):
        """retriever 객체를 반환한다."""
        from app.agent.retriever import get_retriever

        mock_retriever = MagicMock()
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.as_retriever.return_value = mock_retriever
        mock_chroma_cls.return_value = mock_chroma_instance

        result = get_retriever(chroma_host="localhost", chroma_port=8001, market="KOR")
        assert result is mock_retriever

    @patch("app.agent.retriever.Chroma")
    @patch("app.agent.retriever.OpenAIEmbeddings")
    def test_kor_market_uses_news_kor_collection(self, mock_embeddings_cls, mock_chroma_cls):
        """market='KOR'이면 collection_name='news_kor'을 사용한다."""
        from app.agent.retriever import get_retriever

        mock_chroma_instance = MagicMock()
        mock_chroma_cls.return_value = mock_chroma_instance

        get_retriever(chroma_host="localhost", chroma_port=8001, market="KOR")

        call_kwargs = mock_chroma_cls.call_args
        assert call_kwargs[1]["collection_name"] == "news_kor"

    @patch("app.agent.retriever.Chroma")
    @patch("app.agent.retriever.OpenAIEmbeddings")
    def test_us_market_uses_news_us_collection(self, mock_embeddings_cls, mock_chroma_cls):
        """market='US'이면 collection_name='news_us'를 사용한다."""
        from app.agent.retriever import get_retriever

        mock_chroma_instance = MagicMock()
        mock_chroma_cls.return_value = mock_chroma_instance

        get_retriever(chroma_host="localhost", chroma_port=8001, market="US")

        call_kwargs = mock_chroma_cls.call_args
        assert call_kwargs[1]["collection_name"] == "news_us"

    @patch("app.agent.retriever.Chroma")
    @patch("app.agent.retriever.OpenAIEmbeddings")
    def test_default_k_is_5(self, mock_embeddings_cls, mock_chroma_cls):
        """기본 k 값이 5이다."""
        from app.agent.retriever import get_retriever

        mock_chroma_instance = MagicMock()
        mock_chroma_cls.return_value = mock_chroma_instance

        get_retriever(chroma_host="localhost", chroma_port=8001, market="KOR")

        as_retriever_kwargs = mock_chroma_instance.as_retriever.call_args
        search_kwargs = as_retriever_kwargs[1]["search_kwargs"]
        assert search_kwargs["k"] == 5

    @patch("app.agent.retriever.Chroma")
    @patch("app.agent.retriever.OpenAIEmbeddings")
    def test_custom_k_is_applied(self, mock_embeddings_cls, mock_chroma_cls):
        """커스텀 k 값이 retriever에 반영된다."""
        from app.agent.retriever import get_retriever

        mock_chroma_instance = MagicMock()
        mock_chroma_cls.return_value = mock_chroma_instance

        get_retriever(chroma_host="localhost", chroma_port=8001, market="KOR", k=10)

        as_retriever_kwargs = mock_chroma_instance.as_retriever.call_args
        search_kwargs = as_retriever_kwargs[1]["search_kwargs"]
        assert search_kwargs["k"] == 10

    @patch("app.agent.retriever.Chroma")
    @patch("app.agent.retriever.OpenAIEmbeddings")
    def test_uses_text_embedding_3_small(self, mock_embeddings_cls, mock_chroma_cls):
        """OpenAIEmbeddings에 text-embedding-3-small 모델을 사용한다."""
        from app.agent.retriever import get_retriever

        mock_chroma_instance = MagicMock()
        mock_chroma_cls.return_value = mock_chroma_instance

        get_retriever(chroma_host="localhost", chroma_port=8001, market="KOR")

        mock_embeddings_cls.assert_called_once_with(model="text-embedding-3-small")

    @patch("app.agent.retriever.chromadb.HttpClient")
    @patch("app.agent.retriever.Chroma")
    @patch("app.agent.retriever.OpenAIEmbeddings")
    def test_chroma_client_connection_params(
        self, mock_embeddings_cls, mock_chroma_cls, mock_http_client_cls
    ):
        """chromadb.HttpClient에 올바른 host/port가 전달된다."""
        from app.agent.retriever import get_retriever

        mock_chroma_instance = MagicMock()
        mock_chroma_cls.return_value = mock_chroma_instance

        get_retriever(chroma_host="myhost", chroma_port=9999, market="KOR")

        mock_http_client_cls.assert_called_once_with(host="myhost", port=9999)
        call_kwargs = mock_chroma_cls.call_args[1]
        assert call_kwargs["collection_name"] == "news_kor"
        assert call_kwargs["client"] is mock_http_client_cls.return_value

    @patch("app.agent.retriever.Chroma")
    @patch("app.agent.retriever.OpenAIEmbeddings")
    def test_market_filter_in_retriever(self, mock_embeddings_cls, mock_chroma_cls):
        """retriever에 market 메타데이터 필터가 적용된다."""
        from app.agent.retriever import get_retriever

        mock_chroma_instance = MagicMock()
        mock_chroma_cls.return_value = mock_chroma_instance

        get_retriever(chroma_host="localhost", chroma_port=8001, market="KOR")

        as_retriever_kwargs = mock_chroma_instance.as_retriever.call_args
        search_kwargs = as_retriever_kwargs[1]["search_kwargs"]
        assert search_kwargs["filter"] == {"market": "KOR"}
