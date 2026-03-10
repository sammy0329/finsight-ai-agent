"""T-111: ChromaDB 클라이언트 초기화 모듈 테스트."""

from unittest.mock import MagicMock, patch

import pytest

from app.pipeline.chroma_client import get_chroma_client, get_or_create_collection


# ================================================================== #
# get_chroma_client
# ================================================================== #
class TestGetChromaClient:
    """ChromaDB HttpClient 생성 테스트."""

    @patch("app.pipeline.chroma_client.chromadb")
    def test_returns_http_client(self, mock_chromadb):
        """host, port를 전달하면 HttpClient를 반환한다."""
        mock_client = MagicMock()
        mock_chromadb.HttpClient.return_value = mock_client

        result = get_chroma_client("localhost", 8000)

        mock_chromadb.HttpClient.assert_called_once_with(host="localhost", port=8000)
        assert result is mock_client

    @patch("app.pipeline.chroma_client.chromadb")
    def test_with_custom_host_port(self, mock_chromadb):
        """커스텀 host, port도 올바르게 전달된다."""
        mock_client = MagicMock()
        mock_chromadb.HttpClient.return_value = mock_client

        result = get_chroma_client("192.168.1.100", 9090)

        mock_chromadb.HttpClient.assert_called_once_with(host="192.168.1.100", port=9090)
        assert result is mock_client

    @patch("app.pipeline.chroma_client.chromadb")
    def test_connection_error_propagates(self, mock_chromadb):
        """연결 실패 시 예외가 전파된다."""
        mock_chromadb.HttpClient.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectionError, match="Connection refused"):
            get_chroma_client("invalid-host", 8000)


# ================================================================== #
# get_or_create_collection
# ================================================================== #
class TestGetOrCreateCollection:
    """ChromaDB 컬렉션 조회/생성 테스트."""

    def test_returns_collection(self):
        """컬렉션 이름을 전달하면 컬렉션 객체를 반환한다."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        result = get_or_create_collection(mock_client, "test_collection")

        mock_client.get_or_create_collection.assert_called_once_with(name="test_collection")
        assert result is mock_collection

    def test_empty_name_raises_error(self):
        """빈 문자열 이름이면 ValueError를 발생시킨다."""
        mock_client = MagicMock()

        with pytest.raises(ValueError, match="collection name must not be empty"):
            get_or_create_collection(mock_client, "")

    def test_whitespace_name_raises_error(self):
        """공백만 있는 이름이면 ValueError를 발생시킨다."""
        mock_client = MagicMock()

        with pytest.raises(ValueError, match="collection name must not be empty"):
            get_or_create_collection(mock_client, "   ")

    def test_client_error_propagates(self):
        """ChromaDB 클라이언트 오류가 전파된다."""
        mock_client = MagicMock()
        mock_client.get_or_create_collection.side_effect = RuntimeError("ChromaDB error")

        with pytest.raises(RuntimeError, match="ChromaDB error"):
            get_or_create_collection(mock_client, "test_collection")
