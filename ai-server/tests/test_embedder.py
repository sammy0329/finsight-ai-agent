"""T-113: 임베딩 모듈 테스트."""

from unittest.mock import MagicMock, patch

import pytest

from app.pipeline.embedder import embed_documents


# ================================================================== #
# embed_documents
# ================================================================== #
class TestEmbedDocuments:
    """OpenAI 임베딩 호출 테스트."""

    @patch("app.pipeline.embedder.OpenAI")
    def test_returns_embeddings_for_texts(self, mock_openai_cls):
        """텍스트 리스트를 전달하면 임베딩 리스트를 반환한다."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # OpenAI 응답 mock
        mock_embedding_1 = MagicMock()
        mock_embedding_1.embedding = [0.1, 0.2, 0.3]
        mock_embedding_2 = MagicMock()
        mock_embedding_2.embedding = [0.4, 0.5, 0.6]

        mock_response = MagicMock()
        mock_response.data = [mock_embedding_1, mock_embedding_2]
        mock_client.embeddings.create.return_value = mock_response

        result = embed_documents(["hello", "world"], api_key="test-key")

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]

    @patch("app.pipeline.embedder.OpenAI")
    def test_uses_correct_model(self, mock_openai_cls):
        """text-embedding-3-small 모델을 사용한다."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1]
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]
        mock_client.embeddings.create.return_value = mock_response

        embed_documents(["test"], api_key="test-key")

        call_kwargs = mock_client.embeddings.create.call_args
        assert call_kwargs.kwargs["model"] == "text-embedding-3-small"

    @patch("app.pipeline.embedder.OpenAI")
    def test_empty_list_returns_empty(self, mock_openai_cls):
        """빈 리스트를 전달하면 빈 리스트를 반환한다."""
        result = embed_documents([], api_key="test-key")

        assert result == []
        mock_openai_cls.return_value.embeddings.create.assert_not_called()

    @patch("app.pipeline.embedder.OpenAI")
    def test_batch_processing_over_100(self, mock_openai_cls):
        """100개 초과 텍스트는 배치로 분할하여 처리한다."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        def make_response(n):
            mock_resp = MagicMock()
            embeddings = []
            for _ in range(n):
                e = MagicMock()
                e.embedding = [0.1] * 10
                embeddings.append(e)
            mock_resp.data = embeddings
            return mock_resp

        # 150개 텍스트 -> 100 + 50 배치
        mock_client.embeddings.create.side_effect = [
            make_response(100),
            make_response(50),
        ]

        texts = [f"text_{i}" for i in range(150)]
        result = embed_documents(texts, api_key="test-key")

        assert len(result) == 150
        assert mock_client.embeddings.create.call_count == 2

    @patch("app.pipeline.embedder.OpenAI")
    def test_exactly_100_single_batch(self, mock_openai_cls):
        """정확히 100개면 1번의 API 호출로 처리한다."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_resp = MagicMock()
        embeddings = []
        for _ in range(100):
            e = MagicMock()
            e.embedding = [0.1]
            embeddings.append(e)
        mock_resp.data = embeddings
        mock_client.embeddings.create.return_value = mock_resp

        texts = [f"text_{i}" for i in range(100)]
        result = embed_documents(texts, api_key="test-key")

        assert len(result) == 100
        assert mock_client.embeddings.create.call_count == 1

    @patch("app.pipeline.embedder.OpenAI")
    def test_api_error_propagates(self, mock_openai_cls):
        """OpenAI API 오류가 전파된다."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.embeddings.create.side_effect = RuntimeError("API rate limit")

        with pytest.raises(RuntimeError, match="API rate limit"):
            embed_documents(["test"], api_key="test-key")

    @patch("app.pipeline.embedder.OpenAI")
    def test_passes_api_key_to_client(self, mock_openai_cls):
        """api_key가 OpenAI 클라이언트에 전달된다."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1]
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]
        mock_client.embeddings.create.return_value = mock_response

        embed_documents(["test"], api_key="my-secret-key")

        mock_openai_cls.assert_called_once_with(api_key="my-secret-key")
