"""T-114: ChromaDB upsert 모듈 테스트."""

from unittest.mock import MagicMock

import pytest

from app.pipeline.vector_store import get_collection_count, upsert_chunks


# ================================================================== #
# upsert_chunks
# ================================================================== #
class TestUpsertChunks:
    """ChromaDB upsert 테스트."""

    def test_upsert_single_chunk(self):
        """청크 1건을 upsert하면 1을 반환한다."""
        mock_collection = MagicMock()
        chunks = [
            {
                "id": "src_123",
                "document": "테스트 문서",
                "metadata": {"source": "naver_news"},
                "embedding": [0.1, 0.2, 0.3],
            }
        ]

        result = upsert_chunks(mock_collection, chunks)

        assert result == 1
        mock_collection.upsert.assert_called_once()

    def test_upsert_multiple_chunks(self):
        """여러 청크를 upsert하면 전체 건수를 반환한다."""
        mock_collection = MagicMock()
        chunks = [
            {
                "id": f"src_{i}",
                "document": f"문서 {i}",
                "metadata": {"source": "naver_news"},
                "embedding": [0.1 * i],
            }
            for i in range(5)
        ]

        result = upsert_chunks(mock_collection, chunks)

        assert result == 5

    def test_upsert_passes_correct_data(self):
        """upsert 시 ids, documents, metadatas, embeddings가 올바르게 전달된다."""
        mock_collection = MagicMock()
        chunks = [
            {
                "id": "test_1",
                "document": "문서1",
                "metadata": {"source": "newsapi"},
                "embedding": [0.1, 0.2],
            },
            {
                "id": "test_2",
                "document": "문서2",
                "metadata": {"source": "newsapi"},
                "embedding": [0.3, 0.4],
            },
        ]

        upsert_chunks(mock_collection, chunks)

        call_kwargs = mock_collection.upsert.call_args.kwargs
        assert call_kwargs["ids"] == ["test_1", "test_2"]
        assert call_kwargs["documents"] == ["문서1", "문서2"]
        assert call_kwargs["metadatas"] == [{"source": "newsapi"}, {"source": "newsapi"}]
        assert call_kwargs["embeddings"] == [[0.1, 0.2], [0.3, 0.4]]

    def test_empty_chunks_returns_zero(self):
        """빈 리스트를 전달하면 0을 반환하고 upsert를 호출하지 않는다."""
        mock_collection = MagicMock()

        result = upsert_chunks(mock_collection, [])

        assert result == 0
        mock_collection.upsert.assert_not_called()

    def test_upsert_error_propagates(self):
        """ChromaDB upsert 오류가 전파된다."""
        mock_collection = MagicMock()
        mock_collection.upsert.side_effect = RuntimeError("ChromaDB write error")
        chunks = [
            {
                "id": "src_1",
                "document": "문서",
                "metadata": {"source": "naver_news"},
                "embedding": [0.1],
            }
        ]

        with pytest.raises(RuntimeError, match="ChromaDB write error"):
            upsert_chunks(mock_collection, chunks)

    def test_idempotent_upsert(self):
        """같은 id로 두 번 upsert해도 문제없이 동작한다 (멱등성)."""
        mock_collection = MagicMock()
        chunk = {
            "id": "same_id",
            "document": "문서",
            "metadata": {"source": "test"},
            "embedding": [0.1],
        }

        result1 = upsert_chunks(mock_collection, [chunk])
        result2 = upsert_chunks(mock_collection, [chunk])

        assert result1 == 1
        assert result2 == 1
        assert mock_collection.upsert.call_count == 2


# ================================================================== #
# get_collection_count
# ================================================================== #
class TestGetCollectionCount:
    """컬렉션 문서 수 조회 테스트."""

    def test_returns_count(self):
        """컬렉션 내 문서 수를 반환한다."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42

        result = get_collection_count(mock_collection)

        assert result == 42

    def test_empty_collection_returns_zero(self):
        """빈 컬렉션이면 0을 반환한다."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        result = get_collection_count(mock_collection)

        assert result == 0

    def test_error_propagates(self):
        """오류 발생 시 예외가 전파된다."""
        mock_collection = MagicMock()
        mock_collection.count.side_effect = RuntimeError("ChromaDB read error")

        with pytest.raises(RuntimeError, match="ChromaDB read error"):
            get_collection_count(mock_collection)
